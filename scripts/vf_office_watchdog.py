#!/usr/bin/env python3
"""Thin wrapper — canonical office watchdog lives in vf_control_plane.py.

Do not keep a second authoritative inspector here.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vf_control_plane import cmd_watchdog  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true")
    p.add_argument("--write", action="store_true", help="Write report under vfops/hq/")
    args = p.parse_args()
    return int(cmd_watchdog(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
