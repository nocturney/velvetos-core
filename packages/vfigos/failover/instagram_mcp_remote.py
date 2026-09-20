"""Server-side Instagram MCP helper for VelvetOS failover.

Runs on openpost-prod so the MCP bearer stays server-side. Output is deliberately
whitelisted; receipts, signatures, tokens and raw provider payloads are never
printed.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import urllib.request
from typing import Any

DEFAULT_URL = "https://velvet-instagram-mcp-1016876126699.me-west1.run.app/mcp"
DEFAULT_BEARER_FILE = "/var/lib/openpost/velvet-instagram-mcp.bearer"


def _payload(raw: str) -> dict[str, Any]:
    for line in raw.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    return json.loads(raw)


def _post(url: str, bearer: str, body: dict[str, Any], sid: str = "", timeout: int = 120) -> tuple[str, str]:
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    req.add_header("Authorization", "Bearer " + bearer)
    if sid:
        req.add_header("Mcp-Session-Id", sid)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.headers.get("Mcp-Session-Id", sid), response.read().decode("utf-8", "replace")


def _call(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    url = os.environ.get("VELVET_INSTAGRAM_MCP_URL", DEFAULT_URL).strip()
    bearer_file = Path(os.environ.get("VELVET_INSTAGRAM_MCP_BEARER_FILE", DEFAULT_BEARER_FILE))
    bearer = bearer_file.read_text(encoding="utf-8").strip()
    if not bearer:
        raise RuntimeError("empty MCP bearer")

    sid, _ = _post(
        url,
        bearer,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "velvetos-instagram-failover", "version": "1"},
            },
        },
    )
    _post(url, bearer, {"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    _, raw = _post(
        url,
        bearer,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        },
        sid,
    )
    bearer = ""
    p = _payload(raw)
    if p.get("error"):
        err = p["error"] if isinstance(p["error"], dict) else {}
        return {"ok": False, "rpc_error_code": err.get("code"), "rpc_error_message": err.get("message")}

    result = p.get("result") or {}
    for item in result.get("content") or []:
        if item.get("type") != "text":
            continue
        try:
            data = json.loads(item.get("text") or "{}")
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return {"ok": False, "error": "no JSON text result from MCP"}


def _safe_media_item(m: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": m.get("id"),
        "caption": m.get("caption"),
        "media_type": m.get("media_type"),
        "media_product_type": m.get("media_product_type"),
        "permalink": m.get("permalink"),
        "timestamp": m.get("timestamp"),
        "username": m.get("username"),
    }


def _safe_list(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": data.get("ok"),
        "account": data.get("account"),
        "count": data.get("count"),
        "media": [_safe_media_item(m) for m in (data.get("media") or []) if isinstance(m, dict)],
    }


def _safe_publish(data: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "ok",
        "account",
        "media_id",
        "id",
        "permalink",
        "error",
        "error_class",
        "stage",
        "provider_code",
        "provider_subcode",
        "http_status",
        "provider_type",
        "write_outcome",
        "retry_safety",
        "problems",
        "blocked",
    )
    return {key: data.get(key) for key in keys if key in data}


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    ls = sub.add_parser("list-media")
    ls.add_argument("--limit", type=int, default=25)

    gm = sub.add_parser("get-media")
    gm.add_argument("--media-id", required=True)

    pc = sub.add_parser("publish-call")
    pc.add_argument("--call", required=True)

    args = parser.parse_args()
    if args.command == "list-media":
        data = _call("list_media", {"account": "env", "limit": max(1, min(args.limit, 100))})
        print(json.dumps(_safe_list(data), ensure_ascii=False))
        return 0 if data.get("ok") is True else 2

    if args.command == "get-media":
        data = _call("get_media", {"account": "env", "media_id": args.media_id})
        media = data.get("media") if isinstance(data.get("media"), dict) else {}
        safe = {"ok": data.get("ok"), "account": data.get("account"), "media": _safe_media_item(media)}
        if data.get("error"):
            safe["error"] = data.get("error")
        print(json.dumps(safe, ensure_ascii=False))
        return 0 if data.get("ok") is True else 2

    call = json.loads(Path(args.call).read_text(encoding="utf-8"))
    if call.get("name") != "publish_image" or not isinstance(call.get("arguments"), dict):
        raise SystemExit("BLOCKED: call file must contain publish_image arguments")
    data = _call("publish_image", call["arguments"])
    print(json.dumps(_safe_publish(data), ensure_ascii=False))
    return 0 if data.get("ok") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
