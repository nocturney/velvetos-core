#!/usr/bin/env python3
"""#604 offline independent receipt & adversarial claims refusal.

Original witness assembled from actual physical Mac etcdctl and Windows Git
native stdout/receipts; not a signed hardware attestation. This gate does
not connect to network, launch services, read credentials or modify Git.
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
NAME="p0-real-etcd-expiry-github-epoch-cutover-2026-10-10.json"
RECEIPT=P2/NAME
SCHEMA="velvetos.office-v2.604.real-etcd-lease-expiry-vs-github-epoch-cutover.v1"
MAIN="04ba7ae09d8c4197fd02afe496e15aad755af3cb"
REF="refs/heads/office-v2-lab-604-epoch-cutover-20261010"
S="7958921899f174efffe88c3a6be32091949ef3b1"
U="e37698994d9e5a2277e40b794c6c5b0c87e2a024"
M="132e4b3ecfc5b3d76b49d536bfdb53eb5a5341be"
F="6d2edc95386fc09849214afd0d4fa38a3f98b136"
STALE="361038f8e3b4c2883605efa3b52a5d771616140b"
SOURCES={
 "provider":("vf_office_v2_604_provider_epoch_cutover_lab.py",
 "be2315a669cd1228de9681f83cd049edd12d76f4705d958898bf65936cf14e5c"),
 "mac_fixture":("vf_office_v2_604_epoch_mtls_fixture_lab.py",
 "d6876e80d7a6ccdee5382da094ae57d8d8154e6ac1f4ad2893e8c5a70049c4c5"),
 "win_git_sink":("vf_office_v2_604_epoch_native_git_sink_lab.py",
 "2d5c0bba882658bef67e4e8fd6dc5bd4686df7e9e0a7817908ad8c278bec5c34"),
}
STEPS=[
 # phase, generation, provider_revis, expectedSha, refBefore,
 # refAfter, candidate, exitCode, expected status
 ("seed",2,3,"","",S,S,0,"PASS_REAL_GITHUB_EPOCH_REF_CAS"),
 ("unsafe_expired",2,4,S,S,U,U,0,
  "PASS_INTENTIONAL_UNSAFE_EXPIRED_OWNER_GIT_ACCEPTED"),
 ("cutover",5,6,U,U,M,M,0,"PASS_REAL_GITHUB_EPOCH_REF_CAS"),
 ("stale_denied",2,7,U,M,M,STALE,1,
  "PASS_REAL_NATIVE_GIT_STALE_CAS_DENIED"),
 ("fresh_new",5,7,M,M,F,F,0,"PASS_REAL_GITHUB_EPOCH_REF_CAS"),
 ("cleanup",5,7,F,F,"","",0,"PASS_REAL_GITHUB_EPOCH_REF_CAS"),
]
MAC_EVIDENCE={
 "old-owner.json":"f0bf8e049b8995acd78f7a75804d5e9da1e6bbb6f820db06734f021822f22fbd",
 "new-owner.json":"6529ef5c16c9695b97db940bd49baea92f6d050dcdb8a548a4d10688aed82767",
 "activation.json":"34de50208b94195994c853a3933a8a98a34e0c8975ee0facfbc15e2c7e26a279",
 "old-tip-before-cutover.json":"66af1b326b76f779f1e84cc3edfb6751d71471a7f832628373a02418dcd946c3",
}
WIN_EVIDENCE={
 "seed.json":"94b258f6a45e13091ed89a227b9ec3cad400beeacce3730babe0530b1b6641f7",
 "unsafe_expired.json":"efca78b7c2639b2185a7d9453f03ac8b2e62ea8bf36a6a9cd404a8e2a95433f1",
 "cutover.json":"d247596eaa17408d18ecea576b99822f2465472aee0a082839ccc6d74c753d71",
 "stale_denied.json":"e18fa9cdcd4aa72efe59f27ade4a38c39b92b12bf1e22c1b221a0a1ca6e3c30d",
 "fresh_new.json":"6b1484214b645fa20fdd63b402240e0952c7c6a7f73db7738e782728756a4819",
 "cleanup.json":"0fb7d2bb264e49de8ff544a4f364f00aa78785eb7dd01a98b01abf8e586a0263",
}
PROVIDER_CONDITIONS={
 "seed":"LIVE_OLD_LEASE_ACTIVE",
 "unsafe_expired":"EXPIRED_OWNER_NO_AUTHORITATIVE_PROVIDER_LEASE",
 "cutover":"PENDING_NEW_OWNER_NOT_YET_ADMITTED",
 "stale_denied":"STALE_OWNER_AFTER_NEW_EPOCH_ACTIVE",
 "fresh_new":"ACTIVE_NEW_EPOCH_WITH_CURRENT_GIT_REF",
 "cleanup":"ACTIVE_NEW_EPOCH_WITH_CURRENT_GIT_REF",
}
NONCLAIMS=(
 "globally_atomic_etcd_and_github_commit",
 "expired_worker_guaranteed_blocked_without_git_ref_cutover",
 "provider_expiry_and_remote_git_ref_updated_atomically",
 "arbitrary_malicious_windows_git_credential_user_blocked",
 "two_native_physical_git_writers",
 "production_os_acl_or_identity_lifecycle_validated",
 "quorum_ha_partition_skew_validated",
 "unbounded_git_push_duration_safe",
 "unknown_outcome_safely_auto_reconciled",
 "agent_authored_protected_pr",
 "main_branch_modified_by_experiment",
 "second_scheduler_created",
 "provider_selected_for_production",
)

class Refuse(Exception):pass

def need(cond,reason):
 if not cond:raise Refuse(reason)

def sha(b):
 return hashlib.sha256(b).hexdigest()

def verify(v):
 need(type(v) is dict and v.get("schema")==SCHEMA
      and v.get("date")=="2026-10-10"
      and v.get("status")==
      "PASS_REAL_PROVIDER_EXPIRY_ACCEPTS_UNSAFE_GIT_THEN_EPOCH_MARKER_CUTOVER_BLOCKS_STALE_CAS_SCOPE_ONLY"
      and v.get("owner_issue")==604 and v.get("consumer_issue")==612,
      "RECEIPT_IDENTITY_MISMATCH")
 p=v.get("scope") or {}
 need(p.get("physical_hosts")==["MacMiniOffice.local","Chris Windows"]
      and p.get("source_main")==MAIN
      and p.get("provider")==
      "temporary official SHA-pinned etcd 3.6.15 single-node; AuthRevision 13"
      and p.get("provider_binary_sha256")==
      "dd2596ab902c23252da55e770cb7f7216522ae5599f84d2a20e0e7272d52fe82"
      and p.get("provider_client_tls_mtls_rbac_enabled") is True
      and p.get("provider_client_endpoint")=="https://192.168.0.217:32779"
      and p.get("provider_namespace")==
      "/velvet-office2/lab604/epoch-github-20261010/"
      and p.get("provider_is_unique_lease_authority") is True
      and p.get("provider_root_isolated") is True
      and p.get("provider_peer_http_loopback_only") is True
      and p.get("git_effect_authority")==
      "GitHub ref native --force-with-lease by existing Windows native identity only"
      and p.get("windows_is_only_native_git_writer") is True
      and p.get("mac_native_git_push_credential_proven") is False
      and p.get("mac_request_transport")==
      "Temporary Mac read-only HTTPS mTLS fixture :32781 polled by Windows client"
      and p.get("scratch_ref")==REF
      and all(p.get(k) is True for k in
          ("no_software_model_calls","no_codex_cli","no_paid_api",
           "no_business_cad_printer_social_effects",
           "no_production_authority","no_autostart_or_system_config_changes")),
      "FLEET_PROVIDER_OR_PRODUCTION_SCOPE_DRIFT")
 need(v.get("provider_public_ca_cert_sha256")==
      "53347fcfe03baf2242b8addd7581a29f0000e0b5b96bf49621f62e9450732253"
      and v.get("fixture_public_cert_sha256")==
      "f544389f1a55b829f422839e4cf6260c1e09b3f22e411dc18cfebd5ef7cc678a"
      and v.get("windows_public_client_cert_sha256")==
      "fd30c6f27eb7d17786b3ab24af6c067e4421a61a81ff42452b7fb31e87b0d532"
      and v.get("provider_public_cert_sha256")==
      "61162b3f90bb830c9227c4eb280fcf061e8d58d90b2352424e90609bd1861c8d",
      "CLIENT_TLS_PROVIDER_CERT_SHA_NOT_PINNED")
 need(v.get("original_mac_provider_logs_hashes")==MAC_EVIDENCE
      and v.get("original_windows_native_git_receipt_hashes")==WIN_EVIDENCE,
      "ORIGINAL_TWO_HOST_EVIDENCE_HASH_MISSING")
 pin=v.get("source_pins") or {}
 need(set(pin)==set(SOURCES),"SOURCE_SET_DRIFT")
 for name,(file,digest) in SOURCES.items():
  need(pin.get(name)==digest and
       sha((ROOT/"scripts"/file).read_bytes())==digest,
       "EXACT_SOURCE_FILE_HASH_CHANGED")
 mac=v.get("sanitized_mac_provider_records") or {}
 need(set(mac)=={"old-owner","new-owner","activation","old-tip-before-cutover"}
      and mac["old-owner"].get("actor")=="old"
      and mac["old-owner"].get("generation")==2
      and mac["old-owner"].get("ttl")==26
      and mac["old-owner"].get("state")=="ACTIVE"
      and mac["new-owner"].get("actor")=="new"
      and mac["new-owner"].get("generation")==5
      and mac["new-owner"].get("ttl")==360
      and mac["new-owner"].get("state")=="PENDING_CUTOVER"
      and mac["activation"].get("owner_generation")==5
      and mac["activation"].get("prior_state")=="PENDING_CUTOVER"
      and mac["activation"].get("active_state")=="ACTIVE"
      and mac["activation"].get("marker_sha")==M
      and mac["old-tip-before-cutover"].get("pre_cutover_sha")==U,
      "PROVIDER_EPOCH_AND_CUTOVER_WITNESS_UNVERIFIED")
 rows=v.get("real_native_github_effect_receipts")
 need(type(rows) is list and len(rows)==6,"MISSING_ACTUAL_NATIVE_GIT_RECEIPTS")
 for row,expected in zip(rows,STEPS):
  phase,gen,rev,lease_sha,before,after,candidate,exit_code,status=expected
  need(type(row) is dict and
       row.get("schema")=="vf604.epoch-cutover-real-native-git-receipt.v1"
       and row.get("phase")==phase and
       row.get("ref")==REF and row.get("repo")=="nocturney/velvetos-core"
       and row.get("base")==MAIN
       and row.get("mac_provider_generation")==gen
       and row.get("provider_observed_revision")==rev
       and row.get("provider_condition")==PROVIDER_CONDITIONS[phase]
       and row.get("expected_ref_sha")==lease_sha
       and row.get("before_ref_sha")==before
       and row.get("after_ref_sha")==after
       and row.get("synthetic_candidate_commit")==candidate
       and row.get("native_git_push_exit")==exit_code
       and row.get("status")==status
       and row.get("real_mtls_mac_fixture") is True
       and row.get("sole_git_writer")==
       "WIN_EXISTING_NATIVE_GITHUB_IDENTITY"
       and row.get("fully_atomic_etcd_github_fencing") is False
       and row.get("production_authority") is False
       and bool(re.fullmatch("[0-9a-f]{64}",
           str(row.get("mac_request_sha256")))),
       "REAL_ETCD_MAC_TO_WINDOWS_NATIVE_GITHUB_RECEIPT_NOT_EXACT")
 transition=v.get("verified_live_transition") or {}
 need(transition.get("old_owner_generation")==2
      and transition.get("old_owner_grant_ttl_seconds")==26
      and transition.get("old_owner_record_initial_revision")==3
      and transition.get("old_owner_expired_no_active_lease_revision")==4
      and transition.get("unsafe_old_owner_commit_accepted_after_provider_expiry") is True
      and transition.get("unsafe_old_owner_push_result_sha")==U
      and transition.get("new_owner_pending_claim_generation")==5
      and transition.get("new_owner_pending_record_revision")==6
      and transition.get("new_owner_pending_state")=="PENDING_CUTOVER"
      and transition.get("new_epoch_marker_sha")==M
      and transition.get("marker_has_real_new_provider_generation")==5
      and transition.get("new_owner_activated_only_after_mac_git_remote_readback_and_commit_body") is True
      and transition.get("new_owner_activated_provider_revision")==7
      and transition.get("old_generation2_git_attempt_rejected_after_epoch_marker") is True
      and transition.get("old_generation2_stale_candidate_sha")==STALE
      and transition.get("old_generation2_stale_push_exit")==1
      and transition.get("git_remains_epoch_marker_after_stale_denial") is True
      and transition.get("new_owner_generation5_effect_accepted_sha")==F
      and transition.get("branch_guarded_deletion_accepted") is True
      and transition.get("provider_new_owner_revoked_revision")==8
      and transition.get("real_provider_owner_key_final_absent") is True
      and transition.get("original_remote_ref_final_absent_both_hosts") is True
      and transition.get("canonical_main_unchanged_both_hosts") is True
      and transition.get("final_canonical_main")==MAIN,
      "CRITICAL_UNSAFE_WRITE_OR_EPOCH_CUTOVER_EVIDENCE_MISSING")
 clean=v.get("cleanup") or {}
 need(clean.get("exact_etcd_pid")==82356 and
      clean.get("exact_fixture_pid")==82991 and
      clean.get("both_exact_processes_verified_stopped") is True
      and clean.get("mac_listening_lab_port_count")==0
      and clean.get("windows_reachability_etcd_port32779") is False
      and clean.get("windows_reachability_fixture_port32781") is False
      and clean.get("mac_isolated_private_keys_removed")==7
      and clean.get("windows_isolated_test_key_cert_ca_removed")==3
      and clean.get("production_trust_store_or_github_auth_modified") is False
      and clean.get("server_autostart_created") is False
      and clean.get("stopped_preserved_etcd_db_sha256")==
      "58b420ee0fa6fcd76ecd3478191704e986a99e065924e8ca3cfcf801947505a9",
      "TEMP_ISOLATED_SERVICE_OR_CREDENTIAL_CLEANUP_UNVERIFIED")
 n=v.get("nonclaims") or {}
 need(set(n)==set(NONCLAIMS) and
      all(n.get(k) is False for k in NONCLAIMS),
      "UNSAFE_FALSE_ETCD_GITHUB_GLOBAL_ATOMICITY_PROMOTION")
 need(v.get("next_gate","").startswith("Single #604 ready-made lease authority"),
      "OWNER_BOUNDARY_NEXT_REQUIRED_GATE_MISSING")
 return {"status":"PASS_OFFLINE_REAL_EXPIRY_AND_EPOCH_CUTOVER",
         "physical_hosts":2,"provider_generations":[2,5],
         "real_git_ref_pushes_accepted":4,
         "stale_after_epoch_git_push_denied":1,
         "unsafe_expired_owner_git_push_accepted":1,
         "remote_scratch_refs_left":0,
         "provider_owners_left":0,
         "globally_atomic_fencing_proven":False,
         "production_authority":False,"git_remote_calls":0,
         "model_calls":0}

def selftest(original):
 verify(original)
 n=1
 muts=[
 ("falsify_global_success",lambda x:x.update(status="PRODUCTION_READY")),
 ("wrong_main",lambda x:x["scope"].update(source_main="0"*40)),
 ("new_provider",lambda x:x["scope"].update(provider_is_unique_lease_authority=False)),
 ("disable_tls",lambda x:x["scope"].update(provider_client_tls_mtls_rbac_enabled=False)),
 ("invent_second_writer",lambda x:x["scope"].update(windows_is_only_native_git_writer=False)),
 ("wrong_branch",lambda x:x["scope"].update(scratch_ref="refs/heads/main")),
 ("bad_ca",lambda x:x.update(provider_public_ca_cert_sha256="0"*64)),
 ("missing_original_win_receipts",lambda x:x["original_windows_native_git_receipt_hashes"].pop("unsafe_expired.json")),
 ("missing_original_mac_log",lambda x:x["original_mac_provider_logs_hashes"].pop("activation.json")),
 ("source_pin_falsified",lambda x:x["source_pins"].update(win_git_sink="0"*64)),
 ("old_expiry_not_real",lambda x:x["verified_live_transition"].update(old_owner_expired_no_active_lease_revision=0)),
 ("unsafe_missing",lambda x:x["verified_live_transition"].update(unsafe_old_owner_commit_accepted_after_provider_expiry=False)),
 ("unsafe_exit_denied",lambda x:x["real_native_github_effect_receipts"][1].update(native_git_push_exit=1)),
 ("unsafe_commit_changed",lambda x:x["real_native_github_effect_receipts"][1].update(after_ref_sha="0"*40)),
 ("cutover_claim_active_first",lambda x:x["sanitized_mac_provider_records"]["new-owner"].update(state="ACTIVE")),
 ("cutover_git_ref_wrong",lambda x:x["sanitized_mac_provider_records"]["activation"].update(marker_sha=U)),
 ("cutover_not_verifiable",lambda x:x["verified_live_transition"].update(new_owner_activated_only_after_mac_git_remote_readback_and_commit_body=False)),
 ("old_gen_wrong",lambda x:x["sanitized_mac_provider_records"]["old-owner"].update(generation=3)),
 ("new_gen_wrong",lambda x:x["real_native_github_effect_receipts"][2].update(mac_provider_generation=2)),
 ("new_prov_revision_wrong",lambda x:x["real_native_github_effect_receipts"][4].update(provider_observed_revision=5)),
 ("old_stale_accepted",lambda x:x["real_native_github_effect_receipts"][3].update(native_git_push_exit=0)),
 ("old_stale_wrote",lambda x:x["real_native_github_effect_receipts"][3].update(after_ref_sha=STALE)),
 ("stale_revert",lambda x:x["real_native_github_effect_receipts"][3].update(status="PASS_REAL_GITHUB_EPOCH_REF_CAS")),
 ("fresh_new_missing",lambda x:x["verified_live_transition"].update(new_owner_generation5_effect_accepted_sha=M)),
 ("duplicate_phase",lambda x:x["real_native_github_effect_receipts"][4].update(phase="seed")),
 ("missing_cleanup_receipt",lambda x:x["real_native_github_effect_receipts"].pop()),
 ("branch_left_live",lambda x:x["verified_live_transition"].update(original_remote_ref_final_absent_both_hosts=False)),
 ("lease_not_revoked",lambda x:x["verified_live_transition"].update(real_provider_owner_key_final_absent=False)),
 ("etcd_live_left",lambda x:x["cleanup"].update(both_exact_processes_verified_stopped=False)),
 ("win_port_open",lambda x:x["cleanup"].update(windows_reachability_etcd_port32779=True)),
 ("mac_test_keys_left",lambda x:x["cleanup"].update(mac_isolated_private_keys_removed=6)),
 ("windows_test_key_left",lambda x:x["cleanup"].update(windows_isolated_test_key_cert_ca_removed=2)),
 ("false_atomicity",lambda x:x["nonclaims"].update(globally_atomic_etcd_and_github_commit=True)),
 ("false_no_window",lambda x:x["nonclaims"].update(expired_worker_guaranteed_blocked_without_git_ref_cutover=True)),
 ("false_git_user_guard",lambda x:x["nonclaims"].update(arbitrary_malicious_windows_git_credential_user_blocked=True)),
 ("fake_agent_production",lambda x:x["nonclaims"].update(agent_authored_protected_pr=True)),
 ("fake_ha",lambda x:x["nonclaims"].update(quorum_ha_partition_skew_validated=True)),
 ("auth_changed",lambda x:x["cleanup"].update(production_trust_store_or_github_auth_modified=True)),
 ]
 for name,fn in muts:
  v=copy.deepcopy(original);fn(v)
  try:verify(v)
  except Refuse:n+=1
  else:raise AssertionError("NEGATIVE_CASE_FALSE_ALLOW_"+name)
 need(n==39,"ADVERSARIAL_DENIAL_COUNT_DRIFT")
 return {"status":"PASS_OFFLINE","cases":n,
         "git_effect_writes":0,"provider_requests":0,
         "github_network_calls":0,"certificate_secret_reads":0,
         "production_authority":False}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("mode",choices=("verify","selftest"))
 x=json.loads(RECEIPT.read_text(encoding="utf-8"))
 mode=p.parse_args().mode
 print(json.dumps(verify(x) if mode=="verify" else selftest(x),
                  sort_keys=True))

if __name__=="__main__":
 try:main()
 except (Refuse,AssertionError,ValueError,TypeError,KeyError,OSError) as e:
  print(json.dumps({"status":"FAIL_CLOSED","reason":str(e)[:160],
                    "external_network_effects":0}))
  sys.exit(3)
