#!/usr/bin/env python3
"""Public-URL smoke for VelvetOS Instagram remote MCP.

Requires env:
  INSTAGRAM_MCP_REMOTE_URL   (…/mcp)
  VELVET_INSTAGRAM_MCP_BEARER_TOKEN

Checks: no-auth 401, initialize → initialized → tools/list,
healthcheck, get_profile (@velvets_cloud), list_media.
Optional Insights Graph v21 checks (reported; fail suite only when
INSTAGRAM_MCP_INSIGHTS_EXPECT_FIXED=1 after production deploy).
Never calls publish_* / delete_media / DM.
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
    # Starlette Mount may 307 /mcp → /mcp/; urllib does not preserve auth on that hop.
    if code in (301, 302, 307, 308) and not url.endswith("/"):
        alt = url + "/"
        code2, _, _ = _post(
            alt,
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
        if code2 == 401:
            url = alt
            report["url"] = url
            report["checks"]["slash_redirect_workaround"] = True
            code = code2

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

    # Insights Graph v21 — do not invent metrics; surface Meta errors.
    c, ins_default = call("get_account_insights", {"period": "day"}, rid=14)
    default_ok = c == 200 and isinstance(ins_default, dict) and ins_default.get("ok") is True
    default_err = (ins_default or {}).get("error") if isinstance(ins_default, dict) else None
    report["insights"] = {
        "default_ok": default_ok,
        "default_error": default_err,
        "impressions_rejected": bool(default_err and "impressions" in str(default_err).lower())
        or bool(default_err and "metric[1]" in str(default_err)),
    }
    c, ins_mixed = call(
        "get_account_insights",
        {
            "period": "day",
            "metrics": "reach,profile_views,follower_count,total_interactions",
        },
        rid=15,
    )
    mixed_ok = c == 200 and isinstance(ins_mixed, dict) and (
        ins_mixed.get("ok") is True or ins_mixed.get("partial") is True
    )
    mixed_err = (ins_mixed or {}).get("error") if isinstance(ins_mixed, dict) else None
    report["insights"]["mixed_ok"] = mixed_ok
    report["insights"]["mixed_error"] = mixed_err
    report["insights"]["metric_type_error"] = bool(
        mixed_err and "metric_type=total_value" in str(mixed_err)
    )
    expect_fixed = os.environ.get("INSTAGRAM_MCP_INSIGHTS_EXPECT_FIXED", "").strip() in {
        "1",
        "true",
        "yes",
    }
    report["insights"]["expect_fixed"] = expect_fixed

    # Follow-up regressions (ChatGPT live 2026-09-09): media default + days_28 partition.
    media_id = None
    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        if (item.get("media_product_type") or "").upper() == "REELS":
            media_id = item["id"]
            break
        if media_id is None:
            media_id = item["id"]
    if media_id:
        c, media_ins = call("get_media_insights", {"media_id": media_id}, rid=17)
    else:
        c, media_ins = 0, {"ok": False, "error": "no media_id"}
    media_ok = (
        c == 200
        and isinstance(media_ins, dict)
        and media_ins.get("ok") is True
        and "saves" not in (media_ins.get("metrics_requested") or [])
    )
    media_err = (media_ins or {}).get("error") if isinstance(media_ins, dict) else None
    report["insights"]["media_default_ok"] = media_ok
    report["insights"]["media_default_error"] = media_err
    report["insights"]["media_id"] = media_id
    report["insights"]["media_saves_leaked"] = bool(
        isinstance(media_ins, dict)
        and "saves" in (media_ins.get("metrics_requested") or [])
    ) or bool(media_err and "metric[4]" in str(media_err))

    c, days28 = call(
        "get_account_insights",
        {
            "period": "days_28",
            "metrics": (
                "reach,follower_count,profile_views,total_interactions,"
                "likes,comments,shares,saves"
            ),
        },
        rid=18,
    )
    days28_ok = c == 200 and isinstance(days28, dict) and days28.get("ok") is True
    days28_partial = bool(isinstance(days28, dict) and days28.get("partial"))
    days28_names = {
        row.get("name")
        for row in ((days28 or {}).get("insights") or [])
        if isinstance(row, dict)
    }
    days28_err_classes = {
        p.get("error_class")
        for p in ((days28 or {}).get("partial_errors") or [])
        if isinstance(p, dict)
    }
    report["insights"]["days28_ok"] = days28_ok
    report["insights"]["days28_partial"] = days28_partial
    report["insights"]["days28_insight_names"] = sorted(n for n in days28_names if n)
    report["insights"]["days28_error"] = (
        (days28 or {}).get("error") if isinstance(days28, dict) else None
    )
    report["insights"]["days28_whole_snapshot_failed"] = bool(
        isinstance(days28, dict)
        and days28.get("ok") is False
        and "incompatible with the metric (follower_count)" in str(days28.get("error") or "")
    )

    if expect_fixed:
        report["checks"]["insights_default"] = default_ok and not report["insights"]["impressions_rejected"]
        report["checks"]["insights_mixed"] = mixed_ok and not report["insights"]["metric_type_error"]
        report["checks"]["insights_media_default"] = media_ok and not report["insights"]["media_saves_leaked"]
        report["checks"]["insights_days28_partial"] = (
            days28_ok
            and days28_partial
            and "reach" in days28_names
            and "period_incompatible" in days28_err_classes
            and not report["insights"]["days28_whole_snapshot_failed"]
        )
    else:
        report["insights"]["note"] = (
            "Insights reported only — set INSTAGRAM_MCP_INSIGHTS_EXPECT_FIXED=1 after "
            "Cloud Run deploy of remote/insights_v21.py to gate the suite on them."
        )

    # Mutation SoT — unsupported writes must NOT appear as tools.
    tool_set = set(names)
    banned_writes = {
        "update_profile",
        "update_media_caption",
        "update_biography",
        "update_website",
        "update_name",
        "archive_media",
    }
    if "graph_mutation_matrix" in tool_set:
        report["checks"]["no_misleading_write_tools"] = tool_set.isdisjoint(banned_writes)
        report["checks"]["mutation_sot_present"] = "graph_mutation_matrix" in tool_set
        c, matrix = call("graph_mutation_matrix", rid=16)
        report["checks"]["graph_mutation_matrix"] = (
            c == 200
            and isinstance(matrix, dict)
            and matrix.get("ok") is True
            and "matrix" in matrix
        )
        if isinstance(matrix, dict):
            m = matrix.get("matrix") or {}
            report["checks"]["matrix_profile_unsupported"] = (
                (m.get("update_profile") or {}).get("supported") is False
                and (m.get("update_media_caption") or {}).get("supported") is False
            )
    elif expect_fixed:
        report["checks"]["mutation_sot_present"] = False

    ok = all(report["checks"].values())
    report["ok"] = ok
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
