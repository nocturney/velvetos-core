#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"
P3B = ROOT / "docs" / "implementation" / "office-v2" / "phase3b"

REQUIRED = [
    P3B / "README.md",
    P3B / "identity-security-contract-v0.json",
    P3B / "identity-security-destructive-v0.json",
    P3B / "identity-security-shortlist-v0.json",
    P3B / "registry-extension-v0.json",
    P3B / "runtime-pins-v0.json",
    P3B / "admission-v0.json",
    P3B / "lab-status-v0.json",
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
        "candidate-keycloak", "candidate-authentik",
        "candidate-openfga", "candidate-opa", "candidate-cedar",
        "candidate-infisical-agent-vault", "candidate-openbao",
    }
    if admitted != expected_admitted:
        fail("Phase 3B admitted set mismatch")
    if rows["candidate-zitadel"].get("admission_verdict") != "DEFERRED_WITH_REASON":
        fail("ZITADEL must remain license-deferred until explicit license resolution")
    if "AGPL-3.0" not in str(rows["candidate-zitadel"].get("license")):
        fail("ZITADEL license caveat missing")

    lab_authz = {"candidate-openfga", "candidate-opa", "candidate-cedar"}
    pending_admitted = expected_admitted - lab_authz
    for cid in lab_authz:
        item = by_id.get(cid) or {}
        if item.get("lifecycle_state") != "LAB" or item.get("decision_verdict") != "LAB_VALIDATED":
            fail("authorization LAB candidate registry state mismatch: " + cid)
        if item.get("authority_role") != "NONE" or item.get("runtime_verification") != "PASS":
            fail("authorization LAB candidate authority/runtime mismatch: " + cid)
    for cid in pending_admitted:
        item = by_id.get(cid) or {}
        if item.get("lifecycle_state") != "ADMITTED" or item.get("decision_verdict") != "BENCHMARK_REQUIRED":
            fail("pending LAB candidate registry state mismatch: " + cid)
        if item.get("authority_role") != "NONE" or item.get("runtime_verification") != "NOT_RUN":
            fail("pending LAB candidate authority/runtime mismatch: " + cid)

    lab_status = load(P3B / "lab-status-v0.json")
    if lab_status.get("winner_selected") is not False or lab_status.get("production_authority_change") is not False:
        fail("Phase 3B LAB status selected winner or changed authority")
    authz_status = ((lab_status.get("lanes") or {}).get("authorization_policy") or {})
    if authz_status.get("status") != "LAB_SMOKE_PASS_DESTRUCTIVE_FIXTURE_PENDING":
        fail("authorization LAB status mismatch")
    if set(authz_status.get("lab_candidates") or []) != lab_authz:
        fail("authorization LAB candidate set mismatch")

    zit = by_id.get("candidate-zitadel") or {}
    if zit.get("lifecycle_state") != "RESEARCHED" or zit.get("decision_verdict") != "DEFERRED_WITH_REASON":
        fail("ZITADEL registry state must remain researched/deferred")

    shortlist = load(P3B / "identity-security-shortlist-v0.json")
    if shortlist.get("status") != "AUTHORIZATION_LANE_LAB_VALIDATED_OTHER_LANES_PENDING_NO_WINNER":
        fail("Phase 3B shortlist status mismatch")
    if shortlist.get("winner") is not None or shortlist.get("production_authority_granted") is not False:
        fail("Phase 3B shortlist selected winner or authority prematurely")
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
        if lane.get("winner") is not None:
            fail("Phase 3B lane winner selected before LAB: " + lane_id)
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
        elif lane_id == "phase3b-identity-provider":
            expected = {"candidate-zitadel":"DEFERRED_WITH_REASON","candidate-keycloak":"ADMITTED","candidate-authentik":"ADMITTED"}
            if lane.get("candidate_admission") != expected:
                fail("identity shortlist admission state drift")
        elif lane_id == "phase3b-credential-broker":
            expected = {"candidate-infisical-agent-vault":"ADMITTED","candidate-openbao":"ADMITTED"}
            if lane.get("candidate_admission") != expected:
                fail("credential shortlist admission state drift")

    comp = shortlist.get("composition_gate") or {}
    if not all(comp.get(k) is True for k in ("winner_selection_per_lane_allowed_only_after_fixture", "phase3b_closure_requires_cross_role_composition_pass", "no_lane_winner_grants_production_authority")):
        fail("Phase 3B composition gate incomplete")

    readme = (P3B / "README.md").read_text(encoding="utf-8-sig")
    for marker in ("NO WINNER", "NO PRODUCTION AUTHORITY CHANGE", "Authentication never implies authorization", "shared 20-step composition fixture"):
        if marker not in readme:
            fail("Phase 3B README missing safety marker: " + marker)

    print(f"OK office-v2-phase3b contract=FROZEN fixture=20-STEP lanes=3 candidates={len(items)} source-import=68/68 winner=NONE authority=NONE")

if __name__ == "__main__":
    main()
