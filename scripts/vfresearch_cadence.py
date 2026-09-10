#!/usr/bin/env python3
"""Research cadence status + freshness + index build for vfresearch.

Separates:
- status/verify: which routines exist, who runs them, last artifact (no fake 'activated')
- freshness: prove a same-day research body exists and is consumable by the morning brief
- build-index: semantic index for vfmem consumers (fails closed — no || echo)
- Does NOT pretend weekly-links / best-skills / LAST30 ran just because CI started

No network required for status/verify/freshness. build-index needs scikit-learn locally/CI.
No send. No invented Insights.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Jerusalem")
SOURCES = ROOT / "packages" / "vfresearch" / "sources"
BEST_JSON = ROOT / "packages" / "vfresearch" / "BEST-SKILLS.json"
LINKS = ROOT / "packages" / "vfresearch" / "LINKS.json"
RESEARCH_MD = ROOT / "packages" / "vfops" / "data" / "research.md"
INDEX_SCRIPT = ROOT / "packages" / "vfmem" / "scripts" / "vf_semantic_search.py"
INDEX_PKL = ROOT / "packages" / "vfmem" / "semantic_index.pkl"

# Activator map — honest owners (do not invent new paid schedules)
ROUTINES = (
    {
        "id": "daily-orchestra",
        "title": "מחקר יומי / תזמורת 06:15",
        "trigger": "ChatGPT automation Velvet Research Seat 06:15 + packages/vfresearch/DAILY.md",
        "environment": "ChatGPT WebSearch/connectors; Cloud Agent/Cursor may supplement — not GH Actions body fetch",
        "permissions": "read packs; web research; write sources/ + research.md; no subscription UI scraping",
        "input": "yesterday brief, CALENDAR, vfsku/production, live office context",
        "artifact_glob": "*-*-orchestra.md",
        "consumer": "vfops/data/research.md → morning brief slot 05",
        "owner": "Velvet Research Seat; Morning Brief verifies freshness and may fallback without faking provenance",
    },
    {
        "id": "weekly-links",
        "title": "קישורי השראה שבועיים",
        "trigger": "skill vf-weekly-links · packages/vfresearch/WEEKLY.md · calendar weekly",
        "environment": "Cloud Agent with WebFetch/WebSearch",
        "permissions": "update LINKS.json + sources/*-weekly-links.md",
        "input": "LINKS.json registry",
        "artifact_glob": "*-*-weekly-links.md",
        "consumer": "LINKS.json lastReviewed + research.md; check-vfresearch.py",
        "owner": "Cursor research seat",
    },
    {
        "id": "best-skills",
        "title": "LinklyAI best-skills (~48h forever)",
        "trigger": "subscribe_timer vf-best-skills-bi-daily · TIMER.md · skill vf-best-skills",
        "environment": "Cloud Agent (timer + WebFetch to github.com/LinklyAI/best-skills)",
        "permissions": "embed into existing packs; renew timer; no npx skills",
        "input": "BEST-SKILLS.json + LinklyAI rankings",
        "artifact_glob": "*-*-best-skills.md",
        "consumer": "BEST-SKILLS.json dataDate + research.md block 05",
        "owner": "Cursor (standingForever) — not GrokBot cron",
    },
    {
        "id": "last30",
        "title": "מחקר קהילה 30 יום",
        "trigger": "skill vf-last30 · hq/LAST30.md · monthly / on demand",
        "environment": "Cloud Agent WebSearch/gh api (no paid scrapers)",
        "permissions": "write sources/*-last30.md; no invented trends",
        "input": "topic / comparison / discovery prompt",
        "artifact_glob": "*-*-*last30*.md",
        "consumer": "trend / content desks; research.md",
        "owner": "Cursor research seat",
    },
    {
        "id": "semantic-index",
        "title": "אינדקס סמנטי vfmem",
        "trigger": "GH workflow velvetos-research.yml + HQ-ROUTINE daily step א",
        "environment": "GitHub Actions ubuntu / local with scikit-learn",
        "permissions": "write packages/vfmem/semantic_index.pkl (gitignored)",
        "input": "office markdown corpus",
        "artifact_glob": None,
        "artifact_path": "packages/vfmem/semantic_index.pkl",
        "consumer": "vf_semantic_search queries; not a substitute for weekly/best/last30",
        "owner": "CI + any agent that rebuilt after large pull",
    },
)


def latest_source(glob_pat: str | None) -> Path | None:
    if not glob_pat or not SOURCES.is_dir():
        return None
    hits = sorted(SOURCES.glob(glob_pat))
    return hits[-1] if hits else None


def parse_date_from_name(path: Path | None) -> date | None:
    if path is None:
        return None
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", path.name)
    if not m:
        return None
    return date.fromisoformat(m.group(1))


def jerusalem_now() -> datetime:
    return datetime.now(TZ)


def dst_note() -> str:
    """Explain GH cron vs Asia/Jerusalem including DST."""
    now = jerusalem_now()
    offset = now.utcoffset() or timedelta(0)
    hours = int(offset.total_seconds() // 3600)
    # workflow cron: 30 4 * * * UTC
    local_from_cron_hour = 4 + hours
    season = "IDT (קיץ)" if hours == 3 else "IST (חורף)" if hours == 2 else f"UTC{hours:+d}"
    return (
        f"עכשיו {now.isoformat(timespec='minutes')} · {season} · "
        f"cron '30 4 * * *' UTC ≈ {local_from_cron_hour:02d}:30 Asia/Jerusalem · "
        f"Research Seat exact 06:15 Asia/Jerusalem; CI runs after it in both DST seasons"
    )


def cmd_status(_args: argparse.Namespace) -> int:
    print("=== vfresearch cadence status ===")
    print(dst_note())
    print()
    print("| id | last artifact | dataDate/due | environment | activated? |")
    print("|---|---|---|---|---|")
    best = {}
    if BEST_JSON.is_file():
        best = json.loads(BEST_JSON.read_text(encoding="utf-8"))
    for row in ROUTINES:
        art = None
        if row.get("artifact_path"):
            p = ROOT / row["artifact_path"]
            art = p if p.is_file() else None
        else:
            art = latest_source(row.get("artifact_glob"))
        when = parse_date_from_name(art) if art and row["id"] != "semantic-index" else None
        if row["id"] == "semantic-index" and art:
            stamp = datetime.fromtimestamp(art.stat().st_mtime, TZ).date().isoformat()
            last = f"{art.relative_to(ROOT)} · mtime {stamp}"
        elif art:
            last = str(art.relative_to(ROOT))
        else:
            last = "חסר"
        due = "—"
        if row["id"] == "best-skills":
            due = f"lastPass={best.get('lastPass')} standingForever={best.get('standingForever')}"
        activated = "evidence" if art else "not-run-here"
        print(f"| {row['id']} | {last} | {due if due != '—' else (when or '—')} | {row['environment'][:40]}… | {activated} |")
    print()
    print("Daily research body owner: Velvet Research Seat at 06:15 Asia/Jerusalem.")
    print("CI velvetos-research.yml proves freshness+index+sensors; it does NOT fetch research bodies itself.")
    return 0


def cmd_map(_args: argparse.Namespace) -> int:
    for row in ROUTINES:
        print(f"## {row['id']} — {row['title']}")
        for k in ("trigger", "environment", "permissions", "input", "consumer", "owner"):
            print(f"- {k}: {row[k]}")
        print()
    print("## DST / cron")
    print(dst_note())
    return 0


def cmd_freshness(_args: argparse.Namespace) -> int:
    """Fail unless today's actual research-body artifact is present and consumable."""
    today = jerusalem_now().date().isoformat()
    artifact = SOURCES / f"{today}-orchestra.md"
    problems: list[str] = []
    if not artifact.is_file():
        problems.append(f"missing same-day research body {artifact.relative_to(ROOT)}")
        body = ""
    else:
        body = artifact.read_text(encoding="utf-8")
        if len(body.strip()) < 300:
            problems.append("same-day orchestra artifact is too small to prove a body run")
        urls = re.findall(r"https?://[^\s)>]+", body)
        if not urls:
            problems.append("same-day orchestra has no external source URL; CI/index output alone is not research")
        if "אין חדש במשרד" not in body and not any(
            marker in body for marker in ("## ממצאים", "## What I learned", "## מה למדנו", "## תוצאות", "## מה נשאל / מה רץ")
        ):
            problems.append("same-day orchestra has neither findings section nor explicit 'אין חדש במשרד'")

    research = RESEARCH_MD.read_text(encoding="utf-8") if RESEARCH_MD.is_file() else ""
    if today not in research and f"{today}-orchestra.md" not in research:
        problems.append("vfops/data/research.md does not reference today's research body")

    if problems:
        print("FAIL daily research freshness")
        for problem in problems:
            print("-", problem)
        return 1

    source_count = len(re.findall(r"https?://[^\s)>]+", body))
    print(f"OK daily research fresh date={today} artifact={artifact.relative_to(ROOT)} external_sources={source_count}")
    return 0


def cmd_build_index(_args: argparse.Namespace) -> int:
    if not INDEX_SCRIPT.is_file():
        print(f"FAIL missing {INDEX_SCRIPT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    proc = subprocess.run(
        [sys.executable, str(INDEX_SCRIPT), "--build"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    sys.stdout.write(proc.stdout or "")
    sys.stderr.write(proc.stderr or "")
    if proc.returncode != 0:
        print("FAIL semantic index build", file=sys.stderr)
        return proc.returncode
    if not INDEX_PKL.is_file():
        print("FAIL build reported ok but semantic_index.pkl missing", file=sys.stderr)
        return 1
    print(f"OK index → {INDEX_PKL.relative_to(ROOT)} ({INDEX_PKL.stat().st_size} bytes)")
    print("Consumer: python3 packages/vfmem/scripts/vf_semantic_search.py \"<query>\"")
    return 0


def cmd_verify(_args: argparse.Namespace) -> int:
    """Structural verify — does not claim routines ran."""
    bad: list[str] = []
    for path in (BEST_JSON, LINKS, RESEARCH_MD, INDEX_SCRIPT):
        if not path.is_file():
            bad.append(f"missing {path.relative_to(ROOT)}")
    weekly = latest_source("*-*-weekly-links.md")
    best = latest_source("*-*-best-skills.md")
    last30 = latest_source("*-*-*last30*.md")
    research = RESEARCH_MD.read_text(encoding="utf-8") if RESEARCH_MD.is_file() else ""
    if weekly and weekly.stem[:10] not in research and "weekly" not in research.lower():
        if not research.strip():
            bad.append("research.md empty while weekly artifact exists")
    print("verify artifacts:")
    print(f"- weekly: {weekly.relative_to(ROOT) if weekly else 'חסר'}")
    print(f"- best-skills: {best.relative_to(ROOT) if best else 'חסר'}")
    print(f"- last30: {last30.relative_to(ROOT) if last30 else 'חסר'}")
    print(f"- research.md bytes: {len(research)}")
    print(f"- index present: {INDEX_PKL.is_file()}")
    if bad:
        print("FAIL vfresearch cadence verify:")
        for b in bad:
            print("-", b)
        return 1
    print("OK vfresearch cadence verify (structure only — not a live activation claim)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="VelvetOS research cadence")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="honest status table").set_defaults(func=cmd_status)
    sub.add_parser("map", help="full activator map").set_defaults(func=cmd_map)
    sub.add_parser("freshness", help="require today's real research-body artifact").set_defaults(func=cmd_freshness)
    sub.add_parser("build-index", help="build semantic index; fail closed").set_defaults(func=cmd_build_index)
    sub.add_parser("verify", help="structure verify").set_defaults(func=cmd_verify)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
