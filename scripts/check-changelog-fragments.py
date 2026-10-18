#!/usr/bin/env python3
"""Sensor: capability PRs carry a changelog fragment or a CHANGELOG.md edit."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import changelog_contract as contract  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if contract.selftest() != 0:
        return 1
    compiled = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "changelog-compile.py"), "--selftest"],
        text=True, capture_output=True,
    )
    if compiled.returncode != 0:
        print(compiled.stderr or compiled.stdout, file=sys.stderr)
        return compiled.returncode
    sys.stdout.write(compiled.stdout)
    if contract.validate_committed() != 0:
        return 1
    return contract.live_gate()


if __name__ == "__main__":
    raise SystemExit(main())
