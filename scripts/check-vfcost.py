#!/usr/bin/env python3
"""Validate vfcost material-only desk. No network. No send. No invented sale ₪."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packages" / "vfcost"
FILAMENTS = PACK / "FILAMENTS.json"
CARDS = PACK / "CARDS.json"
CLI = ROOT / "scripts" / "vfcost.py"
SKILL = PACK / "SKILL.md"
FLOOR = PACK / "FLOOR-CARD.md"
PLAY = PACK / "hq" / "PLAYBOOK.md"
CLI_DOC = PACK / "CLI.md"
BRIEF = ROOT / "packages" / "vfops" / "BRIEF.md"
SLOTS = ROOT / "packages" / "vfops" / "hq" / "BRIEF-SLOTS.md"
AGENTS = ROOT / "AGENTS.md"
LAYERS = ROOT / "packages" / "vfharness" / "layers.json"

REQUIRED_LOCKS = {
    "no-invented-sale-prices",
    "material-only",
    "missing-grams-refuse",
}
REQUIRED_SPOOLS = {"ella", "rachel", "gefen"}
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


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def main() -> None:
    for path in (FILAMENTS, CARDS, CLI, SKILL, FLOOR, PLAY, CLI_DOC, BRIEF, SLOTS):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    data = json.loads(FILAMENTS.read_text())
    if data.get("name") != "vfcost-filaments":
        fail("FILAMENTS.json name must be vfcost-filaments")
    if data.get("briefSlot") != "02":
        fail("FILAMENTS.json briefSlot must be 02")
    if "grams × ILS/kg" not in (data.get("formula") or ""):
        fail("FILAMENTS.json must document grams × ILS/kg formula")
    if "20.29" not in (data.get("examplePath") or "") or "5.07" not in (
        data.get("examplePath") or ""
    ):
        fail("FILAMENTS.json must keep the 20.29g × 250 → 5.07 example path")

    locks = set(data.get("locks") or [])
    missing = REQUIRED_LOCKS - locks
    if missing:
        fail(f"FILAMENTS.json missing locks {sorted(missing)}")

    ids = {(row.get("id") or "").strip().lower() for row in (data.get("filaments") or [])}
    if ids != REQUIRED_SPOOLS:
        fail(f"FILAMENTS.json must be Ella/Rachel/Gefen, got {sorted(ids)}")
    for row in data.get("filaments") or []:
        if (row.get("ilsPerKg") or "").strip():
            fail(
                f"filament {row.get('id')} has ilsPerKg — do not store an invented rate"
            )

    cards = json.loads(CARDS.read_text())
    if cards.get("name") != "vfcost-material-cards":
        fail("CARDS.json name must be vfcost-material-cards")
    if cards.get("briefSlot") != "02":
        fail("CARDS.json briefSlot must be 02")
    if cards.get("cards") not in ([], None) and cards.get("cards"):
        for card in cards["cards"]:
            if not (card.get("grams") or "").strip():
                fail("CARDS.json card missing grams must not be treated as ready")

    example = run_cli("material", "--grams", "20.29", "--ils-per-kg", "250")
    if example.returncode != 0:
        fail(f"example material path failed: {example.stderr or example.stdout}")
    out = example.stdout
    if "5.07" not in out:
        fail(f"example path must yield 5.07 ILS/unit, got {out!r}")
    if "לא מחיר מכירה" not in out:
        fail("material output must say לא מחיר מכירה")
    if re.search(r"מחיר מכירה:\s*\d", out):
        fail("material output must not invent a sale price")

    named = run_cli(
        "material",
        "--grams",
        "20.29",
        "--ils-per-kg",
        "250",
        "--filament",
        "Ella",
    )
    if named.returncode != 0 or "Ella" not in named.stdout or "5.07" not in named.stdout:
        fail("named Ella path must keep the 5.07 example")

    no_grams = run_cli("material", "--ils-per-kg", "250")
    if no_grams.returncode == 0:
        fail("missing grams must refuse")
    if "חסר גרמים" not in (no_grams.stderr or ""):
        fail("missing grams must say חסר גרמים")
    if "0.00" in (no_grams.stdout or "") or "0 ILS" in (no_grams.stdout or ""):
        fail("missing grams must not print a silent zero cost")

    zero = run_cli("material", "--grams", "0", "--ils-per-kg", "250")
    if zero.returncode == 0:
        fail("zero grams must refuse")

    no_rate = run_cli("material", "--grams", "20.29", "--filament", "Ella")
    if no_rate.returncode == 0:
        fail("filament without verified ILS/kg must refuse")
    if "ILS/kg" not in (no_rate.stderr or ""):
        fail("missing ILS/kg must mention ILS/kg")

    unknown = run_cli("material", "--grams", "20.29", "--ils-per-kg", "250", "--filament", "nope")
    if unknown.returncode == 0:
        fail("unknown filament must refuse")

    brief = run_cli("brief")
    if brief.returncode != 0:
        fail(f"brief failed: {brief.stderr or brief.stdout}")
    if "עלות חומר" not in brief.stdout:
        fail("brief must print עלות חומר")
    if "₪ מכירה" not in brief.stdout and "לא מחיר מכירה" not in brief.stdout:
        fail("brief must refuse a sale price")
    if re.search(r"\d[\d.,]*\s*₪", brief.stdout) and "X ₪" not in brief.stdout:
        fail("brief must not invent a numbered ₪")

    cli_src = CLI.read_text()
    if "חסר גרמים" not in cli_src:
        fail("vfcost.py must contain חסר גרמים")
    if 'add_parser("material"' not in cli_src and 'add_parser(\n        "material"' not in cli_src:
        fail("vfcost.py must expose a material subcommand")
    if 'add_parser("brief"' not in cli_src:
        fail("vfcost.py must expose a brief subcommand")

    skill = SKILL.read_text()
    for needle in ("vfcost.py", "עלות חומר", "לא מחיר מכירה", "חסר גרמים"):
        if needle not in skill:
            fail(f"SKILL.md must mention {needle}")

    floor = FLOOR.read_text()
    for needle in ("גרם", "X ₪", "vfcost.py", "עלות חומר"):
        if needle not in floor:
            fail(f"FLOOR-CARD.md must mention {needle}")

    play = PLAY.read_text()
    for needle in ("גרם ×", "vfcost.py", "עלות חומר ≠ מחיר מכירה"):
        if needle not in play:
            fail(f"hq/PLAYBOOK.md must mention {needle}")

    cli_doc = CLI_DOC.read_text()
    for needle in (
        "python3 scripts/vfcost.py brief",
        "BRIEF-SLOTS",
        "חריץ 02",
        "20.29",
        "5.07",
        "בלי ₪ מכירה",
    ):
        if needle not in cli_doc:
            fail(f"CLI.md must mention {needle}")

    if "vfcost.py brief" not in BRIEF.read_text():
        fail("vfops/BRIEF.md must hook slot 02 to vfcost.py brief")
    if "vfcost.py brief" not in SLOTS.read_text():
        fail("BRIEF-SLOTS.md must hook slot 02 to vfcost.py brief")

    if "check-vfcost.py" not in AGENTS.read_text():
        fail("AGENTS.md sensors table must list check-vfcost.py")

    layers = json.loads(LAYERS.read_text())
    scripts = {row.get("script") for row in (layers.get("sensors") or [])}
    if "scripts/check-vfcost.py" not in scripts:
        fail("layers.json sensors must include scripts/check-vfcost.py")

    for path in (FILAMENTS, CARDS, SKILL, FLOOR, PLAY, CLI_DOC):
        assert_no_ils(path)

    print("OK vfcost material-cli example=5.07 grams-refuse=1 brief-hook=02")


if __name__ == "__main__":
    main()
