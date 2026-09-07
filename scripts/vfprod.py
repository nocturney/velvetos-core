#!/usr/bin/env python3
"""Print-done cards for morning brief slot 03 / 07.

No network. No send. HQ does not drive printers or invent floor scenes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "packages" / "vfprod" / "hq" / "cards"
SKIP = {"README.md", "PRINT-CARD-TEMPLATE.md"}


def list_cards() -> list[Path]:
    if not CARDS.is_dir():
        return []
    return sorted(
        p for p in CARDS.glob("*.md") if p.name not in SKIP
    )


def cmd_print_done(_args: argparse.Namespace) -> int:
    cards = list_cards()
    if not cards:
        print(
            "print.done: אין כרטיס רצפה\n"
            "HQ לא מצלם מדפסת · PREFLIGHT לפני שיבוץ · אין Publish מהבריף"
        )
        return 0
    ready = 0
    blocked = 0
    for path in cards:
        text = path.read_text(encoding="utf-8")
        if "חסר" in text and "proof על המיטה: כן" not in text:
            blocked += 1
        if "card_ready" in text or "draft" in text:
            ready += 1
    names = ", ".join(p.stem for p in cards[:5])
    extra = "…" if len(cards) > 5 else ""
    print(
        f"print.done: {len(cards)} כרטיסים ({names}{extra}) · מוכנים/טיוטה={ready} · חסום-גלם={blocked}\n"
        "אין חיבור למדפסת מ-HQ · תוכן אחרי PREFLIGHT · לא כפתור בריף"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Velvet Factory print-floor cards")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("print-done", help="brief line for print.done cards").set_defaults(func=cmd_print_done)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
