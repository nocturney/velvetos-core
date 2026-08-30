#!/usr/bin/env python3
"""Validate the Velvet Factory desk overlay against The Agency catalog."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / ".cursor" / "vf-desk.json"
AGENCY = ROOT / ".cursor" / "agency-agents.json"
RULE = ROOT / ".cursor" / "rules" / "velvet-factory-desk.mdc"
MANIFEST = ROOT / "packages" / "manifest.json"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (DESK, AGENCY, RULE, MANIFEST):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    desk = json.loads(DESK.read_text())
    agency = json.loads(AGENCY.read_text())
    manifest = json.loads(MANIFEST.read_text())

    slugs = {a["slug"] for a in agency.get("agents", [])}
    packs = {p["name"] for p in manifest.get("packs", [])}

    if not slugs:
        fail("agency catalog has no agents")

    text = RULE.read_text()
    if "alwaysApply: true" not in text:
        fail("velvet-factory-desk.mdc must be alwaysApply: true")
    if "send_message" not in text:
        fail("desk rule must forbid Gmail send_message")

    desk_slugs: list[str] = []
    for row in desk.get("desk", []):
        slug = row.get("slug")
        if not slug:
            fail("desk row missing slug")
        desk_slugs.append(slug)
        if slug not in slugs:
            fail(f"desk slug not in Agency catalog: {slug}")
        for pack in row.get("packs", []):
            if pack not in packs:
                fail(f"{slug} references unknown pack {pack}")

    for seat in desk.get("seats", []):
        for slug in seat.get("specialists", []):
            if slug not in slugs:
                fail(f"seat {seat.get('id')} unknown specialist {slug}")
            if slug not in desk_slugs:
                fail(f"seat {seat.get('id')} specialist {slug} is not on the desk list")
        for pack in seat.get("packs", []):
            if pack not in packs:
                fail(f"seat {seat.get('id')} unknown pack {pack}")

    for rel in desk.get("skills", []):
        if not (ROOT / rel).is_file():
            fail(f"missing skill {rel}")

    print(
        f"OK desk={len(desk_slugs)} seats={len(desk['seats'])} "
        f"agency={len(slugs)} packs={len(packs)}"
    )


if __name__ == "__main__":
    main()
