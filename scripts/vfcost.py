#!/usr/bin/env python3
"""Material-only cost desk — grams × ILS/kg → ILS/unit.

No network. No send. No invented sale prices.
Missing grams → refuse (no silent zero).
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILAMENTS = ROOT / "packages" / "vfcost" / "FILAMENTS.json"
CARDS = ROOT / "packages" / "vfcost" / "CARDS.json"
QUANT = Decimal("0.01")
KG = Decimal("1000")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def parse_decimal(raw: str | None, label: str) -> Decimal:
    if raw is None or not str(raw).strip():
        raise ValueError(label)
    try:
        value = Decimal(str(raw).strip())
    except InvalidOperation as exc:
        raise ValueError(label) from exc
    if value <= 0:
        raise ValueError(label)
    return value


def material_ils(grams: Decimal, ils_per_kg: Decimal) -> Decimal:
    return (grams * ils_per_kg / KG).quantize(QUANT, rounding=ROUND_HALF_UP)


def filament_index(data: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for row in data.get("filaments") or []:
        for key in (row.get("id"), row.get("name"), row.get("nameHe")):
            token = (key or "").strip().lower()
            if token:
                out[token] = row
    return out


def verified_ils_per_kg(row: dict | None) -> Decimal | None:
    if not row:
        return None
    raw = row.get("ilsPerKg")
    if raw is None or not str(raw).strip():
        return None
    try:
        value = Decimal(str(raw).strip())
    except InvalidOperation:
        return None
    if value <= 0:
        return None
    return value


def resolve_filament(name: str | None) -> dict | None:
    if not name or not name.strip():
        return None
    data = load_json(FILAMENTS)
    found = filament_index(data).get(name.strip().lower())
    if found is None:
        raise KeyError(name.strip())
    return found


def refuse(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 2


def cmd_material(args: argparse.Namespace) -> int:
    try:
        grams = parse_decimal(args.grams, "grams")
    except ValueError:
        return refuse("חסר גרמים — אין עלות חומר. לא ממלאים אפס.")

    filament = None
    if args.filament:
        try:
            filament = resolve_filament(args.filament)
        except KeyError:
            return refuse(f"גליל לא ברשימה: {args.filament.strip()}")

    rate: Decimal | None = None
    if args.ils_per_kg is not None:
        try:
            rate = parse_decimal(args.ils_per_kg, "ils-per-kg")
        except ValueError:
            return refuse("חסר ILS/kg מאומת — אין עלות חומר. לא ממציאים.")
    else:
        rate = verified_ils_per_kg(filament)

    if rate is None:
        return refuse("חסר ILS/kg מאומת — אין עלות חומר. לא ממציאים.")

    unit = material_ils(grams, rate)
    spool = ""
    if filament:
        spool = f" · גליל {filament.get('name') or filament.get('id')}"
    print(
        f"עלות חומר: {unit} ILS/unit · {grams}g × {rate} ILS/kg{spool}"
    )
    print("לא מחיר מכירה")
    return 0


def cmd_filaments(_args: argparse.Namespace) -> int:
    data = load_json(FILAMENTS)
    print("גלילי רצפה")
    print(f"{'id':<10}{'שם':<12}ILS/kg")
    for row in data.get("filaments") or []:
        rate = (row.get("ilsPerKg") or "").strip() or "חסר"
        name = (row.get("nameHe") or row.get("name") or "—").strip()
        print(f"{(row.get('id') or '?'):<10}{name:<12}{rate}")
    print((data.get("formula") or "grams × ILS/kg ÷ 1000 = ILS/unit"))
    print("לא מחיר מכירה")
    return 0


def card_unit(card: dict) -> Decimal | None:
    try:
        grams = parse_decimal(str(card.get("grams") or ""), "grams")
        rate = parse_decimal(str(card.get("ilsPerKg") or ""), "ils-per-kg")
    except ValueError:
        return None
    return material_ils(grams, rate)


def cmd_cards(_args: argparse.Namespace) -> int:
    data = load_json(CARDS)
    cards = data.get("cards") or []
    print(f"כרטיסי עלות חומר: {len(cards)}")
    if not cards:
        print("אין כרטיס — חסר גרמים")
        print("לא מחיר מכירה")
        return 0
    for card in cards:
        label = (card.get("id") or card.get("job") or "?").strip()
        grams = (card.get("grams") or "").strip()
        if not grams:
            print(f"{label} חסר גרמים — אין שורה")
            continue
        unit = card_unit(card)
        if unit is None:
            print(f"{label} {grams}g · חסר ILS/kg — אין שורה")
            continue
        print(f"{label} עלות חומר: {unit} ILS/unit")
    print("לא מחיר מכירה")
    return 0


def cmd_brief(_args: argparse.Namespace) -> int:
    data = load_json(CARDS)
    cards = data.get("cards") or []
    ready: list[Decimal] = []
    missing_grams = 0
    missing_rate = 0
    for card in cards:
        grams = (card.get("grams") or "").strip()
        if not grams:
            missing_grams += 1
            continue
        unit = card_unit(card)
        if unit is None:
            missing_rate += 1
            continue
        ready.append(unit)

    if not cards:
        print("עלות חומר: אין כרטיס עם גרמים · בלי ₪ מכירה")
        return 0
    if not ready:
        extras: list[str] = []
        if missing_grams:
            extras.append("חסר גרמים")
        if missing_rate:
            extras.append("חסר ILS/kg")
        extra = " · ".join(extras) if extras else "אין שורה"
        print(f"עלות חומר: {extra} · בלי ₪ מכירה")
        return 0

    total = sum(ready, Decimal("0")).quantize(QUANT, rounding=ROUND_HALF_UP)
    print(
        f"עלות חומר: {len(ready)} כרטיסים · {total} ILS/unit סה״כ חומר · בלי ₪ מכירה"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Velvet Factory material-only cost (grams × ILS/kg)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    material = sub.add_parser(
        "material",
        help="grams × ILS/kg → ILS/unit (refuse if grams missing)",
    )
    material.add_argument("--grams", help="slicer grams (required)")
    material.add_argument("--ils-per-kg", dest="ils_per_kg", help="verified ILS per kg")
    material.add_argument("--filament", help="named spool: Ella / Rachel / Gefen")
    material.set_defaults(func=cmd_material)

    sub.add_parser("filaments", help="list named floor spools").set_defaults(
        func=cmd_filaments
    )
    sub.add_parser("cards", help="list material cards (empty until slice)").set_defaults(
        func=cmd_cards
    )
    sub.add_parser("brief", help="one Hebrew line for morning brief slot 02").set_defaults(
        func=cmd_brief
    )

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
