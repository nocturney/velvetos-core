#!/usr/bin/env python3
"""Office #612 offline verifier of real local-model worker LAB receipts.

Only reads checked-in evidence, checks exact historic receipts and five negative
controls. NEVER invokes a model, subprocess, scheduler, API, or production writer.
SHA-256 self-seals are integrity checks, not independent digital signatures.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path


SCHEMA = "vf.office-v2.p0-real-model-worker-proof.v1"
SOURCE = "b97dfdee85fdb6f083acf9372cb50b42534ce1e4b16535d395e60a5004bdd430"
TEST = "81134cc5640d34646e2419bcc4c4be737dac1a6ca98b35ba9282bd69fa7b5f60"
SUCCESS = {
    "mac-passed": ("MacMiniOffice.local", "qwen3.5:4b"),
    "mac-reissued": ("MacMiniOffice.local", "qwen3.5:4b"),
    "win-passed": ("Chris", "qwen3.5:9b"),
    "win-final": ("Chris", "qwen3.5:9b"),
}
FAILED = {"mac-failed-first", "mac-harness-failed", "win-harness-failed"}
KILL = "mac-forcedkill"


def digest(obj):
    return hashlib.sha256(json.dumps(
        obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def require(condition, problem):
    if not condition:
        raise AssertionError(problem)


def check_seal(obj):
    given = obj.get("receipt_sha256")
    require(isinstance(given, str) and len(given) == 64
            and digest({k: v for k, v in obj.items() if k != "receipt_sha256"}) == given,
            "RECEIPT_SELF_SEAL_DRIFT")


def check_success(name, obj):
    check_seal(obj)
    expected_host, expected_model = SUCCESS[name]
    require(obj.get("schema") == "velvetos.office-v2.p0-local-model-receipt.v1",
            "SUCCESS_SCHEMA_DRIFT")
    require(obj.get("task_id", "").startswith("p0-")
            and obj.get("host") == expected_host and obj.get("model") == expected_model,
            "TASK_OR_HOST_MODEL_DRIFT")
    require(obj.get("state") == "SUCCEEDED" and obj.get("exit_code") == 0,
            "FALSE_SUCCESS")
    require(obj.get("model_invocations_min") == 1
            and obj.get("exact_model_calls") is None, "MODEL_CALL_UNVERIFIED")
    require(obj.get("additional_api_spend_usd") == 0
            and obj.get("production_authority") == "NONE"
            and obj.get("scheduler_proven") is False
            and obj.get("autonomous_retry") is False
            and obj.get("os_network_sandbox_proven") is False, "AUTHORITY_SPEND_OR_CAPABILITY_DRIFT")
    require(obj.get("changed_paths") == ["slug.py"], "UNEXPECTED_CHANGED_FILES")
    qa = obj.get("independent_qa") or {}
    require(qa.get("pass") is True and qa.get("unit_exit") == 0
            and qa.get("hidden_exit") == 0 and qa.get("unit_3_verified") is True
            and qa.get("hidden_12_verified") is True and qa.get("replay_changed_paths") == ["slug.py"],
            "INDEPENDENT_QA_NOT_PASSED")
    require(qa.get("replay_source_sha256") == obj.get("artifact_sha256"),
            "FRESH_QA_OUTPUT_HASH_MISMATCH")
    require(all(isinstance(obj.get(k), str) and len(obj[k]) == 64 for k in (
            "envelope_sha256", "stdout_sha256", "stderr_sha256",
            "llm_history_sha256", "checkpoint_before_sha256", "checkpoint_after_sha256",
            "receipt_sha256")), "MISSING_OUTPUT_INTEGRITY")
    require(isinstance(obj.get("elapsed_seconds"), (float, int))
            and 0 < obj["elapsed_seconds"] < 200, "UNBOUNDED_ELAPSED")
    start = datetime.fromisoformat(obj["started_at"])
    end = datetime.fromisoformat(obj["finished_at"])
    require(start < end and abs((end-start).total_seconds() - obj["elapsed_seconds"]) < 1,
            "INVALID_TIMING")
    return start, end


def check_failed(name, obj):
    check_seal(obj)
    require(obj.get("schema") == "velvetos.office-v2.p0-local-model-receipt.v1",
            "FAILED_SCHEMA")
    require(obj.get("state") == "INDEPENDENT_QA_FAILED" and obj.get("exit_code") == 0,
            "HISTORICAL_FAILURE_RECLASSIFIED")
    require(obj.get("model_invocations_min") == 1
            and obj.get("independent_qa", {}).get("pass") is False,
            "FAILED_ATTEMPT_FALSE_POSITIVE")
    require(obj.get("checkpoint_after_sha256") is None
            and obj.get("changed_paths") == ["slug.py"], "FAILED_ATTEMPT_EFFECT_MISMATCH")
    if name == "mac-failed-first":
        require(obj["independent_qa"]["unit_exit"] != 0, "MODEL_EDIT_FAILURE_NOT_RETAINED")
    else:
        require(obj["independent_qa"]["unit_exit"] == 0
                and obj["independent_qa"]["hidden_exit"] != 0,
                "HISTORIC_EXTERNAL_QA_HARNESS_BUG_NOT_RETAINED")


def check_kill(obj):
    check_seal(obj)
    require(obj.get("schema") == "vf.office-v2.p0-live-model-agent-sigkill-lab.v1",
            "LIVE_KILL_SCHEMA")
    require(obj.get("host") == "MacMiniOffice.local" and obj.get("model") == "qwen3.5:4b",
            "KILLED_HOST_MODEL_DRIFT")
    require(obj.get("task_id") == "p0-mac-kill-1"
            and obj.get("worker_killed_by_sigkill") is True
            and obj.get("aider_group_killed_by_sigkill") is True
            and obj.get("live_model_executable_seen_before_kill") is True
            and obj.get("live_model_executable_runtime_at_least_seconds") >= 6,
            "NO_REAL_LIVE_AGENT_LOSS")
    require(obj.get("owned_worker_pid", 0) > 0 and obj.get("owned_aider_pid", 0) > 0
            and obj.get("owned_aider_process_group") == obj.get("owned_aider_pid"),
            "NO_OWNED_CHILD_PGID")
    require(obj.get("journal_preserved") is True
            and obj.get("old_final_receipt_absent") is True
            and obj.get("false_success") is False
            and obj.get("retry_exit_code") == 2
            and obj.get("retry_rejected_reason") == "DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY",
            "UNSAFE_LOST_WORKER_RETRY")
    require(obj.get("external_business_effects") == 0
            and obj.get("automatic_model_recovery_proven") is False
            and obj.get("cross_host_failover_proven") is False,
            "KILL_PROOF_OVERCLAIM")
    require(isinstance(obj.get("journal_sha256"), str)
            and len(obj["journal_sha256"]) == 64, "UNKNOWN_JOURNAL_NOT_HASHED")


def assess(evidence):
    require(evidence.get("schema") == SCHEMA, "EVIDENCE_SCHEMA")
    require(evidence.get("authority") == "LAB_LOCAL_MODEL_SYNTHETIC_ONLY_NO_EFFECT",
            "UNAUTHORIZED_MODE")
    fixture = evidence.get("fixture") or {}
    require(fixture.get("source_sha256") == SOURCE
            and fixture.get("unit_tests_sha256") == TEST
            and fixture.get("expected_visible_unittests") == 3
            and fixture.get("expected_hidden_cases") == 12, "BASELINE_NOT_IDENTICAL")
    records = evidence.get("sessions") or {}
    require(set(records) == set(SUCCESS) | FAILED | {KILL}, "EVIDENCE_SET_INCOMPLETE")
    times = {}
    for name in SUCCESS:
        times[name] = check_success(name, records[name])
    for name in FAILED:
        check_failed(name, records[name])
    check_kill(records[KILL])
    kill_at = datetime.fromisoformat(records[KILL]["timestamp_utc"])
    require(kill_at < times["mac-reissued"][0],
            "NEW_TASK_DID_NOT_FOLLOW_LOSS")
    require(records["mac-reissued"]["task_id"] != records[KILL]["task_id"],
            "OLD_UNKNOWN_TASK_BLINDLY_RETRIED")
    # These receipts prove bounded, explicitly dispatched LAB tasks, not fleet automation.
    return {"status": "PASS_SCOPED_LAB",
            "successful_real_model_receipts": len(SUCCESS),
            "historical_non_success_receipts": len(FAILED),
            "forced_live_model_worker_kill": True,
            "explicit_new_local_model_attempt_after_loss": True,
            "automatic_failover_proven": False,
            "production_promotion_allowed": False}


def negatives(evidence):
    cases = []
    for label, edit in (
        ("resealed_false_qa", lambda x: x["sessions"]["mac-passed"]["independent_qa"].update({"pass": False})),
        ("resealed_zero_model_invocation", lambda x: x["sessions"]["win-final"].update({"model_invocations_min": 0})),
        ("resealed_false_production_authority", lambda x: x["sessions"]["win-passed"].update({"production_authority": "PRODUCTION"})),
        ("resealed_fake_live_kill", lambda x: x["sessions"][KILL].update({"false_success": True})),
        ("resealed_blind_reissue", lambda x: x["sessions"]["mac-reissued"].update({"task_id": "p0-mac-kill-1"})),
    ):
        attempt = copy.deepcopy(evidence)
        edit(attempt)
        for name in attempt["sessions"]:
            obj = attempt["sessions"][name]
            obj["receipt_sha256"] = digest({k:v for k,v in obj.items() if k != "receipt_sha256"})
        try:
            assess(attempt)
        except AssertionError:
            cases.append(label)
        else:
            raise AssertionError("UNSAFE_NEGATIVE_CONTROL_ACCEPTED:" + label)
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    a = parser.parse_args()
    ev = json.loads(Path(a.evidence).read_text(encoding="utf-8-sig"))
    result = assess(ev)
    result["negative_controls_rejected"] = len(negatives(ev))
    result["offline_verifier_only"] = True
    result["actual_model_calls_during_verification"] = 0
    result["evidence_file_sha256"] = hashlib.sha256(Path(a.evidence).read_bytes()).hexdigest()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:230]}))
        raise SystemExit(2)
