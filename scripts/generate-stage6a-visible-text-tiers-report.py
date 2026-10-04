#!/usr/bin/env python3
"""Generate Reform v2 Stage 6A Visible Text tier acceptance evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage6a-visible-text-tiers.json"
VISIBLE = ROOT / "scripts" / "vf_visible_text.py"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
STAGE5 = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage5-acceptance.json"

BASE_REQUIRED = [
    "truth_checked",
    "reader_first",
    "copy_authority",
    "humanizer_ai_tells",
    "domain_tools_recorded",
    "surface_qa",
]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_bytes(ref: str, rel: str) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise SystemExit(f"cannot read {rel} at {ref}: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def load_visible_module():
    spec = importlib.util.spec_from_file_location("vf_visible_text_stage6a", VISIBLE)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load vf_visible_text.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def args_for(**overrides: Any) -> Namespace:
    data = dict(
        text="שלושה קבצים נבדקו. שני כשלים עדיין פתוחים ודורשים תיקון.",
        file=None,
        surface="owner-brief",
        tier=None,
        language="he",
        context_json=None,
        domain_tool=[],
        marketing_aids=None,
        truth_checked=True,
        reader_first=False,
        copy_authority=False,
        surface_qa=True,
        sensitive=False,
        exact_body_bound=False,
        approved_static_sha256=None,
        no_text_compared=False,
        rewrite=False,
        gate=True,
    )
    data.update(overrides)
    return Namespace(**data)


def summarize(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "tier": payload.get("tier"),
        "surface": payload.get("surface"),
        "visible_text_gate": payload.get("visible_text_gate"),
        "required_evidence": payload.get("required_evidence"),
        "missing_evidence": payload.get("missing_evidence"),
        "heavy_tools_required": payload.get("heavy_tools_required"),
        "failure_reason": payload.get("failure_reason"),
        "lint_status": (payload.get("lint") or {}).get("status"),
        "anti_slop_findings": len((payload.get("anti_slop") or {}).get("findings") or []),
        "approved_static_reuse": (payload.get("approved_static_copy") or {}).get("reuse_allowed"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    ns = ap.parse_args()
    if len(ns.prepared_against) != 40:
        ap.error("--prepared-against must be a full Git SHA")

    before_code = git_bytes(ns.prepared_against, "scripts/vf_visible_text.py")
    before_text = before_code.decode("utf-8")
    for marker in (
        '"truth_checked": bool(args.truth_checked)',
        '"reader_first": bool(args.reader_first)',
        '"copy_authority": bool(args.copy_authority)',
        '"humanizer_ai_tells": lint_pass and not slop_findings',
        '"domain_tools_recorded": bool(domain_tools)',
        '"surface_qa": bool(args.surface_qa)',
        'missing: list[str] = [name for name, ok in stages.items() if not ok]',
    ):
        if marker not in before_text:
            raise SystemExit(f"pre-6A universal-chain marker missing at {ns.prepared_against}: {marker}")

    before_policy = git_bytes(ns.prepared_against, "packages/velvetos/policy/policy-registry.json")
    current_policy = POLICY.read_bytes()
    stage5 = json.loads(STAGE5.read_text(encoding="utf-8"))
    if stage5.get("stage5_gate") != "PASS" or not (stage5.get("stage6_entry") or {}).get("allowed"):
        raise SystemExit("Stage 5 gate does not allow Stage 6")

    mod = load_visible_module()
    rows: dict[str, Any] = {}

    draft_slop = mod.evaluate(args_for(
        text="הנה העניין: הכול השתנה. העתיד כבר כאן.",
        surface="desk", tier="DRAFT_INTERNAL", surface_qa=False,
    ))
    rows["draft_internal_slop_diagnostic"] = summarize(draft_slop)

    draft_fact = mod.evaluate(args_for(
        text="המחיר הוא 120 ₪.",
        surface="desk", tier="DRAFT_INTERNAL", surface_qa=False,
    ))
    rows["draft_internal_unverified_price"] = summarize(draft_fact)

    final_routine = mod.evaluate(args_for(tier="FINAL_INTERNAL"))
    rows["final_internal_routine"] = summarize(final_routine)

    final_sensitive = mod.evaluate(args_for(tier="FINAL_INTERNAL", sensitive=True))
    rows["final_internal_sensitive"] = summarize(final_sensitive)

    external_unbound = mod.evaluate(args_for(
        text="תודה, קיבלתי את הפרטים.",
        surface="customer-message",
        tier="EXTERNAL_COMMITMENT",
        reader_first=True,
        surface_qa=True,
        exact_body_bound=False,
    ))
    rows["external_commitment_unbound"] = summarize(external_unbound)

    external_bound = mod.evaluate(args_for(
        text="תודה, קיבלתי את הפרטים.",
        surface="customer-message",
        tier="EXTERNAL_COMMITMENT",
        reader_first=True,
        surface_qa=True,
        exact_body_bound=True,
    ))
    rows["external_commitment_bound"] = summarize(external_bound)

    public_full = mod.evaluate(args_for(
        text="פרט אמיתי מהמוצר.",
        surface="public-social",
        tier="PUBLIC_PUBLISH",
        domain_tool=["vfgrowth"],
        marketing_aids="copywriting=N/A:short,copy-editing=APPLIED,marketing-psychology=N/A:non-promotional",
        reader_first=True,
        copy_authority=True,
        surface_qa=True,
    ))
    rows["public_publish_full"] = summarize(public_full)

    public_downgrade_blocked = False
    try:
        mod.evaluate(args_for(
            text="פוסט",
            surface="public-social",
            tier="DRAFT_INTERNAL",
            surface_qa=False,
        ))
    except ValueError:
        public_downgrade_blocked = True

    static_text = "שלושה קבצים נבדקו. שני כשלים עדיין פתוחים ודורשים תיקון."
    static_sha = hashlib.sha256(static_text.encode("utf-8")).hexdigest()
    static_exact = mod.evaluate(args_for(
        text=static_text,
        tier="FINAL_INTERNAL",
        surface_qa=False,
        approved_static_sha256=static_sha,
    ))
    rows["approved_static_exact"] = summarize(static_exact)
    static_changed = mod.evaluate(args_for(
        text="שלושה קבצים נבדקו. כשל אחד עדיין פתוח.",
        tier="FINAL_INTERNAL",
        surface_qa=False,
        approved_static_sha256=static_sha,
    ))
    rows["approved_static_changed"] = summarize(static_changed)

    expected = {
        "draft_internal_slop_diagnostic": ("PASS", ["truth_checked"]),
        "draft_internal_unverified_price": ("FAIL", ["truth_checked"]),
        "final_internal_routine": ("PASS", ["truth_checked", "surface_qa"]),
        "final_internal_sensitive": ("UNPROVEN", ["truth_checked", "surface_qa", "reader_first", "copy_authority", "humanizer_ai_tells"]),
        "external_commitment_unbound": ("UNPROVEN", ["truth_checked", "reader_first", "surface_qa", "exact_body_bound"]),
        "external_commitment_bound": ("PASS", ["truth_checked", "reader_first", "surface_qa", "exact_body_bound"]),
        "public_publish_full": ("PASS", BASE_REQUIRED),
        "approved_static_exact": ("PASS", ["truth_checked"]),
        "approved_static_changed": ("FAIL", ["truth_checked", "surface_qa"]),
    }
    vector_pass = True
    for name, (gate, required) in expected.items():
        row = rows[name]
        ok = row["visible_text_gate"] == gate and row["required_evidence"] == required
        if name == "draft_internal_slop_diagnostic":
            ok = ok and row["anti_slop_findings"] > 0
        if name == "draft_internal_unverified_price":
            ok = ok and row["lint_status"] in {"fail_fact", "needs_input"}
        if name == "final_internal_routine":
            ok = ok and row["heavy_tools_required"] is False
        if name == "final_internal_sensitive":
            ok = ok and row["heavy_tools_required"] is True
        if name == "external_commitment_unbound":
            ok = ok and "exact_body_bound" in row["missing_evidence"]
        if name == "approved_static_exact":
            ok = ok and row["approved_static_reuse"] is True
        if name == "approved_static_changed":
            ok = ok and row["failure_reason"] == "approved_static_hash_mismatch"
        row["pass"] = ok
        vector_pass = vector_pass and ok

    policy_unchanged = sha_bytes(before_policy) == sha_bytes(current_policy)
    workflow_files = [
        ".github/workflows/gmail-brief-send.yml",
        ".github/workflows/gmail-tool-updates-send.yml",
    ]
    workflow_explicit = all(
        "--surface owner-brief" in (ROOT / rel).read_text(encoding="utf-8")
        and "--tier FINAL_INTERNAL" in (ROOT / rel).read_text(encoding="utf-8")
        for rel in workflow_files
    )

    before_count = len(BASE_REQUIRED)
    tier_counts = {
        "DRAFT_INTERNAL": 1,
        "FINAL_INTERNAL_routine": 2,
        "FINAL_INTERNAL_sensitive": 5,
        "EXTERNAL_COMMITMENT": 4,
        "PUBLIC_PUBLISH": 6,
    }
    reduction = {
        key: round((before_count - count) / before_count * 100.0, 1)
        for key, count in tier_counts.items()
    }

    acceptance = {
        "draft_internal_truth_only_with_fact_guard_preserved": (
            rows["draft_internal_slop_diagnostic"]["pass"]
            and rows["draft_internal_unverified_price"]["pass"]
        ),
        "routine_final_internal_skips_heavy_copy_ceremony": rows["final_internal_routine"]["pass"],
        "sensitive_final_internal_restores_heavy_copy_evidence": rows["final_internal_sensitive"]["pass"],
        "external_commitment_requires_exact_body_binding": (
            rows["external_commitment_unbound"]["pass"]
            and rows["external_commitment_bound"]["pass"]
        ),
        "public_publish_retains_full_chain": rows["public_publish_full"]["pass"],
        "public_to_internal_downgrade_blocked": public_downgrade_blocked,
        "approved_static_copy_reuse_is_exact_hash_only": (
            rows["approved_static_exact"]["pass"]
            and rows["approved_static_changed"]["pass"]
        ),
        "gmail_owner_brief_workflows_explicit_final_internal": workflow_explicit,
        "external_effect_policy_registry_unchanged": policy_unchanged,
        "all_behavior_vectors_pass": vector_pass,
    }

    report = {
        "schema": "velvetos.stage6a-visible-text-tiers.v1",
        "stage": "6A",
        "behavior_change": True,
        "prepared_against_main_sha": ns.prepared_against,
        "captured_at": ns.captured_at,
        "stage5_entry": {
            "receipt": "packages/velvetos/policy/reports/stage5-acceptance.json",
            "gate": stage5.get("stage5_gate"),
            "stage6_allowed": (stage5.get("stage6_entry") or {}).get("allowed"),
        },
        "before": {
            "source_sha256": sha_bytes(before_code),
            "model": "UNIVERSAL_FULL_CHAIN",
            "universal_required_evidence": BASE_REQUIRED,
            "universal_required_count": before_count,
            "public_extras_preserved": ["marketing_aids_disposition", "no_text_compared"],
        },
        "after": {
            "source_sha256": sha_bytes(VISIBLE.read_bytes()),
            "model": "RISK_AND_SURFACE_TIERS",
            "tier_contract_version": 1,
            "safe_default_by_surface": mod.DEFAULT_TIER_BY_SURFACE,
            "tier_required_evidence_counts": tier_counts,
            "ceremony_reduction_percent_vs_before": reduction,
            "heavy_internal_length_threshold_chars": mod.HEAVY_INTERNAL_LENGTH,
            "approved_static_requires_exact_sha": True,
            "tier_downgrade_fail_closed": True,
        },
        "behavior_vectors": rows,
        "public_downgrade_blocked": public_downgrade_blocked,
        "workflow_binding": {
            "owner_brief_workflows": workflow_files,
            "explicit_tier": "FINAL_INTERNAL",
            "pass": workflow_explicit,
        },
        "authorization_semantics": {
            "entry_policy_registry_sha256": sha_bytes(before_policy),
            "current_policy_registry_sha256": sha_bytes(current_policy),
            "external_effect_policy_registry_unchanged": policy_unchanged,
            "visible_text_is_effect_authority": False,
        },
        "acceptance": acceptance,
        "repository_acceptance": "PASS" if all(acceptance.values()) else "FAIL",
    }

    out = ns.output if ns.output.is_absolute() else ROOT / ns.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE6A_VISIBLE_TEXT "
        f"acceptance={report['repository_acceptance']} "
        f"vectors={sum(1 for r in rows.values() if r['pass'])}/{len(rows)} "
        f"draft_reduction={reduction['DRAFT_INTERNAL']}% "
        f"routine_final_reduction={reduction['FINAL_INTERNAL_routine']}% "
        f"public_reduction={reduction['PUBLIC_PUBLISH']}% "
        f"policy_unchanged={policy_unchanged}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
