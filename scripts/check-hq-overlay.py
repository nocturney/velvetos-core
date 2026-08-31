#!/usr/bin/env python3
"""Validate ChatGPT-share embed: existing packs only, overlays present, no invented ILS."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "packages/manifest.json").read_text())
MAP = json.loads((ROOT / "packages/chatgpt-embed-map.json").read_text())
PACK_NAMES = {p["name"] for p in MANIFEST["packs"]}

ALLOWED_PACKS = PACK_NAMES | {"constitution"}
ILS_NUMBER = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")
PHONE_OK = re.compile(r"050-2517000")
X_ILS_OK = re.compile(r"\bX\s*₪")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if MAP["rule"].find("existing") < 0:
        fail("map rule must say embed into existing packs")

    for agent in MAP["agents"]:
        pack = agent["pack"]
        if pack not in ALLOWED_PACKS:
            fail(f"new/unknown pack in map: {pack}")
        if pack != "constitution" and pack not in PACK_NAMES:
            fail(f"map pack not in manifest: {pack}")
        if pack != "constitution":
            skill = ROOT / "packages" / pack / "SKILL.md"
            play = ROOT / "packages" / pack / "hq" / "PLAYBOOK.md"
            if not skill.is_file():
                fail(f"missing {skill.relative_to(ROOT)}")
            if not play.is_file() and pack not in {"vfbriefux"}:
                # vfbriefux uses PACKET.md
                if not (ROOT / "packages" / pack / "hq").is_dir():
                    fail(f"missing hq overlay for {pack}")

    if not (ROOT / "packages/vfbriefux/hq/PACKET.md").is_file():
        fail("missing daily brief packet")
    if not (ROOT / "constitution/CONSTITUTION.md").is_file():
        fail("missing constitution")
    if not (ROOT / "constitution/tags.md").is_file():
        fail("missing tags")

    vendor = (ROOT / "scripts/vendor-origin-packs.sh").read_text()
    if "HQ overlay wins" not in vendor:
        fail("vendor script must preserve hq overlay")

    skip_need = [
        "auto-DM",
        "boost",
        "invented ILS prices",
    ]
    for s in skip_need:
        if s not in MAP["skipped"]:
            fail(f"skipped list missing {s}")

    # No invented sale prices in HQ overlays (X ₪ and phone are ok).
    overlay_roots = [ROOT / "constitution", ROOT / "packages"]
    for folder in overlay_roots:
        for path in folder.rglob("*"):
            if path.suffix not in {".md", ".json"}:
                continue
            if path.name == "ORIGIN.md":
                continue
            text = path.read_text()
            for m in ILS_NUMBER.finditer(text):
                snippet = text[max(0, m.start() - 24) : m.end() + 8]
                if "X ₪" in snippet or "X   ₪" in snippet:
                    continue
                if "050-2517000" in snippet:
                    continue
                # Policy / list-item ₪ (e.g. "4. ₪ רק אחרי", "בלי ₪") is not a price.
                if re.search(r"(בלי|אין|לא)\s*₪|₪\s*רק", snippet):
                    continue
                if re.fullmatch(r"\d+\.\s*₪", m.group(0).strip()):
                    continue
                fail(f"possible invented ILS in {path.relative_to(ROOT)}: {snippet!r}")

    print("OK hq overlay + share map")


if __name__ == "__main__":
    main()
