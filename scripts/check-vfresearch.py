#!/usr/bin/env python3
"""Validate weekly inspiration-links registry on vfresearch. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINKS = ROOT / "packages" / "vfresearch" / "LINKS.json"
WEEKLY = ROOT / "packages" / "vfresearch" / "WEEKLY.md"
DAILY = ROOT / "packages" / "vfresearch" / "DAILY.md"
ROUTINE = ROOT / "packages" / "vfops" / "ROUTINE.md"
ORCHESTRA = ROOT / "constitution" / "ORCHESTRA.md"
MANIFEST = ROOT / "packages" / "manifest.json"
REQUIRED_LOCKS = {
    "no-send-instagram",
    "no-send-gmail",
    "no-invented-prices",
    "no-invented-insights",
    "no-new-pack-per-idea",
    "no-invented-blocked-body",
}
NEEDLE_WEEKLY = "שבוע"
LINK_FIELDS = ("id", "kind", "url", "title", "firstEmbedded", "lastReviewed")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (LINKS, WEEKLY, DAILY, ROUTINE, ORCHESTRA, MANIFEST):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    data = json.loads(LINKS.read_text())
    if data.get("name") != "vfresearch-inspiration-links":
        fail("LINKS.json name must be vfresearch-inspiration-links")
    if data.get("cadence") != "weekly":
        fail("LINKS.json cadence must be weekly")
    if "existing packs" not in (data.get("rule") or ""):
        fail("LINKS.json rule must say embed into existing packs")

    locks = set(data.get("locks") or [])
    for need in REQUIRED_LOCKS:
        if need not in locks:
            fail(f"missing lock {need}")

    links = data.get("links") or []
    if len(links) < 3:
        fail("LINKS.json must list at least 3 inspiration links")

    ids: set[str] = set()
    for item in links:
        for field in LINK_FIELDS:
            if not item.get(field):
                fail(f"link missing {field}: {item.get('id')}")
        lid = item["id"]
        if lid in ids:
            fail(f"duplicate link id {lid}")
        ids.add(lid)
        url = item["url"]
        if not (url.startswith("https://") or url.startswith("http://")):
            fail(f"link {lid} url must be http(s)")

    weekly = WEEKLY.read_text()
    if "LINKS.json" not in weekly:
        fail("WEEKLY.md must reference LINKS.json")
    if "YYYY-MM-DD-weekly-links.md" not in weekly:
        fail("WEEKLY.md must name weekly artifact pattern")
    if "לא ממציאים" not in weekly and "לא ממציאים גוף" not in weekly:
        fail("WEEKLY.md must forbid inventing blocked bodies")

    routine = ROUTINE.read_text()
    if "WEEKLY.md" not in routine and "קישורי השראה" not in routine:
        fail("vfops/ROUTINE.md must mention weekly inspiration links")
    if NEEDLE_WEEKLY not in routine:
        fail("vfops/ROUTINE.md must mention weekly cadence")

    orchestra = ORCHESTRA.read_text()
    if "WEEKLY.md" not in orchestra and "קישורי השראה" not in orchestra:
        fail("constitution/ORCHESTRA.md must mention weekly link review")

    print(f"OK vfresearch weekly-links links={len(links)}")


if __name__ == "__main__":
    main()
