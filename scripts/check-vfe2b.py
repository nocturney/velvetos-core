#!/usr/bin/env python3
"""Check vfe2b catalog against HQ packs and crew files. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "manifest.json"
CATALOG = ROOT / "packages" / "vfe2b" / "catalog.json"
CREWS = ROOT / "packages" / "vfe2b" / "crews"
VERDICTS = {"embed", "later", "skip"}
REQUIRED_CREWS = {
    "crews/morning-brief.md",
    "crews/research.md",
    "crews/inquiry.md",
    "crews/content.md",
    "crews/books-data.md",
}


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not MANIFEST.is_file():
        fail(f"missing {MANIFEST}")
    if not CATALOG.is_file():
        fail(f"missing {CATALOG}")

    manifest = json.loads(MANIFEST.read_text())
    catalog = json.loads(CATALOG.read_text())
    pack_names = {p["name"] for p in manifest["packs"]}

    if catalog.get("name") != "vfe2b":
        fail("catalog name must be vfe2b")
    listed = catalog.get("source", {}).get("listedCount")
    if listed != 209:
        fail(f"listedCount expected 209, got {listed}")

    picks = catalog.get("picks") or []
    if len(picks) < 20:
        fail(f"expected at least 20 picks, got {len(picks)}")

    crew_refs: set[str] = set()
    embed_count = 0
    for i, pick in enumerate(picks):
        name = pick.get("name") or f"#{i}"
        verdict = pick.get("verdict")
        if verdict not in VERDICTS:
            fail(f"{name}: verdict {verdict!r} not in {sorted(VERDICTS)}")
        if verdict == "embed":
            embed_count += 1
        packs = pick.get("packs") or []
        if not packs:
            fail(f"{name}: no packs")
        for p in packs:
            if p not in pack_names:
                fail(f"{name}: unknown pack {p!r}")
        crew = pick.get("crew")
        if not crew:
            fail(f"{name}: missing crew")
        crew_refs.add(crew)
        crew_path = ROOT / "packages" / "vfe2b" / crew
        if not crew_path.is_file():
            fail(f"{name}: crew file missing {crew}")

    if embed_count < 10:
        fail(f"expected at least 10 embed picks, got {embed_count}")
    missing_crews = REQUIRED_CREWS - crew_refs
    if missing_crews:
        fail(f"crews not referenced: {sorted(missing_crews)}")

    on_disk = {f"crews/{p.name}" for p in CREWS.glob("*.md")}
    extra = on_disk - REQUIRED_CREWS
    if extra:
        fail(f"unexpected crew files: {sorted(extra)}")
    if not on_disk == REQUIRED_CREWS:
        fail(f"crew files mismatch disk={sorted(on_disk)}")

    locks = set(catalog.get("locks") or [])
    for need in (
        "no-send-instagram",
        "no-send-gmail",
        "no-invented-prices",
        "no-invented-insights",
    ):
        if need not in locks:
            fail(f"missing lock {need}")

    if "vfe2b" not in pack_names:
        fail("vfe2b missing from packages/manifest.json")

    print(
        f"OK picks={len(picks)} embed={embed_count} "
        f"crews={len(REQUIRED_CREWS)} packs={len(pack_names)} listed={listed}"
    )


if __name__ == "__main__":
    main()
