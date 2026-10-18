#!/usr/bin/env python3
"""DOMAIN guard for the synthetic #604 desktop eligibility matrix.

Runs the lab checker and a duplicate-id negative control. A synthetic pass is
not a production adapter, a Windows SID, or a Core lease.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "docs/implementation/office-v2/phase2/desktop-runtime-eligibility-check-v0.py"
FIXTURE = ROOT / "docs/implementation/office-v2/phase2/desktop-runtime-eligibility-fixtures-v0.json"


def fail(message: str) -> None:
    print("FAIL " + message, file=sys.stderr)
    raise SystemExit(1)


def load_checker():
    spec = importlib.util.spec_from_file_location("desktop_eligibility_lab_v0", CHECKER)
    if spec is None or spec.loader is None:
        fail("cannot load desktop eligibility checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cli(optimize: bool) -> None:
    command = [sys.executable]
    if optimize:
        command.append("-O")
    command.append(str(CHECKER))
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        fail(f"checker exit {proc.returncode} optimize={optimize}")
    try:
        receipt = json.loads(proc.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        fail(f"checker receipt unreadable optimize={optimize}: {exc}")
    expected = {
        "schema": "velvet.desktop.eligibility-lab-receipt.v0",
        "owner_issue": 604,
        "executed_cases": 69,
        "passed": 69,
        "failed": 0,
        "model_invoked": False,
        "desktop_invoked": False,
        "external_effects": False,
        "production_authority": False,
    }
    if receipt != expected:
        fail(f"happy-path receipt drift optimize={optimize}: {receipt}")


def duplicate_control(module) -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    first = data["cases"][0]
    data["cases"] = [first, *data["cases"]]
    fails, receipt = module.evaluate(data, quiet=True)
    if receipt["executed_cases"] != 70 or receipt["passed"] != 69 or receipt["failed"] != 1:
        fail(f"duplicate id undercounted the pass total: {receipt}")
    if receipt["passed"] + receipt["failed"] != receipt["executed_cases"]:
        fail("duplicate receipt accounting mismatch")
    if [row[1] for row in fails] != ["DUPLICATE_CASE_ID"]:
        fail(f"duplicate id reason drifted: {fails}")
    if receipt["production_authority"] is not False:
        fail("duplicate control gained production authority")


def main() -> None:
    if not CHECKER.is_file() or not FIXTURE.is_file():
        fail("missing #604 desktop eligibility lab files")
    run_cli(False)
    run_cli(True)
    duplicate_control(load_checker())
    print("OK desktop eligibility 69/69; DUPLICATE_CASE_ID keeps passed=69 executed=70")


if __name__ == "__main__":
    main()
