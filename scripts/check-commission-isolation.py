#!/usr/bin/env python3
"""Assert commission_operational_gaps.py does not mutate production SoTs.

Checksums CANONICAL_SOTS before/after running the commission matrix.
Prints OK on success.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from commission_operational_gaps import CANONICAL_SOTS, checksum_sots  # noqa: E402


def main() -> int:
    before = checksum_sots()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "commission_operational_gaps.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    after = checksum_sots()
    drifted = [k for k in CANONICAL_SOTS if before.get(k) != after.get(k)]
    if drifted:
        print("FAIL production SoTs changed:", ", ".join(drifted))
        print(proc.stdout[-2000:] if proc.stdout else "")
        print(proc.stderr[-1000:] if proc.stderr else "")
        return 1
    if proc.returncode != 0:
        print("FAIL commission exited", proc.returncode)
        print(proc.stdout[-2000:] if proc.stdout else "")
        print(proc.stderr[-1000:] if proc.stderr else "")
        return 1
    # Surface brief summary
    try:
        # last JSON object in stdout
        lines = [ln for ln in (proc.stdout or "").splitlines() if ln.strip().startswith("{")]
        if lines:
            summary = json.loads(lines[-1]) if lines[-1].startswith("{") else {}
            # commission prints a final compact JSON — try parse from end
    except json.JSONDecodeError:
        summary = {}
    print("OK check-commission-isolation — production SoTs unchanged")
    print(f"commission_exit={proc.returncode} sots={len(CANONICAL_SOTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
