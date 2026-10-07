#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT / "docs" / "implementation" / "office-v2" / "phase0"
P3B = ROOT / "docs" / "implementation" / "office-v2" / "phase3b"

def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be object")
    return data

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def main() -> None:
    prod = load(P3B / "production-promotion-v0.json")
    authority = load(P0 / "authority-map-v0.1.json")
    trust = load(P0 / "credential-trust-classes-v0.json")
    pilot = load(P3B / "pilot-promotion-v0.json")
    gates = load(P3B / "promotion-gates-v0.json")

    require(prod.get("status") == "READY_AWAITING_EXPLICIT_RUNTIME_AUTHORITY_TRANSFER", "production contract status mismatch")
    require(prod.get("scope_id") == "instagram-publisher-snapshot-read", "production scope mismatch")
    require(prod.get("production_domain") == "instagram_read", "production domain mismatch")
    require(prod.get("selected_composition") == "composition-zitadel-opa-openbao", "composition mismatch")
    required = prod.get("required_project_state_before_promotion") or {}
    require(required.get("phase") == "PHASE_3B_PILOT_ACTIVE", "required project phase mismatch")
    require(required.get("checkpoint") == "office-v2-phase3b-v0-cp016-pilot-active", "required checkpoint mismatch")
    require(required.get("gate") == "GREEN", "required gate mismatch")
    require(prod.get("production_authority_change") is True, "production read-authority transfer must be explicit")
    require(prod.get("production_writer_change") is False, "production writer must remain unchanged")
    require(prod.get("production_promoted") is False, "production contract must not self-promote")
    require(prod.get("external_mutation_allowed") is False, "production read scope must not grant mutation")
    require(prod.get("implicit_promotion_allowed") is False, "implicit production promotion forbidden")

    mapped = authority.get("phase3b_security_authority") or {}
    require(mapped.get("status") == "READY_AWAITING_EXPLICIT_RUNTIME_AUTHORITY_TRANSFER", "authority map status mismatch")
    require(mapped.get("scope_id") == prod.get("scope_id"), "authority map scope mismatch")
    require(mapped.get("authorization_decision_owner") == "OPA", "OPA must own the production decision")
    require(mapped.get("credential_broker_owner") == "OpenBao", "OpenBao must own credential resolution")
    require(mapped.get("production_writer_change") is False, "authority map may not add writer")
    require(mapped.get("external_mutation_authority_added") is False, "authority map may not add mutation authority")
    require(authority.get("single_external_effect_authority") is True, "single effect authority invariant missing")
    require(authority.get("new_production_writer_added") is False, "new production writer invariant violated")

    domain = next((x for x in authority.get("domains") or [] if x.get("domain") == "instagram_read"), {})
    binding = domain.get("phase3b_security_binding") or {}
    require(binding.get("scope_id") == prod.get("scope_id"), "instagram_read binding scope mismatch")
    require(binding.get("credential_class") == "PRODUCTION_READ", "instagram_read credential class mismatch")
    require(binding.get("write_allowed") is False, "instagram_read binding must be read-only")
    require(binding.get("production_writer_change") is False, "instagram_read binding may not change writer")

    row = next((x for x in trust.get("production_bindings") or [] if x.get("id") == "phase3b-instagram-publisher-snapshot-read"), {})
    require(row.get("status") == "READY_AWAITING_EXPLICIT_RUNTIME_AUTHORITY_TRANSFER", "credential binding status mismatch")
    require(row.get("scope_id") == prod.get("scope_id"), "credential binding scope mismatch")
    require(row.get("credential_class") == "PRODUCTION_READ", "credential class mismatch")
    require(row.get("identity_provider") == "ZITADEL", "identity provider mismatch")
    require(row.get("authorization_engine") == "OPA", "authorization engine mismatch")
    require(row.get("credential_broker") == "OpenBao", "credential broker mismatch")
    require(row.get("write_allowed") is False, "credential binding must be read-only")
    require(row.get("control_token_forbidden") is True, "CONTROL_TOKEN reuse must remain forbidden")
    require(row.get("meta_access_token_forbidden") is True, "META_ACCESS_TOKEN reuse must remain forbidden")
    require(row.get("raw_secret_in_git_forbidden") is True, "raw secret in Git must remain forbidden")
    require(row.get("production_writer_change") is False, "credential binding may not add writer")

    require(pilot.get("status") == "READY_AWAITING_EXPLICIT_PROJECT_STATE_PROMOTION", "historical pilot contract drift")
    require(pilot.get("pilot_promoted") is False, "versioned pilot readiness contract must remain historical")
    require((gates.get("production_gate") or {}).get("implicit_promotion_allowed") is False, "historical production gate must remain explicit")

    serialized = json.dumps(prod, sort_keys=True).lower()
    for forbidden in ('"secret_value"', '"raw_token"', '"access_token"', '"client_secret"', '"private_key"'):
        require(forbidden not in serialized, "raw credential material field forbidden: " + forbidden)

    print("OK office-v2-phase3b-production contract=READY scope=instagram-publisher-snapshot-read writer_change=FALSE mutation=FALSE promotion=EXPLICIT_ONLY")

if __name__ == "__main__":
    main()
