#!/usr/bin/env python3
"""Pure offline independent verifier for actual Mac + Windows process-birth LAB.

NEVER launches models, queries processes, or confers retry/scheduling authority.
A SHA-256 self-seal detects drift, not forged/re-sealed evidence or OS attestation.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path

SCHEMA="vf.office-v2.p0-kernel-birth-identity-dual-host-lab.v1"
RECEIPT="vf.office-v2.p0-native-process-pair-probe.v1"
BACKENDS={
    "mac":("MacMiniOffice.local","PSUTIL_OS_CREATE_TIME"),
    "windows":("Chris","WINDOWS_CIM_CREATION_DATE"),
}
IDENTICAL="SAME_KERNEL_INSTANCE_AT_SNAPSHOT"
MISSING={"HISTORICAL_PID_ABSENT","PID_REUSED_DIFFERENT_BIRTH"}


def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,
                                     separators=(",",":")).encode()).hexdigest()


def insist(condition,reason):
    if not condition:
        raise AssertionError(reason)


def check_receipt(which,rec,source_sha):
    host,backend=BACKENDS[which]
    insist(isinstance(rec,dict),"EVIDENCE_RECEIPT_NOT_OBJECT")
    r={k:v for k,v in rec.items() if k!="receipt_sha256"}
    insist(rec.get("receipt_sha256")==digest(r),"EVIDENCE_RECEIPT_HASH_DRIFT")
    insist(rec.get("schema")==RECEIPT and rec.get("host")==host and
           rec.get("os_process_birth_backend")==backend,"EVIDENCE_IDENTITY_DRIFT")
    insist(rec.get("source_sha256")==source_sha,"EXECUTED_SOURCE_HASH_DRIFT")
    insist(rec.get("source_of_test_processes")=="TWO_SYNTHETIC_PYTHON_PROCESSES_NOT_AIDER",
           "FALSE_REAL_AIDER_CLAIM")
    insist(rec.get("live_worker")==IDENTICAL and rec.get("live_child")==IDENTICAL,
           "BIRTH_OR_PARENT_NOT_VERIFIED")
    insist(rec.get("after_exit_worker") in MISSING and
           rec.get("after_exit_child") in MISSING,"POST_EXIT_IDENTITY_MISMATCH")
    insist(rec.get("historical_journal_preserved") is True and
           rec.get("no_final_receipt") is True,"UNKNOWN_JOURNAL_NOT_PRESERVED")
    insist(rec.get("model_invocations")==0 and rec.get("business_effects")==0 and
           rec.get("no_process_signals_or_force_stop") is True,"UNAPPROVED_EFFECT_CLAIM")
    insist(rec.get("safe_to_retry_old") is False and
           rec.get("automatic_failover_proven") is False and
           rec.get("all_orphan_descendants_excluded") is False,
           "FALSE_RETRY_OR_ORPHAN_COMPLETENESS_CLAIM")
    insist(isinstance(rec.get("pin_sha256"),str) and len(rec["pin_sha256"])==64,
           "PIN_HASH_MISSING")
    insist(type(rec.get("elapsed_seconds")) in (int,float) and
           0 < rec["elapsed_seconds"] < 120,"EXPERIMENT_DURATION_INVALID")
    first=rec.get("group_during") or {}
    last=rec.get("group_after") or {}
    if which=="mac":
        insist(first.get("status")=="POSSIBLE_GROUP_MEMBERS" and
               type(first.get("candidate_count")) is int and
               first["candidate_count"]>=1,"MAC_PROCESS_GROUP_NOT_OBSERVED")
        insist(last.get("status")=="NO_GROUP_MEMBERS_SEEN" and
               last.get("candidate_count")==0,"MAC_GROUP_DID_NOT_CLEAR")
    else:
        insist(first.get("status")=="NO_WINDOWS_JOB_OBJECT_IDENTITY" and
               last.get("status")=="NO_WINDOWS_JOB_OBJECT_IDENTITY" and
               first.get("candidate_count") is None and
               last.get("candidate_count") is None,"WINDOWS_JOB_OBJECT_FABRICATED")


def assess(data,source_path):
    insist(isinstance(data,dict) and data.get("schema")==SCHEMA,"BUNDLE_SCHEMA")
    insist(data.get("authority")=="NO_EFFECT_LAB" and
           data.get("automatic_recovery_proven") is False and
           data.get("all_orphans_excluded") is False,"BUNDLE_AUTHORITY")
    src=hashlib.sha256(Path(source_path).read_bytes()).hexdigest()
    insist(data.get("source_sha256")==src,"SOURCE_BYTES_MISMATCH")
    receipts=data.get("trials")
    insist(isinstance(receipts,dict) and set(receipts)==set(BACKENDS),
           "DUAL_HOST_TRIALS_REQUIRED")
    for key in BACKENDS:
        check_receipt(key,receipts[key],src)
    return True


def negative_controls(data,source_path):
    cases=[]
    def trial(name,mutator,reseal=True):
        clone=copy.deepcopy(data)
        mutator(clone)
        if reseal:
            for item in clone.get("trials",{}).values():
                item["receipt_sha256"]=digest({k:v for k,v in item.items() if k!="receipt_sha256"})
        try:
            assess(clone,source_path)
        except (AssertionError,KeyError,ValueError):
            cases.append(name)
        else:
            raise AssertionError("RESEALED_FALSE_EVIDENCE_ACCEPTED:"+name)
    trial("broken_seal",lambda x:x["trials"]["mac"].update(receipt_sha256="0"*64),False)
    trial("source_drift",lambda x:x.update(source_sha256="f"*64))
    trial("falsely_authorized_retry",lambda x:x["trials"]["mac"].update(safe_to_retry_old=True))
    trial("falsely_complete_orphan_scan",lambda x:x["trials"]["windows"].update(all_orphan_descendants_excluded=True))
    trial("false_windows_job",lambda x:x["trials"]["windows"]["group_during"].update(status="POSSIBLE_GROUP_MEMBERS"))
    trial("fake_mac_birth",lambda x:x["trials"]["mac"].update(live_child="HISTORICAL_PID_ABSENT"))
    trial("wrong_host",lambda x:x["trials"]["windows"].update(host="MacMiniOffice.local"))
    trial("duplicate_trial_removed",lambda x:x["trials"].pop("windows"))
    insist(len(cases)==8,"NEGATIVE_TEST_COUNT")
    return cases


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",required=True)
    p.add_argument("--source",required=True)
    args=p.parse_args()
    payload=json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    assess(payload,args.source)
    negatives=negative_controls(payload,args.source)
    print(json.dumps({"status":"PASS_SCOPED_LAB","native_dual_host_observations":2,
                      "negative_controls_rejected":len(negatives),
                      "control_names":negatives,
                      "source_sha256":payload["source_sha256"],
                      "processes_killed":0,"model_invocations":0,
                      "automatic_retry_permitted":False,
                      "all_orphans_excluded":False},sort_keys=True))


if __name__=="__main__":
    try:main()
    except (AssertionError,ValueError,TypeError,OSError,KeyError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:180],
                          "automatic_retry_permitted":False}))
        raise SystemExit(2)
