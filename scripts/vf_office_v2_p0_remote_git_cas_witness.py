#!/usr/bin/env python3
"""Office P0 #612: fail-closed historical witness of real LAB GitHub ref CAS.

One actual GitHub remote ref; two distinct native Windows Git client processes;
explicit --force-with-lease=ref:expected_old; winner accepted, stale loser
denied, stale retry denied, then exact-winner-sha CAS delete. Physical Mac
readback verified the ref gone, but Mac WRITE auth was NOT available.

This is NOT a #604-issued lease / distributed fencing provider, effect receiver
authorization, recovery rule, model writing, or independent Mac writer test.
CI ONLY calls offline verify/selftest; live-readback is explicitly manual,
read-only and never invoked by the Office contract or scheduler.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess

SCHEMA = "velvetos.office-v2.p0-remote-git-ref-cas-one-host-receipt.v0"
STATUS = "PASS_ONE_HOST_TWO_ISOLATED_REMOTE_CAS_CONTENDERS_CLEANED"
REPO = "nocturney/velvetos-core"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
ORIGIN = "https://github.com/nocturney/velvetos-core.git"
MAIN = "1237f2c2f09f65937a9543a60edaa7b3e3c6d36f"
REF = "refs/heads/lab/office-p0-cas-20261010-gpt6-j01"
WIN1 = "99389febd5c3212b61f314f9d4fe96bdf8893b0e"
WIN2 = "79969cf5b9088696880a43013c7b7cbba82510fd"
MAC_LOCAL = "200ec212ede7e9c56cf21eee3c0a4a7512209e59"
HEX40 = re.compile(r"[a-f0-9]{40}\Z")


class Refused(Exception):
    pass


def need(ok, reason):
    if not ok:
        raise Refused(reason)


def exact_sha(value):
    return isinstance(value, str) and HEX40.fullmatch(value) is not None


def validate(row):
    need(isinstance(row, dict) and row.get("schema") == SCHEMA
         and row.get("status") == STATUS and row.get("repo") == REPO
         and row.get("issue") == ISSUE
         and row.get("scope") ==
             "HOST_LOCAL_TWO_WINDOWS_CLIENTS_AGAINST_REAL_GITHUB_REMOTE_REF",
         "INCORRECT_SCOPE_OR_PROVENANCE")
    base = row.get("original_remote_state") or {}
    need(base.get("initial_origin_main") == MAIN
         and base.get("initial_scratch_ref") is None
         and base.get("scratch_ref_created_to") == MAIN
         and base.get("remote_origin") == ORIGIN
         and base.get("scratch_ref") == REF
         and base.get("scratch_ref_created_by") == "Chris",
         "BASE_AND_EXCLUSIVE_SCRATCH_REF_NOT_PROVEN")
    contenders = row.get("contenders") or {}
    need(isinstance(contenders,dict) and set(contenders)=={"win1","win2","mac"}
         and len({c.get("local_commit_sha") for c in contenders.values()
                  if isinstance(c,dict)}) == 3,
         "EXACTLY_THREE_DISTINCT_GIT_COMMIT_IDS_REQUIRED")
    for key,sha,node in (("win1",WIN1,"Chris"),("win2",WIN2,"Chris"),
                         ("mac",MAC_LOCAL,"MacMiniOffice.local")):
        c=contenders.get(key) or {}
        need(c.get("local_commit_sha")==sha
             and c.get("parent_commit_sha")==MAIN
             and c.get("host")==node
             and c.get("repo_isolated") is True
             and c.get("synthetic_lab_only") is True
             and c.get("local_commit_never_in_main") is True
             and exact_sha(c.get("local_commit_sha")),
             "CONTENDER_ORIGINAL_PARENT_OR_HOST_CHANGED_"+key)
    attempt=row.get("remote_writes") or {}
    need(attempt.get("from_physical_host")=="Chris"
         and attempt.get("two_distinct_windows_processes_started_concurrently")
            is True
         and attempt.get("target_ref")==REF
         and attempt.get("expected_old_remote_sha")==MAIN
         and attempt.get("cli_lease_argument")==
            "--force-with-lease="+REF+":"+MAIN
         and attempt.get("unqualified_force_used") is False
         and attempt.get("write_main_attempted") is False
         and attempt.get("win1_written_commit")==WIN1
         and attempt.get("win1_status")=="ACCEPTED"
         and attempt.get("win1_exit_code") is None
         and attempt.get("initial_push_exit_codes_not_logged") is True
         and attempt.get("win2_written_commit")==WIN2
         and attempt.get("win2_status")=="REJECTED_STALE_INFO"
         and attempt.get("win2_exit_code") is None
         and attempt.get("original_win2_git_error_observed") is True
         and attempt.get("win2_repeated_original_expected_main") is True
         and attempt.get("win2_second_status")=="REJECTED_STALE_INFO"
         and attempt.get("win2_second_exit_code")==1
         and attempt.get("both_windows_pushes_succeeded") is False,
         "TWO_WIN_PUSH_RACE_FALSE_ACCEPT_OR_BLIND_FORCE")
    after = row.get("readbacks_and_cleanup") or {}
    need(after.get("winner_sha_after_race_on_Chris")==WIN1
         and after.get("winner_sha_after_race_on_MacMiniOffice_local")==WIN1
         and after.get("loser_ref_never_won") is True
         and after.get("main_sha_during_race_on_Chris")==MAIN
         and after.get("main_sha_during_race_on_MacMiniOffice_local")==MAIN
         and after.get("delete_expected_old_sha")==WIN1
         and after.get("delete_cli_lease_argument")==
            "--force-with-lease="+REF+":"+WIN1
         and after.get("delete_target_ref")==REF
         and after.get("delete_return_code")==0
         and after.get("scratch_ref_absent_final_on_Chris") is True
         and after.get("scratch_ref_absent_final_on_MacMiniOffice_local") is True
         and after.get("final_main_sha_on_Chris")==MAIN
         and after.get("final_main_sha_on_MacMiniOffice_local")==MAIN
         and after.get("non_lab_remote_refs_modified") is False,
         "REMOTE_REF_MAY_STILL_EXIST_OR_MAIN_CHANGED")
    mac = row.get("mac_git_writer_capability") or {}
    need(mac.get("can_read_remote_refs") is True
         and mac.get("can_push_from_native_mac_git") is False
         and mac.get("dry_run_authenticated") is False
         and mac.get("observed_https_push_failure")==
             "could not read Username for https://github.com"
         and mac.get("gh_authenticated") is False
         and mac.get("ssh_authenticated") is False
         and mac.get("credentials_copied_or_created") is False
         and mac.get("participated_in_remote_write_race") is False,
         "FALSE_TWO_PHYSICAL_HOST_AUTHENTICATED_WRITERS")
    limits=row.get("limits") or {}
    required_false=(
        "two_physical_host_writers_proven",
        "canonical_fleet_lease_minted",
        "lease_renew_revoke_verified",
        "monotonic_generation_from_provider_proven",
        "stale_fence_checked_before_arbitrary_effects",
        "crash_rejoin_recovery_proven",
        "original_unknown_task_retried",
        "model_or_aider_invoked_for_this_lab",
        "model_generated_code_git_written_in_this_lab",
        "automatic_agent_pr_authored",
        "production_writer_authority",
        "main_branch_modified_by_lab",
        "customer_social_printer_effects",
        "new_scheduler_or_daemon",
        "remote_lab_ref_left_open",
        "unqualified_force_push_used",
        "real_two_host_concurrent_git_writer_proven",
    )
    for flag in required_false:
        need(limits.get(flag) is False, "UNPROVEN_CAPABILITY_"+flag)
    need(limits.get("real_github_ref_cas_observed") is True
         and limits.get("two_isolated_git_clients_same_windows_host") is True
         and limits.get("witness_is_manual_terminal_observation_not_signed")
            is True
         and limits.get("paid_model_or_api_cost_usd")==0
         and limits.get("verification_model_calls")==0
         and type(limits.get("verification_model_calls")) is int,
         "CAS_SCOPE_FALSE_OR_PAID_CALLS")
    return {
        "status":"PASS_OFFLINE_HISTORICAL_ONE_HOST_REAL_GITHUB_REF_CAS",
        "distinct_contenders":2,
        "accepted_remote_git_writers":1,
        "stale_denied_remote_git_writers":1,
        "stale_original_expected_ref_recheck_denied":True,
        "scratch_git_branch_deleted_and_read_back_on_both_hosts":True,
        "two_physical_host_writers_proven":False,
        "provider_lease_proven":False,
        "model_calls":0,
        "production_writes":0
    }


def selftest(value):
    validate(value)
    done=["original_structural_receipt_only"]
    negatives=[
        ("wrong_ref",lambda q:q["original_remote_state"].update(scratch_ref="refs/heads/main")),
        ("preexisting_ref",lambda q:q["original_remote_state"].update(initial_scratch_ref=MAIN)),
        ("wrong_base",lambda q:q["original_remote_state"].update(initial_origin_main="0"*40)),
        ("wrong_host",lambda q:q["contenders"]["win2"].update(host="MacMiniOffice.local")),
        ("same_commit",lambda q:q["contenders"]["win2"].update(local_commit_sha=WIN1)),
        ("wrong_parent",lambda q:q["contenders"]["win1"].update(parent_commit_sha="0"*40)),
        ("false_mac_writer",lambda q:q["mac_git_writer_capability"].update(can_push_from_native_mac_git=True)),
        ("mac_joined_race",lambda q:q["mac_git_writer_capability"].update(participated_in_remote_write_race=True)),
        ("unauthenticated_mac_claim",lambda q:q["mac_git_writer_capability"].update(gh_authenticated=True)),
        ("two_remote_winners",lambda q:q["remote_writes"].update(both_windows_pushes_succeeded=True)),
        ("stale_accepted",lambda q:q["remote_writes"].update(win2_status="ACCEPTED")),
        ("lose_expected_sha",lambda q:q["remote_writes"].update(expected_old_remote_sha=WIN1)),
        ("unqualified_force",lambda q:q["remote_writes"].update(unqualified_force_used=True)),
        ("fabricated_win1_exit",lambda q:q["remote_writes"].update(win1_exit_code=0)),
        ("cleanup_wrong_lease",lambda q:q["readbacks_and_cleanup"].update(delete_expected_old_sha=MAIN)),
        ("missing_cleanup",lambda q:q["readbacks_and_cleanup"].update(scratch_ref_absent_final_on_Chris=False)),
        ("false_mac_readback",lambda q:q["readbacks_and_cleanup"].update(winner_sha_after_race_on_MacMiniOffice_local=WIN2)),
        ("main_modified",lambda q:q["readbacks_and_cleanup"].update(final_main_sha_on_Chris=WIN1)),
        ("false_distributed_lease",lambda q:q["limits"].update(canonical_fleet_lease_minted=True)),
        ("false_production",lambda q:q["limits"].update(production_writer_authority=True)),
        ("false_model",lambda q:q["limits"].update(model_or_aider_invoked_for_this_lab=True)),
        ("extra_scheduler",lambda q:q["limits"].update(new_scheduler_or_daemon=True)),
        ("paid_cost",lambda q:q["limits"].update(paid_model_or_api_cost_usd=1)),
        ("hidden_ref",lambda q:q["limits"].update(remote_lab_ref_left_open=True)),
    ]
    for name,mutation in negatives:
        fake=copy.deepcopy(value)
        mutation(fake)
        try:
            validate(fake)
        except Refused:
            done.append(name+"_DENIED")
        else:
            raise AssertionError("FORGED_CAS_EVIDENCE_ACCEPTED_"+name)
    need(len(done)==25,"GIT_CAS_ADVERSARIAL_TEST_COUNT_DRIFT")
    return {"status":"PASS_OFFLINE",
            "tests":len(done),
            "model_calls":0,
            "git_writes_by_selftest":0,
            "unqualified_force":False,
            "distributed_lease_proven":False,
            "production_authority":False}


def historical():
    path=Path(__file__).resolve().parent.parent / (
        "docs/implementation/office-v2/phase2/"
        "p0-two-client-real-github-ref-cas-2026-10-10.json"
    )
    need(path.is_file() and not path.is_symlink() and
         path.stat().st_size<18000,"HISTORICAL_GIT_CAS_RECEIPT_NOT_FOUND")
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError) as exc:
        raise Refused("HISTORICAL_RECEIPT_UNPARSABLE") from exc
    return data


def remote_readonly(repo_path):
    p=Path(repo_path)
    need(p.is_absolute() and p.is_dir() and (p/".git").is_dir()
         and not p.is_symlink() and "AgentEnvelopeLab" in p.parts
         and p.name=="repo","ONLY_ISOLATED_LAB_GIT_CLONE")
    def git(*args):
        try:
            p_=subprocess.run(
                ["git","-C",str(p),*args],
                capture_output=True,text=True,timeout=12)
        except (OSError,subprocess.TimeoutExpired) as exc:
            raise Refused("GIT_REMOTE_READ_UNAVAILABLE") from exc
        need(p_.returncode==0,"GIT_REMOTE_READ_REJECTED")
        return p_.stdout.strip()
    need(git("remote","get-url","origin")==ORIGIN,
         "GIT_REMOTE_TARGET_NOT_EXPECTED")
    current=git("ls-remote","origin",REF)
    need(current=="","REMOTE_SCRATCH_REF_NOT_CLEANED")
    main=git("ls-remote","origin","refs/heads/main")
    # This historical readback mode is valid only while main remains exactly
    # the tested SHA; future subsequent unrelated main movement should not
    # change the immutable historical evidence.
    need(main==MAIN+"\trefs/heads/main",
         "ORIGIN_MAIN_ALREADY_ADVANCED_READ_HISTORICAL_RECEIPT_INSTEAD")
    return {"status":"PASS_READ_ONLY_REMOTE_GIT_LAB_REF_ABSENT",
            "expected_main_sha":MAIN,
            "scratch_ref_absent":True,
            "model_calls":0,
            "git_writes":0,
            "fleet_lease":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("verify","selftest","readback"))
    p.add_argument("--repo",default=None)
    args=p.parse_args()
    if args.mode=="readback":
        need(args.repo is not None,"ISOLATED_LAB_REPO_REQUIRED")
        result=remote_readonly(args.repo)
    else:
        need(args.repo is None,"OFFLINE_MODE_DENIES_REPO_ARGUMENT")
        obj=historical()
        result=validate(obj) if args.mode=="verify" else selftest(obj)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    try:
        main()
    except (Refused,OSError,ValueError,TypeError,KeyError,AssertionError) as e:
        print(json.dumps({
            "status":"FAIL_CLOSED",
            "reason":str(e)[:160],
            "model_calls":0,
            "git_writes_by_verifier":0,
            "distributed_lease_proven":False,
            "production_authority":False
        },sort_keys=True))
        raise SystemExit(2)
