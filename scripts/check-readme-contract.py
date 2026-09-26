#!/usr/bin/env python3
"""Sensor: Living README contract exemptions stay narrow (routine output only)."""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import readme_contract  # noqa: E402


def main() -> int:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = readme_contract.selftest()
    line = [l for l in buf.getvalue().splitlines() if l.startswith("OK readme-contract")]
    if rc != 0:
        return rc
    print(line[-1] if line else "OK readme-contract selftest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
