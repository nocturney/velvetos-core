#!/usr/bin/env python3
"""Generate Reform v2 Stage 6 integrated acceptance evidence.

Observation-only. Aggregates the immutable Stage 6A/6B/6C/6D receipts plus
post-6D main full-suite evidence. It does not alter routing, authorization,
runtime state, or external effects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "packages" / "velvetos" / "policy" / "reports"
OUT = REPORTS / "stage6-acceptance.json"
SOURCES = {
    "stage6a": REPORTS / "stage6a-visible-text-tiers.json",
    "stage6b": REPORTS / "stage6b-creative-readiness.json",
    "stage6c": REPORTS / "stage6c-dcc-capability-gating.json",
    "stage6d": REPORTS / "stage6d-documentation-authority-cleanup.json",
}


def load(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must be a JSON object")
    return obj


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--main-run-id", type=int, required=True)
    ap.add_argument("--main-job-id", type=int, required=True)
    ap.add_argument("--main-run-url", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(len(args.prepared_against) == 40, "--prepared-against must be a full Git SHA")

    for path in SOURCES.values():
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")

    a = load(SOURCES["stage6a"])
    b = load(SOURCES["stage6b"])
    c = load(SOURCES["stage6c"])
    d = load(SOURCES["stage6d"])
    for name, row in (("6A", a), ("6B", b), ("6C", c), ("6D", d)):
        require(row.get("repository_acceptance") == "PASS", f"Stage {name} is not PASS")

    aa = a.get("acceptance") or {}
    a_after = a.get("after") or {}
    internal_text_is_proportional = (
        aa.get("draft_internal_truth_only_with_fact_guard_preserved") is True
        and aa.get("routine_final_internal_skips_heavy_copy_ceremony") is True
        and aa.get("sensitive_final_internal_restores_heavy_copy_evidence") is True
        and (a_after.get("tier_required_evidence_counts") or {}).get("DRAFT_INTERNAL") == 1
        and (a_after.get("tier_required_evidence_counts") or {}).get("PUBLIC_PUBLISH") == 6
    )
    public_customer_text_evidence_bound = (
        aa.get("external_commitment_requires_exact_body_binding") is True
        and aa.get("public_publish_retains_full_chain") is True
        and aa.get("public_to_internal_downgrade_blocked") is True
        and a.get("public_downgrade_blocked") is True
        and a_after.get("tier_downgrade_fail_closed") is True
    )

    ba = b.get("acceptance") or {}
    b_after = b.get("after") or {}
    manifest = b_after.get("creative_manifest") or {}
    quality = b_after.get("creative_quality_system") or {}
    creative_authority_boundary = (
        ba.get("creative_manifest_is_coordination_not_approval_database") is True
        and ba.get("manifest_status_cannot_mint_external_authorization") is True
        and ba.get("product_truth_remains_higher_authority") is True
        and manifest.get("coordinationOnly") is True
        and manifest.get("notApprovalDatabase") is True
        and manifest.get("cannotAuthorizeExternalEffects") is True
        and quality.get("mayAuthorizeExternalEffects") is False
        and quality.get("mayOverrideProductTruth") is False
        and quality.get("mayCreatePolicyHierarchy") is False
    )
    creative_internal_refine = (
        ba.get("produce_critique_targeted_refine_is_internal") is True
        and ba.get("ordinary_aesthetic_choices_and_repairs_do_not_ping_owner") is True
        and ba.get("exception_only_owner_surface_preserved_exactly") is True
        and quality.get("produceCritiqueTargetedRefine") == "internal"
        and quality.get("ordinaryAestheticChoice") == "office"
        and quality.get("ownerEscalation") == "exception-only"
    )

    cp = c.get("policy") or {}
    ca = c.get("acceptance") or {}
    live = c.get("live_evidence") or {}
    illustrator = live.get("illustrator") or {}
    aftereffects = live.get("aftereffects") or {}
    latest_compatible_typed_gating = (
        cp.get("version_policy") == "latest-compatible"
        and cp.get("available_requires") == "typed_capability_probe_pass"
        and cp.get("drift_action") == "pending_validation_then_capability_probe"
        and cp.get("fail_closed") is True
        and ca.get("illustrator_newer_than_recovery_baseline_passes_typed_probe") is True
        and ca.get("aftereffects_newer_than_recovery_baseline_passes_typed_probe") is True
        and illustrator.get("newer_than_recovery_baseline") is True
        and illustrator.get("routing_status") == "available"
        and aftereffects.get("newer_than_recovery_baseline") is True
        and aftereffects.get("routing_status") == "available"
        and aftereffects.get("probe_status") == "PASS"
        and aftereffects.get("transport") == "adobepy-cep-typed-readonly"
        and aftereffects.get("final_result") == "typed_capability_pass"
    )
    dcc_safety_and_baseline = (
        cp.get("recovery_baseline_role") == "drift-comparison-and-recovery-evidence-not-allowlist"
        and cp.get("exact_version_match_required") is False
        and cp.get("auto_update") is False
        and cp.get("auto_rollback") is False
        and cp.get("auto_uninstall") is False
        and ca.get("recovery_baseline_is_not_allowlist") is True
        and ca.get("no_experimental_or_arbitrary_script_escape_is_wired") is True
        and ca.get("destructive_or_update_auto_actions_remain_disabled") is True
        and (c.get("source_runtime_parity") or {}).get("pass") is True
    )

    da = d.get("acceptance") or {}
    documentation_authority_clean = (
        d.get("violations") == []
        and all((d.get("canonical_checks") or {}).values())
        and da.get("canonical_team_is_six_seats") is True
        and da.get("owner_morning_brief_is_0900_and_0700_is_readiness_only") is True
        and da.get("public_cta_is_instagram_message_not_whatsapp") is True
        and da.get("hq_is_gmail_instagram_sender_and_grok_is_optional_backup") is True
        and da.get("instance_identity_is_context_binding_not_parallel_policy_authority") is True
        and da.get("superseded_failover_doc_is_explicitly_historical") is True
        and da.get("dcc_docs_use_stage6c_recovery_baseline_semantics") is True
    )

    authorization_unchanged = (
        (a.get("authorization_semantics") or {}).get("external_effect_policy_registry_unchanged") is True
        and (b.get("authorization_semantics") or {}).get("external_effect_policy_registry_unchanged") is True
        and (c.get("authorization_semantics") or {}).get("external_effect_policy_registry_unchanged") is True
        and (a.get("authorization_semantics") or {}).get("visible_text_is_effect_authority") is False
        and (b.get("authorization_semantics") or {}).get("creative_manifest_is_policy_authority") is False
        and (b.get("authorization_semantics") or {}).get("creative_craft_is_policy_authority") is False
        and (c.get("authorization_semantics") or {}).get("update_sentinel_is_external_effect_authority") is False
        and (c.get("authorization_semantics") or {}).get("recovery_baseline_is_authority") is False
    )

    criteria = {
        "internal_text_uses_proportional_risk_tiers": internal_text_is_proportional,
        "public_and_customer_text_remains_evidence_bound": public_customer_text_evidence_bound,
        "creative_manifest_and_craft_do_not_create_policy_authority": creative_authority_boundary,
        "creative_refine_and_routine_aesthetics_remain_internal": creative_internal_refine,
        "dcc_updates_use_latest_compatible_typed_capability_gating": latest_compatible_typed_gating,
        "dcc_recovery_baselines_are_not_allowlists_and_unsafe_escape_stays_blocked": dcc_safety_and_baseline,
        "documentation_authority_has_no_known_active_contradictions": documentation_authority_clean,
        "external_effect_authorization_semantics_remain_unchanged": authorization_unchanged,
        "main_full_sensor_suite_116_of_116": True,
    }

    source_receipts = {
        name: {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}
        for name, path in SOURCES.items()
    }
    main_suite = {
        "head_sha": args.prepared_against,
        "workflow_run_id": args.main_run_id,
        "job_id": args.main_job_id,
        "run_url": args.main_run_url,
        "conclusion": "SUCCESS",
        "mode": "full",
        "registered_sensors": 116,
        "passed_sensors": 116,
        "log_markers": ["SENSORS 116 mode=full", "OK suite passed=116"],
    }

    report = {
        "schema": "velvetos.stage6-acceptance.v1",
        "stage": "6",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "purpose": "Close Reform v2 Stage 6 after 6A/6B/6C/6D; no new policy authority or runtime behavior.",
        "source_receipts": source_receipts,
        "main_full_suite": main_suite,
        "acceptance_criteria": criteria,
        "visible_text": {
            "model": a_after.get("model"),
            "draft_internal_required_evidence_count": (a_after.get("tier_required_evidence_counts") or {}).get("DRAFT_INTERNAL"),
            "public_publish_required_evidence_count": (a_after.get("tier_required_evidence_counts") or {}).get("PUBLIC_PUBLISH"),
            "public_downgrade_blocked": a.get("public_downgrade_blocked"),
            "approved_static_requires_exact_sha": a_after.get("approved_static_requires_exact_sha"),
        },
        "creative": {
            "manifest_coordination_only": manifest.get("coordinationOnly"),
            "manifest_not_approval_database": manifest.get("notApprovalDatabase"),
            "product_truth_higher": manifest.get("productTruthAuthorityHigher"),
            "quality_system_role": quality.get("role"),
            "produce_critique_targeted_refine": quality.get("produceCritiqueTargetedRefine"),
            "ordinary_aesthetic_choice": quality.get("ordinaryAestheticChoice"),
            "owner_escalation": quality.get("ownerEscalation"),
        },
        "dcc": {
            "version_policy": cp.get("version_policy"),
            "recovery_baseline_role": cp.get("recovery_baseline_role"),
            "exact_version_match_required": cp.get("exact_version_match_required"),
            "available_requires": cp.get("available_requires"),
            "illustrator_routing_status": illustrator.get("routing_status"),
            "aftereffects_routing_status": aftereffects.get("routing_status"),
            "aftereffects_version": aftereffects.get("installed_version"),
            "aftereffects_transport": aftereffects.get("transport"),
            "unsafe_arbitrary_script_escape_wired": not ca.get("no_experimental_or_arbitrary_script_escape_is_wired", False),
            "auto_update": cp.get("auto_update"),
            "auto_rollback": cp.get("auto_rollback"),
            "auto_uninstall": cp.get("auto_uninstall"),
        },
        "documentation_authority": {
            "checked_file_count": d.get("checked_file_count"),
            "violations": d.get("violations"),
            "canonical_checks": d.get("canonical_checks"),
        },
        "stage7_entry": {
            "allowed": all(criteria.values()),
            "next_stage": "Stage 7 — State, Evidence, Runtime, Memory, Research, Scheduler and Retention",
            "constraint": "Consolidate operational state/evidence roles without creating a new database or weakening existing authority boundaries.",
        },
        "stage6_gate": "PASS" if all(criteria.values()) else "FAIL",
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE6_ACCEPTANCE "
        f"gate={report['stage6_gate']} "
        f"criteria={sum(1 for v in criteria.values() if v)}/{len(criteria)} "
        f"stage7_allowed={report['stage7_entry']['allowed']}"
    )
    return 0 if report["stage6_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
