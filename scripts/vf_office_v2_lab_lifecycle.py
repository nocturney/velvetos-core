#!/usr/bin/env python3
"""Plan/execute bounded Office v2 LAB lifecycle operations.

Default is plan-only. Execution requires --execute and a READY doctor.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "tools" / "office-v2-lab" / "compose.yaml"
DOCTOR = ROOT / "scripts" / "vf_office_v2_lab_doctor.py"
WSL_DISTRO = os.environ.get("OFFICEV2_WSL_DISTRO", "OfficeV2-Lab")


def wsl_path(path: Path) -> str:
    raw = str(path.resolve()).replace("\\", "/")
    if len(raw) >= 3 and raw[1:3] == ":/":
        return f"/mnt/{raw[0].lower()}{raw[2:]}"
    return raw


def compose_base() -> list[str]:
    if os.name == "nt":
        return ["wsl", "-d", WSL_DISTRO, "--", "docker", "compose", "-f", wsl_path(COMPOSE)]
    return ["docker", "compose", "-f", str(COMPOSE)]


def plan(action: str) -> dict[str, Any]:
    base = compose_base()
    commands = {
        "up": [base + ["up", "-d", "officev2-otel"]],
        "down": [base + ["down"]],
        "destroy": [base + ["down", "--volumes", "--remove-orphans"]],
        "recreate": [base + ["down"], base + ["up", "-d", "officev2-otel"]],
    }
    if action not in commands:
        raise ValueError(action)
    return {
        "schema": "velvetos.office-v2.lab-lifecycle-plan.v0",
        "action": action,
        "commands": commands[action],
        "scope": "tools/office-v2-lab + officev2_lab only",
        "production_mutation": False,
    }


def doctor() -> dict[str, Any]:
    p = subprocess.run(
        [sys.executable, str(DOCTOR), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    if p.returncode != 0:
        return {"verdict": "DOCTOR_FAILED", "raw": (p.stderr or p.stdout)[:1000]}
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"verdict": "DOCTOR_FAILED", "raw": p.stdout[:1000]}


def execute(plan_data: dict[str, Any]) -> dict[str, Any]:
    health = doctor()
    if health.get("verdict") != "READY_FOR_LAB_RUNTIME":
        return {
            "status": "BLOCKED",
            "reason": "LAB doctor is not READY_FOR_LAB_RUNTIME",
            "doctor": health,
            "executed_commands": 0,
        }

    results = []
    for cmd in plan_data["commands"]:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        results.append({
            "command": cmd,
            "returncode": p.returncode,
            "stdout": p.stdout[-2000:],
            "stderr": p.stderr[-2000:],
        })
        if p.returncode != 0:
            return {"status": "FAIL", "results": results, "executed_commands": len(results)}
    return {"status": "PASS", "results": results, "executed_commands": len(results)}


def self_test() -> dict[str, Any]:
    up = plan("up")
    destroy = plan("destroy")
    ok = (
        up["production_mutation"] is False
        and destroy["production_mutation"] is False
        and up["commands"][0][-2:] == ["-d", "officev2-otel"]
        and "--volumes" in destroy["commands"][0]
        and all("office-v2-lab" in " ".join(cmd) for cmd in [*up["commands"], *destroy["commands"]])
    )
    return {
        "status": "PASS" if ok else "FAIL",
        "default_mode": "PLAN_ONLY",
        "execute_requires_flag": True,
        "execute_requires_ready_doctor": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["up", "down", "destroy", "recreate"], nargs="?")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        result = self_test()
    elif args.action:
        p = plan(args.action)
        result = execute(p) if args.execute else {"status": "PLAN", **p, "executed_commands": 0}
    else:
        ap.print_help()
        return 2

    print(json.dumps(result, ensure_ascii=False) if args.json else json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"PASS", "PLAN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
