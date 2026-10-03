#!/usr/bin/env python3
"""Validate VelvetOS policy registries and optionally enforce the Stage 0 policy-creation freeze."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "packages" / "velvetos" / "policy"
POLICIES = POLICY_DIR / "policy-registry.json"
SENSORS = POLICY_DIR / "sensor-registry.json"
SELECTION = POLICY_DIR / "sensor-selection.json"
ARTIFACTS = POLICY_DIR / "artifact-retention.json"
SCHEMAS = POLICY_DIR / "schema"
REPORTS = POLICY_DIR / "reports"
ACTION_RECEIPT_SCHEMA = SCHEMAS / "action-receipt.schema.json"
ACTION_RECEIPT_VECTORS = POLICY_DIR / "action-receipt-test-vectors.json"
ACTION_RECEIPT_VALIDATOR = ROOT / "scripts" / "vf_action_receipt.py"
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
        require(row.get("deletion_authorized") is False, f"{aid}: Stage 0 cannot authorize deletion", problems)
        refs = row.get("policy_refs")
        require(isinstance(refs, list), f"{aid}: policy_refs must be list", problems)
        for policy_id in refs or []:
            require(policy_id in known_policies, f"{aid}: unknown policy ref {policy_id}", problems)

    expected_schemas = {
        "policy-registry.schema.json",
        "sensor-registry.schema.json",
        "sensor-selection.schema.json",
        "artifact-retention.schema.json",
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
                require(isinstance(cutover.get("live_worker_version_id"), str) and bool(cutover.get("live_worker_version_id")),
                        "Stage 4D live cutover missing Worker version", problems)
                require((cutover.get("health_readback") or {}).get("policy_version") == 2,
                        "Stage 4D live cutover health policy version mismatch", problems)

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
