#!/usr/bin/env python3
"""Pure offline CP083 evidence verifier; provider and privileged test never started.

Only validates two original raw real-provider receipts pinned to reviewed
source bytes, strict security RED, negative outcomes, and an inert --selftest.
Never treat this as production, GitHub, Core issuer, or model-code admission.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "vf_office_v2_604_cp083_osuid_tls_localgit_lab.py"
P81 = ROOT / "scripts" / "vf_office_v2_604_cp081_mtls_atomic_admission_lab.py"
P82 = ROOT / "scripts" / "vf_office_v2_604_cp082_tls_native_git_reconcile_lab.py"
EVIDENCE = ROOT / "docs" / "implementation" / "office-v2" / "phase2" / "p0-604-cp083-osuid-tls-localgit-2026-10-17.json"
SCHEMA = "velvetos.office-v2.604.cp083.sealed-osuid-mtls-nativegit.v1"
RUN_SCHEMA = "velvetos.office-v2.604.cp083.osuid-mtls-localgit-option-a.v1"
EXPECTED_SOURCE_SHA = "ff7a648d99b2a4bdda057c0758017b90727c7ee637f660351b9bccaf2f42afe6"
EXPECTED_EVIDENCE_SHA = "cc6a576a57b76c6578c54af36c6d3306976cf92ea5814c3f28de7787285f69b0"
REQUIRED = {
    "worker_cannot_read_sink_key_git_or_journal",
    "attacker_cannot_spoof_worker_uid",
    "worker_cannot_change_task_scope",
    "normal_private_sink_committed_native_local_git",
    "normal_revoke_keeps_reservation",
    "normal_after_drain_blocks_new_request",
    "revoke-first_revoke_committed_before_admit",
    "revoke-first_atomic_admission_denied",
    "revoke-first_worker_refused_stale_provider",
    "revoke-first_never_written_git_ref",
    "drain-before_revoke_moves_to_draining",
    "drain-before_ref_reservation_stays",
    "drain-before_worker_refused_stale_provider",
    "drain-before_never_written_git_ref",
    "mid_native_local_git_wrote_before_revoke",
    "mid_real_etcd_revoke_after_native_git",
    "mid_post_native_revoke_is_unknown_not_success",
    "mid_durable_unknown_frozen",
    "mid_no_blind_retry",
    "mid_restart_does_not_unlock",
    "ack-before_worker_sees_actual_lost_ack",
    "ack-before_durable_unknown_frozen",
    "ack-before_no_blind_retry",
    "ack-before_freeze_keeps_git_effect_truth",
    "ack-before_restart_does_not_unlock",
    "ack-after_worker_sees_actual_lost_ack",
    "ack-after_durable_unknown_frozen",
    "ack-after_no_blind_retry",
    "ack-after_freeze_keeps_git_effect_truth",
    "ack-after_restart_does_not_unlock",
    "crash_after_real_git_killed_sink_before_ack",
    "crash-after_durable_unknown_frozen",
    "crash-after_no_blind_retry",
    "crash-after_freeze_keeps_git_effect_truth",
    "crash-after_restart_does_not_unlock",
}
TRUE_FLAGS = (
    "distinct_kernel_os_uids", "root_test_fixture_controller",
    "real_mtls_rbac_provider", "real_atomic_etcd_admission",
    "native_local_bare_git_effect", "sink_only_tls_key_and_sqlite_git_dac",
    "durable_unknown_freeze",
)
FALSE_FLAGS = (
    "real_protected_core_issuer", "remote_github_sink_proven",
    "claim_signature_validated", "two_host_autonomous_coding_proven",
    "cross_store_atomicity_proven", "production_authority",
)
FALSE_EVIDENCE = (
    "production_authority", "real_protected_core_issuer_proven",
    "authenticated_remote_github_sink_proven",
    "claim_crypto_signature_proven",
    "two_physical_host_autonomous_model_coding_proven",
    "independent_security_review_completed",
)


class Rejected(ValueError):
    pass


def require(condition, label):
    if condition is not True:
        raise Rejected(label)


def hexsha(v):
    return isinstance(v, str) and bool(re.fullmatch("[0-9a-f]{64}", v))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def validate(payload):
    require(type(payload) is dict and payload.get("schema") == SCHEMA,
            "SCHEMA_REFUSED")
    require(payload.get("recorded_date") == "2026-10-17",
            "DATE_DRIFT")
    require(payload.get("security_admission") == "RED"
            and payload.get("remote_github_writes") == 0
            and payload.get("real_provider_runs") == 2
            and payload.get("checks_each") == 59,
            "RED_COUNT_OR_AUTHORITY_DRIFT")
    require(all(payload.get(k) is False for k in FALSE_EVIDENCE),
            "UNPROVEN_SECURITY_CLAIM_PROMOTED")
    require(payload.get("source_sha256") == EXPECTED_SOURCE_SHA,
            "PUBLISHED_SOURCE_DIGEST_CHANGED")
    for key, script in (
        ("source_sha256", SOURCE),
        ("cp081_source_sha256", P81),
        ("cp082_source_sha256", P82),
    ):
        require(hexsha(payload.get(key)) and
                sha(script.read_bytes()) == payload[key],
                "DEPENDENCY_SOURCE_BYTES_DRIFT_" + key)
    receipts = payload.get("raw_receipts")
    require(type(receipts) is list and len(receipts) == 2,
            "ORIGINAL_RECEIPT_COUNT_WRONG")
    observed_fixtures = set()
    observed_names = None
    for index, entry in enumerate(receipts, 1):
        require(type(entry) is dict and entry.get("run") == index,
                "RECEIPT_INDEX_WRONG")
        raw = entry.get("raw_receipt_utf8_lf")
        require(isinstance(raw, str) and raw.endswith("\n") and
                raw.count("\n") == 1 and
                entry.get("raw_receipt_sha256") == sha(raw.encode("utf-8")),
                "RAW_ORIGINAL_RECEIPT_SHA_MISMATCH")
        try:
            r = json.loads(raw)
        except (ValueError, TypeError):
            raise Rejected("ORIGINAL_RECEIPT_NOT_JSON")
        require(r.get("schema") == RUN_SCHEMA and
                r.get("status") == "PASS_CP083_TEST_ONLY" and
                r.get("security_admission") == "RED" and
                r.get("real_external_github_writes") == 0 and
                r.get("check_count") == 59,
                "ORIGINAL_RECEIPT_STATUS_OR_TOTAL_DRIFT")
        require(all(r.get(k) is True for k in TRUE_FLAGS) and
                all(r.get(k) is False for k in FALSE_FLAGS),
                "REAL_UID_OR_SECURITY_BOUNDARY_DRIFT")
        labels = r.get("checks")
        require(type(labels) is list and len(labels) == 59 and
                len(set(labels)) == 59 and REQUIRED.issubset(set(labels)),
                "MISSING_NAMED_NEGATIVE_CASES")
        require(observed_names is None or observed_names == set(labels),
                "INDEPENDENT_RUN_CASE_SET_DRIFT")
        observed_names = set(labels)
        fp = r.get("fixture_prefix_sha256")
        require(hexsha(fp) and fp not in observed_fixtures,
                "PROVIDERS_NOT_DISTINCT")
        observed_fixtures.add(fp)
    return {
        "schema": SCHEMA,
        "status": "CP083_SEALED_TEST_ONLY",
        "checked_real_provider_runs": 2,
        "checked_named_assertions": 118,
        "separate_kernel_uid_proof_in_receipts": True,
        "security_admission": "RED",
        "authenticated_remote_github_proven": False,
        "production_authority": False,
    }


def test_mutations(data):
    scenarios = []
    def reject(name, mutation):
        obj = copy.deepcopy(data)
        mutation(obj)
        try:
            validate(obj)
        except Rejected:
            scenarios.append(name)
        else:
            raise Rejected("NEGATIVE_MUTATION_ACCEPTED_" + name)
    reject("red_to_green", lambda d:d.__setitem__("security_admission","GREEN"))
    reject("production_promoted", lambda d:d.__setitem__("production_authority",True))
    reject("github_credential_claim",lambda d:d.__setitem__(
        "authenticated_remote_github_sink_proven",True))
    reject("source_digest_drift", lambda d:d.__setitem__("source_sha256","0"*64))
    reject("tamper_raw_receipt", lambda d:d["raw_receipts"][0].__setitem__(
        "raw_receipt_utf8_lf",d["raw_receipts"][0]["raw_receipt_utf8_lf"].replace(
            "PASS_CP083_TEST_ONLY","PASS_PRODUCTION",1)))
    reject("same_provider_reused", lambda d:d["raw_receipts"].__setitem__(
        1,dict(d["raw_receipts"][0],run=2)))
    reject("original_sha_forged", lambda d:d["raw_receipts"][1].__setitem__(
        "raw_receipt_sha256","0"*64))
    reject("missing_second_receipt",lambda d:d.__setitem__(
        "raw_receipts",d["raw_receipts"][:1]))
    return len(scenarios)


def main(argv):
    require(argv in (["--check"], ["--selftest"]), "MODE_NOT_ALLOWED")
    require(sha(SOURCE.read_bytes()) == EXPECTED_SOURCE_SHA,
            "EXACT_SOURCE_HASH_CHANGED")
    require(sha(EVIDENCE.read_bytes()) == EXPECTED_EVIDENCE_SHA,
            "SEALED_EVIDENCE_HASH_CHANGED")
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    result = validate(evidence)
    static = subprocess.run(
        [sys.executable, "-B", str(SOURCE), "--selftest"],
        cwd=ROOT, capture_output=True, text=True, timeout=8)
    require(static.returncode == 0, "CP083_INERT_SELFTEST_FAILED")
    obj = json.loads(static.stdout)
    require(obj.get("status") == "OFFLINE_STATIC_ONLY" and
            obj.get("provider_started") is False and
            obj.get("remote_github_writes") == 0 and
            obj.get("security_admission") == "RED" and
            obj.get("production_authority") is False,
            "CP083_SELFTEST_ESCALATED_AUTHORITY")
    if argv == ["--selftest"]:
        result["negative_mutations_rejected"] = test_mutations(evidence)
        require(result["negative_mutations_rejected"] == 8,
                "NEGATIVE_MUTATION_COVERAGE_DRIFT")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (Rejected, OSError, ValueError, RuntimeError,
            subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "FAIL_CLOSED",
            "reason": str(exc)[:100], "security_admission": "RED",
            "production_authority": False}))
        raise SystemExit(2)
