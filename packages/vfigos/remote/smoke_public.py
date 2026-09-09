#!/usr/bin/env python3
"""Public-URL smoke for VelvetOS Instagram remote MCP.

Requires env:
  INSTAGRAM_MCP_REMOTE_URL   (…/mcp)
  VELVET_INSTAGRAM_MCP_BEARER_TOKEN

Checks: no-auth 401, initialize → initialized → tools/list,
healthcheck, get_profile (@velvets_cloud), list_media.
Never calls publish_*.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

EXPECTED_USER = "velvets_cloud"


def _post(url: str, body: dict, *, token: str | None, sid: str | None = None):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if sid:
        req.add_header("Mcp-Session-Id", sid)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.headers.get("Mcp-Session-Id"), resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Mcp-Session-Id") if exc.headers else None, (
            exc.read().decode() if exc.fp else ""
        )


def _sse_payloads(raw: str) -> list[dict]:
    out: list[dict] = []
    for m in re.finditer(r"^data: (.+)$", raw, re.M):
        out.append(json.loads(m.group(1)))
    if raw.strip().startswith("{"):
        out.append(json.loads(raw))
    return out


def _tool_result(payloads: list[dict]) -> dict:
    if not payloads:
        raise AssertionError("empty tools/call response")
    result = payloads[0].get("result") or {}
    text = None
    for c in result.get("content") or []:
        if c.get("type") == "text":
            text = c.get("text")
            break
    if not text:
        raise AssertionError(f"no text content: {result!r}")
    return json.loads(text)


def main() -> int:
    url = (os.environ.get("INSTAGRAM_MCP_REMOTE_URL") or "").strip()
    token = (os.environ.get("VELVET_INSTAGRAM_MCP_BEARER_TOKEN") or "").strip()
    if not url or not token:
        print("FAIL: need INSTAGRAM_MCP_REMOTE_URL + VELVET_INSTAGRAM_MCP_BEARER_TOKEN", file=sys.stderr)
        return 2

    report: dict = {"url": url, "checks": {}}

    code, _, _ = _post(
        url,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "noauth", "version": "1"},
            },
        },
        token=None,
    )
    report["checks"]["noauth_401"] = code == 401
    if code != 401:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print("FAIL: expected 401 without bearer", file=sys.stderr)
        return 1

    code, sid, raw = _post(
        url,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "velvet-smoke", "version": "1"},
            },
        },
        token=token,
    )
    payloads = _sse_payloads(raw)
    proto = (payloads[0].get("result") or {}).get("protocolVersion") if payloads else None
    report["checks"]["initialize"] = code == 200 and bool(sid) and proto is not None
    report["protocolVersion"] = proto
    report["session"] = sid

    code2, sid, _ = _post(
        url,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        token=token,
        sid=sid,
    )
    report["checks"]["initialized"] = code2 in (200, 202)

    code3, sid, raw = _post(
        url,
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        token=token,
        sid=sid,
    )
    tools = (_sse_payloads(raw)[0].get("result") or {}).get("tools") if code3 == 200 else []
    names = [t.get("name") for t in tools]
    report["checks"]["tools_list"] = code3 == 200 and "healthcheck" in names and "get_profile" in names
    report["tool_count"] = len(names)

    def call(name: str, arguments: dict | None = None, rid: int = 10):
        c, s, r = _post(
            url,
            {
                "jsonrpc": "2.0",
                "id": rid,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments or {}},
            },
            token=token,
            sid=sid,
        )
        return c, _tool_result(_sse_payloads(r)) if c == 200 else {}

    c, hc = call("healthcheck", rid=11)
    live = (hc.get("live_check") or {}) if isinstance(hc, dict) else {}
    report["checks"]["healthcheck"] = c == 200 and hc.get("ok") is True and live.get("ok") is True
    report["live_check_username"] = live.get("username")

    c, prof = call("get_profile", rid=12)
    username = ((prof.get("profile") or {}).get("username") if isinstance(prof, dict) else None)
    report["checks"]["get_profile"] = c == 200 and username == EXPECTED_USER
    report["profile_username"] = username

    c, media = call("list_media", {"limit": 3}, rid=13)
    count = media.get("count") if isinstance(media, dict) else None
    items = media.get("media") or media.get("data") or []
    usernames = {i.get("username") for i in items if isinstance(i, dict)}
    report["checks"]["list_media"] = (
        c == 200 and isinstance(count, int) and count >= 1 and (not usernames or usernames == {EXPECTED_USER})
    )
    report["list_media_count"] = count

    ok = all(report["checks"].values())
    report["ok"] = ok
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
