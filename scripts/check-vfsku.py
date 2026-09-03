#!/usr/bin/env python3
"""Validate recurring SKU shelf. No network. No send. No invented names or ₪."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELF = ROOT / "packages" / "vfsku" / "SHELF.json"
GATE = ROOT / "packages" / "vfsku" / "GATE.md"
LAB = ROOT / "packages" / "vfsku" / "LAB.md"
FIRST = ROOT / "packages" / "vfsku" / "FIRST-PRINT.md"
CARDS = ROOT / "packages" / "vfsku" / "CARDS.md"
SHOP_CLOSE = ROOT / "packages" / "vfprod" / "SHOP-CLOSE.md"
CONVERT_PATH = ROOT / "packages" / "vfconvert" / "PATH.md"
CLI = ROOT / "scripts" / "vfsku.py"
BRIEF = ROOT / "packages" / "vfops" / "BRIEF.md"
SLOTS = ROOT / "packages" / "vfops" / "hq" / "BRIEF-SLOTS.md"
LICENSE = ROOT / "packages" / "vlicense" / "GATE.md"

ALLOWED_STATUS = {
    "empty",
    "waiting-license",
    "waiting-slice",
    "lab",
    "ready",
    "blocked",
}
REQUIRED_LOCKS = {
    "no-invented-prices",
    "no-invented-sku-names",
    "no-batch-without-lead-price",
    "pickup-sderot-only",
    "israeli-brand-stop",
}
ILS_NUMBER = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")
NAMED_FIELDS = ("sourceUrl", "license", "licenseChecked")
READY_FIELDS = NAMED_FIELDS + ("sliceGrams", "sliceMinutes")


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
    for path in (SHELF, GATE, LAB, FIRST, CARDS, SHOP_CLOSE, CONVERT_PATH, CLI, BRIEF, SLOTS, LICENSE):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    data = json.loads(SHELF.read_text())
    if data.get("name") != "vfsku-shelf":
        fail("SHELF.json name must be vfsku-shelf")
    if data.get("maxSlots") != 5:
        fail("SHELF.json maxSlots must be 5")
    if data.get("briefSlot") != "03":
        fail("SHELF.json briefSlot must be 03")

    locks = set(data.get("locks") or [])
    missing = REQUIRED_LOCKS - locks
    if missing:
        fail(f"SHELF.json missing locks {sorted(missing)}")

    slots = data.get("slots") or []
    if len(slots) != 5:
        fail(f"SHELF.json must have 5 slots, got {len(slots)}")

    ids: set[int] = set()
    for slot in slots:
        sid = slot.get("id")
        if sid not in range(1, 6):
            fail(f"slot id out of 1–5: {sid}")
        if sid in ids:
            fail(f"duplicate slot id {sid}")
        ids.add(sid)
        status = slot.get("status")
        if status not in ALLOWED_STATUS:
            fail(f"slot {sid} bad status {status!r}")
        name = (slot.get("name") or "").strip()
        if status == "empty" and name:
            fail(f"slot {sid} empty but has a name")
        if name:
            for field in NAMED_FIELDS:
                if not (slot.get(field) or "").strip():
                    fail(f"slot {sid} named but missing {field}")
        if status == "ready":
            if not name:
                fail(f"slot {sid} ready but name empty")
            for field in READY_FIELDS:
                if not (slot.get(field) or "").strip():
                    fail(f"slot {sid} ready but missing {field}")
        if slot.get("israeliBrandStop") is True and status not in {"blocked", "empty"}:
            fail(f"slot {sid} israeliBrandStop must be blocked")

    gate = GATE.read_text()
    for needle in ("SHELF.json", "FIRST-PRINT.md", "vfsku.py", "הורדה ≠"):
        if needle not in gate:
            fail(f"GATE.md must mention {needle}")

    first = FIRST.read_text()
    for needle in ("SHELF.json", "vlicense", "בלי חומרה", "python3 scripts/vfsku.py", "SHOP-CLOSE.md"):
        if needle not in first:
            fail(f"FIRST-PRINT.md must mention {needle}")

    shop_close = SHOP_CLOSE.read_text()
    for needle in ("SHELF.json", "vfsku.py shop", "אין ספירה", "PATH.md"):
        if needle not in shop_close:
            fail(f"SHOP-CLOSE.md must mention {needle}")

    convert_path = CONVERT_PATH.read_text()
    for needle in ("SHELF.json", "מדף", "מינימום התאמה", "vfsku.py shop"):
        if needle not in convert_path:
            fail(f"vfconvert/PATH.md must mention shelf-first needle: {needle}")

    cli_src = CLI.read_text()
    if 'add_parser("shop"' not in cli_src and "add_parser('shop'" not in cli_src:
        fail("vfsku.py must expose a shop subcommand")

    lab = LAB.read_text()
    if "print-in-place" not in lab.lower() and "קופסה" not in lab:
        fail("LAB.md must keep a print-in-place / box direction")
    if "חומרה" not in lab:
        fail("LAB.md must flag hardware as yellow")

    license_gate = LICENSE.read_text()
    if "Commercial License" not in license_gate and "מנוי יוצר" not in license_gate:
        fail("vlicense/GATE.md must mention MakerWorld commercial membership")
    if "הורדה" not in license_gate:
        fail("vlicense/GATE.md must say download is not a license")

    brief = BRIEF.read_text()
    if "vfsku.py" not in brief:
        fail("vfops/BRIEF.md must hook slot 03 to vfsku.py")
    if "vfsku.py" not in SLOTS.read_text():
        fail("BRIEF-SLOTS.md must hook slot 03 to vfsku.py")

    for path in (SHELF, GATE, LAB, FIRST, CARDS, SHOP_CLOSE):
        assert_no_ils(path)

    print("OK vfsku shelf=5 first-print=1 brief-hook=03 shop-close=1")


if __name__ == "__main__":
    main()
