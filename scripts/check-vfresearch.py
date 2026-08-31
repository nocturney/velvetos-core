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
MUSIC = ROOT / "packages" / "vfresearch" / "MUSIC.md"
MUSIC_SOURCES = ROOT / "packages" / "vfresearch" / "SOURCES-MUSIC.json"
MUSIC_SKILL = ROOT / ".cursor" / "skills" / "vf-ig-music" / "SKILL.md"
ROUTINE = ROOT / "packages" / "vfops" / "ROUTINE.md"
ORCHESTRA = ROOT / "constitution" / "ORCHESTRA.md"
RESEARCH_BLOCK = ROOT / "packages" / "vfops" / "data" / "research.md"
MANIFEST = ROOT / "packages" / "manifest.json"
DESK = ROOT / ".cursor" / "vf-desk.json"
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
    for path in (LINKS, WEEKLY, DAILY, MUSIC, MUSIC_SOURCES, MUSIC_SKILL, ROUTINE, ORCHESTRA, MANIFEST, DESK, RESEARCH_BLOCK):
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
    if "data/research.md" not in routine:
        fail("vfops/ROUTINE.md must point brief block 05 at data/research.md")

    orchestra = ORCHESTRA.read_text()
    if "WEEKLY.md" not in orchestra and "קישורי השראה" not in orchestra:
        fail("constitution/ORCHESTRA.md must mention weekly link review")
    for needle in ("Failover", "באותו רגע", "אסור להישאר בלי תוצאה", "studio/render.py"):
        if needle not in orchestra:
            fail(f"constitution/ORCHESTRA.md must mention failover needle: {needle}")
    if "מחכים לבעלים" in orchestra and "לא «מחכים לבעלים»" not in orchestra:
        fail("ORCHESTRA.md must not idle-wait on auth; use immediate failover")

    daily = DAILY.read_text()
    if "failover" not in daily.lower() and "Failover" not in daily:
        fail("vfresearch/DAILY.md must mention failover")
    if "מחכים לבעלים" in daily:
        fail("DAILY.md must not say מחכים לבעלים without failover")
    if "data/research.md" not in daily:
        fail("vfresearch/DAILY.md must write block 05 to vfops/data/research.md")

    block = RESEARCH_BLOCK.read_text()
    if "מה נבנה / יועל" not in block and "אין חדש במשרד" not in block:
        fail("vfops/data/research.md must carry «מה נבנה / יועל» or exact empty-state אין חדש במשרד")

    desk = json.loads(DESK.read_text())
    tools = desk.get("tools") or {}
    for key in ("gmail", "calendar", "drive", "canva", "superdesign", "treg", "mobbin", "fcc"):
        if key not in tools:
            fail(f"vf-desk.json tools missing {key}")
        if not (tools[key].get("failover") or ""):
            fail(f"vf-desk.json tools.{key} must declare failover")
    notes = " ".join(desk.get("notes") or [])
    if "failover" not in notes.lower():
        fail("vf-desk.json notes must mention tool failover")

    music = MUSIC.read_text()
    for needle in ("@trend-researcher", "vfigos", "חסר מקור", "HeyOrca", "@velvets_cloud", "לא בשימוש"):
        if needle not in music:
            fail(f"MUSIC.md must mention {needle}")
    if "YYYY-MM-DD-ig-music.md" not in music:
        fail("MUSIC.md must name ig-music artifact pattern")
    if "לא «שלחו DM»" not in music and 'Not «שלחו DM»' not in music:
        fail("MUSIC.md must forbid Send DM CTA")
    if "heyorca.com/blog/trending-audio" not in music.lower():
        fail("MUSIC.md must point at HeyOrca weekly URL")
    # Treg may appear only as an explicit skip for music
    if "Treg" in music and "עזבו את Treg" not in music and "אין Treg" not in music and "לא בשימוש" not in music:
        fail("MUSIC.md must explicitly skip Treg for music")

    music_src = json.loads(MUSIC_SOURCES.read_text())
    if music_src.get("name") != "vfresearch-ig-music-sources":
        fail("SOURCES-MUSIC.json name mismatch")
    if "treg" not in (music_src.get("skip") or []):
        fail("SOURCES-MUSIC.json must skip treg")
    primary = [s for s in (music_src.get("sources") or []) if s.get("role") == "primary"]
    if not primary or "heyorca" not in primary[0].get("id", ""):
        fail("SOURCES-MUSIC.json primary must be HeyOrca")

    skill = MUSIC_SKILL.read_text()
    if "trend-researcher" not in skill:
        fail("vf-ig-music skill must mention trend-researcher")
    if "MUSIC.md" not in skill:
        fail("vf-ig-music skill must point at MUSIC.md")
    if "no Treg" not in skill and "No Treg" not in skill and "**no Treg**" not in skill:
        fail("vf-ig-music skill must forbid Treg")

    skill_paths = desk.get("skills") or []
    if ".cursor/skills/vf-ig-music/SKILL.md" not in skill_paths:
        fail("vf-desk.json skills must include vf-ig-music")
    trend = next((r for r in desk.get("desk", []) if r.get("slug") == "trend-researcher"), None)
    if not trend:
        fail("desk missing trend-researcher")
    job = trend.get("job") or ""
    if "music" not in job.lower() and "sound" not in job.lower() and "מוזיקה" not in job:
        fail("trend-researcher job must cover Instagram music/sound")
    if "HeyOrca" not in job and "heyorca" not in job.lower():
        fail("trend-researcher job must name HeyOrca (not Treg) for music")

    print(f"OK vfresearch weekly-links links={len(links)} music=1 sources={len(music_src.get('sources') or [])} failover=1")


if __name__ == "__main__":
    main()
