#!/usr/bin/env python3
"""Validate standing IG publish calendar on existing vfgrowth/vfigos packs."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CALENDAR = ROOT / "packages" / "vfgrowth" / "CALENDAR.md"
RHYTHM = ROOT / "packages" / "vfgrowth" / "RHYTHM.md"
G003 = ROOT / "packages" / "vfgrowth" / "G003.md"
HANDOFF = ROOT / "packages" / "vfigos" / "HANDOFF-STANDING-he.md"
QUEUE = ROOT / "packages" / "vfigos" / "QUEUE.md"
ROUTINE = ROOT / "packages" / "vfops" / "ROUTINE.md"
COPY_G003 = ROOT / "packages" / "vfcopy" / "G003.md"
COPY_G006 = ROOT / "packages" / "vfcopy" / "G006.md"

NEEDLES_CALENDAR = (
    "MEDIA-NEEDED-FROM-CHRISTIAN",
    "Asia/Jerusalem",
    "VF-G003",
    "16:00",
    "12:00",
    "20:30",
    "אין פיד",
    "RHYTHM.md",
)
NEEDLES_RHYTHM = (
    "16:00",
    "12:00",
    "20:30",
    "שישי",
    "שבת",
    "36",
)
NEEDLES_HANDOFF = (
    "instagram.com",
    "Meta Suite",
    "MEDIA-NEEDED-FROM-CHRISTIAN",
    "050-2517000",
    "8.9.2026",
    "16:00",
)


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (CALENDAR, RHYTHM, G003, HANDOFF, QUEUE, ROUTINE, COPY_G003, COPY_G006):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    calendar = CALENDAR.read_text()
    for needle in NEEDLES_CALENDAR:
        if needle not in calendar:
            fail(f"CALENDAR.md missing {needle!r}")

    rhythm = RHYTHM.read_text()
    for needle in NEEDLES_RHYTHM:
        if needle not in rhythm:
            fail(f"RHYTHM.md missing {needle!r}")

    g003 = G003.read_text()
    if "MEDIA-NEEDED-FROM-CHRISTIAN" not in g003:
        fail("G003.md must flag MEDIA-NEEDED-FROM-CHRISTIAN")
    if "SoccerBall" not in g003:
        fail("G003.md must name SoccerBall candidate")

    handoff = HANDOFF.read_text()
    for needle in NEEDLES_HANDOFF:
        if needle not in handoff:
            fail(f"HANDOFF-STANDING-he.md missing {needle!r}")
    if "אוטו־DM" not in handoff and "אוטו-DM" not in handoff:
        fail("HANDOFF must still forbid auto-DM")

    if "CALENDAR.md" not in QUEUE.read_text():
        fail("QUEUE.md must point at standing CALENDAR.md")
    if "CALENDAR.md" not in ROUTINE.read_text():
        fail("vfops/ROUTINE.md must mention standing CALENDAR.md")

    print("OK standing-calendar vfgrowth+vfigos+vfcopy+vfops")


if __name__ == "__main__":
    main()
