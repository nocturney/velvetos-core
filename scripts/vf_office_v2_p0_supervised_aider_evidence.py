#!/usr/bin/env python3
"""#612 independent OFFLINE proof for two real Win32 Job-supervised local Aider trials.

Manual LAB-only Windows supervisor is separate. This verifier NEVER starts a
model, touches processes, retries an UNKNOWN task, invokes a scheduler or writes
business/production state. SHA-256 self-hashes are not digital signatures.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import vf_office_v2_p0_kernel_identity as kernel

SCHEMA = "vf.office-v2.p0-supervised-real-aider-win-job-two-modes.v0"
JOB_SCHEMA = "vf.office-v2.p0-job-contained-aider-attempt.v0"
MODEL_SCHEMA = "velvetos.office-v2.p0-local-model-receipt.v1"
KIND = "LOCAL_AIDER_OLLAMA_SYNTHETIC_V1"
BIRTH = "REQUIRE_OS_BIRTH_BEFORE_QA_V1"
CONTAINER = "WINDOWS_UNNAMED_JOB_KILL_ON_LAST_HANDLE_CLOSE"
EXPECTED = {
    "interrupt": "p0-win-job-guard-gpt6-interrupt-20261009-c",
    "success": "p0-win-job-guard-gpt6-success-20261009-d",
}
SHA = re.compile(r"[0-9a-f]{64}\Z")


def require(condition, reason):
    if not condition:
        raise AssertionError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def sealed(value, key):
    require(isinstance(value, dict), "SEALED_OBJECT_REQUIRED")
    given = value.get(key)
    require(isinstance(given, str) and SHA.fullmatch(given), "SEAL_ABSENT_" + key)
    require(digest({k: v for k, v in value.items() if k != key}) == given,
            "SELF_HASH_DRIFT_" + key)


def exact_bytes(entry, field):
    raw = entry.get(field + "_file_base64")
    expected = entry.get(field + "_file_sha256")
    require(isinstance(raw, str) and len(raw) < 100000, "FILE_BYTES_MISSING_" + field)
    require(isinstance(expected, str) and SHA.fullmatch(expected), "FILE_HASH_MISSING_" + field)
    try:
        data = base64.b64decode(raw, validate=True)
        parsed = json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise AssertionError("FILE_BYTES_INVALID_" + field)
    require(0 < len(data) < 65536, "FILE_SIZE_" + field)
    require(hashlib.sha256(data).hexdigest() == expected, "RAW_FILE_HASH_DRIFT_" + field)
    require(isinstance(parsed, dict) and parsed == entry[field],
            "SERIALIZED_FILE_CONTENT_DRIFT_" + field)
    return data


def check_sample(sample, mode):
    require(isinstance(sample, dict), "SAMPLE_OBJECT")
    task = EXPECTED[mode]
    env, job, pin = (sample.get(key) for key in ("envelope", "job", "pin"))
    require(isinstance(env, dict) and isinstance(job, dict) and isinstance(pin, dict),
            "EVIDENCE_COMPONENT_MISSING")
    require(env.get("task_id") == task and env.get("host") == "Chris", "ENVELOPE_TASK_HOST")
    require(env.get("kernel_birth_capture") == BIRTH, "KERNEL_CAPTURE_NOT_OPTED_IN")
    require(env.get("authority") == "LAB_LOCAL_MODEL_SYNTHETIC_ONLY_NO_EFFECT", "AUTHORITY")
    require(env.get("budget", {}).get("max_attempts") == 1 and
            env["budget"].get("max_cost_usd") == 0, "BUDGET_NOT_BOUNDED")
    executor = env.get("executor")
    require(isinstance(executor, dict) and executor.get("kind") == KIND and
            executor.get("model") == "qwen3.5:9b" and
            executor.get("ollama_port") == 11555, "WRONG_MODEL_OR_EXECUTOR")
    require(isinstance(executor.get("model_digest"), str) and
            SHA.fullmatch(executor["model_digest"]), "UNPINNED_MODEL")
    require(str(env.get("branch", "")).startswith("lab-p0-agent-") and
            "AgentEnvelopeLab" in env.get("worktree_path", "") and
            "win-native-job-model-20261009" in env["worktree_path"], "OUTSIDE_SYNTHETIC_LAB")
    exact_bytes(sample, "pin")
    sealed(pin, "pin_sha256")
    require(job.get("schema") == JOB_SCHEMA and job.get("task_id") == task and
            job.get("host") == "Chris" and job.get("mode") ==
            ("complete" if mode == "success" else "interrupt"), "JOB_IDENTITY")
    sealed(job, "selfhash_sha256")
    envelope_sha = digest(env)
    require(job.get("envelope_sha256") == envelope_sha and
            pin.get("envelope_sha256") == envelope_sha, "ENVELOPE_JOB_PIN_DRIFT")
    require(job.get("pin_sha256") == pin["pin_sha256"], "KERNEL_PIN_NOT_MATCHED")
    require(job.get("container") == CONTAINER and
            job.get("helper_assigned_before_model_spawn") is True and
            job.get("all_three_job_members_observed") is True, "JOB_NOT_PROVEN_BOUND")
    require(job.get("production_authority") == "NONE" and
            job.get("fleet_scheduler_authority") is False and
            job.get("original_task_retry_allowed") is False and
            job.get("all_possible_escaped_processes_excluded") is False, "UNSAFE_AUTHORITY_CLAIM")
    ids = [job.get(k) for k in ("helper_pid", "model_worker_pid", "aider_pid")]
    require(all(type(k) is int and k > 1 for k in ids) and len(set(ids)) == 3,
            "JOB_PROCESS_IDS_INVALID")
    helper, worker, aider = [job.get(k) for k in
                             ("helper_birth_us", "model_worker_birth_us", "aider_birth_us")]
    require(all(type(k) is int and k > 0 for k in (helper, worker, aider)) and
            helper <= worker <= aider, "PROCESS_BIRTH_LINEAGE_NOT_ORDERED")
    require(pin.get("worker", {}).get("pid") == ids[1] and
            pin["worker"].get("ppid") == ids[0] and
            pin.get("aider", {}).get("pid") == ids[2] and
            pin["aider"].get("ppid") == ids[1], "PROCESS_PARENT_RELATIONSHIP")
    require(pin["worker"].get("source") == "WINDOWS_CIM_CREATION_DATE" and
            pin["aider"].get("source") == "WINDOWS_CIM_CREATION_DATE", "WINDOWS_KERNEL_SOURCE")
    require(abs(pin["worker"].get("birth_us", 0) - worker) <= 1000000 and
            abs(pin["aider"].get("birth_us", 0) - aider) <= 1000000,
            "KERNEL_BIRTH_REPLAY_DRIFT")
    require(pin.get("retry_permitted") is False and
            pin.get("all_orphans_excluded") is False, "KERNEL_PIN_UNSAFE_INFERENCE")

    if mode == "interrupt":
        require(sample.get("worker_receipt") is None and
                job.get("state") == "INTERRUPTED_OWNED_JOB_TREE" and
                job.get("job_descendants_terminated") is True and
                job.get("model_completion_claim") is False and
                job.get("final_receipt_absent") is True and
                job.get("running_journal_persists") is True and
                job.get("same_envelope_reissue_permitted") is False,
                "FALSE_INTERRUPT_SUCCESS")
        exact_bytes(sample, "journal")
        journal = sample["journal"]
        require(journal.get("state") == "RUNNING" and
                journal.get("unknown_outcome_rule") == "NO_BLIND_RETRY" and
                journal.get("task_id") == task and
                journal.get("envelope_sha256") == envelope_sha,
                "ORIGINAL_RUNNING_JOURNAL_DRIFT")
        require(sample.get("readback", {}).get("final_receipt_absent") is True and
                sample["readback"].get("running_journal_present") is True and
                sample["readback"].get("same_envelope_run_refused") is True,
                "MISSING_INDEPENDENT_INTERRUPT_READBACK")
        kernel.checked_pin(env, journal, pin)
        return {"task_id": task, "state": "UNKNOWN_NO_BLIND_RETRY",
                "observed_owned_process_exit": True,
                "retry_allowed": False}

    receipt = sample.get("worker_receipt")
    require(isinstance(receipt, dict), "REAL_MODEL_RECEIPT_REQUIRED")
    sealed(receipt, "receipt_sha256")
    require(job.get("state") == "SUCCEEDED_LOCAL_MODEL_QA_VERIFIED" and
            job.get("model_completion_claim") is True and
            job.get("model_invocations_min") == 1 and
            job.get("original_task_reissue_permitted") is False and
            job.get("worker_receipt_sha256") == receipt["receipt_sha256"],
            "FALSE_COMPLETION_CLAIM")
    require(receipt.get("schema") == MODEL_SCHEMA and
            receipt.get("state") == "SUCCEEDED" and
            receipt.get("task_id") == task and
            receipt.get("host") == "Chris" and
            receipt.get("exit_code") == 0 and
            receipt.get("envelope_sha256") == envelope_sha and
            receipt.get("model") == executor["model"] and
            receipt.get("model_digest") == executor["model_digest"],
            "MODEL_RECEIPT_IDENTITY")
    require(receipt.get("model_invocations_min") == 1 and
            receipt.get("exact_model_calls") is None and
            receipt.get("additional_api_spend_usd") == 0 and
            receipt.get("autonomous_retry") is False and
            receipt.get("scheduler_proven") is False and
            receipt.get("os_network_sandbox_proven") is False and
            receipt.get("production_authority") == "NONE",
            "MODEL_AUTHORITY_OR_CALLS_FALSE")
    require(receipt.get("kernel_birth_mode") == BIRTH and
            receipt.get("kernel_pin_sha256") == pin["pin_sha256"] and
            receipt.get("kernel_pin_file_sha256") == sample["pin_file_sha256"],
            "MODEL_KERNEL_IDENTITY_MISMATCH")
    require(receipt.get("base_sha") == env["base_sha"] and
            receipt.get("branch") == env["branch"] and
            receipt.get("changed_paths") == ["slug.py"], "MODEL_SCOPE_DRIFT")
    qa = receipt.get("independent_qa", {})
    require(qa.get("pass") is True and
            qa.get("unit_exit") == 0 and
            qa.get("unit_3_verified") is True and
            qa.get("hidden_exit") == 0 and
            qa.get("hidden_12_verified") is True and
            qa.get("replay_changed_paths") == ["slug.py"] and
            qa.get("replay_source_sha256") == receipt.get("artifact_sha256"),
            "MODEL_INDEPENDENT_QA_FALSE")
    require(type(receipt.get("elapsed_seconds")) in (int, float) and
            0 < receipt["elapsed_seconds"] <= env["budget"]["timeout_seconds"],
            "MODEL_ELAPSED_OUT_OF_BOUNDS")
    reconstructed = {"state": "RUNNING", "task_id": task,
                     "envelope_sha256": envelope_sha, "host": "Chris",
                     "started_at": receipt["started_at"],
                     "unknown_outcome_rule": "NO_BLIND_RETRY", "kind": KIND}
    kernel.checked_pin(env, reconstructed, pin)
    require(sample.get("readback", {}).get("separate_worker_verify_pass") is True and
            sample["readback"].get("model_run_was_manual") is True,
            "NO_SEPARATE_VERIFIER_READBACK")
    return {"task_id": task, "state": "SUCCEEDED_INDEPENDENT_LAB_QA",
            "observed_model_seconds": receipt["elapsed_seconds"],
            "model_invocations_min": 1, "retry_allowed": False}


def assess(bundle):
    require(isinstance(bundle, dict) and bundle.get("schema") == SCHEMA,
            "EVIDENCE_BUNDLE_SCHEMA")
    require(bundle.get("scope") == "EXCLUSIVE_SYNTHETIC_WINDOWS_LAB_ONLY" and
            bundle.get("owner_issue") == "https://github.com/nocturney/velvetos-core/issues/612",
            "OWNER_OR_SCOPE")
    require(bundle.get("automatic_recovery_proven") is False and
            bundle.get("scheduler_proven") is False and
            bundle.get("production_authority") == "NONE" and
            bundle.get("all_possible_escaped_processes_excluded") is False,
            "BUNDLE_AUTONOMY_FALSE_CLAIM")
    samples = bundle.get("samples")
    require(isinstance(samples, dict) and set(samples) == set(EXPECTED),
            "MISSING_OR_EXTRA_EXPERIMENTS")
    a = check_sample(samples["interrupt"], "interrupt")
    b = check_sample(samples["success"], "success")
    require(samples["interrupt"]["envelope"]["base_sha"] !=
            samples["success"]["envelope"]["base_sha"] and
            a["task_id"] != b["task_id"], "SAME_ATTEMPT_REISSUE_PROHIBITED")
    return {"status": "PASS_SCOPED_WINDOWS_SUPERVISED_AIDER_LAB",
            "historical_interrupt": a["state"],
            "historical_new_attempt": b["state"],
            "two_distinct_real_task_envelopes": True,
            "model_seconds": b["observed_model_seconds"],
            "verified_real_local_model_min_invocations": 1,
            "original_task_retry_allowed": False,
            "all_possible_escaped_processes_excluded": False,
            "automatic_recovery_proven": False,
            "scheduler_proven": False,
            "model_calls_during_verification": 0,
            "production_effects": 0,
            "receipt_sha256": digest({
                "interrupted": samples["interrupt"]["job"]["selfhash_sha256"],
                "completed": samples["success"]["job"]["selfhash_sha256"],
                "model": samples["success"]["worker_receipt"]["receipt_sha256"],
            })}


def reseal(row, key):
    row[key] = digest({k: v for k, v in row.items() if k != key})


def negative_tests(evidence):
    cases = [
        ("interrupt_selfhash_tampered",
         lambda b: b["samples"]["interrupt"]["job"].__setitem__("selfhash_sha256", "0" * 64)),
        ("interrupt_false_success_resealed",
         lambda b: (b["samples"]["interrupt"]["job"].update({"model_completion_claim": True}),
                    reseal(b["samples"]["interrupt"]["job"], "selfhash_sha256"))),
        ("interrupt_reissue_allowed_resealed",
         lambda b: (b["samples"]["interrupt"]["job"].update({"same_envelope_reissue_permitted": True}),
                    reseal(b["samples"]["interrupt"]["job"], "selfhash_sha256"))),
        ("job_global_orphans_clear_resealed",
         lambda b: (b["samples"]["success"]["job"].update({"all_possible_escaped_processes_excluded": True}),
                    reseal(b["samples"]["success"]["job"], "selfhash_sha256"))),
        ("job_fleet_authority_resealed",
         lambda b: (b["samples"]["success"]["job"].update({"fleet_scheduler_authority": True}),
                    reseal(b["samples"]["success"]["job"], "selfhash_sha256"))),
        ("job_production_authority_resealed",
         lambda b: (b["samples"]["success"]["job"].update({"production_authority": "GRANTED"}),
                    reseal(b["samples"]["success"]["job"], "selfhash_sha256"))),
        ("job_false_aider_pid_resealed",
         lambda b: (b["samples"]["success"]["job"].update({"aider_pid": 99999}),
                    reseal(b["samples"]["success"]["job"], "selfhash_sha256"))),
        ("job_reverse_birth_resealed",
         lambda b: (b["samples"]["success"]["job"].update({"aider_birth_us": 1}),
                    reseal(b["samples"]["success"]["job"], "selfhash_sha256"))),
        ("pin_wrong_parent_resealed",
         lambda b: (b["samples"]["success"]["pin"]["aider"].update({"ppid": 3}),
                    reseal(b["samples"]["success"]["pin"], "pin_sha256"))),
        ("pin_authorizes_retry_resealed",
         lambda b: (b["samples"]["success"]["pin"].update({"retry_permitted": True}),
                    reseal(b["samples"]["success"]["pin"], "pin_sha256"))),
        ("model_receipt_false_qa_resealed",
         lambda b: (b["samples"]["success"]["worker_receipt"]["independent_qa"].update({"pass": False}),
                    reseal(b["samples"]["success"]["worker_receipt"], "receipt_sha256"))),
        ("model_receipt_false_calls_resealed",
         lambda b: (b["samples"]["success"]["worker_receipt"].update({"model_invocations_min": 0}),
                    reseal(b["samples"]["success"]["worker_receipt"], "receipt_sha256"))),
        ("model_receipt_paid_api_resealed",
         lambda b: (b["samples"]["success"]["worker_receipt"].update({"additional_api_spend_usd": 1}),
                    reseal(b["samples"]["success"]["worker_receipt"], "receipt_sha256"))),
        ("journal_blind_retry",
         lambda b: b["samples"]["interrupt"]["journal"].update({"unknown_outcome_rule": "RETRY"})),
        ("envelope_paid_budget",
         lambda b: b["samples"]["success"]["envelope"]["budget"].update({"max_cost_usd": 1})),
        ("swapped_task_envelope",
         lambda b: b["samples"]["success"].update({"envelope": copy.deepcopy(b["samples"]["interrupt"]["envelope"])})),
        ("forged_success_claim_without_separate_verify",
         lambda b: b["samples"]["success"]["readback"].update({"separate_worker_verify_pass": False})),
        ("raw_pin_bytes_changed",
         lambda b: b["samples"]["success"].update({"pin_file_sha256": "f" * 64})),
        ("raw_journal_bytes_changed",
         lambda b: b["samples"]["interrupt"].update({"journal_file_sha256": "0" * 64})),
    ]
    rejected = []
    for name, corrupt in cases:
        cloned = copy.deepcopy(evidence)
        corrupt(cloned)
        try:
            assess(cloned)
        except (AssertionError, kernel.Refused, KeyError, TypeError, ValueError):
            rejected.append(name)
        else:
            raise AssertionError("NEGATIVE_EVIDENCE_ACCEPTED:" + name)
    require(len(rejected) == len(cases), "NEGATIVE_TEST_COUNT")
    return rejected


def main():
    parser = argparse.ArgumentParser(description="Read-only Aider Windows Job LAB verifier")
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()
    p = Path(args.evidence)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size < 160000,
            "EVIDENCE_PATH_UNSAFE")
    bundle = json.loads(p.read_text(encoding="utf-8"))
    res = assess(bundle)
    negatives = negative_tests(bundle)
    res["negative_controls_rejected"] = len(negatives)
    res["negative_control_names"] = negatives
    print(json.dumps(res, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ValueError, OSError, TypeError, KeyError, kernel.Refused) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:200],
                          "original_task_retry_allowed": False,
                          "production_authority": "NONE"}))
        raise SystemExit(2)
