#!/usr/bin/env python3
"""Check vfom catalog against HQ packs and crew files. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "manifest.json"
CATALOG = ROOT / "packages" / "vfom" / "catalog.json"
CREWS = ROOT / "packages" / "vfom" / "crews"
ALLOWED_STATUS = {"embed", "already", "skip", "later"}
REQUIRED_CREWS = {
    "crews/reference-plan.md",
    "crews/clip-factory.md",
    "crews/hybrid-reel.md",
    "crews/scene-gate.md",
    "crews/self-review.md",
}
REQUIRED_LOCKS = {
    "hq-send-via-tools",
    "no-auto-dm",
    "no-boost",
    "no-invented-prices",
    "no-invented-insights",
    "no-invented-floor-scene",
    "no-vendor-openmontage",
}
REQUIRED_PIPELINES = {
    "animated-explainer",
    "animation",
    "avatar-spokesperson",
    "character-animation",
    "cinematic",
    "clip-factory",
    "documentary-montage",
    "hybrid",
    "localization-dub",
    "podcast-repurpose",
    "screen-demo",
    "talking-head",
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

    if catalog.get("name") != "vfom":
        fail("catalog name must be vfom")

    source = catalog.get("source") or {}
    if source.get("pipelineCount") != 12:
        fail(f"pipelineCount expected 12, got {source.get('pipelineCount')}")
    listed = set(source.get("pipelines") or [])
    if listed != REQUIRED_PIPELINES:
        fail(f"pipelines mismatch missing={sorted(REQUIRED_PIPELINES - listed)} extra={sorted(listed - REQUIRED_PIPELINES)}")

    locks = set(catalog.get("locks") or [])
    missing_locks = REQUIRED_LOCKS - locks
    if missing_locks:
        fail(f"missing locks {sorted(missing_locks)}")

    items = catalog.get("items") or []
    if not items:
        fail("catalog has no items")

    counts = {s: 0 for s in ALLOWED_STATUS}
    crew_refs: set[str] = set()

    for i, item in enumerate(items):
        iid = item.get("id") or f"#{i}"
        status = item.get("status")
        if status not in ALLOWED_STATUS:
            fail(f"{iid}: status {status!r} not in {sorted(ALLOWED_STATUS)}")
        counts[status] += 1

        if not item.get("source"):
            fail(f"{iid}: source required")

        packs = item.get("packs") or []
        if not packs:
            fail(f"{iid}: no packs")
        for pack in packs:
            if pack not in pack_names:
                fail(f"{iid}: unknown pack {pack!r}")

        crew = item.get("crew")
        if not crew:
            fail(f"{iid}: missing crew")
        crew_refs.add(crew)
        crew_path = ROOT / "packages" / "vfom" / crew
        if not crew_path.is_file():
            fail(f"{iid}: crew file missing {crew}")

        if status == "embed" and not packs:
            fail(f"{iid}: embed needs packs")
        if status == "skip" and not item.get("reason"):
            fail(f"{iid}: skip needs reason")
        if status in {"already", "later"} and not item.get("note"):
            fail(f"{iid}: {status} needs note")

    if counts["embed"] < 5:
        fail(f"expected at least 5 embed items, got {counts['embed']}")

    covered: set[str] = set()
    for item in items:
        for src in item.get("source") or []:
            name = Path(str(src)).name
            if name.endswith(".yaml"):
                covered.add(name.removesuffix(".yaml"))
    if not REQUIRED_PIPELINES <= covered:
        fail(
            "pipeline yaml not mapped: "
            + ", ".join(sorted(REQUIRED_PIPELINES - covered))
        )

    missing_crews = REQUIRED_CREWS - crew_refs
    if missing_crews:
        fail(f"crews not referenced: {sorted(missing_crews)}")

    on_disk = {f"crews/{p.name}" for p in CREWS.glob("*.md")}
    extra = on_disk - REQUIRED_CREWS
    if extra:
        fail(f"unexpected crew files: {sorted(extra)}")
    if on_disk != REQUIRED_CREWS:
        fail(f"crew files mismatch disk={sorted(on_disk)}")

    writeup = ROOT / catalog.get("writeup", "docs/OPENMONTAGE.md")
    if not writeup.is_file():
        fail(f"missing writeup {writeup}")

    for rel in ("ORIGIN.md", "README.md", "EMBED.md", "LOCK.md", "SKILL.md"):
        if not (ROOT / "packages" / "vfom" / rel).is_file():
            fail(f"missing packages/vfom/{rel}")

    if "vfom" not in pack_names:
        fail("vfom missing from packages/manifest.json")

    print(
        "OK vfom "
        f"embed={counts['embed']} already={counts['already']} "
        f"later={counts['later']} skip={counts['skip']} "
        f"crews={len(REQUIRED_CREWS)} packs={len(pack_names)} pipelines=12"
    )


if __name__ == "__main__":
    main()
