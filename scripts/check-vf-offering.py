#!/usr/bin/env python3
"""Guard Velvet Factory's public offering shape. No network, no send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFERING = ROOT / "packages" / "vfbiz" / "OFFERING.md"


def fail(msg: str) -> None:
    print(f"FAIL vf-offering: {msg}", file=sys.stderr)
    raise SystemExit(1)


def retired_terms() -> tuple[str, ...]:
    # Build retired labels from fragments so the labels themselves do not become
    # searchable business copy in this enforcement file.
    return (
        "סדרות" + " " + "לעסקים",
        "ייצור" + " " + "סדרות",
        "סדרה" + " " + "לעסק",
        "local_" + "b2b" + "_v1",
        "b2b" + "-line-locked",
        "b2b" + "-locked",
        "LOCAL-" + "B2" + "B.md",
        "B2" + "B-QUOTE.md",
        "b2b" + "-local.md",
    )

ACTIVE_FILES = (
    "AGENTS.md",
    ".cursor/vf-desk.json",
    "constitution/STUDIO.md",
    "constitution/ORCHESTRA.md",
    "packages/vfbiz/OFFERING.md",
    "packages/vfbiz/SKILL.md",
    "packages/vfbiz/LOCK.md",
    "packages/vfbiz/hq/PLAYBOOK.md",
    "packages/vfconvert/CARD.md",
    "packages/vfconvert/PATH.md",
    "packages/vfcopy/VOICE.md",
    "packages/vfgrowth/CONTENT-RESET-2026-09-10.md",
    "packages/vfgrowth/FEED-AUDIT.md",
    "packages/vfgrowth/ORGANIC-GROWTH.md",
    "packages/vfgrowth/HASHTAGS.md",
    "packages/vfgrowth/data/growth-brief.json",
    "packages/vfgrowth/data/hashtag-library.json",
    "packages/vfigos/PROFILE-DESIRED.json",
    "packages/vfigos/GRAPH-MUTATIONS.md",
    "packages/vfom/VELVET-VISUAL-SYSTEM-PROMPT.md",
    "packages/vfops/BRIEF.md",
    "packages/vfops/LOOP.json",
    "packages/vfops/hq/GATES.json",
    "packages/vfsales/ORDERS.md",
    "packages/vfsales/QUOTE.md",
    "packages/vfsku/GATE.md",
    "instances/velvet-factory/constitution/STUDIO.md",
    "instances/velvet-factory/instance/velvet-factory.json",
    "instances/velvet-factory/.cursor/vf-desk.json",
)

def main() -> None:
    if not OFFERING.is_file():
        fail("missing packages/vfbiz/OFFERING.md")
    offer = OFFERING.read_text(encoding="utf-8")
    for needle in ("מוצרים מוכנים", "התאמה אישית", "מאפיין של ההזמנה"):
        if needle not in offer:
            fail(f"offering authority missing {needle!r}")

    forbidden = retired_terms()
    for rel in ACTIVE_FILES:
        path = ROOT / rel
        if not path.is_file():
            fail(f"missing active authority {rel}")
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token.lower() in text.lower():
                fail(f"retired customer-type/quantity service label remains in {rel}")

    # First-party authority/public surfaces should not expose the old segmentation shorthand.
    shorthand = "B" + "2" + "B"
    for rel in (
        "AGENTS.md",
        ".cursor/vf-desk.json",
        "constitution/STUDIO.md",
        "packages/vfbiz/OFFERING.md",
        "packages/vfbiz/SKILL.md",
        "packages/vfbiz/LOCK.md",
        "packages/vfigos/PROFILE-DESIRED.json",
        "instances/velvet-factory/constitution/STUDIO.md",
        "instances/velvet-factory/instance/velvet-factory.json",
        "instances/velvet-factory/.cursor/vf-desk.json",
    ):
        if shorthand in (ROOT / rel).read_text(encoding="utf-8"):
            fail(f"retired segmentation shorthand remains in {rel}")

    for rel in (
        "packages/vfbiz/" + "LOCAL-" + "B2" + "B.md",
        "packages/vfbiz/LOCAL.json",
        "packages/vfsales/hq/" + "B2" + "B-QUOTE.md",
        "packages/vfcopy/hq/templates/" + "b2b" + "-local.md",
    ):
        if (ROOT / rel).exists():
            fail(f"retired dedicated service-line artifact still exists: {rel}")

    profile = json.loads((ROOT / "packages/vfigos/PROFILE-DESIRED.json").read_text(encoding="utf-8"))
    desired = (profile.get("desired") or {}).get("bioHe") or ""
    for needle in ("מוצרים מוכנים", "מודלים בהתאמה אישית"):
        if needle not in desired:
            fail(f"desired Instagram bio missing {needle!r}")
    if (profile.get("liveSnapshot") or {}).get("retiredOfferingPhrasePresent") is True:
        if profile.get("liveStatus") != "pending-human-profile-edit":
            fail("live profile debt must stay pending-human-profile-edit until re-verified")

    for rel in (
        "instances/velvet-factory/instance/velvet-factory.json",
        "packages/velvetos/samples/velvet-factory.json",
    ):
        data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        compliance = data.get("compliance") or {}
        if compliance.get("noCustomerTypeServicePillar") is not True:
            fail(f"{rel}: noCustomerTypeServicePillar must be true")
        if compliance.get("offeringAuthority") != "packages/vfbiz/OFFERING.md":
            fail(f"{rel}: offeringAuthority mismatch")

    print(f"OK vf-offering active_files={len(ACTIVE_FILES)} two-track quantity-is-job-attribute live-profile-gated")


if __name__ == "__main__":
    main()
