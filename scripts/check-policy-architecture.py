#!/usr/bin/env python3
"""Validate VelvetOS policy registries and optionally enforce the Stage 0 policy-creation freeze."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "packages" / "velvetos" / "policy"
POLICIES = POLICY_DIR / "policy-registry.json"
SENSORS = POLICY_DIR / "sensor-registry.json"
SELECTION = POLICY_DIR / "sensor-selection.json"
ARTIFACTS = POLICY_DIR / "artifact-retention.json"
STATE_EVIDENCE_MODEL = POLICY_DIR / "state-evidence-model.json"
SCHEMAS = POLICY_DIR / "schema"
REPORTS = POLICY_DIR / "reports"
ACTION_RECEIPT_SCHEMA = SCHEMAS / "action-receipt.schema.json"
ACTION_RECEIPT_VECTORS = POLICY_DIR / "action-receipt-test-vectors.json"
ACTION_RECEIPT_VALIDATOR = ROOT / "scripts" / "vf_action_receipt.py"
STAGE4_ACCEPTANCE = REPORTS / "stage4-acceptance.json"
STAGE4_ACCEPTANCE_GENERATOR = ROOT / "scripts" / "generate-stage4-acceptance.py"
STAGE5_ACCEPTANCE = REPORTS / "stage5-acceptance.json"
STAGE5_ACCEPTANCE_GENERATOR = ROOT / "scripts" / "generate-stage5-acceptance.py"
STAGE6_ACCEPTANCE = REPORTS / "stage6-acceptance.json"
STAGE6_ACCEPTANCE_GENERATOR = ROOT / "scripts" / "generate-stage6-acceptance.py"
STAGE7A_ACCEPTANCE = REPORTS / "stage7a-state-evidence-model.json"
STAGE7A_ACCEPTANCE_GENERATOR = ROOT / "scripts" / "generate-stage7a-state-evidence-model.py"
STAGE7D_ACCEPTANCE = REPORTS / "stage7d-artifact-retention.json"
STAGE7D_ACCEPTANCE_GENERATOR = ROOT / "scripts" / "generate-stage7d-artifact-retention.py"
STAGE7_ACCEPTANCE = REPORTS / "stage7-acceptance.json"
STAGE7_ACCEPTANCE_GENERATOR = ROOT / "scripts" / "generate-stage7-acceptance.py"
STAGE8A_INVENTORY = REPORTS / "stage8a-core-instance-inventory.json"
STAGE8A_INVENTORY_GENERATOR = ROOT / "scripts" / "generate-stage8a-core-instance-inventory.py"
STAGE8B_RESOLVER = REPORTS / "stage8b-instance-resolver-foundation.json"
STAGE8B_RESOLVER_GENERATOR = ROOT / "scripts" / "generate-stage8b-instance-resolver-foundation.py"
STAGE8B_CONFIG = REPORTS / "stage8b-canonical-instance-config.json"
STAGE8B_CONFIG_GENERATOR = ROOT / "scripts" / "generate-stage8b-canonical-instance-config.py"
STAGE8C_SAMPLE = REPORTS / "stage8c-sample-profile-consumers.json"
STAGE8C_SAMPLE_GENERATOR = ROOT / "scripts" / "generate-stage8c-sample-profile-consumers.py"
STAGE8C_ROOT_DESK = REPORTS / "stage8c-root-desk-readers.json"
STAGE8C_ROOT_DESK_GENERATOR = ROOT / "scripts" / "generate-stage8c-root-desk-readers.py"
STAGE8C_DESK_CATALOG = REPORTS / "stage8c-desk-catalog-bindings.json"
STAGE8C_DESK_CATALOG_GENERATOR = ROOT / "scripts" / "generate-stage8c-desk-catalog-bindings.py"
STAGE8C_LIVING_RULES = REPORTS / "stage8c-living-studio-rules.json"
STAGE8C_LIVING_RULES_GENERATOR = ROOT / "scripts" / "generate-stage8c-living-studio-rules.py"
STAGE8C_CONTROL_API_FLEET = REPORTS / "stage8c-control-api-fleet.json"
STAGE8C_CONTROL_API_FLEET_GENERATOR = ROOT / "scripts" / "generate-stage8c-control-api-fleet.py"
STAGE8C_EXPERT_MODULES = REPORTS / "stage8c-expert-modules.json"
STAGE8C_EXPERT_MODULES_GENERATOR = ROOT / "scripts" / "generate-stage8c-expert-modules.py"
STAGE8C_CHATGPT_DISTRIBUTION = REPORTS / "stage8c-chatgpt-distribution-consumers.json"
STAGE8C_CHATGPT_DISTRIBUTION_GENERATOR = ROOT / "scripts" / "generate-stage8c-chatgpt-distribution-consumers.py"
STAGE8C_WINDOWS_HOST = REPORTS / "stage8c-windows-host-binding.json"
STAGE8C_WINDOWS_HOST_GENERATOR = ROOT / "scripts" / "generate-stage8c-windows-host-binding.py"
STAGE8C_CLOSURE = REPORTS / "stage8c-closure.json"
STAGE8C_CLOSURE_GENERATOR = ROOT / "scripts" / "generate-stage8c-closure.py"
STAGE8D_READINESS = REPORTS / "stage8d-retirement-readiness.json"
STAGE8D_READINESS_GENERATOR = ROOT / "scripts" / "generate-stage8d-retirement-readiness.py"
STAGE8D_FLEET = REPORTS / "stage8d-fleet-consumer-migration.json"
STAGE8D_FLEET_GENERATOR = ROOT / "scripts" / "generate-stage8d-fleet-consumer-migration.py"
STAGE8D_ROOT_DESK = REPORTS / "stage8d-root-desk-consumer-migration.json"
STAGE8D_ROOT_DESK_GENERATOR = ROOT / "scripts" / "generate-stage8d-root-desk-consumer-migration.py"
STAGE8D_TOOL_STATUS = REPORTS / "stage8d-tool-status-consumer-migration.json"
STAGE8D_TOOL_STATUS_GENERATOR = ROOT / "scripts" / "generate-stage8d-tool-status-consumer-migration.py"
STAGE8D_CHATGPT_CORE = REPORTS / "stage8d-chatgpt-core-consumer-migration.json"
STAGE8D_CHATGPT_CORE_GENERATOR = ROOT / "scripts" / "generate-stage8d-chatgpt-core-consumer-migration.py"
STAGE8D_POST_MIGRATION = REPORTS / "stage8d-post-migration-readiness.json"
STAGE8D_POST_MIGRATION_GENERATOR = ROOT / "scripts" / "generate-stage8d-post-migration-readiness.py"
STAGE8D_SAMPLE_ROLLBACK_CLOSURE = REPORTS / "stage8d-sample-profile-rollback-closure.json"
STAGE8D_SAMPLE_ROLLBACK_CLOSURE_GENERATOR = ROOT / "scripts" / "generate-stage8d-sample-profile-rollback-closure.py"
STAGE8D_SAMPLE_CONSUMER_CORRECTION = REPORTS / "stage8d-sample-profile-consumer-correction.json"
STAGE8D_SAMPLE_CONSUMER_CORRECTION_GENERATOR = ROOT / "scripts" / "generate-stage8d-sample-profile-consumer-correction.py"
STAGE8D_SAMPLE_ROLLBACK_RECLOSURE = REPORTS / "stage8d-sample-profile-rollback-reclosure.json"
STAGE8D_SAMPLE_ROLLBACK_RECLOSURE_GENERATOR = ROOT / "scripts" / "generate-stage8d-sample-profile-rollback-reclosure.py"
STAGE8D_SAMPLE_DELETION_GATE = REPORTS / "stage8d-sample-profile-deletion-gate.json"
STAGE8D_SAMPLE_DELETION_GATE_GENERATOR = ROOT / "scripts" / "generate-stage8d-sample-profile-deletion-gate.py"
STAGE8D_RETIREMENT_SEMANTIC_AUDIT = REPORTS / "stage8d-retirement-semantic-audit.json"
STAGE8D_RETIREMENT_SEMANTIC_AUDIT_GENERATOR = ROOT / "scripts" / "generate-stage8d-retirement-semantic-audit.py"
STAGE8D_ROOT_DESK_RUNTIME_CORRECTION = REPORTS / "stage8d-root-desk-runtime-consumer-correction.json"
STAGE8D_ROOT_DESK_RUNTIME_CORRECTION_GENERATOR = ROOT / "scripts" / "generate-stage8d-root-desk-runtime-consumer-correction.py"
STAGE8D_ROOT_DESK_ROLLBACK_CLOSURE = REPORTS / "stage8d-root-desk-rollback-closure.json"
STAGE8D_ROOT_DESK_ROLLBACK_CLOSURE_GENERATOR = ROOT / "scripts" / "generate-stage8d-root-desk-rollback-closure.py"
STAGE8D_FLEET_RUNTIME_CORRECTION = REPORTS / "stage8d-fleet-runtime-consumer-correction.json"
STAGE8D_FLEET_RUNTIME_CORRECTION_GENERATOR = ROOT / "scripts" / "generate-stage8d-fleet-runtime-consumer-correction.py"
STAGE8D_FLEET_ROLLBACK_CLOSURE = REPORTS / "stage8d-fleet-rollback-closure.json"
STAGE8D_FLEET_ROLLBACK_CLOSURE_GENERATOR = ROOT / "scripts" / "generate-stage8d-fleet-rollback-closure.py"
STAGE8D_TOOL_STATUS_SEMANTIC_CORRECTION = REPORTS / "stage8d-tool-status-semantic-correction.json"
STAGE8D_TOOL_STATUS_SEMANTIC_CORRECTION_GENERATOR = ROOT / "scripts" / "generate-stage8d-tool-status-semantic-correction.py"
STAGE8D_TOOL_STATUS_ROLLBACK_CLOSURE = REPORTS / "stage8d-tool-status-rollback-closure.json"
STAGE8D_TOOL_STATUS_ROLLBACK_CLOSURE_GENERATOR = ROOT / "scripts" / "generate-stage8d-tool-status-rollback-closure.py"
STAGE8D_CHATGPT_SEMANTIC_CORRECTION = REPORTS / "stage8d-chatgpt-semantic-correction.json"
STAGE8D_CHATGPT_SEMANTIC_CORRECTION_GENERATOR = ROOT / "scripts" / "generate-stage8d-chatgpt-semantic-correction.py"
STAGE8D_CHATGPT_ROLLBACK_CLOSURE = REPORTS / "stage8d-chatgpt-rollback-closure.json"
STAGE8D_CHATGPT_ROLLBACK_CLOSURE_GENERATOR = ROOT / "scripts" / "generate-stage8d-chatgpt-rollback-closure.py"
EXPECTED_REPORTS = {
    "authority-graph.json",
    "sensor-coverage-graph.json",
    "coverage-report.json",
    "conflict-report.json",
    "artifact-inventory.json",
    "ci-baseline.json",
    "baseline-snapshot.json",
    "migration-map.json",
    "stage2-sensor-registry-audit.json",
    "stage3-preactivation-plan.json",
    "stage4d-instagram-happy-path-implementation.json",
    "stage4-acceptance.json",
    "stage5-acceptance.json",
    "stage6-acceptance.json",
    "stage7a-state-evidence-model.json",
    "stage7d-morning-green-asset-archive.json",
    "stage7d-artifact-retention.json",
    "stage7-acceptance.json",
    "stage8a-core-instance-inventory.json",
    "stage8b-instance-resolver-foundation.json",
    "stage8b-canonical-instance-config.json",
    "stage8c-sample-profile-consumers.json",
    "stage8c-root-desk-readers.json",
    "stage8c-desk-catalog-bindings.json",
    "stage8c-living-studio-rules.json",
    "stage8c-control-api-fleet.json",
    "stage8c-expert-modules.json",
    "stage8c-chatgpt-distribution-consumers.json",
    "stage8c-windows-host-binding.json",
    "stage8c-closure.json",
    "stage8d-retirement-readiness.json",
    "stage8d-fleet-consumer-migration.json",
    "stage8d-root-desk-consumer-migration.json",
    "stage8d-tool-status-consumer-migration.json",
    "stage8d-chatgpt-core-consumer-migration.json",
    "stage8d-post-migration-readiness.json",
    "stage8d-sample-profile-rollback-closure.json",
    "stage8d-sample-profile-consumer-correction.json",
    "stage8d-sample-profile-rollback-reclosure.json",
    "stage8d-sample-profile-deletion-gate.json",
    "stage8d-retirement-semantic-audit.json",
    "stage8d-root-desk-runtime-consumer-correction.json",
    "stage8d-root-desk-rollback-closure.json",
    "stage8d-fleet-runtime-consumer-correction.json",
    "stage8d-fleet-rollback-closure.json",
    "stage8d-tool-status-semantic-correction.json",
    "stage8d-tool-status-rollback-closure.json",
    "stage8d-chatgpt-semantic-correction.json",
    "stage8d-chatgpt-rollback-closure.json",
}

RISK = {"critical", "high", "medium", "low"}
STATUS = {"active", "conflicted", "deprecated", "temporary_hotfix"}
FALLBACK = {"FULL_SUITE", "FULL_DOMAIN", "ALWAYS_ON"}
MAPPING = {"broad_legacy_baseline", "mapped", "legacy", "deprecated"}
POLICY_ROLES = {"effect_authority", "evidence_input", "router", "repository_guard", "escalation_boundary"}
DECISION_VOCABULARY = {"ALLOW", "DENY", "REQUIRE_OWNER_APPROVAL"}
RECEIPT_MODES = {"EXACT_ACTION_REQUIRED", "EXACT_ACTION_ON_COMMITMENT", "OWNER_RESERVED", "POLICY_NATIVE_RECEIPT"}
DECISION_AUTHORITY_KINDS = {"runtime_evaluator", "runtime_boundary", "canonical_policy_boundary"}
POLICY_REF = re.compile(r"policy_id\s*[:=]\s*([a-z0-9]+(?:[._-][a-z0-9]+)*)", re.I)
RESERVED = re.compile(
    r"authorized_for_tool_publish|approved_for_manual_posting|standingAuthorization|"
    r"publishAuthorized|publication_authorized|review_delivery_authorized",
    re.I,
)
NORMATIVE = re.compile(
    r"\b(?:ALLOW|DENY|MUST|REQUIRED|FORBIDDEN|AUTHORIZED|APPROVAL REQUIRED)\b|"
    r"(?:אסור|חובה|מותר|דורש(?:ת)? אישור|אישור בעלים)",
    re.I,
)
EXTERNAL = re.compile(
    r"publish|send|delete|payment|cost|billing|credential|permission|secret|boost|"
    r"whatsapp|instagram|gmail|פרסו|שליח|מחיק|מחוק|תשלו|עלות|הרשא|סוד|וואטסאפ|אינסטגרם|ג.?ימייל",
    re.I,
)

def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{path.relative_to(ROOT)}: invalid JSON: {exc}") from exc


def existing_repo_path(value: str) -> bool:
    return bool(value) and (ROOT / value).exists()


def require(condition: bool, message: str, problems: list[str]) -> None:
    if not condition:
        problems.append(message)


def validate_registries() -> tuple[list[str], set[str]]:
    problems: list[str] = []
    policies = load(POLICIES)
    sensors = load(SENSORS)
    selection = load(SELECTION)
    artifacts = load(ARTIFACTS)

    require(policies.get("schema_version") == 1, "policy registry schema_version", problems)
    require(
        policies.get("decision_ownership") == "REFERENCES_ONLY_DO_NOT_DUPLICATE_POLICY_DECISIONS",
        "policy registry must remain references-only",
        problems,
    )
    rows = policies.get("policies")
    require(isinstance(rows, list), "policy registry policies must be a list", problems)
    rows = rows if isinstance(rows, list) else []
    policy_ids = [row.get("policy_id") for row in rows if isinstance(row, dict)]
    require(len(policy_ids) == len(set(policy_ids)), "duplicate policy_id", problems)
    known_policies = {value for value in policy_ids if isinstance(value, str)}

    for row in rows:
        if not isinstance(row, dict):
            problems.append("policy row must be object")
            continue
        pid = row.get("policy_id")
        require(isinstance(pid, str) and bool(pid), "policy_id missing", problems)
        require(row.get("status") in STATUS, f"{pid}: invalid status", problems)
        require(row.get("risk_class") in RISK, f"{pid}: invalid risk_class", problems)
        authorities = row.get("authority_locations")
        require(isinstance(authorities, list) and bool(authorities), f"{pid}: authority_locations required", problems)
        if isinstance(authorities, list):
            for path in authorities:
                require(isinstance(path, str) and existing_repo_path(path), f"{pid}: missing authority {path}", problems)
        machine = row.get("machine_policy_locations")
        require(isinstance(machine, list), f"{pid}: machine_policy_locations must be list", problems)
        if isinstance(machine, list):
            for path in machine:
                require(isinstance(path, str) and existing_repo_path(path), f"{pid}: missing machine policy {path}", problems)
        if row.get("status") == "temporary_hotfix":
            meta = row.get("temporary_metadata")
            require(isinstance(meta, dict), f"{pid}: temporary_metadata required", problems)
            if isinstance(meta, dict):
                for key in ("source_authority", "migration_target", "review_at", "expiry_behavior"):
                    require(bool(meta.get(key)), f"{pid}: hotfix {key} required", problems)
                require(meta.get("review_at") != meta.get("expires_at"), f"{pid}: review_at must not be treated as expires_at", problems)
        require(row.get("policy_role") in POLICY_ROLES, f"{pid}: invalid or missing policy_role", problems)

    contract = policies.get("external_effect_contract")
    require(isinstance(contract, dict), "external_effect_contract missing", problems)
    contract = contract if isinstance(contract, dict) else {}
    require(contract.get("contract_version") == 1, "external-effect contract_version", problems)
    require(contract.get("single_authority_per_effect") is True, "external effects must have one authority each", problems)
    require(set(contract.get("normalized_decision_vocabulary") or []) == DECISION_VOCABULARY,
            "external-effect decision vocabulary drift", problems)
    require(contract.get("action_receipt_schema") == "packages/velvetos/policy/schema/action-receipt.schema.json",
            "action receipt schema binding mismatch", problems)
    require(contract.get("action_receipt_validator") == "scripts/vf_action_receipt.py",
            "action receipt validator binding mismatch", problems)

    evidence_rows = contract.get("evidence_input_classes")
    require(isinstance(evidence_rows, list) and bool(evidence_rows), "evidence_input_classes required", problems)
    evidence_rows = evidence_rows if isinstance(evidence_rows, list) else []
    evidence_ids = [row.get("id") for row in evidence_rows if isinstance(row, dict)]
    require(len(evidence_ids) == len(set(evidence_ids)), "duplicate evidence input class", problems)
    require(all(isinstance(row, dict) and row.get("can_authorize_external_effect") is False for row in evidence_rows),
            "evidence inputs may not authorize external effects", problems)
    evidence_id_set = {value for value in evidence_ids if isinstance(value, str)}
    runtime_health_evidence = next(
        (row for row in evidence_rows if isinstance(row, dict) and row.get("id") == "runtime_health"),
        None,
    )
    require(isinstance(runtime_health_evidence, dict), "runtime_health evidence class missing", problems)
    if isinstance(runtime_health_evidence, dict):
        require(runtime_health_evidence.get("dependency_scoped") is True,
                "runtime_health must remain dependency-scoped", problems)
        require(runtime_health_evidence.get("required_status_when_dependency_real") == "RUNTIME_HEALTHY",
                "runtime_health required status drift", problems)
        require(runtime_health_evidence.get("proof_scope_contract") == "packages/vfharness/runtime/proof-scope.json",
                "runtime_health proof-scope contract drift", problems)
        require(runtime_health_evidence.get("github_event_is_dependency_signal") is False,
                "GitHub event type must not become runtime dependency authority", problems)
        require(existing_repo_path(runtime_health_evidence.get("proof_scope_contract")),
                "runtime_health proof-scope contract missing", problems)

    effect_rows = contract.get("effects")
    require(isinstance(effect_rows, list) and bool(effect_rows), "external effect mappings required", problems)
    effect_rows = effect_rows if isinstance(effect_rows, list) else []
    effect_classes = [row.get("effect_class") for row in effect_rows if isinstance(row, dict)]
    effect_policy_ids = [row.get("policy_id") for row in effect_rows if isinstance(row, dict)]
    require(len(effect_classes) == len(set(effect_classes)), "duplicate external effect_class authority", problems)
    require(len(effect_policy_ids) == len(set(effect_policy_ids)), "policy_id may own only one external effect in Stage 4C", problems)

    policy_by_id = {row.get("policy_id"): row for row in rows if isinstance(row, dict)}
    for effect in effect_rows:
        if not isinstance(effect, dict):
            problems.append("external effect row must be object")
            continue
        effect_class = effect.get("effect_class")
        pid = effect.get("policy_id")
        require(isinstance(effect_class, str) and bool(effect_class), "external effect_class missing", problems)
        require(pid in known_policies, f"{effect_class}: unknown policy_id {pid}", problems)
        if pid in policy_by_id:
            require(policy_by_id[pid].get("policy_role") == "effect_authority",
                    f"{pid}: external effect must resolve to effect_authority role", problems)
        authority = effect.get("decision_authority")
        require(isinstance(authority, dict), f"{pid}: decision_authority required", problems)
        if isinstance(authority, dict):
            require(authority.get("kind") in DECISION_AUTHORITY_KINDS, f"{pid}: invalid decision authority kind", problems)
            require(isinstance(authority.get("path"), str) and existing_repo_path(authority.get("path")),
                    f"{pid}: decision authority path missing", problems)
        require(effect.get("receipt_mode") in RECEIPT_MODES, f"{pid}: invalid receipt_mode", problems)
        inputs = effect.get("evidence_inputs")
        require(isinstance(inputs, list), f"{pid}: evidence_inputs must be list", problems)
        if isinstance(inputs, list):
            require(set(inputs).issubset(evidence_id_set), f"{pid}: unknown evidence input class", problems)

    declared_effect_policies = {
        row.get("policy_id") for row in rows
        if isinstance(row, dict) and row.get("policy_role") == "effect_authority"
    }
    require(set(effect_policy_ids) == declared_effect_policies,
            "every effect_authority policy must map exactly one external effect", problems)
    for pid in ("visible_text.finalization", "public.cta"):
        require(policy_by_id.get(pid, {}).get("policy_role") == "evidence_input",
                f"{pid} must remain evidence_input, not external authorization authority", problems)
    require(policy_by_id.get("project.request.preflight", {}).get("policy_role") == "router",
            "project.request.preflight must remain router-only", problems)

    for path in (ACTION_RECEIPT_SCHEMA, ACTION_RECEIPT_VECTORS, ACTION_RECEIPT_VALIDATOR):
        require(path.is_file(), f"missing {path.relative_to(ROOT)}", problems)
    if ACTION_RECEIPT_SCHEMA.is_file():
        schema = load(ACTION_RECEIPT_SCHEMA)
        require(schema.get("$id") == "velvetos.action-receipt.v1", "action receipt schema id mismatch", problems)
    if ACTION_RECEIPT_VECTORS.is_file():
        vectors = load(ACTION_RECEIPT_VECTORS)
        require(vectors.get("status") == "ACTIVE_STAGE4C_CONTRACT", "action receipt vectors not active Stage 4C contract", problems)
    if ACTION_RECEIPT_VALIDATOR.is_file():
        proc = subprocess.run(
            [sys.executable, str(ACTION_RECEIPT_VALIDATOR), "--self-test"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
        )
        require(proc.returncode == 0, "action receipt self-test failed: " + (proc.stderr.strip() or proc.stdout.strip()), problems)

    sensor_rows = sensors.get("sensors")
    require(sensors.get("schema_version") == 1, "sensor registry schema_version", problems)
    require(sensors.get("suite_runner") == "scripts/check-all.py", "suite runner mismatch", problems)
    require(isinstance(sensor_rows, list), "sensor registry sensors must be list", problems)
    sensor_rows = sensor_rows if isinstance(sensor_rows, list) else []
    sensor_ids = [row.get("id") for row in sensor_rows if isinstance(row, dict)]
    require(len(sensor_ids) == len(set(sensor_ids)), "duplicate sensor id", problems)
    registered = {row.get("path") for row in sensor_rows if isinstance(row, dict)}
    live = {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "scripts").glob("check-*.py")
        if p.name != "check-all.py"
    }
    require(registered == live, f"sensor registry mismatch missing={sorted(live-registered)} extra={sorted(registered-live)}", problems)

    sensor_id_set = {value for value in sensor_ids if isinstance(value, str)}
    for row in sensor_rows:
        if not isinstance(row, dict):
            problems.append("sensor row must be object")
            continue
        sid = row.get("id")
        path = row.get("path")
        require(isinstance(path, str) and existing_repo_path(path), f"{sid}: sensor path missing", problems)
        require(isinstance(path, str) and sid == Path(path).stem, f"{sid}: id/path mismatch", problems)
        require(isinstance(row.get("owns"), list) and bool(row.get("owns")), f"{sid}: owns required", problems)
        require(isinstance(row.get("triggered_by"), list) and bool(row.get("triggered_by")), f"{sid}: triggered_by required", problems)
        require(isinstance(row.get("depends_on"), list), f"{sid}: depends_on must be list", problems)
        if isinstance(row.get("depends_on"), list):
            overlap = set(row.get("triggered_by") or []) & set(row.get("depends_on") or [])
            require(not overlap, f"{sid}: triggered_by/depends_on must be semantically separated: {sorted(overlap)}", problems)
            for dep in row.get("depends_on") or []:
                require(
                    dep in sensor_id_set or existing_repo_path(dep),
                    f"{sid}: dependency must be an existing repo path or sensor id: {dep}",
                    problems,
                )
        require(isinstance(row.get("enforces"), list), f"{sid}: enforces must be list", problems)
        for policy_id in row.get("enforces") or []:
            require(policy_id in known_policies, f"{sid}: unknown enforced policy {policy_id}", problems)
        require(row.get("risk") in RISK, f"{sid}: invalid risk", problems)
        timeout = row.get("timeout_seconds")
        require(type(timeout) is int and 1 <= timeout <= 1800, f"{sid}: invalid timeout", problems)
        require(row.get("fallback_scope") in FALLBACK, f"{sid}: invalid fallback_scope", problems)
        require(row.get("mapping_state") in MAPPING, f"{sid}: invalid mapping_state", problems)
        if row.get("mapping_state") == "broad_legacy_baseline":
            require(row.get("triggered_by") == ["**"], f"{sid}: baseline sensor must fail broad", problems)
            require(row.get("owns") == ["**"], f"{sid}: baseline sensor owns must stay broad", problems)
            require(row.get("fallback_scope") == "FULL_SUITE", f"{sid}: baseline sensor must fall back to FULL_SUITE", problems)
        if row.get("mapping_state") == "mapped" and row.get("fallback_scope") != "ALWAYS_ON":
            require(row.get("triggered_by") != ["**"], f"{sid}: mapped sensor cannot keep wildcard-only trigger", problems)
            require(row.get("owns") != ["**"], f"{sid}: mapped sensor cannot keep wildcard-only ownership", problems)

    always_on = [row for row in sensor_rows if isinstance(row, dict) and row.get("fallback_scope") == "ALWAYS_ON"]
    always_on_ids = {row.get("id") for row in always_on}
    expected_always_on = {
        "check-agent-surface-security",
        "check-critical-syntax",
        "check-machine-writers",
        "check-policy-architecture",
    }
    require(always_on_ids == expected_always_on, f"critical ALWAYS_ON set drifted: {sorted(always_on_ids)}", problems)
    require(len(always_on) <= 6, "critical ALWAYS_ON set must remain small", problems)
    for row in always_on:
        sid = row.get("id")
        require(row.get("risk") == "critical", f"{sid}: ALWAYS_ON sensor must be critical", problems)
        require(row.get("mapping_state") == "mapped", f"{sid}: ALWAYS_ON sensor must be mapped", problems)
        require(type(row.get("timeout_seconds")) is int and row.get("timeout_seconds") <= 180, f"{sid}: ALWAYS_ON timeout must stay fast", problems)

    require(selection.get("schema_version") == 1, "sensor selection schema_version", problems)
    selector_mode = selection.get("mode")
    require(selector_mode in {"shadow", "enforced"}, "sensor selector mode invalid", problems)
    require(selection.get("registry") == "packages/velvetos/policy/sensor-registry.json", "selector registry binding mismatch", problems)
    require(selection.get("unknown_path_behavior") == "FULL_SUITE", "unknown selector paths must fail broad", problems)
    require(selection.get("broad_change_behavior") == "FULL_SUITE", "broad selector changes must run full suite", problems)
    broad_patterns = selection.get("broad_change_patterns")
    require(isinstance(broad_patterns, list) and bool(broad_patterns), "selector broad_change_patterns required", problems)
    required_broad = {
        ".github/workflows/check-all.yml",
        "packages/velvetos/policy/sensor-registry.json",
        "packages/velvetos/policy/sensor-selection.json",
        "packages/velvetos/policy/schema/**",
        "scripts/check-all.py",
        "scripts/check-policy-architecture.py",
        "scripts/sensor_selector.py",
        "scripts/compare-sensor-shadow.py",
        "scripts/stage3_preflight.py",
    }
    require(required_broad <= set(broad_patterns or []), "selector broad-change safety set incomplete", problems)
    shadow_exit = selection.get("shadow_exit") or {}
    require(type(shadow_exit.get("minimum_pull_requests")) is int and shadow_exit.get("minimum_pull_requests") >= 1, "shadow minimum_pull_requests invalid", problems)
    require(type(shadow_exit.get("minimum_observation_days")) is int and shadow_exit.get("minimum_observation_days") >= 1, "shadow minimum_observation_days invalid", problems)
    require(shadow_exit.get("maximum_critical_misses") == 0, "shadow critical miss budget must be zero", problems)
    require(shadow_exit.get("rollback_mode") == "FULL_SUITE_REQUIRED", "shadow rollback must be FULL_SUITE_REQUIRED", problems)

    stage3 = selection.get("stage3_preparation") or {}
    require(stage3.get("activation_requires_shadow_exit_eligible") is True, "Stage 3 activation must require eligible shadow exit", problems)
    require(stage3.get("pull_request_execution") == "SELECTED_SUITE", "Stage 3 PR target must be SELECTED_SUITE", problems)
    require(stage3.get("main_push_execution") == "FULL_SUITE", "Stage 3 main push target must remain FULL_SUITE", problems)
    require(stage3.get("selected_suite_runner") == "scripts/check-all.py --selection sensor-selection.json", "Stage 3 selected suite runner drift", problems)
    require(stage3.get("critical_always_on_preserved") is True, "Stage 3 must preserve critical ALWAYS_ON sensors", problems)
    require(stage3.get("unknown_or_broad_change_behavior") == "FULL_SUITE", "Stage 3 must fail broad on unknown/broad changes", problems)
    require(stage3.get("rollback_mode") == "FULL_SUITE_REQUIRED", "Stage 3 rollback must restore full suite", problems)
    require(stage3.get("required_status_check") == "check-all", "Stage 3 required status check drift", problems)
    require(type(stage3.get("branch_ruleset_id")) is int and stage3.get("branch_ruleset_id") > 0, "Stage 3 branch ruleset id invalid", problems)
    require(stage3.get("branch_ruleset_target_enforcement") == "active", "Stage 3 ruleset target must be active", problems)
    duration_override = stage3.get("activation_duration_override") or {}
    require(duration_override.get("type") == "OWNER_DURATION_ONLY", "Stage 3 duration override type drift", problems)
    require(duration_override.get("criterion") == "minimum_observation_days", "Stage 3 duration override criterion drift", problems)
    require(duration_override.get("authorized_by") == "owner", "Stage 3 duration override must be owner-authorized", problems)
    require(duration_override.get("requires_only_blocker") == "MINIMUM_OBSERVATION_DAYS_NOT_MET", "Stage 3 duration override scope drift", problems)
    duplicate_targets = set(stage3.get("duplicate_direct_invocations_to_remove") or [])
    require(duplicate_targets == {"scripts/check-policy-architecture.py", "scripts/check-commission-isolation.py"}, "Stage 3 duplicate-removal targets drift", problems)

    receipt_rel = str(stage3.get("activation_receipt") or "")
    receipt_path = ROOT / receipt_rel
    workflow_path = ROOT / ".github" / "workflows" / "check-all.yml"
    workflow_text = workflow_path.read_text(encoding="utf-8") if workflow_path.is_file() else ""
    if selector_mode == "shadow":
        require(stage3.get("state") == "PREPARED_NOT_ACTIVE", "Stage 3 must remain PREPARED_NOT_ACTIVE during shadow", problems)
        require(not receipt_path.is_file(), "Stage 3 activation receipt must not exist before cutover", problems)
        require("--selection sensor-selection.json" not in workflow_text, "Stage 3 selected-suite enforcement activated before gate", problems)
    elif selector_mode == "enforced":
        require(stage3.get("state") == "ACTIVE", "Stage 3 enforced mode requires ACTIVE preparation state", problems)
        require(receipt_path.is_file(), "Stage 3 enforced mode requires activation receipt", problems)
        if receipt_path.is_file():
            receipt = load(receipt_path)
            require(receipt.get("schema") == "velvetos.stage3-activation-receipt.v1", "Stage 3 activation receipt schema mismatch", problems)
            activation_gate = receipt.get("activation_gate")
            require(receipt.get("stage") == 3 and activation_gate in {"PASS", "PASS_WITH_OWNER_DURATION_OVERRIDE"}, "Stage 3 activation receipt gate mismatch", problems)
            require(receipt.get("critical_misses") == 0, "Stage 3 activation receipt contains critical miss", problems)
            require(receipt.get("deterministic_replay_pass") is True, "Stage 3 activation receipt replay failed", problems)
            require(receipt.get("run_history_complete") is True, "Stage 3 activation receipt history incomplete", problems)
            require(receipt.get("rollback_mode") == "FULL_SUITE_REQUIRED", "Stage 3 activation receipt rollback mismatch", problems)
            require(int(receipt.get("observed_pull_requests") or 0) >= int(shadow_exit.get("minimum_pull_requests") or 0), "Stage 3 activation receipt PR count below gate", problems)
            if activation_gate == "PASS":
                require(float(receipt.get("observation_days") or 0) >= float(shadow_exit.get("minimum_observation_days") or 0), "Stage 3 activation receipt days below gate", problems)
            else:
                receipt_override = receipt.get("owner_duration_override") or {}
                require(receipt_override.get("type") == "OWNER_DURATION_ONLY", "Stage 3 owner duration override missing from receipt", problems)
                require(receipt_override.get("original_blocker") == "MINIMUM_OBSERVATION_DAYS_NOT_MET", "Stage 3 owner duration override blocker mismatch", problems)
                require(receipt_override.get("authorized_by") == "owner", "Stage 3 owner duration override authorization mismatch", problems)
                require(float(receipt.get("observation_days") or 0) >= float(receipt_override.get("minimum_observed_days") or 0), "Stage 3 owner duration override day floor not met", problems)
                require(int(receipt.get("observed_pull_requests") or 0) >= int(receipt_override.get("minimum_observed_pull_requests") or 0), "Stage 3 owner duration override PR floor not met", problems)
                require(receipt_override.get("authorized_at") == duration_override.get("authorized_at"), "Stage 3 owner duration override receipt/config mismatch", problems)
        require("--selection sensor-selection.json" in workflow_text, "Stage 3 enforced workflow must run selected suite", problems)
        require("Compare sensor selector shadow with full suite" not in workflow_text, "Stage 3 enforced workflow must remove shadow comparison", problems)
        for rel in sorted(duplicate_targets):
            require(f"python3 {rel}" not in workflow_text, f"Stage 3 duplicate direct invocation still present: {rel}", problems)

    for rel in ("scripts/sensor_selector.py", "scripts/compare-sensor-shadow.py", "scripts/stage3_preflight.py", "scripts/check-all.py"):
        require(existing_repo_path(rel), f"selector enforcement component missing: {rel}", problems)
    for shadow_rel in ("scripts/sensor_selector.py", "scripts/compare-sensor-shadow.py", "scripts/collect-sensor-shadow-observations.py"):
        shadow_harness = ROOT / shadow_rel
        if shadow_harness.is_file():
            proc = subprocess.run(
                [sys.executable, str(shadow_harness), "--self-test"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=30,
            )
            require(proc.returncode == 0, "sensor shadow selftest failed " + shadow_rel + ": " + (proc.stderr or proc.stdout).strip()[:500], problems)

    for prep_rel in ("scripts/check-all.py", "scripts/stage3_preflight.py"):
        prep_harness = ROOT / prep_rel
        if prep_harness.is_file():
            proc = subprocess.run(
                [sys.executable, str(prep_harness), "--self-test"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=30,
            )
            require(proc.returncode == 0, "Stage 3 preparation selftest failed " + prep_rel + ": " + (proc.stderr or proc.stdout).strip()[:500], problems)

    for row in rows:
        for item in row.get("enforced_by") or []:
            require(isinstance(item, dict), f"{row.get('policy_id')}: invalid enforcer", problems)
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            require(kind in {"sensor", "runtime", "workflow"}, f"{row.get('policy_id')}: invalid enforcer kind", problems)
            if kind == "sensor":
                require(item.get("id") in sensor_id_set, f"{row.get('policy_id')}: unknown sensor enforcer {item.get('id')}", problems)
            else:
                require(existing_repo_path(item.get("path", "")), f"{row.get('policy_id')}: missing enforcer path {item.get('path')}", problems)

    entries = artifacts.get("entries")
    require(artifacts.get("schema_version") == 1, "artifact registry schema_version", problems)
    require(isinstance(entries, list), "artifact retention entries must be list", problems)
    entries = entries if isinstance(entries, list) else []
    artifact_ids = [row.get("artifact_class_id") for row in entries if isinstance(row, dict)]
    require(len(artifact_ids) == len(set(artifact_ids)), "duplicate artifact_class_id", problems)

    stage7d_retention = artifacts.get("stage7d") or {}
    stage7d_active = stage7d_retention.get("status") == "ACTIVE_STAGE7D"
    if stage7d_active:
        require(stage7d_retention.get("migration_mode") == "COPY_FIRST",
                "Stage 7D artifact migration must remain COPY_FIRST", problems)
        require(stage7d_retention.get("consumer_scan_required_before_tree_removal") is True,
                "Stage 7D removal requires consumer scan", problems)
        require(stage7d_retention.get("external_irreversible_delete_authority_added") is False,
                "Stage 7D must not add external irreversible delete authority", problems)

    for row in entries:
        if not isinstance(row, dict):
            problems.append("artifact row must be object")
            continue
        aid = row.get("artifact_class_id")
        require(isinstance(row.get("match"), list) and bool(row.get("match")), f"{aid}: match required", problems)
        require(bool(row.get("classification")), f"{aid}: classification required", problems)
        require(bool(row.get("current_storage")), f"{aid}: current_storage required", problems)
        require(bool(row.get("target_storage")), f"{aid}: target_storage required", problems)
        require(bool(row.get("retention_class")), f"{aid}: retention_class required", problems)
        if stage7d_active:
            require("CLASSIFY_IN_STAGE_7" not in str(row.get("retention_class")),
                    f"{aid}: Stage 7D retention class must be concrete", problems)
            if row.get("deletion_authorized") is True:
                require(aid == "office-generated-output",
                        f"{aid}: only scoped generated office copies may be tree-removed in Stage 7D", problems)
                require(isinstance(row.get("deletion_scope"), list) and bool(row.get("deletion_scope")),
                        f"{aid}: Stage 7D deletion scope required", problems)
                require(bool(row.get("copy_first_receipt")),
                        f"{aid}: Stage 7D copy-first receipt required", problems)
        else:
            require(row.get("deletion_authorized") is False, f"{aid}: pre-Stage7D cannot authorize deletion", problems)
        refs = row.get("policy_refs")
        require(isinstance(refs, list), f"{aid}: policy_refs must be list", problems)
        for policy_id in refs or []:
            require(policy_id in known_policies, f"{aid}: unknown policy ref {policy_id}", problems)

    expected_schemas = {
        "policy-registry.schema.json",
        "sensor-registry.schema.json",
        "sensor-selection.schema.json",
        "artifact-retention.schema.json",
        "state-evidence-model.schema.json",
        "instagram-publish.schema.json",
        "instagram-publish-context.schema.json",
        "content-ready.schema.json",
    }
    actual_schemas = {p.name for p in SCHEMAS.glob("*.json")}
    require(expected_schemas <= actual_schemas, f"missing schemas {sorted(expected_schemas-actual_schemas)}", problems)
    for name in expected_schemas:
        path = SCHEMAS / name
        if path.exists():
            schema = load(path)
            require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{name}: draft mismatch", problems)

    instagram_policy_path = POLICY_DIR / "instagram.publish.json"
    require(instagram_policy_path.is_file(), "instagram.publish machine policy missing", problems)
    if instagram_policy_path.is_file():
        instagram_policy = load(instagram_policy_path)
        require(instagram_policy.get("policy_id") == "instagram.publish", "instagram.publish policy_id mismatch", problems)
        require(instagram_policy.get("version") == 2, "instagram.publish Stage 4D version mismatch", problems)
        require(instagram_policy.get("required_gates") == ["content_ready"], "instagram.publish must consume one CONTENT_READY gate", problems)
        content_ready_cfg = instagram_policy.get("content_ready") or {}
        require(content_ready_cfg.get("schema_version") == "velvet.content_ready.v1", "instagram.publish CONTENT_READY schema binding mismatch", problems)
        require(content_ready_cfg.get("required_evidence") == ["product_truth", "brand", "copy", "visual_qa", "rights_privacy", "render_transport"], "instagram.publish CONTENT_READY evidence set drift", problems)
        require((content_ready_cfg.get("legacy_gate_compatibility") or {}).get("jobs_created_before") == "2026-10-03T15:58:09.874Z", "CONTENT_READY compatibility cutoff drift", problems)
        require(instagram_policy.get("status") == "active", "instagram.publish machine policy must be active after runtime cutover", problems)
        require(instagram_policy.get("decision_values") == ["ALLOW", "DENY", "REQUIRE_OWNER_APPROVAL"], "instagram.publish decision values mismatch", problems)
        row = next((x for x in rows if x.get("policy_id") == "instagram.publish"), None)
        require(row is not None and row.get("status") == "active", "instagram.publish registry status must be active after runtime cutover", problems)
        require(row is not None and "packages/velvetos/policy/instagram.publish.json" in row.get("machine_policy_locations", []), "instagram.publish registry binding missing", problems)
        for rel_path in (
            "packages/velvetos/policy/instagram-publish-evaluator.mjs",
            "packages/velvetos/policy/instagram-publish-test-vectors.json",
            "packages/velvetos/policy/test-instagram-publish-policy.mjs",
            "scripts/vf_instagram_publish_policy.mjs",
            "packages/vfigos/cloudflare-publisher/src/policy_gate.js",
            "packages/vfigos/cloudflare-publisher/test-policy-gate.mjs",
            "packages/vfigos/cloudflare-publisher/test-format-contracts.mjs",
            "packages/vfigos/routine_publish.py",
            "packages/velvetos/policy/schema/content-ready.schema.json",
            "packages/velvetos/policy/content-ready-test-vectors.json",
            "scripts/vf_content_ready.py",
        ):
            require(existing_repo_path(rel_path), f"instagram.publish component missing: {rel_path}", problems)
        worker_path = ROOT / "packages" / "vfigos" / "cloudflare-publisher" / "src" / "index.js"
        wrangler_path = ROOT / "packages" / "vfigos" / "cloudflare-publisher" / "wrangler.toml"
        instance_path = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
        if worker_path.is_file():
            worker = worker_path.read_text(encoding="utf-8")
            start = worker.find("async function handleOne")
            gate_at = worker.find("const policyDecision=await evaluateInstagramPublishJob(j,env);", start)
            publish_at = worker.find("const live=await publishJob(env,j);", start)
            require(start >= 0 and gate_at > start and publish_at > gate_at, "instagram.publish runtime gate must precede publishJob", problems)
            require('a.kind!=="policy_authorization_v1"' in worker, "new Cloudflare jobs must require policy_authorization_v1", problems)
        if wrangler_path.is_file() and instance_path.is_file():
            wrangler = wrangler_path.read_text(encoding="utf-8")
            instance = load(instance_path)
            standing = bool((((instance.get("creativeAutonomy") or {}).get("publish") or {}).get("standingAuthorization")))
            require(('STANDING_AUTHORIZATION = "true"' in wrangler) == standing, "Cloudflare standing authorization projection drift", problems)
        cutover_path = REPORTS / "stage1-instagram-publish-cutover.json"
        require(cutover_path.is_file(), "instagram.publish production cutover evidence missing", problems)
        if cutover_path.is_file():
            cutover = load(cutover_path)
            require(cutover.get("policy_id") == "instagram.publish" and cutover.get("policy_version") == 1, "instagram.publish cutover policy binding mismatch", problems)
            require(cutover.get("cutover_result") == "PASS", "instagram.publish cutover is not PASS", problems)
            require(cutover.get("negative_control", {}).get("persistent_job_created") is False, "instagram.publish negative control persisted a job", problems)
            require(cutover.get("postdeploy", {}).get("scheduled_count") == 0, "unexpected scheduled jobs recorded at Stage 1 cutover", problems)
        node_tests = [
            ROOT / "packages" / "velvetos" / "policy" / "test-instagram-publish-policy.mjs",
            ROOT / "packages" / "vfigos" / "cloudflare-publisher" / "test-policy-gate.mjs",
            ROOT / "packages" / "vfigos" / "cloudflare-publisher" / "test-format-contracts.mjs",
        ]
        for test in node_tests:
            if test.is_file():
                proc = subprocess.run(["node", str(test)], cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=30)
                require(proc.returncode == 0, f"Node policy test failed {test.relative_to(ROOT)}: " + (proc.stderr or proc.stdout).strip()[:500], problems)
        for content_test, label in ((ROOT / "scripts" / "vf_content_ready.py", "CONTENT_READY"), (ROOT / "packages" / "vfigos" / "routine_publish.py", "routine Instagram happy path")):
            if content_test.is_file():
                env = dict(os.environ)
                env["PYTHONPATH"] = str(ROOT / "packages") + os.pathsep + str(ROOT / "scripts")
                proc = subprocess.run([sys.executable, str(content_test), "--self-test"], cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=30, env=env)
                require(proc.returncode == 0, f"{label} self-test failed: " + (proc.stderr or proc.stdout).strip()[:500], problems)
        policy_gate_path = ROOT / "packages" / "vfigos" / "cloudflare-publisher" / "src" / "policy_gate.js"
        if policy_gate_path.is_file():
            gate_src = policy_gate_path.read_text(encoding="utf-8")
            require("content_ready:" in gate_src, "Cloudflare policy context must project CONTENT_READY", problems)
        stage4d_path = REPORTS / "stage4d-instagram-happy-path-implementation.json"
        require(stage4d_path.is_file(), "Stage 4D implementation report missing", problems)
        if stage4d_path.is_file():
            stage4d = load(stage4d_path)
            require(stage4d.get("schema") == "velvetos.stage4d-instagram-happy-path.implementation.v1", "Stage 4D report schema mismatch", problems)
            require(stage4d.get("prepared_against_main_sha") == "44aef61e7280f3122d6df043b10ee4ad02e2fcb3", "Stage 4D base SHA drift", problems)
            require(stage4d.get("repository_acceptance") == "PASS", "Stage 4D repository acceptance is not PASS", problems)
            require(stage4d.get("policy_version") == 2, "Stage 4D report policy version mismatch", problems)
            happy = stage4d.get("routine_happy_path") or {}
            require(happy.get("formats") == ["image", "carousel", "reel", "story"], "Stage 4D routine format coverage drift", problems)
            require(happy.get("per_asset_owner_approval") is False and happy.get("policy_decisions_per_publish_attempt") == 1,
                    "Stage 4D routine owner/policy decision contract drift", problems)
            failure = stage4d.get("failure_routing") or {}
            require(failure.get("quality_failure") == "TARGETED_REPAIR" and failure.get("transport_failure") == "RETRY_INTERNAL"
                    and failure.get("owner_prompt_on_quality_failure") is False,
                    "Stage 4D internal repair/retry contract drift", problems)
            direct = stage4d.get("immediate_direct_mutation") or {}
            require(direct.get("signed_delivery_approval_preserved") is True
                    and direct.get("receipt_schema") == "velvet.delivery_approval.v1"
                    and direct.get("standing_routine_scheduler_does_not_mint_direct_receipt") is True,
                    "Stage 4D direct mutation boundary drift", problems)
            cutover = stage4d.get("production_cutover") or {}
            require(cutover.get("status") in {"PENDING_AFTER_MERGE", "PASS"}, "Stage 4D cutover status invalid", problems)
            if cutover.get("status") == "PASS":
                cutover_receipt_rel = "packages/velvetos/policy/reports/stage4d-instagram-happy-path-cutover.json"
                require(cutover.get("receipt") == cutover_receipt_rel,
                        "Stage 4D live cutover receipt binding mismatch", problems)
                cutover_receipt_path = ROOT / cutover_receipt_rel
                require(cutover_receipt_path.is_file(), "Stage 4D live cutover receipt missing", problems)
                cutover_receipt = load(cutover_receipt_path) if cutover_receipt_path.is_file() else {}
                require(cutover_receipt.get("schema") == "velvetos.stage4d-instagram-happy-path.cutover.v1"
                        and cutover_receipt.get("stage") == "4D"
                        and cutover_receipt.get("policy_id") == "instagram.publish"
                        and cutover_receipt.get("cutover_status") == "PASS",
                        "Stage 4D live cutover receipt identity/status mismatch", problems)
                receipt_deployment = cutover_receipt.get("deployment") or {}
                require(receipt_deployment.get("deployed_main_sha") == cutover.get("deployed_main_sha")
                        and receipt_deployment.get("live_worker_version_id") == cutover.get("live_worker_version_id")
                        and receipt_deployment.get("worker_version_created_at") == cutover.get("worker_version_created_at"),
                        "Stage 4D live cutover report/receipt deployment mismatch", problems)
                require(cutover_receipt.get("health_readback") == cutover.get("health_readback")
                        and cutover_receipt.get("negative_control") == cutover.get("negative_control")
                        and cutover_receipt.get("compatibility") == cutover.get("compatibility"),
                        "Stage 4D live cutover report/receipt evidence mismatch", problems)
                require(cutover.get("deployed_main_sha") == "fdc4a3cc1d46b43870e6c69ddcf36fc378a406e7",
                        "Stage 4D live cutover deployed main SHA mismatch", problems)
                require(isinstance(cutover.get("live_worker_version_id"), str) and bool(cutover.get("live_worker_version_id")),
                        "Stage 4D live cutover missing Worker version", problems)
                require(isinstance(cutover.get("worker_version_created_at"), str) and bool(cutover.get("worker_version_created_at")),
                        "Stage 4D live cutover missing Worker version timestamp", problems)
                health = cutover.get("health_readback") or {}
                require(health.get("ok") is True and health.get("policy_id") == "instagram.publish" and health.get("policy_version") == 2,
                        "Stage 4D live cutover health policy readback mismatch", problems)
                require(health.get("content_ready") == "velvet.content_ready.v1"
                        and health.get("formats") == ["image", "carousel", "reel", "story"],
                        "Stage 4D live cutover CONTENT_READY/format readback mismatch", problems)
                require(health.get("runtime_ok") is True
                        and isinstance(health.get("runtime_heartbeat_age_seconds"), int)
                        and 0 <= health.get("runtime_heartbeat_age_seconds") <= 180,
                        "Stage 4D live cutover runtime heartbeat unhealthy", problems)
                require(isinstance(health.get("published_verified_count"), int) and health.get("published_verified_count") >= 1
                        and health.get("scheduled_or_retry_count") == 0,
                        "Stage 4D live cutover job-state readback mismatch", problems)
                require(health.get("meta_ok") is True and health.get("meta_username") == "velvets_cloud",
                        "Stage 4D live cutover Meta readback mismatch", problems)
                require(health.get("instagram_read_smoke_run_id") == 37136222049
                        and health.get("instagram_read_smoke_head_sha") == "fdc4a3cc1d46b43870e6c69ddcf36fc378a406e7"
                        and health.get("instagram_read_smoke_live_executed") is True,
                        "Stage 4D live Instagram read smoke evidence mismatch", problems)
                smoke_checks = health.get("instagram_read_smoke_checks") or {}
                require(smoke_checks.get("get_profile") is True and smoke_checks.get("list_media") is True
                        and smoke_checks.get("live_username") == "velvets_cloud",
                        "Stage 4D live Instagram read smoke checks incomplete", problems)
                negative = cutover.get("negative_control") or {}
                require(negative.get("observed_http") == 403
                        and negative.get("observed_error") == "policy_not_allowed"
                        and negative.get("policy_decision") == "DENY"
                        and negative.get("reason_codes") == ["CONTENT_READY_REQUIRED"],
                        "Stage 4D live negative control policy result mismatch", problems)
                require(negative.get("readback_http") == 404 and negative.get("persistent_job_created") is False,
                        "Stage 4D live negative control persisted unexpectedly", problems)

    require(STAGE4_ACCEPTANCE.is_file(), "Stage 4 acceptance receipt missing", problems)
    require(STAGE4_ACCEPTANCE_GENERATOR.is_file(), "Stage 4 acceptance generator missing", problems)
    if STAGE4_ACCEPTANCE.is_file():
        stage4 = load(STAGE4_ACCEPTANCE)
        require(stage4.get("schema") == "velvetos.stage4-acceptance.v1" and stage4.get("stage") == "4",
                "Stage 4 acceptance schema/stage mismatch", problems)
        require(stage4.get("prepared_against_main_sha") == "5a5ebcb655856e758aed2b80ffcb0b683d1b18b3",
                "Stage 4 acceptance main SHA drift", problems)
        require(stage4.get("behavior_change") is False and stage4.get("stage4_gate") == "PASS",
                "Stage 4 gate must remain observation-only PASS", problems)
        criteria = stage4.get("acceptance_criteria") or {}
        expected_criteria = {
            "project_request_routing",
            "single_authority_per_external_effect",
            "routine_instagram_zero_owner_prompts_one_policy_decision_verified_publish",
            "routine_gmail_not_blocked_by_approval_ceremony",
            "unrelated_stale_runtime_evidence_does_not_block_code",
            "bounded_cost_reuses_owner_approval_without_unbounded_spend",
            "critical_guardrail_policy_coverage_preserved",
            "main_full_sensor_suite_116_of_116",
        }
        require(set(criteria) == expected_criteria and all(criteria.get(key) is True for key in expected_criteria),
                "Stage 4 acceptance criteria drift or fail", problems)
        stage5_entry = stage4.get("stage5_entry") or {}
        require(stage5_entry.get("allowed") is True
                and stage5_entry.get("next_stage") == "Stage 5 — Context, Agents, Skills and Capability Locality",
                "Stage 4 gate does not authorize Stage 5 entry", problems)
        main_suite = stage4.get("main_full_suite") or {}
        require(main_suite.get("head_sha") == "5a5ebcb655856e758aed2b80ffcb0b683d1b18b3"
                and main_suite.get("workflow_run_id") == 37142530441
                and main_suite.get("job_id") == 111259753445
                and main_suite.get("conclusion") == "SUCCESS"
                and main_suite.get("mode") == "full"
                and main_suite.get("registered_sensors") == 116
                and main_suite.get("passed_sensors") == 116
                and main_suite.get("log_markers") == ["SENSORS 116 mode=full", "OK suite passed=116"],
                "Stage 4 main full-suite evidence drift", problems)
        routine = stage4.get("routine_operations") or {}
        instagram_accept = routine.get("instagram") or {}
        gmail_accept = routine.get("gmail") or {}
        runtime_accept = routine.get("runtime_receipts") or {}
        cost_accept = routine.get("cost") or {}
        require(instagram_accept.get("owner_prompts") == 0
                and instagram_accept.get("policy_decisions_per_publish_attempt") == 1
                and instagram_accept.get("production_cutover") == "PASS"
                and instagram_accept.get("provider_receipt_required") is True
                and instagram_accept.get("live_readback_required") is True,
                "Stage 4 Instagram acceptance drift", problems)
        require(gmail_accept.get("owner_prompts") == 0
                and gmail_accept.get("routine_vectors_all_allow") is True
                and gmail_accept.get("transport_is_authorization") is False
                and gmail_accept.get("commitment_still_owner_gated") is True,
                "Stage 4 Gmail acceptance drift", problems)
        require(runtime_accept.get("unrelated_stale_runtime_blocks_code") is False
                and runtime_accept.get("real_dependency_still_fail_closed") is True,
                "Stage 4 runtime-scope acceptance drift", problems)
        require(cost_accept.get("active_envelopes") == 0
                and cost_accept.get("spend_authorized_by_stage4g_implementation") is False
                and cost_accept.get("matching_call_owner_prompts") == 0
                and cost_accept.get("full_preflight_per_matching_call") is False
                and cost_accept.get("exact_action_receipt_required") is True,
                "Stage 4 cost-envelope acceptance drift", problems)
        safety = stage4.get("safety_invariants") or {}
        require(bool(safety) and all(value is True for value in safety.values()),
                "Stage 4 safety invariant coverage drift", problems)
        for name, source in (stage4.get("source_receipts") or {}).items():
            require(isinstance(source, dict), f"Stage 4 source receipt {name} invalid", problems)
            rel = source.get("path") if isinstance(source, dict) else None
            source_path = ROOT / rel if isinstance(rel, str) else None
            require(source_path is not None and source_path.is_file(), f"Stage 4 source receipt missing: {name}", problems)
            if source_path is not None and source_path.is_file():
                observed_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
                require(source.get("sha256") == observed_hash, f"Stage 4 source receipt hash drift: {name}", problems)
        if STAGE4_ACCEPTANCE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated = Path(td) / "stage4-acceptance.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE4_ACCEPTANCE_GENERATOR),
                        "--prepared-against", stage4["prepared_against_main_sha"],
                        "--captured-at", stage4["captured_at"],
                        "--main-run-id", str(main_suite["workflow_run_id"]),
                        "--main-job-id", str(main_suite["job_id"]),
                        "--main-run-url", str(main_suite["run_url"]),
                        "--output", str(regenerated),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0, "Stage 4 acceptance regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()), problems)
                if proc.returncode == 0 and regenerated.is_file():
                    require(regenerated.read_bytes() == STAGE4_ACCEPTANCE.read_bytes(),
                            "Stage 4 acceptance receipt is not reproducible", problems)

    require(STAGE5_ACCEPTANCE.is_file(), "Stage 5 acceptance receipt missing", problems)
    require(STAGE5_ACCEPTANCE_GENERATOR.is_file(), "Stage 5 acceptance generator missing", problems)
    if STAGE5_ACCEPTANCE.is_file():
        stage5 = load(STAGE5_ACCEPTANCE)
        require(stage5.get("schema") == "velvetos.stage5-acceptance.v1" and stage5.get("stage") == "5",
                "Stage 5 acceptance schema/stage mismatch", problems)
        require(stage5.get("prepared_against_main_sha") == "67bd5dc1bedfb98b850e4b5b09090dcd51598e48",
                "Stage 5 acceptance main SHA drift", problems)
        require(stage5.get("behavior_change") is False and stage5.get("stage5_gate") == "PASS",
                "Stage 5 gate must remain observation-only PASS", problems)
        criteria5 = stage5.get("acceptance_criteria") or {}
        expected_criteria5 = {
            "core_system_context_is_local_and_business_clean",
            "known_routine_loads_minimum_domain_instructions",
            "single_existing_harness_no_second_orchestrator",
            "workspace_specialists_are_routed_only_not_preloaded",
            "authorization_semantics_unchanged",
            "no_context_warehouse_regression",
            "main_full_sensor_suite_116_of_116",
        }
        require(set(criteria5) == expected_criteria5 and all(criteria5.get(key) is True for key in expected_criteria5),
                "Stage 5 acceptance criteria drift or fail", problems)
        stage6_entry = stage5.get("stage6_entry") or {}
        require(stage6_entry.get("allowed") is True
                and stage6_entry.get("next_stage") == "Stage 6 — Visible Text, Creative and DCC Simplification",
                "Stage 5 gate does not authorize Stage 6 entry", problems)
        main5 = stage5.get("main_full_suite") or {}
        require(main5.get("head_sha") == "67bd5dc1bedfb98b850e4b5b09090dcd51598e48"
                and main5.get("workflow_run_id") == 37175062910
                and main5.get("job_id") == 111355869001
                and main5.get("conclusion") == "SUCCESS"
                and main5.get("mode") == "full"
                and main5.get("registered_sensors") == 116
                and main5.get("passed_sensors") == 116
                and main5.get("log_markers") == ["SENSORS 116 mode=full", "OK suite passed=116"],
                "Stage 5 main full-suite evidence drift", problems)
        context5 = stage5.get("context_locality") or {}
        require(context5.get("root_lines") == 56
                and context5.get("root_words") == 453
                and context5.get("root_domain_leakage_total") == 0
                and context5.get("domain_count") == 10
                and context5.get("warehouse_default") == "off"
                and context5.get("system_engineering_context_clean") is True,
                "Stage 5 context-locality acceptance drift", problems)
        harness5 = stage5.get("harness") or {}
        require(harness5.get("canonical_loop") == "packages/vfharness/LOOP.md"
                and harness5.get("secondary_restating_count") == 0
                and harness5.get("second_orchestrator") == "FORBIDDEN"
                and harness5.get("cross_tool_handoff") == ["office/control/HANDOFF.json", "packages/vfmem/HANDOFF.md"],
                "Stage 5 harness acceptance drift", problems)
        workspace5 = stage5.get("workspace_distribution") or {}
        require(workspace5.get("repository") == "nocturney/velvetos-workspace-distribution"
                and workspace5.get("merge_sha") == "4fa715dc78275b87a942658b26b74608932d8d50"
                and workspace5.get("plugin_version") == "1.6.0"
                and workspace5.get("desired_skill_count") == 35
                and workspace5.get("router") == "creative-craft"
                and workspace5.get("specialist_count") == 8
                and workspace5.get("specialist_activation") == "ROUTED_ONLY"
                and workspace5.get("warehouse_preload") is False
                and workspace5.get("authorization_effect") == "NONE",
                "Stage 5 workspace-distribution acceptance drift", problems)
        expected_sources5 = {"stage5a", "stage5b", "stage5c"}
        sources5 = stage5.get("source_receipts") or {}
        require(set(sources5) == expected_sources5, "Stage 5 source receipt set drift", problems)
        for name, source in sources5.items():
            require(isinstance(source, dict), f"Stage 5 source receipt {name} invalid", problems)
            rel = source.get("path") if isinstance(source, dict) else None
            source_path = ROOT / rel if isinstance(rel, str) else None
            require(source_path is not None and source_path.is_file(), f"Stage 5 source receipt missing: {name}", problems)
            if source_path is not None and source_path.is_file():
                observed_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
                require(source.get("sha256") == observed_hash, f"Stage 5 source receipt hash drift: {name}", problems)
        if STAGE5_ACCEPTANCE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated5 = Path(td) / "stage5-acceptance.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE5_ACCEPTANCE_GENERATOR),
                        "--prepared-against", stage5["prepared_against_main_sha"],
                        "--captured-at", stage5["captured_at"],
                        "--main-run-id", str(main5["workflow_run_id"]),
                        "--main-job-id", str(main5["job_id"]),
                        "--main-run-url", str(main5["run_url"]),
                        "--output", str(regenerated5),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0, "Stage 5 acceptance regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()), problems)
                if proc.returncode == 0 and regenerated5.is_file():
                    require(regenerated5.read_bytes() == STAGE5_ACCEPTANCE.read_bytes(),
                            "Stage 5 acceptance receipt is not reproducible", problems)


    require(STAGE6_ACCEPTANCE.is_file(), "Stage 6 acceptance receipt missing", problems)
    require(STAGE6_ACCEPTANCE_GENERATOR.is_file(), "Stage 6 acceptance generator missing", problems)
    if STAGE6_ACCEPTANCE.is_file():
        stage6 = load(STAGE6_ACCEPTANCE)
        require(stage6.get("schema") == "velvetos.stage6-acceptance.v1" and stage6.get("stage") == "6",
                "Stage 6 acceptance schema/stage mismatch", problems)
        require(stage6.get("prepared_against_main_sha") == "efaaf2f127a17917dcc4a6506fb26548a8bde701",
                "Stage 6 acceptance main SHA drift", problems)
        require(stage6.get("behavior_change") is False and stage6.get("stage6_gate") == "PASS",
                "Stage 6 gate must remain observation-only PASS", problems)
        criteria6 = stage6.get("acceptance_criteria") or {}
        expected_criteria6 = {
            "internal_text_uses_proportional_risk_tiers",
            "public_and_customer_text_remains_evidence_bound",
            "creative_manifest_and_craft_do_not_create_policy_authority",
            "creative_refine_and_routine_aesthetics_remain_internal",
            "dcc_updates_use_latest_compatible_typed_capability_gating",
            "dcc_recovery_baselines_are_not_allowlists_and_unsafe_escape_stays_blocked",
            "documentation_authority_has_no_known_active_contradictions",
            "external_effect_authorization_semantics_remain_unchanged",
            "main_full_sensor_suite_116_of_116",
        }
        require(set(criteria6) == expected_criteria6 and all(criteria6.get(key) is True for key in expected_criteria6),
                "Stage 6 acceptance criteria drift or fail", problems)
        stage7_entry = stage6.get("stage7_entry") or {}
        require(stage7_entry.get("allowed") is True
                and stage7_entry.get("next_stage") == "Stage 7 — State, Evidence, Runtime, Memory, Research, Scheduler and Retention",
                "Stage 6 gate does not authorize Stage 7 entry", problems)
        main6 = stage6.get("main_full_suite") or {}
        require(main6.get("head_sha") == "efaaf2f127a17917dcc4a6506fb26548a8bde701"
                and main6.get("workflow_run_id") == 37188157580
                and main6.get("job_id") == 111394483160
                and main6.get("conclusion") == "SUCCESS"
                and main6.get("mode") == "full"
                and main6.get("registered_sensors") == 116
                and main6.get("passed_sensors") == 116
                and main6.get("log_markers") == ["SENSORS 116 mode=full", "OK suite passed=116"],
                "Stage 6 main full-suite evidence drift", problems)
        visible6 = stage6.get("visible_text") or {}
        require(visible6.get("model") == "RISK_AND_SURFACE_TIERS"
                and visible6.get("draft_internal_required_evidence_count") == 1
                and visible6.get("public_publish_required_evidence_count") == 6
                and visible6.get("public_downgrade_blocked") is True
                and visible6.get("approved_static_requires_exact_sha") is True,
                "Stage 6 visible-text acceptance drift", problems)
        creative6 = stage6.get("creative") or {}
        require(creative6.get("manifest_coordination_only") is True
                and creative6.get("manifest_not_approval_database") is True
                and creative6.get("product_truth_higher") is True
                and creative6.get("quality_system_role") == "authoring_and_quality_system_not_policy_hierarchy"
                and creative6.get("produce_critique_targeted_refine") == "internal"
                and creative6.get("ordinary_aesthetic_choice") == "office"
                and creative6.get("owner_escalation") == "exception-only",
                "Stage 6 creative acceptance drift", problems)
        dcc6 = stage6.get("dcc") or {}
        require(dcc6.get("version_policy") == "latest-compatible"
                and dcc6.get("recovery_baseline_role") == "drift-comparison-and-recovery-evidence-not-allowlist"
                and dcc6.get("exact_version_match_required") is False
                and dcc6.get("available_requires") == "typed_capability_probe_pass"
                and dcc6.get("illustrator_routing_status") == "available"
                and dcc6.get("aftereffects_routing_status") == "available"
                and dcc6.get("aftereffects_version") == "26.5"
                and dcc6.get("aftereffects_transport") == "adobepy-cep-typed-readonly"
                and dcc6.get("unsafe_arbitrary_script_escape_wired") is False
                and dcc6.get("auto_update") is False
                and dcc6.get("auto_rollback") is False
                and dcc6.get("auto_uninstall") is False,
                "Stage 6 DCC acceptance drift", problems)
        docs6 = stage6.get("documentation_authority") or {}
        require(docs6.get("checked_file_count") == 113
                and docs6.get("violations") == []
                and all((docs6.get("canonical_checks") or {}).values()),
                "Stage 6 documentation-authority acceptance drift", problems)
        expected_sources6 = {"stage6a", "stage6b", "stage6c", "stage6d"}
        sources6 = stage6.get("source_receipts") or {}
        require(set(sources6) == expected_sources6, "Stage 6 source receipt set drift", problems)
        for name, source in sources6.items():
            require(isinstance(source, dict), f"Stage 6 source receipt {name} invalid", problems)
            rel = source.get("path") if isinstance(source, dict) else None
            source_path = ROOT / rel if isinstance(rel, str) else None
            require(source_path is not None and source_path.is_file(), f"Stage 6 source receipt missing: {name}", problems)
            if source_path is not None and source_path.is_file():
                observed_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
                require(source.get("sha256") == observed_hash, f"Stage 6 source receipt hash drift: {name}", problems)
        if STAGE6_ACCEPTANCE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated6 = Path(td) / "stage6-acceptance.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE6_ACCEPTANCE_GENERATOR),
                        "--prepared-against", stage6["prepared_against_main_sha"],
                        "--captured-at", stage6["captured_at"],
                        "--main-run-id", str(main6["workflow_run_id"]),
                        "--main-job-id", str(main6["job_id"]),
                        "--main-run-url", str(main6["run_url"]),
                        "--output", str(regenerated6),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0, "Stage 6 acceptance regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()), problems)
                if proc.returncode == 0 and regenerated6.is_file():
                    require(regenerated6.read_bytes() == STAGE6_ACCEPTANCE.read_bytes(),
                            "Stage 6 acceptance receipt is not reproducible", problems)


    require(STATE_EVIDENCE_MODEL.is_file(), "Stage 7A state/evidence model missing", problems)
    require(STAGE7A_ACCEPTANCE.is_file(), "Stage 7A acceptance receipt missing", problems)
    require(STAGE7A_ACCEPTANCE_GENERATOR.is_file(), "Stage 7A acceptance generator missing", problems)
    if STATE_EVIDENCE_MODEL.is_file():
        model7a = load(STATE_EVIDENCE_MODEL)
        require(model7a.get("schema_version") == 1
                and model7a.get("registry_kind") == "velvetos_state_evidence_model"
                and model7a.get("status") == "ACTIVE_STAGE7A",
                "Stage 7A state/evidence registry identity drift", problems)
        categories7a = model7a.get("categories") or []
        category_ids7a = [row.get("id") for row in categories7a if isinstance(row, dict)]
        expected_categories7a = {
            "CANONICAL_STATE", "EVIDENCE_RECEIPT",
            "AUTHORIZATION_DECISION", "AUDIT_HISTORY",
        }
        require(set(category_ids7a) == expected_categories7a and len(category_ids7a) == 4,
                "Stage 7A must define exactly four semantic categories", problems)
        category_by_id7a = {
            row.get("id"): row for row in categories7a
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }
        require(category_by_id7a.get("EVIDENCE_RECEIPT", {}).get("can_authorize_external_effect") is False,
                "Stage 7A evidence may not authorize external effects", problems)
        require(category_by_id7a.get("CANONICAL_STATE", {}).get("can_authorize_external_effect") is False,
                "Stage 7A canonical state may not authorize external effects", problems)
        require(category_by_id7a.get("AUDIT_HISTORY", {}).get("can_authorize_external_effect") is False,
                "Stage 7A audit/history may not authorize external effects", problems)
        require(category_by_id7a.get("AUTHORIZATION_DECISION", {}).get("can_authorize_external_effect") is True,
                "Stage 7A authorization decision must be the sole authorizing category", problems)

        invariants7a = model7a.get("invariants") or {}
        required_invariants7a = {
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
        require(all(invariants7a.get(key) is True for key in required_invariants7a),
                "Stage 7A invariant drift", problems)
        scope7a = model7a.get("scope") or {}
        require(scope7a.get("storage_change") == "NONE_STAGE7A"
                and scope7a.get("migration_change") == "NONE_STAGE7A"
                and scope7a.get("deletion_authorized") is False,
                "Stage 7A must remain classification-only with no storage move/deletion", problems)

        defaults7a = model7a.get("retention_defaults") or []
        default_ids7a = [row.get("artifact_class_id") for row in defaults7a if isinstance(row, dict)]
        require(len(default_ids7a) == len(set(default_ids7a)),
                "Stage 7A duplicate retention semantic mapping", problems)
        require(set(default_ids7a) == set(artifact_ids),
                "Stage 7A must map every artifact-retention class exactly once", problems)
        require(all(isinstance(row, dict) and row.get("category") in expected_categories7a for row in defaults7a),
                "Stage 7A retention mapping references unknown category", problems)

        surfaces7a = model7a.get("surfaces") or []
        surface_ids7a = [row.get("id") for row in surfaces7a if isinstance(row, dict)]
        require(len(surface_ids7a) == len(set(surface_ids7a)), "Stage 7A duplicate surface id", problems)
        required_surfaces7a = {
            "jobs-ledger", "office-followups", "office-dead-letter", "manager-handoff",
            "task-checkpoints", "runtime-health-receipts", "jobs-sync-receipt",
            "research-sources", "exact-action-receipt", "office-decisions-history",
            "media-catalog", "media-intake-current-state", "media-intake-event-history",
            "content-approval-queue", "content-event-history", "feed-audit-evidence",
            "content-calendar", "production-completion", "publication-operational-state",
            "generated-office-output-history",
        }
        require(required_surfaces7a <= set(surface_ids7a),
                "Stage 7A operational surface mapping incomplete", problems)
        for row in surfaces7a:
            if not isinstance(row, dict):
                problems.append("Stage 7A surface row must be object")
                continue
            sid = row.get("id")
            require(row.get("category") in expected_categories7a, f"{sid}: invalid Stage 7A category", problems)
            require(bool(row.get("canonical_owner")), f"{sid}: canonical_owner required", problems)
            require(bool(row.get("authority_scope")), f"{sid}: authority_scope required", problems)
            compatibility7a = row.get("compatibility_paths")
            require(isinstance(compatibility7a, list), f"{sid}: compatibility_paths must be list", problems)
            if isinstance(compatibility7a, list):
                require(all(isinstance(item, dict) and item.get("authoritative") is False for item in compatibility7a),
                        f"{sid}: compatibility path cannot be authoritative", problems)
            if row.get("category") != "AUTHORIZATION_DECISION":
                require(row.get("policy_gate_eligible") is False,
                        f"{sid}: only AUTHORIZATION_DECISION may be policy-gate eligible", problems)
        auth_surfaces7a = [row for row in surfaces7a
                           if isinstance(row, dict) and row.get("category") == "AUTHORIZATION_DECISION"]
        require(len(auth_surfaces7a) == 1 and auth_surfaces7a[0].get("id") == "exact-action-receipt",
                "Stage 7A exact-action receipt must be the sole authorization-decision surface", problems)
        if auth_surfaces7a:
            require((auth_surfaces7a[0].get("locator") or {}).get("values") == ["velvetos.action-receipt.v1"],
                    "Stage 7A authorization surface lost action-receipt schema binding", problems)

        handoff7a = next((row for row in surfaces7a if isinstance(row, dict) and row.get("id") == "manager-handoff"), {})
        require(handoff7a.get("projection_only") is True and handoff7a.get("policy_gate_eligible") is False,
                "Stage 7A handoff must remain continuation context, not policy authority", problems)
        work_ledger7a = model7a.get("work_ledger") or {}
        require(work_ledger7a.get("status") == "INDEX_ONLY_NOT_IMPLEMENTED_STAGE7A"
                and work_ledger7a.get("destination_stage") == "7D"
                and work_ledger7a.get("references_only") is True
                and work_ledger7a.get("policy_authority") is False
                and work_ledger7a.get("external_effect_authority") is False
                and work_ledger7a.get("implementation_allowed_before_stage7d") is False,
                "Stage 7A Work Ledger must remain refs-only and unimplemented until 7D", problems)

    if STAGE7A_ACCEPTANCE.is_file():
        stage7a = load(STAGE7A_ACCEPTANCE)
        require(stage7a.get("schema") == "velvetos.stage7a-state-evidence-model.v1"
                and stage7a.get("stage") == "7A"
                and stage7a.get("behavior_change") is False
                and stage7a.get("prepared_against_main_sha") == "ae8c75745f0d89677078d9834ea969f6da866195"
                and stage7a.get("repository_acceptance") == "PASS",
                "Stage 7A acceptance metadata drift", problems)
        criteria7a = stage7a.get("acceptance") or {}
        expected_criteria7a = {
            "exactly_four_semantic_categories",
            "all_retention_registry_artifact_classes_are_mapped",
            "canonical_owner_and_authority_scope_are_explicit_per_operational_surface",
            "compatibility_paths_are_non_authoritative",
            "evidence_is_distinct_from_authorization_decision",
            "audit_history_cannot_overwrite_current_state",
            "handoff_is_continuation_context_not_cross_domain_authority",
            "work_ledger_is_refs_only_and_not_a_second_store",
            "external_effect_policy_registry_is_unchanged",
            "no_storage_migration_or_deletion_is_authorized",
        }
        require(set(criteria7a) == expected_criteria7a
                and all(criteria7a.get(key) is True for key in expected_criteria7a),
                "Stage 7A acceptance criteria drift or fail", problems)
        require(stage7a.get("next_stage") == "Stage 7B — Memory/Learning lifecycle",
                "Stage 7A next-stage handoff drift", problems)
        model_meta7a = stage7a.get("model") or {}
        if STATE_EVIDENCE_MODEL.is_file():
            require(model_meta7a.get("sha256") == hashlib.sha256(STATE_EVIDENCE_MODEL.read_bytes()).hexdigest(),
                    "Stage 7A model hash drift", problems)
        require(model_meta7a.get("retention_classes_mapped") == len(artifact_ids)
                and model_meta7a.get("retention_class_count") == len(artifact_ids),
                "Stage 7A retention mapping count drift", problems)
        baseline7a = stage7a.get("authority_baseline") or {}
        require(baseline7a.get("unchanged_from_prepared_against") is True
                and baseline7a.get("single_authority_per_effect") is True,
                "Stage 7A external-effect authority baseline drift", problems)
        if STAGE7A_ACCEPTANCE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated7a = Path(td) / "stage7a-state-evidence-model.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE7A_ACCEPTANCE_GENERATOR),
                        "--prepared-against", stage7a["prepared_against_main_sha"],
                        "--captured-at", stage7a["captured_at"],
                        "--output", str(regenerated7a),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 7A acceptance regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated7a.is_file():
                    require(regenerated7a.read_bytes() == STAGE7A_ACCEPTANCE.read_bytes(),
                            "Stage 7A acceptance receipt is not reproducible", problems)

    if STAGE7D_ACCEPTANCE.is_file():
        stage7d = load(STAGE7D_ACCEPTANCE)
        require(stage7d.get("schema") == "velvetos.stage7d-artifact-retention.v1"
                and stage7d.get("stage") == "7D"
                and stage7d.get("behavior_change") is True
                and stage7d.get("repository_acceptance") == "PASS",
                "Stage 7D acceptance metadata drift", problems)
        criteria7d = stage7d.get("acceptance") or {}
        expected_criteria7d = {
            "all_nine_artifact_classes_have_concrete_retention",
            "morning_green_large_history_was_copy_first_archived",
            "archive_receipt_has_per_file_sha256",
            "active_consumers_do_not_reference_removed_dated_bundles",
            "rolling_current_transport_is_producer_and_request_contract",
            "current_transport_assets_match_canonical_assets",
            "git_image_noise_reduction_exceeds_5mb",
            "transient_state_classes_have_bounded_target_retention",
            "work_ledger_resolved_without_new_store",
            "no_external_effect_authority_change",
            "rollback_and_audit_chain_preserved",
        }
        require(set(criteria7d) == expected_criteria7d
                and all(criteria7d.get(key) is True for key in expected_criteria7d),
                "Stage 7D acceptance criteria drift or fail", problems)
        require(stage7d.get("next_stage") == "Stage 7 integrated acceptance gate",
                "Stage 7D next-stage handoff drift", problems)
        migration7d = stage7d.get("copy_first_migration") or {}
        require(migration7d.get("archive_files") == 86
                and migration7d.get("archive_directories") == 18
                and migration7d.get("historical_asset_dirs_remaining_in_tree") == 0
                and migration7d.get("generated_image_bytes_reduced", 0) > 5_000_000,
                "Stage 7D copy-first migration evidence drift", problems)
        scan7d = stage7d.get("consumer_scan") or {}
        require(scan7d.get("pass") is True
                and scan7d.get("dated_transport_refs") == [],
                "Stage 7D active-consumer scan is not clean", problems)
        ledger7d = stage7d.get("work_ledger") or {}
        require(ledger7d.get("decision") == "NO_NEW_WORK_LEDGER_STORE"
                and ledger7d.get("canonical_continuation_view") == "office/control/HANDOFF.json"
                and ledger7d.get("new_store_created") is False
                and ledger7d.get("policy_authority") is False
                and ledger7d.get("external_effect_authority") is False,
                "Stage 7D Work Ledger resolution drift", problems)
        baseline7d = stage7d.get("authority_baseline") or {}
        require(baseline7d.get("unchanged_from_prepared_against") is True,
                "Stage 7D external-effect authority baseline drift", problems)
        if STAGE7D_ACCEPTANCE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated7d = Path(td) / "stage7d-artifact-retention.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE7D_ACCEPTANCE_GENERATOR),
                        "--prepared-against", stage7d["prepared_against_main_sha"],
                        "--captured-at", stage7d["captured_at"],
                        "--output", str(regenerated7d),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 7D acceptance regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated7d.is_file():
                    require(regenerated7d.read_bytes() == STAGE7D_ACCEPTANCE.read_bytes(),
                            "Stage 7D acceptance receipt is not reproducible", problems)

    if STAGE7_ACCEPTANCE.is_file():
        stage7 = load(STAGE7_ACCEPTANCE)
        require(stage7.get("schema") == "velvetos.stage7-acceptance.v1"
                and stage7.get("stage") == "7"
                and stage7.get("behavior_change") is False
                and stage7.get("stage7_gate") == "PASS",
                "Stage 7 integrated acceptance metadata drift", problems)
        criteria7 = stage7.get("acceptance_criteria") or {}
        expected_criteria7 = {
            "state_evidence_model_is_single_and_semantically_explicit",
            "memory_learning_is_selective_evidence_gated_and_nonduplicative",
            "research_and_scheduler_have_single_clock_ownership_and_truth_metadata",
            "artifact_retention_is_concrete_copy_first_and_audit_preserving",
            "work_ledger_question_is_resolved_without_a_second_store",
            "external_effect_authority_remains_unchanged_across_stage7",
            "stage7_adds_no_duplicate_store_daemon_scheduler_or_recurring_cost",
            "stage7_substage_handoff_chain_is_complete",
            "main_full_sensor_suite_116_of_116",
        }
        require(set(criteria7) == expected_criteria7
                and all(criteria7.get(key) is True for key in expected_criteria7),
                "Stage 7 integrated acceptance criteria drift or fail", problems)
        main7 = stage7.get("main_full_suite") or {}
        require(main7.get("head_sha") == stage7.get("prepared_against_main_sha")
                and main7.get("conclusion") == "SUCCESS"
                and main7.get("mode") == "full"
                and main7.get("registered_sensors") == 116
                and main7.get("passed_sensors") == 116
                and main7.get("log_markers") == ["SENSORS 116 mode=full", "OK suite passed=116"],
                "Stage 7 main full-suite evidence drift", problems)
        sources7 = stage7.get("source_receipts") or {}
        require(set(sources7) == {"stage7a", "stage7b", "stage7c", "stage7d"},
                "Stage 7 source receipt set drift", problems)
        for name7, meta7 in sources7.items():
            path7 = ROOT / str((meta7 or {}).get("path") or "")
            require(path7.is_file(), f"Stage 7 source receipt missing: {name7}", problems)
            if path7.is_file():
                obj7 = load(path7)
                canonical7 = hashlib.sha256(
                    json.dumps(obj7, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest()
                require(canonical7 == (meta7 or {}).get("canonical_json_sha256"),
                        f"Stage 7 source receipt hash drift: {name7}", problems)
        state7 = stage7.get("state_evidence") or {}
        require(set(state7.get("semantic_categories") or []) == {
                    "AUDIT_HISTORY", "AUTHORIZATION_DECISION", "CANONICAL_STATE", "EVIDENCE_RECEIPT"
                }
                and state7.get("surface_count") == 22
                and state7.get("retention_classes_mapped") == 9,
                "Stage 7 state/evidence summary drift", problems)
        memory7 = stage7.get("memory_learning") or {}
        require(memory7.get("automatic_promotion") is False
                and memory7.get("new_always_on_memory_systems") == 0
                and memory7.get("incremental_recurring_cost_ils") == 0,
                "Stage 7 memory/learning safety drift", problems)
        scheduler7 = stage7.get("research_scheduler") or {}
        require(scheduler7.get("protected_routine_count") == 9
                and scheduler7.get("primary_clock_owner") == "grok-bot-routines"
                and scheduler7.get("provider_verified") == 9
                and scheduler7.get("deep_review_required") == 0
                and scheduler7.get("pending") == scheduler7.get("reusable_current_review"),
                "Stage 7 research/scheduler summary drift", problems)
        retention7 = stage7.get("retention") or {}
        require(retention7.get("artifact_class_count") == 9
                and retention7.get("unclassified_retention_count") == 0
                and retention7.get("generated_image_bytes_reduced", 0) > 5_000_000
                and retention7.get("active_removed_path_refs") == 0
                and retention7.get("work_ledger_decision") == "NO_NEW_WORK_LEDGER_STORE",
                "Stage 7 retention summary drift", problems)
        authority7 = stage7.get("authority") or {}
        require(authority7.get("external_effect_authority_changed") is False,
                "Stage 7 external-effect authority changed", problems)
        entry8 = stage7.get("stage8_entry") or {}
        require(entry8.get("allowed") is True
                and entry8.get("next_stage") == "Stage 8 — Core / Instance Separation + Capability Placement"
                and "no big-bang delete" in str(entry8.get("constraint") or ""),
                "Stage 8 entry contract drift", problems)
        if STAGE7_ACCEPTANCE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated7 = Path(td) / "stage7-acceptance.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE7_ACCEPTANCE_GENERATOR),
                        "--prepared-against", stage7["prepared_against_main_sha"],
                        "--captured-at", stage7["captured_at"],
                        "--main-run-id", str(main7["workflow_run_id"]),
                        "--main-job-id", str(main7["job_id"]),
                        "--main-run-url", main7["run_url"],
                        "--output", str(regenerated7),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 7 integrated acceptance regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated7.is_file():
                    require(regenerated7.read_bytes() == STAGE7_ACCEPTANCE.read_bytes(),
                            "Stage 7 integrated acceptance receipt is not reproducible", problems)

    if STAGE8A_INVENTORY.is_file():
        stage8a = load(STAGE8A_INVENTORY)
        require(stage8a.get("schema") == "velvetos.stage8a-core-instance-inventory.v1"
                and stage8a.get("stage") == "8A"
                and stage8a.get("behavior_change") is False
                and stage8a.get("repository_acceptance") == "PASS",
                "Stage 8A inventory metadata drift", problems)
        criteria8a = stage8a.get("acceptance_criteria") or {}
        expected_criteria8a = {
            "canonical_instance_profile_and_desk_are_identified",
            "core_compatibility_reference_and_duplicate_sample_are_identified",
            "machine_enforced_sample_autonomy_and_root_desk_debts_are_mapped",
            "fleet_values_and_control_api_consumers_are_mapped",
            "integration_account_and_tool_status_mixed_surface_is_mapped",
            "creative_project_and_expert_distribution_surfaces_are_mapped",
            "host_and_instance_path_surfaces_are_mapped",
            "every_surface_has_target_owner_class_wave_and_no_delete_authority",
            "stage8_preparation_remains_non_normative",
            "external_effect_policy_registry_is_unchanged",
            "stage8a_is_inventory_only_no_move_delete_or_resolver_cutover",
        }
        require(set(criteria8a) == expected_criteria8a
                and all((criteria8a.get(key) or {}).get("pass") is True for key in expected_criteria8a),
                "Stage 8A acceptance criteria drift or fail", problems)
        inventory8a = stage8a.get("inventory") or []
        require(len(inventory8a) == 14, "Stage 8A inventory surface count drift", problems)
        ids8a = {row.get("surface_id") for row in inventory8a if isinstance(row, dict)}
        required_ids8a = {
            "canonical-instance-profile",
            "canonical-instance-desk",
            "core-reference-profile-metadata",
            "core-vf-sample-profile",
            "root-vf-desk-reference-bind",
            "living-studio-embedded-business-rules",
            "vfprod-fleet-registry",
            "control-api-instance-and-fleet-resolution",
            "tool-status-mixed-registry",
            "chatgpt-project-vf-distribution",
            "expert-modules-with-vf-values",
            "windows-host-binding-document",
            "policy-registry-explicit-instance-pointers",
            "stage8-non-normative-preparation",
        }
        require(ids8a == required_ids8a, "Stage 8A inventory surface id set drift", problems)
        require(all(isinstance(row, dict)
                    and row.get("target_owner")
                    and row.get("target_classes")
                    and row.get("migration_wave")
                    and row.get("delete_authorized") is False
                    for row in inventory8a),
                "Stage 8A inventory contains incomplete/unsafe placement row", problems)
        summary8a = stage8a.get("summary") or {}
        require(summary8a.get("surface_count") == 14
                and summary8a.get("duplicate_or_mixed_surface_count") == 10
                and summary8a.get("fleet_printer_count") == 4
                and summary8a.get("project_bundle_revision") == "6.6.4",
                "Stage 8A summary drift", problems)
        require(len(summary8a.get("machine_enforced_initial_debts") or []) == 4,
                "Stage 8A initial machine-enforced debt list drift", problems)
        canonical8a = stage8a.get("canonical_instance") or {}
        require(canonical8a.get("id") == "velvet-factory"
                and canonical8a.get("profile") == "instances/velvet-factory/instance/velvet-factory.json"
                and canonical8a.get("desk") == "instances/velvet-factory/.cursor/vf-desk.json",
                "Stage 8A canonical instance identity/path drift", problems)
        authority8a = stage8a.get("authority_baseline") or {}
        require(authority8a.get("unchanged") is True
                and authority8a.get("policy_registry_canonical_sha256")
                    == authority8a.get("prepared_against_policy_registry_canonical_sha256"),
                "Stage 8A external-effect policy registry drift", problems)
        design8a = stage8a.get("design_inputs") or {}
        require(design8a.get("drafts_are_authority") is False,
                "Stage 8A non-normative prep was promoted to authority", problems)
        require(stage8a.get("next_stage") == "Stage 8B — Canonical Instance Config + Resolver Foundation",
                "Stage 8A next-stage handoff drift", problems)
        constraints8a = set(stage8a.get("stage8a_constraints") or [])
        require({"inventory only", "no fact move", "no resolver cutover", "no legacy delete"} <= constraints8a,
                "Stage 8A observation-only constraints drift", problems)
        if STAGE8A_INVENTORY_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8a = Path(td) / "stage8a-core-instance-inventory.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8A_INVENTORY_GENERATOR),
                        "--prepared-against", stage8a["prepared_against_main_sha"],
                        "--captured-at", stage8a["captured_at"],
                        "--output", str(regenerated8a),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8A inventory regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8a.is_file():
                    require(regenerated8a.read_bytes() == STAGE8A_INVENTORY.read_bytes(),
                            "Stage 8A inventory receipt is not reproducible", problems)

    if STAGE8B_RESOLVER.is_file():
        stage8b = load(STAGE8B_RESOLVER)
        require(stage8b.get("schema") == "velvetos.stage8b-instance-resolver-foundation.v1"
                and stage8b.get("stage") == "8B_RESOLVER_FOUNDATION"
                and stage8b.get("behavior_change") is True
                and stage8b.get("repository_acceptance") == "PASS",
                "Stage 8B resolver-foundation metadata drift", problems)
        criteria8b = stage8b.get("acceptance_criteria") or {}
        expected_criteria8b = {
            "generic_resolver_has_no_vf_business_default",
            "core_requires_explicit_instance_selection",
            "modern_manifest_contract_is_fail_closed",
            "generic_instance_does_not_require_fleet_or_vf_surfaces",
            "vf_manifest_declares_profile_tooldesk_and_fleet_surfaces",
            "canonical_instance_fleet_matches_legacy_fleet",
            "legacy_consumers_and_external_effect_policy_are_unchanged",
            "no_legacy_path_is_deleted_in_resolver_foundation",
            "consumer_cutover_is_deferred_until_parity_migration",
        }
        require(set(criteria8b) == expected_criteria8b
                and all(criteria8b.get(key) is True for key in expected_criteria8b),
                "Stage 8B resolver-foundation acceptance criteria drift or fail", problems)
        resolver8b = stage8b.get("resolver") or {}
        fixture8b = resolver8b.get("generic_fixture") or {}
        require(resolver8b.get("path") == "packages/velvetos/instance_resolver.py"
                and resolver8b.get("core_mode") == "core-explicit-instance"
                and resolver8b.get("environment_variable") == "VELVETOS_INSTANCE_ID"
                and resolver8b.get("silent_business_default") is False,
                "Stage 8B resolver contract drift", problems)
        require(fixture8b.get("instance_id") == "fixture"
                and fixture8b.get("surfaces") == ["profile"]
                and fixture8b.get("bad_surface_contract_version_rejected") is True
                and fixture8b.get("parent_traversal_rejected") is True,
                "Stage 8B generic fixture proof drift", problems)
        manifest8b = stage8b.get("manifest_contract") or {}
        require(manifest8b.get("surface_contract_version") == 1
                and manifest8b.get("generic_required_surfaces") == ["profile"]
                and set((manifest8b.get("vf_surfaces") or {})) == {"profile", "toolDesk", "fleet"},
                "Stage 8B manifest contract drift", problems)
        fleet8b = stage8b.get("fleet") or {}
        require(fleet8b.get("canonical_instance_path") == "instances/velvet-factory/instance/fleet.json"
                and fleet8b.get("legacy_compatibility_path") == "packages/vfprod/FLEET.json"
                and fleet8b.get("parity") is True
                and fleet8b.get("printer_count") == 4
                and fleet8b.get("consumer_cutover") is False,
                "Stage 8B fleet parity/compatibility drift", problems)
        legacy8b = stage8b.get("legacy_baseline") or {}
        require(legacy8b.get("all_unchanged") is True
                and legacy8b.get("legacy_delete_authorized") is False
                and all((legacy8b.get("unchanged") or {}).values()),
                "Stage 8B legacy baseline drift", problems)
        require(stage8b.get("next_stage") == "Stage 8B — Canonical Instance Config continuation",
                "Stage 8B resolver-foundation next-stage handoff drift", problems)
        constraints8b = set(stage8b.get("constraints") or [])
        require("no legacy delete" in constraints8b
                and "no external-effect authority change" in constraints8b
                and "generic Core cannot silently assume Velvet Factory" in constraints8b,
                "Stage 8B resolver-foundation constraints drift", problems)
        if STAGE8B_RESOLVER_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8b = Path(td) / "stage8b-instance-resolver-foundation.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8B_RESOLVER_GENERATOR),
                        "--prepared-against", stage8b["prepared_against_main_sha"],
                        "--captured-at", stage8b["captured_at"],
                        "--output", str(regenerated8b),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8B resolver-foundation regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8b.is_file():
                    require(regenerated8b.read_bytes() == STAGE8B_RESOLVER.read_bytes(),
                            "Stage 8B resolver-foundation receipt is not reproducible", problems)

    if STAGE8B_CONFIG.is_file():
        stage8b_config = load(STAGE8B_CONFIG)
        require(stage8b_config.get("schema") == "velvetos.stage8b-canonical-instance-config.v1"
                and stage8b_config.get("stage") == "8B"
                and stage8b_config.get("behavior_change") is True
                and stage8b_config.get("repository_acceptance") == "PASS",
                "Stage 8B canonical-config metadata drift", problems)
        criteria8bc = stage8b_config.get("acceptance_criteria") or {}
        expected_criteria8bc = {
            "all_stage8b_inventory_items_have_canonical_placement",
            "generic_core_tool_contract_has_no_vf_business_values",
            "instance_tool_state_contains_tools_not_generic_rules",
            "tool_status_split_exactly_composes_legacy_compatibility_document",
            "tool_status_resolution_requires_explicit_instance_from_core",
            "fleet_canonical_copy_remains_exactly_equal_to_legacy",
            "all_known_direct_legacy_readers_are_unchanged_and_still_on_compatibility_surface",
            "resolver_foundation_is_passed_and_bound",
            "external_effect_policy_registry_is_unchanged",
            "no_legacy_path_delete_or_consumer_cutover_in_stage8b",
        }
        require(set(criteria8bc) == expected_criteria8bc
                and all(criteria8bc.get(key) is True for key in expected_criteria8bc),
                "Stage 8B canonical-config acceptance criteria drift or fail", problems)
        surfaces8bc = stage8b_config.get("canonical_instance_surfaces") or {}
        require(surfaces8bc == {
                    "profile": "instance/velvet-factory.json",
                    "toolDesk": ".cursor/vf-desk.json",
                    "fleet": "instance/fleet.json",
                    "toolStatus": "instance/tool-status.json",
                },
                "Stage 8B canonical instance surface map drift", problems)
        split8bc = stage8b_config.get("tool_status_split") or {}
        require(split8bc.get("core_contract") == "packages/velvetos/tool-status-contract.json"
                and split8bc.get("instance_state") == "instances/velvet-factory/instance/tool-status.json"
                and split8bc.get("legacy_composite") == "packages/velvetos/TOOL-STATUS.json"
                and split8bc.get("tool_count") == 10
                and split8bc.get("exact_composition_parity") is True
                and split8bc.get("legacy_composite_unchanged_from_prepared_against") is True
                and split8bc.get("consumer_cutover") is False
                and split8bc.get("sensitive_key_paths") == [],
                "Stage 8B tool-status split evidence drift", problems)
        readers8bc = stage8b_config.get("legacy_reader_evidence") or {}
        require(len(readers8bc) == 6
                and all(isinstance(row, dict)
                        and row.get("unchanged") is True
                        and row.get("still_reads_legacy_composite") is True
                        for row in readers8bc.values()),
                "Stage 8B legacy reader compatibility proof drift", problems)
        authority8bc = stage8b_config.get("authority_baseline") or {}
        require(authority8bc.get("unchanged") is True
                and authority8bc.get("policy_registry_canonical_sha256")
                    == authority8bc.get("prepared_against_policy_registry_canonical_sha256"),
                "Stage 8B external-effect authority baseline drift", problems)
        require(stage8b_config.get("next_stage") == "Stage 8C — Consumer Migration",
                "Stage 8B next-stage handoff drift", problems)
        constraints8bc = set(stage8b_config.get("stage8c_constraints") or [])
        require({
                    "migrate readers domain-by-domain through generic resolvers",
                    "prove semantic parity before each consumer cutover",
                    "keep legacy compatibility files through a rollback window",
                    "retire legacy only after clean consumer scan",
                    "Control API and Living Studio remain projections, never source of truth",
                    "no external-effect authority change",
                } <= constraints8bc,
                "Stage 8C entry constraints drift", problems)
        if STAGE8B_CONFIG_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8bc = Path(td) / "stage8b-canonical-instance-config.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8B_CONFIG_GENERATOR),
                        "--prepared-against", stage8b_config["prepared_against_main_sha"],
                        "--captured-at", stage8b_config["captured_at"],
                        "--output", str(regenerated8bc),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8B canonical-config regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8bc.is_file():
                    require(regenerated8bc.read_bytes() == STAGE8B_CONFIG.read_bytes(),
                            "Stage 8B canonical-config receipt is not reproducible", problems)

    if STAGE8C_SAMPLE.is_file():
        stage8c_sample = load(STAGE8C_SAMPLE)
        require(stage8c_sample.get("schema") == "velvetos.stage8c-sample-profile-consumers.v1"
                and stage8c_sample.get("stage") == "8C_SAMPLE_PROFILE_CONSUMERS"
                and stage8c_sample.get("behavior_change") is True
                and stage8c_sample.get("repository_acceptance") == "PASS",
                "Stage 8C sample/profile metadata drift", problems)
        criteria8cs = stage8c_sample.get("acceptance_criteria") or {}
        expected_criteria8cs = {
            "core_no_longer_declares_vf_sample_as_runtime_reference_profile",
            "core_marks_samples_as_non_runtime_rollback_documentation",
            "offering_guard_reads_canonical_profile_through_instance_resolver",
            "core_scaffold_guard_no_longer_reads_or_validates_vf_sample",
            "core_cli_has_no_silent_vf_default_and_supports_explicit_instance_selection",
            "canonical_and_rollback_sample_module_sets_match",
            "legacy_sample_is_unchanged_and_retained_for_rollback_window",
            "only_non_runtime_guards_and_snapshot_generators_reference_legacy_sample_path",
            "active_docs_point_to_canonical_instance_profile_not_sample",
            "external_effect_policy_registry_is_unchanged",
        }
        require(set(criteria8cs) == expected_criteria8cs
                and all(criteria8cs.get(key) is True for key in expected_criteria8cs),
                "Stage 8C sample/profile acceptance criteria drift or fail", problems)
        legacy8cs = stage8c_sample.get("legacy_sample") or {}
        require(legacy8cs.get("path") == "packages/velvetos/samples/velvet-factory.json"
                and legacy8cs.get("retained") is True
                and legacy8cs.get("unchanged_from_prepared_against") is True
                and legacy8cs.get("runtime_authority") is False
                and legacy8cs.get("delete_authorized") is False
                and legacy8cs.get("rollback_window_open") is True,
                "Stage 8C legacy sample rollback contract drift", problems)
        consumers8cs = stage8c_sample.get("cutover_consumers") or {}
        require(set(consumers8cs) == {
                    "packages/velvetos/CORE.json",
                    "scripts/check-vf-offering.py",
                    "scripts/check-velvetos.py",
                    "scripts/velvetos.py",
                }
                and all(isinstance(row, dict)
                        and row.get("legacy_sample_path_present") is False
                        and row.get("legacy_samples_symbol_present") is False
                        for row in consumers8cs.values()),
                "Stage 8C sample/profile consumer cutover drift", problems)
        require(stage8c_sample.get("remaining_legacy_path_references") == [
                    "scripts/check-policy-architecture.py",
                    "scripts/generate-stage8a-core-instance-inventory.py",
                    "scripts/generate-stage8b-instance-resolver-foundation.py",
                ],
                "Stage 8C sample/profile remaining-reference scan drift", problems)
        cli8cs = stage8c_sample.get("cli_proof") or {}
        require((cli8cs.get("generic_without_instance") or {}).get("exit_code") == 0
                and str((cli8cs.get("generic_without_instance") or {}).get("first_line") or "").startswith("modules (no instance selected")
                and (cli8cs.get("explicit_velvet_factory") or {}).get("exit_code") == 0
                and "selected instance velvet-factory" in str((cli8cs.get("explicit_velvet_factory") or {}).get("first_line") or ""),
                "Stage 8C generic/explicit CLI proof drift", problems)
        authority8cs = stage8c_sample.get("authority_baseline") or {}
        require(authority8cs.get("unchanged") is True
                and authority8cs.get("policy_registry_canonical_sha256")
                    == authority8cs.get("prepared_against_policy_registry_canonical_sha256"),
                "Stage 8C sample/profile authority baseline drift", problems)
        require(stage8c_sample.get("next_stage") == "Stage 8C — Remaining consumer domains",
                "Stage 8C sample/profile next-stage handoff drift", problems)
        if STAGE8C_SAMPLE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8cs = Path(td) / "stage8c-sample-profile-consumers.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8C_SAMPLE_GENERATOR),
                        "--prepared-against", stage8c_sample["prepared_against_main_sha"],
                        "--captured-at", stage8c_sample["captured_at"],
                        "--output", str(regenerated8cs),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8C sample/profile regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8cs.is_file():
                    require(regenerated8cs.read_bytes() == STAGE8C_SAMPLE.read_bytes(),
                            "Stage 8C sample/profile receipt is not reproducible", problems)

    if STAGE8C_ROOT_DESK.is_file():
        stage8c_desk = load(STAGE8C_ROOT_DESK)
        require(stage8c_desk.get("schema") == "velvetos.stage8c-root-desk-readers.v1"
                and stage8c_desk.get("stage") == "8C_ROOT_DESK_READERS"
                and stage8c_desk.get("behavior_change") is True
                and stage8c_desk.get("repository_acceptance") == "PASS",
                "Stage 8C root-desk metadata drift", problems)
        criteria8cd = stage8c_desk.get("acceptance_criteria") or {}
        expected_criteria8cd = {
            "root_desk_is_unchanged_and_retained_for_rollback",
            "canonical_instance_desk_has_exact_required_tool_subtree_parity",
            "canonical_instance_desk_has_exact_ops_seat_parity",
            "vfmedia_reads_tool_desk_through_instance_resolver",
            "send_preflight_reads_tool_desk_through_instance_resolver",
            "offering_guard_no_longer_treats_root_desk_as_active_authority",
            "all_direct_readers_are_free_of_root_desk_literal",
            "external_effect_policy_registry_is_unchanged",
            "legacy_root_desk_delete_is_not_authorized",
        }
        require(set(criteria8cd) == expected_criteria8cd
                and all(criteria8cd.get(key) is True for key in expected_criteria8cd),
                "Stage 8C root-desk acceptance criteria drift or fail", problems)
        root8cd = stage8c_desk.get("root_desk") or {}
        require(root8cd.get("path") == ".cursor/vf-desk.json"
                and root8cd.get("retained") is True
                and root8cd.get("unchanged_from_prepared_against") is True
                and root8cd.get("delete_authorized") is False
                and root8cd.get("rollback_window_open") is True,
                "Stage 8C root-desk rollback contract drift", problems)
        canonical8cd = stage8c_desk.get("canonical_tool_desk") or {}
        parity8cd = canonical8cd.get("parity") or {}
        require(canonical8cd.get("path") == "instances/velvet-factory/.cursor/vf-desk.json"
                and set(parity8cd) == {"gmail", "instagram", "gemini", "chatgpt", "drive", "opsSeat"}
                and all(parity8cd.values()),
                "Stage 8C root-desk canonical parity drift", problems)
        readers8cd = stage8c_desk.get("cutover_readers") or {}
        require(set(readers8cd) == {
                    "scripts/check-vfmedia.py",
                    "scripts/check-vf-offering.py",
                    "scripts/vf_send_preflight.py",
                }
                and all(isinstance(row, dict)
                        and row.get("root_desk_literal_present") is False
                        for row in readers8cd.values()),
                "Stage 8C root-desk direct reader scan drift", problems)
        authority8cd = stage8c_desk.get("authority_baseline") or {}
        require(authority8cd.get("unchanged") is True
                and authority8cd.get("policy_registry_canonical_sha256")
                    == authority8cd.get("prepared_against_policy_registry_canonical_sha256"),
                "Stage 8C root-desk authority baseline drift", problems)
        require(stage8c_desk.get("next_stage") == "Stage 8C — Remaining consumer domains",
                "Stage 8C root-desk next-stage handoff drift", problems)
        if STAGE8C_ROOT_DESK_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8cd = Path(td) / "stage8c-root-desk-readers.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8C_ROOT_DESK_GENERATOR),
                        "--prepared-against", stage8c_desk["prepared_against_main_sha"],
                        "--captured-at", stage8c_desk["captured_at"],
                        "--output", str(regenerated8cd),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8C root-desk regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8cd.is_file():
                    require(regenerated8cd.read_bytes() == STAGE8C_ROOT_DESK.read_bytes(),
                            "Stage 8C root-desk receipt is not reproducible", problems)

    if STAGE8C_DESK_CATALOG.is_file():
        stage8c_catalog = load(STAGE8C_DESK_CATALOG)
        require(stage8c_catalog.get("schema") == "velvetos.stage8c-desk-catalog-bindings.v1"
                and stage8c_catalog.get("stage") == "8C_DESK_CATALOG_BINDINGS"
                and stage8c_catalog.get("behavior_change") is True
                and stage8c_catalog.get("repository_acceptance") == "PASS",
                "Stage 8C desk-catalog metadata drift", problems)
        criteria8cc = stage8c_catalog.get("acceptance_criteria") or {}
        expected_criteria8cc = {
            "all_target_catalog_graph_bindings_point_to_canonical_instance_desk",
            "no_root_only_desk_binding_remains_in_target_packages",
            "vfmem_binding_count_is_exact",
            "vfgraft_binding_count_is_exact",
            "vfharness_binding_count_is_exact",
            "root_desk_remains_unchanged_for_rollback",
            "external_effect_policy_registry_is_unchanged",
            "legacy_root_desk_delete_is_not_authorized",
        }
        require(set(criteria8cc) == expected_criteria8cc
                and all(criteria8cc.get(key) is True for key in expected_criteria8cc),
                "Stage 8C desk-catalog acceptance criteria drift or fail", problems)
        require(stage8c_catalog.get("canonical_path") == "instances/velvet-factory/.cursor/vf-desk.json"
                and stage8c_catalog.get("total_canonical_bindings") == 18,
                "Stage 8C desk-catalog binding summary drift", problems)
        targets8cc = stage8c_catalog.get("targets") or {}
        require(len(targets8cc) == 11
                and all(isinstance(row, dict)
                        and row.get("root_only_binding_count") == 0
                        and int(row.get("canonical_binding_count") or 0) > 0
                        for row in targets8cc.values()),
                "Stage 8C desk-catalog target binding drift", problems)
        root8cc = stage8c_catalog.get("root_desk") or {}
        require(root8cc.get("retained") is True
                and root8cc.get("unchanged_from_prepared_against") is True
                and root8cc.get("delete_authorized") is False,
                "Stage 8C desk-catalog rollback contract drift", problems)
        authority8cc = stage8c_catalog.get("authority_baseline") or {}
        require(authority8cc.get("unchanged") is True
                and authority8cc.get("policy_registry_canonical_sha256")
                    == authority8cc.get("prepared_against_policy_registry_canonical_sha256"),
                "Stage 8C desk-catalog authority baseline drift", problems)
        require(stage8c_catalog.get("next_stage") == "Stage 8C — Remaining consumer domains",
                "Stage 8C desk-catalog next-stage handoff drift", problems)
        if STAGE8C_DESK_CATALOG_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8cc = Path(td) / "stage8c-desk-catalog-bindings.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8C_DESK_CATALOG_GENERATOR),
                        "--prepared-against", stage8c_catalog["prepared_against_main_sha"],
                        "--captured-at", stage8c_catalog["captured_at"],
                        "--output", str(regenerated8cc),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8C desk-catalog regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8cc.is_file():
                    require(regenerated8cc.read_bytes() == STAGE8C_DESK_CATALOG.read_bytes(),
                            "Stage 8C desk-catalog receipt is not reproducible", problems)

    if STAGE8C_LIVING_RULES.is_file():
        stage8c_living = load(STAGE8C_LIVING_RULES)
        require(stage8c_living.get("schema") == "velvetos.stage8c-living-studio-rules.v1"
                and stage8c_living.get("stage") == "8C_LIVING_STUDIO_RULES"
                and stage8c_living.get("behavior_change") is True
                and stage8c_living.get("repository_acceptance") == "PASS",
                "Stage 8C Living Studio rule metadata drift", problems)
        criteria8cl = stage8c_living.get("acceptance_criteria") or {}
        expected_criteria8cl = {
            "stage8a_living_studio_debt_is_bound_to_this_slice",
            "autonomy_config_contains_resolution_contract_not_vf_business_values",
            "effective_business_rules_exactly_match_pre_cutover_legacy_shape_and_values",
            "effective_business_rules_derive_instance_values_from_canonical_profile",
            "generic_living_studio_resolver_has_no_vf_business_default_or_values",
            "core_checkout_requires_explicit_instance_for_business_rule_projection",
            "vf_autonomy_action_engine_is_byte_unchanged",
            "office_control_plane_is_byte_unchanged",
            "no_new_store_queue_or_canonical_write_is_introduced",
            "external_effect_policy_registry_is_unchanged",
        }
        require(set(criteria8cl) == expected_criteria8cl
                and all(criteria8cl.get(key) is True for key in expected_criteria8cl),
                "Stage 8C Living Studio acceptance criteria drift or fail", problems)
        cfg8cl = stage8c_living.get("configuration") or {}
        resolution8cl = cfg8cl.get("resolution") or {}
        require(cfg8cl.get("path") == "packages/velvetos/living-studio/AUTONOMY.json"
                and cfg8cl.get("embedded_business_rules_removed") is True
                and resolution8cl.get("resolver") == "packages/velvetos/living_studio_rules.py"
                and resolution8cl.get("instanceSurface") == "profile"
                and resolution8cl.get("requireExplicitInstanceIdWhenRunningFromCore") is True
                and resolution8cl.get("projectionOnly") is True,
                "Stage 8C Living Studio resolution contract drift", problems)
        parity8cl = stage8c_living.get("legacy_parity") or {}
        require(parity8cl.get("exact") is True
                and parity8cl.get("prepared_against_rules") == parity8cl.get("effective_rules")
                and len(parity8cl.get("effective_rules") or {}) == 7,
                "Stage 8C Living Studio legacy parity drift", problems)
        isolation8cl = stage8c_living.get("runtime_isolation") or {}
        require(isolation8cl.get("vf_autonomy_byte_unchanged") is True
                and isolation8cl.get("office_control_plane_byte_unchanged") is True
                and isolation8cl.get("projection_only") is True
                and isolation8cl.get("new_store") is False
                and isolation8cl.get("new_queue") is False,
                "Stage 8C Living Studio runtime isolation drift", problems)
        authority8cl = stage8c_living.get("authority_baseline") or {}
        require(authority8cl.get("unchanged") is True
                and authority8cl.get("policy_registry_canonical_sha256")
                    == authority8cl.get("prepared_against_policy_registry_canonical_sha256"),
                "Stage 8C Living Studio authority baseline drift", problems)
        require(stage8c_living.get("next_stage") == "Stage 8C — Remaining consumer domains",
                "Stage 8C Living Studio next-stage handoff drift", problems)
        if STAGE8C_LIVING_RULES_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8cl = Path(td) / "stage8c-living-studio-rules.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8C_LIVING_RULES_GENERATOR),
                        "--prepared-against", stage8c_living["prepared_against_main_sha"],
                        "--captured-at", stage8c_living["captured_at"],
                        "--output", str(regenerated8cl),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8C Living Studio regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8cl.is_file():
                    require(regenerated8cl.read_bytes() == STAGE8C_LIVING_RULES.read_bytes(),
                            "Stage 8C Living Studio receipt is not reproducible", problems)

    if STAGE8C_CONTROL_API_FLEET.is_file():
        stage8c_control = load(STAGE8C_CONTROL_API_FLEET)
        require(stage8c_control.get("schema") == "velvetos.stage8c-control-api-fleet.v1"
                and stage8c_control.get("stage") == "8C_CONTROL_API_FLEET"
                and stage8c_control.get("behavior_change") is True
                and stage8c_control.get("repository_acceptance") == "PASS",
                "Stage 8C Control API fleet metadata drift", problems)
        criteria8ccf = stage8c_control.get("acceptance_criteria") or {}
        expected_criteria8ccf = {
            "control_api_production_reads_canonical_instance_fleet_surface",
            "control_api_agents_and_integrations_read_canonical_tooldesk_surface",
            "control_api_runtime_has_no_legacy_fleet_path_or_silent_vf_default",
            "control_api_registry_declares_instance_owned_fleet_and_desk_authority",
            "cloud_run_image_packages_resolver_manifest_and_declared_surfaces_not_legacy_fleet",
            "vf_cloud_run_deployment_selects_instance_explicitly",
            "canonical_fleet_remains_exactly_equal_to_legacy_rollback_copy",
            "legacy_fleet_is_unchanged_and_retained_for_rollback",
            "external_effect_policy_registry_is_unchanged",
        }
        require(set(criteria8ccf) == expected_criteria8ccf
                and all(criteria8ccf.get(key) is True for key in expected_criteria8ccf),
                "Stage 8C Control API fleet acceptance criteria drift or fail", problems)
        fleet8ccf = stage8c_control.get("fleet") or {}
        require(fleet8ccf.get("canonical") == "instances/velvet-factory/instance/fleet.json"
                and fleet8ccf.get("legacy") == "packages/vfprod/FLEET.json"
                and fleet8ccf.get("parity") is True
                and fleet8ccf.get("legacy_unchanged_from_prepared_against") is True
                and fleet8ccf.get("printer_count") == 4
                and fleet8ccf.get("legacy_delete_authorized") is False,
                "Stage 8C Control API fleet rollback/parity drift", problems)
        control8ccf = stage8c_control.get("control_api") or {}
        require(control8ccf.get("production_source") == "instances/<VELVETOS_INSTANCE_ID>/instance/fleet.json"
                and control8ccf.get("agent_source") == "instances/<VELVETOS_INSTANCE_ID>/.cursor/vf-desk.json#desk"
                and control8ccf.get("integration_source") == "instances/<VELVETOS_INSTANCE_ID>/.cursor/vf-desk.json#tools"
                and control8ccf.get("explicit_instance_environment") == "VELVETOS_INSTANCE_ID"
                and control8ccf.get("vf_deployment_instance") == "velvet-factory"
                and control8ccf.get("legacy_fleet_runtime_reference") is False,
                "Stage 8C Control API source contract drift", problems)
        authority8ccf = stage8c_control.get("authority_baseline") or {}
        require(authority8ccf.get("unchanged") is True
                and authority8ccf.get("policy_registry_canonical_sha256")
                    == authority8ccf.get("prepared_against_policy_registry_canonical_sha256"),
                "Stage 8C Control API authority baseline drift", problems)
        require(stage8c_control.get("next_stage") == "Stage 8C — Remaining consumer domains",
                "Stage 8C Control API next-stage handoff drift", problems)
        if STAGE8C_CONTROL_API_FLEET_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8ccf = Path(td) / "stage8c-control-api-fleet.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8C_CONTROL_API_FLEET_GENERATOR),
                        "--prepared-against", stage8c_control["prepared_against_main_sha"],
                        "--captured-at", stage8c_control["captured_at"],
                        "--output", str(regenerated8ccf),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8C Control API fleet regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8ccf.is_file():
                    require(regenerated8ccf.read_bytes() == STAGE8C_CONTROL_API_FLEET.read_bytes(),
                            "Stage 8C Control API fleet receipt is not reproducible", problems)

    if STAGE8C_EXPERT_MODULES.is_file():
        stage8c_experts = load(STAGE8C_EXPERT_MODULES)
        require(stage8c_experts.get("schema") == "velvetos.stage8c-expert-modules.v1"
                and stage8c_experts.get("stage") == "8C_EXPERT_MODULES"
                and stage8c_experts.get("behavior_change") is True
                and stage8c_experts.get("repository_acceptance") == "PASS",
                "Stage 8C expert-modules metadata drift", problems)
        criteria8ce = stage8c_experts.get("acceptance_criteria") or {}
        expected_criteria8ce = {
            "all_three_core_expert_modules_have_no_vf_specific_cta_location_or_visual_digest_values",
            "revenue_loop_resolves_cta_and_fulfillment_from_selected_instance",
            "social_booster_resolves_cta_location_and_contact_semantics_from_selected_instance",
            "media_director_resolves_required_visual_standard_from_selected_instance_profile",
            "media_director_visual_gate_remains_fail_closed_without_generic_fallback",
            "vf_visual_enforcement_still_machine_binds_generic_media_director_module",
            "canonical_instance_profile_retains_vf_values_and_visual_authority",
            "external_effect_policy_registry_is_unchanged",
        }
        require(set(criteria8ce) == expected_criteria8ce
                and all(criteria8ce.get(key) is True for key in expected_criteria8ce),
                "Stage 8C expert-modules acceptance criteria drift or fail", problems)
        modules8ce = stage8c_experts.get("modules") or {}
        require(set(modules8ce) == {"expert-revenue-loop", "expert-social-booster", "expert-media-director"}
                and all(isinstance(row, dict)
                        and row.get("forbidden_instance_value_hits") == []
                        and row.get("mentions_selected_instance") is True
                        for row in modules8ce.values()),
                "Stage 8C expert-module parameterization drift", problems)
        visual8ce = stage8c_experts.get("visual_enforcement") or {}
        require(visual8ce.get("path") == "packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json"
                and visual8ce.get("media_director_reference_count") == 2
                and visual8ce.get("unchanged_in_this_slice") is True,
                "Stage 8C expert-module visual enforcement drift", problems)
        authority8ce = stage8c_experts.get("authority_baseline") or {}
        require(authority8ce.get("unchanged") is True
                and authority8ce.get("policy_registry_canonical_sha256")
                    == authority8ce.get("prepared_against_policy_registry_canonical_sha256"),
                "Stage 8C expert-module authority baseline drift", problems)
        require(stage8c_experts.get("remaining_domains") == [
                    "chatgpt-project-vf-distribution",
                    "windows-host-binding-document",
                ],
                "Stage 8C expert-module remaining-domain handoff drift", problems)
        if STAGE8C_EXPERT_MODULES_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8ce = Path(td) / "stage8c-expert-modules.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8C_EXPERT_MODULES_GENERATOR),
                        "--prepared-against", stage8c_experts["prepared_against_main_sha"],
                        "--captured-at", stage8c_experts["captured_at"],
                        "--output", str(regenerated8ce),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8C expert-module regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8ce.is_file():
                    require(regenerated8ce.read_bytes() == STAGE8C_EXPERT_MODULES.read_bytes(),
                            "Stage 8C expert-modules receipt is not reproducible", problems)

    if STAGE8C_CHATGPT_DISTRIBUTION.is_file():
        stage8c_chat = load(STAGE8C_CHATGPT_DISTRIBUTION)
        require(stage8c_chat.get("schema") == "velvetos.stage8c-chatgpt-distribution-consumers.v1"
                and stage8c_chat.get("stage") == "8C_CHATGPT_DISTRIBUTION_CONSUMERS"
                and stage8c_chat.get("behavior_change") is True
                and stage8c_chat.get("repository_acceptance") == "PASS",
                "Stage 8C ChatGPT distribution metadata drift", problems)
        criteria8cg = stage8c_chat.get("acceptance_criteria") or {}
        expected_criteria8cg = {
            "instance_manifest_declares_chatgpt_project_distribution_surface",
            "instance_distribution_file_set_matches_core_compatibility_bundle",
            "instance_distribution_is_byte_equal_to_core_compatibility_bundle",
            "core_compatibility_non_pin_files_are_unchanged",
            "core_compatibility_trust_updates_are_limited_to_chat_runtime_and_asset_manifest_pins",
            "cold_start_checker_resolves_explicit_instance_distribution",
            "cold_start_preflight_has_no_hardcoded_vf_bundle_revision_or_authority_filename",
            "cold_start_preflight_derives_identity_from_bundle_manifest_or_latest",
            "generic_core_checkout_without_instance_distribution_selection_remains_fail_closed",
            "external_effect_policy_registry_is_unchanged",
        }
        require(set(criteria8cg) == expected_criteria8cg
                and all(criteria8cg.get(key) is True for key in expected_criteria8cg),
                "Stage 8C ChatGPT distribution acceptance criteria drift or fail", problems)
        distribution8cg = stage8c_chat.get("distribution") or {}
        require(distribution8cg.get("surface") == "chatgptProject"
                and distribution8cg.get("surface_pointer") == "distribution/chatgpt-project/LATEST.json"
                and distribution8cg.get("instance_root") == "instances/velvet-factory/distribution/chatgpt-project"
                and distribution8cg.get("core_compatibility_root") == "packages/velvetos/chatgpt-project"
                and distribution8cg.get("file_count") == 33
                and distribution8cg.get("byte_parity") is True
                and distribution8cg.get("core_compatibility_non_pin_files_unchanged") is True
                and distribution8cg.get("asset_manifest_pin_only_change") is True
                and distribution8cg.get("project_manifest_pin_only_change") is True
                and distribution8cg.get("delete_authorized") is False,
                "Stage 8C ChatGPT distribution parity/rollback drift", problems)
        consumers8cg = stage8c_chat.get("consumers") or {}
        require(consumers8cg == {
                    "scripts/check-chat-cold-start-preflight.py": "instance-distribution-explicit-vf",
                    "scripts/vf_chat_cold_start_preflight.py": "generic-bundle-derived-identity",
                },
                "Stage 8C ChatGPT distribution consumer mapping drift", problems)
        authority8cg = stage8c_chat.get("authority_baseline") or {}
        require(authority8cg.get("unchanged") is True
                and authority8cg.get("policy_registry_canonical_sha256")
                    == authority8cg.get("prepared_against_policy_registry_canonical_sha256"),
                "Stage 8C ChatGPT distribution authority baseline drift", problems)
        require(stage8c_chat.get("next_stage") == "Stage 8C — ChatGPT distribution contract continuation",
                "Stage 8C ChatGPT distribution next-stage handoff drift", problems)
        if STAGE8C_CHATGPT_DISTRIBUTION_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8cg = Path(td) / "stage8c-chatgpt-distribution-consumers.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8C_CHATGPT_DISTRIBUTION_GENERATOR),
                        "--prepared-against", stage8c_chat["prepared_against_main_sha"],
                        "--captured-at", stage8c_chat["captured_at"],
                        "--output", str(regenerated8cg),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8C ChatGPT distribution regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8cg.is_file():
                    require(regenerated8cg.read_bytes() == STAGE8C_CHATGPT_DISTRIBUTION.read_bytes(),
                            "Stage 8C ChatGPT distribution receipt is not reproducible", problems)

    if STAGE8C_WINDOWS_HOST.is_file():
        stage8c_windows = load(STAGE8C_WINDOWS_HOST)
        require(stage8c_windows.get("schema") == "velvetos.stage8c-windows-host-binding.v1"
                and stage8c_windows.get("stage") == "8C_WINDOWS_HOST_BINDING"
                and stage8c_windows.get("behavior_change") is True
                and stage8c_windows.get("repository_acceptance") == "PASS",
                "Stage 8C Windows host-binding metadata drift", problems)
        criteria8cw = stage8c_windows.get("acceptance_criteria") or {}
        expected_criteria8cw = {
            "generic_core_windows_contract_has_no_instance_host_or_absolute_root_values",
            "canonical_instance_declares_windows_host_binding_surface",
            "instance_windows_binding_owns_current_host_identity_and_machine_paths",
            "windows_bootstraps_require_explicit_host_id_without_hardcoded_identity",
            "windows_path_consumers_keep_fail_closed_variable_driven_behavior",
            "vfmem_windows_consumers_remain_generic_and_variable_driven",
            "operational_host_and_openpost_registries_are_unchanged_and_match_binding",
            "external_effect_policy_registry_is_unchanged",
        }
        require(set(criteria8cw) == expected_criteria8cw
                and all(criteria8cw.get(key) is True for key in expected_criteria8cw),
                "Stage 8C Windows host-binding acceptance criteria drift or fail", problems)
        binding8cw = stage8c_windows.get("binding") or {}
        require(binding8cw.get("path") == "instances/velvet-factory/instance/windows-host-binding.json"
                and binding8cw.get("surface") == "windowsHostBinding"
                and binding8cw.get("host_id") == "sderot-windows"
                and binding8cw.get("machine_scope_required") is True
                and binding8cw.get("fallback_to_user_profile") is False
                and set(binding8cw.get("environment_keys") or []) == {
                    "VELVET_ROOT", "VELVETOS_REPO_ROOT", "VELVETOS_RUNTIME_ROOT",
                    "VELVETOS_STATE_ROOT", "VELVETOS_HOST_ID"
                }
                and binding8cw.get("lane_count") == 12,
                "Stage 8C Windows host-binding instance contract drift", problems)
        generic8cw = stage8c_windows.get("generic_core") or {}
        require(all(not hits for hits in (generic8cw.get("private_value_hits") or {}).values()),
                "Stage 8C Windows host-binding Core leak scan drift", problems)
        baseline8cw = stage8c_windows.get("operational_registry_baseline") or {}
        require(baseline8cw.get("render_hosts_unchanged") is True
                and baseline8cw.get("openpost_unchanged") is True
                and baseline8cw.get("host_registry_id") == "sderot-windows",
                "Stage 8C Windows operational baseline drift", problems)
        authority8cw = stage8c_windows.get("authority_baseline") or {}
        require(authority8cw.get("unchanged") is True
                and authority8cw.get("policy_registry_canonical_sha256")
                    == authority8cw.get("prepared_against_policy_registry_canonical_sha256"),
                "Stage 8C Windows authority baseline drift", problems)
        require(stage8c_windows.get("next_stage") == "Stage 8C complete"
                and stage8c_windows.get("remaining_domains") == [],
                "Stage 8C Windows closure handoff drift", problems)
        if STAGE8C_WINDOWS_HOST_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8cw = Path(td) / "stage8c-windows-host-binding.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8C_WINDOWS_HOST_GENERATOR),
                        "--prepared-against", stage8c_windows["prepared_against_main_sha"],
                        "--captured-at", stage8c_windows["captured_at"],
                        "--output", str(regenerated8cw),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8C Windows host-binding regeneration failed: "
                        + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8cw.is_file():
                    require(regenerated8cw.read_bytes() == STAGE8C_WINDOWS_HOST.read_bytes(),
                            "Stage 8C Windows host-binding receipt is not reproducible", problems)

    if STAGE8C_CLOSURE.is_file():
        closure8c = load(STAGE8C_CLOSURE)
        require(
            closure8c.get("schema") == "velvetos.stage8c-closure.v1"
            and closure8c.get("stage") == "8C_CLOSURE"
            and closure8c.get("behavior_change") is False
            and closure8c.get("repository_acceptance") == "PASS",
            "Stage 8C closure metadata drift",
            problems,
        )
        criteria8cc = closure8c.get("acceptance_criteria") or {}
        expected8cc = {
            "all_stage8c_inventory_surfaces_have_passed_migration_receipts",
            "all_stage8c_domain_receipts_pass_their_full_acceptance_criteria",
            "no_unsclassified_direct_legacy_consumers_remain_in_migrated_domains",
            "core_resolution_is_explicit_and_fail_closed_across_migrated_domains",
            "rollback_compatibility_paths_remain_present",
            "legacy_paths_remain_protected_from_stage8c_deletion",
            "external_effect_authority_is_unchanged_across_stage8",
            "final_stage8c_domain_reports_no_remaining_stage8c_domains",
            "main_full_sensor_suite_116_of_116",
        }
        require(
            set(criteria8cc) == expected8cc
            and all(criteria8cc.get(key) is True for key in expected8cc),
            "Stage 8C closure criteria drift or fail",
            problems,
        )
        sources8cc = closure8c.get("source_receipts") or {}
        expected_sources8cc = {
            "stage8a_inventory",
            "stage8b_resolver",
            "stage8b_config",
            "sample_profile",
            "root_desk_readers",
            "desk_catalog_bindings",
            "living_studio",
            "control_api_fleet",
            "expert_modules",
            "chatgpt_distribution",
            "windows_host_binding",
        }
        require(set(sources8cc) == expected_sources8cc,
                "Stage 8C closure source receipt set drift", problems)
        for name8cc, meta8cc in sources8cc.items():
            path8cc = ROOT / str((meta8cc or {}).get("path") or "")
            require(path8cc.is_file(), f"Stage 8C closure source missing: {name8cc}", problems)
            if path8cc.is_file():
                obj8cc = load(path8cc)
                canonical8cc = hashlib.sha256(
                    json.dumps(obj8cc, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest()
                require(canonical8cc == (meta8cc or {}).get("canonical_json_sha256"),
                        f"Stage 8C closure source hash drift: {name8cc}", problems)
        coverage8cc = closure8c.get("inventory_coverage") or {}
        require(
            coverage8cc.get("stage8c_surface_count") == 7
            and len(coverage8cc.get("stage8c_surface_ids") or []) == 7
            and coverage8cc.get("all_covered") is True,
            "Stage 8C closure inventory coverage drift",
            problems,
        )
        rollback8cc = closure8c.get("rollback_compatibility") or {}
        require(
            rollback8cc.get("all_present") is True
            and rollback8cc.get("deletion_authorized") is False
            and len(rollback8cc.get("paths") or []) == 5,
            "Stage 8C closure rollback compatibility drift",
            problems,
        )
        authority8cc = closure8c.get("authority") or {}
        require(authority8cc.get("external_effect_authority_changed") is False,
                "Stage 8C closure changed external-effect authority", problems)
        main8cc = closure8c.get("main_full_suite") or {}
        require(
            main8cc.get("head_sha") == closure8c.get("prepared_against_main_sha")
            and main8cc.get("conclusion") == "SUCCESS"
            and main8cc.get("mode") == "full"
            and main8cc.get("registered_sensors") == 116
            and main8cc.get("passed_sensors") == 116
            and main8cc.get("log_markers") == ["SENSORS 116 mode=full", "OK suite passed=116"],
            "Stage 8C closure main full-suite evidence drift",
            problems,
        )
        entry8d = closure8c.get("stage8d_entry") or {}
        require(
            closure8c.get("next_stage") == "Stage 8D — Legacy retirement"
            and entry8d.get("allowed") is True
            and "rollback window" in str(entry8d.get("constraint") or "")
            and "no big-bang delete" in str(entry8d.get("constraint") or ""),
            "Stage 8D entry contract drift",
            problems,
        )
        if STAGE8C_CLOSURE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8cc = Path(td) / "stage8c-closure.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8C_CLOSURE_GENERATOR),
                        "--prepared-against", closure8c["prepared_against_main_sha"],
                        "--captured-at", closure8c["captured_at"],
                        "--main-run-id", str(main8cc["workflow_run_id"]),
                        "--main-job-id", str(main8cc["job_id"]),
                        "--main-run-url", main8cc["run_url"],
                        "--output", str(regenerated8cc),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8C closure regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8cc.is_file():
                    require(regenerated8cc.read_bytes() == STAGE8C_CLOSURE.read_bytes(),
                            "Stage 8C closure receipt is not reproducible", problems)

    if STAGE8D_READINESS.is_file():
        ready8d = load(STAGE8D_READINESS)
        require(
            ready8d.get("schema") == "velvetos.stage8d-retirement-readiness.v1"
            and ready8d.get("stage") == "8D_READINESS"
            and ready8d.get("behavior_change") is False
            and ready8d.get("repository_assessment") == "PASS",
            "Stage 8D readiness metadata drift",
            problems,
        )
        require(
            ready8d.get("retirement_authorized") is False
            and ready8d.get("readiness_state") == "BLOCKED_PENDING_MIGRATION_OR_ROLLBACK_WINDOW",
            "Stage 8D retirement must remain blocked while readiness blockers exist",
            problems,
        )
        surfaces8d = ready8d.get("compatibility_surfaces") or {}
        expected_surfaces8d = {
            "sample_profile",
            "root_desk",
            "fleet",
            "tool_status",
            "chatgpt_core_bundle",
        }
        require(set(surfaces8d) == expected_surfaces8d,
                "Stage 8D compatibility-surface set drift", problems)
        for sid8d, row8d in surfaces8d.items():
            require(
                (row8d or {}).get("present") is True
                and (row8d or {}).get("delete_authorized") is False
                and (row8d or {}).get("retirement_ready") is False,
                f"Stage 8D surface unexpectedly ready/deletable: {sid8d}",
                problems,
            )
        blockers8d = ready8d.get("blockers") or {}
        require(set(blockers8d) == expected_surfaces8d,
                "Stage 8D blocker set must cover all compatibility surfaces", problems)
        require(
            blockers8d.get("sample_profile") == ["rollback_window_open"],
            "Stage 8D sample blocker semantics drift",
            problems,
        )
        for sid8d in {"root_desk", "fleet", "tool_status", "chatgpt_core_bundle"}:
            reasons8d = set(blockers8d.get(sid8d) or [])
            require(
                {"rollback_window_open", "active_compatibility_consumers_remain"} <= reasons8d,
                f"Stage 8D active blocker semantics drift: {sid8d}",
                problems,
            )
        assessment8d = ready8d.get("assessment") or {}
        require(
            assessment8d.get("stage8c_closure_is_passed") is True
            and assessment8d.get("all_compatibility_paths_are_still_present") is True
            and assessment8d.get("sample_profile_has_no_active_runtime_consumer") is True
            and assessment8d.get("sample_profile_rollback_window_is_still_open") is True
            and assessment8d.get("root_desk_rollback_window_is_still_open") is True
            and assessment8d.get("external_effect_authority_is_unchanged") is True,
            "Stage 8D readiness assessment drift",
            problems,
        )
        main8d = ready8d.get("post_closure_main_full_suite") or {}
        require(
            main8d.get("head_sha") == ready8d.get("prepared_against_main_sha")
            and main8d.get("conclusion") == "SUCCESS"
            and main8d.get("mode") == "full"
            and main8d.get("registered_sensors") == 116
            and main8d.get("passed_sensors") == 116
            and main8d.get("log_markers") == ["SENSORS 116 mode=full", "OK suite passed=116"],
            "Stage 8D post-closure main evidence drift",
            problems,
        )
        authority8d = ready8d.get("authority") or {}
        require(authority8d.get("external_effect_authority_changed") is False,
                "Stage 8D readiness changed external-effect authority", problems)
        constraints8d = ready8d.get("constraints") or []
        require(
            "no legacy deletion while retirement_authorized=false" in constraints8d
            and "rollback windows close only on explicit evidence, never by inference" in constraints8d,
            "Stage 8D deletion/rollback guard drift",
            problems,
        )
        if STAGE8D_READINESS_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8d = Path(td) / "stage8d-retirement-readiness.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_READINESS_GENERATOR),
                        "--prepared-against", ready8d["prepared_against_main_sha"],
                        "--captured-at", ready8d["captured_at"],
                        "--main-run-id", str(main8d["workflow_run_id"]),
                        "--main-job-id", str(main8d["job_id"]),
                        "--main-run-url", main8d["run_url"],
                        "--output", str(regenerated8d),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(proc.returncode == 0,
                        "Stage 8D readiness regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()),
                        problems)
                if proc.returncode == 0 and regenerated8d.is_file():
                    require(regenerated8d.read_bytes() == STAGE8D_READINESS.read_bytes(),
                            "Stage 8D readiness receipt is not reproducible", problems)

    if STAGE8D_FLEET.is_file():
        fleet8d = load(STAGE8D_FLEET)
        require(
            fleet8d.get("schema") == "velvetos.stage8d-fleet-consumer-migration.v1"
            and fleet8d.get("stage") == "8D_FLEET_CONSUMER_MIGRATION"
            and fleet8d.get("behavior_change") is True
            and fleet8d.get("repository_acceptance") == "PASS",
            "Stage 8D fleet migration metadata drift",
            problems,
        )
        criteria8df = fleet8d.get("acceptance_criteria") or {}
        expected8df = {
            "living_studio_production_planner_uses_instance_fleet_surface",
            "living_studio_has_no_legacy_fleet_consumer",
            "canonical_instance_manifest_declares_fleet_surface",
            "canonical_and_legacy_fleet_remain_parity_equal",
            "legacy_fleet_is_retained_for_rollback",
            "fleet_retirement_remains_unauthorized_while_rollback_window_is_open",
            "stage8d_readiness_baseline_is_preserved",
            "external_effect_policy_registry_is_unchanged",
        }
        require(
            set(criteria8df) == expected8df and all(criteria8df.get(k) is True for k in expected8df),
            "Stage 8D fleet migration criteria drift or fail",
            problems,
        )
        migration8df = fleet8d.get("migration") or {}
        require(
            migration8df.get("consumer") == "packages/velvetos/living-studio/REGISTRY.json"
            and migration8df.get("skill") == "production-planner"
            and migration8df.get("to") == "instance:surface:fleet"
            and migration8df.get("legacy_path_retained") is True
            and migration8df.get("delete_authorized") is False,
            "Stage 8D fleet migration contract drift",
            problems,
        )
        require(
            (fleet8d.get("parity") or {}).get("equal") is True
            and (fleet8d.get("consumer_scan") or {}).get("living_studio_legacy_references") == []
            and (fleet8d.get("rollback") or {}).get("window_open") is True
            and (fleet8d.get("rollback") or {}).get("delete_authorized") is False,
            "Stage 8D fleet parity/rollback drift",
            problems,
        )
        authority8df = fleet8d.get("authority") or {}
        require(
            authority8df.get("external_effect_authority_changed") is False
            and authority8df.get("policy_registry_canonical_sha256")
                == authority8df.get("prepared_against_policy_registry_canonical_sha256"),
            "Stage 8D fleet migration changed authority",
            problems,
        )
        if STAGE8D_FLEET_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8df = Path(td) / "stage8d-fleet-consumer-migration.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_FLEET_GENERATOR),
                        "--prepared-against", fleet8d["prepared_against_main_sha"],
                        "--source-commit", fleet8d["source_commit_sha"],
                        "--captured-at", fleet8d["captured_at"],
                        "--output", str(regenerated8df),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D fleet migration regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated8df.is_file():
                    require(
                        regenerated8df.read_bytes() == STAGE8D_FLEET.read_bytes(),
                        "Stage 8D fleet migration receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_ROOT_DESK.is_file():
        desk8d = load(STAGE8D_ROOT_DESK)
        require(
            desk8d.get("schema") == "velvetos.stage8d-root-desk-consumer-migration.v1"
            and desk8d.get("stage") == "8D_ROOT_DESK_CONSUMER_MIGRATION"
            and desk8d.get("behavior_change") is True
            and desk8d.get("repository_acceptance") == "PASS",
            "Stage 8D root-desk migration metadata drift",
            problems,
        )
        criteria8dr = desk8d.get("acceptance_criteria") or {}
        expected8dr = {
            "cursor_rule_resolves_selected_instance_tool_desk_surface",
            "cursor_rule_has_no_root_desk_literal",
            "visual_sensor_resolves_tool_desk_through_instance_resolver",
            "visual_sensor_has_no_root_desk_literal",
            "known_active_root_desk_blockers_are_removed",
            "stage8c_required_tool_and_ops_parity_remains_proven",
            "legacy_root_desk_is_retained_for_rollback",
            "root_desk_retirement_remains_unauthorized_while_rollback_window_is_open",
            "stage8d_readiness_baseline_is_preserved",
            "external_effect_policy_registry_is_unchanged",
        }
        require(
            set(criteria8dr) == expected8dr and all(criteria8dr.get(k) is True for k in expected8dr),
            "Stage 8D root-desk migration criteria drift or fail",
            problems,
        )
        migration8dr = desk8d.get("migration") or {}
        require(
            migration8dr.get("legacy_path") == ".cursor/vf-desk.json"
            and migration8dr.get("replacement_surface") == "instance:surface:toolDesk"
            and migration8dr.get("legacy_path_retained") is True
            and migration8dr.get("delete_authorized") is False,
            "Stage 8D root-desk migration contract drift",
            problems,
        )
        require(
            (desk8d.get("prior_parity_evidence") or {}).get("all_required_parity") is True
            and (desk8d.get("consumer_scan") or {}).get("known_active_blocker_references") == []
            and (desk8d.get("rollback") or {}).get("window_open") is True
            and (desk8d.get("rollback") or {}).get("delete_authorized") is False,
            "Stage 8D root-desk parity/rollback drift",
            problems,
        )
        authority8dr = desk8d.get("authority") or {}
        require(
            authority8dr.get("external_effect_authority_changed") is False
            and authority8dr.get("policy_registry_canonical_sha256")
                == authority8dr.get("prepared_against_policy_registry_canonical_sha256"),
            "Stage 8D root-desk migration changed authority",
            problems,
        )
        if STAGE8D_ROOT_DESK_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8dr = Path(td) / "stage8d-root-desk-consumer-migration.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_ROOT_DESK_GENERATOR),
                        "--prepared-against", desk8d["prepared_against_main_sha"],
                        "--source-commit", desk8d["source_commit_sha"],
                        "--captured-at", desk8d["captured_at"],
                        "--output", str(regenerated8dr),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D root-desk migration regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated8dr.is_file():
                    require(
                        regenerated8dr.read_bytes() == STAGE8D_ROOT_DESK.read_bytes(),
                        "Stage 8D root-desk migration receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_TOOL_STATUS.is_file():
        tool8d = load(STAGE8D_TOOL_STATUS)
        require(
            tool8d.get("schema") == "velvetos.stage8d-tool-status-consumer-migration.v1"
            and tool8d.get("stage") == "8D_TOOL_STATUS_CONSUMER_MIGRATION"
            and tool8d.get("behavior_change") is True
            and tool8d.get("repository_acceptance") == "PASS",
            "Stage 8D tool-status migration metadata drift",
            problems,
        )
        criteria8dt = tool8d.get("acceptance_criteria") or {}
        expected8dt = {
            "core_declares_selected_instance_tool_status_as_active_authority",
            "tool_status_contract_marks_consumer_cutover_active",
            "all_stage8b_direct_readers_have_no_legacy_composite_dependency",
            "all_real_stage8b_status_readers_use_the_generic_resolver",
            "unused_vfmcp_legacy_binding_is_removed_without_fake_read",
            "active_authority_docs_and_rules_point_to_instance_tool_status",
            "openpost_and_core_mcp_use_instance_tool_status_authority",
            "canonical_composition_remains_exactly_equal_to_legacy_composite",
            "legacy_tool_status_composite_is_retained_for_rollback",
            "rollback_window_remains_open_and_delete_is_unauthorized",
            "stage8d_readiness_baseline_is_preserved",
            "external_effect_policy_registry_is_unchanged",
        }
        require(
            set(criteria8dt) == expected8dt and all(criteria8dt.get(k) is True for k in expected8dt),
            "Stage 8D tool-status migration criteria drift or fail",
            problems,
        )
        migration8dt = tool8d.get("migration") or {}
        require(
            migration8dt.get("active_authority") == "instance:surface:toolStatus"
            and migration8dt.get("resolver") == "packages/velvetos/tool_status_resolver.py"
            and migration8dt.get("rollback_compatibility_path") == "packages/velvetos/TOOL-STATUS.json"
            and migration8dt.get("consumer_cutover") is True
            and migration8dt.get("rollback_compatibility_retained") is True
            and migration8dt.get("legacy_path_retained") is True
            and migration8dt.get("delete_authorized") is False,
            "Stage 8D tool-status migration contract drift",
            problems,
        )
        require(
            (tool8d.get("consumer_scan") or {}).get("active_authority_legacy_references") == []
            and (tool8d.get("consumer_scan") or {}).get("active_blockers_removed") is True,
            "Stage 8D tool-status active consumer scan drift",
            problems,
        )
        require(
            (tool8d.get("parity") or {}).get("equal") is True
            and (tool8d.get("parity") or {}).get("composed_canonical_json_sha256")
                == (tool8d.get("parity") or {}).get("legacy_canonical_json_sha256"),
            "Stage 8D tool-status parity drift",
            problems,
        )
        require(
            (tool8d.get("rollback") or {}).get("window_open") is True
            and (tool8d.get("rollback") or {}).get("retirement_ready") is False
            and (tool8d.get("rollback") or {}).get("delete_authorized") is False,
            "Stage 8D tool-status rollback semantics drift",
            problems,
        )
        authority8dt = tool8d.get("authority") or {}
        require(
            authority8dt.get("external_effect_authority_changed") is False
            and authority8dt.get("policy_registry_canonical_sha256")
                == authority8dt.get("prepared_against_policy_registry_canonical_sha256"),
            "Stage 8D tool-status migration changed authority",
            problems,
        )
        if STAGE8D_TOOL_STATUS_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8dt = Path(td) / "stage8d-tool-status-consumer-migration.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_TOOL_STATUS_GENERATOR),
                        "--prepared-against", tool8d["prepared_against_main_sha"],
                        "--source-commit", tool8d["source_commit_sha"],
                        "--captured-at", tool8d["captured_at"],
                        "--output", str(regenerated8dt),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D tool-status migration regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated8dt.is_file():
                    require(
                        regenerated8dt.read_bytes() == STAGE8D_TOOL_STATUS.read_bytes(),
                        "Stage 8D tool-status migration receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_CHATGPT_CORE.is_file():
        chat8d = load(STAGE8D_CHATGPT_CORE)
        require(
            chat8d.get("schema") == "velvetos.stage8d-chatgpt-core-consumer-migration.v1"
            and chat8d.get("stage") == "8D_CHATGPT_CORE_CONSUMER_MIGRATION"
            and chat8d.get("behavior_change") is True
            and chat8d.get("repository_acceptance") == "PASS",
            "Stage 8D ChatGPT Core migration metadata drift",
            problems,
        )
        criteria8dc = chat8d.get("acceptance_criteria") or {}
        expected8dc = {
            "stage8c_chatgpt_distribution_parity_is_preserved",
            "instance_manifest_keeps_chatgpt_project_surface",
            "project_authority_bundle_uses_instance_surface_references",
            "reel_and_visual_contracts_use_instance_chatgpt_surface",
            "generic_bundle_resolver_has_no_silent_business_default",
            "vf_runtime_callers_select_instance_explicitly",
            "all_active_chatgpt_consumers_have_no_legacy_root_reference",
            "canonical_instance_distribution_remains_byte_equal_to_legacy_bundle",
            "legacy_chatgpt_core_bundle_is_retained_for_rollback",
            "rollback_window_remains_open_and_delete_is_unauthorized",
            "stage8d_readiness_baseline_is_preserved",
            "external_effect_policy_registry_is_unchanged",
        }
        require(
            set(criteria8dc) == expected8dc and all(criteria8dc.get(k) is True for k in expected8dc),
            "Stage 8D ChatGPT Core migration criteria drift or fail",
            problems,
        )
        migration8dc = chat8d.get("migration") or {}
        require(
            migration8dc.get("active_authority") == "instance:surface:chatgptProject"
            and migration8dc.get("instance_distribution_root") == "instances/velvet-factory/distribution/chatgpt-project"
            and migration8dc.get("rollback_compatibility_root") == "packages/velvetos/chatgpt-project"
            and migration8dc.get("legacy_path_retained") is True
            and migration8dc.get("delete_authorized") is False,
            "Stage 8D ChatGPT Core migration contract drift",
            problems,
        )
        scan8dc = chat8d.get("consumer_scan") or {}
        require(
            scan8dc.get("active_legacy_references") == []
            and scan8dc.get("active_blockers_removed") is True,
            "Stage 8D ChatGPT Core active consumer scan drift",
            problems,
        )
        parity8dc = chat8d.get("parity") or {}
        require(
            parity8dc.get("file_count") == 33
            and parity8dc.get("file_sets_equal") is True
            and parity8dc.get("byte_equal") is True,
            "Stage 8D ChatGPT Core parity drift",
            problems,
        )
        require(
            (chat8d.get("rollback") or {}).get("window_open") is True
            and (chat8d.get("rollback") or {}).get("retirement_ready") is False
            and (chat8d.get("rollback") or {}).get("delete_authorized") is False,
            "Stage 8D ChatGPT Core rollback semantics drift",
            problems,
        )
        authority8dc = chat8d.get("authority") or {}
        require(
            authority8dc.get("external_effect_authority_changed") is False
            and authority8dc.get("policy_registry_canonical_sha256")
                == authority8dc.get("prepared_against_policy_registry_canonical_sha256"),
            "Stage 8D ChatGPT Core migration changed authority",
            problems,
        )
        if STAGE8D_CHATGPT_CORE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8dc = Path(td) / "stage8d-chatgpt-core-consumer-migration.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_CHATGPT_CORE_GENERATOR),
                        "--prepared-against", chat8d["prepared_against_main_sha"],
                        "--source-commit", chat8d["source_commit_sha"],
                        "--captured-at", chat8d["captured_at"],
                        "--output", str(regenerated8dc),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D ChatGPT Core migration regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated8dc.is_file():
                    require(
                        regenerated8dc.read_bytes() == STAGE8D_CHATGPT_CORE.read_bytes(),
                        "Stage 8D ChatGPT Core migration receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_POST_MIGRATION.is_file():
        post8d = load(STAGE8D_POST_MIGRATION)
        require(
            post8d.get("schema") == "velvetos.stage8d-post-migration-readiness.v1"
            and post8d.get("stage") == "8D_POST_MIGRATION_READINESS"
            and post8d.get("behavior_change") is False
            and post8d.get("repository_assessment") == "PASS",
            "Stage 8D post-migration readiness metadata drift",
            problems,
        )
        criteria8dp = post8d.get("acceptance_criteria") or {}
        expected8dp = {
            "initial_stage8d_readiness_baseline_passed",
            "all_five_compatibility_paths_are_still_present",
            "all_active_compatibility_consumers_are_migrated",
            "all_five_surfaces_have_parity_or_unchanged_rollback_proof",
            "all_rollback_windows_remain_explicitly_open",
            "no_rollback_window_is_closed_by_inference",
            "retirement_remains_unauthorized_without_closure_evidence",
            "delete_authority_remains_false_for_every_surface",
            "external_effect_authority_is_unchanged_since_stage8d_entry",
            "post_migration_main_full_sensor_suite_116_of_116",
        }
        require(
            set(criteria8dp) == expected8dp and all(criteria8dp.get(k) is True for k in expected8dp),
            "Stage 8D post-migration readiness criteria drift or fail",
            problems,
        )
        assessment8dp = post8d.get("assessment") or {}
        require(
            assessment8dp.get("all_active_compatibility_consumers_migrated") is True
            and assessment8dp.get("all_required_parity_proven") is True
            and assessment8dp.get("all_compatibility_paths_retained") is True
            and assessment8dp.get("all_rollback_windows_open") is True
            and assessment8dp.get("remaining_active_consumer_blockers") == []
            and assessment8dp.get("remaining_blocker_class") == "ROLLBACK_WINDOW_CLOSURE_EVIDENCE_ONLY"
            and assessment8dp.get("external_effect_authority_unchanged") is True,
            "Stage 8D post-migration assessment drift",
            problems,
        )
        surfaces8dp = post8d.get("compatibility_surfaces") or {}
        require(
            set(surfaces8dp) == {"sample_profile", "root_desk", "fleet", "tool_status", "chatgpt_core_bundle"},
            "Stage 8D post-migration surface set drift",
            problems,
        )
        for sid8dp, row8dp in surfaces8dp.items():
            require(
                row8dp.get("present") is True
                and row8dp.get("active_consumers_migrated") is True
                and row8dp.get("parity_proven") is True
                and row8dp.get("rollback_window_open") is True
                and row8dp.get("rollback_window_closure_evidence") is None
                and row8dp.get("retirement_ready") is False
                and row8dp.get("delete_authorized") is False
                and row8dp.get("blocking_reasons") == ["rollback_window_open_without_explicit_closure_evidence"],
                f"Stage 8D post-migration rollback semantics drift: {sid8dp}",
                problems,
            )
        require(
            post8d.get("retirement_authorized") is False
            and post8d.get("readiness_state") == "BLOCKED_ROLLBACK_WINDOWS_ONLY",
            "Stage 8D post-migration retirement must remain blocked",
            problems,
        )
        full8dp = post8d.get("post_migration_main_full_suite") or {}
        require(
            full8dp.get("head_sha") == post8d.get("source_commit_sha")
            and full8dp.get("verification_source") == "local_post_merge_check-all"
            and full8dp.get("mode") == "full"
            and full8dp.get("registered_sensors") == 116
            and full8dp.get("passed_sensors") == 116
            and full8dp.get("conclusion") == "SUCCESS",
            "Stage 8D post-migration full-suite evidence drift",
            problems,
        )
        authority8dp = post8d.get("authority") or {}
        require(
            authority8dp.get("external_effect_authority_changed") is False
            and authority8dp.get("policy_registry_sha256")
                == authority8dp.get("stage8d_entry_policy_registry_sha256"),
            "Stage 8D post-migration readiness changed authority",
            problems,
        )
        if STAGE8D_POST_MIGRATION_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8dp = Path(td) / "stage8d-post-migration-readiness.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_POST_MIGRATION_GENERATOR),
                        "--prepared-against", post8d["prepared_against_main_sha"],
                        "--source-commit", post8d["source_commit_sha"],
                        "--captured-at", post8d["captured_at"],
                        "--output", str(regenerated8dp),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D post-migration readiness regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated8dp.is_file():
                    require(
                        regenerated8dp.read_bytes() == STAGE8D_POST_MIGRATION.read_bytes(),
                        "Stage 8D post-migration readiness receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_SAMPLE_ROLLBACK_CLOSURE.is_file():
        close8ds = load(STAGE8D_SAMPLE_ROLLBACK_CLOSURE)
        require(
            close8ds.get("schema") == "velvetos.stage8d-sample-profile-rollback-closure.v1"
            and close8ds.get("stage") == "8D_SAMPLE_PROFILE_ROLLBACK_CLOSURE"
            and close8ds.get("behavior_change") is False
            and close8ds.get("surface_id") == "sample_profile"
            and close8ds.get("repository_assessment") == "PASS",
            "Stage 8D sample rollback closure metadata drift",
            problems,
        )
        criteria8ds = close8ds.get("acceptance_criteria") or {}
        expected8ds = {
            "stage8c_sample_cutover_passed",
            "legacy_sample_has_no_runtime_authority",
            "active_legacy_consumers_remain_zero",
            "legacy_sample_is_byte_unchanged_since_cutover",
            "canonical_and_legacy_module_sets_match",
            "external_effect_authority_is_unchanged",
            "observation_window_contains_multiple_downstream_main_full_suites",
            "all_observed_failures_are_explicitly_classified",
            "only_observed_failure_is_unrelated_to_sample_profile",
            "unrelated_failure_has_explicit_repair_and_post_repair_green_runs",
            "closure_is_evidence_based_not_elapsed_time_based",
            "legacy_file_is_retained_after_window_closure",
            "deletion_requires_a_separate_retirement_gate",
        }
        require(
            set(criteria8ds) == expected8ds and all(criteria8ds.get(k) is True for k in expected8ds),
            "Stage 8D sample rollback closure criteria drift or fail",
            problems,
        )
        current8ds = close8ds.get("current_evidence") or {}
        require(
            current8ds.get("legacy_present") is True
            and current8ds.get("runtime_authority") is False
            and current8ds.get("legacy_reference_class") == "HISTORICAL_GUARDS_AND_SNAPSHOT_GENERATORS_ONLY"
            and current8ds.get("legacy_byte_unchanged_since_cutover") is True
            and current8ds.get("canonical_legacy_module_parity") is True
            and current8ds.get("active_consumer_count") == 0
            and current8ds.get("external_effect_authority_unchanged") is True,
            "Stage 8D sample rollback closure current evidence drift",
            problems,
        )
        observation8ds = close8ds.get("observation_window") or {}
        failures8ds = observation8ds.get("classified_failures") or []
        require(
            observation8ds.get("basis") == "DOWNSTREAM_MAIN_FULL_SUITE_AND_CONSUMER_STABILITY"
            and observation8ds.get("elapsed_time_is_not_closure_authority") is True
            and observation8ds.get("main_push_run_count") == 18
            and observation8ds.get("success_count") == 17
            and observation8ds.get("failure_count") == 1
            and len(observation8ds.get("runs") or []) == 18
            and observation8ds.get("post_repair_success_count") == 10
            and observation8ds.get("latest_main_full_suite_success") is True,
            "Stage 8D sample rollback observation evidence drift",
            problems,
        )
        require(
            len(failures8ds) == 1
            and failures8ds[0].get("workflow_run_id") == 37218152953
            and failures8ds[0].get("failed_sensor") == "check-vfresearch.py"
            and failures8ds[0].get("sample_profile_related") is False
            and failures8ds[0].get("repair_pr") == 519
            and failures8ds[0].get("repair_merge_sha") == "b46f0414613c1e957ea9f3f0d34ad0ba82ccdf93",
            "Stage 8D sample rollback failure classification drift",
            problems,
        )
        rollback8ds = close8ds.get("rollback_window") or {}
        require(
            rollback8ds.get("was_open_in_stage8c_receipt") is True
            and rollback8ds.get("was_open_in_post_migration_baseline") is True
            and rollback8ds.get("closure_evidence") == "this_receipt"
            and rollback8ds.get("closed") is True,
            "Stage 8D sample rollback window was not explicitly closed by evidence",
            problems,
        )
        require(
            close8ds.get("rollback_window_closed") is True
            and close8ds.get("retirement_ready_for_deletion_gate") is True
            and close8ds.get("delete_authorized") is False
            and close8ds.get("retirement_authorized") is False,
            "Stage 8D sample closure must not authorize deletion",
            problems,
        )
        authority8ds = close8ds.get("authority") or {}
        require(
            authority8ds.get("external_effect_authority_changed") is False
            and authority8ds.get("policy_registry_sha256") == authority8ds.get("stage8c_policy_registry_sha256"),
            "Stage 8D sample rollback closure changed authority",
            problems,
        )
        constraints8ds = set(close8ds.get("constraints") or [])
        require(
            {
                "closure evidence does not itself authorize deletion",
                "legacy sample remains present in this change",
                "no big-bang delete",
                "retirement must be isolated to sample_profile",
                "external-effect authority must remain unchanged",
            } <= constraints8ds,
            "Stage 8D sample rollback closure safety constraints drift",
            problems,
        )
        if STAGE8D_SAMPLE_ROLLBACK_CLOSURE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated8ds = Path(td) / "stage8d-sample-profile-rollback-closure.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_SAMPLE_ROLLBACK_CLOSURE_GENERATOR),
                        "--prepared-against", close8ds["prepared_against_main_sha"],
                        "--captured-at", close8ds["captured_at"],
                        "--output", str(regenerated8ds),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D sample rollback closure regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated8ds.is_file():
                    require(
                        regenerated8ds.read_bytes() == STAGE8D_SAMPLE_ROLLBACK_CLOSURE.read_bytes(),
                        "Stage 8D sample rollback closure receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_SAMPLE_CONSUMER_CORRECTION.is_file():
        fix8ds = load(STAGE8D_SAMPLE_CONSUMER_CORRECTION)
        require(
            fix8ds.get("schema") == "velvetos.stage8d-sample-profile-consumer-correction.v1"
            and fix8ds.get("stage") == "8D_SAMPLE_PROFILE_CONSUMER_CORRECTION"
            and fix8ds.get("behavior_change") is True
            and fix8ds.get("surface_id") == "sample_profile"
            and fix8ds.get("repository_assessment") == "PASS",
            "Stage 8D sample consumer correction metadata drift",
            problems,
        )
        discovery8ds = fix8ds.get("discovery") or {}
        require(
            discovery8ds.get("previous_closure_pull_request") == 529
            and discovery8ds.get("scan_blind_spot") == "LEGACY_PATH_ASSEMBLED_FROM_PATH_SEGMENTS"
            and discovery8ds.get("hidden_consumer") == "scripts/check-public-cta.py"
            and discovery8ds.get("prepared_against_active_semantic_refs") == ["scripts/check-public-cta.py"],
            "Stage 8D sample hidden-consumer discovery drift",
            problems,
        )
        correction8ds = fix8ds.get("correction") or {}
        require(
            correction8ds.get("hidden_consumer_migrated") is True
            and correction8ds.get("canonical_instance_validation_retained") is True
            and correction8ds.get("active_semantic_legacy_refs_after") == []
            and correction8ds.get("legacy_present_after_correction") is True
            and correction8ds.get("legacy_unchanged") is True
            and correction8ds.get("canonical_legacy_module_parity") is True,
            "Stage 8D sample hidden-consumer correction drift",
            problems,
        )
        rollback_fix8ds = fix8ds.get("rollback_window") or {}
        require(
            rollback_fix8ds.get("previous_closure_receipt_preserved") is True
            and rollback_fix8ds.get("previous_closure_superseded_for_retirement") is True
            and rollback_fix8ds.get("reopened") is True
            and rollback_fix8ds.get("closed") is False
            and rollback_fix8ds.get("closure_evidence") is None
            and rollback_fix8ds.get("reclosure_requires_fresh_downstream_main_full_suite_observation") is True,
            "Stage 8D sample rollback window must be reopened after hidden-consumer discovery",
            problems,
        )
        expected_fix8ds = {
            "historical_stage8c_receipt_is_preserved",
            "pr529_closure_receipt_is_preserved_as_historical_evidence",
            "hidden_consumer_is_detected_by_semantic_scan",
            "hidden_consumer_is_migrated_to_canonical_instance_only",
            "no_active_semantic_legacy_sample_consumers_remain",
            "legacy_sample_remains_present_and_unchanged",
            "canonical_legacy_module_parity_is_preserved",
            "external_effect_authority_is_unchanged",
            "previous_rollback_closure_is_superseded_not_used_for_deletion",
            "rollback_window_is_reopened_for_fresh_downstream_observation",
            "delete_authority_remains_false",
        }
        criteria_fix8ds = fix8ds.get("acceptance_criteria") or {}
        require(
            set(criteria_fix8ds) == expected_fix8ds
            and all(criteria_fix8ds.get(k) is True for k in expected_fix8ds),
            "Stage 8D sample consumer correction criteria drift or fail",
            problems,
        )
        require(
            fix8ds.get("rollback_window_closed") is False
            and fix8ds.get("retirement_ready_for_deletion_gate") is False
            and fix8ds.get("delete_authorized") is False
            and fix8ds.get("retirement_authorized") is False,
            "Stage 8D sample correction must block retirement",
            problems,
        )
        authority_fix8ds = fix8ds.get("authority") or {}
        require(
            authority_fix8ds.get("external_effect_authority_changed") is False
            and authority_fix8ds.get("policy_registry_sha256")
            == authority_fix8ds.get("prepared_against_policy_registry_sha256"),
            "Stage 8D sample consumer correction changed authority",
            problems,
        )
        current_public_cta = (ROOT / "scripts" / "check-public-cta.py").read_text(encoding="utf-8")
        require(
            "sample_path" not in current_public_cta
            and "packages/velvetos/samples/velvet-factory.json" not in current_public_cta,
            "public CTA sensor reintroduced the legacy sample consumer",
            problems,
        )
        if STAGE8D_SAMPLE_CONSUMER_CORRECTION_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated_fix8ds = Path(td) / "stage8d-sample-profile-consumer-correction.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_SAMPLE_CONSUMER_CORRECTION_GENERATOR),
                        "--prepared-against", fix8ds["prepared_against_main_sha"],
                        "--source-commit", fix8ds["source_commit_sha"],
                        "--captured-at", fix8ds["captured_at"],
                        "--output", str(regenerated_fix8ds),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D sample consumer correction regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated_fix8ds.is_file():
                    require(
                        regenerated_fix8ds.read_bytes() == STAGE8D_SAMPLE_CONSUMER_CORRECTION.read_bytes(),
                        "Stage 8D sample consumer correction receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_SAMPLE_ROLLBACK_RECLOSURE.is_file():
        reclose8ds = load(STAGE8D_SAMPLE_ROLLBACK_RECLOSURE)
        require(
            reclose8ds.get("schema") == "velvetos.stage8d-sample-profile-rollback-reclosure.v2"
            and reclose8ds.get("stage") == "8D_SAMPLE_PROFILE_ROLLBACK_RECLOSURE"
            and reclose8ds.get("behavior_change") is False
            and reclose8ds.get("surface_id") == "sample_profile"
            and reclose8ds.get("repository_assessment") == "PASS",
            "Stage 8D sample rollback re-closure metadata drift",
            problems,
        )
        supersession8ds = reclose8ds.get("supersession") or {}
        require(
            supersession8ds.get("historical_closure_receipt")
            == "packages/velvetos/policy/reports/stage8d-sample-profile-rollback-closure.json"
            and supersession8ds.get("historical_closure_preserved") is True
            and supersession8ds.get("historical_closure_superseded_for_current_retirement_authority") is True
            and supersession8ds.get("correction_receipt")
            == "packages/velvetos/policy/reports/stage8d-sample-profile-consumer-correction.json"
            and supersession8ds.get("correction_pull_request") == 531,
            "Stage 8D sample re-closure supersession chain drift",
            problems,
        )
        evidence8ds = reclose8ds.get("current_evidence") or {}
        require(
            evidence8ds.get("legacy_present") is True
            and evidence8ds.get("runtime_authority") is False
            and evidence8ds.get("active_semantic_legacy_consumer_count") == 0
            and evidence8ds.get("semantic_preflight_clear") is True
            and evidence8ds.get("all_stage8d_semantic_preflights_clear") is True
            and evidence8ds.get("legacy_byte_unchanged_since_correction") is True
            and evidence8ds.get("canonical_legacy_module_parity") is True
            and evidence8ds.get("external_effect_authority_unchanged") is True,
            "Stage 8D sample re-closure current evidence drift",
            problems,
        )
        observations8ds = reclose8ds.get("observation_window") or {}
        runs8ds = observations8ds.get("runs") or []
        require(
            observations8ds.get("basis") == "FRESH_POST_CORRECTION_DOWNSTREAM_MAIN_FULL_SUITE_AND_SEMANTIC_STABILITY"
            and observations8ds.get("elapsed_time_is_not_closure_authority") is True
            and observations8ds.get("main_push_run_count") == 6
            and observations8ds.get("success_count") == 6
            and observations8ds.get("failure_count") == 0
            and len(runs8ds) == 6
            and len({row.get("sha") for row in runs8ds}) == 6
            and all(row.get("conclusion") == "success" for row in runs8ds)
            and observations8ds.get("all_descend_from_correction") is True
            and observations8ds.get("monotonic_main_lineage") is True
            and observations8ds.get("latest_main_full_suite_success") is True,
            "Stage 8D sample re-closure observation window drift",
            problems,
        )
        rollback_reclose8ds = reclose8ds.get("rollback_window") or {}
        require(
            rollback_reclose8ds.get("reopened_by_correction") is True
            and rollback_reclose8ds.get("closure_evidence") == "this_receipt"
            and rollback_reclose8ds.get("closed") is True
            and reclose8ds.get("rollback_window_closed") is True
            and reclose8ds.get("retirement_ready_for_deletion_gate") is True
            and reclose8ds.get("delete_authorized") is False
            and reclose8ds.get("retirement_authorized") is False,
            "Stage 8D sample re-closure must close rollback without authorizing deletion",
            problems,
        )
        criteria_reclose8ds = reclose8ds.get("acceptance_criteria") or {}
        require(
            len(criteria_reclose8ds) == 16
            and all(value is True for value in criteria_reclose8ds.values()),
            "Stage 8D sample re-closure criteria drift or fail",
            problems,
        )
        authority_reclose8ds = reclose8ds.get("authority") or {}
        require(
            authority_reclose8ds.get("external_effect_authority_changed") is False
            and authority_reclose8ds.get("policy_registry_sha256")
            == authority_reclose8ds.get("sample_correction_policy_registry_sha256"),
            "Stage 8D sample re-closure changed external-effect authority",
            problems,
        )
        if STAGE8D_SAMPLE_ROLLBACK_RECLOSURE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated_reclose8ds = Path(td) / "stage8d-sample-profile-rollback-reclosure.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_SAMPLE_ROLLBACK_RECLOSURE_GENERATOR),
                        "--prepared-against", reclose8ds["prepared_against_main_sha"],
                        "--captured-at", reclose8ds["captured_at"],
                        "--output", str(regenerated_reclose8ds),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=180,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D sample rollback re-closure regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated_reclose8ds.is_file():
                    require(
                        regenerated_reclose8ds.read_bytes() == STAGE8D_SAMPLE_ROLLBACK_RECLOSURE.read_bytes(),
                        "Stage 8D sample rollback re-closure receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_SAMPLE_DELETION_GATE.is_file():
        gate8ds = load(STAGE8D_SAMPLE_DELETION_GATE)
        require(
            gate8ds.get("schema") == "velvetos.stage8d-sample-profile-deletion-gate.v1"
            and gate8ds.get("stage") == "8D_SAMPLE_PROFILE_DELETION_GATE"
            and gate8ds.get("behavior_change") is False
            and gate8ds.get("surface_id") == "sample_profile"
            and gate8ds.get("repository_assessment") == "PASS",
            "Stage 8D sample deletion gate metadata drift",
            problems,
        )
        target_gate8ds = gate8ds.get("target") or {}
        require(
            target_gate8ds.get("legacy_path") == "packages/velvetos/samples/velvet-factory.json"
            and target_gate8ds.get("canonical_path") == "instances/velvet-factory/instance/velvet-factory.json"
            and target_gate8ds.get("delete_exactly") == ["packages/velvetos/samples/velvet-factory.json"]
            and target_gate8ds.get("delete_other_surfaces") is False,
            "Stage 8D sample deletion target drift",
            problems,
        )
        prereq_gate8ds = gate8ds.get("prerequisite_closure") or {}
        require(
            prereq_gate8ds.get("receipt")
            == "packages/velvetos/policy/reports/stage8d-sample-profile-rollback-reclosure.json"
            and prereq_gate8ds.get("schema") == "velvetos.stage8d-sample-profile-rollback-reclosure.v2"
            and prereq_gate8ds.get("rollback_window_closed") is True
            and prereq_gate8ds.get("retirement_ready_for_deletion_gate") is True,
            "Stage 8D sample deletion gate closure prerequisite drift",
            problems,
        )
        cross_gate8ds = gate8ds.get("cross_surface_state") or {}
        require(
            sorted(cross_gate8ds) == sorted([
                "sample_profile", "root_desk", "fleet", "tool_status", "chatgpt_core_bundle"
            ])
            and all(
                row.get("repository_assessment") == "PASS"
                and row.get("rollback_window_closed") is True
                and row.get("retirement_ready_for_deletion_gate") is True
                and row.get("delete_authorized") is False
                and row.get("retirement_authorized") is False
                for row in cross_gate8ds.values()
            ),
            "Stage 8D sample deletion gate cross-surface prerequisite drift",
            problems,
        )
        evidence_gate8ds = gate8ds.get("current_evidence") or {}
        compat_gate8ds = evidence_gate8ds.get("compatibility_metadata_excluded_from_canonical_coverage") or {}
        require(
            evidence_gate8ds.get("legacy_present") is True
            and evidence_gate8ds.get("runtime_authority") is False
            and evidence_gate8ds.get("active_semantic_legacy_consumer_count") == 0
            and evidence_gate8ds.get("semantic_preflight_clear") is True
            and evidence_gate8ds.get("all_stage8d_semantic_preflights_clear") is True
            and compat_gate8ds.get("role") == "sample"
            and "Reference profile hosted in VelvetOS Core for sensors/compat" in str(compat_gate8ds.get("notes"))
            and evidence_gate8ds.get("canonical_semantically_covers_legacy_business_config") is True
            and evidence_gate8ds.get("canonical_legacy_module_parity") is True
            and evidence_gate8ds.get("external_effect_authority_unchanged") is True,
            "Stage 8D sample deletion gate current evidence drift",
            problems,
        )
        restore_gate8ds = gate8ds.get("restore_anchor") or {}
        require(
            restore_gate8ds.get("source_commit_sha") == gate8ds.get("prepared_against_main_sha")
            and restore_gate8ds.get("legacy_path") == "packages/velvetos/samples/velvet-factory.json"
            and restore_gate8ds.get("git_blob_sha1") == "7ffc401ef4ce87acd25c48a2d095ab82eca8f76b"
            and restore_gate8ds.get("sha256") == "01a792c229721fa95590636a645aab8d46439d6efd523c48b6ee6b73ca366f5d"
            and restore_gate8ds.get("size_bytes") == 5214
            and restore_gate8ds.get("restore_command")
            == "git show 495a6c91e8dea4b65dacf415be42aa22fc471ae4:packages/velvetos/samples/velvet-factory.json > packages/velvetos/samples/velvet-factory.json",
            "Stage 8D sample deletion restore anchor drift",
            problems,
        )
        ci_gate8ds = gate8ds.get("latest_main_ci") or {}
        require(
            ci_gate8ds.get("workflow") == "VelvetOS Core Sensors"
            and ci_gate8ds.get("run_id") == 37277013397
            and ci_gate8ds.get("sha") == "495a6c91e8dea4b65dacf415be42aa22fc471ae4"
            and ci_gate8ds.get("event") == "push"
            and ci_gate8ds.get("conclusion") == "success",
            "Stage 8D sample deletion gate latest-main CI evidence drift",
            problems,
        )
        criteria_gate8ds = gate8ds.get("acceptance_criteria") or {}
        require(
            len(criteria_gate8ds) == 16
            and all(value is True for value in criteria_gate8ds.values()),
            "Stage 8D sample deletion gate criteria drift or fail",
            problems,
        )
        authority_gate8ds = gate8ds.get("authority") or {}
        require(
            authority_gate8ds.get("external_effect_authority_changed") is False
            and authority_gate8ds.get("policy_registry_sha256")
            == authority_gate8ds.get("sample_reclosure_policy_registry_sha256")
            and authority_gate8ds.get("delete_authorized") is True
            and authority_gate8ds.get("delete_authorized_surface") == "sample_profile"
            and authority_gate8ds.get("delete_authorized_paths")
            == ["packages/velvetos/samples/velvet-factory.json"]
            and authority_gate8ds.get("retirement_authorized") is False
            and gate8ds.get("delete_authorized") is True
            and gate8ds.get("deletion_performed") is False
            and gate8ds.get("retirement_authorized") is False,
            "Stage 8D sample deletion gate authority drift",
            problems,
        )
        if STAGE8D_SAMPLE_DELETION_GATE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated_gate8ds = Path(td) / "stage8d-sample-profile-deletion-gate.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_SAMPLE_DELETION_GATE_GENERATOR),
                        "--prepared-against", gate8ds["prepared_against_main_sha"],
                        "--captured-at", gate8ds["captured_at"],
                        "--output", str(regenerated_gate8ds),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=180,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D sample deletion gate regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated_gate8ds.is_file():
                    require(
                        regenerated_gate8ds.read_bytes() == STAGE8D_SAMPLE_DELETION_GATE.read_bytes(),
                        "Stage 8D sample deletion gate receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_ROOT_DESK_RUNTIME_CORRECTION.is_file():
        fix8dr = load(STAGE8D_ROOT_DESK_RUNTIME_CORRECTION)
        require(
            fix8dr.get("schema") == "velvetos.stage8d-root-desk-runtime-consumer-correction.v1"
            and fix8dr.get("stage") == "8D_ROOT_DESK_RUNTIME_CONSUMER_CORRECTION"
            and fix8dr.get("behavior_change") is True
            and fix8dr.get("surface_id") == "root_desk"
            and fix8dr.get("repository_assessment") == "PASS",
            "Stage 8D root-desk runtime correction metadata drift",
            problems,
        )
        criteria8dr = fix8dr.get("acceptance_criteria") or {}
        require(
            bool(criteria8dr) and all(value is True for value in criteria8dr.values()),
            "Stage 8D root-desk runtime correction criteria drift or fail",
            problems,
        )
        migration8dr = fix8dr.get("migration") or {}
        readers8dr = migration8dr.get("runtime_readers") or {}
        require(
            migration8dr.get("runtime_consumers_migrated") is True
            and migration8dr.get("legacy_present") is True
            and migration8dr.get("legacy_byte_unchanged") is True
            and len(readers8dr) == 10
            and all(
                row.get("uses_instance_surface_resolver") is True
                and row.get("direct_root_legacy_read") is False
                for row in readers8dr.values()
            ),
            "Stage 8D root-desk reader migration drift",
            problems,
        )
        parity8dr = fix8dr.get("operational_parity") or {}
        require(
            parity8dr.get("legacy_tool_count") == 18
            and parity8dr.get("canonical_tool_count") >= 18
            and parity8dr.get("legacy_seat_count") == 6
            and parity8dr.get("canonical_seat_count") >= 6
            and parity8dr.get("legacy_specialist_count") == 38
            and parity8dr.get("canonical_specialist_count") >= 38
            and parity8dr.get("tools_equal_by_id") is True
            and parity8dr.get("seats_equal_by_id") is True
            and parity8dr.get("specialists_equal_by_slug") is True
            and parity8dr.get("skills_superset") is True
            and parity8dr.get("notes_superset") is True,
            "Stage 8D root-desk operational parity drift",
            problems,
        )
        sem8dr = fix8dr.get("semantic_audit") or {}
        require(
            sem8dr.get("retirement_preflight_clear") is True
            and sem8dr.get("remaining_blockers") == [],
            "Stage 8D root-desk semantic preflight is not clear",
            problems,
        )
        rollback8dr = fix8dr.get("rollback") or {}
        require(
            rollback8dr.get("window_open") is True
            and rollback8dr.get("closure_evidence") is None
            and rollback8dr.get("retirement_ready_for_deletion_gate") is False
            and rollback8dr.get("delete_authorized") is False
            and fix8dr.get("retirement_authorized") is False
            and fix8dr.get("delete_authorized") is False,
            "Stage 8D root-desk correction must not close rollback or authorize deletion",
            problems,
        )
        authority8dr = fix8dr.get("authority") or {}
        require(
            authority8dr.get("external_effect_authority_changed") is False
            and authority8dr.get("policy_registry_sha256")
            == authority8dr.get("prepared_against_policy_registry_sha256"),
            "Stage 8D root-desk correction changed external-effect authority",
            problems,
        )
        if STAGE8D_ROOT_DESK_RUNTIME_CORRECTION_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated_fix8dr = Path(td) / "stage8d-root-desk-runtime-consumer-correction.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_ROOT_DESK_RUNTIME_CORRECTION_GENERATOR),
                        "--prepared-against", fix8dr["prepared_against_main_sha"],
                        "--source-commit", fix8dr["source_commit_sha"],
                        "--captured-at", fix8dr["captured_at"],
                        "--output", str(regenerated_fix8dr),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D root-desk runtime correction regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated_fix8dr.is_file():
                    require(
                        regenerated_fix8dr.read_bytes() == STAGE8D_ROOT_DESK_RUNTIME_CORRECTION.read_bytes(),
                        "Stage 8D root-desk runtime correction receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_ROOT_DESK_ROLLBACK_CLOSURE.is_file():
        close8dr = load(STAGE8D_ROOT_DESK_ROLLBACK_CLOSURE)
        require(
            close8dr.get("schema") == "velvetos.stage8d-root-desk-rollback-closure.v1"
            and close8dr.get("stage") == "8D_ROOT_DESK_ROLLBACK_CLOSURE"
            and close8dr.get("behavior_change") is False
            and close8dr.get("surface_id") == "root_desk"
            and close8dr.get("repository_assessment") == "PASS",
            "Stage 8D root-desk rollback closure metadata drift",
            problems,
        )
        correction_close8dr = close8dr.get("correction") or {}
        require(
            correction_close8dr.get("receipt")
            == "packages/velvetos/policy/reports/stage8d-root-desk-runtime-consumer-correction.json"
            and correction_close8dr.get("pull_request") == 533
            and correction_close8dr.get("merge_sha") == "a6f74bcd3fe9cd9b4c116df1dbc2a06b09519634",
            "Stage 8D root-desk closure correction binding drift",
            problems,
        )
        evidence_close8dr = close8dr.get("current_evidence") or {}
        readers_close8dr = evidence_close8dr.get("runtime_readers") or {}
        require(
            evidence_close8dr.get("legacy_present") is True
            and evidence_close8dr.get("runtime_authority") is False
            and evidence_close8dr.get("runtime_reader_count") == 10
            and len(readers_close8dr) == 10
            and all(
                row.get("uses_instance_surface_resolver") is True
                and row.get("direct_root_legacy_read") is False
                for row in readers_close8dr.values()
            )
            and evidence_close8dr.get("semantic_preflight_clear") is True
            and evidence_close8dr.get("all_stage8d_semantic_preflights_clear") is True
            and evidence_close8dr.get("legacy_byte_unchanged_since_correction") is True
            and evidence_close8dr.get("legacy_tool_count") == 18
            and evidence_close8dr.get("canonical_tool_count") >= 18
            and evidence_close8dr.get("legacy_seat_count") == 6
            and evidence_close8dr.get("canonical_seat_count") >= 6
            and evidence_close8dr.get("legacy_specialist_count") == 38
            and evidence_close8dr.get("canonical_specialist_count") >= 38
            and evidence_close8dr.get("tools_equal_by_id") is True
            and evidence_close8dr.get("seats_equal_by_id") is True
            and evidence_close8dr.get("specialists_equal_by_slug") is True
            and evidence_close8dr.get("skills_superset") is True
            and evidence_close8dr.get("nonfleet_notes_preserved") is True
            and evidence_close8dr.get("fleet_note_semantically_superseded") is True
            and evidence_close8dr.get("fleet_correction_receipt")
            == "packages/velvetos/policy/reports/stage8d-fleet-runtime-consumer-correction.json"
            and evidence_close8dr.get("external_effect_authority_unchanged") is True,
            "Stage 8D root-desk closure current evidence drift",
            problems,
        )
        observations_close8dr = close8dr.get("observation_window") or {}
        runs_close8dr = observations_close8dr.get("runs") or []
        require(
            observations_close8dr.get("basis") == "POST_CORRECTION_DOWNSTREAM_MAIN_FULL_SUITE_AND_SEMANTIC_STABILITY"
            and observations_close8dr.get("elapsed_time_is_not_closure_authority") is True
            and observations_close8dr.get("verified_main_head_run_count") == 7
            and observations_close8dr.get("workflow_events") == ["push", "workflow_dispatch"]
            and observations_close8dr.get("success_count") == 7
            and observations_close8dr.get("failure_count") == 0
            and len(runs_close8dr) == 7
            and len({row.get("sha") for row in runs_close8dr}) == 7
            and all(row.get("conclusion") == "success" for row in runs_close8dr)
            and runs_close8dr[-1].get("id") == 37269731921
            and runs_close8dr[-1].get("additional_successful_run_ids") == [37269817015]
            and observations_close8dr.get("all_descend_from_correction") is True
            and observations_close8dr.get("monotonic_main_lineage") is True
            and observations_close8dr.get("latest_main_full_suite_success") is True,
            "Stage 8D root-desk closure observation window drift",
            problems,
        )
        rollback_close8dr = close8dr.get("rollback_window") or {}
        require(
            rollback_close8dr.get("was_open_in_correction_receipt") is True
            and rollback_close8dr.get("closure_evidence") == "this_receipt"
            and rollback_close8dr.get("closed") is True
            and close8dr.get("rollback_window_closed") is True
            and close8dr.get("retirement_ready_for_deletion_gate") is True
            and close8dr.get("delete_authorized") is False
            and close8dr.get("retirement_authorized") is False,
            "Stage 8D root-desk closure must close rollback without authorizing deletion",
            problems,
        )
        criteria_close8dr = close8dr.get("acceptance_criteria") or {}
        require(
            len(criteria_close8dr) == 20
            and all(value is True for value in criteria_close8dr.values()),
            "Stage 8D root-desk closure criteria drift or fail",
            problems,
        )
        authority_close8dr = close8dr.get("authority") or {}
        require(
            authority_close8dr.get("external_effect_authority_changed") is False
            and authority_close8dr.get("policy_registry_sha256")
            == authority_close8dr.get("root_desk_correction_policy_registry_sha256"),
            "Stage 8D root-desk closure changed external-effect authority",
            problems,
        )
        if STAGE8D_ROOT_DESK_ROLLBACK_CLOSURE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated_close8dr = Path(td) / "stage8d-root-desk-rollback-closure.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_ROOT_DESK_ROLLBACK_CLOSURE_GENERATOR),
                        "--prepared-against", close8dr["prepared_against_main_sha"],
                        "--captured-at", close8dr["captured_at"],
                        "--output", str(regenerated_close8dr),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=180,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D root-desk rollback closure regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated_close8dr.is_file():
                    require(
                        regenerated_close8dr.read_bytes() == STAGE8D_ROOT_DESK_ROLLBACK_CLOSURE.read_bytes(),
                        "Stage 8D root-desk rollback closure receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_FLEET_RUNTIME_CORRECTION.is_file():
        fix8df = load(STAGE8D_FLEET_RUNTIME_CORRECTION)
        require(
            fix8df.get("schema") == "velvetos.stage8d-fleet-runtime-consumer-correction.v2"
            and fix8df.get("stage") == "8D_FLEET_RUNTIME_CONSUMER_CORRECTION"
            and fix8df.get("behavior_change") is True
            and fix8df.get("surface_id") == "fleet"
            and fix8df.get("repository_assessment") == "PASS",
            "Stage 8D fleet runtime correction metadata drift",
            problems,
        )
        criteria8df = fix8df.get("acceptance_criteria") or {}
        require(
            bool(criteria8df) and all(value is True for value in criteria8df.values()),
            "Stage 8D fleet runtime correction criteria drift or fail",
            problems,
        )
        migration8df = fix8df.get("migration") or {}
        require(
            migration8df.get("runtime_consumers_migrated") is True
            and migration8df.get("legacy_present") is True
            and migration8df.get("legacy_byte_unchanged") is True
            and migration8df.get("canonical_legacy_parity") is True
            and len(migration8df.get("migrated_code") or []) == 4
            and all((migration8df.get("active_documentation") or {}).values()),
            "Stage 8D fleet migration/parity drift",
            problems,
        )
        sem8df = fix8df.get("semantic_audit") or {}
        require(
            sem8df.get("retirement_preflight_clear") is True
            and sem8df.get("remaining_blockers") == []
            and sorted(sem8df.get("negative_controls") or []) == sorted([
                "packages/velvetos/living-studio/tests/test_living_studio.py",
                "packages/velvetos_control_api/tests/test_control_api.py",
            ])
            and sem8df.get("retained_legacy_surface_references") == [".cursor/vf-desk.json"],
            "Stage 8D fleet semantic correction drift",
            problems,
        )
        rollback8df = fix8df.get("rollback") or {}
        require(
            rollback8df.get("window_open") is True
            and rollback8df.get("closure_evidence") is None
            and rollback8df.get("retirement_ready_for_deletion_gate") is False
            and rollback8df.get("delete_authorized") is False
            and fix8df.get("retirement_authorized") is False
            and fix8df.get("delete_authorized") is False,
            "Stage 8D fleet correction must not close rollback or authorize deletion",
            problems,
        )
        authority8df = fix8df.get("authority") or {}
        require(
            authority8df.get("external_effect_authority_changed") is False
            and authority8df.get("policy_registry_sha256")
            == authority8df.get("prepared_against_policy_registry_sha256"),
            "Stage 8D fleet correction changed external-effect authority",
            problems,
        )
        if STAGE8D_FLEET_RUNTIME_CORRECTION_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated_fix8df = Path(td) / "stage8d-fleet-runtime-consumer-correction.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_FLEET_RUNTIME_CORRECTION_GENERATOR),
                        "--prepared-against", fix8df["prepared_against_main_sha"],
                        "--source-commit", fix8df["source_commit_sha"],
                        "--captured-at", fix8df["captured_at"],
                        "--output", str(regenerated_fix8df),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D fleet runtime correction regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated_fix8df.is_file():
                    require(
                        regenerated_fix8df.read_bytes() == STAGE8D_FLEET_RUNTIME_CORRECTION.read_bytes(),
                        "Stage 8D fleet runtime correction receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_FLEET_ROLLBACK_CLOSURE.is_file():
        close8df = load(STAGE8D_FLEET_ROLLBACK_CLOSURE)
        require(
            close8df.get("schema") == "velvetos.stage8d-fleet-rollback-closure.v1"
            and close8df.get("stage") == "8D_FLEET_ROLLBACK_CLOSURE"
            and close8df.get("behavior_change") is False
            and close8df.get("surface_id") == "fleet"
            and close8df.get("repository_assessment") == "PASS",
            "Stage 8D fleet rollback closure metadata drift",
            problems,
        )
        correction_close8df = close8df.get("correction") or {}
        require(
            correction_close8df.get("receipt")
            == "packages/velvetos/policy/reports/stage8d-fleet-runtime-consumer-correction.json"
            and correction_close8df.get("pull_request") == 534
            and correction_close8df.get("merge_sha") == "027700b3077bc900658313186e313772f539bd7d",
            "Stage 8D fleet closure correction binding drift",
            problems,
        )
        evidence_close8df = close8df.get("current_evidence") or {}
        migrated_close8df = evidence_close8df.get("migrated_code") or {}
        docs_close8df = evidence_close8df.get("active_documentation") or {}
        require(
            evidence_close8df.get("legacy_present") is True
            and evidence_close8df.get("runtime_authority") is False
            and len(migrated_close8df) == 4
            and all(
                row.get("legacy_path_absent") is True
                and row.get("canonical_fleet_binding_present") is True
                for row in migrated_close8df.values()
            )
            and len(docs_close8df) == 7
            and all(row.get("legacy_path_absent") is True for row in docs_close8df.values())
            and evidence_close8df.get("semantic_preflight_clear") is True
            and evidence_close8df.get("all_stage8d_semantic_preflights_clear") is True
            and evidence_close8df.get("legacy_byte_unchanged_since_correction") is True
            and evidence_close8df.get("canonical_legacy_exact_equal") is True
            and evidence_close8df.get("printer_count") == 4
            and evidence_close8df.get("external_effect_authority_unchanged") is True,
            "Stage 8D fleet closure current evidence drift",
            problems,
        )
        observations_close8df = close8df.get("observation_window") or {}
        runs_close8df = observations_close8df.get("runs") or []
        require(
            observations_close8df.get("basis") == "POST_CORRECTION_EXACT_MAIN_HEAD_FULL_SUITE_AND_SEMANTIC_STABILITY"
            and observations_close8df.get("elapsed_time_is_not_closure_authority") is True
            and observations_close8df.get("verified_main_head_run_count") == 8
            and observations_close8df.get("workflow_events") == ["push", "workflow_dispatch"]
            and observations_close8df.get("success_count") == 8
            and observations_close8df.get("failure_count") == 0
            and len(runs_close8df) == 8
            and len({row.get("sha") for row in runs_close8df}) == 8
            and all(row.get("conclusion") == "success" for row in runs_close8df)
            and runs_close8df[5].get("id") == 37269731921
            and runs_close8df[5].get("additional_successful_run_ids") == [37269817015]
            and runs_close8df[-1].get("id") == 37270881356
            and observations_close8df.get("all_descend_from_correction") is True
            and observations_close8df.get("monotonic_main_lineage") is True
            and observations_close8df.get("latest_main_full_suite_success") is True,
            "Stage 8D fleet closure observation window drift",
            problems,
        )
        rollback_close8df = close8df.get("rollback_window") or {}
        require(
            rollback_close8df.get("was_open_in_correction_receipt") is True
            and rollback_close8df.get("closure_evidence") == "this_receipt"
            and rollback_close8df.get("closed") is True
            and close8df.get("rollback_window_closed") is True
            and close8df.get("retirement_ready_for_deletion_gate") is True
            and close8df.get("delete_authorized") is False
            and close8df.get("retirement_authorized") is False,
            "Stage 8D fleet closure must close rollback without authorizing deletion",
            problems,
        )
        criteria_close8df = close8df.get("acceptance_criteria") or {}
        require(
            len(criteria_close8df) == 15
            and all(value is True for value in criteria_close8df.values()),
            "Stage 8D fleet closure criteria drift or fail",
            problems,
        )
        authority_close8df = close8df.get("authority") or {}
        require(
            authority_close8df.get("external_effect_authority_changed") is False
            and authority_close8df.get("policy_registry_sha256")
            == authority_close8df.get("fleet_correction_policy_registry_sha256"),
            "Stage 8D fleet closure changed external-effect authority",
            problems,
        )
        if STAGE8D_FLEET_ROLLBACK_CLOSURE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated_close8df = Path(td) / "stage8d-fleet-rollback-closure.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_FLEET_ROLLBACK_CLOSURE_GENERATOR),
                        "--prepared-against", close8df["prepared_against_main_sha"],
                        "--captured-at", close8df["captured_at"],
                        "--output", str(regenerated_close8df),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=180,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D fleet rollback closure regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated_close8df.is_file():
                    require(
                        regenerated_close8df.read_bytes() == STAGE8D_FLEET_ROLLBACK_CLOSURE.read_bytes(),
                        "Stage 8D fleet rollback closure receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_TOOL_STATUS_SEMANTIC_CORRECTION.is_file():
        fix8dt = load(STAGE8D_TOOL_STATUS_SEMANTIC_CORRECTION)
        require(
            fix8dt.get("schema") == "velvetos.stage8d-tool-status-semantic-correction.v1"
            and fix8dt.get("stage") == "8D_TOOL_STATUS_SEMANTIC_CORRECTION"
            and fix8dt.get("behavior_change") is False
            and fix8dt.get("surface_id") == "tool_status"
            and fix8dt.get("repository_assessment") == "PASS",
            "Stage 8D tool-status semantic correction metadata drift",
            problems,
        )
        criteria8dt = fix8dt.get("acceptance_criteria") or {}
        require(
            bool(criteria8dt) and all(value is True for value in criteria8dt.values()),
            "Stage 8D tool-status semantic correction criteria drift or fail",
            problems,
        )
        classification8dt = fix8dt.get("classification") or {}
        safe8dt = classification8dt.get("content_validated_safe_references") or {}
        require(
            classification8dt.get("retirement_preflight_clear") is True
            and classification8dt.get("remaining_blockers") == []
            and len(safe8dt) == 6,
            "Stage 8D tool-status semantic classification drift",
            problems,
        )
        parity8dt = fix8dt.get("parity") or {}
        require(
            parity8dt.get("equal") is True
            and parity8dt.get("canonical_composed_sha256")
            == parity8dt.get("legacy_sha256"),
            "Stage 8D tool-status parity drift",
            problems,
        )
        rollback8dt = fix8dt.get("rollback") or {}
        require(
            rollback8dt.get("window_open") is True
            and rollback8dt.get("closure_evidence") is None
            and rollback8dt.get("retirement_ready_for_deletion_gate") is False
            and rollback8dt.get("delete_authorized") is False
            and fix8dt.get("retirement_authorized") is False
            and fix8dt.get("delete_authorized") is False,
            "Stage 8D tool-status correction must not close rollback or authorize deletion",
            problems,
        )
        authority8dt = fix8dt.get("authority") or {}
        require(
            authority8dt.get("active_authority") == "instance:surface:toolStatus"
            and authority8dt.get("external_effect_authority_changed") is False
            and authority8dt.get("policy_registry_sha256")
            == authority8dt.get("prepared_against_policy_registry_sha256"),
            "Stage 8D tool-status correction authority drift",
            problems,
        )
        if STAGE8D_TOOL_STATUS_SEMANTIC_CORRECTION_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated_fix8dt = Path(td) / "stage8d-tool-status-semantic-correction.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_TOOL_STATUS_SEMANTIC_CORRECTION_GENERATOR),
                        "--prepared-against", fix8dt["prepared_against_main_sha"],
                        "--source-commit", fix8dt["source_commit_sha"],
                        "--captured-at", fix8dt["captured_at"],
                        "--output", str(regenerated_fix8dt),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D tool-status semantic correction regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated_fix8dt.is_file():
                    require(
                        regenerated_fix8dt.read_bytes() == STAGE8D_TOOL_STATUS_SEMANTIC_CORRECTION.read_bytes(),
                        "Stage 8D tool-status semantic correction receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_TOOL_STATUS_ROLLBACK_CLOSURE.is_file():
        close8dt = load(STAGE8D_TOOL_STATUS_ROLLBACK_CLOSURE)
        require(
            close8dt.get("schema") == "velvetos.stage8d-tool-status-rollback-closure.v1"
            and close8dt.get("stage") == "8D_TOOL_STATUS_ROLLBACK_CLOSURE"
            and close8dt.get("behavior_change") is False
            and close8dt.get("surface_id") == "tool_status"
            and close8dt.get("repository_assessment") == "PASS",
            "Stage 8D tool-status rollback closure metadata drift",
            problems,
        )
        correction_close8dt = close8dt.get("correction") or {}
        require(
            correction_close8dt.get("receipt")
            == "packages/velvetos/policy/reports/stage8d-tool-status-semantic-correction.json"
            and correction_close8dt.get("pull_request") == 536
            and correction_close8dt.get("merge_sha") == "ed183f59959b4eaebd5a092e61d4ef969e834df7",
            "Stage 8D tool-status closure correction binding drift",
            problems,
        )
        evidence_close8dt = close8dt.get("current_evidence") or {}
        safe_close8dt = evidence_close8dt.get("content_validated_safe_references") or {}
        require(
            evidence_close8dt.get("legacy_present") is True
            and evidence_close8dt.get("runtime_authority") is False
            and evidence_close8dt.get("active_authority") == "instance:surface:toolStatus"
            and evidence_close8dt.get("safe_reference_count") == 6
            and len(safe_close8dt) == 6
            and evidence_close8dt.get("semantic_preflight_clear") is True
            and evidence_close8dt.get("all_stage8d_semantic_preflights_clear") is True
            and evidence_close8dt.get("legacy_byte_unchanged_since_correction") is True
            and evidence_close8dt.get("canonical_composition_exact_equal") is True
            and evidence_close8dt.get("canonical_composed_sha256")
            == evidence_close8dt.get("legacy_sha256")
            and evidence_close8dt.get("external_effect_authority_unchanged") is True,
            "Stage 8D tool-status closure current evidence drift",
            problems,
        )
        observations_close8dt = close8dt.get("observation_window") or {}
        runs_close8dt = observations_close8dt.get("runs") or []
        require(
            observations_close8dt.get("basis") == "POST_CORRECTION_EXACT_MAIN_HEAD_FULL_SUITE_AND_SEMANTIC_STABILITY"
            and observations_close8dt.get("elapsed_time_is_not_closure_authority") is True
            and observations_close8dt.get("verified_main_head_run_count") == 7
            and observations_close8dt.get("workflow_events") == ["push"]
            and observations_close8dt.get("success_count") == 7
            and observations_close8dt.get("failure_count") == 0
            and len(runs_close8dt) == 7
            and len({row.get("sha") for row in runs_close8dt}) == 7
            and all(row.get("conclusion") == "success" for row in runs_close8dt)
            and runs_close8dt[-1].get("id") == 37272603427
            and observations_close8dt.get("all_descend_from_correction") is True
            and observations_close8dt.get("monotonic_main_lineage") is True
            and observations_close8dt.get("latest_main_full_suite_success") is True,
            "Stage 8D tool-status closure observation window drift",
            problems,
        )
        rollback_close8dt = close8dt.get("rollback_window") or {}
        require(
            rollback_close8dt.get("was_open_in_correction_receipt") is True
            and rollback_close8dt.get("closure_evidence") == "this_receipt"
            and rollback_close8dt.get("closed") is True
            and close8dt.get("rollback_window_closed") is True
            and close8dt.get("retirement_ready_for_deletion_gate") is True
            and close8dt.get("delete_authorized") is False
            and close8dt.get("retirement_authorized") is False,
            "Stage 8D tool-status closure must close rollback without authorizing deletion",
            problems,
        )
        criteria_close8dt = close8dt.get("acceptance_criteria") or {}
        require(
            len(criteria_close8dt) == 15
            and all(value is True for value in criteria_close8dt.values()),
            "Stage 8D tool-status closure criteria drift or fail",
            problems,
        )
        authority_close8dt = close8dt.get("authority") or {}
        require(
            authority_close8dt.get("active_authority") == "instance:surface:toolStatus"
            and authority_close8dt.get("external_effect_authority_changed") is False
            and authority_close8dt.get("policy_registry_sha256")
            == authority_close8dt.get("tool_status_correction_policy_registry_sha256"),
            "Stage 8D tool-status closure changed authority",
            problems,
        )
        if STAGE8D_TOOL_STATUS_ROLLBACK_CLOSURE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated_close8dt = Path(td) / "stage8d-tool-status-rollback-closure.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_TOOL_STATUS_ROLLBACK_CLOSURE_GENERATOR),
                        "--prepared-against", close8dt["prepared_against_main_sha"],
                        "--captured-at", close8dt["captured_at"],
                        "--output", str(regenerated_close8dt),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=180,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D tool-status rollback closure regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated_close8dt.is_file():
                    require(
                        regenerated_close8dt.read_bytes() == STAGE8D_TOOL_STATUS_ROLLBACK_CLOSURE.read_bytes(),
                        "Stage 8D tool-status rollback closure receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_CHATGPT_SEMANTIC_CORRECTION.is_file():
        fix8dc = load(STAGE8D_CHATGPT_SEMANTIC_CORRECTION)
        require(
            fix8dc.get("schema") == "velvetos.stage8d-chatgpt-semantic-correction.v1"
            and fix8dc.get("stage") == "8D_CHATGPT_SEMANTIC_CORRECTION"
            and fix8dc.get("behavior_change") is True
            and fix8dc.get("surface_id") == "chatgpt_core_bundle"
            and fix8dc.get("repository_assessment") == "PASS",
            "Stage 8D ChatGPT semantic correction metadata drift",
            problems,
        )
        criteria8dc = fix8dc.get("acceptance_criteria") or {}
        require(
            bool(criteria8dc) and all(value is True for value in criteria8dc.values()),
            "Stage 8D ChatGPT semantic correction criteria drift or fail",
            problems,
        )
        migration8dc = fix8dc.get("migration") or {}
        require(
            migration8dc.get("brand_asset_source_migrated") is True
            and migration8dc.get("sensor_registry_migrated") is True
            and migration8dc.get("canonical_sensor_binding_count") == 18
            and migration8dc.get("legacy_distribution_present") is True
            and migration8dc.get("legacy_tree_unchanged") is True,
            "Stage 8D ChatGPT migration metadata drift",
            problems,
        )
        parity8dc = fix8dc.get("parity") or {}
        require(
            parity8dc.get("file_count") == 33
            and parity8dc.get("file_sets_equal") is True
            and parity8dc.get("byte_equal") is True
            and parity8dc.get("mismatches") == [],
            "Stage 8D ChatGPT parity drift",
            problems,
        )
        classification8dc = fix8dc.get("classification") or {}
        require(
            classification8dc.get("retirement_preflight_clear") is True
            and classification8dc.get("remaining_blockers") == []
            and len(classification8dc.get("content_validated_safe_references") or {}) == 6,
            "Stage 8D ChatGPT semantic classification drift",
            problems,
        )
        rollback8dc = fix8dc.get("rollback") or {}
        require(
            rollback8dc.get("window_open") is True
            and rollback8dc.get("closure_evidence") is None
            and rollback8dc.get("retirement_ready_for_deletion_gate") is False
            and rollback8dc.get("delete_authorized") is False
            and fix8dc.get("retirement_authorized") is False
            and fix8dc.get("delete_authorized") is False,
            "Stage 8D ChatGPT correction must not close rollback or authorize deletion",
            problems,
        )
        authority8dc = fix8dc.get("authority") or {}
        require(
            authority8dc.get("active_authority") == "instance:surface:chatgptProject"
            and authority8dc.get("external_effect_authority_changed") is False
            and authority8dc.get("policy_registry_sha256")
            == authority8dc.get("prepared_against_policy_registry_sha256"),
            "Stage 8D ChatGPT correction authority drift",
            problems,
        )
        if STAGE8D_CHATGPT_SEMANTIC_CORRECTION_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated_fix8dc = Path(td) / "stage8d-chatgpt-semantic-correction.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_CHATGPT_SEMANTIC_CORRECTION_GENERATOR),
                        "--prepared-against", fix8dc["prepared_against_main_sha"],
                        "--source-commit", fix8dc["source_commit_sha"],
                        "--captured-at", fix8dc["captured_at"],
                        "--output", str(regenerated_fix8dc),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D ChatGPT semantic correction regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated_fix8dc.is_file():
                    require(
                        regenerated_fix8dc.read_bytes() == STAGE8D_CHATGPT_SEMANTIC_CORRECTION.read_bytes(),
                        "Stage 8D ChatGPT semantic correction receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_CHATGPT_ROLLBACK_CLOSURE.is_file():
        close8dc = load(STAGE8D_CHATGPT_ROLLBACK_CLOSURE)
        require(
            close8dc.get("schema") == "velvetos.stage8d-chatgpt-rollback-closure.v1"
            and close8dc.get("stage") == "8D_CHATGPT_ROLLBACK_CLOSURE"
            and close8dc.get("behavior_change") is False
            and close8dc.get("surface_id") == "chatgpt_core_bundle"
            and close8dc.get("repository_assessment") == "PASS",
            "Stage 8D ChatGPT rollback closure metadata drift",
            problems,
        )
        correction_close8dc = close8dc.get("correction") or {}
        require(
            correction_close8dc.get("receipt")
            == "packages/velvetos/policy/reports/stage8d-chatgpt-semantic-correction.json"
            and correction_close8dc.get("pull_request") == 538
            and correction_close8dc.get("merge_sha") == "b722f622dd2eab031c087fe051c56a5eb019d705",
            "Stage 8D ChatGPT closure correction binding drift",
            problems,
        )
        evidence_close8dc = close8dc.get("current_evidence") or {}
        safe_close8dc = evidence_close8dc.get("content_validated_safe_references") or {}
        require(
            evidence_close8dc.get("legacy_present") is True
            and evidence_close8dc.get("runtime_authority") is False
            and evidence_close8dc.get("active_authority") == "instance:surface:chatgptProject"
            and evidence_close8dc.get("file_count") == 33
            and evidence_close8dc.get("file_sets_equal") is True
            and evidence_close8dc.get("byte_equal") is True
            and evidence_close8dc.get("mismatches") == []
            and evidence_close8dc.get("legacy_tree_unchanged_since_correction") is True
            and evidence_close8dc.get("rollback_git_attributes_unchanged_since_correction") is True
            and evidence_close8dc.get("canonical_sensor_binding_count") == 18
            and evidence_close8dc.get("brand_asset_source_canonical") is True
            and evidence_close8dc.get("safe_reference_count") == 6
            and len(safe_close8dc) == 6
            and evidence_close8dc.get("semantic_preflight_clear") is True
            and evidence_close8dc.get("all_stage8d_semantic_preflights_clear") is True
            and evidence_close8dc.get("external_effect_authority_unchanged") is True,
            "Stage 8D ChatGPT closure current evidence drift",
            problems,
        )
        observations_close8dc = close8dc.get("observation_window") or {}
        runs_close8dc = observations_close8dc.get("runs") or []
        require(
            observations_close8dc.get("basis") == "POST_CORRECTION_EXACT_MAIN_HEAD_FULL_SUITE_AND_SEMANTIC_STABILITY"
            and observations_close8dc.get("elapsed_time_is_not_closure_authority") is True
            and observations_close8dc.get("verified_main_head_run_count") == 6
            and observations_close8dc.get("workflow_events") == ["push"]
            and observations_close8dc.get("success_count") == 6
            and observations_close8dc.get("failure_count") == 0
            and len(runs_close8dc) == 6
            and len({row.get("sha") for row in runs_close8dc}) == 6
            and all(row.get("conclusion") == "success" for row in runs_close8dc)
            and runs_close8dc[-1].get("id") == 37273584691
            and observations_close8dc.get("all_descend_from_correction") is True
            and observations_close8dc.get("monotonic_main_lineage") is True
            and observations_close8dc.get("latest_main_full_suite_success") is True,
            "Stage 8D ChatGPT closure observation window drift",
            problems,
        )
        rollback_close8dc = close8dc.get("rollback_window") or {}
        require(
            rollback_close8dc.get("was_open_in_correction_receipt") is True
            and rollback_close8dc.get("closure_evidence") == "this_receipt"
            and rollback_close8dc.get("closed") is True
            and close8dc.get("rollback_window_closed") is True
            and close8dc.get("retirement_ready_for_deletion_gate") is True
            and close8dc.get("delete_authorized") is False
            and close8dc.get("retirement_authorized") is False,
            "Stage 8D ChatGPT closure must close rollback without authorizing deletion",
            problems,
        )
        criteria_close8dc = close8dc.get("acceptance_criteria") or {}
        require(
            len(criteria_close8dc) == 19
            and all(value is True for value in criteria_close8dc.values()),
            "Stage 8D ChatGPT closure criteria drift or fail",
            problems,
        )
        authority_close8dc = close8dc.get("authority") or {}
        require(
            authority_close8dc.get("active_authority") == "instance:surface:chatgptProject"
            and authority_close8dc.get("external_effect_authority_changed") is False
            and authority_close8dc.get("policy_registry_sha256")
            == authority_close8dc.get("chatgpt_correction_policy_registry_sha256"),
            "Stage 8D ChatGPT closure changed authority",
            problems,
        )
        if STAGE8D_CHATGPT_ROLLBACK_CLOSURE_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated_close8dc = Path(td) / "stage8d-chatgpt-rollback-closure.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_CHATGPT_ROLLBACK_CLOSURE_GENERATOR),
                        "--prepared-against", close8dc["prepared_against_main_sha"],
                        "--captured-at", close8dc["captured_at"],
                        "--output", str(regenerated_close8dc),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=180,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D ChatGPT rollback closure regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated_close8dc.is_file():
                    require(
                        regenerated_close8dc.read_bytes() == STAGE8D_CHATGPT_ROLLBACK_CLOSURE.read_bytes(),
                        "Stage 8D ChatGPT rollback closure receipt is not reproducible",
                        problems,
                    )

    if STAGE8D_RETIREMENT_SEMANTIC_AUDIT.is_file():
        audit8d = load(STAGE8D_RETIREMENT_SEMANTIC_AUDIT)
        require(
            audit8d.get("schema") == "velvetos.stage8d-retirement-semantic-audit.v1"
            and audit8d.get("stage") == "8D_RETIREMENT_SEMANTIC_AUDIT"
            and audit8d.get("behavior_change") is False
            and audit8d.get("repository_assessment") == "PASS",
            "Stage 8D retirement semantic audit metadata drift",
            problems,
        )
        model8d = audit8d.get("audit_model") or {}
        require(
            model8d.get("exact_path_detection") is True
            and model8d.get("assembled_path_component_detection") is True
            and model8d.get("ambiguous_machine_or_config_reference_blocks_retirement") is True
            and model8d.get("cross_surface_compatibility_refs_require_correction_receipt") is True
            and model8d.get("tool_status_rollback_refs_are_content_validated") is True
            and model8d.get("chatgpt_remaining_refs_are_content_validated") is True,
            "Stage 8D retirement semantic audit model drift",
            problems,
        )
        surfaces8d = audit8d.get("compatibility_surfaces") or {}
        expected_surface_ids8d = {"sample_profile", "fleet", "root_desk", "tool_status", "chatgpt_core_bundle"}
        require(set(surfaces8d) == expected_surface_ids8d, "Stage 8D semantic audit surface set drift", problems)
        require(
            all(
                row.get("present") is True
                and row.get("rollback_window_closed_by_this_audit") is False
                and row.get("delete_authorized") is False
                for row in surfaces8d.values()
            ),
            "Stage 8D semantic audit changed retirement/delete state",
            problems,
        )
        sample_audit8d = surfaces8d.get("sample_profile") or {}
        require(
            sample_audit8d.get("retirement_preflight_clear") is True
            and sample_audit8d.get("retirement_preflight_blockers") == [],
            "Stage 8D semantic audit sample state drift",
            problems,
        )


    if STAGE8D_RETIREMENT_SEMANTIC_AUDIT.is_file():
        audit8d = load(STAGE8D_RETIREMENT_SEMANTIC_AUDIT)
        surfaces8d = audit8d.get("compatibility_surfaces") or {}
        blocked_ids8d = set()
        require(
            (surfaces8d.get("root_desk") or {}).get("retirement_preflight_clear") is True
            and (surfaces8d.get("root_desk") or {}).get("retirement_preflight_blockers") == []
            and (surfaces8d.get("fleet") or {}).get("retirement_preflight_clear") is True
            and (surfaces8d.get("fleet") or {}).get("retirement_preflight_blockers") == []
            and (surfaces8d.get("tool_status") or {}).get("retirement_preflight_clear") is True
            and (surfaces8d.get("tool_status") or {}).get("retirement_preflight_blockers") == []
            and (surfaces8d.get("chatgpt_core_bundle") or {}).get("retirement_preflight_clear") is True
            and (surfaces8d.get("chatgpt_core_bundle") or {}).get("retirement_preflight_blockers") == [],
            "Stage 8D semantic audit corrected surfaces are not clear",
            problems,
        )
        require(
            all(
                (surfaces8d.get(sid) or {}).get("retirement_preflight_clear") is False
                and bool((surfaces8d.get(sid) or {}).get("retirement_preflight_blockers"))
                for sid in blocked_ids8d
            ),
            "Stage 8D semantic audit unexpectedly cleared an uncorrected surface",
            problems,
        )
        assessment8d = audit8d.get("assessment") or {}
        require(
            assessment8d.get("surfaces_total") == 5
            and assessment8d.get("surfaces_preflight_clear") == 5
            and set(assessment8d.get("surfaces_with_candidate_blockers") or []) == blocked_ids8d
            and assessment8d.get("rollback_windows_closed_by_audit") == 0
            and assessment8d.get("deletion_authorized") is False
            and audit8d.get("retirement_authorized") is False
            and audit8d.get("deletion_authorized") is False,
            "Stage 8D semantic audit assessment drift",
            problems,
        )
        if STAGE8D_RETIREMENT_SEMANTIC_AUDIT_GENERATOR.is_file():
            with tempfile.TemporaryDirectory() as td:
                regenerated_audit8d = Path(td) / "stage8d-retirement-semantic-audit.json"
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(STAGE8D_RETIREMENT_SEMANTIC_AUDIT_GENERATOR),
                        "--source-commit", audit8d["source_commit_sha"],
                        "--captured-at", audit8d["captured_at"],
                        "--output", str(regenerated_audit8d),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                require(
                    proc.returncode == 0,
                    "Stage 8D semantic audit regeneration failed: "
                    + (proc.stderr.strip() or proc.stdout.strip()),
                    problems,
                )
                if proc.returncode == 0 and regenerated_audit8d.is_file():
                    require(
                        regenerated_audit8d.read_bytes() == STAGE8D_RETIREMENT_SEMANTIC_AUDIT.read_bytes(),
                        "Stage 8D semantic audit receipt is not reproducible",
                        problems,
                    )

    report_names = {p.name for p in REPORTS.glob("*.json")} if REPORTS.is_dir() else set()
    require(EXPECTED_REPORTS <= report_names, f"missing policy reports {sorted(EXPECTED_REPORTS-report_names)}", problems)
    if EXPECTED_REPORTS <= report_names:
        coverage = load(REPORTS / "coverage-report.json")
        sensor_graph = load(REPORTS / "sensor-coverage-graph.json")
        require(
            coverage.get("runnable_sensor_count") == coverage.get("registered_sensor_count")
            and coverage.get("runnable_sensor_count") == sensor_graph.get("sensor_count")
            and coverage.get("omitted_sensors") == [],
            "historical Stage 0 coverage report is internally inconsistent",
            problems,
        )
        authority = load(REPORTS / "authority-graph.json")
        require(authority.get("policy_count") == len(authority.get("nodes") or []), "historical authority graph policy count mismatch", problems)
        conflicts = load(REPORTS / "conflict-report.json")
        conflict_ids = {x.get("id") for x in conflicts.get("conflicts", [])}
        require("instagram-publish-split-brain" in conflict_ids, "Stage 0 publish conflict report missing", problems)
        inventory = load(REPORTS / "artifact-inventory.json")
        require(inventory.get("stage0_action") == "CLASSIFICATION_ONLY_NO_MOVE_NO_DELETE", "Stage 0 artifact action drifted", problems)
        ci = load(REPORTS / "ci-baseline.json")
        require(bool(ci.get("cutoff_utc")) and bool(ci.get("runs")), "CI baseline cutoff/runs missing", problems)
        require(ci.get("branch_protection", {}).get("state") == "UNPROTECTED", "Stage 0 branch baseline changed in report", problems)
        migration = load(REPORTS / "migration-map.json")
        require([x.get("stage") for x in migration.get("stages", [])] == list(range(1, 10)), "migration map stages must be 1..9", problems)
        generator = ROOT / "scripts" / "generate-policy-reports.py"
        require(generator.is_file(), "policy report generator missing", problems)
        if generator.is_file():
            proc = subprocess.run(
                [sys.executable, str(generator), "--check"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=60,
            )
            require(proc.returncode == 0, "policy reports not reproducible: " + (proc.stderr or proc.stdout).strip()[:500], problems)

        stage2 = load(REPORTS / "stage2-sensor-registry-audit.json")
        require(stage2.get("stage") == "2A" and stage2.get("behavior_change") is False, "Stage 2A audit metadata mismatch", problems)

        stage3_plan = load(REPORTS / "stage3-preactivation-plan.json")
        require(stage3_plan.get("stage") == 3 and stage3_plan.get("state") == "PREPARED_NOT_ACTIVE", "Stage 3 preactivation plan state mismatch", problems)
        require(stage3_plan.get("behavior_change") is False, "Stage 3 preactivation plan must not change behavior", problems)
        require(stage3_plan.get("current_selector_mode") == "shadow", "Stage 3 preactivation plan must preserve shadow mode", problems)
        require(stage3_plan.get("current_merge_authority") == "FULL_SUITE", "Stage 3 preactivation plan must preserve full-suite authority", problems)
        require(stage3_plan.get("selected_suite_runner_prepared") is True, "Stage 3 selected suite runner not prepared", problems)
        require(stage3_plan.get("current_workflow_changed") is False, "Stage 3 preactivation plan must not change workflow", problems)
        require(stage3_plan.get("branch_ruleset_mutated") is False, "Stage 3 preactivation plan must not mutate ruleset", problems)
        require(stage3_plan.get("rollback_mode") == "FULL_SUITE_REQUIRED", "Stage 3 preactivation rollback mismatch", problems)
        require((stage3_plan.get("ruleset_snapshot") or {}).get("id") == stage3.get("branch_ruleset_id"), "Stage 3 ruleset snapshot id mismatch", problems)
        require((stage3_plan.get("ruleset_snapshot") or {}).get("enforcement") == "disabled", "Stage 3 preactivation ruleset snapshot must remain disabled", problems)
        require(stage2.get("registry_matches_live") is True, "Stage 2A sensor registry does not match live sensors", problems)
        require(stage2.get("registered_sensor_count") == len(sensor_rows), "Stage 2A sensor count drift", problems)
        require(set(stage2.get("critical_always_on") or []) == expected_always_on, "Stage 2A critical ALWAYS_ON report drift", problems)
        require(stage2.get("duplicate_removal_stage") == 3, "Stage 2A duplicate removal must remain deferred to Stage 3", problems)
        audit_generator = ROOT / "scripts" / "generate-sensor-registry-audit.py"
        require(audit_generator.is_file(), "Stage 2A sensor audit generator missing", problems)
        if audit_generator.is_file():
            proc = subprocess.run(
                [sys.executable, str(audit_generator), "--check"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=30,
            )
            require(proc.returncode == 0, "Stage 2A sensor audit not reproducible: " + (proc.stderr or proc.stdout).strip()[:500], problems)

    return problems, known_policies


def diff_added_markdown(base: str, head: str) -> dict[str, list[str]]:
    proc = subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", base, head, "--", "*.md", "*.mdc"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise ValueError(proc.stderr.strip() or "git diff failed")
    current: str | None = None
    added: dict[str, list[str]] = {}
    for line in proc.stdout.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            added.setdefault(current, [])
        elif current and line.startswith("+") and not line.startswith("+++"):
            added[current].append(line[1:])
    return added

def is_normative_external(line: str) -> bool:
    return bool(RESERVED.search(line) or (NORMATIVE.search(line) and EXTERNAL.search(line)))


def freeze_selftest() -> list[str]:
    problems: list[str] = []
    cases = {
        "ALLOW publish after all gates": True,
        "אסור למחוק ללא אישור בעלים": True,
        "authorized_for_tool_publish is the state": True,
        "This paragraph explains a registry field.": False,
    }
    for text, expected in cases.items():
        if is_normative_external(text) is not expected:
            problems.append(f"freeze classifier selftest mismatch: {text}")
    if POLICY_REF.findall("policy_id: instagram.publish") != ["instagram.publish"]:
        problems.append("policy_id parser selftest failed")
    return problems


def freeze_check(base: str, head: str, known_policies: set[str]) -> list[str]:
    problems: list[str] = []
    canonical_prefixes = ("constitution/", "packages/velvetos/policy/")
    canonical_exact = {"office/control/POLICY.md"}
    for path, lines in diff_added_markdown(base, head).items():
        if path in canonical_exact or path.startswith(canonical_prefixes):
            continue
        normative = [line for line in lines if is_normative_external(line)]
        if not normative:
            continue
        try:
            proc = subprocess.run(
                ["git", "show", f"{head}:{path}"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=30,
            )
        except OSError as exc:
            problems.append(f"{path}: cannot read head file: {exc}")
            continue
        content = proc.stdout if proc.returncode == 0 else "\n".join(lines)
        refs = set(POLICY_REF.findall(content))
        valid = sorted(refs & known_policies)
        if not valid:
            sample = normative[0].strip()[:180]
            problems.append(f"{path}: new normative external-effect text lacks a valid policy_id reference: {sample}")
    return problems


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base")
    p.add_argument("--head")
    return p


def main() -> int:
    args = parser().parse_args()
    if bool(args.base) != bool(args.head):
        print("FAIL --base and --head must be supplied together", file=sys.stderr)
        return 2
    problems, known_policies = validate_registries()
    problems.extend(freeze_selftest())
    if args.base and args.head:
        problems.extend(freeze_check(args.base, args.head, known_policies))
    if problems:
        for problem in problems:
            print(f"FAIL {problem}", file=sys.stderr)
        return 1
    mode = " + policy-creation-freeze" if args.base else ""
    print(
        f"OK policy-architecture policies={len(known_policies)} "
        f"sensors={len(load(SENSORS)['sensors'])} "
        f"artifact_classes={len(load(ARTIFACTS)['entries'])}{mode}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
