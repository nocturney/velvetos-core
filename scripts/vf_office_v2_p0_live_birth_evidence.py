#!/usr/bin/env python3
"""#612: independently verify sanitized actual Aider OS-birth LAB evidence.

Pure offline. Reads known source and evidence; never invokes an LLM, process
table, scheduler, worker, shell, paid API, or customer-effect action.
Host-local full receipts/logs remain external; SHA references are not signatures.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path

SCHEMA="vf.office-v2.p0-real-aider-kernel-birth-worker-lab.v1"
OBS_SCHEMA="velvetos.office-v2.p0-process-birth-readback.v1"
EXPECTED={
    "p0-mac-birth-live-20261009-a":("MacMiniOffice.local","qwen3.5:4b"),
    "p0-win-birth-live-20261009-a":("Chris","qwen3.5:9b"),
    "p0-mac-birth-afterloss-20261009-c":("MacMiniOffice.local","qwen3.5:4b"),
}
COMPLETE="SAME_KERNEL_INSTANCE_AT_SNAPSHOT"
ABSENT="HISTORICAL_PID_ABSENT"


def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,
                                     separators=(",",":")).encode()).hexdigest()


def check(ok,code):
    if not ok:
        raise AssertionError(code)


def sha(value):
    return (isinstance(value,str) and len(value)==64 and
            all(c in "0123456789abcdef" for c in value))


def verify_observation(obs,expected_task,expected_pin,expected_env,stage):
    check(isinstance(obs,dict) and obs.get("schema")==OBS_SCHEMA,"OBS_SCHEMA")
    check(obs.get("task_id")==expected_task and obs.get("host")=="MacMiniOffice.local",
          "OBS_TASK_OR_HOST")
    check(obs.get("pin_sha256")==expected_pin and
          obs.get("envelope_sha256")==expected_env,"OBS_BOUND_PINS")
    raw={k:v for k,v in obs.items() if k!="observation_sha256"}
    check(obs.get("observation_sha256")==digest(raw),"OBS_HASH_DRIFT")
    for field,expected in (
        ("all_orphans_excluded",False),("automatic_requeue_allowed",False),
        ("historical_journal_stays_unknown",True),("original_retry_permitted",False),
        ("fleet_scheduler_authority",False),("new_task_authorized",False),
        ("production_writer",False),("read_only",True),("model_invocations",0),
        ("kernel_birth_pin_available",True),("live_process_claim_only_at_snapshot",True),
    ):
        check(obs.get(field)==expected and type(obs.get(field)) is type(expected),
              "OBS_FALSE_AUTHORITY_"+field)
    processes=obs.get("historical_processes") or {}
    group=obs.get("group_observation") or {}
    if stage=="before":
        check(processes=={"aider":COMPLETE,"worker":COMPLETE},"NO_LIVE_AIDER_BIRTH_READBACK")
        check(group.get("status")=="POSSIBLE_GROUP_MEMBERS" and
              type(group.get("candidate_count")) is int and
              group.get("candidate_count")>=1,"NO_PINNED_AIDER_GROUP_DURING")
    else:
        check(processes=={"aider":ABSENT,"worker":ABSENT},"HISTORICAL_PID_NOT_ABSENT")
        check(group.get("status")=="NO_GROUP_MEMBERS_SEEN" and
              group.get("candidate_count")==0,"POTENTIAL_SURVIVORS_NOT_RECONCILED")
    started=datetime.fromisoformat(obs["observed_at_utc"].replace("Z","+00:00"))
    check(started.tzinfo is not None,"UNZONED_OBSERVATION")
    return started


def assess(data,worker_path):
    check(isinstance(data,dict) and data.get("schema")==SCHEMA,"EVIDENCE_SCHEMA")
    check(data.get("authority")=="LAB_SYNTHETIC_NO_BUSINESS_EFFECT","EVIDENCE_AUTHORITY")
    check(data.get("worker_git_commit")=="030eccbe98e5165115faa37253ad82208fc59614",
          "WORKER_REVISION_NOT_THE_TESTED_HEAD")
    worker_hash=hashlib.sha256(Path(worker_path).read_bytes()).hexdigest()
    check(data.get("worker_source_sha256")==worker_hash,"TESTED_WORKER_SOURCE_DRIFT")
    runs=data.get("model_runs")
    check(isinstance(runs,list) and len(runs)==3,"MISSING_REAL_MODEL_RUNS")
    got_tasks=set()
    bases=set()
    for row in runs:
        check(isinstance(row,dict),"MODEL_RECEIPT_ROW")
        task=row.get("task_id")
        check(task in EXPECTED and task not in got_tasks,"TASK_DUPLICATED_OR_UNKNOWN")
        got_tasks.add(task)
        host,model=EXPECTED[task]
        check(row.get("host")==host and row.get("model")==model,
              "SOURCE_HOST_MODEL_DRIFT")
        check(row.get("state")=="SUCCEEDED" and
              row.get("independent_separate_process_verify")=="PASS",
              "FALSE_MODEL_WORKER_SUCCESS")
        check(row.get("model_invocations_min")==1 and
              row.get("exact_model_calls") is None,
              "REAL_INFERENCE_NOT_PROVEN_OR_EXAGGERATED")
        check(row.get("qa_visible3") is True and row.get("qa_hidden12") is True and
              row.get("qa_fresh_clone") is True,"MODEL_INDEPENDENT_QA_MISSING")
        for field in ("receipt_sha256","kernel_pin_sha256",
                      "kernel_pin_file_sha256","artifact_sha256"):
            check(sha(row.get(field)),"NO_"+field.upper())
        check(row.get("source_git_commit")==data["worker_git_commit"],
              "EXECUTED_REPO_SHA_MISMATCH")
        check(type(row.get("elapsed_seconds")) in (int,float) and
              1 < row["elapsed_seconds"] < 200,"MODEL_RUNTIME_NOT_BOUNDED")
        base=row.get("base_sha")
        check(isinstance(base,str) and len(base)==40 and base not in bases,
              "REUSED_OR_INVALID_GIT_FIXTURE")
        bases.add(base)
    check(got_tasks==set(EXPECTED),"MISSING_ONE_TASK")
    killed=data.get("interrupted") or {}
    task=killed.get("task_id")
    check(task=="p0-mac-birth-kill-20261009-b" and
          killed.get("host")=="MacMiniOffice.local" and
          killed.get("model")=="qwen3.5:4b","FORCED_KILL_SCOPE")
    check(task not in got_tasks,"FAILED_TASK_MISTAKEN_FOR_SUCCESS")
    for key in ("envelope_sha256","pin_sha256","pin_file_sha256",
                "old_journal_file_sha256"):
        check(sha(killed.get(key)),"KILLED_PIN_OR_JOURNAL_MISSING")
    before=verify_observation(killed.get("live_observation"),task,
                              killed["pin_sha256"],killed["envelope_sha256"],"before")
    after=verify_observation(killed.get("post_interruption_observation"),task,
                             killed["pin_sha256"],killed["envelope_sha256"],"after")
    check(before<after,"INVALID_KILL_OBSERVATION_ORDER")
    for field in ("pinned_worker_stopped","pinned_aider_stopped",
                  "original_running_journal_still_present","original_final_receipt_absent",
                  "old_journal_unchanged_after_new_task"):
        check(killed.get(field) is True,"KILL_PROOF_MISSING_"+field)
    check(killed.get("same_task_retry_rejected")=="DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY",
          "REPLAY_NOT_EXPLICITLY_DENIED")
    check(killed.get("auto_restart_permitted") is False and
          killed.get("all_orphans_excluded") is False,"UNPROVEN_ORPHAN_CLEANUP")
    check(data.get("additional_api_spend_usd")==0 and
          data.get("codex_cli_used") is False and
          data.get("production_writer_added") is False and
          data.get("scheduler_proven") is False and
          data.get("automatic_cross_host_failover_proven") is False,
          "EXAGGERATED_COST_AUTHORITY_OR_RECOVERY")
    return True


def test_mutation_guards(data,worker_path):
    checks=[]
    def negative(name,fn,reseal=False):
        altered=copy.deepcopy(data)
        fn(altered)
        if reseal:
            for which in ("live_observation","post_interruption_observation"):
                o=altered["interrupted"][which]
                o["observation_sha256"]=digest({k:v for k,v in o.items()
                                                 if k!="observation_sha256"})
        try:
            assess(altered,worker_path)
        except (AssertionError,KeyError,TypeError,ValueError):
            checks.append(name)
        else:
            raise AssertionError("FALSE_EVIDENCE_ACCEPTED:"+name)
    negative("fake_model_success",lambda x:x["model_runs"][0].update(state="UNKNOWN_OUTCOME"))
    negative("fake_pin_missing",lambda x:x["model_runs"][1].update(kernel_pin_sha256=None))
    negative("fake_model_calls",lambda x:x["model_runs"][2].update(exact_model_calls=7))
    negative("fake_independent_qa",lambda x:x["model_runs"][0].update(qa_hidden12=False))
    negative("false_auto_restart",lambda x:x["interrupted"].update(auto_restart_permitted=True))
    negative("forged_orphan_completion",lambda x:x["interrupted"].update(all_orphans_excluded=True))
    negative("faked_post_pid_match",lambda x:x["interrupted"]["post_interruption_observation"]["historical_processes"].update(aider=COMPLETE),True)
    negative("broken_observation_hash",lambda x:x["interrupted"]["live_observation"].update(observation_sha256="0"*64))
    negative("forged_observation_authority",lambda x:x["interrupted"]["live_observation"].update(original_retry_permitted=True),True)
    negative("host_model_swap",lambda x:x["model_runs"][1].update(host="MacMiniOffice.local"))
    negative("false_fleet_claim",lambda x:x.update(scheduler_proven=True))
    check(len(checks)==11,"NEGATIVE_CASES_MISSING")
    return checks


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",required=True)
    p.add_argument("--worker-source",required=True)
    args=p.parse_args()
    value=json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    assess(value,args.worker_source)
    checks=test_mutation_guards(value,args.worker_source)
    print(json.dumps({"status":"PASS_SCOPED_LAB",
        "actual_local_model_success_receipt_refs":3,
        "pinned_live_model_killed_and_unknown_preserved":True,
        "explicit_new_local_attempt_verified":True,
        "reissued_old_task":False,"original_retry_permitted":False,
        "negative_controls_rejected":len(checks),
        "test_cases":checks,"model_invocations_during_verification":0,
        "auto_cross_host_failover_proven":False,"production_promotion_allowed":False,
        "worker_source_sha256":value["worker_source_sha256"]},sort_keys=True))


if __name__=="__main__":
    try:main()
    except (AssertionError,ValueError,TypeError,KeyError,OSError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:200],
                          "original_retry_permitted":False}))
        raise SystemExit(2)
