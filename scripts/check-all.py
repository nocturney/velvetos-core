#!/usr/bin/env python3
"""Run every computational HQ sensor. No network. No send."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SKIP = {"check-all.py"}


def main() -> int:
    checks = sorted(
        p
        for p in SCRIPTS.glob("check-*.py")
        if p.name not in SKIP
    )
    if not checks:
        print("FAIL no check-*.py sensors found", file=sys.stderr)
        return 1

    failed: list[str] = []
    print(f"SENSORS {len(checks)}")
    for path in checks:
        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        if proc.returncode == 0:
            print(f"PASS {path.name}  {out}")
        else:
            failed.append(path.name)
            detail = err or out or f"exit {proc.returncode}"
            print(f"FAIL {path.name}  {detail}", file=sys.stderr)

    if failed:
        print(f"FAIL suite failed={len(failed)}/{len(checks)}", file=sys.stderr)
        return 1
    print(f"OK suite passed={len(checks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
