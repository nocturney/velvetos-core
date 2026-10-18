#!/usr/bin/env python3
"""Pure read-only owner Option A decision / CP082 evidence gate.

Checks revocation semantics only. Does NOT authorize GitHub/OS actions, load
model source, spawn etcd, run the native lab, contact networks or mutate data.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs/implementation/office-v2/phase2/p0-604-owner-option-a-revocation-2026-10-16.json"
RECEIPTS = ROOT / "docs/implementation/office-v2/phase2/p0-604-cp082-tls-localgit-unknown-2026-10-16.json"
SCHEMA = "velvetos.office-v2.604.owner-option-a-revocation.v1"
EVIDENCE_SCHEMA = "velvetos.office-v2.604.cp082.sealed-native-integration-receipts.v1"
LAB_SCHEMA = "velvetos.office-v2.604.cp082.authenticated-local-git-unknown-lab.v1"
SOURCE_SHA256 = "fa108cfd9bea1aec38a9e7e4c1a3e369e6ba4be94eef413ea0ec0304bb1a8eee"
SEMANTICS = {
    "revoke_wins_before_admit": "DENY_NEW_ADMISSION",
    "revoke_after_admit": "DRAINING_ADMITTED_KEEP_REF_AND_TASK_RESERVATIONS",
    "already_dispatched_external_git_effect": "MAY_COMPLETE_CANNOT_BE_ATOMICALLY_UNSENT",
    "unknown_effect_or_lost_ack": "DURABLE_UNKNOWN_EFFECT_RECONCILE_AND_FREEZE",
    "recovery": "INDEPENDENT_REMOTE_READBACK_NO_BLIND_RETRY",
    "uncertain_or_conflicting_readback": "REVIEW_REQUIRED_KEEP_FROZEN",
    "new_work_during_drain_or_unknown": "DENY",
    "process_restart": "PRESERVE_JOURNAL_AND_FREEZE",
    "safe_reopening": "ONLY_AFTER_CONFIRMED_OUTCOME_AND_SEPARATE_AUTHORIZED_CLEARANCE",
    "option_b_immediate_cancel_guarantee": "REJECTED_UNPROVABLE_FOR_DISPATCHED_REMOTE_EFFECT",
}
REQUIRED_CP082 = (
    "normal_revoke_transitions_to_drain_not_release",
    "already_granted_drain_refuses_any_new_local_effect",
    "revocation_committed_before_local_effect",
    "revoke_before_native_git_ref_fails_closed",
    "post_local_git_revoke_forces_unknown_not_safe_success",
    "durable_recovery_classifies_remote_advanced_without_retry",
    "unknown_persists_and_blocks_second_request",
    "ack_lost_after_local_git_freezes_durable_journal",
    "ack_after_no_blind_retry",
    "ack_after_new_SQLite_reader_cannot_unfreeze",
    "ack_lost_before_git_freezes_without_effect",
    "ack_before_no_blind_retry",
    "ack_before_new_SQLite_reader_cannot_unfreeze",
)
NO_AUTHORITY = (
    "production_deploy", "production_merge", "production_credentials",
    "protected_remote_github_writes", "generated_source_execution",
    "grant_issuance_or_security_signoff", "cross_store_atomicity_claim",
    "automatic_unknown_retries", "automatic_drain_lock_release",
    "bypass_of_owner_authentication",
)


class PolicyRefusal(ValueError):
    pass


def require(predicate: bool, reason: str) -> None:
    if predicate is not True:
        raise PolicyRefusal("OPTION_A_" + reason)


def load(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink(), "SOURCE_MISSING")
    raw = path.read_bytes()
    require(len(raw) < 100000 and raw.endswith(b"\n"), "RAW_FILE_INVALID")
    value = json.loads(raw)
    require(type(value) is dict, "NONOBJECT_SOURCE")
    return value


def verify(policy: dict, evidence: dict) -> dict:
    require(type(policy) is dict, "POLICY_TYPE")
    require(policy.get("schema") == SCHEMA, "SCHEMA")
    require(policy.get("recorded_date") == "2026-10-16", "OWNER_DECISION_DATE")
    require(policy.get("recorded_source") ==
            "EXPLICIT_PROJECT_OWNER_CONFIRMATION_IN_THIS_CHAT",
            "SOURCE_NOT_RECORDED")
    require(policy.get("approval_basis") ==
            "OWNER_CHOSE_A_AFTER_EXPLANATION_OF_NO_CROSS_STORE_CANCEL_GUARANTEE",
            "ACKNOWLEDGEMENT_SCOPE")
    require(policy.get("owner_decision") == "OPTION_A_APPROVED",
            "OWNER_CHOICE_IS_NOT_A")
    require(policy.get("scope") ==
            "OFFICE_2_0_REVOCATION_SEMANTICS_ONLY",
            "SCOPE_ESCALATED")
    require(policy.get("design_effect") ==
            "ADOPT_OPTION_A_FOR_FUTURE_IMPLEMENTATION_AND_TESTS",
            "DESIGN_EFFECT_ESCALATED")
    require(policy.get("policy") == SEMANTICS, "REVOCATION_SEMANTICS_DRIFT")
    require(policy.get("required_cp082_cases") == list(REQUIRED_CP082),
            "REQUIRED_CP082_CASES_DRIFT")
    require(policy.get("security_admission") == "RED", "SECURITY_PROMOTED")
    require(policy.get("approval_is_not_cryptographic_credential") is True,
            "OWNER_CHAT_NOT_CRYPTO_SIGNOFF")
    require(policy.get("existing_security_gates_remain_required") is True,
            "SECURITY_GATES_BYPASSED")
    excluded = policy.get("explicitly_not_authorized")
    require(type(excluded) is dict and set(excluded) == set(NO_AUTHORITY) and
            all(excluded.get(key) is False for key in NO_AUTHORITY),
            "PRODUCTION_OR_UNSAFE_ACTION_GRANTED")
    reference = policy.get("existing_lab_reference")
    require(reference == {
        "cp082_source_sha256": SOURCE_SHA256,
        "cp082_evidence_schema": EVIDENCE_SCHEMA,
        "real_live_github_proof": False,
        "distinct_temporary_etcd_instances": 2,
        "bounded_synthetic_assertions": 52,
    }, "LOCAL_ONLY_PROOF_REFERENCE_DRIFT")
    require(type(evidence) is dict and evidence.get("schema") == EVIDENCE_SCHEMA,
            "EVIDENCE_SOURCE_TYPE")
    require(evidence.get("security_admission") == "RED" and
            evidence.get("test_script_sha256") == SOURCE_SHA256,
            "CP082_SOURCE_OR_AUTHORITY_DRIFT")
    totals = evidence.get("totals") or {}
    require(totals.get("independent_fresh_provider_runs") == 2 and
            totals.get("real_etcd_mtls_localgit_unknown_assertions_passed") == 52 and
            totals.get("remote_github_writes") == 0 and
            totals.get("production_security_admission_gates_passed") == 0,
            "CP082_TOTALS_OR_REMOTE_EFFECT_DRIFT")
    receipts = evidence.get("raw_receipts")
    require(type(receipts) is list and len(receipts) == 2,
            "ORIGINAL_TWO_PROVIDER_RUNS_MISSING")
    ids = set()
    checked = 0
    for index, entry in enumerate(receipts, start=1):
        raw = entry.get("raw_json_with_final_lf") if type(entry) is dict else None
        require(type(raw) is str and raw.endswith("\n") and
                entry.get("run_index") == index and
                hashlib.sha256(raw.encode("utf8")).hexdigest() == entry.get("raw_sha256"),
                "RAW_CP082_RECEIPT_HASH")
        actual = json.loads(raw)
        scenario = actual.get("scenarios")
        require(actual.get("schema") == LAB_SCHEMA and
                actual.get("security_admission") == "RED" and
                actual.get("remote_github_writes") == 0 and
                actual.get("production_authority") is False and
                actual.get("cross_store_atomicity_proven") is False and
                actual.get("os_separate_sink_proven") is False and
                actual.get("scenario_count") == 26 and
                type(scenario) is list and len(scenario) == 26 and
                all(name in scenario for name in REQUIRED_CP082),
                "CP082_OPTION_A_NEGATIVE_COVERAGE_ABSENT")
        distinct_id = actual.get("disposable_prefix_sha256")
        require(type(distinct_id) is str and len(distinct_id) == 64 and
                distinct_id not in ids, "NONINDEPENDENT_LAB_RUNS")
        ids.add(distinct_id)
        checked += len(scenario)
    require(checked == 52, "CASE_TOTAL_DISAGREEMENT")
    return {
        "schema": SCHEMA, "owner_option": "A", "owner_semantics_approved": True,
        "security_admission": "RED", "production_authority": False,
        "authenticated_remote_github_proven": False,
        "checked_original_provider_runs": len(ids),
        "checked_lab_cases": checked,
        "option_b_guarantee_rejected": True,
    }


def selftest() -> dict:
    policy, evidence = load(POLICY), load(RECEIPTS)
    real = verify(policy, evidence)
    cases = [
        ("OPTION_B", lambda p,e:p.update(owner_decision="OPTION_B_APPROVED")),
        ("PREMATURE_GREEN", lambda p,e:p.update(security_admission="GREEN")),
        ("AUTO_RETRY", lambda p,e:p["policy"].update(recovery="AUTOMATIC_RETRY")),
        ("AUTO_LOCK_RELEASE", lambda p,e:p["explicitly_not_authorized"].update(
            automatic_drain_lock_release=True)),
        ("SOURCE_PERMISSION", lambda p,e:p["explicitly_not_authorized"].update(
            generated_source_execution=True)),
        ("NO_CP082_CASE", lambda p,e:p["required_cp082_cases"].pop()),
        ("CLAIM_REMOTE_GITHUB", lambda p,e:p["existing_lab_reference"].update(
            real_live_github_proof=True)),
    ]
    for name, mutate in cases:
        copy_policy, copy_receipt = copy.deepcopy(policy), copy.deepcopy(evidence)
        mutate(copy_policy, copy_receipt)
        try:
            verify(copy_policy, copy_receipt)
        except PolicyRefusal:
            continue
        raise PolicyRefusal("NEGATIVE_MUTATION_ACCEPTED_" + name)
    return {"selftest_cases": len(cases), **real}


def main(argv: list[str]) -> int:
    require(argv in (["--check"], ["--selftest"]), "EXPLICIT_READONLY_MODE")
    outcome = (selftest() if argv == ["--selftest"] else
               verify(load(POLICY), load(RECEIPTS)))
    print(json.dumps(outcome, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (PolicyRefusal, KeyError, ValueError, OSError) as exc:
        print(json.dumps({
            "status": "FAIL_CLOSED", "reason": str(exc)[:160],
            "security_admission": "RED", "production_authority": False,
        }), file=sys.stderr)
        raise SystemExit(2)
