#!/usr/bin/env python3
"""#604 read-only issuer/provenance guard before ANY proposed privileged Git sink.

Historical, unsigned Github connector GETs establish facts about ONE PR and
one active repo ruleset. They never establish a live provider lease, a trusted
sole credential holder, trusted PR-authored QA policy, or commit authority.

Modes: selftest / inspect ONLY. Never opens sockets, starts subprocesses,
executes source, performs Git operations, reads credentials or mints leases.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = (ROOT / "docs/implementation/office-v2/phase2"
            / "p0-604-github-ci-trust-ingress-readonly-2026-10-11.json")
SOURCE_REL = ("docs/implementation/office-v2/phase2/"
              "quarantined-new-model-sources-2026-10-11/"
              "mac-qwen4b-tag-byteexact-c1.py.txt")
SOURCE_SHA = "084d446873fb871ad444f7704b7868b72e599829b9da6e0a2fca0f972d4dae6a"
SOURCE_BLOB = "7ec37475b86cabe728b95be37e38e984a74e6264"
PR_HEAD = "33370b0a3750cfe4749c90f40349b1b8ffd9c4f0"
CORE_FLOW = ".github/workflows/check-all.yml"
C1_FLOW = ".github/workflows/office-p0-hosted-mac4b-c1-nativeblob-qa.yml"
MAIN_AT_SNAPSHOT = "975c72ed2c757a0c3d08776aa76f8d11ba687d71"
SCHEMA = "velvetos.office-v2.p0-604-github-ci-issuer-trust-readonly.v0"


class Refused(Exception):
    pass


def need(ok, why):
    if not ok:
        raise Refused(why)


# Expected values are from individually read-back, real GitHub GETs. They are
# NOT a signing key, a provider lease or a current authorization oracle.
EXPECTED = {
    "schema": SCHEMA,
    "capture_date": "2026-10-11",
    "observation": "GITHUB_CONNECTOR_REST_READONLY_SNAPSHOT_NOT_SIGNED_AND_NOT_LIVE_ADMISSION",
    "repository": "nocturney/velvetos-core",
    "main_sha_at_capture": MAIN_AT_SNAPSHOT,
    "ruleset": {
        "id": 23284099,
        "name": "VelvetOS main protection",
        "enforcement": "active",
        "target": "branch",
        "include": ["~DEFAULT_BRANCH"],
        "exclude": [],
        "bypass_actors": [],
        "types": ["deletion", "non_fast_forward", "required_status_checks"],
        "required_status_context": "check-all",
        "strict_required_status_checks_policy": False,
        "requires_pull_request_rule": False,
        "covers_scratch_refs": False,
    },
    "case": {
        "pr_number": 698,
        "pr_head_sha": PR_HEAD,
        "pr_base_sha": "cd2385807aa5b981cb048520e969bd3d813e14f5",
        "pr_squash_main_sha": "81beb1c19e89cc36141eff5c3520d20ed33687a7",
        "source_path": SOURCE_REL,
        "source_sha256": SOURCE_SHA,
        "source_blob_sha1": SOURCE_BLOB,
        "source_bytes": 480,
        "source_last_byte": 41,
        "source_terminal_lf": False,
        "visible_tests_passed": 3,
        "hidden_tests_passed": 12,
        "core_run": {
            "id": 38124430291,
            "event": "pull_request",
            "workflow_id": 352155264,
            "path": CORE_FLOW,
            "head_sha": PR_HEAD,
            "status": "completed",
            "conclusion": "success",
            "attempt": 1,
            "workflow_blob_at_protected_base": "02583e57bbc527056c89e8cb2e360ce515cce006",
            "workflow_blob_at_pr_head": "02583e57bbc527056c89e8cb2e360ce515cce006",
        },
        "qa_run": {
            "id": 38124430260,
            "event": "pull_request",
            "workflow_id": 381116266,
            "path": C1_FLOW,
            "head_sha": PR_HEAD,
            "status": "completed",
            "conclusion": "success",
            "attempt": 1,
            "workflow_blob_at_pr_head": "44b5545b24b77925a9eb41d8637e6f9248708b40",
            "workflow_existed_at_protected_base": False,
            "workflow_added_by_subject_pr": True,
        },
    },
    "risk": {
        "protected_main_restriction_not_independent_scratch_fencing": True,
        "existing_main_ruleset_mandates_pr": False,
        "original_source_qa_succeeded": True,
        "qa_workflow_preexisting_trusted_policy_at_pr_base": False,
        "core_workflow_on_base_unchanged": True,
        "head_can_modify_test_scripts_unless_independently_restricted": True,
        "expired_etcd_owner_git_ref_write_accepted_in_prior_live_lab": True,
        "etcd_github_atomic_commit_proven": False,
        "sole_sink_credentials_os_isolated_proven": False,
        "provider_epoch_read_authenticated_for_this_candidate": False,
        "current_authoritative_lease_and_ttl_proven": False,
        "unknown_effect_reconciled": False,
        "worker_or_model_received_git_write_token": False,
        "safe_general_generated_code_auto_promotion": False,
        "existing_scratch_ref_protected_by_main_ruleset": False,
    },
    "policy": {
        "mode": "READ_ONLY_GATE_NOT_AN_ISSUER",
        "request_writes_permitted": False,
        "synthetic_provider_data_never_writer_authority": True,
        "positive_qa_receipt_not_unattended_promotion": True,
        "unknown_effect_never_replayed": True,
        "require_different_verified_credentials_and_provider_atomic_sink_gate": True,
        "model_executed_locally": False,
        "network_or_git_mutations": 0,
        "codex_calls": 0,
        "paid_api_usd": 0,
        "production_effects": False,
    },
}


def exact(raw, expected, prefix):
    """Closed, type-exact recursive schema: reject even unexpected fields."""
    need(type(raw) is type(expected), "UNTRUSTED_TYPE_" + prefix)
    if type(expected) is dict:
        need(set(raw) == set(expected), "UNTRUSTED_FIELDS_" + prefix)
        for key, value in expected.items():
            exact(raw[key], value, prefix + "." + key)
    elif type(expected) is list:
        need(len(raw) == len(expected), "UNTRUSTED_ARRAY_" + prefix)
        for index, (value, original) in enumerate(zip(raw, expected)):
            exact(value, original, prefix + "[" + str(index) + "]")
    else:
        need(raw == expected, "UNTRUSTED_VALUE_" + prefix)


def source_sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def source_bytes_are_original(data: bytes):
    need(type(data) is bytes, "MODEL_SOURCE_MUST_BE_BYTES")
    need(len(data) == 480 and data[-1:] == b")" and not data.endswith(b"\n"),
         "MODEL_SOURCE_SIZE_OR_TERMINAL_LF_CHANGED")
    need(source_sha(data) == SOURCE_SHA and git_blob(data) == SOURCE_BLOB,
         "MODEL_SOURCE_PROVENANCE_SHA_CHANGED")


def historical_evidence(snapshot, data):
    exact(snapshot, EXPECTED, "github_historical")
    source_bytes_are_original(data)
    rules = snapshot["ruleset"]
    case = snapshot["case"]
    need(rules["include"] == ["~DEFAULT_BRANCH"] and
         not rules["covers_scratch_refs"] and
         "pull_request" not in rules["types"],
         "SCRATCH_REF_FENCING_FALSE_CLAIM")
    need(case["core_run"]["path"] == CORE_FLOW and
         case["core_run"]["workflow_blob_at_pr_head"] ==
         case["core_run"]["workflow_blob_at_protected_base"],
         "MUTATED_EXISTING_CORE_WORKFLOW")
    need(case["qa_run"]["path"] == C1_FLOW and
         not case["qa_run"]["workflow_existed_at_protected_base"] and
         case["qa_run"]["workflow_added_by_subject_pr"],
         "SAME_PR_WORKFLOW_IMPERSONATES_PRETRUSTED_APPROVER")
    need(case["core_run"]["head_sha"] ==
         case["qa_run"]["head_sha"] == case["pr_head_sha"],
         "CI_REPLAYED_FOR_DIFFERENT_PR_HEAD")
    need(snapshot["risk"]["expired_etcd_owner_git_ref_write_accepted_in_prior_live_lab"],
         "HISTORICAL_REAL_EXPIRED_WRITER_ACCEPTANCE_ERASED")
    return True


def deny_effect_ticket(proposal):
    """Any untrusted proposal can be reviewed; none can mint write authority.

    Even a valid head, green CI and current Git SHA cannot bind the real etcd
    lease / revocation atomically to a GitHub mutation. No credential-bearing
    OS principal or native sink is attested here. NEVER return 'admitted'.
    """
    need(type(proposal) is dict, "PROPOSAL_NOT_OBJECT")
    need(set(proposal) <= {
        "actor", "epoch", "head_sha", "expected_git_sha",
        "qa_passed", "github_writer_request", "effect_state",
    }, "UNAPPROVED_PROPOSAL_FIELD")
    if proposal.get("effect_state") in ("UNKNOWN", "EFFECT_IN_FLIGHT"):
        return "BLOCKED_UNKNOWN_EFFECT_NO_BLIND_RETRY"
    if proposal.get("qa_passed") is True:
        return "BLOCKED_GREEN_QA_NOT_GIT_SINK_AUTHORIZATION"
    return "BLOCKED_SOLE_CREDENTIAL_SINK_AND_LIVE_FENCE_NOT_PROVEN"


def inspected_report(snapshot, data):
    historical_evidence(snapshot, data)
    # Real C1 QA is preserved as passed. Trust/no-write classification is
    # intentionally separate and NEVER promoted from submitted JSON.
    return {
        "schema": SCHEMA,
        "status": "PASS_HISTORICAL_GITHUB_TRUST_GAP_INVENTORY_WRITE_DENIED",
        "source_qa_pass_observed": True,
        "source_sha256": SOURCE_SHA,
        "github_original_blob_sha1": SOURCE_BLOB,
        "source_bytes": len(data),
        "protected_main_ruleset_checkall_observed": True,
        "scratch_ref_provider_lease_fencing_proven": False,
        "core_workflow_preexisted_on_base": True,
        "core_workflow_policy_scripts_immutable_proven": False,
        "mac_c1_qa_workflow_preexisted_on_base": False,
        "mac_c1_qa_3_visible_12_hidden_observed": True,
        "approved_sole_credential_sink_principal_proven": False,
        "expired_owner_native_github_rejected_universally": False,
        "unknown_effect_safe_auto_replayed": False,
        "provider_cross_store_atomicity_proven": False,
        "model_code_executed": False,
        "any_github_git_write_permitted": False,
        "actual_github_git_writes_by_gate": 0,
        "provider_requests_by_gate": 0,
        "model_calls_by_gate": 0,
        "network_requests_by_gate": 0,
        "credentials_read_by_gate": 0,
        "production_authority": False,
        "next_gate": "ISOLATED_SINK_IDENTITY_PLUS_LIVE_EPOCH_FENCE_AND_UNKNOWN_RECONCILIATION",
    }


def read_original():
    need(SNAPSHOT.is_file() and not SNAPSHOT.is_symlink(),
         "TRUST_EVIDENCE_SNAPSHOT_MISSING")
    path = ROOT / SOURCE_REL
    need(path.is_file() and not path.is_symlink(), "ORIGINAL_C1_SOURCE_MISSING")
    need(path.resolve() == ROOT / SOURCE_REL, "UNEXPECTED_SOURCE_ALIAS")
    try:
        snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError):
        raise Refused("UNPARSABLE_HISTORICAL_GITHUB_SNAPSHOT")
    return snapshot, path.read_bytes()


def selftest():
    original, data = read_original()
    inspected_report(original, data)
    checks = ["historical_C1_source_sha_and_scope_read_only"]
    # Each exact mutation of historic GitHub observations must be denied,
    # never silently reclassified as a new valid trusted issuer.
    scenarios = [
        ("schema", "_spoofed"),
        ("capture_date", "2026-10-12"),
        ("observation", "CRYPTOGRAPHIC_ATTESTATION"),
        ("repository", "foreign/repo"),
        ("main_sha_at_capture", "0" * 40),
    ]
    families = [
        ("ruleset", [
            ("id", 1), ("name", "Fake rule"), ("enforcement", "disabled"),
            ("target", "tag"), ("include", ["~ALL"]), ("exclude", ["main"]),
            ("bypass_actors", [{"actor_id": 1}]),
            ("types", ["required_status_checks"]),
            ("required_status_context", "fake-check"), 
            ("strict_required_status_checks_policy", True),
            ("requires_pull_request_rule", True),
            ("covers_scratch_refs", True),
        ]),
        ("case", [
            ("pr_number", 999), ("pr_head_sha", "a" * 40),
            ("pr_base_sha", "a" * 40),
            ("pr_squash_main_sha", "a" * 40),
            ("source_path", "../../private.key"),
            ("source_sha256", "0" * 64),
            ("source_blob_sha1", "0" * 40),
            ("source_bytes", 481), ("source_last_byte", 10),
            ("source_terminal_lf", True),
            ("visible_tests_passed", 0), ("hidden_tests_passed", 0),
        ]),
        ("case.core_run", [
            ("id", 0), ("event", "workflow_dispatch"),
            ("workflow_id", 99), ("path", "fake.yml"),
            ("head_sha", "b" * 40), ("status", "in_progress"),
            ("conclusion", "failure"), ("attempt", 2),
            ("workflow_blob_at_protected_base", "0" * 40),
            ("workflow_blob_at_pr_head", "0" * 40),
        ]),
        ("case.qa_run", [
            ("id", 0), ("event", "workflow_dispatch"),
            ("workflow_id", 99), ("path", "fake.yml"),
            ("head_sha", "c" * 40), ("status", "queued"),
            ("conclusion", "cancelled"), ("attempt", 2),
            ("workflow_blob_at_pr_head", "0" * 40),
            ("workflow_existed_at_protected_base", True),
            ("workflow_added_by_subject_pr", False),
        ]),
    ]
    for path, cases in families:
        for key, replacement in cases:
            wrong = copy.deepcopy(original)
            target = wrong
            for part in path.split("."):
                target = target[part]
            target[key] = replacement
            try:
                inspected_report(wrong, data)
            except Refused:
                checks.append("deny_mutated_" + path + "." + key)
            else:
                raise Refused("FALSE_ATTESTED_GITHUB_DATA_" + path + "." + key)
    for key, replacement in scenarios:
        wrong = copy.deepcopy(original)
        wrong[key] = replacement
        try:
            inspected_report(wrong, data)
        except Refused:
            checks.append("deny_top_level_provenance_mutation")
        else:
            raise Refused("SPOOFED_TOP_LEVEL_ISSUER_ACCEPTED")
    for family in ("risk", "policy"):
        for key, value in original[family].items():
            wrong = copy.deepcopy(original)
            wrong[family][key] = (not value if type(value) is bool
                                  else 1 if type(value) is int
                                  else "ALLOW_GITHUB_PRODUCTION_WRITE")
            try:
                inspected_report(wrong, data)
            except Refused:
                checks.append("deny_forged_" + family + "." + key)
            else:
                raise Refused("FALSE_PROMOTION_" + family + "." + key)
    for extra in ("approval", "git_sink_authorized", "safe_to_publish"):
        wrong = copy.deepcopy(original)
        wrong[extra] = True
        try:
            inspected_report(wrong, data)
        except Refused:
            checks.append("deny_extra_attestation_field")
        else:
            raise Refused("EXTRA_AUTHORITY_FIELD_ALLOWED")
    for altered in (
        data + b"\n", data[:-1], data[:-6] + b"broken",
        data.replace(b"pending_separator", b"pending_separat0r"),
    ):
        try:
            inspected_report(original, altered)
        except Refused:
            checks.append("deny_source_bytes_tampering")
        else:
            raise Refused("SOURCE_REWRITTEN_AS_IF_ORIGINAL")
    for forged in (
        {"actor": "win", "epoch": 7, "qa_passed": True,
         "expected_git_sha": "f" * 40, "github_writer_request": True},
        {"actor": "mac", "epoch": 8, "qa_passed": True,
         "effect_state": "UNKNOWN"},
        {"actor": "mac", "epoch": 9, "effect_state": "EFFECT_IN_FLIGHT"},
        {"actor": "fake", "epoch": True, "qa_passed": False},
        {"actor": "win", "head_sha": PR_HEAD, "qa_passed": True},
    ):
        response = deny_effect_ticket(forged)
        need(response.startswith("BLOCKED_"),
             "WORKER_CLAIM_GRANTED_REMOTE_GITHUB_WRITE")
        checks.append("worker_requested_writer_rights_denied")
    try:
        deny_effect_ticket({"remote_token": "secret"})
    except Refused:
        checks.append("unknown_token_field_denied")
    else:
        raise Refused("EXTRA_REMOTE_TOKEN_ACCEPTED")
    need(len(checks) >= 70, "TOO_FEW_INDEPENDENT_NEGATIVES")
    return {
        "schema": SCHEMA,
        "status": "PASS_OFFLINE_GITHUB_CI_ISSUER_AND_SINK_TRUST_NEGATIVES",
        "tests": len(checks),
        "historical_positive_source_qa": True,
        "ci_policy_new_in_same_pr_not_pretrusted": True,
        "main_ruleset_does_not_fence_scratch_refs": True,
        "sole_git_writer_credential_proven": False,
        "unknown_effect_auto_replayed": False,
        "github_git_writes": 0,
        "model_source_executed": False,
        "network_calls": 0,
        "provider_calls": 0,
        "production_authority": False,
    }


def main():
    need(len(sys.argv) == 2 and sys.argv[1] in ("selftest", "inspect"),
         "ONLY_SELFTEST_OR_READONLY_INSPECT")
    snapshot, data = read_original()
    result = selftest() if sys.argv[1] == "selftest" else (
        inspected_report(snapshot, data)
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refused, OSError, TypeError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED",
                          "reason": str(exc)[:150],
                          "network_calls": 0, "github_git_writes": 0,
                          "production_authority": False},
                         sort_keys=True))
        raise SystemExit(2)
