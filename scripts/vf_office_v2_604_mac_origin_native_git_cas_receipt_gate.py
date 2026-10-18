#!/usr/bin/env python3
"""#604 offline bounded audit of physical Mac-origin / Win-native GitHub CAS.

Operator-collected synthetic remote ref evidence is a SHA-pinned witness, NOT
signed proof of production GitHub/etcd atomicity. Offline modes only; never
call live HTTPS, git, push, leases, process shutdown or user credentials.
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
RECEIPT=P2/"p0-mac-origin-windows-real-github-ref-cas-2026-10-10.json"
SERVER=ROOT/"scripts/vf_office_v2_604_mac_fixture_mtls_lab.py"
SINK=ROOT/"scripts/vf_office_v2_604_windows_native_git_cas_sink_lab.py"
SCHEMA="velvetos.office-v2.604.mac-origin-real-github-native-cas-lab.v1"
BASE="cc2cccb2770a79424741719795d552fa85d69a81"
SEED="c57fad167c82ab302b3303ec0c9178d0e59932c3"
A="17ff710e753311cc6be69bfa9069adfc3da94c44"
B="3d4b78da882b0457debc663d4cc5aba4b55675ff"
REF="refs/heads/office-v2-lab-604-mac-origin-cas-20261010"
REPO="nocturney/velvetos-core"
SOURCE_SHAS={
 "server":"9ed711552f14ba099b8b4bc7d371f69ff36251caca66c2ce541046be9605fcec",
 "sink":"a0eb08af718e3140d0cb8bb514fc8d7a8818a04019a90901890b4a923f1e02ea"}
# phase, GitHub ref before, GitHub ref after, object sent, fixture
# expected SHA, actual Git push exit, status
EXPECTED=[
 ("seed","",SEED,SEED,"",0,"PASS_REAL_GITHUB_REF_CAS_ACCEPTED"),
 ("effect_a",SEED,A,A,SEED,0,"PASS_REAL_GITHUB_REF_CAS_ACCEPTED"),
 ("stale_b",A,A,B,SEED,1,"PASS_REAL_GITHUB_REF_STALE_CAS_REJECTED"),
 ("fresh_b",A,B,B,A,0,"PASS_REAL_GITHUB_REF_CAS_ACCEPTED"),
 ("stale_a",B,B,A,A,1,"PASS_REAL_GITHUB_REF_STALE_CAS_REJECTED"),
 ("cleanup",B,"","",B,0,"PASS_REAL_GITHUB_REF_CAS_ACCEPTED"),
]
FORBIDDEN=(
 "two_distinct_native_host_git_writers",
 "connected_to_etcd_fencing_generation",
 "atomic_cross_store_provider_and_github_effect",
 "arbitrary_malicious_git_credential_user_blocked",
 "multiple_remote_receiver_failover",
 "network_partition_or_clock_skew_passing",
 "mac_native_git_push_rights_proven",
 "production_branch_edit_or_merge_authorized",
 "agent_generated_protected_pr",
 "unresolved_unknown_auto_reconciled",
 "second_fleet_scheduler_created",
 "paid_model_or_codex_run",
)


class Denied(Exception):
    pass


def need(ok, message):
    if not ok:
        raise Denied(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(v):
    need(type(v) is dict and v.get("schema")==SCHEMA
         and v.get("date")=="2026-10-10"
         and v.get("status")==
         "PASS_ONE_NATIVE_WIN_GIT_WRITER_MAC_MTLS_ORIGIN_SCRATCH_REF_CAS_ONLY"
         and v.get("owner_issue")==604 and v.get("consumer_issue")==612,
         "WRONG_RECEIPT_IDENTITY")
    p=v.get("provenance") or {}
    need(p.get("canonical_main_at_begin_and_after")==BASE
         and p.get("hosts")==["MacMiniOffice.local","Chris Windows"]
         and p.get("mac_native_git_writer_authorized") is False
         and p.get("windows_native_gh_auth_push_true") is True
         and p.get("windows_git_helper_or_global_creds_modified") is False
         and p.get("scratch_remote_ref")==REF
         and p.get("mac_role")==
         "mTLS-authenticated read-only fixture origin and independent GitHub ref reader"
         and p.get("windows_role")==
         "sole authenticated native git writer and mTLS request consumer"
         and p.get("git_cas_operation")==
         "native Git push --force-with-lease=ref:expected SHA including guarded deletion"
         and p.get("provider_lease_integrated") is False
         and p.get("external_sink_ref_cas_proven") is True
         and p.get("cross_store_etcd_git_transaction_proven") is False
         and p.get("mac_original_credentials_from_github_app_copied") is False
         and p.get("mac_to_win_direct_connection_succeeded") is False
         and p.get("windows_to_mac_tls_requests_succeeded") is True
         and p.get("mac_mtls_service_ip")=="192.168.0.217"
         and p.get("mac_mtls_service_port")==32683
         and p.get("model_calls")==p.get("codex_cli_calls")==p.get("api_spend")==0
         and p.get("agent_authored_pr")==0
         and p.get("core_source_real_branch_changes")==0
         and p.get("business_cad_social_printer_effects")==0,
         "AUTHORITY_PROVENANCE_SCOPE_DRIFT")
    t=v.get("temporary_mtls") or {}
    need(t.get("public_ca_sha256")==
         "85a68f7aaf4287ad526d4ee0f8c7b73e02b42378873447d3bf367eb3c9796964"
         and t.get("public_server_sha256")==
         "65d9d4b5fb266d7c346c2d8438dd060c825b40ae8aa06806bd8bc61b35885b36"
         and t.get("public_win_client_sha256")==
         "233fc03d7adbe42b278b1834401bb06392ce62ba84b930218587da391c817fce"
         and t.get("client_cert_cn")=="vf604-win-native-github-cas-sink"
         and t.get("ephemeral_only") is True
         and t.get("local_private_ca_deleted") is True
         and t.get("mac_server_private_deleted") is True
         and t.get("mac_win_client_private_deleted") is True
         and t.get("win_copy_client_private_deleted") is True
         and t.get("win_copy_ca_and_public_certificate_deleted") is True
         and t.get("system_trust_stores_unchanged") is True
         and t.get("server_ephemeral_pid")==78451
         and t.get("server_stopped_after_receipts") is True
         and t.get("final_mac_port32683_listeners")==0
         and t.get("no_autostart") is True,
         "TEMP_AUTHENTICATION_OR_CLEANUP_UNVERIFIED")
    need(sha(SERVER)==SOURCE_SHAS["server"]
         and sha(SINK)==SOURCE_SHAS["sink"],
         "SOURCE_BYTES_CHANGED")
    commits=v.get("commits") or {}
    need(commits.get("base")==BASE and
         commits.get("seed")==SEED and
         commits.get("a")==A and commits.get("b")==B and
         commits.get("effects_are_synthetic_commits_using_original_core_tree") is True,
         "ACTUAL_GIT_OBJECT_LINEAGE_MISMATCH")
    rows=v.get("actual_windows_native_git_receipts")
    need(type(rows) is list and len(rows)==6,"NATIVE_WINDOWS_SIX_RECEIPTS_REQUIRED")
    seen=set()
    for row,wanted in zip(rows,EXPECTED):
        phase,before,after,candidate,expect,exit_code,state=wanted
        need(type(row) is dict and
             row.get("schema")=="vf604.mac-origin-win-native-git-cas-effect.v1"
             and row.get("phase")==phase and phase not in seen
             and row.get("repo")==REPO and row.get("ref")==REF
             and row.get("git_base")==BASE
             and row.get("before")==before and row.get("after")==after
             and row.get("candidate_sha")==candidate
             and row.get("expected_sha")==expect
             and row.get("git_push_exit_code")==exit_code
             and row.get("status")==state
             and row.get("client_mtls") is True
             and row.get("sole_git_writer")==
             "CHRIS_WINDOWS_NATIVE_AUTHENTICATED_GIT"
             and row.get("external_git_ref_cas_at_sink") is True
             and row.get("provider_lease_integrated") is False
             and row.get("no_production_or_protected_main_writes") is True
             and row.get("no_codex_or_paid_model") is True
             and bool(re.fullmatch("[0-9a-f]{64}",
                                   str(row.get("request_sha256")))),
             "REAL_GIT_CAS_REQUEST_WRITE_OR_REMOTE_READBACK_DRIFT")
        seen.add(phase)
    need(seen==set(x[0] for x in EXPECTED),
         "DUPLICATE_OR_MISSING_REMOTE_PUSH_PHASE")
    final=v.get("final_independent_postconditions") or {}
    need(final.get("mac_ls_remote_scratch_ref_absent") is True
         and final.get("windows_ls_remote_scratch_ref_absent") is True
         and final.get("mac_ls_remote_main_unchanged") is True
         and final.get("windows_ls_remote_main_unchanged") is True
         and final.get("mac_independent_midway_readback_seed_sha")==SEED
         and final.get("mac_independent_midway_readback_a_sha")==A
         and final.get("mac_independent_precleanup_readback_b_sha")==B
         and final.get("stale_b_actual_native_git_push_exit")==1
         and final.get("stale_a_actual_native_git_push_exit")==1
         and final.get("accepted_remote_pushes")==3
         and final.get("guarded_branch_deletions")==1
         and final.get("stale_denials")==2
         and final.get("remaining_lab_branches")==0
         and final.get("canonical_main_sha")==BASE,
         "REMOTE_CAS_EFFECT_AND_CLEANUP_NOT_VERIFIED")
    stop=v.get("nonclaims") or {}
    need(set(stop)==set(FORBIDDEN)
         and all(stop.get(k) is False for k in FORBIDDEN),
         "FALSE_PROVIDER_OR_PRODUCTION_PROMOTION")
    need(v.get("future_gate","").startswith("Issue #604 choose one authority"),
         "OWNER_NEXT_STEP_LOST")
    return {"status":"PASS_OFFLINE_MAC_ORIGIN_REAL_GITHUB_SINK_CAS_ONLY",
            "physical_hosts":2,"native_git_writers":1,
            "real_remote_ref_effect_pushes":3,
            "stale_native_git_pushes_denied":2,
            "guarded_deleted_test_refs":1,"unremoved_test_refs":0,
            "provider_fencing_integrated":False,
            "mac_native_git_writer":False,
            "git_effects_this_verification":0,
            "production_authority":False}


def selftest(original):
    verify(original)
    count=1
    muts=[
        ("fake_production",lambda x:x.update(status="PRODUCTION_READY")),
        ("fake_writer",lambda x:x["provenance"].update(mac_native_git_writer_authorized=True)),
        ("fake_mac_native",lambda x:x["nonclaims"].update(mac_native_git_push_rights_proven=True)),
        ("fake_provider",lambda x:x["provenance"].update(provider_lease_integrated=True)),
        ("fake_cross_store",lambda x:x["nonclaims"].update(atomic_cross_store_provider_and_github_effect=True)),
        ("owner_issue",lambda x:x.update(owner_issue=612)),
        ("fake_cli",lambda x:x["provenance"].update(codex_cli_calls=1)),
        ("credentials_changed",lambda x:x["provenance"].update(windows_git_helper_or_global_creds_modified=True)),
        ("wrong_repo",lambda x:x["actual_windows_native_git_receipts"][3].update(repo="other/repo")),
        ("wrong_ref",lambda x:x["actual_windows_native_git_receipts"][0].update(ref="refs/heads/main")),
        ("wrong_base",lambda x:x["commits"].update(base="0"*40)),
        ("too_many_effects",lambda x:x["final_independent_postconditions"].update(accepted_remote_pushes=4)),
        ("write_loser",lambda x:x["actual_windows_native_git_receipts"][2].update(git_push_exit_code=0)),
        ("silent_stale",lambda x:x["actual_windows_native_git_receipts"][4].update(status="PASS_REAL_GITHUB_REF_CAS_ACCEPTED")),
        ("after_tamper",lambda x:x["actual_windows_native_git_receipts"][3].update(after="0"*40)),
        ("expected_tamper",lambda x:x["actual_windows_native_git_receipts"][4].update(expected_sha=B)),
        ("candidate_tamper",lambda x:x["actual_windows_native_git_receipts"][1].update(candidate_sha=B)),
        ("duplicate_phase",lambda x:x["actual_windows_native_git_receipts"][4].update(phase="stale_b")),
        ("missing_receipt",lambda x:x["actual_windows_native_git_receipts"].pop()),
        ("force_claim",lambda x:x["provenance"].update(git_cas_operation="force push without lease")),
        ("malicious_request",lambda x:x["actual_windows_native_git_receipts"][3].update(request_sha256="0"*20)),
        ("bad_mtls",lambda x:x["actual_windows_native_git_receipts"][1].update(client_mtls=False)),
        ("ca_changed",lambda x:x["temporary_mtls"].update(public_ca_sha256="0"*64)),
        ("left_key",lambda x:x["temporary_mtls"].update(mac_server_private_deleted=False)),
        ("left_server",lambda x:x["temporary_mtls"].update(final_mac_port32683_listeners=1)),
        ("branch_left",lambda x:x["final_independent_postconditions"].update(remaining_lab_branches=1)),
        ("hidden_main_write",lambda x:x["final_independent_postconditions"].update(mac_ls_remote_main_unchanged=False)),
        ("wrong_mac_observe",lambda x:x["final_independent_postconditions"].update(mac_independent_midway_readback_a_sha=SEED)),
        ("lost_provider_boundary",lambda x:x["nonclaims"].update(connected_to_etcd_fencing_generation=True)),
        ("fake_agent_pr",lambda x:x["nonclaims"].update(agent_generated_protected_pr=True)),
        ("unverified_windows_writer",lambda x:x["provenance"].update(windows_native_gh_auth_push_true=False)),
        ("paid_model",lambda x:x["provenance"].update(model_calls=1)),
        ("false_2_native_writers",lambda x:x["nonclaims"].update(two_distinct_native_host_git_writers=True)),
    ]
    for label,mod in muts:
        x=copy.deepcopy(original)
        mod(x)
        try:verify(x)
        except Denied:count+=1
        else:raise AssertionError("FALSE_ALLOW_"+label)
    need(count==34,"ADVERSARIAL_CASE_COUNT_CHANGED")
    return {"status":"PASS_OFFLINE","cases":count,
            "network_calls":0,"git_pushes":0,"server_started":False,
            "client_credentials_used":False,
            "production_authority":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("verify","selftest"))
    mode=p.parse_args().mode
    data=json.loads(RECEIPT.read_text(encoding="utf-8"))
    print(json.dumps(verify(data) if mode=="verify" else selftest(data),
                     sort_keys=True))


if __name__=="__main__":
    try:main()
    except (Denied,AssertionError,KeyError,ValueError,TypeError,OSError) as error:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(error)[:170],
                          "network_calls":0,"git_effects":0},sort_keys=True))
        sys.exit(2)
