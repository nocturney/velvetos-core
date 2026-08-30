#!/usr/bin/env python3
"""Check vfmakers catalog against HQ packs and crew files. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "manifest.json"
CATALOG = ROOT / "packages" / "vfmakers" / "catalog.json"
CREWS = ROOT / "packages" / "vfmakers" / "crews"
VERDICTS = {"embed", "later", "skip"}
REQUIRED_CREWS = {
    "crews/decide.md",
    "crews/unstuck.md",
    "crews/cash-pulse.md",
    "crews/content-rotation.md",
    "crews/studio-brain.md",
}
REQUIRED_LOCKS = (
    "no-send-instagram",
    "no-send-gmail",
    "no-invented-prices",
    "no-invented-insights",
    "no-makerskills-plugin",
    "no-typefully",
    "no-live-bank",
)
SOURCE_SKILLS = 20


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

    if catalog.get("name") != "vfmakers":
        fail("catalog name must be vfmakers")
    listed = catalog.get("source", {}).get("listedCount")
    if listed != SOURCE_SKILLS:
        fail(f"listedCount expected {SOURCE_SKILLS}, got {listed}")

    picks = catalog.get("picks") or []
    if len(picks) != SOURCE_SKILLS:
        fail(f"expected {SOURCE_SKILLS} picks, got {len(picks)}")

    names = [p.get("name") for p in picks]
    if len(set(names)) != SOURCE_SKILLS:
        fail(f"duplicate or missing skill names: {names}")

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
        crew_path = ROOT / "packages" / "vfmakers" / crew
        if not crew_path.is_file():
            fail(f"{name}: crew file missing {crew}")
        if verdict == "skip" and not pick.get("note"):
            fail(f"{name}: skip needs note")
        if verdict == "later" and not pick.get("note"):
            fail(f"{name}: later needs note")

    if embed_count < 5:
        fail(f"expected at least 5 embed picks, got {embed_count}")
    missing_crews = REQUIRED_CREWS - crew_refs
    if missing_crews:
        fail(f"crews not referenced: {sorted(missing_crews)}")

    on_disk = {f"crews/{p.name}" for p in CREWS.glob("*.md")}
    extra = on_disk - REQUIRED_CREWS
    if extra:
        fail(f"unexpected crew files: {sorted(extra)}")
    if on_disk != REQUIRED_CREWS:
        fail(f"crew files mismatch disk={sorted(on_disk)}")

    locks = set(catalog.get("locks") or [])
    for need in REQUIRED_LOCKS:
        if need not in locks:
            fail(f"missing lock {need}")

    if "vfmakers" not in pack_names:
        fail("vfmakers missing from packages/manifest.json")

    for rel in (
        "packages/vfmakers/EMBED.md",
        "packages/vfmakers/LOCK.md",
        "packages/vfmakers/ATTRIBUTION.md",
        "packages/vfbiz/hq/decisions/INDEX.md",
        "packages/vfops/hq/walls/INDEX.md",
        "packages/vfbooks/hq/pulse/INDEX.md",
        "packages/vfgrowth/hq/rotation/INDEX.md",
        ".cursor/rules/vfmakers-desk.mdc",
        ".cursor/skills/vf-makers/SKILL.md",
    ):
        if not (ROOT / rel).is_file():
            fail(f"missing {rel}")

    print(
        f"OK picks={len(picks)} embed={embed_count} "
        f"crews={len(REQUIRED_CREWS)} packs={len(pack_names)} listed={listed}"
    )


if __name__ == "__main__":
    main()
