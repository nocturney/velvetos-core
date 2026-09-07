#!/usr/bin/env python3
"""Floor fleet helpers: recommend a bed, check spool remainder, maintenance line.

No network. No send. No Print from HQ. No invented ₪ or telemetry.
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLEET = ROOT / "packages" / "vfprod" / "FLEET.json"
SNAP = ROOT / "packages" / "vfprod" / "data" / "maintenance-snapshot.json"
FILAMENTS = ROOT / "packages" / "vfcost" / "FILAMENTS.json"

MATERIALS = {
    "pla": {
        "prefer": ["bambu-a", "bambu-b", "elegoo-centauri", "snapmaker-u1"],
        "note": "כללי — אדם בוחר מיטה פנויה",
    },
    "petg": {
        "prefer": ["bambu-a", "bambu-b", "elegoo-centauri"],
        "note": "עמיד — Bambu או Elegoo",
    },
    "abs": {
        "prefer": ["bambu-a", "bambu-b"],
        "note": "סגירה + פילטר",
    },
    "asa": {
        "prefer": ["bambu-a", "bambu-b"],
        "note": "חוץ/UV — Bambu סגורה + פילטר",
    },
    "nylon": {
        "prefer": ["bambu-a", "bambu-b"],
        "note": "הנדסי — יבש + טמפ גבוהה, Bambu סגורה",
    },
    "peba": {
        "prefer": ["bambu-a", "bambu-b"],
        "note": "גמיש — נתיב TPU ב-Bambu; Snapmaker רק אם הרצפה אישרה",
    },
}

STRENGTH = {
    "outdoor": "asa",
    "uv": "asa",
    "flex": "peba",
    "flexible": "peba",
    "engineering": "nylon",
    "heat": "nylon",
    "durable": "petg",
    "general": "pla",
}


def fail(msg: str, code: int = 2) -> int:
    print(msg, file=sys.stderr)
    return code


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def printer_label(fleet: dict, pid: str) -> str:
    for row in fleet.get("printers") or []:
        if row.get("id") == pid:
            brand = (row.get("brand") or "").strip() or pid
            model = (row.get("model") or "").strip()
            return f"{brand} {model}".strip() if model else brand
    return pid


def cmd_fleet(_args: argparse.Namespace) -> int:
    data = load_json(FLEET)
    printers = data.get("printers") or []
    print(f"צי רצפה · {len(printers)} מיטות · hq_prints=false")
    print(f"{'id':<18}{'מותג':<16}פרוטוקול Watchtower")
    for row in printers:
        proto = row.get("watchtowerProtocol") or "unknown"
        print(f"{row.get('id', '?'):<18}{(row.get('brand') or ''):<16}{proto}")
    print("הקצאה: אדם על הרצפה. HQ לא דוחף G-code.")
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    material = (args.material or "").strip().lower()
    strength = (args.strength or "").strip().lower()
    if strength and not material:
        material = STRENGTH.get(strength, "")
        if not material:
            return fail(f"חוזק לא ממופה: {args.strength.strip()} — outdoor/flex/engineering/durable/general")
    if not material:
        return fail("חסר חומר — --material PLA|PETG|ABS|ASA|Nylon|PEBA")
    spec = MATERIALS.get(material)
    if spec is None:
        return fail(f"חומר לא בצי: {args.material.strip()}")
    fleet = load_json(FLEET)
    prefer = spec["prefer"]
    first = prefer[0] if prefer else ""
    label = printer_label(fleet, first)
    print(
        f"המלצת מיטה: {label} ({first}) · חומר {material.upper()} · {spec['note']}"
    )
    print("hq_prints: false · אדם על המיטה לוחץ Print · Watchtower=Edge אם נרכש")
    return 0


def cmd_remaining(args: argparse.Namespace) -> int:
    raw_grams = (args.grams or "").strip()
    if not raw_grams:
        return fail("חסר גרמים מסלייס — --grams")
    try:
        grams = Decimal(raw_grams)
    except InvalidOperation:
        return fail("גרמים לא מספר")
    if grams <= 0:
        return fail("גרמים חייבים להיות > 0")
    name = (args.filament or "").strip()
    data = load_json(FILAMENTS)
    found = None
    if name:
        key = name.lower()
        for row in data.get("filaments") or []:
            tokens = {
                (row.get("id") or "").strip().lower(),
                (row.get("name") or "").strip().lower(),
                (row.get("nameHe") or "").strip().lower(),
            }
            if key in tokens:
                found = row
                break
        if found is None:
            return fail(f"גליל לא ברשימה: {name}")
    else:
        return fail("חסר שם גליל — --filament Ella|Rachel|Gefen")
    remaining_raw = (found.get("remainingGrams") or "").strip()
    spool_name = found.get("name") or found.get("id")
    if not remaining_raw:
        print(
            f"גליל {spool_name}: אין ספירת גרם · לא מדפיסים לילה בלי משקל גליל מאומת"
        )
        return 0
    try:
        remaining = Decimal(remaining_raw)
    except InvalidOperation:
        return fail(f"יתרת גרם בגליל {spool_name} לא מספר מאומת")
    if remaining < grams:
        print(
            f"חסר פילמנט: סלייס {grams}g > יתרת {spool_name} {remaining}g · חוסמים הדפסת לילה"
        )
        return 0
    print(
        f"פילמנט מספיק: סלייס {grams}g ≤ יתרת {spool_name} {remaining}g · hq_prints=false"
    )
    return 0


def cmd_maintain(_args: argparse.Namespace) -> int:
    data = load_json(SNAP)
    printers = data.get("printers") or []
    if not printers or not (data.get("updatedAt") or "").strip():
        print("תחזוקה: אין ספירת Edge · לא מנחשים טמפ/רטט/שעות")
        return 0
    alerts: list[str] = []
    for row in printers:
        pid = row.get("id") or "?"
        temp = (row.get("tempDeviation") or "").strip()
        dupes = row.get("errorDupes") or 0
        vibe = (row.get("vibration") or "").strip()
        nozzle = (row.get("nozzleHoursSinceClean") or "").strip()
        if temp:
            alerts.append(f"{pid} סטיית טמפ={temp}")
        if isinstance(dupes, int) and dupes > 0:
            alerts.append(f"{pid} כפילות שגיאות={dupes}")
        if vibe:
            alerts.append(f"{pid} רטט={vibe}")
        if nozzle:
            alerts.append(f"{pid} דיזה שעות={nozzle}")
        if row.get("axisLubeDue") is True:
            alerts.append(f"{pid} שימון צירים")
        if row.get("filterDue") is True:
            alerts.append(f"{pid} פילטר")
    if not alerts:
        print("תחזוקה: סנאפשוט יש · אין חריגה רשומה · ניקוי/שימון לפי כרטיס Print-Done")
        return 0
    print("תחזוקה לפני עבודה מורכבת: " + " · ".join(alerts))
    return 0


def cmd_brief(_args: argparse.Namespace) -> int:
    fleet = load_json(FLEET)
    n = len(fleet.get("printers") or [])
    snap = load_json(SNAP)
    if not (snap.get("updatedAt") or "").strip():
        maint = "תחזוקה: אין ספירת Edge"
    else:
        maint = "תחזוקה: יש סנאפשוט רצפה"
    print(
        f"צי: {n} מיטות · ניתוב לפי חומר ב-vfprod.py route · {maint} · אין Print מ-HQ"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Velvet Factory floor fleet (recommend only)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fleet", help="list the four beds").set_defaults(func=cmd_fleet)
    route = sub.add_parser("route", help="recommend a bed from material/strength")
    route.add_argument("--material", default="")
    route.add_argument("--strength", default="", help="outdoor|flex|engineering|durable|general")
    route.set_defaults(func=cmd_route)
    rem = sub.add_parser("remaining", help="slice grams vs verified spool remainder")
    rem.add_argument("--grams", required=True)
    rem.add_argument("--filament", required=True)
    rem.set_defaults(func=cmd_remaining)
    sub.add_parser("maintain", help="morning-brief maintenance line from snapshot").set_defaults(
        func=cmd_maintain
    )
    sub.add_parser("brief", help="one Hebrew line for morning brief slot 03").set_defaults(
        func=cmd_brief
    )
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
