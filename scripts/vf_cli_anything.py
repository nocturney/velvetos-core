#!/usr/bin/env python3
"""VelvetOS adapter for the pinned, headless CLI-Anything FreeCAD pilot."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "packages" / "vfharness" / "devtools" / "cli-anything.json"
CLONE = ROOT / ".local-devtools" / "phase5" / "cli-anything"
VENV = ROOT / ".local-devtools" / "phase5" / "venv"
VENV_SCRIPTS = VENV / ("Scripts" if os.name == "nt" else "bin")
CLI = VENV_SCRIPTS / ("cli-anything-freecad.exe" if os.name == "nt" else "cli-anything-freecad")
FREECAD_ROOT = (
    Path.home() / "Documents" / "VelvetPrintLab" / "tools"
    / "FreeCAD_1.1.3-Windows-x86_64-py311"
)
FREECAD_CMD = FREECAD_ROOT / "FreeCADCmd.exe"
BLOCKED_GROUPS = {"preview", "motion", "repl"}


def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8-sig"))


def run(args: list[str], *, cwd: Path | None = None,
        env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)


def detect_group(args: list[str]) -> str | None:
    index = 0
    while index < len(args):
        token = args[index]
        if token in {"--json", "--dry-run"}:
            index += 1
            continue
        if token in {"-p", "--project"}:
            index += 2
            continue
        if token.startswith("--project="):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token
    return None
def tool_env() -> dict[str, str]:
    env = os.environ.copy()
    env["FREECAD_PATH"] = str(FREECAD_CMD)
    env["CLI_ANYTHING_FORCE_INSTALLED"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PATH"] = os.pathsep.join(
        [str(VENV_SCRIPTS), str(FREECAD_ROOT), env.get("PATH", "")]
    )
    return env


def doctor() -> int:
    data = registry()
    issues: list[str] = []
    head = ""
    if (CLONE / ".git").is_dir():
        proc = run(["git", "rev-parse", "HEAD"], cwd=CLONE)
        head = proc.stdout.strip()
        if proc.returncode or head != data["pin"]:
            issues.append(f"CLI-Anything pin mismatch: {head or 'unreadable'}")
    else:
        issues.append("CLI-Anything local clone missing")

    if not CLI.is_file():
        issues.append(f"FreeCAD CLI entry point missing: {CLI}")
    if not FREECAD_CMD.is_file():
        issues.append(f"FreeCADCmd missing: {FREECAD_CMD}")

    freecad_version = ""
    if FREECAD_CMD.is_file():
        proc = run([str(FREECAD_CMD), "--version"])
        freecad_version = proc.stdout.strip()
        if proc.returncode or "FreeCAD 1.1.3" not in freecad_version:
            issues.append(f"Unexpected FreeCAD version: {freecad_version}")

    patch_ok = False
    if (CLONE / ".git").is_dir():
        patch = ROOT / data["overlay"]
        patch_ok = (
            run(["git", "apply", "--unidiff-zero", "--reverse", "--check", str(patch)], cwd=CLONE).returncode
            == 0
        )
        if not patch_ok:
            issues.append("FreeCAD boolean/export overlay is not applied")

    payload = {
        "status": "PASS" if not issues else "BLOCKED",
        "cli_anything_pin": head,
        "freecad_version": freecad_version,
        "overlay_applied": patch_ok,
        "blocked_groups": sorted(BLOCKED_GROUPS),
        "canonical_cad_route": data["authority"]["canonical_cad_route"],
        "slicer_authority": "scripts/vf_cad.py + VelvetPrintLab printer_matrix.json",
        "printer_control": False,
        "incremental_recurring_cost_ils": 0,
        "issues": issues,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not issues else 2
def freecad(args: list[str]) -> int:
    if args and args[0] == "--":
        args = args[1:]
    if not args:
        args = ["--help"]

    group = detect_group(args)
    if group in BLOCKED_GROUPS:
        print(json.dumps({
            "status": "BLOCKED",
            "reason": f"CLI-Anything FreeCAD group '{group}' is disabled by VelvetOS scope",
            "allowed_route": "headless structured CAD; use other visual tools only when GUI automation is actually required",
        }, indent=2), file=sys.stderr)
        return 2

    if not CLI.is_file() or not FREECAD_CMD.is_file():
        print(json.dumps({
            "status": "BLOCKED",
            "reason": "CLI-Anything pilot is not installed",
            "repair": "python scripts/setup-cli-anything-pilot.py",
        }, indent=2), file=sys.stderr)
        return 2

    call_args = list(args)
    if "--help" not in call_args and "-h" not in call_args and "--json" not in call_args:
        call_args.insert(0, "--json")
    proc = subprocess.run([str(CLI), *call_args], env=tool_env(), text=True)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    fc = sub.add_parser("freecad")
    fc.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command == "doctor":
        return doctor()
    if args.command == "freecad":
        return freecad(args.args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
