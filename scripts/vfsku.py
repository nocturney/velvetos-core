#!/usr/bin/env python3
"""Recurring SKU shelf — status for the morning brief.

No network. No send. No invented names or ₪.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELF = ROOT / "packages" / "vfsku" / "SHELF.json"
READY = "ready"


def load_shelf() -> dict:
    return json.loads(SHELF.read_text())


def slot_name(slot: dict) -> str:
    name = (slot.get("name") or "").strip()
    return name if name else "—"


def cmd_shelf(_args: argparse.Namespace) -> int:
    data = load_shelf()
    slots = data.get("slots") or []
    print("מדף חוזר · 5 מקומות")
    print(f"{'#':<3}{'סטטוס':<18}שם")
    counts: Counter[str] = Counter()
    for slot in slots:
        status = slot.get("status") or "empty"
        counts[status] += 1
        print(f"{slot.get('id', '?'):<3}{status:<18}{slot_name(slot)}")
    parts = [f"{key}={counts.get(key, 0)}" for key in (data.get("statusValues") or [])]
    print(" ".join(parts) if parts else f"ready={counts.get(READY, 0)}")
    return 0


def cmd_brief(_args: argparse.Namespace) -> int:
    data = load_shelf()
    slots = data.get("slots") or []
    total = len(slots)
    ready = sum(1 for s in slots if s.get("status") == READY)
    waiting_license = sum(1 for s in slots if s.get("status") == "waiting-license")
    waiting_slice = sum(1 for s in slots if s.get("status") == "waiting-slice")
    lab = sum(1 for s in slots if s.get("status") == "lab")
    blocked = sum(1 for s in slots if s.get("status") == "blocked")
    line = f"מדף חוזר: {ready}/{total} כרטיסים אחרי שער+סלייס"
    extras: list[str] = []
    if waiting_license:
        extras.append(f"{waiting_license} ממתין לרישיון")
    if waiting_slice:
        extras.append(f"{waiting_slice} ממתין לסלייס")
    if lab:
        extras.append(f"{lab} במעבדה")
    if blocked:
        extras.append(f"{blocked} חסום")
    if extras:
        line = f"{line} · {' · '.join(extras)}"
    if ready == 0:
        line = f"{line} · אין שם להציע"
    print(line)
    return 0


def cmd_shop(_args: argparse.Namespace) -> int:
    data = load_shelf()
    slots = data.get("slots") or []
    ready_slots = [s for s in slots if s.get("status") == READY]
    print("חנות מחר")
    print(f"מדף: {len(ready_slots)}/{len(slots)} ready")
    if not ready_slots:
        print("אין כרטיס להציע — לא ממציאים שם")
    else:
        for slot in ready_slots:
            count = (slot.get("shelfCount") or "").strip() or "אין ספירה"
            print(f"{slot.get('id')} {slot_name(slot)} מלאי={count}")
    print("סגירה: packages/vfprod/SHOP-CLOSE.md")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Velvet Factory recurring SKU shelf")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("shelf", help="print the 5-slot table").set_defaults(func=cmd_shelf)
    sub.add_parser("brief", help="one Hebrew line for morning brief slot 03").set_defaults(func=cmd_brief)
    sub.add_parser("shop", help="tomorrow-shop line: ready slots only, no invented names").set_defaults(func=cmd_shop)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
