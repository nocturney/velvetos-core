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
from lint_he import lint_hebrew_copy  # noqa: E402

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


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    text = _read_text(args)
    context = _load_context(args.context_json)
    context["visible_text_surface"] = args.surface

    verdict = lint_hebrew_copy(
        text,
        label=f"visible-text:{args.surface}",
        context=context,
        offer_rewrite=args.rewrite,
    )
    problems = _surface_filter(args.surface, verdict.problems)
    lint_status = _classify(problems, verdict.status)
    lint_pass = lint_status == "pass"

    domain_tools = [x.strip() for x in (args.domain_tool or []) if x.strip()]
    marketing_disposition = (args.marketing_aids or "").strip()

    stages = {
        "truth_checked": bool(args.truth_checked),
        "reader_first": bool(args.reader_first),
        "copy_authority": bool(args.copy_authority),
        "humanizer_ai_tells": lint_pass,
        "domain_tools_recorded": bool(domain_tools),
        "surface_qa": bool(args.surface_qa),
    }

    missing: list[str] = [name for name, ok in stages.items() if not ok]
    if args.surface == "visual-microcopy" and not args.no_text_compared:
        missing.append("no_text_compared")
    if args.surface in MARKETING_SURFACES and not marketing_disposition:
        missing.append("marketing_aids_disposition")

    if not lint_pass:
        gate = "FAIL"
    elif args.gate and not missing:
        gate = "PASS"
    else:
        gate = "UNPROVEN"

    payload: dict[str, Any] = {
        "schema": 1,
        "surface": args.surface,
        "language": args.language,
        "text_sha256": _sha256(text),
        "lint": {
            "status": lint_status,
            "problems": problems,
            "raw_status": verdict.status,
        },
        "stages": stages,
        "domain_tools": domain_tools,
        "marketing_aids": marketing_disposition or None,
        "no_text_compared": bool(args.no_text_compared) if args.surface == "visual-microcopy" else None,
        "missing_evidence": missing,
        "visible_text_gate": gate,
        "rule": "PASS requires the relevant chain on this exact text; lint/eval existence alone is not execution proof.",
    }
    if args.rewrite and verdict.rewrite:
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
