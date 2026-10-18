#!/usr/bin/env python3
"""Structural/executable Phase 0 sensor for Office v2. No network/provider mutation."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE0 = ROOT / "docs" / "implementation" / "office-v2" / "phase0"
CONTRACTS = PHASE0 / "contracts"

REQUIRED = [
    PHASE0 / "README.md",
    PHASE0 / "authority-map-v0.1.json",
    PHASE0 / "state-class-map-v0.1.json",
    PHASE0 / "contract-registry-v0.json",
    PHASE0 / "backup-restore-admission-policy-v0.md",
    PHASE0 / "credential-trust-classes-v0.json",
    PHASE0 / "external-effect-safety-contract-v0.md",
    PHASE0 / "context-pressure-and-compaction-runbook-v0.md",
    CONTRACTS / "correlation-envelope.schema.json",
    CONTRACTS / "provenance-envelope.schema.json",
    CONTRACTS / "capability-contract.schema.json",
    CONTRACTS / "provider-contract.schema.json",
    CONTRACTS / "evidence-contract.schema.json",
    CONTRACTS / "artifact-contract.schema.json",
    CONTRACTS / "node-contract.schema.json",
    CONTRACTS / "side-effect-contract.schema.json",
    CONTRACTS / "effect-intent.schema.json",
    CONTRACTS / "effect-receipt.schema.json",
    CONTRACTS / "project-state-manifest.schema.json",
    CONTRACTS / "migration-ledger-entry.schema.json",
    CONTRACTS / "ecosystem-inventory-entry.schema.json",
    ROOT / "scripts" / "vf_office_v2_continuity.py",
    ROOT / "scripts" / "vf_office_v2_migration_console.py",
]

PROJECT_STATE_FIELDS = {
    "schema_version", "project_id", "checkpoint_id", "parent_checkpoint_id",
    "current_goal", "scope_and_constraints", "completed_work", "decisions",
    "unresolved_questions", "active_tasks", "blockers", "artifact_document_refs",
    "important_links", "receipt_refs", "production_snapshot_refs", "migration_phase",
    "gate_status", "active_experiments", "rollback_point", "prohibited_actions",
    "runtime_refs", "business_entity_refs", "assumptions", "risks",
    "resume_instructions", "content_hash",
}

NODE_FIELDS = {
    "node_id", "os_build", "execution_surfaces", "cpu_ram", "gpu_vram",
    "installed_applications", "capability_contract_versions", "local_runtimes",
    "load", "health", "artifact_locality", "trust_security_level",
    "maintenance_state", "compatibility_range",
}

BACKUP_MARKERS = {
    "data owner", "storage path", "backup target", "off-host copy", "encryption",
    "RPO/RTO", "restore procedure", "schema migration path",
    "export/uninstall path", "health probe", "restore drill",
}

CONTRACT_SEMANTICS = {
    "success", "failure", "idempotency_scope", "cancellation", "timeout",
    "evidence", "compatibility", "readback", "fallback",
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    raise AssertionError("unreachable")


def require_text(path: Path, needles: set[str] | list[str]) -> None:
    text = path.read_text(encoding="utf-8-sig")
    missing = sorted(needle for needle in needles if needle not in text)
    if missing:
        fail(f"{path.relative_to(ROOT)} missing markers: {missing}")


def run_self_test(path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(path), "--self-test", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        fail(f"{path.name} self-test failed: {(proc.stderr or proc.stdout)[:800]}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        fail(f"{path.name} self-test did not return JSON: {exc}")
    if payload.get("status") != "PASS":
        fail(f"{path.name} self-test status={payload.get('status')}")


def required_property_names(schema: dict) -> set[str]:
    return set(schema.get("required") or [])


def main() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.is_file()]
    if missing:
        fail("missing Phase 0 files: " + ", ".join(missing))

    state_map = load_json(PHASE0 / "state-class-map-v0.1.json")
    expected_classes = {
        "VERSIONED_DEFINITION", "BUSINESS_TRUTH", "PROJECT_STATE", "RUNTIME_STATE",
        "EVENT", "GENERATED_ARTIFACT", "DERIVED_SEARCH_OR_MEMORY",
    }
    actual_classes = {row.get("id") for row in state_map.get("classes", [])}
    if actual_classes != expected_classes:
        fail(f"state-class ids mismatch: {sorted(actual_classes)}")
    if state_map.get("relationship_to_reform_v2", {}).get("orthogonal_axis") is not True:
        fail("Office v2 state classes must be orthogonal to Reform v2 semantic categories")
    if state_map.get("git_live_state_policy") != "VERSIONED_DEFINITION_ONLY":
        fail("Git live-state policy must remain VERSIONED_DEFINITION_ONLY")

    authority_map = load_json(PHASE0 / "authority-map-v0.1.json")
    if authority_map.get("single_external_effect_authority") is not True:
        fail("authority map must preserve one external-effect authority")
    if authority_map.get("new_production_writer_added") is not False:
        fail("Phase 0 must not add a production writer")
    for row in authority_map.get("domains") or []:
        for key in (
            "domain", "production_writer", "authoritative_store", "readers",
            "allowed_mutations", "fallback", "forbidden_second_writers",
        ):
            if key not in row:
                fail(f"authority domain {row.get('domain')} missing {key}")

    registry = load_json(PHASE0 / "contract-registry-v0.json")
    semantics = set(registry.get("required_semantics") or [])
    if semantics != CONTRACT_SEMANTICS:
        fail(f"contract registry semantic set mismatch: {sorted(semantics)}")
    contract_rows = registry.get("contracts") or []
    if len(contract_rows) < 13:
        fail("contract registry is incomplete")
    for row in contract_rows:
        rel = row.get("path")
        if not rel or not (ROOT / rel).is_file():
            fail(f"contract path missing: {rel}")
    if registry.get("new_production_writer") is not False:
        fail("contract registry claims a Phase 0 production writer")

    project_schema = load_json(CONTRACTS / "project-state-manifest.schema.json")
    missing_project_fields = sorted(PROJECT_STATE_FIELDS - required_property_names(project_schema))
    if missing_project_fields:
        fail(f"Project State schema missing START HERE fields: {missing_project_fields}")

    node_schema = load_json(CONTRACTS / "node-contract.schema.json")
    missing_node_fields = sorted(NODE_FIELDS - required_property_names(node_schema))
    if missing_node_fields:
        fail(f"Node Contract missing START HERE fields: {missing_node_fields}")

    require_text(PHASE0 / "backup-restore-admission-policy-v0.md", BACKUP_MARKERS)
    require_text(
        PHASE0 / "external-effect-safety-contract-v0.md",
        {"EffectIntent", "EffectReceipt", "UNKNOWN_OUTCOME", "blind-retry", "policy-registry.json"},
    )
    require_text(
        PHASE0 / "context-pressure-and-compaction-runbook-v0.md",
        {"turn_volume", "unresolved_decisions", "tool_activity", "checkpoint_age", "upcoming_risk", "manual_trigger"},
    )

    credentials = load_json(PHASE0 / "credential-trust-classes-v0.json")
    if credentials.get("secrets_in_git_allowed") is not False:
        fail("credential contract must forbid secrets in Git")
    if credentials.get("lab_receives_production_credentials_by_default") is not False:
        fail("LAB must not receive production credentials by default")
    expected_credential_classes = {
        "LAB_ONLY_SECRET", "PRODUCTION_READ", "PRODUCTION_SCOPED_WRITE",
        "OWNER_HIGH_IMPACT", "HUMAN_ONLY",
    }
    actual_credential_classes = {row.get("id") for row in credentials.get("credential_classes") or []}
    if actual_credential_classes != expected_credential_classes:
        fail(f"credential class ids mismatch: {sorted(actual_credential_classes)}")

    side_effect = load_json(CONTRACTS / "side-effect-contract.schema.json")
    side_text = json.dumps(side_effect, sort_keys=True)
    for needle in (
        "policy-registry.json", "blind_retry", "unknown_outcome", "cancellation",
        "timeout", "compatibility", "readback", "fallback",
    ):
        if needle not in side_text:
            fail(f"side-effect contract missing semantic marker {needle}")

    correlation = load_json(CONTRACTS / "correlation-envelope.schema.json")
    correlation_required = set(correlation.get("required") or [])
    for key in ("request_id", "project_id", "workflow_id", "run_id", "attempt_id"):
        if key not in correlation_required:
            fail(f"correlation envelope missing required {key}")
    for key in (
        "conversation_id", "approval_id", "domain_entity_id", "event_id", "artifact_id",
        "provider_id", "node_id", "policy_decision_id", "receipt_id",
    ):
        if key not in (correlation.get("properties") or {}):
            fail(f"correlation envelope missing optional identifier {key}")

    sensor_registry = load_json(ROOT / "packages" / "velvetos" / "policy" / "sensor-registry.json")
    rows = [row for row in sensor_registry.get("sensors") or [] if row.get("id") == "check-office-v2-phase0"]
    if len(rows) != 1 or rows[0].get("path") != "scripts/check-office-v2-phase0.py":
        fail("Office v2 Phase 0 sensor is not registered exactly once")

    run_self_test(ROOT / "scripts" / "vf_office_v2_continuity.py")
    run_self_test(ROOT / "scripts" / "vf_office_v2_migration_console.py")

    print("OK office-v2-phase0 contracts=PASS continuity=PASS migration-console=PASS authority=single")


if __name__ == "__main__":
    main()
