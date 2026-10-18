#!/usr/bin/env python3
"""#612: exact original LAB Aider stdout usage DISPLAY, not exact tokens.

Three separately QA-green Mac local Qwen/Aider Task Envelopes already executed.
Original receipts and stdout only read in the manually invoked observe mode.
No model, API, network calls, writer, scheduler, other tasks, or model retry.

Aider's terminal token strings may be rounded (e.g. '1.0k'). Never present
them as exact Ollama token accounting, a stable p50/p95 or a cost estimate.
Protected CI calls ONLY offline verify/selftest against sanitized history.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

SCHEMA = "velvetos.office-v2.p0-three-mac-aider-display-usage.v0"
STATUS = "PASS_THREE_ORIGINAL_QA_SUCCESSES_AIDER_DISPLAY_ONLY"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
DIGEST = "7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13"
LAB = "AgentEnvelopeLab"
MAIN_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = MAIN_ROOT / "docs/implementation/office-v2/phase2/p0-three-mac-aider-displayed-tokens-2026-10-10.json"
TASKS = [
    {
        "id":"p0-diverse-run-mac-merge-guided-20261010-a",
        "path":"p0-diverse-execution-mac-profile-20261010",
        "fixture":"merge-windows-v1",
        "source_sha":"999f8ae84cbca062a41297b6fadf6703ee69fa8a61e427a8441cd1a169c3b0a0",
        "receipt_raw_sha":"f6dac1286bb1fad2ddb525ecf51d3fd86a9149d2a5cc8464f05c5569350cedda",
        "elapsed":65.527,
        "expected_terminal_usage":"Tokens: 1.0k sent, 1.1k received.",
    },
    {
        "id":"p0-diverse-run-mac-tag-state-v2-20261010-c",
        "path":"p0-diverse-execution-mac-state-v2-20261010",
        "fixture":"canonical-tag-v1",
        "source_sha":"b2ec92fed514a5e0e37aeca31155fe0d04cdfde70a3d46fafeeb9a09b0ef1ccb",
        "receipt_raw_sha":"c2f81cec7419219f942ec74524864a2159ca233759ba643e193cead7ed5087d5",
        "elapsed":58.344,
        "expected_terminal_usage":"Tokens: 1.0k sent, 940 received.",
    },
    {
        "id":"p0-diverse-run-mac-merge-exact-int-20261010-d",
        "path":"p0-diverse-execution-mac-exact-int-20261010",
        "fixture":"merge-windows-v1",
        "source_sha":"0ec526a84d6a814aecbfc586c237ef59044811f920c0d73640cbf24b76e25479",
        "receipt_raw_sha":"b0cc5ff5e24d33243e65fa7c5f569f7c11bcc275060e76813ed4198e65236fda",
        "elapsed":62.586,
        "expected_terminal_usage":"Tokens: 1.1k sent, 1.0k received.",
    }
]
TOKEN = re.compile(
    r"(?m)^Tokens: (?:[0-9]+(?:\.[0-9]+)?k|[0-9]+) sent, "
    r"(?:[0-9]+(?:\.[0-9]+)?k|[0-9]+) received\.$"
)
HEX64 = re.compile("[0-9a-f]{64}\\Z")


class Refused(Exception):
    pass


def need(ok, why):
    if not ok:
        raise Refused(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def observe(root_raw):
    root=Path(root_raw)
    need(root.is_absolute() and root.is_dir() and
         root.name==LAB and not root.is_symlink(),
         "ONLY_MAC_LAB_ORIGINAL_ROOT")
    import platform
    need(platform.node()=="MacMiniOffice.local",
         "MUST_BE_ORIGINAL_MAC_HOST")
    results=[]
    for spec in TASKS:
        base=root/spec["path"]/spec["id"]
        receipt=base/"output/receipt.json"
        log=base/"output/stdout.log"
        need(base.is_dir() and not base.is_symlink() and
             receipt.is_file() and not receipt.is_symlink() and
             log.is_file() and not log.is_symlink() and
             not (base/"output/receipt.json.running").exists(),
             "ORIGINAL_QA_SUCCESS_ONLY_NO_UNKNOWN")
        rbytes=receipt.read_bytes()
        need(sha(rbytes)==spec["receipt_raw_sha"],
             "ORIGINAL_RECEIPT_BYTES_DRIFT")
        try:
            obj=json.loads(rbytes)
        except (ValueError,UnicodeError):
            raise Refused("ORIGINAL_WORKER_RECEIPT_NOT_JSON")
        qa=obj.get("independent_qa") or {}
        need(obj.get("state")=="SUCCEEDED"
             and obj.get("task_id")==spec["id"]
             and obj.get("model")=="qwen3.5:4b"
             and obj.get("model_digest")==DIGEST
             and obj.get("elapsed_seconds")==spec["elapsed"]
             and obj.get("source_sha256")==spec["source_sha"]
             and obj.get("model_invocations_min")==1
             and obj.get("exact_model_calls") is None
             and obj.get("local_model_usage_tokens") is None
             and obj.get("additional_api_spend_usd")==0
             and qa.get("pass") is True
             and qa.get("unit_3_verified") is True
             and qa.get("hidden_12_verified") is True,
             "NOT_ORIGINAL_MODEL_QA_GREEN")
        raw_log=log.read_bytes()
        need(sha(raw_log)==obj.get("stdout_log_sha256") and
             100 < len(raw_log)<1000000,
             "ORIGINAL_AIDER_LOG_SHA_NOT_MATCHED")
        text=raw_log.decode("utf-8",errors="replace")
        matches=TOKEN.findall(text)
        need(len(matches)==1 and matches[0]==spec["expected_terminal_usage"],
             "NOT_EXACTLY_ONE_EXPECTED_AIDER_TERMINAL_USAGE_LINE")
        results.append({
            "task_id":spec["id"],
            "fixture":spec["fixture"],
            "original_worker_receipt_raw_sha256":sha(rbytes),
            "original_worker_stdout_raw_sha256":sha(raw_log),
            "original_worker_source_sha256":spec["source_sha"],
            "original_elapsed_seconds":spec["elapsed"],
            "original_independent_qa":"3_VISIBLE_12_HIDDEN_PASS",
            "terminal_usage_lines_found":len(matches),
            "terminal_usage_line_exact_text":matches[0],
            "displayed_tokens_are_not_exact":True,
            "underlying_ollama_usage_tokens_known":False,
            "exact_model_call_count_known":False,
        })
    return {
        "schema":SCHEMA,"status":STATUS,"issue":ISSUE,
        "recorded_date_utc":"2026-10-10",
        "source_host":"MacMiniOffice.local",
        "model":"qwen3.5:4b","model_digest":DIGEST,
        "source":"ORIGINAL_MAC_WORKER_RECEIPT_AND_AIDER_STDOUT_READ_ONLY",
        "results":results,
        "limits":{
            "original_receipts_or_logs_mutated":False,
            "any_model_replayed":False,
            "any_background_scheduler_added":False,
            "exact_ollama_token_counts_proven":False,
            "tokens_per_second_accurate_proven":False,
            "cost_per_token_estimated":False,
            "statistically_valid_p95_proven":False,
            "repeated_identical_workloads":False,
            "two_host_execution_proven":False,
            "model_calls_during_observe":0,
            "production_writer_authority":False,
            "distributed_fleet_fencing_proven":False,
        }
    }


def validate(data):
    need(isinstance(data,dict) and data.get("schema")==SCHEMA
         and data.get("status")==STATUS and data.get("issue")==ISSUE
         and data.get("source_host")=="MacMiniOffice.local"
         and data.get("model")=="qwen3.5:4b"
         and data.get("model_digest")==DIGEST
         and data.get("source")==
             "ORIGINAL_MAC_WORKER_RECEIPT_AND_AIDER_STDOUT_READ_ONLY",
         "AIDER_USAGE_WRONG_SOURCE_OR_SCOPE")
    results=data.get("results")
    need(isinstance(results,list) and len(results)==3,
         "EXACT_THREE_ORIGINAL_RECEIPTS_REQUIRED")
    for i,spec in enumerate(TASKS):
        a=results[i]
        need(isinstance(a,dict)
             and a.get("task_id")==spec["id"]
             and a.get("fixture")==spec["fixture"]
             and a.get("original_worker_receipt_raw_sha256")==spec["receipt_raw_sha"]
             and a.get("original_worker_source_sha256")==spec["source_sha"]
             and a.get("original_elapsed_seconds")==spec["elapsed"]
             and a.get("original_independent_qa")=="3_VISIBLE_12_HIDDEN_PASS"
             and a.get("terminal_usage_lines_found")==1
             and a.get("terminal_usage_line_exact_text")==spec["expected_terminal_usage"]
             and a.get("displayed_tokens_are_not_exact") is True
             and a.get("underlying_ollama_usage_tokens_known") is False
             and a.get("exact_model_call_count_known") is False,
             "HISTORICAL_SOURCE_USAGE_OR_QA_DRIFT_"+str(i))
        need(isinstance(a.get("original_worker_stdout_raw_sha256"),str)
             and HEX64.fullmatch(a["original_worker_stdout_raw_sha256"]) is not None,
             "ORIGINAL_STDOUT_HASH_NOT_VALID")
    flags=data.get("limits") or {}
    for k in ("original_receipts_or_logs_mutated","any_model_replayed",
              "any_background_scheduler_added","exact_ollama_token_counts_proven",
              "tokens_per_second_accurate_proven","cost_per_token_estimated",
              "statistically_valid_p95_proven","repeated_identical_workloads",
              "two_host_execution_proven","production_writer_authority",
              "distributed_fleet_fencing_proven"):
        need(flags.get(k) is False,"FALSE_TOKEN_USAGE_OR_AUTHORITY_"+k)
    need(type(flags.get("model_calls_during_observe")) is int
         and flags["model_calls_during_observe"]==0,
         "MODEL_CALLS_DURING_OBSERVER")
    return {"status":"PASS_HISTORICAL_AIDER_DISPLAY_ONLY_NO_EXACT_TOKENS",
            "mac_original_successes":3,
            "unique_task_envelopes":3,
            "model_calls_by_verifier":0,
            "accurate_ollama_token_counts_proven":False,
            "statistically_reliable_p95_proven":False,
            "production_authority":False}


def selftest(data):
    validate(data)
    cases=["original_three_exact_receipts"]
    modifications=[
        ("invented_exact_ollama",lambda x:x["limits"].update(exact_ollama_token_counts_proven=True)),
        ("pretend_p95",lambda x:x["limits"].update(statistically_valid_p95_proven=True)),
        ("fake_model_usage",lambda x:x["results"][0].update(underlying_ollama_usage_tokens_known=True)),
        ("rounded_as_exact",lambda x:x["results"][1].update(displayed_tokens_are_not_exact=False)),
        ("fake_source_hash",lambda x:x["results"][2].update(original_worker_stdout_raw_sha256="oops")),
        ("fake_receipt_hash",lambda x:x["results"][0].update(original_worker_receipt_raw_sha256="0"*64)),
        ("fake_id",lambda x:x["results"][0].update(task_id=x["results"][1]["task_id"])),
        ("wrong_host",lambda x:x.update(source_host="Chris")),
        ("wrong_model",lambda x:x.update(model="qwen3.5:9b")),
        ("wrong_digest",lambda x:x.update(model_digest="0"*64)),
        ("fake_speed",lambda x:x["limits"].update(tokens_per_second_accurate_proven=True)),
        ("fake_cost",lambda x:x["limits"].update(cost_per_token_estimated=True)),
        ("fake_two_host",lambda x:x["limits"].update(two_host_execution_proven=True)),
        ("fake_prod",lambda x:x["limits"].update(production_writer_authority=True)),
        ("fake_fence",lambda x:x["limits"].update(distributed_fleet_fencing_proven=True)),
        ("new_model_calls",lambda x:x["limits"].update(model_calls_during_observe=1)),
        ("multiple_token_lines",lambda x:x["results"][0].update(terminal_usage_lines_found=2)),
        ("altered_token_display",lambda x:x["results"][2].update(terminal_usage_line_exact_text="Tokens: 2.0k sent, 2.0k received.")),
        ("false_qa",lambda x:x["results"][0].update(original_independent_qa="NOT_VERIFIED")),
        ("false_repeated_identical",lambda x:x["limits"].update(repeated_identical_workloads=True)),
    ]
    for name,fn in modifications:
        fake=copy.deepcopy(data)
        fn(fake)
        try:
            validate(fake)
        except Refused:
            cases.append(name+"_DENIED")
        else:
            raise AssertionError("FALSE_AIDER_TOKEN_EVIDENCE_ACCEPTED_"+name)
    need(len(cases)==21,"AIDER_USAGE_SELFTEST_COUNT_DRIFT")
    return {"status":"PASS_OFFLINE","tests":len(cases),"model_calls":0,
            "production_writes":0,"exact_tokens_proven":False,
            "two_host_execution_proven":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("observe","verify","selftest"))
    p.add_argument("--mac-lab-root",default=None)
    p.add_argument("--evidence",default=str(EVIDENCE))
    args=p.parse_args()
    if args.mode=="observe":
        need(args.mac_lab_root is not None
             and Path(args.evidence)==EVIDENCE,
             "EXPLICIT_ORIGINAL_MAC_ONLY_NO_OTHER_INPUTS")
        result=observe(args.mac_lab_root)
    else:
        need(args.mac_lab_root is None,
             "OFFLINE_VERIFIER_DENIES_LIVE_HOST_INPUT")
        path=Path(args.evidence)
        need(path.is_file() and not path.is_symlink()
             and path.stat().st_size<16000,
             "PINNED_SANITIZED_HISTORY_REQUIRED")
        try:
            row=json.loads(path.read_text(encoding="utf-8"))
        except (OSError,ValueError) as exc:
            raise Refused("HISTORICAL_STDOUT_METADATA_INVALID") from exc
        result=validate(row) if args.mode=="verify" else selftest(row)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    try:main()
    except (Refused,OSError,ValueError,KeyError,TypeError,AssertionError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:150],
                          "model_calls":0,"automatic_retry":False,
                          "production_authority":False},sort_keys=True))
        raise SystemExit(2)
