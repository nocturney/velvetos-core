#!/usr/bin/env python3
"""#612: independent read-only cross-host comparison of TWO historic coding successes.

No new model tasks, agent-generated PRs, provider leases or autonomous recovery.
Original run owners retain the only raw receipts; CI checks pinned repo evidence.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
P2=ROOT/"docs"/"implementation"/"office-v2"/"phase2"
WIN_NAME="p0-supervised-aider-windows-job-2026-10-09.json"
MAC_NAME="p0-two-fresh-guided-model-qa-2026-10-10.json"
PINS={
 WIN_NAME:"7f690fd1da3b8f0dad5b84dca93133e86077b70287192eecc5f1d12e84c0a3a8",
 MAC_NAME:"f032b75a5a16a1292d61390e3f47d53987aa7e7b3005309b5eef01dda0ef42d7",
}
SCHEMA="velvetos.office-v2.p0-cross-host-historical-qa-witness.v0"
WIN_TASK="p0-win-job-guard-gpt6-success-20261009-d"
MAC_TASK="p0-diverse-run-mac-merge-guided-20261010-a"
WIN_RECEIPT_SELFHASH="4424b020ead05e6d30bd4467f105792f98fc37f0aca039144f0413432a5eec02"
MAC_RECEIPT_RAW="f6dac1286bb1fad2ddb525ecf51d3fd86a9149d2a5cc8464f05c5569350cedda"

class Refused(Exception): pass
def require(ok,code):
    if not ok: raise Refused(code)

def loaded(name):
    p=P2/name
    b=p.read_bytes()
    require(hashlib.sha256(b).hexdigest()==PINS[name],"PINNED_SOURCE_EVIDENCE_CHANGED")
    return json.loads(b.decode("utf-8"))

def verify(win,mac):
    require(win.get("schema")=="vf.office-v2.p0-supervised-real-aider-win-job-two-modes.v0",
            "WINDOWS_SOURCE_SCHEMA")
    require(mac.get("schema")=="velvetos.office-v2.p0-two-fresh-guided-model-qa-results.v0",
            "MAC_SOURCE_SCHEMA")
    w=win["samples"]["success"]
    failed_win=win["samples"]["interrupt"]
    m=mac["attempts"][0]
    failed_mac=mac["attempts"][1]
    we=w["envelope"];wr=w["worker_receipt"];wj=w["job"];r=w["readback"]
    qa=wr["independent_qa"];mq=m["independent_qa"]
    require(we["host"]=="Chris" and mac["source"]["host"]=="MacMiniOffice.local"
            and we["host"]!=mac["source"]["host"],"NOT_TWO_PHYSICAL_HOSTS")
    require(we["task_id"]==wr["task_id"]==wj["task_id"]==WIN_TASK
            and m["task_id"]==MAC_TASK and WIN_TASK!=MAC_TASK,
            "TASK_LINEAGE_NOT_TWO_DISTINCT")
    require(we["base_sha"]==wr["base_sha"] and
            we["base_sha"]!=m["base_sha"],"GIT_BASE_NOT_DISTINCT")
    require(we["branch"]==wr["branch"] and
            we["branch"]!=m["branch"],"GIT_BRANCH_NOT_DISTINCT")
    require(we["executor"]["model"]==wr["model"]=="qwen3.5:9b"
            and mac["source"]["model"]=="qwen3.5:4b",
            "MODEL_HOST_PROVENANCE")
    require(wj["state"]=="SUCCEEDED_LOCAL_MODEL_QA_VERIFIED" and
            wr["state"]=="SUCCEEDED" and wr["exit_code"]==0 and
            m["result"]=="SUCCEEDED" and m["original_model_worker_verify"]=="PASS",
            "REAL_WORKER_SUCCESS_REQUIRED")
    require(r["separate_worker_verify_pass"] is True and
            r["source_change_only_slug_py"] is True and
            qa["pass"] is True and qa["unit_3_verified"] is True and
            qa["hidden_12_verified"] is True and
            qa["unit_exit"]==qa["hidden_exit"]==0 and
            qa["replay_changed_paths"]==["slug.py"],
            "WINDOWS_INDEPENDENT_QA_NOT_PASS")
    require(mq["pass"] is True and mq["unit_3_verified"] is True and
            mq["hidden_12_verified"] is True and
            mq["unit_exit"]==mq["hidden_exit"]==0 and
            mq["changed_paths"]==["windows_merge.py"] and
            m["target"]=="windows_merge.py" and
            m["fixture"]=="merge-windows-v1",
            "MAC_INDEPENDENT_QA_NOT_PASS")
    require(qa["replay_changed_paths"]!=mq["changed_paths"],
            "NOT_TWO_CODE_FAMILIES")
    require(wr["receipt_sha256"]==wj["worker_receipt_sha256"]==
            WIN_RECEIPT_SELFHASH and
            m["receipt_raw_sha256"]==MAC_RECEIPT_RAW and
            isinstance(m["receipt_selfhash"],str) and len(m["receipt_selfhash"])==64,
            "RECEIPT_INTEGRITY_CLAIMS_CHANGED")
    require(wr["model_invocations_min"]>=1 and m["model_invocations_min"]>=1 and
            wr["additional_api_spend_usd"]==m["additional_api_spend_usd"]==0 and
            wr["production_authority"]=="NONE" and
            m["production_authority"] is False,
            "MODEL_COST_OR_PRODUCTION_AUTHORITY")
    require(failed_win["job"]["running_journal_persists"] is True and
            failed_win["job"]["original_task_retry_allowed"] is False and
            failed_mac["result"]=="FAILED_INDEPENDENT_QA_NO_SUCCESS" and
            failed_mac["original_journal_preserved"] is True and
            failed_mac["success_receipt_absent"] is True and
            failed_mac["original_attempt_retried"] is False,
            "HISTORICAL_FAILED_ATTEMPTS_MUST_STAY_UNKNOWN")
    return {
        "schema":SCHEMA,
        "status":"PASS_TWO_HOST_DISTINCT_HISTORICAL_CODING_QA_ONLY",
        "hosts":["Chris","MacMiniOffice.local"],
        "tasks":[WIN_TASK,MAC_TASK],
        "code_families":["slug.py","windows_merge.py"],
        "historic_successes_with_independent_qa":2,
        "current_new_model_invocations":0,
        "original_receipt_bytes_checked_by_CI":False,
        "simultaneous_cross_host_execution_proven":False,
        "distributed_lease_proven":False,
        "agent_authored_pr_or_merge_proven":False,
        "autonomous_recovery_proven":False,
        "historical_failed_attempts_retried":False,
        "production_effects":0
    }

def selftest():
    win=loaded(WIN_NAME);mac=loaded(MAC_NAME)
    good=verify(win,mac)
    require(good["historic_successes_with_independent_qa"]==2 and
            good["agent_authored_pr_or_merge_proven"] is False,
            "FALSE_HISTORICAL_PROMOTION")
    checks=["two_owners_two_tasks_different_code_and_verified_qa"]
    cases=[
     ("wrong_win_host","win",("samples","success","envelope","host"),"MacMiniOffice.local","NOT_TWO_PHYSICAL_HOSTS"),
     ("same_win_task","win",("samples","success","envelope","task_id"),MAC_TASK,"TASK_LINEAGE_NOT_TWO_DISTINCT"),
     ("same_mac_task","mac",("attempts",0,"task_id"),WIN_TASK,"TASK_LINEAGE_NOT_TWO_DISTINCT"),
     ("win_receipt_foreign_task","win",("samples","success","worker_receipt","task_id"),"alien","TASK_LINEAGE_NOT_TWO_DISTINCT"),
     ("same_base","mac",("attempts",0,"base_sha"),win["samples"]["success"]["envelope"]["base_sha"],"GIT_BASE_NOT_DISTINCT"),
     ("same_branch","mac",("attempts",0,"branch"),win["samples"]["success"]["envelope"]["branch"],"GIT_BRANCH_NOT_DISTINCT"),
     ("model_changed_win","win",("samples","success","worker_receipt","model"),"codex-cli","MODEL_HOST_PROVENANCE"),
     ("model_changed_mac","mac",("source","model"),"api-cloud","MODEL_HOST_PROVENANCE"),
     ("win_false_success","win",("samples","success","worker_receipt","state"),"UNKNOWN","REAL_WORKER_SUCCESS_REQUIRED"),
     ("mac_false_success","mac",("attempts",0,"result"),"FAILED","REAL_WORKER_SUCCESS_REQUIRED"),
     ("mac_missing_worker_verify","mac",("attempts",0,"original_model_worker_verify"),None,"REAL_WORKER_SUCCESS_REQUIRED"),
     ("win_missing_worker_verify","win",("samples","success","readback","separate_worker_verify_pass"),False,"WINDOWS_INDEPENDENT_QA_NOT_PASS"),
     ("win_false_qa","win",("samples","success","worker_receipt","independent_qa","pass"),False,"WINDOWS_INDEPENDENT_QA_NOT_PASS"),
     ("win_unit_failure","win",("samples","success","worker_receipt","independent_qa","unit_exit"),1,"WINDOWS_INDEPENDENT_QA_NOT_PASS"),
     ("win_hidden_false","win",("samples","success","worker_receipt","independent_qa","hidden_12_verified"),False,"WINDOWS_INDEPENDENT_QA_NOT_PASS"),
     ("win_changed_file","win",("samples","success","worker_receipt","independent_qa","replay_changed_paths"),["other.py"],"WINDOWS_INDEPENDENT_QA_NOT_PASS"),
     ("mac_false_qa","mac",("attempts",0,"independent_qa","pass"),False,"MAC_INDEPENDENT_QA_NOT_PASS"),
     ("mac_hidden_false","mac",("attempts",0,"independent_qa","hidden_12_verified"),False,"MAC_INDEPENDENT_QA_NOT_PASS"),
     ("mac_wrong_file","mac",("attempts",0,"independent_qa","changed_paths"),["slug.py"],"MAC_INDEPENDENT_QA_NOT_PASS"),
     ("win_forged_receipt","win",("samples","success","worker_receipt","receipt_sha256"),"0"*64,"RECEIPT_INTEGRITY_CLAIMS_CHANGED"),
     ("mac_forged_receipt","mac",("attempts",0,"receipt_raw_sha256"),"0"*64,"RECEIPT_INTEGRITY_CLAIMS_CHANGED"),
     ("win_calls_zero","win",("samples","success","worker_receipt","model_invocations_min"),0,"MODEL_COST_OR_PRODUCTION_AUTHORITY"),
     ("mac_calls_zero","mac",("attempts",0,"model_invocations_min"),0,"MODEL_COST_OR_PRODUCTION_AUTHORITY"),
     ("win_paid","win",("samples","success","worker_receipt","additional_api_spend_usd"),2,"MODEL_COST_OR_PRODUCTION_AUTHORITY"),
     ("mac_paid","mac",("attempts",0,"additional_api_spend_usd"),1,"MODEL_COST_OR_PRODUCTION_AUTHORITY"),
     ("win_prod","win",("samples","success","worker_receipt","production_authority"),"PRODUCTION","MODEL_COST_OR_PRODUCTION_AUTHORITY"),
     ("mac_prod","mac",("attempts",0,"production_authority"),True,"MODEL_COST_OR_PRODUCTION_AUTHORITY"),
     ("retry_win_unknown","win",("samples","interrupt","job","original_task_retry_allowed"),True,"HISTORICAL_FAILED_ATTEMPTS_MUST_STAY_UNKNOWN"),
     ("retry_mac_failed","mac",("attempts",1,"original_attempt_retried"),True,"HISTORICAL_FAILED_ATTEMPTS_MUST_STAY_UNKNOWN"),
     ("mac_false_green_failed","mac",("attempts",1,"success_receipt_absent"),False,"HISTORICAL_FAILED_ATTEMPTS_MUST_STAY_UNKNOWN"),
    ]
    for name,side,path,value,code in cases:
        w=copy.deepcopy(win);m=copy.deepcopy(mac)
        obj=w if side=="win" else m
        for key in path[:-1]:
            obj=obj[key]
        obj[path[-1]]=value
        try:
            verify(w,m)
        except Refused as err:
            require(str(err)==code,"WRONG_REFUSAL_"+name+":"+str(err))
            checks.append(name)
        else:
            raise AssertionError("UNSAFE_FALSE_CROSS_HOST_SUCCESS:"+name)
    require(len(checks)==31,"OFFLINE_TESTS_MISSING:"+str(len(checks)))
    return {"status":"PASS_OFFLINE","tests":len(checks),"cases":checks,
            "model_invocations":0,"production_effects":0,"no_retries":True}

def validate_existing():
    for args,expected in (
        (["scripts/vf_office_v2_p0_supervised_aider_evidence.py","--evidence",str(P2/WIN_NAME)],
         "PASS_SCOPED_WINDOWS_SUPERVISED_AIDER_LAB"),
        (["scripts/vf_office_v2_p0_guided_qa_evidence.py","verify","--evidence",str(P2/MAC_NAME)],
         "PASS_HISTORICAL_METADATA_ONLY")
    ):
        result=subprocess.run([sys.executable,str(ROOT/args[0]),*args[1:]],
                              cwd=ROOT,capture_output=True,text=True,timeout=30)
        require(result.returncode==0,"CANONICAL_SOURCE_VALIDATOR_REJECTED")
        try: out=json.loads(result.stdout)
        except ValueError: raise Refused("CANONICAL_SOURCE_VERIFIER_NOT_JSON")
        require(out.get("status")==expected,"CANONICAL_SOURCE_VERDICT_CHANGED")
    return verify(loaded(WIN_NAME),loaded(MAC_NAME))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("selftest","verify"))
    a=p.parse_args()
    try:
        v=selftest() if a.command=="selftest" else validate_existing()
        print(json.dumps(v,sort_keys=True))
        return 0
    except (Refused,KeyError,IndexError,ValueError,OSError) as exc:
        print(json.dumps({"status":"REFUSED","reason":str(exc)},sort_keys=True))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
