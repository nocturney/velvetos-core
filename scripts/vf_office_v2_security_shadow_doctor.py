#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT / "docs" / "implementation" / "office-v2" / "phase0"
P2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"
P3B = ROOT / "docs" / "implementation" / "office-v2" / "phase3b"

RUNTIME = P3B / "runtime-readiness-v0.json"
PROMOTION = P3B / "promotion-gates-v0.json"
SHADOW = P3B / "shadow-readiness-v0.json"
TRUST = P0 / "credential-trust-classes-v0.json"
AUTHORITY = P0 / "authority-map-v0.1.json"
REGISTRY = P2 / "candidate-registry-v0.json"

PRIMARY = {
    "identity_provider": "candidate-zitadel",
    "authorization_policy": "candidate-opa",
    "credential_broker": "candidate-openbao",
}
INCUMBENTS = {
    "identity_provider": "incumbent-current-service-identity",
    "authorization_policy": "incumbent-current-authorization",
    "credential_broker": "incumbent-current-credential-management",
}


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: root must be object")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_contract() -> dict[str, Any]:
    runtime = load(RUNTIME)
    promotion = load(PROMOTION)
    shadow = load(SHADOW)
    trust = load(TRUST)
    authority = load(AUTHORITY)
    registry = load(REGISTRY)

    require(runtime.get("status") == "PRE_SHADOW_RUNTIME_READINESS_PASS_NOT_ACTIVATED", "runtime readiness status mismatch")
    require(runtime.get("mode") == "PRE_SHADOW_ONLY", "runtime readiness mode mismatch")
    require(runtime.get("selected_composition") == "composition-zitadel-opa-openbao", "runtime composition mismatch")
    require(runtime.get("current_authority") == "NONE", "runtime authority must remain NONE")
    for field in (
        "production_authority_change",
        "production_writer_change",
        "production_credentials_bound",
        "production_secret_material_allowed",
        "external_effects_allowed",
        "shadow_promoted",
        "runtime_activation_allowed",
    ):
        require(runtime.get(field) is False, f"runtime field must remain false: {field}")

    health = runtime.get("health_contract") or {}
    require(health.get("status") == "PASS_CONTRACT_AND_EXISTING_LAB_OUTAGE_EVIDENCE", "health contract status mismatch")
    require("every unknown/unhealthy state is DENY" in str(health.get("aggregate_rule") or ""), "health aggregate must deny unknown/unhealthy")
    for role, candidate in PRIMARY.items():
        row = health.get(role) or {}
        require(row.get("candidate") == candidate, f"health candidate mismatch: {role}")
        require(row.get("failure_action") == "DENY_SHADOW_RESULT", f"health failure action mismatch: {role}")
    require("may trigger an alternate engine to seek ALLOW" in str(health.get("outage_rule") or ""), "health outage fallback rule missing")
    refs = set(health.get("source_evidence_refs") or [])
    require("D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-06/composition-winners-zitadel-opa-openbao.json" in refs, "composition health evidence ref missing")
    require("D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-06/persistence-readiness.json" in refs, "persistence health evidence ref missing")

    service = runtime.get("service_autostart_plan") or {}
    require(service.get("status") == "PLAN_COMPLETE_NOT_INSTALLED_NOT_ENABLED", "service plan status mismatch")
    require(service.get("windows_permanent_task") == "OfficeV2 LAB Lease", "service plan must reuse OfficeV2 LAB Lease")
    require(service.get("new_permanent_windows_tasks_allowed") is False, "new permanent Windows tasks forbidden")
    require(service.get("wsl_distribution") == "OfficeV2-Lab", "WSL distribution mismatch")
    require(service.get("systemd_target") == "officev2-phase3b-shadow.target", "systemd target mismatch")
    require(len(service.get("planned_units") or []) == 5, "planned service unit set incomplete")
    require(service.get("installed") is False and service.get("enabled") is False, "pre-shadow services must remain uninstalled/disabled")
    require(service.get("host_port_bindings_allowed") is False, "host port bindings must remain forbidden")
    require("separate explicit SHADOW promotion receipt" in str(service.get("activation_rule") or ""), "service activation promotion boundary missing")

    keymat = runtime.get("key_material_handling") or {}
    require(keymat.get("status") == "PASS_DPAPI_CROSS_PROCESS_PROBE_NO_RUNTIME_SECRETS", "key-material status mismatch")
    require(keymat.get("credential_class") == "LAB_ONLY_SECRET", "key material must remain LAB_ONLY_SECRET")
    require(keymat.get("encryption") == "Windows DPAPI CurrentUser under the same Chris user context as OfficeV2 LAB Lease", "DPAPI binding mismatch")
    require(keymat.get("git_allowed") is False and keymat.get("artifact_evidence_allowed") is False and keymat.get("log_allowed") is False, "key material leak boundary mismatch")
    require(keymat.get("fallback_if_dpapi_unavailable") == "BLOCK_CANDIDATE_RUNTIME_KEEP_INCUMBENTS_CANONICAL", "DPAPI failure must fail closed")
    require(keymat.get("prelogin_claimed") is False, "pre-login DPAPI capability must not be claimed")
    require(keymat.get("probe_evidence_ref") == "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-06/dpapi-key-material-probe.json", "DPAPI probe evidence ref mismatch")
    require(len(keymat.get("probe_evidence_sha256") or "") == 64, "DPAPI probe evidence hash missing")
    require(keymat.get("cross_process_verified") is True and keymat.get("plaintext_hash_match") is True and keymat.get("encrypted_blob_removed_after_probe") is True, "DPAPI cross-process proof mismatch")
    require(set(keymat.get("acl_identities") or []) == {"CHRIS\\Chris", "NT AUTHORITY\\SYSTEM"}, "DPAPI ACL identity set mismatch")
    require("production provider credentials" in (keymat.get("not_persisted") or []), "production credentials must not be persisted")

    rollback = runtime.get("rollback") or {}
    require(rollback.get("status") == "PASS_CONTRACT_SELFTEST_INCUMBENTS_REMAIN_CANONICAL", "rollback status mismatch")
    require(rollback.get("identity_incumbent") == INCUMBENTS["identity_provider"], "identity rollback incumbent mismatch")
    require(rollback.get("authorization_incumbent") == INCUMBENTS["authorization_policy"], "authorization rollback incumbent mismatch")
    require(rollback.get("credential_incumbent") == INCUMBENTS["credential_broker"], "credential rollback incumbent mismatch")
    require(rollback.get("canonical_effect_authority_during_shadow") == "production incumbents only", "candidate must not own effect authority")
    require(rollback.get("automatic_fallback_from_canonical_deny") is False, "canonical DENY fallback forbidden")
    require(rollback.get("authority_transfer_required_for_rollback") is False, "rollback must not require authority transfer")

    trust_rows = {row.get("id"): row for row in trust.get("credential_classes") or []}
    require((trust_rows.get("LAB_ONLY_SECRET") or {}).get("production_access") is False, "LAB_ONLY_SECRET production access drift")
    require(trust.get("secrets_in_git_allowed") is False, "secrets in Git must remain forbidden")
    require(authority.get("single_external_effect_authority") is True, "single effect authority invariant missing")
    require(authority.get("new_production_writer_added") is False, "runtime readiness may not add production writer")

    items = {row.get("candidate_id"): row for row in registry.get("items") or []}
    for role, cid in INCUMBENTS.items():
        row = items.get(cid) or {}
        require(row.get("lifecycle_state") == "PRODUCTION", f"incumbent not production: {role}")
        require(row.get("authority_role") == "PRODUCTION_INCUMBENT", f"incumbent authority drift: {role}")
        require(row.get("decision_verdict") == "KEEP_INCUMBENT", f"incumbent verdict drift: {role}")

    require(promotion.get("status") == "PRE_SHADOW_READY_AWAITING_EXPLICIT_PROMOTION", "promotion status drift")
    require(promotion.get("shadow_promoted") is False, "promotion unexpectedly grants SHADOW")
    require(shadow.get("status") == "PRE_SHADOW_READINESS_COMPLETE_NO_PROMOTION", "shadow readiness status drift")
    require(shadow.get("shadow_promoted") is False, "shadow readiness unexpectedly promoted")
    exact = shadow.get("exact_regression") or {}
    require(exact.get("status") == "PASS" and exact.get("suite") == "116/116", "exact regression status mismatch")
    require(exact.get("validated_after_rebase") is True and exact.get("repository_files_unchanged") is True, "exact regression proof incomplete")
    require(exact.get("services_activated") is False and exact.get("production_authority_change") is False and exact.get("shadow_promoted") is False, "exact regression crossed activation/authority boundary")
    require(shadow.get("remaining_preconditions_before_shadow_can_be_considered") == ["separate explicit project-state SHADOW promotion receipt"], "remaining SHADOW preconditions drift")
    return runtime


def evaluate_health(identity: Any, authorization: Any, broker: Any, synthetic_e2e: Any, canonical_policy: str = "ALLOW") -> dict[str, Any]:
    states = {
        "identity_provider": identity is True,
        "authorization_policy": authorization is True,
        "credential_broker": broker is True,
        "synthetic_e2e": synthetic_e2e is True,
    }
    canonical = str(canonical_policy or "UNKNOWN").upper()
    reasons: list[str] = []
    for name, ok in states.items():
        if not ok:
            reasons.append(f"{name.upper()}_UNHEALTHY_OR_UNKNOWN")
    if canonical != "ALLOW":
        reasons.append("CANONICAL_POLICY_NOT_ALLOW")
    healthy = not reasons
    return {
        "mode": "PRE_SHADOW_ONLY",
        "shadow_result": "SHADOW_OBSERVE_ONLY" if healthy else "DENY_SHADOW_RESULT",
        "production_path": "INCUMBENTS_CANONICAL",
        "external_effect_allowed": False,
        "automatic_fallback_to_seek_allow": False,
        "component_health": states,
        "reason_codes": reasons or ["ALL_SHADOW_HEALTH_GATES_PASS"],
    }


def rollback_selection(candidate_enabled: bool, dpapi_available: bool = True) -> dict[str, Any]:
    if not dpapi_available:
        candidate_enabled = False
        reason = "DPAPI_UNAVAILABLE_CANDIDATE_BLOCKED"
    elif candidate_enabled:
        reason = "CANDIDATE_SHADOW_OBSERVER_ONLY"
    else:
        reason = "CANDIDATE_DISABLED"
    return {
        "production_route": dict(INCUMBENTS),
        "shadow_route": dict(PRIMARY) if candidate_enabled else None,
        "candidate_runtime_enabled": candidate_enabled,
        "production_authority": "INCUMBENTS_ONLY",
        "external_effect_allowed_for_candidate": False,
        "reason": reason,
    }


def selftest() -> None:
    validate_contract()

    good = evaluate_health(True, True, True, True)
    require(good["shadow_result"] == "SHADOW_OBSERVE_ONLY", "healthy shadow simulation did not pass")
    require(good["production_path"] == "INCUMBENTS_CANONICAL" and good["external_effect_allowed"] is False, "healthy shadow simulation changed authority")

    for label, args in (
        ("identity", (False, True, True, True)),
        ("authorization", (True, False, True, True)),
        ("broker", (True, True, False, True)),
        ("e2e", (True, True, True, False)),
        ("unknown", (None, True, True, True)),
    ):
        row = evaluate_health(*args)
        require(row["shadow_result"] == "DENY_SHADOW_RESULT", f"negative health control failed: {label}")
        require(row["external_effect_allowed"] is False, f"negative health control allowed effect: {label}")

    canonical_deny = evaluate_health(True, True, True, True, canonical_policy="DENY")
    require(canonical_deny["shadow_result"] == "DENY_SHADOW_RESULT", "canonical DENY must discard shadow result")
    require(canonical_deny["automatic_fallback_to_seek_allow"] is False, "canonical DENY may not seek fallback ALLOW")

    rollback = rollback_selection(False)
    require(rollback["production_route"] == INCUMBENTS and rollback["shadow_route"] is None, "rollback did not restore incumbents")
    observer = rollback_selection(True)
    require(observer["production_route"] == INCUMBENTS and observer["shadow_route"] == PRIMARY, "shadow observer routing mismatch")
    dpapi_fail = rollback_selection(True, dpapi_available=False)
    require(dpapi_fail["candidate_runtime_enabled"] is False and dpapi_fail["production_route"] == INCUMBENTS, "DPAPI failure did not fail closed")

    print("PASS office-v2-security-shadow-doctor selftest=10 mode=PRE_SHADOW_ONLY services=NOT_ACTIVATED authority=INCUMBENTS_ONLY effect=NONE")


def main() -> None:
    parser = argparse.ArgumentParser(description="Office v2 Phase 3B pre-SHADOW runtime readiness validator")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("selftest")
    health = sub.add_parser("health-simulate")
    health.add_argument("--identity", choices=["pass", "fail", "unknown"], required=True)
    health.add_argument("--authorization", choices=["pass", "fail", "unknown"], required=True)
    health.add_argument("--broker", choices=["pass", "fail", "unknown"], required=True)
    health.add_argument("--e2e", choices=["pass", "fail", "unknown"], required=True)
    health.add_argument("--canonical-policy", default="ALLOW")
    rollback = sub.add_parser("rollback-simulate")
    rollback.add_argument("--candidate-enabled", action="store_true")
    rollback.add_argument("--dpapi-unavailable", action="store_true")
    args = parser.parse_args()

    def state(value: str) -> bool | None:
        return True if value == "pass" else False if value == "fail" else None

    try:
        if args.command == "validate":
            validate_contract()
            print("PASS office-v2-security-shadow-doctor contract=VALID mode=PRE_SHADOW_ONLY services=NOT_ACTIVATED authority=NONE")
        elif args.command == "selftest":
            selftest()
        elif args.command == "health-simulate":
            validate_contract()
            print(json.dumps(evaluate_health(
                state(args.identity),
                state(args.authorization),
                state(args.broker),
                state(args.e2e),
                args.canonical_policy,
            ), sort_keys=True))
        else:
            validate_contract()
            print(json.dumps(rollback_selection(args.candidate_enabled, not args.dpapi_unavailable), sort_keys=True))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL office-v2-security-shadow-doctor: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
