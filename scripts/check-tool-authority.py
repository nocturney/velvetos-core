#!/usr/bin/env python3
from pathlib import Path
import json
from datetime import datetime
import sys

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "packages" / "velvetos" / "TOOL-STATUS.json"
OPENPOST = ROOT / "packages" / "vfigos" / "OPENPOST.json"
GROK = ROOT / "automation" / "grok" / "manifest.json"
OPENPOST_WATCH_REMOVAL = ROOT / "automation" / "grok" / "openpost-release-watch-removal.json"
SEND = ROOT / "packages" / "vfigos" / "SEND.md"
MORNING = ROOT / "packages" / "vfbriefux" / "FEED-SOURCE.json"


def fail(message: str) -> None:
    print(f"TOOL AUTHORITY FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    registry = json.loads(REG.read_text(encoding="utf-8"))
    tools = registry.get("tools") or {}
    if (tools.get("openpost") or {}).get("status") != "frozen":
        fail("OpenPost must remain frozen")
    if (tools.get("cloudflare-instagram-publisher") or {}).get("status") != "active":
        fail("Cloudflare Instagram Publisher must be active")

    op = json.loads(OPENPOST.read_text(encoding="utf-8"))
    op_status = op.get("status")
    if isinstance(op_status, dict):
        frozen = op_status.get("state") == "paused" and op_status.get("publishingFrozen") is True
    else:
        frozen = str(op_status or "").upper() == "FROZEN"
    if not frozen:
        fail("OPENPOST.json must remain paused/frozen")
    for key in ("newSchedulesAllowed", "queueAuthority", "retryAuthority", "failoverTarget", "releaseWatchEnabled", "healthDependency"):
        if op.get(key) is not False:
            fail(f"OPENPOST.json {key} must be false while frozen")

    grok = json.loads(GROK.read_text(encoding="utf-8"))
    scheduler_rows = list(grok.get("routines") or [])
    for row in scheduler_rows:
        if str(row.get("id") or "").casefold() == "openpost-release-watch" or str(row.get("title") or "").casefold() == "openpost release watch":
            fail("OpenPost Release Watch must be absent from active Grok scheduler authority")

    if not OPENPOST_WATCH_REMOVAL.is_file():
        fail("live OpenPost watch removal evidence is missing")
    removal = json.loads(OPENPOST_WATCH_REMOVAL.read_text(encoding="utf-8"))
    if removal.get("schema") != "velvetos.grok-routine-removal.v1":
        fail("OpenPost watch removal evidence schema mismatch")
    routine = removal.get("routine") or {}
    readback = removal.get("provider_readback") or {}
    if routine.get("title") != "OpenPost Release Watch" or routine.get("action") != "delete":
        fail("OpenPost watch removal evidence must identify the deleted routine")
    if readback.get("routine_present") is not False or readback.get("remaining_count") != 8:
        fail("OpenPost watch provider readback must prove absence with exactly 8 routines remaining")
    remaining_titles = set(readback.get("remaining_titles") or [])
    removal_binding = (grok.get("publisherAuthority") or {}).get("openpostReleaseWatchRemoval") or {}
    # Compare the 2026-09-27 removal readback with the routines that were protected
    # at that time; routines added later carry protectedFrom and are not back-filled.
    removal_at = datetime.fromisoformat(str(removal_binding.get("verifiedAt") or "").replace("Z", "+00:00"))
    manifest_titles = set()
    for row in grok.get("routines") or []:
        since = row.get("protectedFrom")
        if since is None or datetime.fromisoformat(str(since).replace("Z", "+00:00")) <= removal_at:
            manifest_titles.add(str(row.get("title") or ""))
    if remaining_titles != manifest_titles:
        fail("live Grok readback titles must match the protected manifest routine set at removal time")
    if removal_binding.get("state") != "live_verified_deleted" or removal_binding.get("evidence") != "automation/grok/openpost-release-watch-removal.json":
        fail("Grok manifest must bind the live-verified OpenPost watch deletion evidence")
    openpost_tool = tools.get("openpost") or {}
    if openpost_tool.get("release_watch_provider_state") != "deleted_verified":
        fail("TOOL-STATUS must record the verified live OpenPost watch deletion")
    if openpost_tool.get("release_watch_evidence") != "automation/grok/openpost-release-watch-removal.json":
        fail("TOOL-STATUS OpenPost watch evidence path mismatch")

    send = SEND.read_text(encoding="utf-8")
    if "Cloudflare Worker" not in send or "Meta Instagram Graph API" not in send:
        fail("SEND.md must route scheduled publication to Cloudflare + Meta Graph")

    feed = json.loads(MORNING.read_text(encoding="utf-8"))
    if "cloudflare_publisher" not in feed:
        fail("Morning Green feed source must be Cloudflare publisher")
    if (feed.get("openpost") or {}).get("state") in {"active", "ready", "live"}:
        fail("Morning Green must not activate OpenPost")

    print("TOOL AUTHORITY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
