#!/usr/bin/env python3
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"
P3B = ROOT / "docs" / "implementation" / "office-v2" / "phase3b"
WIRING_SCRIPT = ROOT / "scripts" / "vf_office_v2_security_wiring.py"
SHADOW_DOCTOR = ROOT / "scripts" / "vf_office_v2_security_shadow_doctor.py"

REQUIRED = [
    P3B / "README.md",
    P3B / "identity-security-contract-v0.json",
    P3B / "identity-security-destructive-v0.json",
    P3B / "identity-security-shortlist-v0.json",
    P3B / "registry-extension-v0.json",
    P3B / "runtime-pins-v0.json",
    P3B / "admission-v0.json",
    P3B / "lab-status-v0.json",
    P3B / "authorization-lane-verdict-v0.json",
    P3B / "identity-lane-verdict-v0.json",
    P3B / "credential-lane-verdict-v0.json",
    P3B / "composition-gate-verdict-v0.json",
    P3B / "integration-wiring-v0.json",
    P3B / "promotion-gates-v0.json",
    P3B / "shadow-readiness-v0.json",
    P3B / "runtime-readiness-v0.json",
    P3B / "shadow-active-v0.json",
    P3B / "pilot-scope-v0.json",
    P3B / "pilot-readiness-v0.json",
    WIRING_SCRIPT,
    SHADOW_DOCTOR,
    P3B / "scorecards" / "credential-candidate-openbao.json",
    P3B / "scorecards" / "credential-candidate-infisical-agent-vault.json",
    P3B / "scorecards" / "identity-candidate-zitadel.json",
    P3B / "scorecards" / "identity-candidate-keycloak.json",
    P3B / "scorecards" / "identity-candidate-authentik.json",
    P3B / "scorecards" / "identity-incumbent-current-service-identity.json",
    P3B / "scorecards" / "authorization-candidate-opa.json",
    P3B / "scorecards" / "authorization-candidate-cedar.json",
    P3B / "scorecards" / "authorization-candidate-openfga.json",
    P3B / "scorecards" / "authorization-incumbent-current-authorization.json",
]
EXPECTED_LANES = {
    "phase3b-identity-provider": ("identity_provider", "incumbent-current-service-identity", 3),
    "phase3b-authorization-policy": ("authorization_policy", "incumbent-current-authorization", 3),
    "phase3b-credential-broker": ("credential_broker", "incumbent-current-credential-management", 2),
}
EXPECTED_NEW = {
    "incumbent-current-service-identity",
    "incumbent-current-authorization",
    "incumbent-current-credential-management",
    "candidate-zitadel", "candidate-keycloak", "candidate-authentik",
    "candidate-openfga", "candidate-opa", "candidate-cedar", "candidate-openbao",
}
REQUIRED_STEP_IDS = {
    "anonymous-deny", "wrong-principal-deny", "wrong-action-deny", "cross-scope-deny",
    "scoped-credential", "unrelated-secret-proof", "credential-rotate", "old-credential-revoke",
    "identity-revoke", "revoked-identity-deny", "policy-revoke", "dependency-outage", "inspect-finalize",
}

def fail(msg: str) -> None:
    print("FAIL " + msg, file=sys.stderr)
    raise SystemExit(1)

def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(data, dict):
        fail(f"JSON root must be object: {path.relative_to(ROOT)}")
    return data

def main() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.is_file()]
    if missing:
        fail("missing Phase 3B files: " + ", ".join(missing))

    contract = load(P3B / "identity-security-contract-v0.json")
    if contract.get("status") != "CONTRACT_V0_FROZEN_FOR_LAB":
        fail("Phase 3B contract is not frozen for LAB")
    for field in ("authority_change", "production_writer_change", "production_credentials_allowed", "production_secret_material_allowed"):
        if contract.get(field) is not False:
            fail(f"Phase 3B safety field must be false: {field}")
    roles = contract.get("roles") or {}
    if set(roles) != {"identity_provider", "authorization_policy", "credential_broker"}:
        fail("Phase 3B role separation drift")
    gate = contract.get("gate") or {}
    if not gate or not all(v is True for v in gate.values()):
        fail("Phase 3B gate must be fully fail-closed")
    for key in ("deny_by_default", "service_identity_required", "scoped_credential_required", "revocation_required", "policy_decision_receipt_required", "no_unrelated_secret_exposure"):
        if gate.get(key) is not True:
            fail("Phase 3B START HERE gate missing: " + key)

    fixture = load(P3B / "identity-security-destructive-v0.json")
    if fixture.get("fixture_id") != "identity-security-destructive-20-step":
        fail("Phase 3B fixture id mismatch")
    if fixture.get("vendor_specific_fields_forbidden") is not True:
        fail("Phase 3B fixture must remain vendor-neutral")
    if fixture.get("production_credentials_forbidden") is not True or fixture.get("production_effects_forbidden") is not True:
        fail("Phase 3B fixture must forbid production credentials/effects")
    strategy = fixture.get("lane_strategy") or {}
    if strategy.get("cartesian_exhaustion_required") is not False:
        fail("Phase 3B fixture strategy drift")
    steps = fixture.get("steps") or []
    if len(steps) != 20 or [s.get("n") for s in steps] != list(range(1, 21)):
        fail("Phase 3B fixture must have exactly 20 ordered steps")
    ids = [s.get("id") for s in steps]
    if len(ids) != len(set(ids)) or not REQUIRED_STEP_IDS.issubset(set(ids)):
        fail("Phase 3B fixture missing required security semantics")
    required_evidence = set(fixture.get("required_evidence") or [])
    for step in steps:
        expected = set(step.get("expected") or [])
        if not expected or not expected.issubset(required_evidence):
            fail("Phase 3B required evidence incomplete for " + str(step.get("id")))

    registry = load(P2 / "candidate-registry-v0.json")
    items = registry.get("items") or []
    by_id = {x.get("candidate_id"): x for x in items}
    if registry.get("candidate_count") != len(items):
        fail("candidate registry count drift")
    source_ids = [x.get("source_item_id") for x in items if x.get("source_item_id") is not None]
    if len(source_ids) != 68 or len(set(source_ids)) != 68:
        fail("Phase 3B extension changed closed 68-item source import")
    if not EXPECTED_NEW.issubset(set(by_id)):
        fail("Phase 3B registry extension candidates missing")
    if "candidate-infisical-agent-vault" not in by_id:
        fail("Infisical credential candidate missing")

    extension = load(P3B / "registry-extension-v0.json")
    if extension.get("status") != "APPLIED":
        fail("Phase 3B registry extension not applied")
    preserved = extension.get("source_import_preserved") or {}
    if preserved != {"source_item_count": 68, "imported_source_item_count": 68}:
        fail("Phase 3B registry extension did not preserve Phase 2 source import")
    if extension.get("authority_change") is not False or extension.get("production_writer_change") is not False or extension.get("production_credentials_used") is not False:
        fail("Phase 3B registry extension changed authority or used production credentials")

    pins = load(P3B / "runtime-pins-v0.json")
    artifacts = pins.get("artifacts") or []
    if len(artifacts) != 8:
        fail("Phase 3B runtime pin set must contain 8 candidates")
    pin_ids = {x.get("candidate_id") for x in artifacts}
    expected_pin_ids = {
        "candidate-zitadel", "candidate-keycloak", "candidate-authentik",
        "candidate-openfga", "candidate-opa", "candidate-cedar",
        "candidate-infisical-agent-vault", "candidate-openbao",
    }
    if pin_ids != expected_pin_ids or any(x.get("status") != "RESOLVED" for x in artifacts):
        fail("Phase 3B immutable artifact pins incomplete")
    for row in artifacts:
        if row.get("candidate_id") == "candidate-cedar":
            if not row.get("sha256") or row.get("artifact") != "crates.io:cedar-policy@4.13.0":
                fail("Cedar crate pin missing")
        else:
            if not row.get("linux_amd64_digest") or not str(row.get("linux_amd64_digest")).startswith("sha256:"):
                fail("OCI linux/amd64 digest missing: " + str(row.get("candidate_id")))

    admission = load(P3B / "admission-v0.json")
    if admission.get("status") != "ADMISSION_RESEARCH_COMPLETE_LAB_SMOKES_PENDING":
        fail("Phase 3B admission status mismatch")
    if admission.get("authority_change") is not False or admission.get("production_writer_change") is not False:
        fail("Phase 3B admission changed authority/writers")
    if admission.get("production_credentials_used") is not False or admission.get("production_secret_material_used") is not False:
        fail("Phase 3B admission used production credential material")
    rows = {x.get("candidate_id"): x for x in admission.get("candidates") or []}
    if set(rows) != expected_pin_ids:
        fail("Phase 3B admission candidate set mismatch")
    admitted = {cid for cid,row in rows.items() if row.get("admission_verdict") == "ADMITTED"}
    expected_admitted = {
        "candidate-zitadel", "candidate-keycloak", "candidate-authentik",
        "candidate-openfga", "candidate-opa", "candidate-cedar",
        "candidate-infisical-agent-vault", "candidate-openbao",
    }
    if admitted != expected_admitted:
        fail("Phase 3B admitted set mismatch")
    if rows["candidate-zitadel"].get("admission_verdict") != "ADMITTED":
        fail("ZITADEL must be admitted after explicit owner license resolution")
    if rows["candidate-zitadel"].get("license_review") != "PASS_OWNER_ACCEPTED_AGPL_BOUNDARY_FOR_LAB":
        fail("ZITADEL owner AGPL decision marker missing")
    if "AGPL-3.0" not in str(rows["candidate-zitadel"].get("license")):
        fail("ZITADEL license caveat missing")

    lab_authz = {"candidate-openfga", "candidate-opa", "candidate-cedar"}
    lab_identity = {"candidate-zitadel", "candidate-keycloak", "candidate-authentik"}
    lab_credential = {"candidate-infisical-agent-vault", "candidate-openbao"}
    pending_admitted = expected_admitted - lab_authz - lab_identity - lab_credential
    for cid in lab_authz | lab_identity | lab_credential:
        item = by_id.get(cid) or {}
        if item.get("lifecycle_state") != "LAB" or item.get("decision_verdict") != "LAB_VALIDATED":
            fail("LAB candidate registry state mismatch: " + cid)
        if item.get("authority_role") != "NONE" or item.get("runtime_verification") != "PASS":
            fail("LAB candidate authority/runtime mismatch: " + cid)
    for cid in pending_admitted:
        item = by_id.get(cid) or {}
        if item.get("lifecycle_state") != "ADMITTED" or item.get("decision_verdict") != "BENCHMARK_REQUIRED":
            fail("pending LAB candidate registry state mismatch: " + cid)
        if item.get("authority_role") != "NONE" or item.get("runtime_verification") != "NOT_RUN":
            fail("pending LAB candidate authority/runtime mismatch: " + cid)

    lab_status = load(P3B / "lab-status-v0.json")
    if lab_status.get("winner_selected") is not True or lab_status.get("winner") != "composition-zitadel-opa-openbao":
        fail("Phase 3B LAB status missing selected primary composition")
    if any(lab_status.get(k) is not False for k in ("production_authority_change", "production_writer_change", "production_credentials_used")):
        fail("Phase 3B LAB status changed production authority/writer/credentials")
    authz_status = ((lab_status.get("lanes") or {}).get("authorization_policy") or {})
    if authz_status.get("status") != "DESTRUCTIVE_PASS_COMPOSITION_VALIDATED_NO_PRODUCTION_AUTHORITY":
        fail("authorization LAB status mismatch")
    if set(authz_status.get("lab_candidates") or []) != lab_authz:
        fail("authorization LAB candidate set mismatch")
    if authz_status.get("winner") != "candidate-opa" or authz_status.get("fallback") != "candidate-cedar":
        fail("authorization lane winner/fallback mismatch")
    if authz_status.get("lane_verdict_ref") != "docs/implementation/office-v2/phase3b/authorization-lane-verdict-v0.json":
        fail("authorization lane verdict ref missing")
    identity_status = ((lab_status.get("lanes") or {}).get("identity_provider") or {})
    if identity_status.get("status") != "DESTRUCTIVE_PASS_COMPOSITION_VALIDATED_NO_PRODUCTION_AUTHORITY":
        fail("identity LAB status mismatch")
    if set(identity_status.get("lab_candidates") or []) != lab_identity:
        fail("identity LAB candidate set mismatch")
    if identity_status.get("winner") != "candidate-zitadel" or identity_status.get("fallback") != "candidate-keycloak":
        fail("identity lane winner/fallback mismatch")
    if identity_status.get("specialized_reserve") != "candidate-authentik":
        fail("identity lane reserve mismatch")
    if identity_status.get("lane_verdict_ref") != "docs/implementation/office-v2/phase3b/identity-lane-verdict-v0.json":
        fail("identity lane verdict ref missing")
    if identity_status.get("pending_candidates"):
        fail("identity LAB must have no pending candidates after ZITADEL smoke")
    if len(identity_status.get("receipt_refs") or []) != 3 or len(identity_status.get("cleanup_refs") or []) != 3:
        fail("identity LAB evidence refs incomplete")

    credential_status = ((lab_status.get("lanes") or {}).get("credential_broker") or {})
    if credential_status.get("status") != "DESTRUCTIVE_PASS_COMPOSITION_VALIDATED_NO_PRODUCTION_AUTHORITY":
        fail("credential LAB status mismatch")
    if credential_status.get("winner") != "candidate-openbao" or credential_status.get("fallback") != "candidate-infisical-agent-vault":
        fail("credential lane winner/fallback mismatch")
    if credential_status.get("lane_verdict_ref") != "docs/implementation/office-v2/phase3b/credential-lane-verdict-v0.json":
        fail("credential lane verdict ref missing")
    if set(credential_status.get("lab_candidates") or []) != lab_credential:
        fail("credential LAB candidate set mismatch")
    if credential_status.get("pending_candidates"):
        fail("credential LAB must have no pending candidates after OpenBao smoke")
    if len(credential_status.get("receipt_refs") or []) != 2 or len(credential_status.get("cleanup_refs") or []) != 2:
        fail("credential LAB evidence refs incomplete")

    lab_comp = lab_status.get("composition_gate") or {}
    if lab_comp.get("status") != "PASS" or lab_comp.get("winner") != "composition-zitadel-opa-openbao":
        fail("Phase 3B LAB composition gate status/winner mismatch")
    if lab_comp.get("fixture_id") != "identity-security-destructive-20-step" or lab_comp.get("production_authority_change") is not False:
        fail("Phase 3B LAB composition fixture/authority mismatch")
    if lab_comp.get("primary") != {"identity_provider":"candidate-zitadel","authorization_policy":"candidate-opa","credential_broker":"candidate-openbao"}:
        fail("Phase 3B LAB primary composition mismatch")
    if lab_comp.get("validated_fallback_swaps") != {"identity_provider":"candidate-keycloak","authorization_policy":"candidate-cedar","credential_broker":"candidate-infisical-agent-vault"}:
        fail("Phase 3B LAB fallback composition mismatch")
    if lab_comp.get("cartesian_exhaustion_required") is not False or len(lab_comp.get("evidence_refs") or []) != 4:
        fail("Phase 3B LAB composition evidence/strategy mismatch")
    if lab_comp.get("verdict_ref") != "docs/implementation/office-v2/phase3b/composition-gate-verdict-v0.json":
        fail("Phase 3B LAB composition verdict ref missing")
    lab_wiring = lab_status.get("integration_wiring") or {}
    if lab_wiring.get("status") != "PASS" or lab_wiring.get("mode") != "LAB_SIMULATION_ONLY" or lab_wiring.get("selftest_cases") != 7:
        fail("Phase 3B LAB integration wiring status mismatch")
    if lab_wiring.get("wiring_ref") != "docs/implementation/office-v2/phase3b/integration-wiring-v0.json" or lab_wiring.get("promotion_gate_ref") != "docs/implementation/office-v2/phase3b/promotion-gates-v0.json":
        fail("Phase 3B LAB integration wiring refs mismatch")
    if lab_wiring.get("reference_implementation") != "scripts/vf_office_v2_security_wiring.py":
        fail("Phase 3B LAB integration wiring implementation ref mismatch")
    if lab_wiring.get("evidence_ref") != "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-06/integration-wiring-validation.json":
        fail("Phase 3B LAB integration wiring evidence ref mismatch")
    for field in ("network_calls_allowed", "external_effects_allowed", "production_credentials_bound", "shadow_promoted", "pilot_promoted", "production_promoted", "production_authority_change"):
        if lab_wiring.get(field) is not False:
            fail("Phase 3B LAB integration wiring unsafe field: " + field)
    lab_persistence = lab_status.get("persistence_readiness") or {}
    if lab_persistence.get("status") != "PASS" or lab_persistence.get("scope") != "LAB_ONLY_SYNTHETIC":
        fail("Phase 3B LAB persistence readiness status/scope mismatch")
    if lab_persistence.get("readiness_ref") != "docs/implementation/office-v2/phase3b/shadow-readiness-v0.json":
        fail("Phase 3B LAB persistence readiness ref mismatch")
    if lab_persistence.get("evidence_ref") != "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-06/persistence-readiness.json" or len(lab_persistence.get("evidence_sha256") or "") != 64:
        fail("Phase 3B LAB persistence evidence ref/hash mismatch")
    if any(lab_persistence.get(role) != "PASS" for role in ("opa", "openbao", "zitadel")):
        fail("Phase 3B LAB persistence component status mismatch")
    if lab_persistence.get("host_port_bindings_empty") is not True:
        fail("Phase 3B LAB persistence must expose no host ports")
    for field in ("production_credentials_used", "production_secret_material_used", "production_authority_change", "shadow_promoted"):
        if lab_persistence.get(field) is not False:
            fail("Phase 3B LAB persistence unsafe field: " + field)
    lab_runtime = lab_status.get("runtime_readiness") or {}
    if lab_runtime.get("status") != "PASS_NOT_ACTIVATED" or lab_runtime.get("selftest_cases") != 10:
        fail("Phase 3B LAB runtime readiness status/selftest mismatch")
    if lab_runtime.get("contract_ref") != "docs/implementation/office-v2/phase3b/runtime-readiness-v0.json" or lab_runtime.get("validator") != "scripts/vf_office_v2_security_shadow_doctor.py":
        fail("Phase 3B LAB runtime readiness refs mismatch")
    if lab_runtime.get("health_fail_closed") is not True or lab_runtime.get("service_plan_complete") is not True or lab_runtime.get("rollback_to_incumbents_selftest") is not True:
        fail("Phase 3B LAB runtime readiness proof incomplete")
    if lab_runtime.get("services_installed") is not False or lab_runtime.get("services_enabled") is not False:
        fail("Phase 3B pre-SHADOW services must remain inactive")
    if lab_runtime.get("dpapi_cross_process_probe") != "PASS" or len(lab_runtime.get("dpapi_evidence_sha256") or "") != 64:
        fail("Phase 3B DPAPI key-material proof missing")
    for field in ("external_effects_allowed", "production_credentials_bound", "production_authority_change", "shadow_promoted"):
        if lab_runtime.get(field) is not False:
            fail("Phase 3B LAB runtime readiness unsafe field: " + field)
    lab_shadow = lab_status.get("shadow_runtime") or {}
    if lab_shadow.get("status") != "SHADOW_ACTIVE_OBSERVER_ONLY" or lab_shadow.get("active_ref") != "docs/implementation/office-v2/phase3b/shadow-active-v0.json":
        fail("Phase 3B LAB status missing active SHADOW runtime")
    if lab_shadow.get("selected_composition") != "composition-zitadel-opa-openbao" or lab_shadow.get("project_state") != "PHASE_3B_SHADOW_ACTIVE" or lab_shadow.get("health") != "READY":
        fail("Phase 3B LAB SHADOW composition/project-state/health mismatch")
    if lab_shadow.get("fail_closed_outage_drill") != "PASS" or lab_shadow.get("restart_restore") != "PASS":
        fail("Phase 3B LAB SHADOW fail-closed/restart evidence missing")
    if lab_shadow.get("host_port_bindings_empty") is not True or lab_shadow.get("lease_managed") is not True or lab_shadow.get("production_path") != "INCUMBENTS_CANONICAL":
        fail("Phase 3B LAB SHADOW isolation/lifecycle mismatch")
    for field in ("production_credentials_used", "external_effects_allowed", "production_authority_change", "pilot_promoted"):
        if lab_shadow.get(field) is not False:
            fail("Phase 3B LAB SHADOW unsafe field: " + field)

    zit = by_id.get("candidate-zitadel") or {}
    if zit.get("lifecycle_state") != "LAB" or zit.get("decision_verdict") != "LAB_VALIDATED":
        fail("ZITADEL registry state must be LAB/LAB_VALIDATED after smoke PASS")
    if zit.get("authority_role") != "NONE" or zit.get("runtime_verification") != "PASS":
        fail("ZITADEL LAB state must have runtime PASS and no authority")

    infisical = by_id.get("candidate-infisical-agent-vault") or {}
    if infisical.get("lifecycle_state") != "LAB" or infisical.get("decision_verdict") != "LAB_VALIDATED":
        fail("Infisical registry state must be LAB/LAB_VALIDATED after smoke PASS")
    if infisical.get("authority_role") != "NONE" or infisical.get("runtime_verification") != "PASS":
        fail("Infisical LAB state must have runtime PASS and no authority")
    infisical_evidence = set(infisical.get("evidence_refs") or [])
    if "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-06/infisical-lab-smoke-pass.json" not in infisical_evidence:
        fail("Infisical LAB receipt evidence missing from registry")

    openbao = by_id.get("candidate-openbao") or {}
    if openbao.get("lifecycle_state") != "LAB" or openbao.get("decision_verdict") != "LAB_VALIDATED":
        fail("OpenBao registry state must be LAB/LAB_VALIDATED after smoke PASS")
    if openbao.get("authority_role") != "NONE" or openbao.get("runtime_verification") != "PASS":
        fail("OpenBao LAB state must have runtime PASS and no authority")
    openbao_evidence = set(openbao.get("evidence_refs") or [])
    if "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-06/openbao-lab-smoke-pass.json" not in openbao_evidence:
        fail("OpenBao LAB receipt evidence missing from registry")

    shortlist = load(P3B / "identity-security-shortlist-v0.json")
    if shortlist.get("status") != "COMPOSITION_GATE_PASS_PRIMARY_SELECTED_NO_PRODUCTION_AUTHORITY":
        fail("Phase 3B shortlist status mismatch")
    if shortlist.get("winner") != "composition-zitadel-opa-openbao" or shortlist.get("production_authority_granted") is not False:
        fail("Phase 3B shortlist primary composition/authority mismatch")
    lanes = {x.get("lane_id"): x for x in shortlist.get("lanes") or []}
    if set(lanes) != set(EXPECTED_LANES):
        fail("Phase 3B shortlist lane set mismatch")
    for lane_id, (role, incumbent, n_challengers) in EXPECTED_LANES.items():
        lane = lanes[lane_id]
        if lane.get("role") != role or lane.get("incumbent") != incumbent:
            fail("Phase 3B lane role/incumbent mismatch: " + lane_id)
        challengers = lane.get("challengers") or []
        if len(challengers) != n_challengers or len(challengers) != len(set(challengers)):
            fail("Phase 3B challenger count mismatch: " + lane_id)
        if lane_id == "phase3b-authorization-policy":
            if lane.get("winner") != "candidate-opa" or lane.get("fallback") != "candidate-cedar":
                fail("authorization lane selection mismatch")
        elif lane_id == "phase3b-identity-provider":
            if lane.get("winner") != "candidate-zitadel" or lane.get("fallback") != "candidate-keycloak" or lane.get("specialized_reserve") != "candidate-authentik":
                fail("identity lane selection mismatch")
        elif lane_id == "phase3b-credential-broker":
            if lane.get("winner") != "candidate-openbao" or lane.get("fallback") != "candidate-infisical-agent-vault":
                fail("credential lane selection mismatch")
        elif lane.get("winner") is not None:
            fail("Phase 3B lane winner selected before destructive fixture: " + lane_id)
        for cid in [incumbent, *challengers]:
            if cid not in by_id:
                fail("Phase 3B shortlist candidate missing from registry: " + cid)
        for cid in challengers:
            row = by_id[cid]
            if row.get("authority_role") != "NONE":
                fail("Phase 3B challenger has authority: " + cid)
            if lane_id not in (row.get("shortlist_lanes") or []):
                fail("Phase 3B candidate lane binding missing: " + cid)
        if lane_id == "phase3b-authorization-policy":
            if set((lane.get("candidate_admission") or {}).values()) != {"LAB"}:
                fail("authorization shortlist candidates must all be LAB after smoke")
            if not lane.get("lab_smoke_ref"):
                fail("authorization shortlist missing LAB smoke receipt")
            if lane.get("admission_status") != "DESTRUCTIVE_COMPLETE_COMPOSITION_VALIDATED_NO_PRODUCTION_AUTHORITY":
                fail("authorization destructive status mismatch")
            if lane.get("lane_verdict_ref") != "docs/implementation/office-v2/phase3b/authorization-lane-verdict-v0.json":
                fail("authorization shortlist lane verdict ref missing")
        elif lane_id == "phase3b-identity-provider":
            expected = {"candidate-zitadel":"LAB","candidate-keycloak":"LAB","candidate-authentik":"LAB"}
            if lane.get("candidate_admission") != expected:
                fail("identity shortlist admission state drift")
            refs = lane.get("lab_smoke_refs") or {}
            if set(refs) != lab_identity or not all(refs.values()):
                fail("identity shortlist LAB smoke refs incomplete")
            if lane.get("admission_status") != "DESTRUCTIVE_COMPLETE_COMPOSITION_VALIDATED_NO_PRODUCTION_AUTHORITY":
                fail("identity destructive status mismatch")
            if lane.get("lane_verdict_ref") != "docs/implementation/office-v2/phase3b/identity-lane-verdict-v0.json":
                fail("identity shortlist lane verdict ref missing")
        elif lane_id == "phase3b-credential-broker":
            expected = {"candidate-infisical-agent-vault":"LAB","candidate-openbao":"LAB"}
            if lane.get("candidate_admission") != expected:
                fail("credential shortlist admission state drift")
            refs = lane.get("lab_smoke_refs") or {}
            if set(refs) != lab_credential or not all(refs.values()):
                fail("credential shortlist LAB smoke refs incomplete")
            if lane.get("admission_status") != "DESTRUCTIVE_COMPLETE_COMPOSITION_VALIDATED_NO_PRODUCTION_AUTHORITY":
                fail("credential destructive status mismatch")
            if lane.get("lane_verdict_ref") != "docs/implementation/office-v2/phase3b/credential-lane-verdict-v0.json":
                fail("credential shortlist lane verdict ref missing")

    identity_verdict = load(P3B / "identity-lane-verdict-v0.json")
    if identity_verdict.get("status") != "LANE_WINNER_SELECTED_FOR_COMPOSITION_NO_PRODUCTION_AUTHORITY":
        fail("identity lane verdict status mismatch")
    if identity_verdict.get("winner") != "candidate-zitadel" or identity_verdict.get("fallback") != "candidate-keycloak" or identity_verdict.get("specialized_reserve") != "candidate-authentik":
        fail("identity lane verdict selection mismatch")
    if identity_verdict.get("production_authority_change") is not False or identity_verdict.get("shadow_or_pilot_promotion") is not False:
        fail("identity lane verdict changed authority or promoted runtime")
    for cid in ("candidate-zitadel", "candidate-keycloak", "candidate-authentik", "incumbent-current-service-identity"):
        sc = load(P3B / "scorecards" / f"identity-{cid}.json")
        if sc.get("fixture_id") != "identity-security-destructive-20-step" or sc.get("candidate_id") != cid:
            fail("identity scorecard identity/fixture mismatch: " + cid)

    authz_verdict = load(P3B / "authorization-lane-verdict-v0.json")
    if authz_verdict.get("status") != "LANE_WINNER_SELECTED_FOR_COMPOSITION_NO_PRODUCTION_AUTHORITY":
        fail("authorization lane verdict status mismatch")
    if authz_verdict.get("winner") != "candidate-opa" or authz_verdict.get("fallback") != "candidate-cedar":
        fail("authorization lane verdict winner/fallback mismatch")
    if authz_verdict.get("production_authority_change") is not False or authz_verdict.get("shadow_or_pilot_promotion") is not False:
        fail("authorization lane verdict changed authority or promoted runtime")
    for cid in ("candidate-opa", "candidate-cedar", "candidate-openfga", "incumbent-current-authorization"):
        sc = load(P3B / "scorecards" / f"authorization-{cid}.json")
        if sc.get("fixture_id") != "identity-security-destructive-20-step" or sc.get("candidate_id") != cid:
            fail("authorization scorecard identity/fixture mismatch: " + cid)

    credential_verdict = load(P3B / "credential-lane-verdict-v0.json")
    if credential_verdict.get("status") != "LANE_WINNER_SELECTED_FOR_COMPOSITION_NO_PRODUCTION_AUTHORITY":
        fail("credential lane verdict status mismatch")
    if credential_verdict.get("winner") != "candidate-openbao" or credential_verdict.get("fallback") != "candidate-infisical-agent-vault":
        fail("credential lane verdict winner/fallback mismatch")
    if credential_verdict.get("production_authority_change") is not False or credential_verdict.get("shadow_or_pilot_promotion") is not False:
        fail("credential lane verdict changed authority or promoted runtime")
    for cid in ("candidate-openbao", "candidate-infisical-agent-vault"):
        sc = load(P3B / "scorecards" / f"credential-{cid}.json")
        if sc.get("fixture_id") != "identity-security-destructive-20-step" or sc.get("candidate_id") != cid:
            fail("credential scorecard identity/fixture mismatch: " + cid)
    expected_primary = {
        "identity_provider": "candidate-zitadel",
        "authorization_policy": "candidate-opa",
        "credential_broker": "candidate-openbao",
    }
    expected_fallbacks = {
        "identity_provider": "candidate-keycloak",
        "authorization_policy": "candidate-cedar",
        "credential_broker": "candidate-infisical-agent-vault",
    }
    comp = shortlist.get("composition_gate") or {}
    if not all(comp.get(k) is True for k in ("winner_selection_per_lane_allowed_only_after_fixture", "phase3b_closure_requires_cross_role_composition_pass", "no_lane_winner_grants_production_authority")):
        fail("Phase 3B composition gate policy incomplete")
    if comp.get("status") != "PASS" or comp.get("winner") != "composition-zitadel-opa-openbao":
        fail("Phase 3B composition gate result mismatch")
    if comp.get("fixture_id") != "identity-security-destructive-20-step" or comp.get("primary") != expected_primary:
        fail("Phase 3B composition fixture/primary mismatch")
    if comp.get("validated_fallback_swaps") != expected_fallbacks or comp.get("cartesian_exhaustion_required") is not False:
        fail("Phase 3B composition fallback strategy mismatch")
    if comp.get("verdict_ref") != "docs/implementation/office-v2/phase3b/composition-gate-verdict-v0.json" or len(comp.get("evidence_refs") or []) != 4:
        fail("Phase 3B composition verdict/evidence refs incomplete")

    composition_verdict = load(P3B / "composition-gate-verdict-v0.json")
    if composition_verdict.get("status") != "SELECTED_FOR_INTEGRATION_NO_PRODUCTION_AUTHORITY":
        fail("Phase 3B composition verdict status mismatch")
    if composition_verdict.get("fixture_id") != "identity-security-destructive-20-step" or composition_verdict.get("winner") != "composition-zitadel-opa-openbao":
        fail("Phase 3B composition verdict fixture/winner mismatch")
    if composition_verdict.get("phase3b_gate_closed") is not True or composition_verdict.get("cartesian_exhaustion_required") is not False:
        fail("Phase 3B composition verdict closure/strategy mismatch")
    if any(composition_verdict.get(k) is not False for k in (
        "production_authority_change", "production_writer_change", "production_credentials_used",
        "production_secret_material_used", "shadow_or_pilot_promotion",
    )):
        fail("Phase 3B composition verdict changed production authority")
    primary = composition_verdict.get("primary_composition") or {}
    if {k: primary.get(k) for k in expected_primary} != expected_primary or primary.get("benchmark_status") != "PASS":
        fail("Phase 3B primary composition verdict mismatch")
    fallback_rows = composition_verdict.get("validated_fallback_swaps") or {}
    if set(fallback_rows) != set(expected_fallbacks):
        fail("Phase 3B fallback verdict set mismatch")
    for role, candidate in expected_fallbacks.items():
        row = fallback_rows.get(role) or {}
        if row.get("candidate") != candidate or row.get("benchmark_status") != "PASS":
            fail("Phase 3B fallback verdict mismatch: " + role)
        ev = row.get("evidence") or {}
        if not ev.get("path") or len(ev.get("sha256") or "") != 64:
            fail("Phase 3B fallback evidence incomplete: " + role)
    primary_ev = primary.get("evidence") or {}
    if not primary_ev.get("path") or len(primary_ev.get("sha256") or "") != 64:
        fail("Phase 3B primary evidence incomplete")

    wiring = load(P3B / "integration-wiring-v0.json")
    if wiring.get("status") != "LAB_WIRING_DEFINED_NO_PRODUCTION_AUTHORITY" or wiring.get("mode") != "LAB_SIMULATION_ONLY":
        fail("Phase 3B integration wiring status/mode mismatch")
    if wiring.get("selected_composition") != "composition-zitadel-opa-openbao" or wiring.get("credential_trust_class") != "LAB_ONLY_SECRET":
        fail("Phase 3B integration wiring composition/trust mismatch")
    for field in (
        "production_authority_change", "production_writer_change", "production_credentials_allowed",
        "production_secret_material_allowed", "external_effects_allowed", "network_calls_allowed_by_reference_implementation",
    ):
        if wiring.get(field) is not False:
            fail("Phase 3B integration wiring unsafe field: " + field)
    wiring_roles = wiring.get("roles") or {}
    for role, candidate in expected_primary.items():
        if (wiring_roles.get(role) or {}).get("primary") != candidate or (wiring_roles.get(role) or {}).get("fallback") != expected_fallbacks[role]:
            fail("Phase 3B integration wiring role selection mismatch: " + role)
    pipeline = wiring.get("pipeline") or []
    expected_pipeline = ["request_intake", "identity_verify", "claim_normalize", "authorize", "credential_scope_check", "credential_resolution_decision", "effect_gate", "evidence_finalize"]
    if [row.get("id") for row in pipeline] != expected_pipeline or not all(row.get("fail_closed") is True for row in pipeline):
        fail("Phase 3B integration wiring pipeline must remain ordered and fail-closed")
    evidence_contract = wiring.get("evidence_contract") or {}
    if evidence_contract.get("raw_secret_material_allowed") is not False or evidence_contract.get("raw_bearer_material_allowed") is not False:
        fail("Phase 3B integration wiring evidence redaction drift")
    if any(marker in json.dumps(wiring, sort_keys=True).lower() for marker in ("http://", "https://", "127.0.0.1", "localhost")):
        fail("Phase 3B integration wiring must not embed runtime endpoints")

    promotion = load(P3B / "promotion-gates-v0.json")
    if promotion.get("status") != "SHADOW_ACTIVE_OBSERVER_ONLY_PILOT_BLOCKED" or promotion.get("current_authority") != "INCUMBENTS_CANONICAL":
        fail("Phase 3B promotion gate active SHADOW status/authority mismatch")
    if promotion.get("shadow_readiness_ref") != "docs/implementation/office-v2/phase3b/shadow-readiness-v0.json":
        fail("Phase 3B shadow readiness ref missing")
    if promotion.get("current_project_state_must_remain") != "PHASE_3B_SHADOW_ACTIVE":
        fail("Phase 3B promotion gate project-state mismatch")
    for field in ("production_authority_change", "production_writer_change", "production_credentials_bound", "pilot_promoted", "production_promoted"):
        if promotion.get(field) is not False:
            fail("Phase 3B promotion unsafe field: " + field)
    if promotion.get("shadow_promoted") is not True:
        fail("Phase 3B SHADOW promotion must be explicit and recorded")
    integration_gate = promotion.get("integration_gate") or {}
    if integration_gate.get("status") != "PASS_NO_RUNTIME_PROMOTION":
        fail("Phase 3B integration gate must remain a historical non-promotion gate")
    shadow_gate = promotion.get("shadow_gate") or {}
    if shadow_gate.get("status") != "PASS_SHADOW_ACTIVE_OBSERVER_ONLY":
        fail("Phase 3B SHADOW gate must record observer-only active state")
    persistence = shadow_gate.get("persistence_readiness") or {}
    if persistence.get("status") != "PASS" or persistence.get("evidence_ref") != "D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-06/persistence-readiness.json" or len(persistence.get("evidence_sha256") or "") != 64:
        fail("Phase 3B promotion gate persistence evidence mismatch")
    if any(persistence.get(role) != "PASS" for role in ("opa", "openbao", "zitadel")):
        fail("Phase 3B promotion gate persistence component mismatch")
    gate_regression = shadow_gate.get("exact_regression") or {}
    if gate_regression.get("status") != "PASS" or gate_regression.get("suite") != "116/116" or gate_regression.get("repository_files_unchanged") is not True:
        fail("Phase 3B promotion gate exact regression mismatch")
    if gate_regression.get("production_authority_change") is not False or gate_regression.get("shadow_promoted") is not False:
        fail("Phase 3B historical pre-promotion regression receipt drift")
    if (shadow_gate.get("remaining_preconditions") or []) != []:
        fail("Phase 3B SHADOW gate should have no remaining SHADOW preconditions after explicit promotion")
    runtime_evidence = shadow_gate.get("runtime_evidence") or {}
    if runtime_evidence.get("status") != "PASS" or runtime_evidence.get("shadow_active_ref") != "docs/implementation/office-v2/phase3b/shadow-active-v0.json":
        fail("Phase 3B SHADOW runtime evidence missing")
    if runtime_evidence.get("project_state_checkpoint") != "office-v2-phase3b-v0-cp014-shadow-active" or len(runtime_evidence.get("project_state_content_hash") or "") != 64:
        fail("Phase 3B SHADOW project-state evidence mismatch")
    if runtime_evidence.get("outage_fail_closed") != "PASS_3_OF_3" or runtime_evidence.get("restart_restore") != "PASS" or runtime_evidence.get("temporary_task_cleanup") != "PASS":
        fail("Phase 3B SHADOW operational evidence incomplete")
    if runtime_evidence.get("production_path") != "INCUMBENTS_CANONICAL" or runtime_evidence.get("external_effects_allowed") is not False:
        fail("Phase 3B SHADOW runtime authority boundary drift")
    pilot_gate = promotion.get("pilot_gate") or {}
    if pilot_gate.get("status") != "READINESS_SCOPE_SELECTED_LIVE_PROOF_PENDING" or pilot_gate.get("production_class_must_be_explicitly_rebound") is not True:
        fail("Phase 3B PILOT readiness gate status mismatch")
    if pilot_gate.get("selected_scope_ref") != "docs/implementation/office-v2/phase3b/pilot-scope-v0.json" or pilot_gate.get("selected_scope_id") != "instagram-publisher-snapshot-read":
        fail("Phase 3B PILOT selected scope mismatch")
    if pilot_gate.get("selected_credential_class") != "PRODUCTION_READ" or pilot_gate.get("static_source_proof") != "PASS":
        fail("Phase 3B PILOT credential/static proof mismatch")
    if not pilot_gate.get("remaining_live_preconditions") or "separate explicit PILOT promotion receipt" not in pilot_gate.get("remaining_live_preconditions"):
        fail("Phase 3B PILOT live proof/promotion boundary missing")
    if (promotion.get("production_gate") or {}).get("implicit_promotion_allowed") is not False:
        fail("Phase 3B implicit production promotion must remain forbidden")

    readiness = load(P3B / "shadow-readiness-v0.json")
    if readiness.get("status") != "PRE_SHADOW_READINESS_COMPLETE_NO_PROMOTION" or readiness.get("selected_composition") != "composition-zitadel-opa-openbao":
        fail("Phase 3B shadow readiness status/composition mismatch")
    if readiness.get("current_authority") != "NONE" or readiness.get("current_project_state_must_remain") != "PHASE_3A_CLOSED_GREEN__PHASE_3B_READY":
        fail("Phase 3B shadow readiness authority/project-state mismatch")
    for field in ("production_authority_change", "production_writer_change", "production_credentials_bound", "production_secret_material_used", "external_effects_allowed", "shadow_promoted", "pilot_promoted", "production_promoted"):
        if readiness.get(field) is not False:
            fail("Phase 3B shadow readiness unsafe field: " + field)
    readiness_wiring = readiness.get("integration_wiring") or {}
    if readiness_wiring.get("status") != "PASS" or readiness_wiring.get("mode") != "LAB_SIMULATION_ONLY" or len(readiness_wiring.get("evidence_sha256") or "") != 64:
        fail("Phase 3B shadow readiness integration proof mismatch")
    readiness_persistence = readiness.get("persistence_restore") or {}
    if readiness_persistence.get("status") != "PASS" or readiness_persistence.get("scope") != "LAB_ONLY_SYNTHETIC" or len(readiness_persistence.get("evidence_sha256") or "") != 64:
        fail("Phase 3B shadow readiness persistence proof mismatch")
    if (readiness_persistence.get("opa") or {}).get("restored_allow") is not True:
        fail("Phase 3B OPA restore readiness mismatch")
    if (readiness_persistence.get("openbao") or {}).get("storage_backend") != "raft" or (readiness_persistence.get("openbao") or {}).get("restored_value_match") is not True:
        fail("Phase 3B OpenBao restore readiness mismatch")
    if (readiness_persistence.get("zitadel") or {}).get("restored_identity_token_http") != 200:
        fail("Phase 3B ZITADEL restore readiness mismatch")
    readiness_runtime = readiness.get("runtime_readiness") or {}
    if readiness_runtime.get("status") != "PASS_NOT_ACTIVATED" or readiness_runtime.get("validator_selftest_cases") != 10:
        fail("Phase 3B shadow runtime readiness status/selftest mismatch")
    if readiness_runtime.get("contract_ref") != "docs/implementation/office-v2/phase3b/runtime-readiness-v0.json" or readiness_runtime.get("validator") != "scripts/vf_office_v2_security_shadow_doctor.py":
        fail("Phase 3B shadow runtime readiness refs mismatch")
    if readiness_runtime.get("health_fail_closed") is not True or readiness_runtime.get("service_plan_complete") is not True or readiness_runtime.get("rollback_to_incumbents_selftest") is not True:
        fail("Phase 3B shadow runtime readiness proof incomplete")
    if readiness_runtime.get("services_installed") is not False or readiness_runtime.get("services_enabled") is not False:
        fail("Phase 3B shadow readiness must not activate services")
    if readiness_runtime.get("dpapi_cross_process_probe") != "PASS" or len(readiness_runtime.get("dpapi_evidence_sha256") or "") != 64:
        fail("Phase 3B shadow readiness DPAPI proof mismatch")
    for field in ("production_authority_change", "shadow_promoted"):
        if readiness_runtime.get(field) is not False:
            fail("Phase 3B shadow runtime readiness unsafe field: " + field)
    readiness_regression = readiness.get("exact_regression") or {}
    if readiness_regression.get("status") != "PASS" or readiness_regression.get("suite") != "116/116" or readiness_regression.get("validated_after_rebase") is not True or readiness_regression.get("repository_files_unchanged") is not True:
        fail("Phase 3B shadow exact regression proof mismatch")
    if readiness_regression.get("services_activated") is not False or readiness_regression.get("production_authority_change") is not False or readiness_regression.get("shadow_promoted") is not False:
        fail("Phase 3B shadow exact regression crossed activation/authority boundary")
    remaining = readiness.get("remaining_preconditions_before_shadow_can_be_considered") or []
    if remaining != ["separate explicit project-state SHADOW promotion receipt"]:
        fail("Phase 3B historical shadow readiness remaining preconditions drift")

    active = load(P3B / "shadow-active-v0.json")
    if active.get("status") != "SHADOW_ACTIVE_OBSERVER_ONLY" or active.get("selected_composition") != "composition-zitadel-opa-openbao" or active.get("mode") != "SHADOW_OBSERVER_ONLY":
        fail("Phase 3B active SHADOW receipt status/composition/mode mismatch")
    if active.get("promotion_baseline_sha") != "5799dd5553b10b8dac4e5119e9b71a0fb343bac7":
        fail("Phase 3B active SHADOW promotion baseline mismatch")
    project_state = active.get("project_state") or {}
    if project_state.get("phase") != "PHASE_3B_SHADOW_ACTIVE" or project_state.get("checkpoint_id") != "office-v2-phase3b-v0-cp014-shadow-active":
        fail("Phase 3B active SHADOW project state mismatch")
    for field in ("checkpoint_content_hash", "checkpoint_file_sha256", "promotion_receipt_sha256"):
        if len(project_state.get(field) or "") != 64:
            fail("Phase 3B active SHADOW project-state hash missing: " + field)
    runtime = active.get("runtime") or {}
    if runtime.get("target_active") is not True or runtime.get("target_enabled") is not False or runtime.get("lease_managed") is not True or runtime.get("permanent_windows_task") != "OfficeV2 LAB Lease":
        fail("Phase 3B active SHADOW lifecycle ownership mismatch")
    if runtime.get("new_permanent_windows_tasks") != 0 or runtime.get("candidate_host_port_bindings_empty") is not True or runtime.get("production_endpoint_bindings") is not False:
        fail("Phase 3B active SHADOW runtime isolation mismatch")
    health = active.get("health") or {}
    for field in ("identity_ready", "identity_issue_and_readback", "authorization_health", "authorization_allow_control", "authorization_deny_control", "credential_broker_health", "credential_exact_scope_read", "credential_unrelated_scope_denied", "credential_value_hash_match"):
        if health.get(field) is not True:
            fail("Phase 3B active SHADOW health proof missing: " + field)
    if health.get("status") != "READY" or health.get("automatic_fallback_to_seek_allow") is not False or health.get("shadow_result") != "SHADOW_OBSERVE_ONLY":
        fail("Phase 3B active SHADOW health semantics mismatch")
    outage = active.get("fail_closed_outage_drill") or {}
    if outage.get("status") != "PASS" or outage.get("cases") != 3 or outage.get("final_status") != "READY" or len(outage.get("evidence_sha256") or "") != 64:
        fail("Phase 3B active SHADOW outage drill evidence mismatch")
    restart = active.get("restart_restore") or {}
    if restart.get("status") != "PASS" or restart.get("wsl_terminate") is not True or restart.get("lab_lease_restart") is not True or restart.get("dpapi_bundle_unchanged") is not True or restart.get("marker_unchanged") is not True or restart.get("health_after_restore") != "READY" or len(restart.get("evidence_sha256") or "") != 64:
        fail("Phase 3B active SHADOW restart/restore evidence mismatch")
    key_material = active.get("key_material") or {}
    if key_material.get("status") != "PASS" or key_material.get("credential_class") != "LAB_ONLY_SECRET" or key_material.get("protection") != "Windows DPAPI CurrentUser":
        fail("Phase 3B active SHADOW key material contract mismatch")
    for field in ("acl_protected", "runtime_plaintext_only"):
        if key_material.get(field) is not True:
            fail("Phase 3B active SHADOW key-material safety missing: " + field)
    for field in ("openbao_root_token_persisted", "raw_secret_recorded_in_evidence", "production_credentials_used"):
        if key_material.get(field) is not False:
            fail("Phase 3B active SHADOW key-material unsafe field: " + field)
    cleanup = active.get("temporary_task_cleanup") or {}
    if cleanup.get("status") != "PASS" or cleanup.get("removed_count") != 14 or cleanup.get("remaining_officev2_tasks") != ["OfficeV2 LAB Lease"] or cleanup.get("lab_lease_running") is not True:
        fail("Phase 3B active SHADOW temporary-task cleanup mismatch")
    authority = active.get("authority") or {}
    if authority.get("candidate_authority") != "NONE" or authority.get("production_path") != "INCUMBENTS_CANONICAL":
        fail("Phase 3B active SHADOW authority owner mismatch")
    for field in ("production_authority_change", "production_writer_change", "production_credentials_bound", "production_secret_material_used", "external_effects_allowed", "canonical_business_truth_change"):
        if authority.get(field) is not False:
            fail("Phase 3B active SHADOW authority boundary drift: " + field)
    if (active.get("pilot_gate") or {}).get("status") != "BLOCKED":
        fail("Phase 3B active SHADOW must not imply PILOT")

    pilot_scope = load(P3B / "pilot-scope-v0.json")
    if pilot_scope.get("status") != "PILOT_SCOPE_FROZEN_LIVE_PROOF_PENDING" or pilot_scope.get("scope_id") != "instagram-publisher-snapshot-read":
        fail("Phase 3B PILOT scope status/id mismatch")
    if pilot_scope.get("selected_composition") != "composition-zitadel-opa-openbao" or pilot_scope.get("credential_class") != "PRODUCTION_READ":
        fail("Phase 3B PILOT scope composition/credential class mismatch")
    if pilot_scope.get("production_domain") != "instagram_read" or pilot_scope.get("write_allowed") is not False:
        fail("Phase 3B PILOT must remain bounded read-only")
    provider = pilot_scope.get("provider") or {}
    if provider.get("service") != "velvetos-instagram-publisher" or provider.get("credential_binding") != "SNAPSHOT_TOKEN":
        fail("Phase 3B PILOT provider binding mismatch")
    if provider.get("existing_control_token_reuse_forbidden") is not True or provider.get("meta_access_token_binding_forbidden") is not True:
        fail("Phase 3B PILOT must forbid incumbent control/meta credential reuse")
    source_contract = pilot_scope.get("source_contract") or {}
    if source_contract.get("reader_guard") != "requireRead" or source_contract.get("writer_guard") != "requireAdmin" or source_contract.get("snapshot_token_can_authorize_write") is not False:
        fail("Phase 3B PILOT source read/write separation drift")
    lifecycle = pilot_scope.get("provider_native_credential_lifecycle") or {}
    if lifecycle.get("old_token_after_rotation_must_return") != 401 or lifecycle.get("revoked_token_must_return") != 401 or lifecycle.get("current_token_read_must_return") != 200 or lifecycle.get("current_token_write_must_return") != 401:
        fail("Phase 3B PILOT provider-native lifecycle expectations drift")
    broker = pilot_scope.get("credential_broker_binding") or {}
    if broker.get("broker") != "candidate-openbao" or broker.get("exact_scope_only") is not True or broker.get("control_token_forbidden") is not True or broker.get("meta_access_token_forbidden") is not True:
        fail("Phase 3B PILOT OpenBao exact-scope boundary drift")
    if (pilot_scope.get("promotion") or {}).get("pilot_promoted") is not False:
        fail("Phase 3B PILOT scope must not self-promote")

    pilot_readiness = load(P3B / "pilot-readiness-v0.json")
    if pilot_readiness.get("status") != "STATIC_READINESS_PASS_LIVE_PROOF_PENDING" or pilot_readiness.get("scope_id") != "instagram-publisher-snapshot-read":
        fail("Phase 3B PILOT readiness status/scope mismatch")
    if pilot_readiness.get("credential_class") != "PRODUCTION_READ" or pilot_readiness.get("pilot_promoted") is not False:
        fail("Phase 3B PILOT readiness credential/promotion mismatch")
    cf = pilot_readiness.get("cloudflare_preflight") or {}
    if cf.get("status") != "PASS" or cf.get("authenticated") is not True or cf.get("snapshot_token_currently_present") is not False:
        fail("Phase 3B PILOT Cloudflare preflight mismatch")
    static = pilot_readiness.get("static_source_proof") or {}
    if static.get("snapshot_token_is_read_only") is not True or static.get("write_endpoints_require_control_token") is not True:
        fail("Phase 3B PILOT static source proof mismatch")
    remaining = pilot_readiness.get("remaining_preconditions") or []
    for required in ("provider-native rotation proof: old token=401 new token=200", "provider-native revocation proof: revoked token=401", "separate explicit PILOT promotion receipt"):
        if required not in remaining:
            fail("Phase 3B PILOT remaining precondition missing: " + required)

    wiring_source = WIRING_SCRIPT.read_text(encoding="utf-8-sig")
    for forbidden_import in ("import requests", "from requests", "import httpx", "from httpx", "import socket", "import urllib"):
        if forbidden_import in wiring_source:
            fail("Phase 3B reference wiring may not import network client: " + forbidden_import)
    selftest = subprocess.run([sys.executable, str(WIRING_SCRIPT), "selftest"], cwd=ROOT, text=True, capture_output=True, timeout=30)
    if selftest.returncode != 0 or "selftest=7" not in selftest.stdout or "external_effect=NONE" not in selftest.stdout:
        fail("Phase 3B integration wiring selftest failed: " + (selftest.stderr.strip() or selftest.stdout.strip()))
    shadow_source = SHADOW_DOCTOR.read_text(encoding="utf-8-sig")
    for forbidden_import in ("import requests", "from requests", "import httpx", "from httpx", "import socket", "import urllib"):
        if forbidden_import in shadow_source:
            fail("Phase 3B shadow doctor may not import network client: " + forbidden_import)
    shadow_selftest = subprocess.run([sys.executable, str(SHADOW_DOCTOR), "selftest"], cwd=ROOT, text=True, capture_output=True, timeout=30)
    if shadow_selftest.returncode != 0 or "selftest=10" not in shadow_selftest.stdout or "services=NOT_ACTIVATED" not in shadow_selftest.stdout or "effect=NONE" not in shadow_selftest.stdout:
        fail("Phase 3B shadow readiness selftest failed: " + (shadow_selftest.stderr.strip() or shadow_selftest.stdout.strip()))

    readme = (P3B / "README.md").read_text(encoding="utf-8-sig")
    for marker in ("CROSS-ROLE COMPOSITION PASS", "SHADOW ACTIVE", "OBSERVER-ONLY", "FAIL-CLOSED", "RESTART-RESTORE PASS", "PILOT SCOPE SELECTED", "LIVE PROOF PENDING", "PILOT BLOCKED", "NO PRODUCTION AUTHORITY CHANGE", "Authentication never implies authorization", "shared 20-step composition fixture", "composition-gate-verdict-v0.json", "LAB_SIMULATION_ONLY", "promotion-gates-v0.json", "shadow-readiness-v0.json", "shadow-active-v0.json", "OfficeV2 LAB Lease"):
        if marker not in readme:
            fail("Phase 3B README missing safety/composition marker: " + marker)

    print(f"OK office-v2-phase3b contract=FROZEN fixture=20-STEP lanes=3 candidates={len(items)} source-import=68/68 winner=composition-zitadel-opa-openbao shadow=ACTIVE pilot_scope=instagram-publisher-snapshot-read pilot=BLOCKED_LIVE_PROOF_PENDING production=INCUMBENTS_CANONICAL")

if __name__ == "__main__":
    main()
