#!/usr/bin/env python3
"""Office P0 #612: offline exact-hash checker for two distinct real Mac coding fixes.

This tool NEVER starts Aider/Ollama, executes any model, requeues a previous
failure, changes source code, grants a #604 lease, or asserts host-independent
throughput. Original raw byte evidence stays separately on Mac. No external
digital signature is claimed.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re

SCHEMA = "velvetos.office-v2.p0-two-distinct-mac-coding-families-qa-green.v0"
MODEL_DIGEST = "7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13"
WORKER_SHA = "4bab56091da28e18d7ad5e28023ddaedbbdc5537c10340e02bdd330a862e6d06"
HEX = re.compile(r"[0-9a-f]{64}\Z")
EXPECTED = (
    {
        "task_id": "p0-diverse-run-mac-merge-guided-20261010-a",
        "fixture_id": "merge-windows-v1",
        "target_file": "windows_merge.py",
        "base_sha": "d081112707ad55ff9e848a380227223bc75dff63",
        "source_execution_commit": "9140b5a87acd2f0bec1ea55a5e591e17ef14b906",
        "prompt_profile": "PUBLIC_SPEC_REMINDER_V1",
        "candidate_raw_sha256": "bf850cf6c147bc41135b1129e1c2d46d91be8a6b88c3bf86637142007e76fc7a",
        "prompt_sha256": "4f4d0b6bd11950defc786e41d6022dd3f512ab6c5a1193077401341ab9c2c663",
        "raw_file_sha256": {
            "envelope": "6fb794fcca74d457fc84baaf143ccb727608da561e86e1b18e53d63c6b758b96",
            "receipt": "f6dac1286bb1fad2ddb525ecf51d3fd86a9149d2a5cc8464f05c5569350cedda",
            "pin": "873b186e5044d242d41bea958c4f4d1bbaabb59632992e03285c45872af0e02c",
            "prompt": "4f4d0b6bd11950defc786e41d6022dd3f512ab6c5a1193077401341ab9c2c663",
            "code": "999f8ae84cbca062a41297b6fadf6703ee69fa8a61e427a8441cd1a169c3b0a0",
        },
        "elapsed_seconds": 65.527,
        "receipt_sha256": "431c9d94ac939c794da794e84175964508e77125397e1fcc36a5a7fdc8862524",
    },
    {
        "task_id": "p0-diverse-run-mac-tag-state-v2-20261010-c",
        "fixture_id": "canonical-tag-v1",
        "target_file": "canonical_tag.py",
        "base_sha": "b078080a31fca74f622ed93bd2c58a7421a51536",
        "source_execution_commit": "34a505292caab5c0769adc4bfb7fcf78fad7c115",
        "prompt_profile": "PUBLIC_SPEC_STATE_MACHINE_V2",
        "candidate_raw_sha256": "599f5aa7b6a52607ed958691cac83df0e3777d2429e8c991926f5c68bba70e66",
        "prompt_sha256": "4b97af9e8df68441cb1381729471b7315308e97e0a7efc917a0fc59954cd592e",
        "raw_file_sha256": {
            "envelope": "4dbee088b61d7112d6c34737e6d2f9555f392889b5f6dba99973aaf9e8c988ec",
            "receipt": "c2f81cec7419219f942ec74524864a2159ca233759ba643e193cead7ed5087d5",
            "pin": "252483fd3a7efffd33b9318085eed5f26831ddea454923ddd7ee3965ff61601a",
            "prompt": "4b97af9e8df68441cb1381729471b7315308e97e0a7efc917a0fc59954cd592e",
            "code": "b2ec92fed514a5e0e37aeca31155fe0d04cdfde70a3d46fafeeb9a09b0ef1ccb",
        },
        "elapsed_seconds": 58.344,
        "receipt_sha256": "2bdb477dc94308e8a8c8d1dff63e5a68843a4d783946d0aaaf93b13c24629e9d",
    },
)


class Refused(Exception):
    pass


def require(ok, message):
    if not ok:
        raise Refused(message)


def sha64(s):
    return isinstance(s, str) and HEX.fullmatch(s) is not None


def verify(proof):
    require(isinstance(proof, dict) and proof.get("schema") == SCHEMA and
            proof.get("issue") == "https://github.com/nocturney/velvetos-core/issues/612" and
            proof.get("status") == "PASS_TWO_DIFFERENT_REAL_LOCAL_CODING_FAMILIES_SAME_MAC_ONLY",
            "WRONG_SCHEMA_OR_SCOPE")
    source = proof.get("source") or {}
    require(source.get("repository") == "nocturney/velvetos-core" and
            source.get("host") == "MacMiniOffice.local" and
            source.get("main_when_v2_created") ==
            "2998a9682cce3f8d624df12c06f471976935ff08" and
            source.get("v2_observed_worker_source_sha256") == WORKER_SHA and
            source.get("v2_working_branch") ==
            "office-v2/p0-diverse-single-separator-state-profile-20261010" and
            source.get("prompt_material") == "PUBLIC_TASK_SPEC_ONLY_NEVER_HIDDEN_QA_OR_GOLDEN_SOURCE",
            "SOURCE_HOST_OR_PUBLISHED_SPEC_DRIFT")
    attempts = proof.get("real_attempts")
    require(isinstance(attempts, list) and len(attempts) == 2,
            "EXACTLY_TWO_REAL_HISTORICAL_ATTEMPTS")
    unique_tasks, unique_bases, unique_branches, unique_targets = set(), set(), set(), set()
    for i, (a, expected) in enumerate(zip(attempts, EXPECTED)):
        require(isinstance(a, dict), "ATTEMPT_NOT_OBJECT")
        for field in ("task_id", "fixture_id", "target_file", "base_sha",
                      "source_execution_commit", "prompt_profile",
                      "candidate_raw_sha256", "prompt_sha256"):
            require(a.get(field) == expected[field],
                    "HISTORICAL_TASK_OR_PROMPT_DRIFT_" + field)
        require(a.get("host") == "MacMiniOffice.local"
                and a.get("model") == "qwen3.5:4b"
                and a.get("model_digest") == MODEL_DIGEST
                and a.get("branch") == "lab-p0-diverse-run-" + expected["task_id"]
                and a.get("raw_file_sha256") == expected["raw_file_sha256"]
                and all(sha64(s) for s in (a.get("raw_file_sha256") or {}).values()),
                "HOST_MODEL_BRANCH_OR_RAW_BYTES_DRIFT")
        r = a.get("worker_receipt") or {}
        qa = r.get("independent_qa") or {}
        require(r.get("state") == "SUCCEEDED"
                and type(r.get("elapsed_seconds")) in (float, int)
                and r["elapsed_seconds"] == expected["elapsed_seconds"]
                and r.get("receipt_sha256") == expected["receipt_sha256"]
                and r.get("source_sha256") == expected["raw_file_sha256"]["code"]
                and r.get("changed_paths") == [expected["target_file"]]
                and r.get("kernel_pin_sha256") ==
                   (a.get("kernel_birth") or {}).get("pin_sha256")
                and type(r.get("model_invocations_min")) is int
                and r["model_invocations_min"] == 1
                and r.get("exact_model_calls") is None
                and type(r.get("additional_api_spend_usd")) is int
                and r["additional_api_spend_usd"] == 0,
                "WORKER_RECEIPT_OR_SOURCE_PROMOTED_FALSELY")
        require(qa.get("pass") is True and
                qa.get("unit_3_verified") is True and
                qa.get("hidden_12_verified") is True and
                qa.get("unit_exit") == 0 and qa.get("hidden_exit") == 0
                and qa.get("replay_changed_paths") == [expected["target_file"]]
                and qa.get("artifact_sha256") == expected["raw_file_sha256"]["code"]
                and sha64(qa.get("hidden_stdout_sha256")),
                "VISIBLE_OR_HIDDEN_INDEPENDENT_QA_NOT_VERIFIED")
        k = a.get("kernel_birth") or {}
        for name in ("worker", "aider"):
            row = k.get(name)
            require(isinstance(row, dict)
                    and type(row.get("pid")) is int and row["pid"] > 0
                    and type(row.get("birth_us")) is int and row["birth_us"] > 0
                    and row.get("source") == "PSUTIL_OS_CREATE_TIME",
                    "OS_BIRTH_HISTORIC_IDENTITY_DRIFT")
        require(k["aider"].get("ppid") == k["worker"]["pid"]
                and k["aider"]["pid"] != k["worker"]["pid"]
                and k.get("retry_permitted") is False
                and k.get("all_orphans_excluded") is False,
                "OS_BIRTH_PARENT_OR_RETRY_FENCE_MISSING")
        require(a.get("separate_worker_verify") == "PASS"
                and a.get("running_journal_cleared_after_success") is True
                and a.get("original_task_retried") is False
                and a.get("production_authority") is False,
                "WRONG_RECEIPT_AUTHORITY_OR_SEPARATE_REPLAY")
        unique_tasks.add(a["task_id"]); unique_bases.add(a["base_sha"])
        unique_branches.add(a["branch"]); unique_targets.add(a["target_file"])
    require(len(unique_tasks) == len(unique_bases) == len(unique_branches)
            == len(unique_targets) == 2,
            "NOT_TWO_DISTINCT_INDEPENDENT_CODE_TASKS")
    old = proof.get("previous_unmodified_failed_journal_sha256") or {}
    require(old == {
        "mac_original_merge": "e909db6a1ab48bd5baaafece671c3a6cf825c6f804b7a273b7314e447fddd89d",
        "mac_original_tag": "dbf9fa62bfdf6c9da85586810e30dbc0a6fba4c10e6bd5286419375ba5f8e7a3",
        "mac_public_spec_v1_tag": "316dcd74d082da4c8531a29ab8097ccbf5d753692e24a5f6a23d5312b2df7250",
    }, "PREVIOUS_UNKNOWN_JOURNALS_MODIFIED_OR_LOST")
    stat = proof.get("statistics") or {}
    require(type(stat.get("newly_verified_different_code_families")) is int and
            stat["newly_verified_different_code_families"] == 2 and
            type(stat.get("newly_verified_qa_successes")) is int and
            stat["newly_verified_qa_successes"] == 2 and
            type(stat.get("distinct_hosts")) is int and stat["distinct_hosts"] == 1 and
            type(stat.get("distinct_git_bases")) is int and stat["distinct_git_bases"] == 2 and
            stat.get("independent_visible_unit_tests_each") == "3/3" and
            stat.get("independent_hidden_tests_each") == "12/12" and
            stat.get("observed_worker_elapsed_seconds") == [65.527, 58.344] and
            stat.get("mean_worker_elapsed_seconds") == 61.9355 and
            stat.get("meaningful_p95_estimate") is False and
            stat.get("two_host_model_success_proven") is False and
            stat.get("causal_prompt_effect_proven") is False,
            "FALSE_TWO_HOST_P95_OR_SUCCESS_STATISTICS")
    limits = proof.get("scope_limits") or {}
    for field in ("three_older_failed_task_envelopes_retried",
                  "original_failed_journals_removed",
                  "canonical_cross_host_lease", "distributed_fencing_verified",
                  "autonomous_recovery_proven", "exhaustive_orphan_exclusion",
                  "production_writer", "paid_api_calls", "codex_cli_calls",
                  "new_scheduler", "real_repository_agent_authored_PRs_proven",
                  "original_raw_files_in_git", "signatures_are_external_attestations"):
        require(limits.get(field) is False, "FALSE_AUTHORITY_OR_READINESS_"+field)
    return {"status":"PASS_HISTORICAL_TWO_DIFFERENT_MAC_CODING_FAMILIES_OFFLINE_ONLY",
            "separate_original_worker_verifications":2,
            "different_target_files":2,
            "different_physical_hosts":1,
            "prior_unknown_journals_intact":True,
            "original_model_tasks_retried":False,
            "reliable_p95":False,
            "additional_model_calls":0,
            "production_or_distributed_fencing_authority":False}


def selftest(data):
    verify(data)
    tests=["original_two_mac_task_metadata_only"]
    variants=[
        ("not_two",lambda z:z["real_attempts"].pop()),
        ("same_task_id",lambda z:z["real_attempts"][1].update(task_id=z["real_attempts"][0]["task_id"])),
        ("same_git_base",lambda z:z["real_attempts"][1].update(base_sha=z["real_attempts"][0]["base_sha"])),
        ("same_target",lambda z:z["real_attempts"][1].update(target_file=z["real_attempts"][0]["target_file"])),
        ("wrong_host",lambda z:z["source"].update(host="Chris")),
        ("false_two_host",lambda z:z["statistics"].update(distinct_hosts=2)),
        ("reliable_p95",lambda z:z["statistics"].update(meaningful_p95_estimate=True)),
        ("causal_profile",lambda z:z["statistics"].update(causal_prompt_effect_proven=True)),
        ("wrong_model",lambda z:z["real_attempts"][0].update(model="qwen3.5:9b")),
        ("wrong_digest",lambda z:z["real_attempts"][0].update(model_digest="0"*64)),
        ("prompt_profile",lambda z:z["real_attempts"][1].update(prompt_profile="ARBITRARY")),
        ("changed_prompt",lambda z:z["real_attempts"][0].update(prompt_sha256="0"*64)),
        ("changed_original_receipt",lambda z:z["real_attempts"][0]["raw_file_sha256"].update(receipt="0"*64)),
        ("changed_code",lambda z:z["real_attempts"][1]["worker_receipt"].update(source_sha256="0"*64)),
        ("changed_qa",lambda z:z["real_attempts"][0]["worker_receipt"]["independent_qa"].update(pass_=False)),
        ("hidden_fails",lambda z:z["real_attempts"][1]["worker_receipt"]["independent_qa"].update(hidden_12_verified=False)),
        ("unit_fails",lambda z:z["real_attempts"][1]["worker_receipt"]["independent_qa"].update(unit_exit=1)),
        ("wrong_birth",lambda z:z["real_attempts"][1]["kernel_birth"]["aider"].update(ppid=0)),
        ("model_falsified_calls",lambda z:z["real_attempts"][1]["worker_receipt"].update(exact_model_calls=1)),
        ("cost",lambda z:z["real_attempts"][0]["worker_receipt"].update(additional_api_spend_usd=1)),
        ("rerun_old",lambda z:z["scope_limits"].update(three_older_failed_task_envelopes_retried=True)),
        ("tamper_unknown",lambda z:z["previous_unmodified_failed_journal_sha256"].update(mac_original_merge="0"*64)),
        ("fencing",lambda z:z["scope_limits"].update(distributed_fencing_verified=True)),
        ("production",lambda z:z["scope_limits"].update(production_writer=True)),
    ]
    for label, mutate in variants:
        fake=copy.deepcopy(data)
        mutate(fake)
        if label=="changed_qa":fake["real_attempts"][0]["worker_receipt"]["independent_qa"]["pass"]=False
        try:
            verify(fake)
        except Refused:
            tests.append(label+"_DENIED")
        else:
            raise AssertionError("UNSAFE_METADATA_ADMITTED_"+label)
    require(len(tests)==25, "EXPECTED_25_SAFE_TESTS")
    return {"status":"PASS_OFFLINE","tests":len(tests),
            "model_invocations":0,"scheduler_calls":0,
            "production_actions":0,"authority_promoted":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("verify","selftest"))
    p.add_argument("--evidence",required=True)
    arg=p.parse_args()
    file=Path(arg.evidence)
    require(file.is_file() and not file.is_symlink() and
            0 < file.stat().st_size < 1024*1024,"BAD_OR_MISSING_HISTORICAL_EVIDENCE")
    doc=json.loads(file.read_text(encoding="utf-8"))
    result=verify(doc) if arg.mode=="verify" else selftest(doc)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    try: main()
    except (Refused,OSError,ValueError,TypeError,KeyError,AssertionError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:170],
                          "no_model_or_automatic_retries":True,
                          "no_production_authority":True},sort_keys=True))
        raise SystemExit(2)
