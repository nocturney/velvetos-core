#!/usr/bin/env python3
"""Surface-aware human-visible AI text gate for VelvetOS.

This is not a second writer. It validates the exact candidate through the existing
vfcopy Hebrew lint and records whether the *other* required stages were actually
reported as executed. A clean lint alone is never enough for PASS.

Examples:
  python3 scripts/vf_visible_text.py --surface owner-brief --text '...' \
    --gate --truth-checked --reader-first --copy-authority --surface-qa \
    --domain-tool vfops

  python3 scripts/vf_visible_text.py --surface customer-message --file reply.txt \
    --context-json '{"price":120,"price_verified":true}' \
    --gate --truth-checked --reader-first --copy-authority --surface-qa \
    --domain-tool vfconvert --domain-tool vfsales --domain-tool vfcost

Exit: 0 only when lint passes; with --gate, exit 0 only for visible_text_gate=PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "vfcopy"))
from lint_he import detect_ai_slop, lint_hebrew_copy  # noqa: E402

SURFACES = (
    "public-social",
    "visual-microcopy",
    "customer-message",
    "sales-proposal",
    "owner-brief",
    "human-document",
    "ui-microcopy",
    "desk",
)
PUBLIC_SURFACES = {"public-social", "visual-microcopy"}
LONGFORM_SURFACES = {"owner-brief", "human-document", "sales-proposal"}
MARKETING_SURFACES = {"public-social", "visual-microcopy", "sales-proposal"}

TIERS = (
    "DRAFT_INTERNAL",
    "FINAL_INTERNAL",
    "EXTERNAL_COMMITMENT",
    "PUBLIC_PUBLISH",
)
INTERNAL_SURFACES = {"owner-brief", "human-document", "ui-microcopy", "desk"}
EXTERNAL_COMMITMENT_SURFACES = {"customer-message", "sales-proposal", "human-document"}
DEFAULT_TIER_BY_SURFACE = {
    "public-social": "PUBLIC_PUBLISH",
    "visual-microcopy": "PUBLIC_PUBLISH",
    "customer-message": "EXTERNAL_COMMITMENT",
    "sales-proposal": "EXTERNAL_COMMITMENT",
    "owner-brief": "FINAL_INTERNAL",
    "human-document": "FINAL_INTERNAL",
    "ui-microcopy": "FINAL_INTERNAL",
    "desk": "FINAL_INTERNAL",
}
HEAVY_INTERNAL_LENGTH = 800

PUBLIC_ONLY_MARKERS = (
    "CTA וואטסאפ/טלפון אסור בתוכן ציבורי",
)
PUBLIC_LENGTH_MARKERS = (
    "יותר מ־5 האשטגים",
)
LONGFORM_MARKERS = (
    "כיתוב ארוך מדי",
)


def _read_text(args: argparse.Namespace) -> str:
    if bool(args.text) == bool(args.file):
        raise ValueError("provide exactly one of --text or --file")
    if args.text is not None:
        return args.text
    path = Path(args.file)
    if not path.is_file():
        raise ValueError(f"missing text file: {path}")
    return path.read_text(encoding="utf-8")


def _load_context(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("--context-json must be a JSON object")
    return value


def _surface_filter(surface: str, problems: list[str]) -> list[str]:
    """Remove only rules that are explicitly public-caption-specific.

    Business truth (price, turnaround, shipping, invented customer, etc.) remains
    active on every human-visible surface. We do not weaken those checks here.
    """
    out: list[str] = []
    for problem in problems:
        if surface not in PUBLIC_SURFACES and any(m in problem for m in PUBLIC_ONLY_MARKERS):
            continue
        if surface not in PUBLIC_SURFACES and any(m in problem for m in PUBLIC_LENGTH_MARKERS):
            continue
        if surface in LONGFORM_SURFACES and any(m in problem for m in LONGFORM_MARKERS):
            continue
        out.append(problem)
    return out


def _classify(filtered: list[str], original_status: str) -> str:
    if not filtered:
        return "pass"
    if any("needs_input" in p or "חסר" in p for p in filtered):
        return "needs_input"
    fact_markers = (
        "מחיר",
        "₪",
        "זמן",
        "turnaround",
        "לקוח/testimonial",
        "משך הדפסה",
        "משלוח ארצי",
        "לא תואם context",
    )
    if any(any(m in p for m in fact_markers) for p in filtered):
        return "fail_fact"
    if original_status == "fail_fact":
        return "fail_fact"
    return "fail_style"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _resolve_tier(args: argparse.Namespace) -> str:
    tier = (getattr(args, "tier", None) or DEFAULT_TIER_BY_SURFACE[args.surface]).strip()
    if tier not in TIERS:
        raise ValueError(f"unsupported visible-text tier: {tier}")
    if tier in {"DRAFT_INTERNAL", "FINAL_INTERNAL"} and args.surface not in INTERNAL_SURFACES:
        raise ValueError(f"{tier} cannot be used for external/public surface {args.surface}")
    if tier == "EXTERNAL_COMMITMENT" and args.surface not in EXTERNAL_COMMITMENT_SURFACES:
        raise ValueError(f"EXTERNAL_COMMITMENT cannot be used for surface {args.surface}")
    if tier == "PUBLIC_PUBLISH" and args.surface not in PUBLIC_SURFACES:
        raise ValueError(f"PUBLIC_PUBLISH requires a public surface, got {args.surface}")
    return tier


def _approved_static_match(text: str, args: argparse.Namespace) -> tuple[bool, bool, str | None]:
    expected = (getattr(args, "approved_static_sha256", None) or "").strip().lower()
    if not expected:
        return False, False, None
    if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
        raise ValueError("--approved-static-sha256 must be 64 lowercase/uppercase hex characters")
    observed = _sha256(text)
    return True, observed == expected, expected


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    text = _read_text(args)
    tier = _resolve_tier(args)
    context = _load_context(getattr(args, "context_json", None))
    context["visible_text_surface"] = args.surface
    context["visible_text_tier"] = tier

    static_requested, static_match, static_expected = _approved_static_match(text, args)
    sensitive = bool(getattr(args, "sensitive", False))
    heavy_internal = tier == "FINAL_INTERNAL" and (
        sensitive or len(text) > HEAVY_INTERNAL_LENGTH
    )
    exact_body_bound = bool(getattr(args, "exact_body_bound", False))

    slop_findings = detect_ai_slop(text)
    verdict = lint_hebrew_copy(
        text,
        label=f"visible-text:{args.surface}",
        context=context,
        offer_rewrite=bool(getattr(args, "rewrite", False)),
    )
    problems = _surface_filter(args.surface, verdict.problems)
    lint_status = _classify(problems, verdict.status)
    lint_pass = lint_status == "pass"
    fact_safe = lint_status not in {"fail_fact", "needs_input"}

    domain_tools = [
        x.strip() for x in (getattr(args, "domain_tool", None) or []) if x.strip()
    ]
    marketing_disposition = (getattr(args, "marketing_aids", None) or "").strip()

    stages = {
        "truth_checked": bool(getattr(args, "truth_checked", False)),
        "reader_first": bool(getattr(args, "reader_first", False)),
        "copy_authority": bool(getattr(args, "copy_authority", False)),
        "humanizer_ai_tells": lint_pass and not slop_findings,
        "domain_tools_recorded": bool(domain_tools),
        "surface_qa": bool(getattr(args, "surface_qa", False)),
        "exact_body_bound": exact_body_bound,
    }

    if static_match:
        required = ["truth_checked"]
        if tier == "EXTERNAL_COMMITMENT":
            required.append("exact_body_bound")
    elif tier == "DRAFT_INTERNAL":
        required = ["truth_checked"]
    elif tier == "FINAL_INTERNAL":
        required = ["truth_checked", "surface_qa"]
        if heavy_internal:
            required.extend(["reader_first", "copy_authority", "humanizer_ai_tells"])
    elif tier == "EXTERNAL_COMMITMENT":
        required = ["truth_checked", "reader_first", "surface_qa", "exact_body_bound"]
    else:
        required = [
            "truth_checked",
            "reader_first",
            "copy_authority",
            "humanizer_ai_tells",
            "domain_tools_recorded",
            "surface_qa",
        ]

    missing: list[str] = [name for name in required if not stages[name]]
    if tier == "PUBLIC_PUBLISH" and args.surface == "visual-microcopy" and not bool(
        getattr(args, "no_text_compared", False)
    ):
        missing.append("no_text_compared")
    if tier == "PUBLIC_PUBLISH" and args.surface in MARKETING_SURFACES and not marketing_disposition:
        missing.append("marketing_aids_disposition")

    if static_requested and not static_match:
        gate = "FAIL"
        failure_reason = "approved_static_hash_mismatch"
    else:
        failure_reason = None
        lint_blocked = not (fact_safe if tier == "DRAFT_INTERNAL" or static_match else lint_pass)
        if lint_blocked:
            gate = "FAIL"
            failure_reason = "lint_or_fact_gate"
        elif bool(getattr(args, "gate", False)) and not missing:
            gate = "PASS"
        else:
            gate = "UNPROVEN"

    payload: dict[str, Any] = {
        "schema": 1,
        "tier_contract_version": 1,
        "tier": tier,
        "surface": args.surface,
        "language": getattr(args, "language", "he"),
        "text_sha256": _sha256(text),
        "lint": {
            "status": lint_status,
            "problems": problems,
            "raw_status": verdict.status,
            "blocking_for_tier": not (
                fact_safe if tier == "DRAFT_INTERNAL" or static_match else lint_pass
            ),
        },
        "anti_slop": {
            "checked": True,
            "findings": slop_findings,
            "blocking_for_tier": tier != "DRAFT_INTERNAL" and not static_match,
            "authorship": "NOT_INFERRED — named writing patterns only",
        },
        "stages": stages,
        "required_evidence": required,
        "heavy_tools_required": heavy_internal or tier == "PUBLIC_PUBLISH",
        "domain_tools": domain_tools,
        "marketing_aids": marketing_disposition or None,
        "no_text_compared": (
            bool(getattr(args, "no_text_compared", False))
            if args.surface == "visual-microcopy"
            else None
        ),
        "approved_static_copy": {
            "requested": static_requested,
            "expected_sha256": static_expected,
            "exact_match": static_match,
            "reuse_allowed": static_match and stages["truth_checked"],
        },
        "missing_evidence": missing,
        "failure_reason": failure_reason,
        "visible_text_gate": gate,
        "rule": (
            "Tiered Visible Text Gate: internal drafts pay truth/basic-safety only; "
            "internal finals add clarity/facts with heavy ceremony only for sensitivity/length; "
            "external commitments require facts + reader/surface QA + exact-body binding; "
            "public publish keeps the full public-copy chain. Exact approved static copy may "
            "reuse prior copy work only while its hash is unchanged and facts are rechecked."
        ),
    }
    if bool(getattr(args, "rewrite", False)) and verdict.rewrite:
        payload["rewrite_candidate"] = verdict.rewrite
        payload["rewrite_invalidates_current_hash"] = True
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", required=True, choices=SURFACES)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--file")
    parser.add_argument("--language", choices=("he", "mixed"), default="he")
    parser.add_argument("--tier", choices=TIERS, help="Risk/surface tier. Defaults safely from --surface.")
    parser.add_argument("--context-json")
    parser.add_argument("--domain-tool", action="append", default=[])
    parser.add_argument(
        "--marketing-aids",
        help="Explicit disposition, e.g. 'copywriting=APPLIED,copy-editing=APPLIED,marketing-psychology=N/A:non-promotional'.",
    )
    parser.add_argument("--truth-checked", action="store_true")
    parser.add_argument("--reader-first", action="store_true")
    parser.add_argument("--copy-authority", action="store_true")
    parser.add_argument("--surface-qa", action="store_true")
    parser.add_argument("--sensitive", action="store_true", help="Require heavier internal copy ceremony for sensitive content.")
    parser.add_argument("--exact-body-bound", action="store_true", help="Assert the exact body/hash is bound to the external commitment action.")
    parser.add_argument("--approved-static-sha256", help="Reuse approved static copy only when the exact current text SHA-256 matches.")
    parser.add_argument("--no-text-compared", action="store_true")
    parser.add_argument("--rewrite", action="store_true")
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Fail closed unless all required stage evidence is present and the exact text lint passes.",
    )
    args = parser.parse_args()

    try:
        payload = evaluate(args)
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"visible_text_gate": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.gate:
        return 0 if payload["visible_text_gate"] == "PASS" else 1
    return 0 if payload["lint"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
