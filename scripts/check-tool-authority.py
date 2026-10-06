#!/usr/bin/env python3
from pathlib import Path
import json
from datetime import datetime
import sys

ROOT = Path(__file__).resolve().parents[1]
VELVETOS_PACK = ROOT / "packages" / "velvetos"
if str(VELVETOS_PACK) not in sys.path:
    sys.path.insert(0, str(VELVETOS_PACK))
from tool_status_resolver import compose_tool_status  # noqa: E402
OPENPOST = ROOT / "packages" / "vfigos" / "OPENPOST.json"
GROK = ROOT / "automation" / "grok" / "manifest.json"
OPENPOST_WATCH_REMOVAL = ROOT / "automation" / "grok" / "openpost-release-watch-removal.json"
SEND = ROOT / "packages" / "vfigos" / "SEND.md"
MORNING = ROOT / "packages" / "vfbriefux" / "FEED-SOURCE.json"


def fail(message: str) -> None:
    print(f"TOOL AUTHORITY FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    registry = compose_tool_status(ROOT, instance_id="velvet-factory", env={})
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
    # The 2026-09-27 removal witness is historical. Current Grok authority is retired,
    # so replay it against its own recorded cardinality rather than today's empty set.
    if len(remaining_titles) != 8 or removal_binding.get("remainingRoutineCount") != 8:
        fail("historical OpenPost watch removal witness must preserve its eight-routine readback")
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
