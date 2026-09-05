#!/usr/bin/env python3
"""Validate standing IG publish calendar on vfgrowth. No network. No send."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "packages" / "vfgrowth" / "CALENDAR.md"
LEDGER = ROOT / "packages" / "vfgrowth" / "LEDGER.md"
HANDOFF = ROOT / "packages" / "vfgrowth" / "HANDOFF-he.md"
G003 = ROOT / "packages" / "vfgrowth" / "G003.md"
COPY = ROOT / "packages" / "vfcopy" / "G003.md"
COPY_ALT = ROOT / "packages" / "vfcopy" / "G003-alt.md"
STORIES = ROOT / "packages" / "vfcopy" / "hq" / "templates" / "ig-stories.md"
AGENTS = ROOT / "AGENTS.md"
ILS_NUMBER = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def assert_no_ils(path: Path) -> None:
    text = path.read_text()
    for m in ILS_NUMBER.finditer(text):
        snippet = text[max(0, m.start() - 20) : m.end() + 8]
        if "X ₪" in snippet:
            continue
        if re.search(r"(בלי|אין|לא)\s*₪|₪\s*רק", snippet):
            continue
        fail(f"possible invented ILS in {path.relative_to(ROOT)}: {snippet!r}")


def main() -> None:
    for path in (CAL, LEDGER, HANDOFF, G003, COPY, COPY_ALT, STORIES):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
        assert_no_ils(path)

    cal = CAL.read_text()
    for needle in (
        "16:00",
        "12:00",
        "20:30",
        "אין פיד",
        "36",
        "instagram.com",
        "G003",
        "G003-alt",
        "7.9.2026",
        "מוכן לשיבוץ",
        "משובץ",
        "VF-G003-reel.mp4",
        "vf-user-2026-08-30.mp4",
    ):
        if needle not in cal:
            fail(f"CALENDAR.md missing {needle!r}")
    if "Meta Suite" in cal and "לא Meta Suite" not in cal:
        fail("CALENDAR.md must forbid Meta Suite")
    if "שישי" not in cal or "שבת" not in cal:
        fail("CALENDAR.md must mention Friday/Saturday no-feed")

    ledger = LEDGER.read_text()
    for needle in (
        "DcqkjOLlYVX",
        "DcvuJLxCJgU",
        "Dc0cKegEbxd",
        "G001",
        "G002",
        "G005",
        "G003",
        "SoccerBall",
        "SoccerBall final_PLA_9h55m_20260715143622.mp4",
        "vf-user-2026-08-30.mp4",
        "vf-user-2026-08-30-9x16.mp4",
        "G003-alt",
        "VF-G003-reel.mp4",
        "VF-G003-cover.jpg",
        "VF-G003-caption.txt",
        "משובץ",
        "זמין מקומית",
        "חסום",
    ):
        if needle not in ledger:
            fail(f"LEDGER.md missing {needle!r}")

    handoff = HANDOFF.read_text()
    for needle in (
        "instagram.com",
        "חסום",
        "16:00",
        "12:00",
        "20:30",
        "לא סוויט",
        "מוכן לשיבוץ",
        "משובץ",
        "VF-G003-reel.mp4",
        "vf-user-2026-08-30.mp4",
        "G003-alt",
    ):
        if needle not in handoff:
            fail(f"HANDOFF-he.md missing {needle!r}")
    if "050-2517000" not in handoff:
        fail("HANDOFF-he.md must include WhatsApp CTA")
    if "שלחו DM" in handoff and "לא «שלחו DM»" not in handoff and "בלי «שלחו DM»" not in handoff:
        fail("HANDOFF-he.md must forbid שלחו DM")

    g003 = G003.read_text()
    if "משובץ" not in g003:
        fail("G003.md must mark G003-alt as scheduled")
    if "VF-G003-reel.mp4" not in g003:
        fail("G003.md must name Studio-cut reel path")
    if "מוכן לשיבוץ" not in g003:
        fail("G003.md must keep SoccerBall as optional unlock")
    if "זמין מקומית" not in g003:
        fail("G003.md must mark SoccerBall as locally available")
    if "G003-alt" not in g003:
        fail("G003.md must name G003-alt printer-reel track")
    if "SoccerBall" not in g003:
        fail("G003.md must name SoccerBall candidate")
    if "SoccerBall final_PLA_9h55m_20260715143622.mp4" not in g003:
        fail("G003.md must name the ledger SoccerBall filename")
    if "vf-user-2026-08-30.mp4" not in g003:
        fail("G003.md must name Grok machine process video")
    if "vf-user-2026-08-30-9x16.mp4" not in g003:
        fail("G003.md must name the 9x16 process video")
    stop = ROOT / "packages" / "vfcovers" / "g003" / "HANDOFF-he.md"
    if not stop.is_file():
        fail("missing vfcovers/g003/HANDOFF-he.md")
    stop_text = stop.read_text()
    for needle in (
        "SoccerBall final_PLA_9h55m_20260715143622.mp4",
        "vf-user-2026-08-30.mp4",
        "vf-user-2026-08-30-9x16.mp4",
        "מוכן לשיבוץ",
        "משובץ",
        "VF-G003-reel.mp4",
        "VF-G003-cover.jpg",
        "VF-G003-caption.txt",
        "G003-alt",
    ):
        if needle not in stop_text:
            fail(f"g003 HANDOFF must include {needle!r}")

    copy = COPY.read_text()
    if "050-2517000" not in copy:
        fail("vfcopy/G003.md must include WhatsApp CTA")
    if "שלחו DM" in copy and "לא «שלחו DM»" not in copy and "בלי «שלחו DM»" not in copy:
        fail("vfcopy/G003.md must not instruct שלחו DM")
    alt_text = COPY_ALT.read_text()
    if "050-2517000" not in alt_text:
        fail("vfcopy/G003-alt.md must include WhatsApp CTA")
    paste = alt_text.split("## להדבקה", 1)[-1] if "## להדבקה" in alt_text else ""
    if "כדור" in paste:
        fail("vfcopy/G003-alt.md paste block must not claim a soccer ball")
    if "שלחו DM" in alt_text and "לא «שלחו DM»" not in alt_text and "בלי «שלחו DM»" not in alt_text:
        fail("vfcopy/G003-alt.md must not instruct שלחו DM")

    stories = STORIES.read_text()
    if "20:30" not in stories or "050-2517000" not in stories:
        fail("ig-stories.md must lock 20:30 + WhatsApp CTA")

    if "check-vfgrowth.py" not in AGENTS.read_text():
        fail("AGENTS.md sensor table must list check-vfgrowth.py")

    print("OK standing calendar + ledger + handoff")


if __name__ == "__main__":
    main()
