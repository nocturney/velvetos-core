#!/usr/bin/env python3
"""Send preflight for VelvetOS.

Two different checks live here and must never be confused:
1. transport readiness — local desk/session/env readiness only;
2. publication quality approval — exact content approval required before Instagram publish.

For Instagram publish, the default is fail-closed and requires a machine-readable
PREFLIGHT v3 bound to the exact final package. Use --transport-only only for health
or diagnostics; its success is explicitly NOT publish authorization.

Publish Gate v3 invariant:
- every asset entering Velvet Media is RAW source material;
- crop/resize/format-normalization alone is never a publishable creative treatment;
- the exact final derivative must pass creative, brand, commercial-visual and
  scroll-stop QA before transport can be authorized.

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
  2 — actionable failover / publish authorization is incomplete; do not publish
  1 — supplied approval is invalid, unknown gate, or hard block
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
SEND = ROOT / "constitution" / "SEND.md"
PREFLIGHT_ROOT = ROOT / "packages" / "vfgrowth" / "preflight"

READY = {"ready", "skill-installed", "plugin-installed", "hq-native"}
IG_AUTH_READY = {"ready", "ready-codespace", "ready-local"}
FAILOVER = {"needsAuth", "needs-key", "down", "not-on-this-cloud-agent"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
VELVET_VISUAL_STANDARD_ASSET = "MAHVJjCCKQA"
VELVET_VISUAL_STANDARD_SHA256 = "707edde3f4d43cffea090bf90ed2418c160db2f8d90d104e4920b44697a014c0"
VELVET_VISUAL_STANDARD_DOCUMENT = "packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md"
VELVET_VISUAL_STANDARD_FAILURE = "visual_standard_unavailable"
CREATIVE_TREATMENT_CATEGORIES = {
    "composition",
    "cleanup",
    "background",
    "lighting",
    "color_grade",
    "subject_separation",
    "retouch",
    "brand_system",
    "typography",
    "motion",
    "audio",
}
TRIVIAL_ONLY_CATEGORIES = {"crop", "resize", "format", "normalize", "normalization"}


def _env_present(*names: str) -> bool:
    return any((os.environ.get(n) or "").strip() for n in names)


def _tool(desk: dict[str, Any], name: str) -> dict[str, Any]:
    tools = desk.get("tools") or {}
    row = tools.get(name) or {}
    return row if isinstance(row, dict) else {}


def _field(text: str, name: str) -> str | None:
    match = re.search(rf"(?mi)^\s*(?:[-*]\s*)?`?{re.escape(name)}`?\s*:\s*(.*?)\s*$", text)
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


def _csv_tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    return {
        token.strip().lower().replace("-", "_").replace(" ", "_")
        for token in re.split(r"[,;|]", value)
        if token.strip()
    }


def validate_publication_approval(
    approval_ref: str,
    content_id: str,
    format_name: str,
    package_sha256: str,
) -> dict[str, Any]:
    """Validate fail-closed PREFLIGHT v3 for the exact Instagram package."""
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
        problems.append(f"approval/content mismatch: {approval_path.stem!r} != {content_id!r}")

    text = approval_path.read_text(encoding="utf-8")
    schema = (_field(text, "publish_gate_schema") or "").strip()
    gate = (_field(text, "publish_gate") or "").strip().upper()
    invalidated = (_field(text, "approval_invalidated") or "false").strip().lower()
    visual_standard_gate = (_field(text, "visual_standard_gate") or "").strip().upper()
    visual_standard_asset = (_field(text, "visual_standard_canva_asset_id") or "").strip()
    visual_standard_sha = (_field(text, "visual_standard_artifact_sha256") or "").strip().lower()
    visual_standard_document = (_field(text, "visual_standard_document") or "").strip()
    product_truth_source_refs = (_field(text, "product_truth_source_refs") or "").strip()


    if schema != "3":
        problems.append("PREFLIGHT v3 required: publish_gate_schema: 3")
    if gate not in {"PASS", "עבור"}:
        problems.append("publish_gate must be PASS")
    if invalidated in {"1", "true", "yes", "כן"}:
        problems.append("approval is explicitly invalidated")
    if visual_standard_gate != "PASS":
        problems.append(f"{VELVET_VISUAL_STANDARD_FAILURE}: visual_standard_gate must be PASS")
    if visual_standard_asset != VELVET_VISUAL_STANDARD_ASSET:
        problems.append(f"{VELVET_VISUAL_STANDARD_FAILURE}: visual_standard_canva_asset_id does not match canonical owner-approved standard")
    if visual_standard_sha != VELVET_VISUAL_STANDARD_SHA256:
        problems.append(f"{VELVET_VISUAL_STANDARD_FAILURE}: visual_standard_artifact_sha256 does not match canonical owner-approved standard")
    if visual_standard_document != VELVET_VISUAL_STANDARD_DOCUMENT:
        problems.append(f"{VELVET_VISUAL_STANDARD_FAILURE}: visual_standard_document does not match canonical owner-approved standard")
    if not product_truth_source_refs or "<" in product_truth_source_refs or product_truth_source_refs.upper() in {"N/A","NONE","PENDING","_"}:
        problems.append(f"{VELVET_VISUAL_STANDARD_FAILURE}: product_truth_source_refs must identify real source-product evidence")

    rubric = _field(text, "content_rubric_total")
    rubric_match = re.fullmatch(r"\s*(\d{1,2})\s*/\s*25\s*", rubric or "")
    if not rubric_match:
        problems.append("content_rubric_total must be explicit, e.g. 22/25")
    elif int(rubric_match.group(1)) < 20:
        problems.append("CONTENT-RUBRIC total is below 20/25")

    artifact_digest = _clean_sha(_field(text, "artifact_digest"))
    if artifact_digest is None:
        problems.append("artifact_digest must be sha256:<64 hex>")

    # v3 applies the exact-final quality checks to every Instagram format, not only Stories.
    required_pass_fields = {
        "qa_scope": "exact-final-render",
        "visible_text_gate": "PASS",
        "fact_gate": "PASS",
        "brand_guardian": "PASS",
        "copy_qa": "PASS",
        "readability": "PASS",
        "contrast": "PASS",
        "creative_treatment": "PASS",
        "brand_treatment": "PASS",
        "commercial_visual_qa": "PASS",
        "scroll_stop_qa": "PASS",
        "derivative_is_distinct_from_source": "PASS",
    }
    for field, expected in required_pass_fields.items():
        actual = (_field(text, field) or "").strip()
        if actual.upper() != expected.upper():
            problems.append(f"{field} must be {expected}")

    source_material_state = (_field(text, "source_material_state") or "").strip().upper()
    if source_material_state != "RAW":
        problems.append("source_material_state must be RAW: vault uploads never imply edit/approval")

    reviewed_at = (_field(text, "qa_reviewed_at") or "").strip()
    if not reviewed_at or "<" in reviewed_at or reviewed_at == "_":
        problems.append("qa_reviewed_at must identify the exact final-render review")

    approved_package = _clean_sha(_field(text, "final_package_sha256"))
    supplied_package = _clean_sha(package_sha256)
    if approved_package is None:
        problems.append("final_package_sha256 missing/invalid in PREFLIGHT")
    if supplied_package is None:
        problems.append("--package-sha256 must be a 64-hex SHA-256")
    if approved_package and supplied_package and approved_package != supplied_package:
        problems.append("exact final package SHA-256 does not match the approved render")

    edit_evidence = (_field(text, "creative_edit_evidence") or "").strip()
    if not edit_evidence or edit_evidence.upper() in {"N/A", "NONE", "PENDING", "_"} or "<" in edit_evidence:
        problems.append("creative_edit_evidence must identify the actual edited final derivative/review")

    treatment_tokens = _csv_tokens(_field(text, "creative_treatment_categories"))
    recognized = treatment_tokens & CREATIVE_TREATMENT_CATEGORIES
    trivial = treatment_tokens & TRIVIAL_ONLY_CATEGORIES
    if len(recognized) < 3:
        problems.append("creative_treatment_categories must contain at least 3 real treatments")
    if treatment_tokens and treatment_tokens <= TRIVIAL_ONLY_CATEGORIES:
        problems.append("crop/resize/format normalization alone is never creative treatment")
    if trivial and not recognized:
        problems.append("technical transforms cannot substitute for art direction")

    # Prevent the exact failure that triggered v3: declaring a crop-only path as edited creative.
    lowered = text.lower()
    crop_only_markers = (
        "deterministic-crop",
        "crop/order/qa",
        "crop only",
        "resize only",
        "normalization only",
    )
    if any(marker in lowered for marker in crop_only_markers):
        problems.append("preflight documents a crop/resize-only path; create a real creative derivative")

    if "ניגודיות" in text and "לא חוסם" in text:
        problems.append("contrast/readability may not be waived as non-blocking")
    if "soft contrast" in lowered and "non-block" in lowered:
        problems.append("soft contrast may not be waived as non-blocking")

    audio_gate = (_field(text, "audio_gate") or "").strip().upper()
    if format_name == "reel" and audio_gate != "PASS":
        problems.append("reel audio_gate must be PASS")
    if format_name in {"carousel", "post"} and audio_gate not in {"N/A", "NA", "NOT_APPLICABLE"}:
        problems.append(f"{format_name} audio_gate must be N/A")
    if format_name == "story" and audio_gate not in {"PASS", "N/A", "NA", "NOT_APPLICABLE"}:
        problems.append("story audio_gate must be PASS for video or N/A for still image")

    return {
        "ok": not problems,
        "approvalRef": approval_ref,
        "contentId": content_id,
        "format": format_name,
        "publishGateSchema": schema or None,
        "packageSha256": _clean_sha(package_sha256),
        "problems": problems,
        "rule": "vault media is RAW; publish authorization requires an exact-final branded creative derivative, not a transport-ready crop",
    }


def channel_report(desk: dict[str, Any]) -> dict[str, Any]:
    gmail = _tool(desk, "gmail")
    canva = _tool(desk, "canva")
    ig = _tool(desk, "instagram")
    gemini = _tool(desk, "gemini")
    chatgpt = _tool(desk, "chatgpt")

    ig_status = ig.get("status") or ""
    ig_remote = ig.get("remote_access") or ""
    ig_auth_ok = ig_status in IG_AUTH_READY or ig.get("auth") == "ready"
    ig_secrets = _env_present("INSTAGRAM_MCP_ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN")
    ig_session_ready = ig_auth_ok and (ig_remote == "ready" or (ig_secrets and ig_status in IG_AUTH_READY))
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
            "failover": canva.get("failover") or "Canva לא מחובר → packages/vfcanva/studio/render.py → Superdesign",
        },
        "instagram": {
            "desk_status": ig_status or "unknown",
            "auth": ig.get("auth") or ("ready" if ig_auth_ok else "unknown"),
            "transport": ig.get("transport") or "stdio",
            "remote_access": ig_remote or "unknown",
            "ready": ig_session_ready and not ig_needs_failover,
            "needs_failover": ig_needs_failover,
            "action": "publish_image|carousel|reel|story then list_media/get_media verify",
            "failover": "Canva + Drive create_file + Gmail same turn · #ממתין-ל-כלי-IG",
            "forbid": ["send_message DM", "auto-DM", "boost without lead", "INSTAGRAM_MCP_DM_ENABLED"],
        },
        "gemini": {
            "desk_status": gemini.get("status") or "unknown",
            "key_present": gemini_key,
            "ready": gemini_key,
            "action": "python3 scripts/vf_gemini.py",
            "failover": "חסר מפתח Gemini → ChatGPT API + Perplexity + WebSearch",
        },
        "chatgpt": {
            "desk_status": chatgpt.get("status") or "unknown",
            "key_present": chatgpt_key,
            "ready": chatgpt_key,
            "action": "python3 scripts/vf_chatgpt.py",
            "failover": "חסר מפתח ChatGPT → Gemini API + Perplexity + WebSearch",
        },
    }
    return {
        "ok": True,
        "mode": "local-only",
        "send_law": str(SEND.relative_to(ROOT)) if SEND.is_file() else None,
        "channels": channels,
        "rule": "Transport readiness is not creative approval. Instagram publish requires exact-package PREFLIGHT v3.",
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
    parser.add_argument("--gate", choices=("gmail", "instagram", "canva", "gemini", "chatgpt"))
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
    quality_missing = False

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
                    "rule": "fail closed: legacy transport-only invocation is not publish authorization",
                }
                quality_missing = True
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
    if quality_missing:
        print("GATE instagram=failover (publish quality approval missing)", file=sys.stderr)
        return 2
    if args.gate:
        return gate_channel(report, args.gate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
