#!/usr/bin/env python3
"""#612 pure offline guard for two FRESH guided local-model Mac coding outcomes.

Read-only historical metadata, no Aider/Ollama/OS process, no scheduler, no
model retries, no external effects. Raw originals retained on Mac only.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re

SCHEMA = "velvetos.office-v2.p0-two-fresh-guided-model-qa-results.v0"
MODEL_SHA = "7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13"
SOURCE_SHA = "0099792f8be5d20c4c698a417d83bf5d12d00bfeaeccd92a90aeef81865a2cbb"
OLD_SOURCE_SHA = "c08a8413f59a1924c013adc66f523c897f1e477fae810f2c76127699d4262087"
EXPECTED = (
    {
        "task_id": "p0-diverse-run-mac-merge-guided-20261010-a",
        "fixture": "merge-windows-v1",
        "base_sha": "d081112707ad55ff9e848a380227223bc75dff63",
        "target": "windows_merge.py",
        "candidate_raw_sha256": "bf850cf6c147bc41135b1129e1c2d46d91be8a6b88c3bf86637142007e76fc7a",
        "prompt_raw_sha256": "4f4d0b6bd11950defc786e41d6022dd3f512ab6c5a1193077401341ab9c2c663",
        "envelope_raw_sha256": "6fb794fcca74d457fc84baaf143ccb727608da561e86e1b18e53d63c6b758b96",
        "kernel_pin_raw_sha256": "873b186e5044d242d41bea958c4f4d1bbaabb59632992e03285c45872af0e02c",
        "artifact": "999f8ae84cbca062a41297b6fadf6703ee69fa8a61e427a8441cd1a169c3b0a0",
        "result": "SUCCEEDED",
    },
    {
        "task_id": "p0-diverse-run-mac-tag-guided-20261010-b",
        "fixture": "canonical-tag-v1",
        "base_sha": "14d67645008a068b2f01aae31ff4c02c749308fa",
        "target": "canonical_tag.py",
        "candidate_raw_sha256": "9221e38da7f61f3544f2e8bc4042009403bb969ff6912cea3635cce6b88a6434",
        "prompt_raw_sha256": "09863d9198d0705fb260b0b17b9f54580a87c4ee4e26bbec37111bee90376a57",
        "envelope_raw_sha256": "5d45c89b138647e53b2619c9eb8ec32ecf0fd20563f55f811f458ccadcaf1bdd",
        "kernel_pin_raw_sha256": "d6fa4ec7f1daf8aaf5b05e7f985de713df53940d5530a4ad815977d172e10c29",
        "artifact": "7cadf341335664b89b9dfc40effb127f6315d31429b4759a3c0ab5b6325003fc",
        "result": "FAILED_INDEPENDENT_QA_NO_SUCCESS",
    },
)


class Refused(Exception):
    pass


def need(condition, message):
    if not condition:
        raise Refused(message)


def hash64(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def validate(data):
    need(isinstance(data, dict) and data.get("schema") == SCHEMA
         and data.get("issue") ==
         "https://github.com/nocturney/velvetos-core/issues/612"
         and data.get("status") ==
         "ONE_SUCCESS_ONE_FAILED_QA_ORIGINAL_JOURNAL_PRESERVED",
         "WRONG_HISTORIC_SUCCESS_FAILURE_SCOPE")
    s = data.get("source") or {}
    need(s.get("host") == "MacMiniOffice.local"
         and s.get("repo") == "nocturney/velvetos-core"
         and s.get("base_main") == "f329165c3e10e763913e1fe136f13e503ec66ac7"
         and s.get("executed_code_commit") ==
         "9140b5a87acd2f0bec1ea55a5e591e17ef14b906"
         and s.get("executed_worker_source_sha256") == SOURCE_SHA
         and s.get("archived_failed_worker_source_sha256") == OLD_SOURCE_SHA
         and s.get("model") == "qwen3.5:4b"
         and s.get("model_digest") == MODEL_SHA
         and s.get("prompt_profile") == "PUBLIC_SPEC_REMINDER_V1",
         "HOST_MODEL_PROFILE_OR_SOURCE_DRIFT")
    tasks = data.get("attempts")
    need(isinstance(tasks, list) and len(tasks) == 2, "EXACT_TWO_TASKS")
    observed_tasks, observed_bases, observed_targets = set(), set(), set()
    for n, (t, expected) in enumerate(zip(tasks, EXPECTED)):
        need(isinstance(t, dict), "TASK_NOT_AN_OBJECT")
        for key in ("task_id", "fixture", "base_sha", "target",
                    "candidate_raw_sha256", "prompt_raw_sha256",
                    "envelope_raw_sha256", "kernel_pin_raw_sha256", "result"):
            need(t.get(key) == expected[key], "EXACT_RAW_PROOF_DRIFT_"+key)
        need(t.get("branch") ==
             "lab-p0-diverse-run-" + expected["task_id"]
             and t.get("independent_qa", {}).get("changed_paths") ==
             [expected["target"]]
             and t.get("independent_qa", {}).get("artifact_sha256") ==
             expected["artifact"]
             and t.get("model_invocations_min") == 1
             and t.get("exact_model_calls") is None
             and type(t.get("additional_api_spend_usd")) is int
             and t["additional_api_spend_usd"] == 0
             and t.get("production_authority") is False,
             "FALSE_QA_SOURCE_OR_MODEL_CALL_"+str(n))
        for field in ("candidate_raw_sha256", "prompt_raw_sha256",
                      "envelope_raw_sha256", "kernel_pin_raw_sha256"):
            need(hash64(t.get(field)), "MALFORMED_PROOF_HASH_"+field)
        observed_tasks.add(t["task_id"])
        observed_bases.add(t["base_sha"])
        observed_targets.add(t["target"])
    need(len(observed_tasks) == len(observed_bases) == len(observed_targets) == 2,
         "DUPLICATE_TASK_OR_SAME_CODE")
    good, bad = tasks
    qa = good.get("independent_qa") or {}
    need(good.get("original_model_worker_verify") == "PASS"
         and good.get("result") == "SUCCEEDED"
         and qa.get("pass") is True
         and qa.get("unit_3_verified") is True
         and qa.get("hidden_12_verified") is True
         and qa.get("unit_exit") == qa.get("hidden_exit") == 0
         and good.get("worker_elapsed_seconds") == 65.527
         and good.get("receipt_selfhash") ==
         "431c9d94ac939c794da794e84175964508e77125397e1fcc36a5a7fdc8862524"
         and good.get("receipt_raw_sha256") ==
         "f6dac1286bb1fad2ddb525ecf51d3fd86a9149d2a5cc8464f05c5569350cedda"
         and good.get("running_journal_removed_only_after_independent_success")
         is True,
         "GOOD_TASK_NOT_INDEPENDENTLY_QA_GREEN")
    failed = bad.get("independent_qa") or {}
    need(bad.get("result") == "FAILED_INDEPENDENT_QA_NO_SUCCESS"
         and failed.get("pass") is False
         and failed.get("unit_exit") == failed.get("hidden_exit") == 1
         and failed.get("hidden_12_verified") is False
         and bad.get("original_model_worker_verify") is None
         and bad.get("failed_audit_verify") ==
         "PASS_OFFLINE_HISTORICAL_FAILED_QA_REPORT"
         and bad.get("receipt_selfhash") is None
         and bad.get("receipt_raw_sha256") is None
         and bad.get("original_journal_raw_sha256") ==
         "316dcd74d082da4c8531a29ab8097ccbf5d753692e24a5f6a23d5312b2df7250"
         and bad.get("failed_audit_raw_sha256") ==
         "dd538dee3e06e4c50e635f25b823ce23a226a631991cd5a8b4cb07aba4ffbd3f"
         and bad.get("failed_audit_selfhash") ==
         "24945797067d6177d91b8b1de97b9fbdb0a4a65e1aec593f135b216e2b911227"
         and bad.get("original_journal_preserved") is True
         and bad.get("success_receipt_absent") is True
         and bad.get("original_attempt_retried") is False,
         "ORIGINAL_FAILED_QA_FALSLY_PROMOTED")
    need(data.get("previous_failed_qa_journals_unchanged") == {
        "merge-windows-v1":
        "e909db6a1ab48bd5baaafece671c3a6cf825c6f804b7a273b7314e447fddd89d",
        "canonical-tag-v1":
        "dbf9fa62bfdf6c9da85586810e30dbc0a6fba4c10e6bd5286419375ba5f8e7a3",
    }, "OLD_UNKNOWN_JOURNALS_TOUCHED")
    stats = data.get("statistics") or {}
    need(type(stats.get("attempted")) is int and stats["attempted"] == 2
         and type(stats.get("independent_qa_successes")) is int
         and stats["independent_qa_successes"] == 1
         and type(stats.get("independent_qa_failures")) is int
         and stats["independent_qa_failures"] == 1
         and stats.get("successful_targets") == ["windows_merge.py"]
         and stats.get("failed_targets") == ["canonical_tag.py"]
         and stats.get("successful_worker_elapsed_seconds") == 65.527
         and stats.get("comparison") == "TWO_FRESH_TASKS_NOT_RANDOMIZED_CAUSAL_AB_TEST"
         and stats.get("two_host_execution_proven") is False
         and stats.get("reliable_p95_proven") is False,
         "FALSE_SAMPLE_STATISTICS")
    limits = data.get("limits") or {}
    for flag in ("original_failed_envelopes_retried",
                 "autonomous_unknown_recovery_proven",
                 "all_orphan_descendants_excluded",
                 "cross_host_fencing_verified", "canonical_fleet_lease",
                 "production_writer", "two_independent_host_successes_proven",
                 "auto_requeue_authorized",
                 "confidence_of_prompt_causing_success_established",
                 "original_raw_files_shared_in_git"):
        need(limits.get(flag) is False, "UNPROVEN_AUTHORITY_"+flag)
    need(type(limits.get("model_calls_by_evidence_checker")) is int
         and limits["model_calls_by_evidence_checker"] == 0
         and type(limits.get("additional_paid_api_spend_usd")) is int
         and limits["additional_paid_api_spend_usd"] == 0,
         "UNSUPPORTED_SPEND")
    return {"status":"PASS_HISTORICAL_METADATA_ONLY",
            "successful_coding_tasks":1,
            "failed_qa_tasks":1,"distinct_task_families":2,
            "original_failed_journals_preserved":True,
            "model_invocations_by_verifier":0,
            "two_host_success_proven":False,
            "causal_prompt_improvement_proven":False,
            "production_authority":False}


def selftest(data):
    validate(data)
    tests = ["valid_historical_not_live_execution"]
    negatives = [
        ("fake_success",lambda d:d["attempts"][1].update(result="SUCCEEDED")),
        ("fake_qa",lambda d:d["attempts"][1]["independent_qa"].update(pass_=True)),
        ("false_hidden",lambda d:d["attempts"][1]["independent_qa"].update(hidden_12_verified=True)),
        ("invented_receipt",lambda d:d["attempts"][1].update(receipt_selfhash="0"*64)),
        ("missing_journal",lambda d:d["attempts"][1].update(original_journal_preserved=False)),
        ("falsified_old_journal",lambda d:d["previous_failed_qa_journals_unchanged"].update(**{"merge-windows-v1":"0"*64})),
        ("reuse_task",lambda d:d["attempts"][1].update(task_id=d["attempts"][0]["task_id"])),
        ("reuse_git_base",lambda d:d["attempts"][1].update(base_sha=d["attempts"][0]["base_sha"])),
        ("source_changed",lambda d:d["attempts"][0].update(receipt_raw_sha256="0"*64)),
        ("profile_modified",lambda d:d["source"].update(prompt_profile="CUSTOM")),
        ("worker_source_changed",lambda d:d["source"].update(executed_worker_source_sha256="0"*64)),
        ("model_swapped",lambda d:d["source"].update(model="gpt-5")),
        ("fake_two_success",lambda d:d["statistics"].update(independent_qa_successes=2)),
        ("fake_two_host",lambda d:d["statistics"].update(two_host_execution_proven=True)),
        ("fake_p95",lambda d:d["statistics"].update(reliable_p95_proven=True)),
        ("fake_causal",lambda d:d["limits"].update(confidence_of_prompt_causing_success_established=True)),
        ("false_fencing",lambda d:d["limits"].update(cross_host_fencing_verified=True)),
        ("false_recovery",lambda d:d["limits"].update(autonomous_unknown_recovery_proven=True)),
        ("paid_spend",lambda d:d["limits"].update(additional_paid_api_spend_usd=1)),
        ("fake_production",lambda d:d["limits"].update(production_writer=True)),
        ("invented_calls",lambda d:d["attempts"][0].update(exact_model_calls=3)),
        ("fake_qa_unit",lambda d:d["attempts"][0]["independent_qa"].update(unit_exit=1)),
        ("fake_success_elapsed",lambda d:d["attempts"][0].update(worker_elapsed_seconds=1)),
        ("promote_audit",lambda d:d["attempts"][1].update(failed_audit_verify="PASS_MODEL")),
    ]
    for name, edit in negatives:
        fake=copy.deepcopy(data)
        edit(fake)
        if name=="fake_qa":
            fake["attempts"][1]["independent_qa"]["pass"]=True
        try:
            validate(fake)
        except Refused:
            tests.append(name+"_rejected")
        else:
            raise AssertionError("UNSAFE_FAKE_EVIDENCE_ACCEPTED:"+name)
    need(len(tests)==25,"NEGATIVE_TEST_COUNT_DRIFT")
    return {"status":"PASS_OFFLINE","tests":len(tests),
            "model_calls":0,"new_model_worker_tasks":0,
            "production_writes":0,"cross_host_lease":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("verify","selftest"))
    p.add_argument("--evidence",required=True)
    args=p.parse_args()
    path=Path(args.evidence)
    need(path.is_file() and not path.is_symlink()
         and 0<path.stat().st_size<=1024*1024, "UNSAFE_HISTORICAL_EVIDENCE")
    data=json.loads(path.read_text(encoding="utf-8"))
    outcome=validate(data) if args.mode=="verify" else selftest(data)
    print(json.dumps(outcome,sort_keys=True))


if __name__=="__main__":
    try: main()
    except (Refused,OSError,ValueError,KeyError,TypeError,AssertionError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:140],
                          "no_model_calls":True,"no_automatic_retries":True},
                         sort_keys=True))
        raise SystemExit(2)
