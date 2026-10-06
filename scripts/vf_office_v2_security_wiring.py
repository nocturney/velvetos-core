#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT / "docs" / "implementation" / "office-v2" / "phase0"
P3B = ROOT / "docs" / "implementation" / "office-v2" / "phase3b"
WIRING_PATH = P3B / "integration-wiring-v0.json"
PROMOTION_PATH = P3B / "promotion-gates-v0.json"
VERDICT_PATH = P3B / "composition-gate-verdict-v0.json"
TRUST_PATH = P0 / "credential-trust-classes-v0.json"
AUTHORITY_PATH = P0 / "authority-map-v0.1.json"

EXPECTED_PIPELINE = [
    "request_intake",
    "identity_verify",
    "claim_normalize",
    "authorize",
    "credential_scope_check",
    "credential_resolution_decision",
    "effect_gate",
    "evidence_finalize",
]
EXPECTED_PRIMARY = {
    "identity_provider": "candidate-zitadel",
    "authorization_policy": "candidate-opa",
    "credential_broker": "candidate-openbao",
}
EXPECTED_FALLBACK = {
    "identity_provider": "candidate-keycloak",
    "authorization_policy": "candidate-cedar",
    "credential_broker": "candidate-infisical-agent-vault",
}
INPUT_FIELDS = {
    "correlation_id",
    "principal_id",
    "identity_verified",
    "action",
    "resource",
    "requested_scope",
    "policy_decision",
    "broker_available",
    "broker_scope",
}
REQUIRED_INPUTS = INPUT_FIELDS
FORBIDDEN_INPUT_KEYS = {
    "access_token",
    "refresh_token",
    "id_token",
    "bearer_token",
    "authorization_header",
    "client_secret",
    "secret",
    "secret_value",
    "password",
    "private_key",
    "credential_material",
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
    wiring = load(WIRING_PATH)
    promotion = load(PROMOTION_PATH)
    verdict = load(VERDICT_PATH)
    trust = load(TRUST_PATH)
    authority = load(AUTHORITY_PATH)

    require(wiring.get("status") == "LAB_WIRING_DEFINED_NO_PRODUCTION_AUTHORITY", "wiring status mismatch")
    require(wiring.get("mode") == "LAB_SIMULATION_ONLY", "reference wiring must remain simulation-only")
    require(wiring.get("selected_composition") == "composition-zitadel-opa-openbao", "composition mismatch")
    for field in (
        "production_authority_change",
        "production_writer_change",
        "production_credentials_allowed",
        "production_secret_material_allowed",
        "external_effects_allowed",
        "network_calls_allowed_by_reference_implementation",
    ):
        require(wiring.get(field) is False, f"{field} must remain false")
    require(wiring.get("credential_trust_class") == "LAB_ONLY_SECRET", "LAB trust class required")

    trust_rows = {row.get("id"): row for row in trust.get("credential_classes") or []}
    lab_secret = trust_rows.get("LAB_ONLY_SECRET") or {}
    require(lab_secret.get("production_access") is False, "LAB_ONLY_SECRET must not have production access")
    require(trust.get("lab_receives_production_credentials_by_default") is False, "LAB production credential default drift")
    require(trust.get("secrets_in_git_allowed") is False, "secrets in Git must remain forbidden")
    require(authority.get("single_external_effect_authority") is True, "single effect authority invariant missing")
    require(authority.get("new_production_writer_added") is False, "integration wiring cannot add a production writer")

    roles = wiring.get("roles") or {}
    require(set(roles) == set(EXPECTED_PRIMARY), "role set mismatch")
    for role, primary in EXPECTED_PRIMARY.items():
        require((roles.get(role) or {}).get("primary") == primary, f"{role} primary mismatch")
        require((roles.get(role) or {}).get("fallback") == EXPECTED_FALLBACK[role], f"{role} fallback mismatch")
    fallback = wiring.get("fallback_policy") or {}
    require(fallback.get("automatic_failover_enabled") is False, "automatic fallback must remain disabled")
    require(fallback.get("mode") == "EXPLICIT_REWIRE_ONLY", "fallback mode mismatch")

    pipeline = wiring.get("pipeline") or []
    require([row.get("n") for row in pipeline] == list(range(1, 9)), "pipeline order numbers mismatch")
    require([row.get("id") for row in pipeline] == EXPECTED_PIPELINE, "pipeline stage order mismatch")
    require(all(row.get("fail_closed") is True for row in pipeline), "every pipeline stage must fail closed")

    evidence = wiring.get("evidence_contract") or {}
    forbidden = set(evidence.get("forbidden_fields") or [])
    require(FORBIDDEN_INPUT_KEYS.issubset(forbidden), "forbidden evidence fields incomplete")
    require(evidence.get("raw_secret_material_allowed") is False, "raw secret evidence must remain forbidden")
    require(evidence.get("raw_bearer_material_allowed") is False, "raw bearer evidence must remain forbidden")

    require(verdict.get("status") == "SELECTED_FOR_INTEGRATION_NO_PRODUCTION_AUTHORITY", "composition verdict status mismatch")
    require(verdict.get("phase3b_gate_closed") is True, "composition gate must be closed before wiring")
    require(verdict.get("winner") == wiring.get("selected_composition"), "wiring/verdict winner mismatch")
    for field in ("production_authority_change", "production_writer_change", "production_credentials_used", "production_secret_material_used", "shadow_or_pilot_promotion"):
        require(verdict.get(field) is False, f"composition verdict unsafe field: {field}")

    require(promotion.get("status") == "INTEGRATION_WIRING_ONLY_NOT_PROMOTED", "promotion status mismatch")
    require(promotion.get("current_authority") == "NONE", "promotion authority must remain NONE")
    for field in ("production_authority_change", "production_writer_change", "production_credentials_bound", "shadow_promoted", "pilot_promoted", "production_promoted"):
        require(promotion.get(field) is False, f"promotion field must remain false: {field}")
    require((promotion.get("shadow_gate") or {}).get("status") == "BLOCKED_PENDING_SEPARATE_PROMOTION", "SHADOW gate must remain blocked")
    require((promotion.get("pilot_gate") or {}).get("status") == "BLOCKED_UNTIL_SHADOW_PASS_AND_SEPARATE_PROMOTION", "PILOT gate must remain blocked")
    require((promotion.get("production_gate") or {}).get("implicit_promotion_allowed") is False, "implicit production promotion forbidden")

    return wiring


def walk_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key).lower())
            found.update(walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(walk_keys(child))
    return found


def simulate(request: dict[str, Any], wiring: dict[str, Any] | None = None) -> dict[str, Any]:
    wiring = wiring or validate_contract()
    keys = walk_keys(request)
    forbidden = keys & FORBIDDEN_INPUT_KEYS
    if forbidden:
        raise ValueError("raw credential/bearer fields forbidden: " + ",".join(sorted(forbidden)))
    unknown = set(request) - INPUT_FIELDS
    if unknown:
        raise ValueError("unknown request fields forbidden: " + ",".join(sorted(unknown)))

    missing = sorted(REQUIRED_INPUTS - set(request))
    reasons: list[str] = []
    if missing:
        reasons.append("MISSING_REQUIRED_INPUT")
    correlation_id = str(request.get("correlation_id") or "")
    principal_id = str(request.get("principal_id") or "")
    identity_verified = request.get("identity_verified") is True
    policy_decision = str(request.get("policy_decision") or "UNAVAILABLE").upper()
    requested_scope = str(request.get("requested_scope") or "")
    broker_scope = str(request.get("broker_scope") or "")
    broker_available = request.get("broker_available") is True

    if not identity_verified:
        reasons.append("IDENTITY_UNVERIFIED")
    if policy_decision != "ALLOW":
        reasons.append("POLICY_DENY_OR_UNAVAILABLE")
    scope_match = bool(requested_scope) and requested_scope == broker_scope
    if not scope_match:
        reasons.append("SCOPE_MISMATCH")
    if not broker_available:
        reasons.append("BROKER_UNAVAILABLE")
    if not correlation_id or not principal_id or not request.get("action") or not request.get("resource"):
        if "MISSING_REQUIRED_INPUT" not in reasons:
            reasons.append("MISSING_REQUIRED_INPUT")

    credential_eligible = not reasons
    outcome = "ALLOW_SIMULATION_ONLY" if credential_eligible else "DENY"
    roles = wiring["roles"]
    receipt = {
        "schema": "velvetos.office-v2.phase3b-security-wiring-receipt.v0",
        "mode": "LAB_SIMULATION_ONLY",
        "correlation_id": correlation_id,
        "principal_id_hash": hashlib.sha256(principal_id.encode("utf-8")).hexdigest() if principal_id else None,
        "action": request.get("action"),
        "resource": request.get("resource"),
        "requested_scope": requested_scope,
        "identity_status": "VERIFIED" if identity_verified else "DENY",
        "policy_decision": "ALLOW" if policy_decision == "ALLOW" else "DENY",
        "scope_match": scope_match,
        "credential_resolution_eligible": credential_eligible,
        "external_effect_allowed": False,
        "outcome": outcome,
        "reason_codes": reasons or ["ALL_INTEGRATION_GATES_PASS"],
        "component_selection": {role: row["primary"] for role, row in roles.items()},
    }
    allowed = set((wiring.get("evidence_contract") or {}).get("allowed_fields") or [])
    require(set(receipt).issubset(allowed), "receipt contains non-allowlisted evidence field")
    return receipt


def selftest() -> None:
    wiring = validate_contract()
    allow = {
        "correlation_id": "test-correlation-001",
        "principal_id": "synthetic-principal",
        "identity_verified": True,
        "action": "synthetic.read",
        "resource": "lab/resource-1",
        "requested_scope": "lab/scope-a",
        "policy_decision": "ALLOW",
        "broker_available": True,
        "broker_scope": "lab/scope-a",
    }
    receipt = simulate(allow, wiring)
    require(receipt["outcome"] == "ALLOW_SIMULATION_ONLY", "positive simulation did not pass")
    require(receipt["credential_resolution_eligible"] is True, "positive credential gate did not pass")
    require(receipt["external_effect_allowed"] is False, "simulation must never allow external effect")

    for field, value in (
        ("identity_verified", False),
        ("policy_decision", "DENY"),
        ("broker_available", False),
        ("broker_scope", "lab/scope-b"),
    ):
        case = dict(allow)
        case[field] = value
        require(simulate(case, wiring)["outcome"] == "DENY", f"negative control failed: {field}")

    missing = dict(allow)
    missing.pop("resource")
    require(simulate(missing, wiring)["outcome"] == "DENY", "missing input must deny")

    leaked = dict(allow)
    leaked["access_token"] = "forbidden"
    try:
        simulate(leaked, wiring)
    except ValueError:
        pass
    else:
        raise ValueError("raw token negative control did not fail")

    print("PASS office-v2-security-wiring selftest=7 mode=LAB_SIMULATION_ONLY network=NONE external_effect=NONE authority=NONE")


def main() -> None:
    parser = argparse.ArgumentParser(description="Office v2 Phase 3B non-authoritative security wiring reference")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sim = sub.add_parser("simulate")
    sim.add_argument("--request", required=True, help="Path to synthetic request JSON")
    sub.add_parser("selftest")
    args = parser.parse_args()

    try:
        if args.command == "validate":
            validate_contract()
            print("PASS office-v2-security-wiring contract=VALID mode=LAB_SIMULATION_ONLY authority=NONE")
        elif args.command == "simulate":
            request = load(Path(args.request))
            print(json.dumps(simulate(request), ensure_ascii=False, sort_keys=True))
        else:
            selftest()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL office-v2-security-wiring: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
