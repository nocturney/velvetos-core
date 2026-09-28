#!/usr/bin/env python3
"""Validate the Windows D: path contract without touching host state."""
from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "packages" / "velvetos" / "WINDOWS-PATH-CONTRACT.md"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL {message}")


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
    return path.read_text(encoding="utf-8")


def require(blob: str, needle: str, label: str) -> None:
    if needle not in blob:
        fail(f"{label} missing {needle}")


FAIL_CLOSED_PS = "The legacy user-profile fallback is closed"

# Windows code must never fall back to %USERPROFILE%\.velvetos or %USERPROFILE%\velvetos-core.
LEGACY_WINDOWS_FALLBACK = re.compile(
    r"(?:\$env:USERPROFILE|%USERPROFILE%|\$HOME\b|\$env:HOME\b|~)[\\/\s\"',()]*(?:Join-Path[^\r\n]*)?"
    r"[\\/\"'\s]*\.?velvetos(?:-core)?\b|\$LegacyRoot\b|GetFolderPath\([^)]*UserProfile[^)]*\)[^\r\n]*velvetos",
    re.I,
)


def legacy_windows_fallbacks(blob: str) -> list[str]:
    hits: list[str] = []
    for line in blob.splitlines():
        code = line.split("#", 1)[0] if line.lstrip().startswith("#") else line
        if LEGACY_WINDOWS_FALLBACK.search(code):
            hits.append(line.strip()[:160])
    return hits


def legacy_scanner_selftest() -> None:
    bad = (
        '$LegacyRoot = Join-Path $env:USERPROFILE ".velvetos"',
        '$Repo = Resolve-VelvetPath "VELVETOS_REPO_ROOT" (Join-Path $env:USERPROFILE "velvetos-core")',
        "$RuntimeRoot = Resolve-VelvetPath 'VELVETOS_RUNTIME_ROOT' $LegacyRoot",
        r"$Root = '%USERPROFILE%\.velvetos\cognee'",
        '$x = Join-Path $HOME ".velvetos"',
    )
    good = (
        '$Repo = Resolve-VelvetPath "VELVETOS_REPO_ROOT"',
        '& git clone https://github.com/nocturney/velvetos-core.git $Repo',
        "# the legacy user-profile fallback is closed",
    )
    for line in bad:
        if not legacy_windows_fallbacks(line):
            fail(f"legacy fallback scanner selftest missed: {line}")
    for line in good:
        if legacy_windows_fallbacks(line):
            fail(f"legacy fallback scanner selftest false positive: {line}")


class _WindowsOs:
    """Delegate to the real os module but report os.name == 'nt' (pathlib stays native)."""

    name = "nt"

    def __getattr__(self, attr: str) -> Any:
        return getattr(os, attr)


VFMEM_ENV = (
    "VELVETOS_RUNTIME_ROOT", "VFMEM_COGNEE_ROOT", "VFMEM_COGNEE_HOME",
    "VFMEM_COGNEE_LIVE_VENV", "VFMEM_COGNEE_PYTHON",
)


@contextlib.contextmanager
def scoped_env(**values: str) -> Iterator[None]:
    saved = {key: os.environ.get(key) for key in (*VFMEM_ENV, "HOME", *values)}
    try:
        for key in VFMEM_ENV:
            os.environ.pop(key, None)
        os.environ.update(values)
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def load_module(rel: str, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    if spec is None or spec.loader is None:
        fail(f"cannot load {rel}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def expect_windows_block(label: str, call: Any) -> None:
    try:
        value = call()
    except RuntimeError as exc:
        if "VELVETOS_RUNTIME_ROOT" not in str(exc) or "WINDOWS-PATH-CONTRACT.md" not in str(exc):
            fail(f"{label} Windows fail-closed error is unclear: {exc}")
        return
    fail(f"{label} falls back to {value} on Windows without VELVETOS_RUNTIME_ROOT")


def check_python_windows_fail_closed() -> None:
    """Simulate os.name == 'nt' against the real Cognee/vfmem path helpers."""
    cognee = load_module("packages/vfmem/scripts/vf_cognee.py", "_wpc_vf_cognee")
    runtime = load_module("packages/vfmem/scripts/vf_cognee_runtime.py", "_wpc_vf_cognee_runtime")
    vfmem = load_module("scripts/vfmem.py", "_wpc_vfmem")
    cfg = cognee.load_config()
    real_os = os
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "profile"
        legacy = home / ".velvetos" / "cognee-venv"
        for rel in ("Scripts/python.exe", "bin/python"):
            (legacy / rel).parent.mkdir(parents=True, exist_ok=True)
            (legacy / rel).write_text("", encoding="utf-8")
        d_runtime = str(Path(tmp) / "D" / "Velvet" / "Runtime" / "VelvetOS")
        try:
            for module in (cognee, runtime, vfmem):
                module.os = _WindowsOs()
            with scoped_env(HOME=str(home)):
                expect_windows_block("vf_cognee.runtime_root", lambda: cognee.runtime_root(cfg))
                expect_windows_block("vf_cognee_runtime.home", runtime.home)
                expect_windows_block("vf_cognee_runtime.live_venv", runtime.live_venv)
                expect_windows_block("vf_cognee_runtime.runtime_root", runtime.runtime_root)
                if vfmem._cognee_python() is not None:
                    fail("vfmem._cognee_python still uses the legacy ~/.velvetos/cognee-venv on Windows")
            with scoped_env(HOME=str(home), VELVETOS_RUNTIME_ROOT=d_runtime):
                if cognee.runtime_root(cfg) != Path(d_runtime) / "Cognee" / "cognee":
                    fail("vf_cognee.runtime_root must use %VELVETOS_RUNTIME_ROOT%\\Cognee\\cognee on Windows")
                if runtime.home() != (Path(d_runtime) / "Cognee").resolve():
                    fail("vf_cognee_runtime.home must use %VELVETOS_RUNTIME_ROOT%\\Cognee on Windows")
            explicit = str(Path(tmp) / "D" / "explicit")
            with scoped_env(HOME=str(home), VFMEM_COGNEE_ROOT=explicit, VFMEM_COGNEE_LIVE_VENV=explicit + "-venv"):
                if cognee.runtime_root(cfg) != Path(explicit):
                    fail("vf_cognee.runtime_root must honor VFMEM_COGNEE_ROOT on Windows")
                if runtime.runtime_root() != Path(explicit).resolve() or runtime.live_venv() != Path(explicit + "-venv").resolve():
                    fail("vf_cognee_runtime must honor explicit VFMEM_COGNEE_* overrides on Windows")
        finally:
            for module in (cognee, runtime, vfmem):
                module.os = real_os
        if os.name != "nt":
            # Non-Windows (Mac) hosts keep the ~/.velvetos default unchanged.
            with scoped_env(HOME=str(home)):
                if cognee.runtime_root(cfg) != Path(cfg["runtimeRoot"]).expanduser():
                    fail("vf_cognee.runtime_root changed its non-Windows default")
                if runtime.home() != (home / ".velvetos").resolve():
                    fail("vf_cognee_runtime.home changed its non-Windows default")
                if vfmem._cognee_python() not in (legacy / "Scripts" / "python.exe", legacy / "bin" / "python"):
                    fail("vfmem._cognee_python dropped the non-Windows ~/.velvetos/cognee-venv candidate")


def check_upstream_watch_local_paths() -> None:
    watch = read("packages/velvetos/UPSTREAM-WATCH.json")
    for hit in re.findall(r"%USERPROFILE%[\\/]+\.?velvetos[^\"]*", watch, re.I):
        fail(f"UPSTREAM-WATCH.json still points at a legacy user-profile path: {hit}")
    rows = {row.get("repo"): row for row in json.loads(watch).get("sources", []) if isinstance(row, dict)}
    for repo, needle in (
        ("topoteretes/cognee", "%VELVETOS_RUNTIME_ROOT%/Cognee/cognee-venv"),
        ("OpenMOSS/MOSS-TTS-Nano", "%VELVETOS_RUNTIME_ROOT%/deps/MOSS-TTS-Nano"),
    ):
        if needle not in ((rows.get(repo) or {}).get("integration") or []):
            fail(f"UPSTREAM-WATCH.json {repo} must track {needle}")
    upstream = load_module("scripts/vf_upstream_watch.py", "_wpc_vf_upstream_watch")
    if not callable(getattr(upstream, "expand_local_ref", None)):
        fail("vf_upstream_watch.py must expand %VELVETOS_*% local refs via expand_local_ref()")
    with scoped_env(VELVETOS_RUNTIME_ROOT="/velvet-runtime"):
        got = upstream.expand_local_ref("%VELVETOS_RUNTIME_ROOT%/deps/MOSS-TTS-Nano")
        if got != os.sep.join(("", "velvet-runtime", "deps", "MOSS-TTS-Nano")).replace("/", os.sep):
            fail(f"vf_upstream_watch does not expand %VELVETOS_RUNTIME_ROOT%: {got}")
    with scoped_env():
        if upstream.expand_local_ref("%VELVETOS_RUNTIME_ROOT%/deps/MOSS-TTS-Nano") is not None:
            fail("vf_upstream_watch must skip a local ref whose variable is unset")
    if upstream.expand_local_ref("packages/vfmem/cognee.json") is not None:
        fail("vf_upstream_watch must treat repo-relative integration paths as non-local")


legacy_scanner_selftest()


contract = CONTRACT.read_text(encoding="utf-8")
for needle in (
    r"D:\Velvet\Workspaces",
    r"D:\Velvet\Data",
    r"D:\Velvet\Artifacts",
    r"D:\Velvet\Logs",
    r"D:\Velvet\Cache",
    r"D:\Velvet\Tmp",
    r"D:\Velvet\Backups",
    r"VELVET_ROOT=D:\Velvet",
    r"VELVETOS_REPO_ROOT=D:\Velvet\Repos\velvetos-core",
    r"VELVETOS_RUNTIME_ROOT=D:\Velvet\Runtime\VelvetOS",
    r"VELVETOS_STATE_ROOT=D:\Velvet\State\VelvetOS",
    "## Default working path and forbidden locations",
    r"%USERPROFILE%\Desktop",
    "If D: is unavailable, stop and report it",
    "## Compatibility rule",
    "fallbacks are closed (fail closed)",
    "Mac hosts are out of scope",
):
    require(contract, needle, "path contract")
compat = contract.split("## Compatibility rule", 1)[1].split("\n## ", 1)[0]
for stale in ("During migration only", "may fall back", "rollback/commissioning safety net"):
    if stale in compat:
        fail(f"path contract compatibility rule still allows the legacy fallback: {stale}")

for rel, needles in {
    "scripts/bootstrap-edge-host-windows.ps1": (
        "VELVET_ROOT", "VELVETOS_REPO_ROOT", "VELVETOS_RUNTIME_ROOT", "VELVETOS_STATE_ROOT", "$TmpRoot", FAIL_CLOSED_PS
    ),
    "scripts/bootstrap-speech-host-windows.ps1": (
        "VELVET_ROOT", "VELVETOS_REPO_ROOT", "VELVETOS_STATE_ROOT", "$TmpRoot", FAIL_CLOSED_PS
    ),
    "scripts/bootstrap-manim-host-windows.ps1": (
        "VELVET_ROOT", "VELVETOS_RUNTIME_ROOT", "VELVETOS_STATE_ROOT", "$TmpRoot", FAIL_CLOSED_PS
    ),
    "packages/vfmem/scripts/vf_cognee_runtime.py": ("VELVETOS_RUNTIME_ROOT", 'os.name == "nt"'),
    "packages/vfmem/scripts/vf_cognee.py": ("VELVETOS_RUNTIME_ROOT", 'os.name == "nt"'),
    "scripts/vfmem.py": ("VELVETOS_RUNTIME_ROOT", 'os.name != "nt"'),
}.items():
    blob = read(rel)
    for needle in needles:
        require(blob, needle, rel)
    if r"C:\Users\Chris" in blob:
        fail(f"Chris-specific absolute path in {rel}")

for rel in (
    "scripts/bootstrap-edge-host-windows.ps1",
    "scripts/bootstrap-speech-host-windows.ps1",
    "scripts/bootstrap-manim-host-windows.ps1",
):
    blob = read(rel)
    # Formerly exactly one GetTempPath() legacy fallback; the fallback is now closed.
    if blob.count("GetTempPath()") != 0:
        fail(f"{rel} must resolve scratch through VELVET_ROOT\\Tmp only (no Windows temp fallback)")
    if not re.search(r"function Resolve-VelvetPath\(\[string\]\$Name\) \{", blob):
        fail(f"{rel} Resolve-VelvetPath must take only the variable name (no fallback argument)")
    for call in re.findall(r"Resolve-VelvetPath [^\r\n]*", blob):
        if not re.fullmatch(r"Resolve-VelvetPath ['\"](?:VELVET_ROOT|VELVETOS_[A-Z_]+)['\"]\s*", call):
            fail(f"{rel} Resolve-VelvetPath call carries a fallback: {call.strip()}")

windows_ps = sorted((ROOT / "scripts").glob("*-windows.ps1"))
if len(windows_ps) < 4:
    fail("expected the Windows bootstraps under scripts/*-windows.ps1")
for path in windows_ps:
    rel = path.relative_to(ROOT).as_posix()
    hits = legacy_windows_fallbacks(path.read_text(encoding="utf-8"))
    if hits:
        fail(f"{rel} falls back to a legacy user-profile path: {hits[0]}")

check_python_windows_fail_closed()
check_upstream_watch_local_paths()

rule = read(".cursor/rules/windows-d-paths.mdc")
if not rule.startswith("---\n"):
    fail(".cursor/rules/windows-d-paths.mdc needs YAML front matter")
front = rule.split("\n---", 1)[0]
if "alwaysApply: true" not in front:
    fail(".cursor/rules/windows-d-paths.mdc must be alwaysApply: true")
for needle in ("WINDOWS-PATH-CONTRACT.md", r"D:\Velvet", "Desktop", "C:", "VELVETOS_RUNTIME_ROOT"):
    require(rule, needle, ".cursor/rules/windows-d-paths.mdc")

hosts = json.loads(read("packages/vfmcp/RENDER-HOSTS.json"))
windows = hosts["hosts"]["sderot-windows"]
if windows.get("repoPath") != r"%VELVETOS_REPO_ROOT%":
    fail("Windows repoPath must use VELVETOS_REPO_ROOT")
if windows.get("localState") != r"%VELVETOS_STATE_ROOT%\edge-host.json":
    fail("Windows edge state must use VELVETOS_STATE_ROOT")
if windows.get("speechLocalState") != r"%VELVETOS_STATE_ROOT%\speech-host.json":
    fail("Windows speech state must use VELVETOS_STATE_ROOT")

video = json.loads(read("packages/vfom/VIDEO-TOOLCHAIN.json"))
manim = video["animationSlots"]["manim"]["hostEvidence"]
if manim.get("toolchain") != r"%VELVETOS_RUNTIME_ROOT%\Toolchains\manim-0.21.0-py312":
    fail("Manim host evidence must use VELVETOS_RUNTIME_ROOT")

grok = json.loads(read("automation/grok/cognee-routines.json"))
prompts = "\n".join(str(row.get("prompt") or "") for row in grok.get("routines", []))
for needle in (
    r"%VELVETOS_RUNTIME_ROOT%\Cognee\cognee-core",
    r"%VELVETOS_RUNTIME_ROOT%\Cognee\cognee-venv",
    r"%VELVETOS_RUNTIME_ROOT%\Cognee\cognee\active-state.json",
):
    require(prompts, needle, "Grok Cognee path contract")
if r"C:\Users\Chris" in prompts:
    fail("Grok Cognee prompts still contain Chris-specific absolute paths")

openpost = json.loads(read("packages/vfigos/OPENPOST.json"))
persistence = (openpost.get("runtime") or {}).get("persistence") or {}
if persistence.get("startScript") != r"D:\Velvet\Services\OpenPost\staging\start-openpost-staging.ps1":
    fail("OpenPost staging startScript must live under D:\\Velvet\\Services")
if str(persistence.get("startScriptSha256") or "").lower() != "2d5541e4c2b7017c9d34212e78e53c02ee6f144f0e54cf1b1f68defbfed03bd0":
    fail("OpenPost staging startScript SHA drift")

fallback = read("packages/vfmcp/WINDOWS-EDGE-FALLBACK.md")
require(fallback, "WINDOWS-PATH-CONTRACT.md", "Windows fallback playbook")
require(fallback, r"%VELVETOS_STATE_ROOT%\edge-host.json", "Windows fallback playbook")

print("OK windows-path-contract vars=4 workspaces+datalanes+services default-path-section=yes "
      f"legacy-fallback=closed windows-ps1={len(windows_ps)} nt-sim=3 cursor-rule=yes chris-absolute=0")
