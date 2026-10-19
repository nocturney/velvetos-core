#!/usr/bin/env python3
"""Offline fail-closed validator for two REAL native-local Git/SQLite receipts.

Checks exact bytes, pinned source, independent-run IDs, outcomes, mandatory
denials and negative mutations. NOT host cryptographic attestation, live etcd
mTLS, guest UID separation, remote GitHub effect or CP083 security admission.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import sys

import vf_office_v2_604_cp083_candidate_evidence_gate as evidence_gate

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/implementation/office-v2/phase2/p0-604-cp083-native-lostack-two-receipts-2026-10-18.json"
DRIVER = ROOT / "scripts/vf_office_v2_604_cp083_native_lostack_two_receipts.py"
NATIVE = ROOT / "scripts/vf_office_v2_604_native_git_crash_reconcile_offline.py"
CANDIDATE = ROOT / "scripts/vf_office_v2_604_cp083_hardened_candidate.py"
DRIVER_SHA = "0d38f4e45f1d94a64167b72e0f57ca44efa73a758fc72fe368705294de737251"
NATIVE_RECEIPT_SHA = "2bbd81c9c7f59c1b28937286d1c365ca46c0ceb9db96157859f7225e0dd6d632"
NATIVE_LIVE_SHA = "03c2fd244eac2adf4eb7c288de43f1e28d935e9f2d8f4fe772bfb962390b9a2c"
CANDIDATE_PARENT_SHA = "39b0c918f906980f1ba87c49a03cc6cbf10b4d144b157b3221605a14ad3626b6"
CANDIDATE_LIVE_SHA = "83260c77846b34c4f459eaa812f477e51764fa1eee261af1d542a39dd561cd2c"
EXPECTED = {
    "MacMiniOffice.local": "c3dab4f9582f7aa25cdff4ce4e5a85db15e9c9918569011333a7e9e8a71538f0",
    "Mac-Bedroom.local": "5dbc39e1824b910718bc45344bcffad7845db486bfc534664b7a8b4715035947",
}
SCHEMA = "velvetos.office-v2.604.cp083.nativegit-sqlite-two-receipts-seal.v1"
RUN_SCHEMA = "velvetos.office-v2.604.cp083.nativegit-sqlite-two-fresh.v1"
CASE_EXPECT = {
    "process_death_before_git": ("crash_after_prepare", 91, False,
                                 "REAL_PROCESS_TERMINATION_NO_ACK", False),
    "process_death_after_git": ("crash_after_native_git", 92, True,
                                "REAL_PROCESS_TERMINATION_NO_ACK", False),
    "injected_ack_drop_before_git": ("lost_ack_before_git", 0, False,
                                     "EXPLICIT_INJECTED_ACK_BLACKHOLE", False),
    "injected_ack_drop_after_git": ("lost_ack_after_git", 0, True,
                                    "EXPLICIT_INJECTED_ACK_BLACKHOLE", False),
    "synthetic_revocation_after_git": ("provider_revoked_after_git", 0, True,
                                       "SYNTHETIC_PROVIDER_REVOKE", True),
    "normal_local_cas": ("none", 0, True, "NORMAL_LOCAL_ACK", True),
}
CASE_BASE = (
    "expected_exit", "native_ref_truth", "independent_process_readback",
    "sqlite_full_requested",
)
CASE_END = ("blind_retry_denied", "no_second_effect_after_restart")


class Refused(ValueError):
    pass


def need(value, label):
    if value is not True:
        raise Refused(label)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha40(v):
    return type(v) is str and bool(re.fullmatch("[0-9a-f]{40}", v))


def expected_checks():
    checks = set()
    for case in CASE_EXPECT:
        extras = (("commit_only_after_readback", "native_stale_cas_rejected")
                  if case == "normal_local_cas" else
                  ("uncertain_not_success",) +
                  (("real_child_died_no_ack",)
                   if case.startswith("process_death_") else
                   ("injected_ack_blackhole_explicit",)
                   if case.startswith("injected_ack_") else ()) +
                  ("authoritative_reconciliation_classification",
                   "durable_unknown_after_restart"))
        checks.update(case + ":" + field
                      for field in CASE_BASE + extras + CASE_END)
    checks.add("exact_57_case_assertions")
    need(len(checks) == 58, "CHECK_SCHEMA_DRIFT")
    return checks


def validate(evidence, check_local_sources=True):
    need(type(evidence) is dict and evidence.get("schema") == SCHEMA,
         "SCHEMA")
    need(evidence.get("issue") == 604
         and evidence.get("stacked_parent_pr") == 755
         and evidence.get("parent_head_at_run") ==
         "e065552825d64e9151dca0a53d4b3c7a896ab479"
         and evidence.get("recorded_date") == "2026-10-18",
         "PROVENANCE_SCOPE")
    for name, exact in (
        ("driver_source_sha256", DRIVER_SHA),
        ("native_implementation_sha256", NATIVE_RECEIPT_SHA),
        ("hardened_candidate_source_sha256_at_parent", CANDIDATE_PARENT_SHA),
    ):
        need(evidence.get(name) == exact, name + "_DRIFT")
    need(evidence.get("source_used_by_hardened_candidate") ==
         "scripts/vf_office_v2_604_native_git_crash_reconcile_offline.py",
         "CANDIDATE_DEPENDENCY_SCOPE")
    need(evidence.get("run_count") == 2
         and evidence.get("checks_per_run") == 58
         and evidence.get("security_admission") == "RED"
         and evidence.get("production_authority") is False
         and evidence.get("remote_github_writes") == 0
         and evidence.get("scope") ==
         "TWO_DISTINCT_PHYSICAL_MACOS_HOSTS_NATIVE_LOCAL_GIT_SQLITE_NO_ETCD_MTLS_OR_GUEST_UID",
         "COUNTS_OR_AUTHORITY_DRIFT")
    for no_claim in ("guest_uid_gate_proven", "real_etcd_mtls_gate_proven",
                     "joined_cp083_candidate_replayed",
                     "protected_core_issuer_proven",
                     "authenticated_remote_git_effect_proven",
                     "external_security_qa_completed",
                     "host_cryptographic_attestation"):
        need(evidence.get(no_claim) is False, "FALSE_CLAIM_" + no_claim)
    if check_local_sources:
        need(NATIVE_LIVE_SHA != NATIVE_RECEIPT_SHA, "NATIVE_PINS_MERGED")
        for p, digest in ((DRIVER, DRIVER_SHA), (NATIVE, NATIVE_LIVE_SHA),
                          (CANDIDATE, CANDIDATE_LIVE_SHA)):
            need(p.is_file() and sha(p.read_bytes()) == digest,
                 "SOURCE_BYTES_CHANGED:" + p.name)
        need("import vf_office_v2_604_native_git_crash_reconcile_offline as offline"
             in CANDIDATE.read_text(encoding="utf-8"),
             "CP083_NO_LONGER_USES_NATIVE_IMPL")
    receipts = evidence.get("receipts")
    need(type(receipts) is list and len(receipts) == 2, "TWO_RECEIPTS")
    ids = set()
    hosts = set()
    for item in receipts:
        need(type(item) is dict, "RECEIPT_TYPE")
        host = item.get("device")
        need(host in EXPECTED and host not in hosts, "HOST_DISTINCT")
        hosts.add(host)
        raw = item.get("raw_receipt_utf8_lf")
        need(type(raw) is str and raw.endswith("\n")
             and raw.count("\n") == 1, "EXACT_RAW_LF")
        raw_hash = sha(raw.encode("utf-8"))
        need(item.get("raw_receipt_sha256") == EXPECTED[host]
             and raw_hash == EXPECTED[host], "PINNED_RECEIPT_HASH")
        r = json.loads(raw)
        need(type(r) is dict and r.get("schema") == RUN_SCHEMA
             and r.get("status") == "PASS_NATIVE_LOCAL_ONLY"
             and r.get("security_admission") == "RED"
             and r.get("production_authority") is False
             and r.get("github_remote_writes") == 0
             and r.get("synthetic_provider_only") is True
             and r.get("guest_uid_gate_not_executed") is True
             and r.get("etcd_mtls_not_executed") is True
             and r.get("signed_host_attestation") is False
             and r.get("native_local_bare_git_executed") is True
             and r.get("sqlite_durable_journal_executed") is True,
             "RUN_SECURITY_RED")
        need(r.get("declared_device") == host
             and r.get("os_host_observed") == host
             and r.get("os") == "Darwin"
             and r.get("architecture") == "arm64"
             and r.get("driver_source_sha256") == DRIVER_SHA
             and r.get("native_implementation_sha256") == NATIVE_RECEIPT_SHA,
             "RUN_SOURCE_HOST")
        uid = r.get("run_id")
        need(type(uid) is str and bool(re.fullmatch("[0-9a-f]{32}", uid))
             and uid not in ids, "RUN_ID_DISTINCT")
        ids.add(uid)
        checks = r.get("checks")
        need(type(checks) is list and len(checks) == 58
             and r.get("check_count") == 58
             and set(checks) == expected_checks(), "NAMED_CHECKS")
        cases = r.get("observations")
        need(type(cases) is dict and set(cases) == set(CASE_EXPECT),
             "ALL_NATIVE_CASES")
        for case, exp in CASE_EXPECT.items():
            fault, exit_code, wrote, kind, ack = exp
            ob = cases[case]
            need(type(ob) is dict and
                 ob.get("fault") == fault
                 and ob.get("worker_exit_code") == exit_code
                 and ob.get("fault_kind") == kind
                 and ob.get("ack_seen_by_observer") is ack
                 and ob.get("sqlite_journal_mode") == "delete"
                 and ob.get("sqlite_full_requested") is True
                 and ob.get("attempt_rows_after_retry") == 1,
                 "CASE_NATIVE_OUTCOME:" + case)
            seed = ob.get("seed_sha")
            target = ob.get("intent_sha")
            actual = ob.get("head_after_native")
            need(sha40(seed) and sha40(target) and target != seed
                 and actual == (target if wrote else seed),
                 "NATIVE_GIT_READBACK:" + case)
            if case == "normal_local_cas":
                need(ob.get("journal_state_after_new_process") ==
                     "COMMITTED_READBACK"
                     and ob.get("recovery_classification") ==
                     "NO_PENDING_UNKNOWN"
                     and ob.get("frozen_after_new_process") is False
                     and ob.get("native_stale_cas_denied") is True,
                     "NORMAL_NATIVE_CAS")
            else:
                need(ob.get("journal_state_after_new_process") ==
                     "UNKNOWN_EFFECT_RECONCILE"
                     and ob.get("recovery_classification") ==
                     ("REMOTE_ADVANCED_REVIEW_REQUIRED" if wrote else
                      "REMOTE_UNCHANGED_REVIEW_REQUIRED")
                     and ob.get("frozen_after_new_process") is True,
                     "UNKNOWN_MUST_STAY_FROZEN:" + case)
    need(hosts == set(EXPECTED) and len(ids) == 2,
         "HOSTS_OR_RUNS_MISSING")
    return {"status": "PASS_TWO_NATIVE_LOCAL_RECEIPTS_SECURITY_RED",
            "distinct_hosts": len(hosts),
            "real_native_git_sqlite_receipts": len(ids),
            "named_assertions": len(ids) * 58,
            "remote_github_writes": 0,
            "security_admission": "RED"}


def negatives(original):
    mutations = []
    def change(fn):
        x = copy.deepcopy(original)
        fn(x)
        mutations.append(x)
    change(lambda x: x.__setitem__("security_admission", "GREEN"))
    change(lambda x: x.__setitem__("run_count", 3))
    change(lambda x: x.__setitem__("remote_github_writes", 1))
    change(lambda x: x.__setitem__("guest_uid_gate_proven", True))
    change(lambda x: x.__setitem__("joined_cp083_candidate_replayed", True))
    change(lambda x: x.__setitem__("host_cryptographic_attestation", True))
    change(lambda x: x["receipts"].pop())
    change(lambda x: x["receipts"][1].__setitem__(
        "device", "MacMiniOffice.local"))
    change(lambda x: x["receipts"][0].__setitem__(
        "raw_receipt_sha256", "0" * 64))
    change(lambda x: x["receipts"][0].__setitem__(
        "raw_receipt_utf8_lf",
        x["receipts"][0]["raw_receipt_utf8_lf"].replace(
            '"security_admission":"RED"', '"security_admission":"GREEN"')))
    change(lambda x: x.__setitem__("driver_source_sha256", "0" * 64))
    change(lambda x: x.__setitem__("hardened_candidate_source_sha256_at_parent",
                                   "0" * 64))
    denied = 0
    for data in mutations:
        try:
            validate(data)
        except (Refused, ValueError, TypeError, KeyError, json.JSONDecodeError):
            denied += 1
    need(denied == len(mutations) == 12, "MUTATION_ESCAPED")
    return denied


def read_evidence(path: Path) -> dict:
    """Load sealed evidence only when it is one regular file with one name."""
    raw = evidence_gate.read_bounded(Path(path), 1024 * 1024)
    return json.loads(raw.decode("utf-8"))


def main(argv):
    if argv not in ([], ["--selftest"]):
        raise Refused("OFFLINE_VERIFY_ONLY")
    data = read_evidence(EVIDENCE)
    result = validate(data)
    if argv == ["--selftest"]:
        result["mutations_rejected"] = negatives(data)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (Refused, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED",
                          "reason": str(exc)[:160],
                          "security_admission": "RED"}))
        raise SystemExit(2)
