#!/usr/bin/env python3
"""Light send preflight — local readiness only. No network. No send.

Reads desk tool status + env key presence + CONNECT-IG markers + remote-health.json.
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
REMOTE_HEALTH = ROOT / "packages" / "vfigos" / "live" / "remote-health.json"

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


def _remote_health_ok() -> tuple[bool, dict[str, Any]]:
    """Cloud autonomy truth: remote-health.json from vf_instagram_mcp_remote_health.py."""
    if not REMOTE_HEALTH.is_file():
        return False, {"ok": False, "remote_access": "pending", "error": "missing remote-health.json"}
    try:
        data = json.loads(REMOTE_HEALTH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, {"ok": False, "remote_access": "degraded", "error": "remote-health.json unreadable"}
    if not isinstance(data, dict):
        return False, {"ok": False, "remote_access": "degraded", "error": "remote-health.json not object"}
    ok = data.get("ok") is True and data.get("remote_access") == "ready"
    return ok, data


def channel_report(desk: dict[str, Any]) -> dict[str, Any]:
    gmail = _tool(desk, "gmail")
    canva = _tool(desk, "canva")
    ig = _tool(desk, "instagram")
    gemini = _tool(desk, "gemini")
    chatgpt = _tool(desk, "chatgpt")

    ig_status = ig.get("status") or ""
    ig_remote = ig.get("remote_access") or ""
    ig_auth_ok = ig_status in IG_AUTH_READY or (ig.get("auth") == "ready")
    ig_secrets = _env_present("INSTAGRAM_MCP_ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN")
    remote_ok, remote_blob = _remote_health_ok()

    # Cloud autonomy: desk remote_access ready AND verified remote-health.json
    # Codespace/local secrets alone NEVER count as cloud autonomy.
    ig_cloud_ready = ig_remote == "ready" and remote_ok
    # Local/dev session (Codespace stdio with Meta secrets) — publish possible on that host only
    ig_local_ready = bool(ig_auth_ok and ig_secrets and ig_status in IG_AUTH_READY)
    # Gate "ready" for publish: cloud verified OR local secrets session
    ig_session_ready = ig_cloud_ready or ig_local_ready

    # Honesty: desk claiming remote ready without health file → not ready (sensor also fails)
    fake_remote = ig_remote == "ready" and not remote_ok
    # Cloud / stopped Codespace: remote pending + no Meta secrets on this agent → failover
    ig_needs_failover = (
        fake_remote
        or ig_status in FAILOVER
        or ig_status == "needsAuth"
        or not ig_auth_ok
        or (not ig_session_ready)
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
            "cloud_autonomy_ready": ig_cloud_ready,
            "local_stdio_session": ig_local_ready and not ig_cloud_ready,
            "remote_health_ok": remote_ok,
            "remote_health": {
                "ok": remote_blob.get("ok"),
                "remote_access": remote_blob.get("remote_access"),
                "error": remote_blob.get("error"),
                "endpoint": remote_blob.get("endpoint"),
            },
            "ready": ig_session_ready and not fake_remote,
            "needs_failover": ig_needs_failover,
            "action": "publish_image|carousel|reel|story (adelaidasofia/instagram-mcp) then list_media/get_media verify",
            "failover": "Canva + Drive create_file + Gmail same turn · #ממתין-ל-כלי-IG",
            "connect": "packages/vfigos/CONNECT-IG.md",
            "remote": "packages/vfigos/REMOTE.md",
            "forbid": ["send_message DM", "auto-DM", "boost without lead", "INSTAGRAM_MCP_DM_ENABLED"],
            "note": (
                "cloud_autonomy_ready requires remote_access=ready AND remote-health.json ok; "
                "Codespace stdio alone does not satisfy Cloud Agent autonomy"
            ),
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
