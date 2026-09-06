#!/usr/bin/env python3
"""Validate weekly inspiration-links registry on vfresearch. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINKS = ROOT / "packages" / "vfresearch" / "LINKS.json"
WEEKLY = ROOT / "packages" / "vfresearch" / "WEEKLY.md"
BEST_SKILLS = ROOT / "packages" / "vfresearch" / "BEST-SKILLS.md"
BEST_SKILLS_JSON = ROOT / "packages" / "vfresearch" / "BEST-SKILLS.json"
BEST_SKILLS_TIMER = ROOT / "packages" / "vfresearch" / "TIMER.md"
BEST_SKILLS_SKILL = ROOT / ".cursor" / "skills" / "vf-best-skills" / "SKILL.md"
LAST30 = ROOT / "packages" / "vfresearch" / "hq" / "LAST30.md"
LAST30_SKILL = ROOT / ".cursor" / "skills" / "vf-last30" / "SKILL.md"
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
    "hq-send-via-tools",
    "no-auto-dm",
    "no-boost",
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
    for path in (LINKS, WEEKLY, BEST_SKILLS, BEST_SKILLS_JSON, BEST_SKILLS_TIMER, BEST_SKILLS_SKILL, LAST30, LAST30_SKILL, DAILY, MUSIC, MUSIC_SOURCES, MUSIC_SKILL, ROUTINE, ORCHESTRA, MANIFEST, DESK, RESEARCH_BLOCK):
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

    orchestra = ORCHESTRA.read_text()
    if "WEEKLY.md" not in orchestra and "קישורי השראה" not in orchestra:
        fail("constitution/ORCHESTRA.md must mention weekly link review")
    if "BEST-SKILLS.md" not in orchestra and "best-skills" not in orchestra.lower():
        fail("constitution/ORCHESTRA.md must mention bi-daily best-skills review")
    for needle in ("Failover", "באותו רגע", "אסור להישאר בלי תוצאה", "studio/render.py"):
        if needle not in orchestra:
            fail(f"constitution/ORCHESTRA.md must mention failover needle: {needle}")
    if "מחכים לבעלים" in orchestra and "לא «מחכים לבעלים»" not in orchestra:
        fail("ORCHESTRA.md must not idle-wait on auth; use immediate failover")

    best = BEST_SKILLS.read_text()
    if "LinklyAI/best-skills" not in best and "linklyai/best-skills" not in best.lower():
        fail("BEST-SKILLS.md must name LinklyAI/best-skills")
    if "YYYY-MM-DD-best-skills.md" not in best:
        fail("BEST-SKILLS.md must name bi-daily artifact pattern")
    if "npx skills" not in best.lower() and "npx skills" not in best:
        # must forbid install
        fail("BEST-SKILLS.md must mention npx skills (forbid on Cloud)")
    if "כל יומיים" not in best and "48" not in best:
        fail("BEST-SKILLS.md must state every-2-days cadence")

    best_json = json.loads(BEST_SKILLS_JSON.read_text())
    if best_json.get("name") != "vfresearch-best-skills":
        fail("BEST-SKILLS.json name must be vfresearch-best-skills")
    if best_json.get("cadence") != "every-2-days":
        fail("BEST-SKILLS.json cadence must be every-2-days")
    if "existing packs" not in (best_json.get("rule") or ""):
        fail("BEST-SKILLS.json rule must say embed into existing packs")
    if best_json.get("standingForever") is not True:
        fail("BEST-SKILLS.json standingForever must be true until owner stops")
    if best_json.get("timerName") != "vf-best-skills-bi-daily":
        fail("BEST-SKILLS.json timerName must be vf-best-skills-bi-daily")
    if "TIMER.md" not in (best_json.get("timerPlaybook") or ""):
        fail("BEST-SKILLS.json must point timerPlaybook at TIMER.md")
    best_locks = set(best_json.get("locks") or [])
    for need in ("no-npx-skills-on-cloud", "no-second-runtime", "no-invented-blocked-body"):
        if need not in best_locks:
            fail(f"BEST-SKILLS.json missing lock {need}")
    if not best_json.get("lastPass"):
        fail("BEST-SKILLS.json must set lastPass")

    timer = BEST_SKILLS_TIMER.read_text()
    if "vf-best-skills-bi-daily" not in timer:
        fail("TIMER.md must name vf-best-skills-bi-daily")
    if "172800" not in timer:
        fail("TIMER.md must set delaySeconds 172800")
    if "לנצח" not in timer and "forever" not in timer.lower():
        fail("TIMER.md must state forever-until-owner-stops standing order")
    if "subscribe_timer" not in timer:
        fail("TIMER.md must instruct subscribe_timer renew")

    best_skill = BEST_SKILLS_SKILL.read_text()
    if "BEST-SKILLS.md" not in best_skill:
        fail("vf-best-skills skill must point at BEST-SKILLS.md")
    if "TIMER.md" not in best_skill:
        fail("vf-best-skills skill must point at TIMER.md")
    if "research-synthesist" not in best_skill:
        fail("vf-best-skills skill must mention research-synthesist")
    if "npx" not in best_skill.lower():
        fail("vf-best-skills skill must forbid npx install")
    if "standing" not in best_skill.lower() and "לנצח" not in best_skill:
        fail("vf-best-skills skill must mention standing forever order")
    if "renew" not in best_skill.lower() and "חדש" not in best_skill:
        fail("vf-best-skills skill must require timer renew")

    link_ids = {item["id"] for item in links}
    if "linklyai-best-skills" not in link_ids:
        fail("LINKS.json must register linklyai-best-skills")
    if "mvanhorn-last30days-skill" not in link_ids:
        fail("LINKS.json must register mvanhorn-last30days-skill")

    last30 = LAST30.read_text()
    for needle in ("mvanhorn/last30days-skill", "nothing-solid", "WebSearch", "vf-last30", "npx skills"):
        if needle not in last30 and needle.lower() not in last30.lower():
            fail(f"LAST30.md must mention {needle}")
    if "YYYY-MM-DD-<topic" not in last30 and "YYYY-MM-DD-<topic-slug>-last30.md" not in last30:
        fail("LAST30.md must name last30 artifact pattern")

    last30_skill = LAST30_SKILL.read_text()
    if "LAST30.md" not in last30_skill:
        fail("vf-last30 skill must point at LAST30.md")
    if "research-synthesist" not in last30_skill:
        fail("vf-last30 skill must mention research-synthesist")
    if "trend-researcher" not in last30_skill:
        fail("vf-last30 skill must mention trend-researcher")
    if "npx" not in last30_skill.lower():
        fail("vf-last30 skill must forbid npx install")

    routine = ROUTINE.read_text()
    if "BEST-SKILLS" not in routine and "best-skills" not in routine.lower():
        fail("vfops/ROUTINE.md must mention bi-daily best-skills")
    if "WEEKLY.md" not in routine and "קישורי השראה" not in routine:
        fail("vfops/ROUTINE.md must mention weekly inspiration links")
    if NEEDLE_WEEKLY not in routine:
        fail("vfops/ROUTINE.md must mention weekly cadence")
    if "data/research.md" not in routine:
        fail("vfops/ROUTINE.md must point brief block 05 at data/research.md")

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
    for key in ("gmail", "calendar", "drive", "canva", "superdesign", "treg", "mobbin", "fcc", "web", "image", "gemini", "chatgpt"):
        if key not in tools:
            fail(f"vf-desk.json tools missing {key}")
        if not (tools[key].get("failover") or ""):
            fail(f"vf-desk.json tools.{key} must declare failover")
    notes = " ".join(desk.get("notes") or [])
    if "failover" not in notes.lower():
        fail("vf-desk.json notes must mention tool failover")
    if "best-skills" not in notes.lower() and "BEST-SKILLS" not in notes:
        fail("vf-desk.json notes must mention bi-daily best-skills")

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
    if ".cursor/skills/vf-best-skills/SKILL.md" not in skill_paths:
        fail("vf-desk.json skills must include vf-best-skills")
    if ".cursor/skills/vf-last30/SKILL.md" not in skill_paths:
        fail("vf-desk.json skills must include vf-last30")
    trend = next((r for r in desk.get("desk", []) if r.get("slug") == "trend-researcher"), None)
    if not trend:
        fail("desk missing trend-researcher")
    job = trend.get("job") or ""
    if "music" not in job.lower() and "sound" not in job.lower() and "מוזיקה" not in job:
        fail("trend-researcher job must cover Instagram music/sound")
    if "HeyOrca" not in job and "heyorca" not in job.lower():
        fail("trend-researcher job must name HeyOrca (not Treg) for music")
    if "LAST30" not in job and "last30" not in job.lower() and "last-30" not in job.lower():
        fail("trend-researcher job must cover last-30 / LAST30 research")
    synthesist = next((r for r in desk.get("desk", []) if r.get("slug") == "research-synthesist"), None)
    if not synthesist:
        fail("desk missing research-synthesist")
    syn_job = synthesist.get("job") or ""
    if "LAST30" not in syn_job and "last30" not in syn_job.lower() and "last-30" not in syn_job.lower():
        fail("research-synthesist job must cover last-30 / LAST30 research")

    print(
        f"OK vfresearch weekly-links links={len(links)} "
        f"best-skills=1 last30=1 music=1 sources={len(music_src.get('sources') or [])} failover=1"
    )


if __name__ == "__main__":
    main()
