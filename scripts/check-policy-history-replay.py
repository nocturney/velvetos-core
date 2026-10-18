#!/usr/bin/env python3
"""Explicit replay of completed Stage 4-8 policy history."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check-policy-architecture.py"


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(CHECK), "--historical-replay"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
        print("FAIL policy-history-replay: " + detail, file=sys.stderr)
        return 1
    tail = (proc.stdout.strip().splitlines() or ["PASS"])[-1]
    print("OK policy-history-replay " + tail)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
