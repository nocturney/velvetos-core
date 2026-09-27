#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "packages" / "velvetos" / "TOOL-STATUS.json"
OPENPOST = ROOT / "packages" / "vfigos" / "OPENPOST.json"
GROK = ROOT / "automation" / "grok" / "manifest.json"
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
    scheduler_rows = list(grok.get("routines") or []) + list(grok.get("retiredRoutines") or [])
    for row in scheduler_rows:
        if str(row.get("id") or "").casefold() == "openpost-release-watch" or str(row.get("title") or "").casefold() == "openpost release watch":
            fail("OpenPost Release Watch must be deleted from Grok scheduler authority")

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
