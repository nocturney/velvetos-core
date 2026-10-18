#!/usr/bin/env python3
"""Delegate to the check-all sensor so this phase2 path cannot drift."""
from __future__ import annotations

import runpy
from pathlib import Path

TARGET = Path(__file__).resolve().parents[4] / "scripts" / "check-veto-inventory.py"
runpy.run_path(str(TARGET), run_name="__main__")
