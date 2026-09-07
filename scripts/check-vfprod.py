#!/usr/bin/env python3
"""Validate floor fleet routing + maintenance snapshot. No network. No Print. No invented ₪."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packages" / "vfprod"
FLEET = PACK / "FLEET.json"
ROUTING = PACK / "ROUTING.md"
MAINT = PACK / "MAINTENANCE.md"
SNAP = PACK / "data" / "maintenance-snapshot.json"
CLI = ROOT / "scripts" / "vfprod.py"
FLOOR = PACK / "FLOOR.md"
WATCH = PACK / "WATCHTOWER.md"
SKILL = PACK / "SKILL.md"
BRIEF = ROOT / "packages" / "vfops" / "BRIEF.md"
SLOTS = ROOT / "packages" / "vfops" / "hq" / "BRIEF-SLOTS.md"
AGENTS = ROOT / "AGENTS.md"
LAYERS = ROOT / "packages" / "vfharness" / "layers.json"
EVENTS = ROOT / "packages" / "velvetos" / "schema" / "events.catalog.json"

REQUIRED_IDS = {"bambu-a", "bambu-b", "snapmaker-u1", "elegoo-centauri"}
REQUIRED_MATERIALS = {"PLA", "PETG", "ABS", "ASA", "Nylon", "PEBA"}
REQUIRED_LOCKS = {
    "no-print-from-hq",
    "no-invented-prices",
    "no-invented-telemetry",
    "floor-assigns",
}
ILS_NUMBER = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def assert_no_ils(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for m in ILS_NUMBER.finditer(text):
        snippet = text[max(0, m.start() - 20) : m.end() + 8]
        if "X ₪" in snippet:
            continue
        if re.search(r"(בלי|אין|לא)\s*₪|₪\s*רק", snippet):
            continue
        fail(f"possible invented ILS in {path.relative_to(ROOT)}: {snippet!r}")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def main() -> None:
    for path in (FLEET, ROUTING, MAINT, SNAP, CLI, FLOOR, WATCH, SKILL, BRIEF, SLOTS):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    data = json.loads(FLEET.read_text(encoding="utf-8"))
    if data.get("name") != "vfprod-fleet":
        fail("FLEET.json name must be vfprod-fleet")
    if data.get("hqPrints") is not False:
        fail("FLEET.json hqPrints must be false")
    if data.get("briefSlot") != "03":
        fail("FLEET.json briefSlot must be 03")
    locks = set(data.get("locks") or [])
    missing = REQUIRED_LOCKS - locks
    if missing:
        fail(f"FLEET.json missing locks {sorted(missing)}")
    mats = set(data.get("materials") or [])
    if not REQUIRED_MATERIALS <= mats:
        fail(f"FLEET.json must list {sorted(REQUIRED_MATERIALS)}")
    printers = data.get("printers") or []
    if len(printers) != 4:
        fail(f"FLEET.json must have 4 beds, got {len(printers)}")
    ids = {p.get("id") for p in printers}
    if ids != REQUIRED_IDS:
        fail(f"FLEET.json ids must be {sorted(REQUIRED_IDS)}, got {sorted(ids)}")
    for row in printers:
        if (row.get("model") or "").strip() in {"X1C", "P1S", "X1 Carbon"}:
            fail("do not invent a Bambu model number")

    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    if snap.get("name") != "vfprod-maintenance-snapshot":
        fail("maintenance-snapshot.json name mismatch")
    if (snap.get("updatedAt") or "").strip() and not (snap.get("printers") or []):
        fail("snapshot with updatedAt must list printers or stay empty")

    fleet = run_cli("fleet")
    if fleet.returncode != 0:
        fail(f"vfprod.py fleet: {fleet.stderr or fleet.stdout}")
    if "hq_prints=False" not in fleet.stdout and "hq_prints=false" not in fleet.stdout:
        fail("fleet must print hq_prints=false")

    route = run_cli("route", "--material", "ASA")
    if route.returncode != 0:
        fail(f"route ASA failed: {route.stderr or route.stdout}")
    if "hq_prints: false" not in route.stdout:
        fail("route must refuse HQ print")
    if "Bambu" not in route.stdout:
        fail("ASA should prefer Bambu")

    outdoor = run_cli("route", "--strength", "outdoor")
    if outdoor.returncode != 0 or "ASA" not in outdoor.stdout.upper():
        fail("strength outdoor must map to ASA")

    bad = run_cli("route", "--material", "unobtanium")
    if bad.returncode == 0:
        fail("unknown material must refuse")

    rem = run_cli("remaining", "--grams", "80", "--filament", "Ella")
    if rem.returncode != 0:
        fail(f"remaining empty spool must still run: {rem.stderr or rem.stdout}")
    if "אין ספירת גרם" not in rem.stdout:
        fail("empty remainingGrams must say אין ספירת גרם")

    night = run_cli("remaining", "--grams", "0", "--filament", "Ella")
    if night.returncode == 0:
        fail("zero grams remaining check must refuse")

    maint = run_cli("maintain")
    if maint.returncode != 0:
        fail(f"maintain failed: {maint.stderr or maint.stdout}")
    if "אין ספירת Edge" not in maint.stdout:
        fail("empty snapshot must say אין ספירת Edge")

    brief = run_cli("brief")
    if brief.returncode != 0:
        fail(f"brief failed: {brief.stderr or brief.stdout}")
    if "אין Print" not in brief.stdout:
        fail("brief must say אין Print מ-HQ")

    routing = ROUTING.read_text(encoding="utf-8")
    for needle in ("hq_prints", "ASA", "PEBA", "Nylon", "WATCHTOWER.md", "G-code"):
        if needle not in routing:
            fail(f"ROUTING.md must mention {needle}")

    maint_doc = MAINT.read_text(encoding="utf-8")
    for needle in ("print.maintenance_due", "דיזה", "Watchtower", "אין ספירה"):
        if needle not in maint_doc:
            fail(f"MAINTENANCE.md must mention {needle}")

    if "vfprod.py" not in SKILL.read_text(encoding="utf-8"):
        fail("vfprod/SKILL.md must mention vfprod.py")
    if "ROUTING.md" not in FLOOR.read_text(encoding="utf-8"):
        fail("FLOOR.md must point at ROUTING.md")
    if "WATCHTOWER.md" not in FLOOR.read_text(encoding="utf-8"):
        fail("FLOOR.md must keep WATCHTOWER.md")

    if "vfprod.py" not in BRIEF.read_text(encoding="utf-8"):
        fail("BRIEF.md must hook slot 03 to vfprod.py")
    if "vfprod.py" not in SLOTS.read_text(encoding="utf-8"):
        fail("BRIEF-SLOTS.md must hook slot 03 to vfprod.py")

    if "check-vfprod.py" not in AGENTS.read_text(encoding="utf-8"):
        fail("AGENTS.md sensors table must list check-vfprod.py")

    layers = json.loads(LAYERS.read_text(encoding="utf-8"))
    scripts = {row.get("script") for row in (layers.get("sensors") or [])}
    if "scripts/check-vfprod.py" not in scripts:
        fail("layers.json sensors must include scripts/check-vfprod.py")

    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    ids = {e.get("id") for e in (events.get("events") or [])}
    for need in ("print.maintenance_due", "print.route_suggested", "print.filament_short"):
        if need not in ids:
            fail(f"events.catalog.json missing {need}")

    for path in (FLEET, ROUTING, MAINT, SNAP, SKILL):
        assert_no_ils(path)

    print("OK vfprod fleet=4 hq_prints=false remaining-empty=1 maintain-empty=1")


if __name__ == "__main__":
    main()
