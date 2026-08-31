#!/usr/bin/env python3
"""Staleness sensor — Huginn working? pattern for HQ. No network. No send."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
LINKS = ROOT / "packages" / "vfresearch" / "LINKS.json"
VFOPS = ROOT / "packages" / "vfops"
STATE = ROOT / "packages" / "vfharness" / "state"
SCENARIOS = ROOT / "packages" / "vfe2b" / "scenarios.json"

LINKS_MAX_STALE_DAYS = 8
CHECKPOINT_MAX_STALE_DAYS = 2
TZ = ZoneInfo("Asia/Jerusalem")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def parse_day(value: str) -> date:
    """Accept YYYY-MM-DD or ISO-8601 prefix."""
    return date.fromisoformat(value[:10])


def check_links_stale(today: date) -> tuple[int, list[str]]:
    data = json.loads(LINKS.read_text())
    stale: list[str] = []
    for item in data.get("links") or []:
        lid = item.get("id") or "?"
        reviewed = item.get("lastReviewed")
        if not reviewed:
            stale.append(f"{lid}:missing-lastReviewed")
            continue
        age = (today - parse_day(reviewed)).days
        if age > LINKS_MAX_STALE_DAYS:
            stale.append(f"{lid}:{age}d")
    return len(data.get("links") or []), stale


def check_brief_today(today: date) -> bool:
    iso = today.isoformat()
    candidates = [
        VFOPS / f"BRIEF-{iso}.md",
        VFOPS / "hq" / f"brief-{iso}.json",
    ]
    return any(p.is_file() for p in candidates)


def check_running_checkpoints(today: date) -> list[str]:
    stale: list[str] = []
    if not STATE.is_dir():
        return stale
    for path in STATE.glob("*.json"):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            stale.append(f"{path.name}:invalid-json")
            continue
        if data.get("status") != "running":
            continue
        updated = data.get("last_updated")
        if not updated:
            stale.append(f"{path.name}:missing-last_updated")
            continue
        age = (today - parse_day(updated)).days
        if age > CHECKPOINT_MAX_STALE_DAYS:
            stale.append(f"{path.name}:{age}d")
    return stale


def main() -> None:
    for path in (LINKS, SCENARIOS):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    today = datetime.now(TZ).date()
    link_count, stale_links = check_links_stale(today)
    brief_ok = check_brief_today(today)
    stale_runs = check_running_checkpoints(today)

    if stale_links:
        fail(
            f"LINKS.json stale>{LINKS_MAX_STALE_DAYS}d: {', '.join(stale_links)}"
        )
    if not brief_ok:
        fail(
            f"no brief artifact for {today.isoformat()} "
            f"(want BRIEF-{today}.md or hq/brief-{today}.json)"
        )
    if stale_runs:
        fail(
            f"running checkpoints stale>{CHECKPOINT_MAX_STALE_DAYS}d: "
            f"{', '.join(stale_runs)}"
        )

    print(
        f"OK staleness links={link_count} brief={today.isoformat()} "
        f"running_checkpoints=0 stale"
    )


if __name__ == "__main__":
    main()
