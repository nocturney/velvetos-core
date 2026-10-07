#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT / "docs" / "implementation" / "office-v2" / "phase0"
P3B = ROOT / "docs" / "implementation" / "office-v2" / "phase3b"
VFIGOS = ROOT / "packages" / "vfigos"

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
    prod_read = load(P3B / "production-read-v0.json")
    prod_authority = load(P3B / "production-read-authority-map-v0.json")
    prod_trust = load(P3B / "production-read-credential-trust-v0.json")

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

    require(prod_read.get("status") == "IMPLEMENTATION_READY_RUNTIME_PROOF_PENDING", "production read implementation status mismatch")
    require(prod_read.get("production_domain") == "instagram_read", "production read implementation domain mismatch")
    require(prod_read.get("principal") == "svc:officev2-p3b-prod-publisher-snapshot", "production read principal mismatch")
    require(prod_read.get("credential_class") == "PRODUCTION_READ", "production read credential class mismatch")
    require(prod_read.get("production_promoted") is False, "production read implementation must not self-promote")
    require(prod_read.get("production_writer_change") is False and prod_read.get("external_mutation_allowed") is False, "production read implementation writer/mutation boundary drift")
    runtime_contract = prod_read.get("runtime_contract") or {}
    require(runtime_contract.get("broker_instance") == "officev2-p3b-prod-openbao", "production runtime broker instance mismatch")
    require(runtime_contract.get("broker_volume") == "officev2_p3b_prod_bao", "production runtime broker volume mismatch")
    require(runtime_contract.get("broker_isolated_from_pilot") is True, "production broker must be isolated from PILOT broker")
    require(runtime_contract.get("broker_path") == "officev2-prod/data/instagram-publisher-snapshot", "production runtime broker path mismatch")
    require(runtime_contract.get("broker_role") == "officev2-prod-publisher-snapshot", "production runtime broker role mismatch")
    require(runtime_contract.get("broker_rotator_role") == "officev2-prod-publisher-snapshot-rotator", "production runtime rotator role mismatch")
    require(runtime_contract.get("broker_rotator_capabilities") == ["create", "update", "read"], "production runtime rotator capability mismatch")
    require(runtime_contract.get("broker_rotator_scope") == "secret/data/officev2-prod/instagram-publisher-snapshot only", "production runtime rotator scope mismatch")
    require(runtime_contract.get("identity_lifecycle") == "persistent_until_explicit_rollback", "production identity must be persistent")
    require(runtime_contract.get("prepare_reuses_current_pilot_provider_credential_without_cutover") is True, "prepare must not rotate provider credential")
    require(runtime_contract.get("rotate_requires_old_provider_credential_http") == 401, "rotation old credential denial proof missing")
    require(runtime_contract.get("rotate_requires_new_provider_read_http") == 200 and runtime_contract.get("rotate_requires_new_provider_write_http") == 401, "rotation new credential read/write boundary mismatch")
    require(runtime_contract.get("generated_openbao_root_must_be_revoked") is True and runtime_contract.get("persistent_openbao_root_forbidden") is True, "generated OpenBao root boundary mismatch")
    require(runtime_contract.get("raw_secret_evidence_forbidden") is True, "production raw-secret evidence must remain forbidden")

    require(prod_authority.get("domain") == "instagram_read", "production authority extension domain mismatch")
    require(prod_authority.get("principal") == "svc:officev2-p3b-prod-publisher-snapshot", "production authority extension principal mismatch")
    require(prod_authority.get("production_writer_change") is False and prod_authority.get("allowed_mutations") == [], "production authority extension mutation boundary drift")
    require(prod_trust.get("principal") == "svc:officev2-p3b-prod-publisher-snapshot", "production trust extension principal mismatch")
    require(prod_trust.get("credential_class") == "PRODUCTION_READ" and prod_trust.get("write_allowed") is False, "production trust extension read-only mismatch")
    require(prod_trust.get("admin_or_control_credential_fallback_allowed") is False and prod_trust.get("meta_access_token_allowed") is False, "production trust extension fallback boundary drift")

    refs = prod_read.get("implementation_refs") or {}
    required_refs = {
        "consumer": "packages/vfigos/officev2_secure_publisher_snapshot.py",
        "resolver": "packages/vfigos/officev2_production_snapshot_resolver.ps1",
        "runtime_binding": "packages/vfigos/officev2_production_runtime_bind.ps1",
        "snapshot_read": "packages/vfigos/officev2_production_snapshot_read.sh",
        "pilot_token_read_for_cutover_only": "packages/vfigos/officev2_pilot_token_read.sh",
        "production_token_read_for_rollback_only": "packages/vfigos/officev2_production_token_read.sh",
        "openbao_binding": "packages/vfigos/officev2_production_openbao_bind.sh",
        "zitadel_bootstrap": "packages/vfigos/officev2_production_zitadel_bootstrap.sh",
        "zitadel_cleanup": "packages/vfigos/officev2_production_zitadel_delete.sh",
        "opa_apply": "packages/vfigos/officev2_production_opa_apply.sh",
        "rollback_drill": "packages/vfigos/officev2_production_rollback_drill.ps1",
        "recovery_drill": "packages/vfigos/officev2_production_recovery_drill.sh",
        "recovery_wrapper": "packages/vfigos/officev2_production_recovery.ps1",
    }
    require(refs == required_refs, "production implementation refs mismatch")
    for rel in required_refs.values():
        require((ROOT / rel).is_file(), "production implementation file missing: " + rel)

    resolver = (VFIGOS / "officev2_production_snapshot_resolver.ps1").read_text(encoding="utf-8-sig")
    snapshot_read = (VFIGOS / "officev2_production_snapshot_read.sh").read_text(encoding="utf-8-sig")
    production_token_read = (VFIGOS / "officev2_production_token_read.sh").read_text(encoding="utf-8-sig")
    runtime_bind = (VFIGOS / "officev2_production_runtime_bind.ps1").read_text(encoding="utf-8-sig")
    openbao_bind = (VFIGOS / "officev2_production_openbao_bind.sh").read_text(encoding="utf-8-sig")
    zitadel_bootstrap = (VFIGOS / "officev2_production_zitadel_bootstrap.sh").read_text(encoding="utf-8-sig")
    opa_apply = (VFIGOS / "officev2_production_opa_apply.sh").read_text(encoding="utf-8-sig")
    rollback_drill = (VFIGOS / "officev2_production_rollback_drill.ps1").read_text(encoding="utf-8-sig")
    recovery = (VFIGOS / "officev2_production_recovery_drill.sh").read_text(encoding="utf-8-sig")
    recovery_wrapper = (VFIGOS / "officev2_production_recovery.ps1").read_text(encoding="utf-8-sig")
    adapter = (VFIGOS / "officev2_secure_publisher_snapshot.py").read_text(encoding="utf-8-sig")
    opa_policy = (P3B / "production-opa-policy.rego").read_text(encoding="utf-8-sig")

    require("[string[]]$Args" not in runtime_bind, "production runtime binding may not use PowerShell automatic $Args as a named parameter")
    require("[string[]]$Args" not in rollback_drill, "production rollback drill may not use PowerShell automatic $Args as a named parameter")
    require("[string[]]$ScriptArgs" in runtime_bind, "production runtime binding ScriptArgs guard missing")
    require("[string[]]$ScriptArgs" in rollback_drill and "[string[]]$WranglerArgs" in rollback_drill, "production rollback argument guards missing")

    for marker in (
        "production-read-bundle.dpapi",
        "PHASE_3B_PILOT_ACTIVE",
        "office-v2-phase3b-v0-cp016-pilot-active",
        "PHASE_3B_PRODUCTION_READ_ACTIVE",
        "production-runtime-binding.json",
        "production-authority-transfer-authorization-v1.json",
        "svc:officev2-p3b-prod-publisher-snapshot",
        "officev2-prod-publisher-snapshot",
        "officev2-prod/data/instagram-publisher-snapshot",
    ):
        require(marker in resolver, "production resolver missing marker: " + marker)
    require("openbao-pilot-approle.dpapi" not in resolver, "active production resolver may not use PILOT AppRole bundle")

    for marker in (
        "svc:officev2-p3b-prod-publisher-snapshot",
        "officev2-prod-publisher-snapshot",
        "officev2-prod/data/instagram-publisher-snapshot",
        "officev2-p3b-prod-openbao",
        '"persistent_principal":True',
        '"ephemeral_cleanup_on_exit":False',
        'write_http!=401',
    ):
        require(marker in snapshot_read, "production snapshot read missing marker: " + marker)
    for forbidden in ("officev2-pilot/instagram-publisher-snapshot", "/v2/users/new", "META_ACCESS_TOKEN", "CONTROL_TOKEN"):
        require(forbidden not in snapshot_read, "production snapshot read contains forbidden path/material: " + forbidden)

    for marker in (
        "ValidateSet('Prepare','Rotate','Cleanup')",
        "production-read-bundle.dpapi",
        "officev2-prod-publisher-snapshot",
        "oldAfter -eq 401",
        "newRead -eq 200",
        "newWrite -ne 401",
        "Put-Snapshot $oldToken",
        "production_authority_active=$false",
        "Protect-Text",
    ):
        require(marker in runtime_bind, "production runtime binding missing fail-closed marker: " + marker)

    for marker in (
        "officev2-p3b-prod-openbao",
        "officev2_p3b_prod_bao",
        "officev2-phase3b-prod-openbao.service",
        "officev2-prod/data/instagram-publisher-snapshot",
        "officev2-prod-publisher-snapshot",
        "officev2-prod-publisher-snapshot-rotator",
        "token_no_default_policy",
        "/v1/sys/init",
        "auth/token/revoke-self",
        "auth/token/lookup-self",
        "root_after",
        "root_used\":false",
    ):
        require(marker in openbao_bind, "production OpenBao binder missing marker: " + marker)
    require("secret/data/officev2-pilot/instagram-publisher-snapshot" not in openbao_bind, "production OpenBao binder may not write/read PILOT secret path")
    require("officev2-p3b-prod-openbao" in production_token_read, "production token reader must use isolated production OpenBao")
    require("officev2-p3b-shadow-openbao" not in production_token_read, "production token reader may not use PILOT OpenBao")

    for marker in ("SUCCESS=false", "client_credentials", "wrong-", "SUCCESS=true"):
        require(marker in zitadel_bootstrap, "production ZITADEL bootstrap missing marker: " + marker)
    require("svc:officev2-p3b-prod-publisher-snapshot" in opa_policy, "production OPA policy canonical principal missing")
    for marker in ("prod_allow", "prod_write", "pilot_allow", "shadow_allow", "anonymous"):
        require(marker in opa_apply, "production OPA apply negative-control marker missing: " + marker)
    for marker in ("systemctl stop", "officev2-phase3b-prod-openbao.service", "officev2-p3b-prod-openbao", "/opt/officev2-phase3b-prod/unseal.key", "PROD_RECOVERY_OPA_FAIL_OPEN", "PROD_RECOVERY_ZITADEL_FAIL_OPEN", "PROD_RECOVERY_OPENBAO_FAIL_OPEN", "v1/sys/unseal"):
        require(marker in recovery, "production recovery drill missing marker: " + marker)
    for marker in ("production-recovery.json", "ROTATED_PRODUCTION_CREDENTIAL_READY_FOR_PROMOTION", "outage_fail_closed", "unseal_without_persistent_root"):
        require(marker in recovery_wrapper, "production recovery wrapper missing marker: " + marker)
    for marker in ("production-rollback-drill.json", "former_production_credential_http", "restored_pilot_runtime_http", "Put-Snapshot $prodToken", "ROLLBACK_DRILL_COMPLETE_REQUIRES_FRESH_ROTATE"):
        require(marker in rollback_drill, "production rollback drill missing marker: " + marker)
    for marker in ("Resolve-Phase3B-ProductionSnapshot.ps1", "--mode", "Production", "vf.instagram.schedule-snapshot.v1"):
        require(marker in adapter, "secure production snapshot adapter missing marker: " + marker)
    for forbidden in ("VELVET_INSTAGRAM_PUBLISHER_CONTROL_TOKEN", "cloudflare-publisher-control.dpapi", "resolve_token"):
        require(forbidden not in adapter, "secure production snapshot adapter contains forbidden incumbent credential path: " + forbidden)

    serialized = json.dumps(prod, sort_keys=True).lower()
    for forbidden in ('"secret_value"', '"raw_token"', '"access_token"', '"client_secret"', '"private_key"'):
        require(forbidden not in serialized, "raw credential material field forbidden: " + forbidden)

    print("OK office-v2-phase3b-production contract=READY scope=instagram-publisher-snapshot-read writer_change=FALSE mutation=FALSE promotion=EXPLICIT_ONLY")

if __name__ == "__main__":
    main()
