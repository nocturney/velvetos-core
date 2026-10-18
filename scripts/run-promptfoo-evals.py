#!/usr/bin/env python3
"""Run the pinned Promptfoo suite locally with no configured remote model/provider."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from vf_spawn import SpawnRefusal, executable_is_absolute, run_tool

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "packages" / "vfharness" / "evals"
CONFIG = EVALS / "promptfooconfig.json"
BIN = ROOT / "tools" / "promptfoo" / "node_modules" / ".bin" / (
    "promptfoo.cmd" if os.name == "nt" else "promptfoo"
)
ENTRY_REL = Path("promptfoo") / "dist" / "src" / "entrypoint.js"

HARDEN = {
    "CI": "true",
    "NO_ANALYTICS": "1",
    "PROMPTFOO_DISABLE_TELEMETRY": "1",
    "PROMPTFOO_DISABLE_REMOTE_GENERATION": "true",
    "PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION": "true",
    "PROMPTFOO_DISABLE_SHARING": "1",
    "PROMPTFOO_SELF_HOSTED": "1",
    "PROMPTFOO_DISABLE_UPDATE": "1",
}

def metrics(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    prompts = data["results"]["prompts"]
    if len(prompts) != 1:
        raise RuntimeError("expected exactly one local provider")
    return prompts[0]["metrics"]

PROMPTFOO_TIMEOUT_SECONDS = 120


def javascript_entrypoint(bin_path: Path) -> Path:
    """Real promptfoo JS entry. POSIX .bin/promptfoo is a symlink to that file."""
    if not bin_path.exists():
        raise SpawnRefusal("SPAWN_EXECUTABLE_MISSING")
    real = Path(os.path.realpath(bin_path))
    if real.suffix.lower() == ".js" and real.is_file():
        return real
    candidate = (bin_path.parent.parent / ENTRY_REL).resolve()
    if candidate.is_file() and candidate.suffix.lower() == ".js":
        return candidate
    raise SpawnRefusal("SPAWN_ENTRYPOINT_REFUSED")


def command_pin(name: str) -> tuple[str, str]:
    """Absolute binary plus the directory that still contains this command name.

    Path.resolve() follows a symlink into another directory. Promptfoo execs
    ``python`` by name, so the pin is the directory from the one PATH lookup.
    """
    if not isinstance(name, str) or not name or "/" in name or "\\" in name or name.startswith("-"):
        raise SpawnRefusal("SPAWN_ARGV_REFUSED")
    found = shutil.which(name)
    if not found or not executable_is_absolute(found):
        code = "SPAWN_PYTHON_REFUSED" if name == "python" else "SPAWN_PATH_LOOKUP_REFUSED"
        raise SpawnRefusal(code)
    name_dir = str(Path(found).parent.resolve())
    binary = str(Path(found).resolve())
    if not executable_is_absolute(binary) or not executable_is_absolute(name_dir):
        raise SpawnRefusal("SPAWN_PATH_LOOKUP_REFUSED")
    return binary, name_dir


def promptfoo_plan(bin_path: Path, args: list[str]) -> tuple[list[str], str, str]:
    """Absolute node, the JS entry, and the python directory the provider execs.

    PATH is the node command directory plus the python command directory.
    It is not the inherited search PATH and not the JS directory.
    """
    entry = javascript_entrypoint(bin_path)
    node, node_dir = command_pin("node")
    _python, python_dir = command_pin("python")
    return [node, str(entry), *args], node_dir, python_dir


def run(config: Path, output: Path):
    argv, node_dir, python_dir = promptfoo_plan(
        BIN,
        ["eval", "-c", str(config), "-o", str(output), "--no-cache"],
    )
    return run_tool(
        argv,
        cwd=ROOT,
        timeout=PROMPTFOO_TIMEOUT_SECONDS,
        extra_env=HARDEN,
        path_dirs=[node_dir, python_dir],
    )

def main() -> int:
    if not BIN.is_file():
        print("FAIL Promptfoo local install missing; run npm ci --prefix tools/promptfoo --ignore-scripts --no-audit --no-fund", file=sys.stderr)
        return 2
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config.get("providers") != ["exec: python policy_target.py"]:
        print("FAIL remote or untrusted provider configured", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "results.json"
        proc = run(CONFIG, out)
        if proc.returncode != 0 or not out.is_file():
            print(proc.stdout[-4000:], file=sys.stderr)
            print(proc.stderr[-4000:], file=sys.stderr)
            return 2
        good = metrics(out)
        if (good.get("testPassCount"), good.get("testFailCount"), good.get("testErrorCount")) != (17, 0, 0):
            print(f"FAIL unexpected Promptfoo metrics {good}", file=sys.stderr)
            return 2
        if good.get("cost") != 0 or (good.get("tokenUsage") or {}).get("total") != 0:
            print("FAIL local suite unexpectedly reported model cost/tokens", file=sys.stderr)
            return 2

        bad_config = json.loads(CONFIG.read_text(encoding="utf-8"))
        bad_config["tests"][0]["assert"][0]["value"] = "ALLOW|price_source_present"
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", dir=EVALS, encoding="utf-8", delete=False
        ) as fh:
            json.dump(bad_config, fh, ensure_ascii=False)
            bad_path = Path(fh.name)
        try:
            bad_out = Path(td) / "negative-results.json"
            bad_proc = run(bad_path, bad_out)
            if not bad_out.is_file():
                print("FAIL negative control produced no result", file=sys.stderr)
                return 2
            bad = metrics(bad_out)
            if bad.get("testFailCount", 0) < 1:
                print("FAIL Promptfoo negative control did not fail", file=sys.stderr)
                return 2
        finally:
            bad_path.unlink(missing_ok=True)

    print("OK promptfoo local=0.123.1 cases=17 pass=17 negative_control=PASS cost=0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
