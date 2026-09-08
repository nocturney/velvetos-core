#!/usr/bin/env python3
"""Light send preflight — local readiness only. No network. No send.

Reads desk tool status + env key presence + CONNECT-IG markers.
Prints one JSON object so HQ can failover before claiming a send.

Usage:
  python3 scripts/vf_send_preflight.py
  python3 scripts/vf_send_preflight.py --gate gmail
  python3 scripts/vf_send_preflight.py --gate instagram
  python3 scripts/vf_send_preflight.py --gate canva

Exit codes:
  0 — report ok (and gate channel is ready, if --gate set)
  2 — gate channel needs failover (still actionable — do not idle)
  1 — missing desk / unknown gate / hard block
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / ".cursor" / "vf-desk.json"
CONNECT_IG = ROOT / "packages" / "vfigos" / "CONNECT-IG.md"
SEND = ROOT / "constitution" / "SEND.md"

# Statuses that mean "use this tool for the primary path"
READY = {"ready", "skill-installed", "plugin-installed", "hq-native"}
IG_AUTH_READY = {"ready", "ready-codespace", "ready-local"}
# Statuses that mean "primary path blocked — failover same turn"
FAILOVER = {"needsAuth", "needs-key", "down", "not-on-this-cloud-agent"}


def _env_present(*names: str) -> bool:
    return any((os.environ.get(n) or "").strip() for n in names)


def _tool(desk: dict[str, Any], name: str) -> dict[str, Any]:
    tools = desk.get("tools") or {}
    row = tools.get(name) or {}
    return row if isinstance(row, dict) else {}


def channel_report(desk: dict[str, Any]) -> dict[str, Any]:
    gmail = _tool(desk, "gmail")
    canva = _tool(desk, "canva")
    ig = _tool(desk, "instagram")
    gemini = _tool(desk, "gemini")
    chatgpt = _tool(desk, "chatgpt")

    ig_status = ig.get("status") or ""
    ig_remote = ig.get("remote_access") or ""
    ig_auth_ok = ig_status in IG_AUTH_READY or (ig.get("auth") == "ready")
    # Live primary path needs auth-ready AND (remote ready OR local MCP secrets present)
    ig_secrets = _env_present("INSTAGRAM_MCP_ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN")
    ig_session_ready = ig_auth_ok and (
        ig_remote == "ready" or (ig_secrets and ig_status in IG_AUTH_READY)
    )
    # remote_access pending without secrets → failover (Cloud / stopped Codespace honesty)
    ig_needs_failover = (
        ig_status in FAILOVER
        or ig_status == "needsAuth"
        or not ig_auth_ok
        or (ig_remote == "pending" and not ig_secrets)
    )

    gemini_key = _env_present("GEMINI_API_KEY", "GOOGLE_API_KEY")
    chatgpt_key = _env_present("OPENAI_API_KEY", "CHATGPT_API_KEY")

    channels = {
        "gmail": {
            "desk_status": gmail.get("status") or "unknown",
            "ready": (gmail.get("status") or "") in READY,
            "action": "send_message / reply / forward",
            "failover": "Drive create_file + continue; never invent inquiry",
            "note": "Desk status only — MCP auth is runtime. Failover if tool call fails.",
        },
        "canva": {
            "desk_status": canva.get("status") or "unknown",
            "ready": (canva.get("status") or "") in READY,
            "action": "generate-design / export-design",
            "failover": canva.get("failover")
            or "Canva לא מחובר → packages/vfcanva/studio/render.py → Superdesign",
        },
        "instagram": {
            "desk_status": ig_status or "unknown",
            "auth": ig.get("auth") or ("ready" if ig_auth_ok else "unknown"),
            "transport": ig.get("transport") or "stdio",
            "remote_access": ig_remote or "unknown",
            "ready": ig_session_ready and not ig_needs_failover,
            "needs_failover": ig_needs_failover,
            "action": "publish_image|carousel|reel|story (adelaidasofia/instagram-mcp) then list_media/get_media verify",
            "failover": "Canva + Drive create_file + Gmail same turn · #ממתין-ל-כלי-IG",
            "connect": "packages/vfigos/CONNECT-IG.md",
            "forbid": ["send_message DM", "auto-DM", "boost without lead", "INSTAGRAM_MCP_DM_ENABLED"],
        },
        "gemini": {
            "desk_status": gemini.get("status") or "unknown",
            "key_present": gemini_key,
            "ready": gemini_key,
            "action": "python3 scripts/vf_gemini.py",
            "failover": "חסר מפתח Gemini → ChatGPT API + Perplexity + WebSearch",
            "note": "API key only. Do not open gemini.google.com from Cloud.",
        },
        "chatgpt": {
            "desk_status": chatgpt.get("status") or "unknown",
            "key_present": chatgpt_key,
            "ready": chatgpt_key,
            "action": "python3 scripts/vf_chatgpt.py",
            "failover": "חסר מפתח ChatGPT → Gemini API + Perplexity + WebSearch",
            "note": "API key only. Do not open chatgpt.com from Cloud.",
        },
    }
    return {
        "ok": True,
        "mode": "local-only",
        "send_law": str(SEND.relative_to(ROOT)) if SEND.is_file() else None,
        "channels": channels,
        "rule": "If primary not ready → failover same turn. Never idle. Never invent ₪ / Insights / blocked body.",
    }


def gate_channel(report: dict[str, Any], name: str) -> int:
    ch = (report.get("channels") or {}).get(name)
    if not ch:
        print(f"FAIL unknown gate channel {name!r}", file=sys.stderr)
        return 1
    if ch.get("ready"):
        print(f"GATE {name}=ready")
        return 0
    if ch.get("needs_failover") or not ch.get("ready"):
        print(f"GATE {name}=failover")
        return 2
    print(f"GATE {name}=blocked", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gate",
        choices=("gmail", "instagram", "canva", "gemini", "chatgpt"),
        help="Exit 0 if channel ready, 2 if failover required",
    )
    args = parser.parse_args()

    if not DESK.is_file():
        print("FAIL missing .cursor/vf-desk.json", file=sys.stderr)
        return 1

    desk = json.loads(DESK.read_text(encoding="utf-8"))
    report = channel_report(desk)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.gate:
        return gate_channel(report, args.gate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
