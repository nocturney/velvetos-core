#!/usr/bin/env python3
"""Offline receipt/authority regression for real #604 two-host mTLS filesystem LAB.

Consumes a sanitized historical record; NO live provider TLS connections,
NO server startup, no key access, no artifact writes, no Git or model.
Proof record is a pinned operator witness, not a signed attestation.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent.parent
P2=ROOT/"docs/implementation/office-v2/phase2"
RECEIPT=P2/"p0-authenticated-two-host-external-fs-receiver-lab-2026-10-10.json"
RECEIVER=ROOT/"scripts/vf_office_v2_604_authenticated_artifact_receiver_lab.py"
CLIENT=ROOT/"scripts/vf_office_v2_604_authenticated_artifact_client_lab.py"
SCHEMA="velvetos.office-v2.604.authenticated-mtls-external-filesystem-lab.v1"
FINAL_RECEIVER_SHA="b8eee6b5491536ec8031a47297ea8c095119ceb9329daa075cae483bfe6bc9e0"
FINAL_CLIENT_SHA="99348d20e3f5da08ea098b87fd23d5ba31473d1b831f8903814995d8144e3d55"
EXPECTED={
 "handoff":("vf604-mac",7,"e69b4ef188a37138495f0ec6cc678940519484e42285937559681b764fffa689"),
 "expiry":("vf604-mac",17,"40f141c5710da60e4a2ecd5661d38603c80782e6cd311589c8515408ce89ef2c"),
 "outage":("vf604-mac",23,"b881f23a493166c45c00b670bda9f0be7e6cea4c324499b270443d9bd410989d"),
 "duplicate":("vf604-win",28,"9b349fbd2b1b40fd9ef732461815ba4621ed3a49e698b00e7462c0887f30ca94"),
}
FORBIDDEN_CLAIMS=(
 "provider_selected_for_production",
 "external_mac_filesystem_and_etcd_2pc_atomic_proven",
 "blind_safe_external_effect_retry_proven",
 "mac_external_file_os_permissions_production_hardened",
 "anonymous_or_malicious_same_os_user_bypass_blocked",
 "multi_node_quorum_high_availability_proven",
 "controlled_network_partition_and_clock_skew_proven",
 "production_tls_certificate_rotation_or_revocation_proven",
 "github_git_ref_or_pr_effect_fenced",
 "mac_native_github_writer_credential_verified",
 "agent_authored_protected_pr_or_autonomous_merge_proven",
 "unknown_outcome_reconciled",
 "customer_social_cad_printer_business_production_effects",
 "second_fleet_scheduler_installed",
 "model_call_paid_api_or_codex_used",
)

class Denied(Exception):
    pass

def need(ok, reason):
    if not ok:
        raise Denied(reason)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(x):
    need(type(x) is dict and x.get("schema")==SCHEMA
         and x.get("date")=="2026-10-10"
         and x.get("status")==
         "PASS_TWO_PHYSICAL_HOSTS_REAL_MAC_FILESYSTEM_AUTHENTICATED_GATE_WITH_UNKNOWN_FAIL_CLOSED",
         "INVALID_RECEIPT_IDENTITY")
    s=x.get("scope") or {}
    need(x.get("issues")=={"owner":604,"consumer":612}
         and s.get("git_base")=="aff483709c98f7e38a0d8597edf9c0fc56533889"
         and s.get("isolated_lab_slug")=="p0-fence604-mtls-fs-receiver-gpt6-20261010"
         and s.get("hosts")==["MacMiniOffice.local","Chris Windows"]
         and s.get("real_physical_hosts")==2
         and s.get("provider")=="etcd 3.6.15 OFFICIAL_PINNED_BINARY"
         and s.get("provider_is_only_lease_clock_and_generation_authority") is True
         and s.get("provider_binary_sha256")=="dd2596ab902c23252da55e770cb7f7216522ae5599f84d2a20e0e7272d52fe82"
         and s.get("etcdctl_binary_sha256")=="05f34d3be92b0ba78dfc5aa9fd5d63224d551a7f8c2eadfbaa7dc2f35ae625ad"
         and s.get("client_to_provider")=="native_etcdctl_mtls_grpc_using_provider_issued_revision"
         and s.get("worker_to_effect_receiver")=="python_stdlib_https_mutual_tls_client_cert_required"
         and s.get("provider_endpoint")=="https://192.168.0.217:32579"
         and s.get("receiver_endpoint")=="https://192.168.0.217:32581"
         and s.get("private_lan_temporary_only") is True
         and s.get("ephemeral_lab_ca_not_global_trust") is True
         and s.get("etcd_auth_enabled_and_verified") is True
         and s.get("provider_auth_revision")==13
         and s.get("restricted_worker_role")=="vf604-worker-read"
         and s.get("receiver_write_role")=="vf604-receiver-write"
         and s.get("worker_direct_effect_key_write_authorized") is False
         and s.get("receiver_direct_write_outside_exact_prefix_authorized") is False
         and s.get("receiver_file_root")=="runtime/artifacts - Mac, lab-only"
         and s.get("external_effect_mode")==
         "POSIX_O_EXCL_temp_then_atomic_hardlink_no_overwrite_and_fsync"
         and s.get("cross_store_global_atomic_commit_proven") is False
         and s.get("new_scheduler_or_production_authority") is False
         and s.get("model_invocations")==0 and s.get("codex_cli_calls")==0
         and s.get("paid_api_or_model_calls")==0
         and s.get("business_social_cad_printer_effects")==0,
         "SOURCE_OF_AUTHORITY_OR_SCOPE_DRIFT")
    c=x.get("code") or {}
    need(c.get("receiver")=="scripts/vf_office_v2_604_authenticated_artifact_receiver_lab.py"
         and c.get("receiver_final_sha256")==FINAL_RECEIVER_SHA
         and c.get("receiver_earlier_lab_sha256")==
         "0a0971084e4d5e9fbfb2179fdb2c54eaa079948884e74f7e84d3120de9c185aa"
         and c.get("client")=="scripts/vf_office_v2_604_authenticated_artifact_client_lab.py"
         and c.get("client_final_sha256")==FINAL_CLIENT_SHA
         and c.get("win_source_sha_equal_mac_source") is True
         and c.get("receiver_selftest_final_cases")==25
         and c.get("client_selftest_cases")==14
         and c.get("live_modes_ci_prohibited") is True
         and c.get("evidence_not_signed_and_raw_tool_logs_not_committed") is True,
         "CODE_OR_OWNERSHIP_SCOPE_CHANGED")
    need(sha(RECEIVER)==FINAL_RECEIVER_SHA and sha(CLIENT)==FINAL_CLIENT_SHA,
         "BYTE_PINNED_SOURCE_CHANGED")
    auth=x.get("auth") or {}
    certs=auth.get("public_cert_sha256") or {}
    need(auth.get("test_ca_public_sha256")==
         "74f334f452a7bbbaa602d592b71b2517fbaa1ae4d4b14e614d1ca6441d870618"
         and set(certs)=={"server","root","receiver","win","mac"}
         and certs.get("win")==
         "1de1becb14a82d62758e8fad51bd4359e5db6a7d42f6b3f63ec8c265842975c5"
         and certs.get("mac")==
         "8755dcec5ed6131efd18bc5e7b251d623ff87c94e98d45604ed153a4958c3df0"
         and all(re.fullmatch(r"[0-9a-f]{64}",v) for v in certs.values())
         and auth.get("etcd_native_mac_worker_direct_raw_put_exit")==1
         and auth.get("etcd_native_mac_worker_raw_put_denial")==
         "etcdserver: permission denied"
         and auth.get("etcd_native_receiver_outside_prefix_put_exit")==1
         and auth.get("etcd_native_receiver_outside_prefix_denial")==
         "etcdserver: permission denied"
         and auth.get("win_unauthenticated_tls_no_client_cert_result")==
         "URLError_DENIED"
         and auth.get("mac_mtls_worker_read_success") is True
         and auth.get("win_mtls_worker_real_remote_read_success") is True
         and auth.get("root_ca_and_mac_keys_ephemeral_lab_only") is True
         and auth.get("win_private_test_cert_copied_only_into_isolated_lab") is True
         and auth.get("global_machine_trust_stores_changed") is False,
         "TLS_CLIENT_RBAC_OR_DIRECT_BYPASS_NEGATIVE_CHANGED")
    v=x.get("live_scenarios") or {}
    need(set(v)=={"handoff","expiry","unknown","provider_outage",
                  "win_external_effect_hardened_receiver"}, "EXPERIMENT_SCOPE_CHANGED")
    handoff=v["handoff"]
    need(handoff.get("win_original_generation")==5
         and handoff.get("mac_new_generation")==7
         and handoff.get("mac_competing_claim_during_win_ownership_denied") is True
         and handoff.get("win_explicit_revoke_confirmed") is True
         and handoff.get("stale_win_effect_http_status")==409
         and handoff.get("stale_win_effect_denial")=="DENIED_STALE_OWNER_OR_EXPIRED"
         and handoff.get("repeat_mac_effect_denied_no_second_file") is True,
         "PHYSICAL_CROSS_HOST_TRANSFER_NEGATIVE_MISSING")
    expiry=v["expiry"]
    need(expiry.get("win_original_generation")==15
         and expiry.get("win_ttl_seconds")==6
         and expiry.get("original_owner_absent_provider_revision")==16
         and expiry.get("mac_new_generation")==17
         and expiry.get("win_stale_effect_exit")==3
         and expiry.get("win_stale_effect_denial")=="DENIED_STALE_OWNER_OR_EXPIRED",
         "PROVIDER_TTL_FENCING_NOT_PROVEN")
    unknown=v["unknown"]
    need(unknown.get("win_original_generation")==10
         and unknown.get("first_attempt_result")==
         "UNKNOWN_OUTCOME_INTENT_COMMITTED_NO_EXTERNAL_WRITE"
         and unknown.get("original_provider_intent_state")=="PENDING_EXTERNAL_WRITE"
         and unknown.get("external_file_created") is False
         and unknown.get("old_win_repeat_exit")==4
         and unknown.get("mac_before_hardening_was_issued_new_lease_generation")==13
         and unknown.get("mac_before_hardening_effect_denied_no_blind_retry") is True
         and unknown.get("hardening_added_to_grant")=="guard_reassignment_on_intent"
         and unknown.get("final_hardened_mac_owner_regrant_exit")==3
         and unknown.get("final_hardened_windows_owner_regrant_exit")==3
         and unknown.get("final_hardened_deny_reason")==
         "DENIED_UNKNOWN_OUTCOME_RECONCILIATION_REQUIRED"
         and unknown.get("final_provider_intent_still_pending") is True
         and unknown.get("final_file_absent") is True
         and unknown.get("safe_reconciliation_not_automated") is True,
         "UNSAFE_UNKNOWN_RETRY_OR_HISTORY_REWRITTEN")
    outage=v["provider_outage"]
    need(outage.get("win_original_generation")==21
         and outage.get("original_ttl_seconds")==22
         and outage.get("original_etcd_pid")==71082
         and outage.get("original_etcd_stopped_verified") is True
         and outage.get("effect_receiver_stayed_running_on_mac_pid")==71849
         and outage.get("win_effect_during_provider_down_exit")==3
         and outage.get("win_observe_during_provider_down_exit")==3
         and outage.get("provider_down_denial")=="PROVIDER_UNAVAILABLE_OR_DENIED"
         and outage.get("no_external_file_before_restart") is True
         and outage.get("same_database_restart_etcd_pid")==72577
         and outage.get("tls_auth_rbac_revision_still_13_after_restart") is True
         and outage.get("original_owner_survived_fast_restart_temporarily") is True
         and outage.get("old_win_lease_expired_provider_revision")==22
         and outage.get("mac_reassignment_generation")==23
         and outage.get("old_win_stale_effect_post_restart_exit")==3
         and outage.get("mac_new_external_file_accepted") is True,
         "PROVIDER_FAILURE_STALE_EFFECT_FAIL_CLOSED_MISSING")
    win=v["win_external_effect_hardened_receiver"]
    need(win.get("win_lease_generation")==28
         and win.get("win_initiated_and_receiver_wrote_real_mac_file") is True
         and win.get("win_repeat_denied") is True
         and win.get("mac_independent_filesystem_sha_readback") is True
         and win.get("mac_new_owner_after_existing_file_claim_denied") is True
         and win.get("etcd_provider_committed_readback_match") is True,
         "NEW_HARDENED_RECEIVER_REAL_WINDOWS_WRITER_NOT_PROVEN")
    final=x.get("independent_final_readback") or {}
    items=final.get("actual_files") or {}
    need(set(items)==set(EXPECTED)
         and final.get("native_mac_etcdctl_and_real_fs_inspected") is True
         and final.get("windows_mtls_independent_four_scenarios_readback") is True
         and final.get("authoritative_final_global_provider_revision")==31
         and final.get("actual_mac_external_files_count")==4
         and final.get("pending_unknown_without_file_count")==1
         and final.get("live_provider_lease_keys_count")==0
         and final.get("unexpected_files_count")==0
         and final.get("local_sanitized_immutable_readback_sha256")==
         "5b71562ea2b60c0f3f7dfda1e002d2ef44c12f6e674f8da8c86512b32357509e",
         "INDEPENDENT_READBACK_MISSING_OR_DRIFTED")
    for name,(host,generation,digest) in EXPECTED.items():
        need(items[name]=={"host":host,"generation":generation,"sha256":digest}
             and v["win_external_effect_hardened_receiver"].get("file_exact_sha256")==digest
             if name=="duplicate" else
             (items[name]=={"host":host,"generation":generation,"sha256":digest}),
             "EXTERNAL_FILE_HASH_OR_GENERATION_MISMATCH")
        section={"handoff":"handoff","expiry":"expiry",
                 "outage":"provider_outage",
                 "duplicate":"win_external_effect_hardened_receiver"}[name]
        key={"handoff":"accepted_file_sha256","expiry":"accepted_file_sha256",
             "outage":"accepted_external_file_sha256",
             "duplicate":"file_exact_sha256"}[name]
        need(v[section].get(key)==digest,"PER_SCENARIO_RECEIPT_DIGEST_DRIFT")
        if name in ("handoff","expiry","outage"):
            need(v[section].get("file_and_provider_committed_readback_match") is True,
                 "CANONICAL_FILE_RECEIPT_NOT_CROSS_CHECKED")
    clean=x.get("cleanup") or {}
    need(all(clean.get(k) is True for k in (
        "initial_receiver_pid_71849_stopped","hardened_receiver_pid_73060_stopped",
        "initial_etcd_pid_71082_stopped","restarted_etcd_pid_72577_stopped",
        "windows_ephemeral_ca_and_worker_cert_key_deleted",
        "mac_ephemeral_public_certificates_preserved",
        "no_autostart_or_service_installed",
        "windows_ollama_original_pid43272_preserved",
        "windows_mayapy_original_pid24392_preserved"))
         and clean.get("mac_ephemeral_private_keys_deleted_count")==6
         and clean.get("final_mac_lab_listening_ports_count")==0
         and clean.get("final_windows_tcp_to_provider_connected") is False
         and clean.get("final_windows_tcp_to_receiver_connected") is False
         and clean.get("stopped_provider_db_persisted_sha256")==
         "5385d31493f9de012286c9208e2ab0358825f1d1dbc04940cfe04dbca511f9c6"
         and clean.get("production_cert_or_trust_stores_changed") is False,
         "EXACT_TEMPORARY_DAEMON_OR_CREDENTIAL_CLEANUP_NOT_VERIFIED")
    bad=x.get("hard_limits_and_nonclaims") or {}
    need(set(bad)==set(FORBIDDEN_CLAIMS)
         and all(bad.get(k) is False for k in FORBIDDEN_CLAIMS),
         "FORBIDDEN_PRODUCTION_OR_ATOMICITY_PROMOTION")
    need(x.get("next_required_gate","").startswith("#604 compare ready-made provider"),
         "OWNER_NEXT_GATE_LOST")
    return {"status":"PASS_OFFLINE_AUTHENTICATED_TWO_HOST_EXTERNAL_FS_LAB",
            "physical_hosts":2, "real_external_files":4,
            "windows_initiated_files":1,"pending_unknown_unresolved":1,
            "active_leases_final":0,"provider_revision":31,
            "tls_rbac_denial_verified":True,
            "cross_store_atomicity_proven":False,
            "production_authority":False,"server_actions":0}


def selftest(obj):
    verify(obj)
    cases=1
    mutations=[
        ("fake_scope",lambda x:x.update(status="PRODUCTION_READY")),
        ("other_provider",lambda x:x["scope"].update(provider="redis")),
        ("fake_third_host",lambda x:x["scope"].update(real_physical_hosts=3)),
        ("fake_model",lambda x:x["scope"].update(model_invocations=1)),
        ("fake_external_atomicity",lambda x:x["scope"].update(cross_store_global_atomic_commit_proven=True)),
        ("fake_provider_clock",lambda x:x["scope"].update(provider_is_only_lease_clock_and_generation_authority=False)),
        ("fake_rbac",lambda x:x["scope"].update(etcd_auth_enabled_and_verified=False)),
        ("role_bypass",lambda x:x["scope"].update(worker_direct_effect_key_write_authorized=True)),
        ("receiver_bypass",lambda x:x["scope"].update(receiver_direct_write_outside_exact_prefix_authorized=True)),
        ("tls_gap",lambda x:x["auth"].update(win_unauthenticated_tls_no_client_cert_result="ACCEPTED")),
        ("worker_direct_put",lambda x:x["auth"].update(etcd_native_mac_worker_direct_raw_put_exit=0)),
        ("bad_mac_public_cert",lambda x:x["auth"]["public_cert_sha256"].update(mac="0"*64)),
        ("source_change",lambda x:x["code"].update(client_final_sha256="0"*64)),
        ("early_reassign_hidden",lambda x:x["live_scenarios"]["unknown"].update(mac_before_hardening_was_issued_new_lease_generation=None)),
        ("unknown_retry",lambda x:x["live_scenarios"]["unknown"].update(final_hardened_windows_owner_regrant_exit=0)),
        ("unknown_file_forged",lambda x:x["live_scenarios"]["unknown"].update(final_file_absent=False)),
        ("unknown_grant_allowed",lambda x:x["live_scenarios"]["unknown"].update(final_hardened_deny_reason="GRANTED")),
        ("win_stale_ok",lambda x:x["live_scenarios"]["handoff"].update(stale_win_effect_http_status=200)),
        ("ttl_not_real",lambda x:x["live_scenarios"]["expiry"].update(win_ttl_seconds=500)),
        ("provider_down_not_closed",lambda x:x["live_scenarios"]["provider_outage"].update(win_effect_during_provider_down_exit=0)),
        ("fake_mac_fs_readback",lambda x:x["live_scenarios"]["win_external_effect_hardened_receiver"].update(mac_independent_filesystem_sha_readback=False)),
        ("no_actual_win",lambda x:x["live_scenarios"]["win_external_effect_hardened_receiver"].update(win_initiated_and_receiver_wrote_real_mac_file=False)),
        ("tamper_external_hash",lambda x:x["independent_final_readback"]["actual_files"]["duplicate"].update(sha256="0"*64)),
        ("false_no_active_lease",lambda x:x["independent_final_readback"].update(live_provider_lease_keys_count=1)),
        ("pretend_no_unknown",lambda x:x["independent_final_readback"].update(pending_unknown_without_file_count=0)),
        ("wrong_provider_revision",lambda x:x["independent_final_readback"].update(authoritative_final_global_provider_revision=29)),
        ("left_live_service",lambda x:x["cleanup"].update(final_mac_lab_listening_ports_count=1)),
        ("left_windows_test_creds",lambda x:x["cleanup"].update(windows_ephemeral_ca_and_worker_cert_key_deleted=False)),
        ("left_mac_private_key",lambda x:x["cleanup"].update(mac_ephemeral_private_keys_deleted_count=5)),
        ("production_cert_mutation",lambda x:x["cleanup"].update(production_cert_or_trust_stores_changed=True)),
        ("fake_git_fencing",lambda x:x["hard_limits_and_nonclaims"].update(github_git_ref_or_pr_effect_fenced=True)),
        ("fake_mac_writer",lambda x:x["hard_limits_and_nonclaims"].update(mac_native_github_writer_credential_verified=True)),
        ("fake_HA",lambda x:x["hard_limits_and_nonclaims"].update(multi_node_quorum_high_availability_proven=True)),
        ("fake_cross_store",lambda x:x["hard_limits_and_nonclaims"].update(external_mac_filesystem_and_etcd_2pc_atomic_proven=True)),
    ]
    for name,change in mutations:
        mutant=copy.deepcopy(obj)
        change(mutant)
        try:verify(mutant)
        except Denied:cases+=1
        else:raise AssertionError("FALSE_POSITIVE_"+name)
    need(cases==35,"WRONG_ADVERSARIAL_TEST_COUNT")
    return {"status":"PASS_OFFLINE","tests":cases,
            "provider_connections":0,"server_processes_started":0,
            "filesystem_effects_created":0,"git_remote_writes":0,
            "model_calls":0,"production_authority":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("verify","selftest"))
    args=p.parse_args()
    value=json.loads(RECEIPT.read_text(encoding="utf-8"))
    result=verify(value) if args.mode=="verify" else selftest(value)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    try:main()
    except (Denied,AssertionError,KeyError,TypeError,ValueError,OSError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:150],
                          "provider_connections":0,"git_remote_writes":0},sort_keys=True))
        sys.exit(2)
