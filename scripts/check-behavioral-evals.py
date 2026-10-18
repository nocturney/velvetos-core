#!/usr/bin/env python3
"""Validate the zero-cost behavioral regression contract without network access."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

import stat

from vf_spawn import same_pinned_directory

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "packages" / "vfharness" / "evals"
CONFIG = EVALS / "promptfooconfig.json"
TARGET = EVALS / "policy_target.py"
PACKAGE = ROOT / "tools" / "promptfoo" / "package.json"
LOCK = ROOT / "tools" / "promptfoo" / "package-lock.json"
REQUIRED = {
    "missing_price", "missing_authority", "tool_failure", "memory_only",
    "untrusted_authority_change", "readonly_to_write", "handoff_bypass",
    "publish_without_authorization", "write_without_readback", "prompt_injection",
}

def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)

def load_target():
    spec = importlib.util.spec_from_file_location("vf_behavior_target", TARGET)
    if spec is None or spec.loader is None:
        fail("cannot load policy target")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_promptfoo_runner():
    spec = importlib.util.spec_from_file_location(
        "run_promptfoo_evals", ROOT / "scripts" / "run-promptfoo-evals.py"
    )
    if spec is None or spec.loader is None:
        fail("cannot load promptfoo runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def promptfoo_fixture(root: Path) -> tuple[Path, Path, Path]:
    """A real .bin shim whose target is entrypoint.js, plus a python shim."""
    entry = root / "node_modules" / "promptfoo" / "dist" / "src" / "entrypoint.js"
    entry.parent.mkdir(parents=True)
    entry.write_text(
        "#!/usr/bin/env node\n"
        "const {spawnSync} = require('child_process');\n"
        "const node = spawnSync('node', ['-e', 'process.stdout.write(\"node-path-ok\")'], {encoding:'utf8'});\n"
        "const py = spawnSync('python', ['-c', 'print(\"python-ok\")'], {encoding:'utf8', shell: process.platform === 'win32'});\n"
        "if (node.status !== 0 || !String(node.stdout).includes('node-path-ok')) {\n"
        "  process.stderr.write('node unreachable\\n');\n"
        "  process.exit(2);\n"
        "}\n"
        "if (py.status !== 0 || !String(py.stdout).includes('python-ok')) {\n"
        "  process.stderr.write('python unreachable\\n');\n"
        "  process.exit(3);\n"
        "}\n"
        "process.stdout.write('reachable\\n');\n",
        encoding="utf-8",
    )
    bin_dir = root / "node_modules" / ".bin"
    bin_dir.mkdir(parents=True)
    py_dir = root / "py"
    py_dir.mkdir()
    if os.name == "nt":
        shim = bin_dir / "promptfoo.cmd"
        shim.write_text("@echo off\r\n", encoding="utf-8")
        python = py_dir / "python.cmd"
        python.write_text("@echo python-ok\r\n", encoding="utf-8")
    else:
        shim = bin_dir / "promptfoo"
        shim.symlink_to(entry)
        python = py_dir / "python"
        python.write_text("#!/bin/sh\necho python-ok\n", encoding="utf-8")
        python.chmod(python.stat().st_mode | stat.S_IEXEC)
    return shim, entry, py_dir


def prove_promptfoo_hygiene() -> None:
    """Promptfoo spawns absolute node and keeps node and python on PATH."""
    import vf_spawn

    module = load_promptfoo_runner()
    sentinel = "VF_SPAWN_SENTINEL"
    previous_sentinel = os.environ.get(sentinel)
    previous_node_options = os.environ.get("NODE_OPTIONS")
    previous_path = os.environ.get("PATH", "")
    os.environ[sentinel] = "nope"
    os.environ["NODE_OPTIONS"] = "--experimental-permission"
    directory = Path(tempfile.mkdtemp(prefix="vf-promptfoo-"))
    shim, entry, py_dir = promptfoo_fixture(directory)
    os.environ["PATH"] = os.pathsep.join([str(py_dir), previous_path])
    captured: list[tuple[list[str], dict]] = []
    original = vf_spawn.subprocess.run

    def fake_run(argv, **kwargs):
        captured.append((list(argv), kwargs))
        return vf_spawn.subprocess.CompletedProcess(argv, 0, stdout="reachable\n", stderr="")

    module.BIN = shim
    vf_spawn.subprocess.run = fake_run
    try:
        module.run(CONFIG, directory / "out.json")
    finally:
        vf_spawn.subprocess.run = original
        if previous_sentinel is None:
            os.environ.pop(sentinel, None)
        else:
            os.environ[sentinel] = previous_sentinel
        if previous_node_options is None:
            os.environ.pop("NODE_OPTIONS", None)
        else:
            os.environ["NODE_OPTIONS"] = previous_node_options
        os.environ["PATH"] = previous_path
    if len(captured) != 1:
        fail("promptfoo spawn did not run")
    argv, kwargs = captured[0]
    if len(argv) < 2 or argv[1] != str(entry.resolve()) or not os.path.isabs(argv[0]):
        fail(f"promptfoo was not absolute node plus the entrypoint: {argv}")
    if Path(argv[0]).name.lower() not in {"node", "node.exe"}:
        fail(f"promptfoo argv did not start with node: {argv}")
    if kwargs.get("timeout") != module.PROMPTFOO_TIMEOUT_SECONDS:
        fail("promptfoo timeout missing")
    env = kwargs.get("env")
    allowed = set(vf_spawn._BASE_ENV_KEYS) | set(module.HARDEN) | {"PATH"}
    if not isinstance(env, dict) or sentinel in env or "NODE_OPTIONS" in env or set(env) - allowed:
        fail(f"promptfoo environment was not allowlisted: {env}")
    for key, value in module.HARDEN.items():
        if env.get(key) != value:
            fail(f"promptfoo lost harden key {key}")
    parts = env.get("PATH", "").split(os.pathsep)
    node_dir = str(Path(argv[0]).resolve().parent)
    python_dir = str(py_dir.resolve())
    if len(parts) != 2 or not same_pinned_directory(parts[0], node_dir):
        fail(f"promptfoo PATH did not start with the node directory: {env.get('PATH')}")
    if not same_pinned_directory(parts[1], python_dir):
        fail(f"promptfoo PATH did not include the python directory: {env.get('PATH')}")
    if same_pinned_directory(parts[0], str(entry.resolve().parent)):
        fail("promptfoo PATH was only the entrypoint directory")


def prove_promptfoo_python_symlink() -> None:
    """A python symlink must stay pinned at the name, not the target directory."""
    if os.name == "nt":
        return
    module = load_promptfoo_runner()
    previous_path = os.environ.get("PATH", "")
    directory = Path(tempfile.mkdtemp(prefix="vf-promptfoo-link-"))
    shim, _entry, py_dir = promptfoo_fixture(directory)
    target_dir = directory / "python-target"
    target_dir.mkdir()
    target = target_dir / "python3"
    target.write_text("#!/bin/sh\necho python-ok\n", encoding="utf-8")
    target.chmod(target.stat().st_mode | stat.S_IEXEC)
    link = py_dir / "python"
    link.unlink()
    link.symlink_to(target)
    os.environ["PATH"] = os.pathsep.join([str(py_dir), previous_path])
    module.BIN = shim
    try:
        proc = module.run(CONFIG, directory / "out.json")
    finally:
        os.environ["PATH"] = previous_path
    if proc.returncode != 0 or "reachable" not in proc.stdout:
        fail(
            "promptfoo lost the python symlink directory: "
            f"exit={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr!r}"
        )


def prove_promptfoo_reachable() -> None:
    """Run the real resolver. A mock subprocess cannot see a missing node."""
    module = load_promptfoo_runner()
    previous_path = os.environ.get("PATH", "")
    directory = Path(tempfile.mkdtemp(prefix="vf-promptfoo-live-"))
    shim, _entry, py_dir = promptfoo_fixture(directory)
    os.environ["PATH"] = os.pathsep.join([str(py_dir), previous_path])
    module.BIN = shim
    try:
        proc = module.run(CONFIG, directory / "out.json")
    finally:
        os.environ["PATH"] = previous_path
    if proc.returncode != 0 or "reachable" not in proc.stdout:
        fail(
            "promptfoo PATH cannot run node and python: "
            f"exit={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr!r}"
        )


def main() -> None:
    prove_promptfoo_hygiene()
    prove_promptfoo_reachable()
    prove_promptfoo_python_symlink()
    for path in (CONFIG, TARGET, PACKAGE, LOCK):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    if package.get("devDependencies", {}).get("promptfoo") != "0.123.1":
        fail("Promptfoo version must be pinned to 0.123.1")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config.get("providers") != ["exec: python policy_target.py"]:
        fail("Promptfoo provider must remain the trusted local exec target only")
    tests = config.get("tests") or []
    if len(tests) < 10:
        fail("behavioral suite is too small")
    module = load_target()
    seen = set()
    for test in tests:
        scenario = json.loads(test["vars"]["scenario"])
        kind = scenario.get("kind")
        seen.add(kind)
        assertions = test.get("assert") or []
        if len(assertions) != 1 or assertions[0].get("type") != "equals":
            fail(f"{test.get('description')}: exactly one equals assertion required")
        actual = module.evaluate(scenario)
        if actual != assertions[0].get("value"):
            fail(f"{test.get('description')}: {actual!r} != expected")
    missing = REQUIRED - seen
    if missing:
        fail("missing required scenarios: " + ",".join(sorted(missing)))
    unsafe = module.evaluate({"kind": "missing_price", "price_source": False})
    if unsafe == "ALLOW|price_source_present":
        fail("negative control did not catch invented-price path")
    injected = module.evaluate({"kind": "prompt_injection"})
    if not injected.startswith("BLOCK|"):
        fail("negative control did not block prompt injection")
    print(f"OK behavioral-evals cases={len(tests)} required={len(REQUIRED)} negative_controls=2")

if __name__ == "__main__":
    main()
