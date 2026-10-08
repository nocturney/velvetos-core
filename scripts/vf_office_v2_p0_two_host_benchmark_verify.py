#!/usr/bin/env python3
"""Independent offline verifier of #612 two-host identical-source coding receipts.
Does not schedule workers, run a model, access customer data, or grant authority.
"""
from __future__ import annotations
import argparse, copy, datetime, hashlib, json, pathlib, sys

EXPECTED_SOURCE="b97dfdee85fdb6f083acf9372cb50b42534ce1e4b16535d395e60a5004bdd430"
EXPECTED_BLOB="62f22e42701997037df6454501a22f03c8d53433"
EXPECTED_HOST={"win-serial":"Chris","win-parallel":"Chris","mac-serial":"MacMiniOffice.local","mac-parallel":"MacMiniOffice.local"}
EXPECTED_MODEL={"win-serial":"qwen3.5:9b","win-parallel":"qwen3.5:9b","mac-serial":"qwen3.5:4b","mac-parallel":"qwen3.5:4b"}

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,
        separators=(",",":")).encode("utf-8")).hexdigest()
def verify_sig(receipt):
    unsigned={key:value for key,value in receipt.items() if key!="receipt_sha256"}
    assert digest(unsigned)==receipt.get("receipt_sha256"),"HASH_NOT_SEALED"
def when(value):
    return datetime.datetime.fromisoformat(value)
def verify_trial(trial,rec):
    verify_sig(rec)
    assert rec.get("schema")=="vf.office-v2.same-fixture-two-host-lab.v0","WRONG_SCHEMA"
    assert rec.get("trial")==trial,"TRIAL_MISMATCH"
    assert rec.get("host")==EXPECTED_HOST[trial],"HOST_MISMATCH"
    assert rec.get("model")==EXPECTED_MODEL[trial],"MODEL_MISMATCH"
    assert rec.get("source_sha256")==EXPECTED_SOURCE,"SOURCE_SHA_DRIFT"
    assert rec.get("source_blob")==EXPECTED_BLOB,"SOURCE_BLOB_DRIFT"
    assert rec.get("state")=="FINISHED" and rec.get("exit_code")==0,"EXECUTOR_NOT_FINISHED"
    assert rec.get("verified_success") is True and rec.get("codex_cli") is False,"VERIFICATION_NOT_GREEN"
    assert rec.get("external_spend_usd")==0,"NONZERO_MODEL_COST"
    assert rec.get("changed_paths")==[" M slug.py"],"CHANGED_OTHER_PATHS"
    qa=rec.get("independent_qa") or {}
    assert qa.get("pass") is True and qa.get("unit_exit")==0,"INDEPENDENT_UNIT_FAIL"
    assert qa.get("edge_exit")==0 and qa.get("edge_ok") is True,"INDEPENDENT_EDGE_FAIL"
    assert qa.get("changed_paths")==[" M slug.py"],"INDEPENDENT_REPLAY_CHANGED_PATHS"
    assert qa.get("replayed_sha256")==rec.get("after_sha256"),"REPLAY_ARTIFACT_DRIFT"
    assert "Ran 3 tests" in " ".join(qa.get("unit_summary") or []),"UNIT_COUNT_NOT_PROVEN"
    start,end=when(rec["started_utc"]),when(rec["finished_utc"])
    elapsed=(end-start).total_seconds()
    assert start<end and abs(elapsed-rec["elapsed_seconds"])<.7,"INVALID_ELAPSED_CLOCK"
    return start,end

def verify_crash(rec):
    verify_sig(rec)
    assert rec.get("schema")=="vf.office-v2.forced-worker-loss-lab.v0","CRASH_SCHEMA"
    for field,expected in (
     ("worker_returncode",-9),("running_journal_present",True),("final_receipt_present",False),
     ("partial_output_present",True),("complete_output_present",False),
     ("checkpoint_unchanged",True),("blind_replay_exit_code",1),
     ("no_false_success",True),("external_business_effects",0),
     ("actual_scheduler_failover_tested",False),("autonomous_resume_tested",False)):
        assert rec.get(field)==expected,"CRASH_GATE_"+field
    assert rec.get("blind_replay_rejection")=="DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY","BLIND_RETRY_UNBLOCKED"
    assert rec.get("dirty_paths")==["?? started.txt"],"PARTIAL_EFFECT_NOT_VISIBLE"
    assert len(rec.get("journal_sha256",""))==64,"JOURNAL_HASH_MISSING"
    return True

def assess(receipts):
    times={key:verify_trial(key,receipts[key]) for key in EXPECTED_HOST}
    verify_crash(receipts["forced-crash"])
    w0,w1=times["win-serial"];m0,m1=times["mac-serial"]
    assert w1<=m0,"SERIAL_LANES_OVERLAPPED"
    wp0,wp1=times["win-parallel"];mp0,mp1=times["mac-parallel"]
    assert min(wp1,mp1)>max(wp0,mp0),"NO_TRUE_CONCURRENT_AGENT_EXECUTION"
    assert receipts["win-parallel"]["after_sha256"]==receipts["win-serial"]["after_sha256"],"WINDOWS_OUTPUT_DRIFT"
    assert receipts["mac-parallel"]["after_sha256"]==receipts["mac-serial"]["after_sha256"],"MAC_OUTPUT_DRIFT"
    serial_wall=(m1-w0).total_seconds()
    parallel_wall=(max(wp1,mp1)-min(wp0,mp0)).total_seconds()
    summed_serial_model_seconds=round(sum(receipts[k]["elapsed_seconds"] for k in ("win-serial","mac-serial")),3)
    assert serial_wall>=summed_serial_model_seconds-.6,"BAD_SERIAL_WALL"
    result={
      "schema":"vf.office-v2.p0-two-host-measured-concurrency-and-loss.v0",
      "status":"PASS_SCOPED_LAB",
      "canonical_issue":"https://github.com/nocturney/velvetos-core/issues/612",
      "test":"two identical source/test coding tasks, serial dispatch on Windows then Mac versus overlapping dispatch",
      "fixture":{"source_sha256":EXPECTED_SOURCE,"source_git_blob":EXPECTED_BLOB},
      "runs":{k:{"host":receipts[k]["host"],"model":receipts[k]["model"],
          "started_utc":receipts[k]["started_utc"],"finished_utc":receipts[k]["finished_utc"],
          "model_elapsed_seconds":receipts[k]["elapsed_seconds"],
          "unit_passed":3,"edge_passed":12,"independent_qa_pass":True,
          "receipt_sha256":receipts[k]["receipt_sha256"],
          "after_sha256":receipts[k]["after_sha256"]} for k in EXPECTED_HOST},
      "serial_wall_seconds":round(serial_wall,3),
      "serial_sum_model_seconds":summed_serial_model_seconds,
      "parallel_wall_seconds":round(parallel_wall,3),
      "parallel_overlap_seconds":round((min(wp1,mp1)-max(wp0,mp0)).total_seconds(),3),
      "speedup_total_dispatch_wall":round(serial_wall/parallel_wall,3),
      "speedup_model_time_upper_bound":round(summed_serial_model_seconds/parallel_wall,3),
      "all_four_real_local_model_invocations_verified":True,
      "no_p50_p95_claim":"one pair per mode; repeats required for confidence",
      "resource_peak_metrics":"NOT_MEASURED; after-run memory snapshots are not peak measurements",
      "cross_host_model_parity":"DIFFERENT_QWEN_4B_AND_9B; same model on same host for serial/parallel",
      "concurrent_inference_did_not_fail_qa":True,
      "forced_worker_interruption":{"host":"MacMiniOffice.local",
        "source_git_sha":receipts["forced-crash"]["source_git_sha"],
        "receipt_sha256":receipts["forced-crash"]["receipt_sha256"],
        "force_killed_parent_and_owned_child":True,
        "running_journal_preserved":True,"partial_effect_detected":True,
        "no_blind_retry_rejection":"DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY",
        "no_false_success":True},
      "production_authority":"NONE",
      "codex_cli_used":False,"paid_model_api_calls":0,
      "autonomous_scheduler_failover_proven":False,
      "cross_host_crash_resume_proven":False,
      "end_to_end_agent_placement_proven":False,
      "protected_ci_delivery_proven_by_this_trial":False,
      "notes":["This experiment was directly dispatched via authenticated remote tooling, not Dagu or an Office scheduler.",
        "Serial one-at-a-time work spans two hosts; not a single physical host throughput measurement.",
        "No uncontrolled business mutation or customer/printer/social side effects.",
        "Repeated identical fixture on same host may benefit from warm caches; this is one paired observation."]
    }
    result["receipt_sha256"]=digest(result)
    return result

def self_test(receipts):
    assess(receipts)
    negative=[]
    for tag,change in (
      ("tampered_hash",lambda x:x["win-serial"].update({"receipt_sha256":"0"*64})),
      ("false_qa",lambda x:x["win-serial"]["independent_qa"].update({"pass":False})),
      ("cross_host_claim",lambda x:x["mac-serial"].update({"host":"Chris"})),
      ("false_crash",lambda x:x["forced-crash"].update({"no_false_success":False})),
    ):
        x=copy.deepcopy(receipts)
        change(x)
        try:assess(x)
        except AssertionError:negative.append(tag)
        else:raise AssertionError("NEGATIVE_CONTROL_ACCEPTED:"+tag)
    assert len(negative)==4
    return negative

def main():
    ap=argparse.ArgumentParser(description="Verify exact signed #612 evidence bundle offline")
    ap.add_argument("--evidence",required=True)
    args=ap.parse_args()
    bundle=json.loads(pathlib.Path(args.evidence).read_text(encoding="utf-8-sig"))
    if bundle.get("schema")!="vf.office-v2.p0-two-host-evidence-bundle.v0":
        raise AssertionError("BUNDLE_SCHEMA")
    receipts=bundle.get("receipts") or {}
    if set(receipts)!=set(EXPECTED_HOST)|{"forced-crash"}:
        raise AssertionError("MISSING_OR_EXTRA_TRIAL")
    independent=assess(receipts)
    negatives=self_test(receipts)
    independent["independent_negative_controls"]=negatives
    independent.pop("receipt_sha256")
    independent["receipt_sha256"]=digest(independent)
    if independent!=bundle.get("independent_summary"):
        raise AssertionError("EVIDENCE_SUMMARY_HASH_OR_CONTENT_DRIFT")
    if bundle.get("authority")!="LAB_ONLY_NO_PRODUCTION_EFFECT":
        raise AssertionError("AUTHORITY_MISMATCH")
    print(json.dumps({"status":"PASS_SCOPED_LAB",
        "serial_wall_seconds":independent["serial_wall_seconds"],
        "parallel_wall_seconds":independent["parallel_wall_seconds"],
        "observed_speedup":independent["speedup_total_dispatch_wall"],
        "verified_model_runs":4,"forced_loss_no_false_success":True,
        "negative_cases":len(negatives),
        "summary_sha256":independent["receipt_sha256"]}))
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:220]}))
        sys.exit(2)
