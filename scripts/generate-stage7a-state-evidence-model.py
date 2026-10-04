#!/usr/bin/env python3
"""Generate Reform v2 Stage 7A state/evidence-model acceptance evidence.

Observation-only. Validates the semantic registry against the existing
retention registry and the Stage 6 external-effect authority baseline.
It creates no database, moves no artifacts, and authorizes no deletion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "packages" / "velvetos" / "policy"
MODEL = POLICY / "state-evidence-model.json"
RETENTION = POLICY / "artifact-retention.json"
POLICY_REGISTRY = POLICY / "policy-registry.json"
OUT = POLICY / "reports" / "stage7a-state-evidence-model.json"

CATEGORIES = {
    "CANONICAL_STATE",
    "EVIDENCE_RECEIPT",
    "AUTHORIZATION_DECISION",
    "AUDIT_HISTORY",
}
REQUIRED_SURFACES = {
    "jobs-ledger",
    "office-followups",
    "office-dead-letter",
    "manager-handoff",
    "task-checkpoints",
    "runtime-health-receipts",
    "jobs-sync-receipt",
    "research-sources",
    "exact-action-receipt",
    "office-decisions-history",
    "media-catalog",
    "media-intake-current-state",
    "media-intake-event-history",
    "content-approval-queue",
    "content-event-history",
    "feed-audit-evidence",
    "content-calendar",
    "production-completion",
    "publication-operational-state",
    "generated-office-output-history",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_show(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-against", required=True)
    parser.add_argument("--captured-at", required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    require(len(args.prepared_against) == 40, "--prepared-against must be a full Git SHA")

    model = load(MODEL)
    retention = load(RETENTION)
    policies = load(POLICY_REGISTRY)

    require(model.get("schema_version") == 1, "state/evidence schema_version drift")
    require(model.get("registry_kind") == "velvetos_state_evidence_model", "registry_kind drift")
    require(model.get("status") == "ACTIVE_STAGE7A", "Stage 7A model not active")

    categories = model.get("categories") or []
    category_ids = [row.get("id") for row in categories if isinstance(row, dict)]
    require(set(category_ids) == CATEGORIES and len(category_ids) == 4, "exactly four semantic categories are required")
    category_by_id = {row["id"]: row for row in categories}
    require(category_by_id["CANONICAL_STATE"].get("can_authorize_external_effect") is False,
            "canonical state may not authorize external effects")
    require(category_by_id["EVIDENCE_RECEIPT"].get("can_authorize_external_effect") is False,
            "evidence may not authorize external effects")
    require(category_by_id["AUDIT_HISTORY"].get("can_authorize_external_effect") is False,
            "audit/history may not authorize external effects")
    require(category_by_id["AUTHORIZATION_DECISION"].get("can_authorize_external_effect") is True,
            "authorization decision category must be the sole category that can authorize an external effect")

    invariants = model.get("invariants") or {}
    expected_true = {
        "exactly_four_categories",
        "one_canonical_owner_per_domain",
        "compatibility_paths_are_not_authority",
        "projections_are_not_authority_outside_their_narrow_domain",
        "evidence_never_authorizes_external_effect",
        "authorization_decision_is_distinct_from_evidence",
        "audit_history_never_overwrites_current_state",
        "superseded_current_state_becomes_history",
        "no_new_database",
    }
    require(all(invariants.get(key) is True for key in expected_true), "Stage 7A invariant drift")
    scope = model.get("scope") or {}
    require(scope.get("storage_change") == "NONE_STAGE7A", "Stage 7A may not introduce storage migration")
    require(scope.get("migration_change") == "NONE_STAGE7A", "Stage 7A may not move artifacts")
    require(scope.get("deletion_authorized") is False, "Stage 7A may not authorize deletion")

    retention_ids = {
        row.get("artifact_class_id")
        for row in (retention.get("entries") or [])
        if isinstance(row, dict) and isinstance(row.get("artifact_class_id"), str)
    }
    defaults = model.get("retention_defaults") or []
    default_ids = [row.get("artifact_class_id") for row in defaults if isinstance(row, dict)]
    require(len(default_ids) == len(set(default_ids)), "duplicate retention default mapping")
    require(set(default_ids) == retention_ids, "every retention-registry artifact class must have one Stage 7A semantic default")
    require(all(row.get("category") in CATEGORIES for row in defaults if isinstance(row, dict)),
            "retention default references unknown semantic category")

    surfaces = model.get("surfaces") or []
    ids = [row.get("id") for row in surfaces if isinstance(row, dict)]
    require(len(ids) == len(set(ids)), "duplicate state/evidence surface id")
    require(REQUIRED_SURFACES <= set(ids), "required operational surface mapping is incomplete")
    for row in surfaces:
        require(isinstance(row, dict), "surface row must be object")
        sid = row.get("id")
        require(row.get("category") in CATEGORIES, f"{sid}: unknown category")
        require(isinstance(row.get("canonical_owner"), str) and bool(row["canonical_owner"].strip()),
                f"{sid}: canonical_owner required")
        require(isinstance(row.get("authority_scope"), str) and bool(row["authority_scope"].strip()),
                f"{sid}: authority_scope required")
        compatibility = row.get("compatibility_paths")
        require(isinstance(compatibility, list), f"{sid}: compatibility_paths must be list")
        require(all(isinstance(item, dict) and item.get("authoritative") is False for item in compatibility),
                f"{sid}: compatibility path cannot be authoritative")
        if row.get("category") != "AUTHORIZATION_DECISION":
            require(row.get("policy_gate_eligible") is False,
                    f"{sid}: only AUTHORIZATION_DECISION may satisfy an external-effect policy gate")

    auth_surfaces = [row for row in surfaces if row.get("category") == "AUTHORIZATION_DECISION"]
    require(len(auth_surfaces) == 1 and auth_surfaces[0].get("id") == "exact-action-receipt",
            "exact-action receipt must be the only Stage 7A authorization-decision surface")
    require((auth_surfaces[0].get("locator") or {}).get("values") == ["velvetos.action-receipt.v1"],
            "authorization decision must remain bound to the canonical action-receipt schema")

    handoff = next(row for row in surfaces if row.get("id") == "manager-handoff")
    require(handoff.get("projection_only") is True and handoff.get("policy_gate_eligible") is False,
            "HANDOFF must remain a continuation projection, not policy authority")
    require("continuation/index" in handoff.get("authority_scope", ""),
            "HANDOFF authority must be explicitly narrow")

    work_ledger = model.get("work_ledger") or {}
    require(work_ledger.get("status") == "INDEX_ONLY_NOT_IMPLEMENTED_STAGE7A",
            "Work Ledger must remain unimplemented in Stage 7A")
    require(work_ledger.get("destination_stage") == "7D", "Work Ledger implementation remains owned by Stage 7D")
    require(work_ledger.get("references_only") is True, "Work Ledger must be references-only")
    require(work_ledger.get("policy_authority") is False, "Work Ledger cannot be policy authority")
    require(work_ledger.get("external_effect_authority") is False, "Work Ledger cannot authorize external effects")
    require(work_ledger.get("full_transcript_allowed") is False, "Work Ledger cannot become a transcript store")
    require(work_ledger.get("embedded_large_media_allowed") is False, "Work Ledger cannot become a media store")
    require(work_ledger.get("implementation_allowed_before_stage7d") is False,
            "Stage 7A must not create Work Ledger storage")

    current_policy_bytes = POLICY_REGISTRY.read_bytes()
    baseline_policy_bytes = git_show(args.prepared_against, "packages/velvetos/policy/policy-registry.json")
    require(current_policy_bytes == baseline_policy_bytes,
            "Stage 7A must not alter external-effect policy registry or decision ownership")

    contract = policies.get("external_effect_contract") or {}
    require(contract.get("single_authority_per_effect") is True,
            "single external-effect authority invariant changed")
    evidence_rows = contract.get("evidence_input_classes") or []
    require(all(row.get("can_authorize_external_effect") is False for row in evidence_rows if isinstance(row, dict)),
            "canonical external-effect evidence inputs must remain non-authoritative")

    control_readme = (ROOT / "office" / "control" / "README.md").read_text(encoding="utf-8")
    require("מצביעי תאימות (לא SoT)" in control_readme, "Office compatibility pointers must remain non-SoT")
    handoff_doc = (ROOT / "packages" / "vfmem" / "HANDOFF.md").read_text(encoding="utf-8")
    require("A handoff is **context, not authority**." in handoff_doc,
            "handoff context-not-authority contract missing")
    task_state = (ROOT / "scripts" / "vf_task_state.py").read_text(encoding="utf-8")
    require("duplicate task_id in selected checkpoints" in task_state,
            "task checkpoint uniqueness guard missing")

    criteria = {
        "exactly_four_semantic_categories": True,
        "all_retention_registry_artifact_classes_are_mapped": set(default_ids) == retention_ids,
        "canonical_owner_and_authority_scope_are_explicit_per_operational_surface": all(
            bool(row.get("canonical_owner")) and bool(row.get("authority_scope")) for row in surfaces
        ),
        "compatibility_paths_are_non_authoritative": all(
            item.get("authoritative") is False
            for row in surfaces
            for item in row.get("compatibility_paths", [])
        ),
        "evidence_is_distinct_from_authorization_decision": (
            category_by_id["EVIDENCE_RECEIPT"].get("can_authorize_external_effect") is False
            and len(auth_surfaces) == 1
        ),
        "audit_history_cannot_overwrite_current_state": invariants.get("audit_history_never_overwrites_current_state") is True,
        "handoff_is_continuation_context_not_cross_domain_authority": handoff.get("projection_only") is True,
        "work_ledger_is_refs_only_and_not_a_second_store": (
            work_ledger.get("references_only") is True
            and work_ledger.get("implementation_allowed_before_stage7d") is False
        ),
        "external_effect_policy_registry_is_unchanged": current_policy_bytes == baseline_policy_bytes,
        "no_storage_migration_or_deletion_is_authorized": (
            scope.get("storage_change") == "NONE_STAGE7A"
            and scope.get("migration_change") == "NONE_STAGE7A"
            and scope.get("deletion_authorized") is False
        ),
    }

    report = {
        "schema": "velvetos.stage7a-state-evidence-model.v1",
        "stage": "7A",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "purpose": "Define one semantic model for state/evidence/authorization/history without adding a store, moving artifacts, or changing effect authority.",
        "model": {
            "path": MODEL.relative_to(ROOT).as_posix(),
            "sha256": sha256(MODEL),
            "categories": sorted(CATEGORIES),
            "surface_count": len(surfaces),
            "retention_class_count": len(retention_ids),
            "retention_classes_mapped": len(set(default_ids) & retention_ids),
        },
        "authority_baseline": {
            "policy_registry_path": POLICY_REGISTRY.relative_to(ROOT).as_posix(),
            "policy_registry_sha256": sha256(POLICY_REGISTRY),
            "unchanged_from_prepared_against": current_policy_bytes == baseline_policy_bytes,
            "single_authority_per_effect": contract.get("single_authority_per_effect"),
        },
        "work_ledger": {
            "status": work_ledger.get("status"),
            "destination_stage": work_ledger.get("destination_stage"),
            "references_only": work_ledger.get("references_only"),
            "policy_authority": work_ledger.get("policy_authority"),
            "external_effect_authority": work_ledger.get("external_effect_authority"),
        },
        "acceptance": criteria,
        "repository_acceptance": "PASS" if all(criteria.values()) else "FAIL",
        "next_stage": "Stage 7B — Memory/Learning lifecycle" if all(criteria.values()) else None,
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    out.write_bytes(payload.encode("utf-8"))
    print(
        "STAGE7A_STATE_EVIDENCE "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(1 for value in criteria.values() if value)}/{len(criteria)} "
        f"surfaces={len(surfaces)} retention={len(retention_ids)}/{len(default_ids)}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
