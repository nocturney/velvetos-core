#!/usr/bin/env python3
"""Offline gated receipt for real #604 two-host etcd 3.6.15 synthetic KV pilot.

The receipt is operator-collected LAB evidence, NOT a signed attestation.
NEVER contacts etcd or any network, runs its agent, starts a server or writes.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
P2 = ROOT / "docs/implementation/office-v2/phase2"
RECEIPT = P2 / "p0-etcd-two-host-real-provider-atomic-kv-2026-10-10.json"
PROBE = ROOT / "scripts/vf_office_v2_604_etcd_provider_pilot.py"
SCHEMA = "velvetos.office-v2.fleet.etcd-two-host-kv-fence-lab.v1"
PROBE_SHA = "139f8e144d8d858ee38febc209ae6ba8f960f7eee178dd85b5ba9ac8ecf31893"
PROVIDER_ARCHIVE_SHA = "c791b3b8e94845e130994f99dc5be7db4f57e6481d15f0a78e9bead7028d1e91"
DB_SHA = "6270dd86521083f7b7130b804d318e98cb87e0374be4f8601d27484ed83bc548"
ARTIFACTS = {
    "race": ("mac", 2, "4b807fa56468ba263cb7e35c8318095d183094b4f3d6b16fd1ec6642927dde02"),
    "expiry": ("mac", 9, "1b402124a276c262f1783b23a81da8bfb24b80895823fe321715c34e71a1e40b"),
    "renew": ("mac", 12, "cbafb47c8d80dee835d5b9978b04e1776922da7da63a970649036e3f42a7de0c"),
    "outage": ("win", 17, "1cbf69a961f03f7f6c65f726cc08a6237e9085ec6b250391197bd111b3f4bb75"),
}
GENERATIONS = [2, 5, 7, 9, 12, 15, 17]
NONCLAIMS = (
    "provider_selected", "production_lease_or_writer_admission",
    "production_safe_authentication", "quorum_failure_tolerance_or_multinode_ha",
    "malicious_direct_client_cannot_bypass_raw_kv_put",
    "atomic_external_git_push_or_artifact_filesystem_fence",
    "agent_authored_pr_or_autonomous_merge",
    "controlled_network_partition_or_clock_skew_test",
    "independent_git_writer_mac_verified",
    "actual_worker_crash_unknown_recovery",
    "queue_scheduler_dispatched_jobs",
    "unverified_host_capacity_counted", "reliable_p95_latency",
    "cost_incurred", "customer_printer_social_or_cad_effects",
    "duplicate_runtime_controller_created",
)


class Refused(Exception):
    pass


def need(ok, message):
    if not ok:
        raise Refused(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(v):
    need(type(v) is dict and v.get("schema") == SCHEMA and
         v.get("date") == "2026-10-10" and
         v.get("status") == "PASS_TWO_PHYSICAL_HOST_ETCD_ATOMIC_KV_ONLY_NOT_EXTERNAL_WRITER",
         "RECEIPT_IDENTITY_REFUSED")
    s = v.get("scope") or {}
    need(s.get("owner_issue") == 604 and s.get("consumer_issue") == 612 and
         s.get("provider_candidate") == "etcd" and
         s.get("candidate_version") == "3.6.15" and
         s.get("provider_selected_for_production") is False and
         s.get("physical_hosts_real") == 2 and
         s.get("mac_host") == "MacMiniOffice.local" and
         s.get("windows_host") == "Chris" and
         s.get("future_hosts_claimed") == 0 and
         s.get("real_model_workers_run") == 0 and
         s.get("git_base") == "3689168e48f85bd1008421d69f7484a800073adf" and
         s.get("only_synthetic_etcd_namespace") ==
             "/velvet-office2/lab604/etcd-revision-20261010" and
         s.get("provider_endpoint_during_lab") == "http://192.168.0.217:32379" and
         s.get("authentication_enabled") is False and
         s.get("tls_enabled") is False and
         s.get("temporary_lan_unauthenticated_hard_nonproduction") is True and
         s.get("api_client_path") ==
             "scripts/vf_office_v2_604_etcd_provider_pilot.py" and
         s.get("api_client_source_sha256") == PROBE_SHA and
         s.get("api_client_source_sha256_same_on_both_hosts") is True and
         s.get("official_release") ==
             "https://github.com/etcd-io/etcd/releases/tag/v3.6.15" and
         s.get("official_mac_arm64_archive_bytes") == 24037957 and
         s.get("official_mac_arm64_archive_sha256") == PROVIDER_ARCHIVE_SHA and
         s.get("native_etcd_binary_sha256") ==
             "dd2596ab902c23252da55e770cb7f7216522ae5599f84d2a20e0e7272d52fe82" and
         s.get("native_etcdctl_binary_sha256") ==
             "05f34d3be92b0ba78dfc5aa9fd5d63224d551a7f8c2eadfbaa7dc2f35ae625ad" and
         s.get("new_scheduler_installed_or_started") is False and
         s.get("production_credentials_copied") is False and
         s.get("existing_fleet_service_changed") is False and
         s.get("paid_model_or_api_calls") == 0,
         "PROVIDER_PROVENANCE_OR_SCOPE_REFUSED")
    need(sha(PROBE) == PROBE_SHA, "PILOT_SCRIPT_CHANGED")
    a = v.get("attempts")
    expected = [
        ("race","mac","GRANTED_REAL_ETCD_LEASE",2),
        ("race","win","DENIED_COMPETING_CLAIM",None),
        ("race","win","GRANTED_AFTER_MAC_REVOKE",5),
        ("expiry","win","GRANTED_BEFORE_TTL_EXPIRY",7),
        ("expiry","mac","GRANTED_AFTER_WIN_TTL_EXPIRY",9),
        ("renew","mac","GRANTED_AND_RENEWED",12),
        ("outage","mac","GRANTED_PRE_STOP",15),
        ("outage","win","GRANTED_AFTER_STOP_RESTART_OLD_LEASE_EXPIRY",17),
    ]
    need(type(a) is list and len(a) == len(expected), "OWNER_ATTEMPT_COUNT_WRONG")
    for row, wanted in zip(a, expected):
        need(type(row) is dict and
             (row.get("scenario"), row.get("host"), row.get("result"),
              row.get("generation")) == wanted,
             "TWO_HOST_CLAIM_OR_REJECTION_DRIFT")
    need(a[1].get("provider_revision") == 2 and
         a[1].get("unused_lease_revoked") is True and
         a[0].get("ttl_s") == a[2].get("ttl_s") == 100 and
         a[3].get("ttl_s") == 6 and
         a[4].get("ttl_s") == 80 and
         a[5].get("initial_ttl_s") == a[5].get("reported_renewed_ttl_s") == 9 and
         a[6].get("ttl_s") == 20 and a[7].get("ttl_s") == 60,
         "LEASE_TTL_OR_RACE_CONTRACT_DRIFT")
    need(v.get("provider_epoch_sequence") == GENERATIONS
         and len(set(GENERATIONS)) == 7
         and GENERATIONS == sorted(GENERATIONS),
         "GENERATION_NOT_MONOTONIC")

    ef = v.get("real_atomic_effect_postconditions") or {}
    final = (v.get("independent_native_etcdctl_final_readback") or {})
    items = final.get("effects") or {}
    need(set(ef) == set(ARTIFACTS) and
         set(items) == set(ARTIFACTS) and
         final.get("result") == "PASS" and
         final.get("provider_global_revision") == 19 and
         final.get("original_lease_keys_remaining") == 0 and
         final.get("synthetic_effect_keys_present") == 4 and
         final.get("windows_independent_cross_host_final_observe_all_four_pass") is True,
         "NATIVE_PROVIDER_EFFECT_OR_FINAL_COUNT_WRONG")
    for name, (host, generation, hashvalue) in ARTIFACTS.items():
        row, native = ef[name], items[name]
        need(row.get("accepted_host") == native.get("host") == host and
             row.get("generation") == native.get("generation") == generation and
             row.get("sha256") == native.get("sha256") == hashvalue,
             "EFFECT_SHAS_GENERATION_OR_HOST_DRIFT")
    need(ef["race"].get("repeat_original_owner_denied") is True and
         ef["race"].get("post_handoff_new_owner_denied_duplicate") is True and
         ef["race"].get("post_handoff_old_owner_denied_stale") is True and
         ef["expiry"].get("old_win_generation") == 7 and
         ef["expiry"].get("old_win_effect_denied") is True and
         ef["expiry"].get("old_win_lease_absent_observed_revision") == 8 and
         ef["renew"].get("provider_keepalive_confirmed") is True and
         ef["renew"].get("effect_after_10_s_observed") is True and
         ef["renew"].get("late_revoke_returned_provider_http_error_not_false_success") is True and
         ef["outage"].get("old_mac_generation") == 15 and
         ef["outage"].get("mac_old_lease_survived_initial_fast_restart") is True and
         ef["outage"].get("old_mac_lease_expired_later_revision") == 16 and
         ef["outage"].get("no_effect_before_reassignment") is True and
         ef["outage"].get("provider_down_mac_effect_exit") == 3 and
         ef["outage"].get("provider_down_win_observe_exit") == 3 and
         ef["outage"].get("provider_down_mac_and_win_result") == "FAIL_CLOSED" and
         ef["outage"].get("old_mac_effect_denied_after_rejoin") is True,
         "REAL_STALE_OWNER_OR_OUTAGE_NEGATIVE_MISSING")

    state = v.get("provider_shutdown_restart") or {}
    need(state.get("original_mac_native_pid") == 67630 and
         state.get("restarted_mac_native_pid") == 68234 and
         state.get("first_pid_verified_birth_and_command") is True and
         state.get("both_exact_pids_absent_after_cleanup") is True and
         state.get("same_on_disk_etcd_data_directory_used") is True and
         state.get("endpoint_health_true_after_restart") is True and
         state.get("provider_down_clients_fail_closed") is True and
         state.get("single_node_only_no_quorum_or_ha_proof") is True,
         "RESTART_OR_OUTAGE_UNVERIFIED")
    done = v.get("final_cleanup_readback") or {}
    need(done.get("server_processes_absent") is True and
         done.get("mac_listening_pilot_ports_count") == 0 and
         done.get("windows_tcp_to_mac_lab_port_connected") is False and
         done.get("software_left_installed_in_global_path") is False and
         done.get("autostart_enabled") is False and
         done.get("local_mac_binary_and_db_retained_for_forensic_replay") is True and
         done.get("local_mac_etcd_db_sha256") == DB_SHA and
         len(done.get("mac_original_state_sha256") or {}) == 4 and
         len(done.get("windows_original_state_sha256") or {}) == 3 and
         all(re.fullmatch("[a-f0-9]{64}", value) for value in
             list(done["mac_original_state_sha256"].values()) +
             list(done["windows_original_state_sha256"].values())) and
         done.get("preexisting_services_preserved") ==
         {"windows_ollama_pid43272":True, "windows_maya_pid24392":True,
          "mac_ollama_pid99094":True},
         "SCOPED_SHUTDOWN_ORIGINAL_RECEIPT_FAIL")
    non = v.get("nonclaims") or {}
    need(set(non) == set(NONCLAIMS) and
         all(non.get(label) is False for label in NONCLAIMS),
         "UNAUTHORIZED_PRODUCTION_OR_FENCE_PROMOTION")
    need((v.get("future_gate") or "").startswith("#604 choose one canonical placement/lease"),
         "CONTRACT_NEXT_GATE_LOST")
    return {
        "status":"PASS_OFFLINE_ETCD_REAL_TWO_HOST_KV_ONLY",
        "real_physical_hosts":2,
        "live_lease_attempts":8,
        "lease_generations":7,
        "atomic_provider_kv_effects":4,
        "live_server_processes_still_running":0,
        "provider_selection":False,
        "external_effect_fence_proven":False,
        "paid_model_calls":0,
        "production_authority":False,
    }


def selftest(obj):
    verify(obj)
    passed=["strict_positive_original"]
    mutants=[
        ("wrong_schema",lambda x:x.update(schema="new")),
        ("fictional_production",lambda x:x.update(status="PRODUCTION_READY")),
        ("wrong_provider",lambda x:x["scope"].update(provider_candidate="Dagu")),
        ("false_selected",lambda x:x["scope"].update(provider_selected_for_production=True)),
        ("fake_tls",lambda x:x["scope"].update(tls_enabled=True)),
        ("fake_auth",lambda x:x["scope"].update(authentication_enabled=True)),
        ("asset_tamper",lambda x:x["scope"].update(official_mac_arm64_archive_sha256="0"*64)),
        ("fake_third_host",lambda x:x["scope"].update(physical_hosts_real=3)),
        ("false_paid",lambda x:x["scope"].update(paid_model_or_api_calls=1)),
        ("actor_not_real",lambda x:x["attempts"][1].update(result="GRANTED")),
        ("lease_not_revoked",lambda x:x["attempts"][1].update(unused_lease_revoked=False)),
        ("repeated_generation",lambda x:x["attempts"][2].update(generation=2)),
        ("generation_order",lambda x:x.update(provider_epoch_sequence=[2,5,7,9,12,15,15])),
        ("duplicate_artifact",lambda x:x["independent_native_etcdctl_final_readback"].update(synthetic_effect_keys_present=5)),
        ("artifact_hash",lambda x:x["real_atomic_effect_postconditions"]["outage"].update(sha256="0"*64)),
        ("lying_native",lambda x:x["independent_native_etcdctl_final_readback"]["effects"]["renew"].update(host="win")),
        ("false_stale",lambda x:x["real_atomic_effect_postconditions"]["expiry"].update(old_win_effect_denied=False)),
        ("false_keepalive",lambda x:x["real_atomic_effect_postconditions"]["renew"].update(provider_keepalive_confirmed=False)),
        ("wrong_restart",lambda x:x["provider_shutdown_restart"].update(same_on_disk_etcd_data_directory_used=False)),
        ("false_fail_closed",lambda x:x["real_atomic_effect_postconditions"]["outage"].update(provider_down_mac_effect_exit=0)),
        ("dirty_end",lambda x:x["final_cleanup_readback"].update(server_processes_absent=False)),
        ("dirty_ports",lambda x:x["final_cleanup_readback"].update(mac_listening_pilot_ports_count=1)),
        ("old_mac_write",lambda x:x["real_atomic_effect_postconditions"]["outage"].update(old_mac_effect_denied_after_rejoin=False)),
        ("production_role",lambda x:x["nonclaims"].update(production_lease_or_writer_admission=True)),
        ("bad_git_claim",lambda x:x["nonclaims"].update(atomic_external_git_push_or_artifact_filesystem_fence=True)),
        ("false_ha",lambda x:x["nonclaims"].update(quorum_failure_tolerance_or_multinode_ha=True)),
        ("bad_clock_test",lambda x:x["nonclaims"].update(controlled_network_partition_or_clock_skew_test=True)),
        ("mac_git_fake",lambda x:x["nonclaims"].update(independent_git_writer_mac_verified=True)),
        ("unsafe_direct_raw_kv",lambda x:x["nonclaims"].update(malicious_direct_client_cannot_bypass_raw_kv_put=True)),
        ("hide_local_lab",lambda x:x["final_cleanup_readback"].update(local_mac_etcd_db_sha256="0"*64)),
    ]
    for name,mutate in mutants:
        value=copy.deepcopy(obj)
        mutate(value)
        try:verify(value)
        except Refused:passed.append(name+"_DENIED")
        else:raise AssertionError("FALSE_ALLOW_"+name)
    need(len(passed)==31,"SELFTEST_CASE_COUNT_WRONG")
    return {"status":"PASS_OFFLINE","cases":len(passed),
            "remote_etcd_requests":0,"server_processes_started_or_stopped":0,
            "model_calls":0,"git_effect_writes":0,"production_authority":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=("verify","selftest"))
    mode=parser.parse_args().mode
    data=json.loads(RECEIPT.read_text(encoding="utf-8"))
    result=verify(data) if mode=="verify" else selftest(data)
    print(json.dumps(result,sort_keys=True))


if __name__ == "__main__":
    try:main()
    except (Refused, AssertionError, ValueError, KeyError,
            TypeError, FileNotFoundError, OSError) as err:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(err)[:180],
                          "remote_etcd_requests":0,"git_effect_writes":0},sort_keys=True))
        sys.exit(2)
