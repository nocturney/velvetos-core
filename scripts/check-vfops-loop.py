#!/usr/bin/env python3
"""Validate the office activation loop. No network. No send."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "packages" / "vfops" / "LOOP.json"
CLI = ROOT / "scripts" / "vfops_loop.py"
PLAY = ROOT / "packages" / "vfops" / "hq" / "LOOP.md"
ORCHESTRA = ROOT / "constitution" / "ORCHESTRA.md"
INSTANCE = ROOT / "constitution" / "INSTANCE.md"
STUDIO = ROOT / "constitution" / "STUDIO.md"
ROUTINE = ROOT / "packages" / "vfops" / "ROUTINE.md"
HANDOFF = ROOT / "packages" / "vfgrowth" / "HANDOFF-he.md"
EDIT = ROOT / "packages" / "vfgrowth" / "EDIT-GATE.md"
CAL_OPS = ROOT / "packages" / "vfgrowth" / "CALENDAR-OPS.md"
AGENTS = ROOT / "AGENTS.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (LOOP, CLI, PLAY, ORCHESTRA, INSTANCE, STUDIO, ROUTINE, HANDOFF, EDIT, CAL_OPS):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    data = json.loads(LOOP.read_text())
    if data.get("name") != "vfops-loop":
        fail("LOOP.json name must be vfops-loop")
    ids = [p["id"] for p in data.get("packs") or []]
    if len(ids) != len(set(ids)):
        fail("LOOP.json duplicate pack ids")
    if "vfcost" not in ids or "vfsku" not in ids or "vfgrowth" not in ids:
        fail("LOOP.json must include vfcost, vfsku, vfgrowth")
    cost = next(p for p in data["packs"] if p["id"] == "vfcost")
    if cost.get("consumeOptional"):
        fail("vfcost CLI is on main — consume must be live, not optional")
    if "vfcost.py brief" not in (cost.get("consume") or ""):
        fail("vfcost consume must be vfcost.py brief")
    if cost.get("briefSlot") != "02":
        fail("vfcost briefSlot must be 02")
    if not (ROOT / "scripts" / "vfcost.py").is_file():
        fail("scripts/vfcost.py missing after rebase onto main")

    orch = ORCHESTRA.read_text()
    for needle in ("vfops_loop.py", "07:00", "FOLLOWER-GROWTH", "רף סוכנות"):
        if needle not in orch:
            fail(f"ORCHESTRA.md must mention {needle}")
    for path, needles in (
        (INSTANCE, ("רף סוכנות", "חצי-פק", "עברית")),
        (STUDIO, ("רף סוכנות", "JPEG גולמי", "לא שואלים", "VOICE.md")),
        (EDIT, ("JPEG גולמי", "Canva", "vfcovers")),
        (CAL_OPS, ("לא שואלים", "Google Calendar", "050-2517000")),
    ):
        text = path.read_text()
        for needle in needles:
            if needle not in text:
                fail(f"{path.name} must mention {needle}")

    if "vfops_loop.py" not in ROUTINE.read_text():
        fail("ROUTINE.md must run vfops_loop.py at 07:00")
    if "vfops_loop.py" not in HANDOFF.read_text():
        fail("HANDOFF-he.md must point at vfops_loop.py")
    if "G004" not in HANDOFF.read_text() or "vfcopy/G004.md" not in HANDOFF.read_text():
        fail("HANDOFF-he.md must open G004 pack")

    if "check-vfops-loop.py" not in AGENTS.read_text():
        fail("AGENTS.md sensor table must list check-vfops-loop.py")

    proc = subprocess.run(
        [sys.executable, str(CLI), "check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        fail(f"vfops_loop.py check: {proc.stderr or proc.stdout}")

    print("OK vfops-loop wired into orchestra+brief+handoff")


if __name__ == "__main__":
    main()
