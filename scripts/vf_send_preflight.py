#!/usr/bin/env python3
"""Send preflight for VelvetOS.

Two different checks live here and must never be confused:
1. transport readiness — local desk/session/env readiness only;
2. publication quality approval — exact content approval required before Instagram publish.

For Instagram publish, the default is fail-closed and requires a machine-readable
PREFLIGHT v2 bound to the exact final package. Use --transport-only only for health
or diagnostics; its success is explicitly NOT publish authorization.

Usage:
  python3 scripts/vf_send_preflight.py
  python3 scripts/vf_send_preflight.py --gate gmail
  python3 scripts/vf_send_preflight.py --gate instagram --transport-only
  python3 scripts/vf_send_preflight.py --gate instagram \
    --content-id G004 --format story \
    --approval-ref packages/vfgrowth/preflight/G004.md \
    --package-sha256 <sha256-of-ordered-final-package>

Exit codes:
  0 — requested gate is ready and, for Instagram publish, quality approval is valid
  2 — transport gate needs failover
  1 — missing/invalid approval, unknown gate, or hard block
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / ".cursor" / "vf-desk.json"
CONNECT_IG = ROOT / "packages" / "vfigos" / "CONNECT-IG.md"
SEND = ROOT / "constitution" / "SEND.md"
PREFLIGHT_ROOT = ROOT / "packages" / "vfgrowth" / "preflight"

# Statuses that mean "use this tool for the primary path"
READY = {"ready", "skill-installed", "plugin-installed", "hq-native"}
IG_AUTH_READY = {"ready", "ready-codespace", "ready-local"}
# Statuses that mean "primary path blocked — failover same turn"
FAILOVER = {"needsAuth", "needs-key", "down", "not-on-this-cloud-agent"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)


def _env_present(*names: str) -> bool:
    return any((os.environ.get(n) or "").strip() for n in names)


def _tool(desk: dict[str, Any], name: str) -> dict[str, Any]:
    tools = desk.get("tools") or {}
    row = tools.get(name) or {}
    return row if isinstance(row, dict) else {}


def _field(text: str, name: str) -> str | None:
    """Read a simple machine field from Markdown, including fenced YAML blocks."""
    match = re.search(
        rf"(?mi)^\s*(?:[-*]\s*)?`?{re.escape(name)}`?\s*:\s*(.*?)\s*$",
        text,
    )
    if not match:
        return None
    value = match.group(1).strip().strip("`").strip()
    return value or None


def _clean_sha(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().lower()
    if value.startswith("sha256:"):
        value = value.split(":", 1)[1].strip()
    return value if SHA256_RE.fullmatch(value) else None


def validate_publication_approval(
    approval_ref: str,
    content_id: str,
    format_name: str,
    package_sha256: str,
) -> dict[str, Any]:
    """Validate a fail-closed PREFLIGHT v2 for an exact Instagram package."""
    problems: list[str] = []
    approval_path = (ROOT / approval_ref).resolve()
    try:
        approval_path.relative_to(PREFLIGHT_ROOT.resolve())
    except ValueError:
        problems.append("approval-ref must stay under packages/vfgrowth/preflight")
        return {"ok": False, "problems": problems, "approvalRef": approval_ref}

    if not approval_path.is_file():
        problems.append(f"approval-ref does not exist: {approval_ref}")
        return {"ok": False, "problems": problems, "approvalRef": approval_ref}

    if approval_path.stem != content_id:
        problems.append(
            f"approval/content mismatch: {approval_path.stem!r} != {content_id!r}"
        )

    text = approval_path.read_text(encoding="utf-8")
    schema = (_field(text, "publish_gate_schema") or "").strip()
    gate = (_field(text, "publish_gate") or "").strip().upper()
    invalidated = (_field(text, "approval_invalidated") or "false").strip().lower()

    if schema != "2":
        problems.append("PREFLIGHT v2 required: publish_gate_schema: 2")
    if gate not in {"PASS", "עבור"}:
        problems.append("publish_gate must be PASS")
    if invalidated in {"1", "true", "yes", "כן"}:
        problems.append("approval is explicitly invalidated")

    rubric = _field(text, "content_rubric_total")
    rubric_match = re.fullmatch(r"\s*(\d{1,2})\s*/\s*25\s*", rubric or "")
    if not rubric_match:
        problems.append("content_rubric_total must be explicit, e.g. 22/25")
    elif int(rubric_match.group(1)) < 20:
        problems.append("CONTENT-RUBRIC total is below 20/25")

    artifact_digest = _clean_sha(_field(text, "artifact_digest"))
    if artifact_digest is None:
        problems.append("artifact_digest must be sha256:<64 hex>")

    if format_name == "story":
        required_pass_fields = {
            "qa_scope": "exact-final-render",
            "brand_guardian": "PASS",
            "copy_qa": "PASS",
            "readability": "PASS",
            "contrast": "PASS",
        }
        for field, expected in required_pass_fields.items():
            actual = (_field(text, field) or "").strip()
            if actual.upper() != expected.upper():
                problems.append(f"{field} must be {expected}")

        reviewed_at = (_field(text, "qa_reviewed_at") or "").strip()
        if not reviewed_at or "<" in reviewed_at or "_" == reviewed_at:
            problems.append("qa_reviewed_at must identify the final-render review")

        approved_package = _clean_sha(_field(text, "final_package_sha256"))
        supplied_package = _clean_sha(package_sha256)
        if approved_package is None:
            problems.append("final_package_sha256 missing/invalid in PREFLIGHT")
        if supplied_package is None:
            problems.append("--package-sha256 must be a 64-hex SHA-256")
        if approved_package and supplied_package and approved_package != supplied_package:
            problems.append("exact final package SHA-256 does not match the approved render")

        # A known anti-pattern from G004: weak contrast cannot be waived as non-blocking.
        lowered = text.lower()
        if "ניגודיות" in text and "לא חוסם" in text:
            problems.append("contrast/readability may not be waived as non-blocking")
        if "soft contrast" in lowered and "non-block" in lowered:
            problems.append("soft contrast may not be waived as non-blocking")

    return {
        "ok": not problems,
        "approvalRef": approval_ref,
        "contentId": content_id,
        "format": format_name,
        "publishGateSchema": schema or None,
        "packageSha256": _clean_sha(package_sha256),
        "problems": problems,
        "rule": "quality approval must cover the exact final render; transport success alone never authorizes publish",
    }


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
    ig_session_ready = ig_auth_ok and (
        ig_remote == "ready" or (ig_secrets and ig_status in IG_AUTH_READY)
    )
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
        "rule": "Transport readiness is not creative approval. Instagram publish requires exact-package PREFLIGHT v2.",
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
        help="Exit 0 if requested gate is ready; Instagram publish also requires quality approval",
    )
    parser.add_argument("--transport-only", action="store_true", help="diagnostic only; never authorizes publish")
    parser.add_argument("--approval-ref", help="repo-relative packages/vfgrowth/preflight/<ID>.md")
    parser.add_argument("--content-id", help="content correlation, e.g. G004")
    parser.add_argument("--format", dest="format_name", choices=("story", "reel", "carousel", "post"))
    parser.add_argument("--package-sha256", help="SHA-256 of the ordered exact final package")
    args = parser.parse_args()

    if not DESK.is_file():
        print("FAIL missing .cursor/vf-desk.json", file=sys.stderr)
        return 1

    desk = json.loads(DESK.read_text(encoding="utf-8"))
    report = channel_report(desk)

    quality_failed = False
    if args.gate == "instagram":
        if args.transport_only:
            report["publication_quality"] = {
                "ok": None,
                "publishAuthorized": False,
                "mode": "transport-only",
                "rule": "diagnostic success cannot be used as publish approval",
            }
        else:
            missing = [
                flag
                for flag, value in (
                    ("--approval-ref", args.approval_ref),
                    ("--content-id", args.content_id),
                    ("--format", args.format_name),
                    ("--package-sha256", args.package_sha256),
                )
                if not value
            ]
            if missing:
                report["publication_quality"] = {
                    "ok": False,
                    "publishAuthorized": False,
                    "problems": ["missing required publish arguments: " + ", ".join(missing)],
                }
                quality_failed = True
            else:
                approval = validate_publication_approval(
                    args.approval_ref,
                    args.content_id,
                    args.format_name,
                    args.package_sha256,
                )
                approval["publishAuthorized"] = bool(approval.get("ok"))
                report["publication_quality"] = approval
                quality_failed = not bool(approval.get("ok"))

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if quality_failed:
        print("FAIL instagram publication quality gate", file=sys.stderr)
        return 1
    if args.gate:
        return gate_channel(report, args.gate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
