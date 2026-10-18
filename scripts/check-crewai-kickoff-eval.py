#!/usr/bin/env python3
"""Sensor: offline CrewAI kickoff eval. No model, no network, no promptfoo."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from office_v2_crewai.kickoff_eval import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["--self-test"]))
