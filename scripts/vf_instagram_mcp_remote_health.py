#!/usr/bin/env python3
"""Remote Instagram MCP smoke test for VelvetOS.

Proves:
  Cloud/remote client → HTTPS MCP endpoint → healthcheck → Meta Graph → @velvets_cloud

Does NOT print secrets. Writes packages/vfigos/live/remote-health.json (no tokens).

Usage:
  python3 scripts/vf_instagram_mcp_remote_health.py
  python3 scripts/vf_instagram_mcp_remote_health.py --url https://HOST/mcp
  python3 scripts/vf_instagram_mcp_remote_health.py --write

Env:
  INSTAGRAM_MCP_REMOTE_URL          — https://…/mcp
  VELVET_INSTAGRAM_MCP_BEARER_TOKEN — MCP gate bearer (not Meta token)

Exit:
  0 — remote ready criteria met
  2 — actionable failure (pending / degraded / auth / transport)
  1 — hard misconfig
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "vfigos" / "live" / "remote-health.json"
EXPECTED_IG_USER_ID = "17841407772120429"
EXPECTED_USERNAME = "velvets_cloud"

SECRET_PATTERNS = (
    re.compile(r"EAA[A-Za-z0-9]+"),
    re.compile(r"IGQV[A-Za-z0-9]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{16,}"),
)


def _scrub(text: str) -> str:
    out = text
    for pat in SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _env_raw(name: str) -> str:
    return os.environ.get(name) or ""


def _bearer_has_internal_whitespace(raw: str) -> bool:
    """True when paste corruption put whitespace inside the token (not only ends)."""
    if not raw:
        return False
    return any(c.isspace() for c in raw.strip())


def _sanitize_bearer(raw: str) -> str:
    """Remove all whitespace from a paste-corrupted bearer. Never log the value."""
    return "".join((raw or "").split())


def _extract_payload(result: Any) -> dict[str, Any]:
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    if isinstance(result, dict):
        return result
    # CallToolResult content blocks
    content = getattr(result, "content", None)
    if content:
        for block in content:
            text = getattr(block, "text", None)
            if text:
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    pass
    return {"ok": False, "error": "unparseable_healthcheck_result", "raw_type": type(result).__name__}


async def _probe(url: str, bearer: str) -> dict[str, Any]:
    from fastmcp import Client

    report: dict[str, Any] = {
        "checkedAt": _now(),
        "endpoint": url,
        "transport": "streamable-http",
        "auth": "bearer",
        "ok": False,
        "remote_access": "degraded",
        "accounts_configured": None,
        "live_check_ok": None,
        "account": None,
        "ig_user_id": None,
        "error": None,
    }
    try:
        async with Client(url, auth=bearer) as client:
            tools = await client.list_tools()
            names = {t.name for t in tools}
            report["tools_seen"] = sorted(names)
            if "healthcheck" not in names:
                report["error"] = "healthcheck tool missing on remote MCP"
                return report
            raw = await client.call_tool("healthcheck", {})
            payload = _extract_payload(raw)
            report["healthcheck"] = {
                k: payload.get(k)
                for k in (
                    "ok",
                    "accounts_configured",
                    "default_account",
                    "dm_enabled",
                    "graph_version",
                    "live_check",
                    "hint",
                    "error",
                    "error_class",
                )
                if k in payload
            }
            accounts = payload.get("accounts_configured")
            report["accounts_configured"] = accounts
            live = payload.get("live_check") or {}
            live_ok = bool(isinstance(live, dict) and live.get("ok") is True)
            report["live_check_ok"] = live_ok

            username = None
            ig_id = None
            if isinstance(live, dict):
                username = live.get("username")
            default_acct = payload.get("default_account")
            if isinstance(default_acct, str):
                report["default_account_label"] = default_acct

            if "get_profile" in names and (accounts or 0) >= 1:
                try:
                    prof = _extract_payload(await client.call_tool("get_profile", {}))
                    if isinstance(prof, dict):
                        inner = prof.get("profile") if isinstance(prof.get("profile"), dict) else prof
                        username = username or inner.get("username")
                        ig_id = inner.get("id") or inner.get("ig_user_id") or prof.get("id")
                        report["profile_ok"] = bool(inner.get("username") or inner.get("id"))
                        # Never store biography / tokens — identity fields only
                        report["profile"] = {
                            k: inner.get(k)
                            for k in ("username", "id", "name", "account_type", "media_count")
                            if k in inner
                        }
                except Exception as exc:  # noqa: BLE001
                    report["profile_error"] = _scrub(str(exc))[:200]

            if "list_media" in names and (accounts or 0) >= 1:
                try:
                    media = _extract_payload(await client.call_tool("list_media", {}))
                    if isinstance(media, dict):
                        items = media.get("media") or media.get("data") or media.get("items")
                        count = media.get("count")
                        if not isinstance(count, int):
                            count = len(items) if isinstance(items, list) else None
                        report["list_media_ok"] = media.get("ok") is True or isinstance(items, list)
                        report["list_media_count"] = count
                        report["list_media_read_only"] = True
                    else:
                        report["list_media_ok"] = False
                        report["list_media_error"] = "unparseable_list_media_result"
                except Exception as exc:  # noqa: BLE001
                    report["list_media_ok"] = False
                    report["list_media_error"] = _scrub(str(exc))[:200]

            report["account"] = username
            report["ig_user_id"] = str(ig_id) if ig_id is not None else None

            identity_ok = False
            if report["account"] and str(report["account"]).lstrip("@") == EXPECTED_USERNAME:
                identity_ok = True
            if report["ig_user_id"] == EXPECTED_IG_USER_ID:
                identity_ok = True
            if report["ig_user_id"] and report["ig_user_id"] != EXPECTED_IG_USER_ID:
                identity_ok = False
                report["error"] = (
                    f"ig_user_id mismatch: got {report['ig_user_id']} "
                    f"expected {EXPECTED_IG_USER_ID}"
                )
            elif report["account"] and str(report["account"]).lstrip("@") != EXPECTED_USERNAME:
                identity_ok = False
                report["error"] = (
                    f"account mismatch: got {report['account']} expected @{EXPECTED_USERNAME}"
                )

            if (
                payload.get("ok") is True
                and isinstance(accounts, int)
                and accounts >= 1
                and live_ok
                and identity_ok
                and payload.get("dm_enabled") is not True
            ):
                report["ok"] = True
                report["remote_access"] = "ready"
                report["error"] = None
            elif payload.get("dm_enabled") is True:
                report["error"] = "dm_enabled must be false for VelvetOS"
                report["remote_access"] = "degraded"
            else:
                report["error"] = (
                    report["error"]
                    or payload.get("hint")
                    or payload.get("error")
                    or "healthcheck not ready"
                )
                report["remote_access"] = "degraded"
    except Exception as exc:  # noqa: BLE001
        report["error"] = _scrub(str(exc))[:400]
        report["remote_access"] = "degraded"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Override INSTAGRAM_MCP_REMOTE_URL")
    parser.add_argument("--write", action="store_true", help=f"Write {OUT.relative_to(ROOT)}")
    parser.add_argument("--json", action="store_true", help="Print report JSON to stdout")
    parser.add_argument(
        "--sanitize-whitespace",
        action="store_true",
        help=(
            "Recovery only: strip URL ends and remove ALL whitespace from bearer "
            "(paste-corruption workaround). Re-set Cursor Team secrets without spaces/newlines."
        ),
    )
    args = parser.parse_args()

    url_raw = args.url or _env_raw("INSTAGRAM_MCP_REMOTE_URL")
    bearer_raw = _env_raw("VELVET_INSTAGRAM_MCP_BEARER_TOKEN")
    url = (url_raw or "").strip()
    bearer = (bearer_raw or "").strip()
    env_notes: dict[str, Any] = {
        "url_had_edge_whitespace": bool(url_raw) and url_raw != url,
        "bearer_had_internal_whitespace": _bearer_has_internal_whitespace(bearer_raw),
        "bearer_len_raw": len(bearer_raw),
        "sanitized": False,
        "consumer": "cursor-cloud-agent",
        "transport_path": "streamable-http",
        "published": False,
    }

    if not url:
        report = {
            "checkedAt": _now(),
            "endpoint": None,
            "ok": False,
            "remote_access": "pending",
            "error": "INSTAGRAM_MCP_REMOTE_URL unset — remote autonomy not configured",
            "env": env_notes,
        }
        if args.write:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print("REMOTE Instagram MCP: pending (no INSTAGRAM_MCP_REMOTE_URL)")
        return 2

    if env_notes["bearer_had_internal_whitespace"]:
        if not args.sanitize_whitespace:
            print(
                "FAIL VELVET_INSTAGRAM_MCP_BEARER_TOKEN contains internal whitespace "
                "(paste corruption in Cursor Team / Cloud env). "
                "Re-set the secret from Secret Manager velvet-instagram-mcp-bearer "
                "with NO spaces/newlines. Or pass --sanitize-whitespace for one recovery probe.",
                file=sys.stderr,
            )
            report = {
                "checkedAt": _now(),
                "endpoint": url if url.startswith("https://") else None,
                "ok": False,
                "remote_access": "degraded",
                "error": "bearer_internal_whitespace",
                "env": env_notes,
            }
            if args.write:
                OUT.parent.mkdir(parents=True, exist_ok=True)
                OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            return 1
        bearer = _sanitize_bearer(bearer_raw)
        env_notes["sanitized"] = True
        env_notes["bearer_len_sanitized"] = len(bearer)

    if not url.startswith("https://"):
        print("FAIL remote URL must be https://", file=sys.stderr)
        return 1
    if not bearer or len(bearer) < 24:
        print("FAIL VELVET_INSTAGRAM_MCP_BEARER_TOKEN missing/short", file=sys.stderr)
        return 1
    if bearer.startswith("EAA") or bearer.startswith("IGQV"):
        print("FAIL bearer must not be the Meta Graph token", file=sys.stderr)
        return 1

    report = asyncio.run(_probe(url, bearer))
    report["env"] = env_notes
    # Never echo bearer / Meta tokens
    blob = json.dumps(report, ensure_ascii=False, indent=2)
    blob = _scrub(blob)

    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(blob + "\n", encoding="utf-8")

    if args.json or not args.write:
        print(blob)

    if report.get("ok") and report.get("remote_access") == "ready":
        print("REMOTE Instagram MCP: ready", file=sys.stderr)
        if env_notes.get("sanitized") or env_notes.get("url_had_edge_whitespace"):
            print(
                "WARN Cursor Team env still needs clean re-save "
                "(URL edge whitespace and/or bearer internal whitespace).",
                file=sys.stderr,
            )
        return 0
    print(f"REMOTE Instagram MCP: {report.get('remote_access')} — {report.get('error')}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
