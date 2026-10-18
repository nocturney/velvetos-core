#!/usr/bin/env python3
"""Office P0 #612: pure offline validation of five Mac local-model LAB receipts.

Does not run Ollama, Aider, OS probes, workers, scheduling, network or effects.
Input is a sanitized historical summary; original raw bytes stay on the host.
Pinned raw hashes detect changes after recordkeeping, not deliberate forgery.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import re

SCHEMA = "velvetos.office-v2.p0-mac-single-model-repeat-evidence.v0"
MODEL = "qwen3.5:4b"
MODEL_PIN = "7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13"
SOURCE = "7b4cb176c9c66351f9658c08589f45ec94d50c2a8b6450fe8e5cb1d8f09d86f7"
FIXTURE = "a1b6687cb6da7631b954077911b8c4986f8547c1197b613a1000bb13a274a47d"
EXPECTED_ARTIFACT = "456f89bec0af23e6287e88956b8b85e992d4926b89e9613238bee7f77302ab45"
EXPECTED = (
    ("01", "192e9f966b7d6b99d639b81529c899da2082f1d0", 44.632,
     "fa317f0a0d51842cf0d6d881deabf707f88cdb5384886e22d7ec59e0b9039754",
     "eba7a0d681dff3e69c710e1c0eb1cf7ac27a9af72ae57d7c843465c146e0bf32",
     "33168006d6814f3ae4f981d531d1dcd13855f1d7a1260d81a37b219325b6d736",
     "27e2ca7a5d768e9e45a12f25e438776e4fa0edd76ba6811a1d3c9e3f657c99bf"),
    ("02", "88754762fc6e994d0e2f94a9612a8d324d3f3fcc", 47.229,
     "7878d9b368d2630f3baaf2dd5e4b78df76b9d657a09553a9551e75330bc43028",
     "efe858fbc61110f0b4612552543435e7272dc92c7095b5c7c3f2c13d794acbbd",
     "a3ff2ab27d4265759b73e3be5121d0b7bfadf0d3a076093d586e59522c65f3ea",
     "3b2af503b8d1bb14725a81473db25ff546b7700ea39618c48fc87605062363ef"),
    ("03", "e285a0e3b09b3bdec55ecfe349943061916e4cf1", 46.331,
     "5d83fb4781a573473bf8ff49aecc18101d2c400c745dc2a72ad15142f6cbd985",
     "c37e8a86c6cc3932c43327946e830181faacb551a8320879f5760eac47b4bedf",
     "4bc380b5c56b3f187d93a7663603b491920904d441e0f016c934b3ed6e84b164",
     "16c00df928683c998a2b29863e233d4b808933737914ebf1e7a745d19a9bb7e2"),
    ("04", "4f83c1540b9144746a2cc263cd518604b38b5dcf", 45.228,
     "7110a5c2325f33e45966aef6b62bcf9b92288539dbc82ed6ebd8094f83bfa2dc",
     "69eb52c83397728299029befee54435e72d0f112427f54956af3b11162e93e74",
     "5f00549183a04fd9f8f51cd0761b625a44dd372970ae0946377eba34898f7e14",
     "b69d369f579c41ebec737073976d2a41e22c6a6da8a4e8d5428e3652a4516c8b"),
    ("05", "28d20d8d47a1f33d1749ffaba32b2c5c1a13467b", 48.576,
     "9fa142a5a154683d9c935b246c24f77287e3fbc6788d16654d1226faed2eb560",
     "7aa128fa00f0762b0b91eb5f1a7ddf746589cee828190a7a101c0ca74459bc67",
     "636af041e9d6425e4c7ff0c779fbb502f97831808680ffd2ddc94d2adc12abeb",
     "33b2e71f701aead30d09d48982919f654c186f7662d177e1db76579ea8c9a73c"),
)


class Refused(Exception):
    pass


def require(ok, why):
    if not ok:
        raise Refused(why)


def sha(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def verify(data):
    require(isinstance(data, dict) and data.get("schema") == SCHEMA and
            data.get("issue") == "https://github.com/nocturney/velvetos-core/issues/612" and
            data.get("status") ==
            "PASS_FIVE_INDEPENDENT_REAL_LOCAL_MODEL_LAB_FIXES_SINGLE_HOST_ONLY",
            "SCHEMA_SCOPE_OR_STATUS_DRIFT")
    source = data.get("source") or {}
    require(source.get("repository") == "nocturney/velvetos-core" and
            source.get("host") == "MacMiniOffice.local" and
            source.get("model") == MODEL and source.get("model_digest") == MODEL_PIN
            and source.get("worker_source_sha256") == SOURCE
            and source.get("fixture_source_sha256") == FIXTURE and
            source.get("executed_main_snapshot") ==
            "b1147951747ca38550fee9da118e6b51447d0215",
            "WORKER_MODEL_OR_SOURCE_PIN_DRIFT")
    rows = data.get("attempts")
    require(isinstance(rows, list) and len(rows) == len(EXPECTED),
            "EXACT_FIVE_REAL_RECEIPTS_REQUIRED")
    tasks, bases, branches, receipts, pins = set(), set(), set(), set(), set()
    secs = []
    for row, (n, base, elapsed, receipt_selfhash, raw_env, raw_rec, raw_pin) in zip(rows, EXPECTED):
        require(isinstance(row, dict), "RECEIPT_NOT_OBJECT")
        tid = "p0-repeat-metrics-mac-20261009-" + n
        require(row.get("task_id") == tid and row.get("base_sha") == base
                and row.get("branch") == "lab-p0-agent-" + tid
                and row.get("state") == "SUCCEEDED"
                and row.get("model") == MODEL
                and row.get("model_digest") == MODEL_PIN
                and row.get("receipt_selfhash") == receipt_selfhash
                and row.get("raw_envelope_sha256") == raw_env
                and row.get("raw_receipt_sha256") == raw_rec
                and row.get("raw_kernel_pin_sha256") == raw_pin,
                "HISTORICAL_TASK_ID_OR_HASH_DRIFT_" + n)
        value = row.get("elapsed_seconds")
        require(type(value) in (int, float) and value == elapsed and value > 0,
                "ELAPSED_TIME_DRIFT_" + n)
        require(row.get("artifact_sha256") == EXPECTED_ARTIFACT
                and sha(row.get("checkpoint_after_sha256"))
                and row.get("independent_separate_worker_verify") == "PASS",
                "SOURCE_OR_INDEPENDENT_QA_DRIFT_" + n)
        qa = row.get("qa") or {}
        require(qa.get("pass") is True and qa.get("unit_3_verified") is True
                and qa.get("hidden_12_verified") is True
                and qa.get("changed_paths") == ["slug.py"]
                and sha(qa.get("hidden_stdout_sha256")),
                "HIDDEN_QA_FALSE_OR_MISSING_" + n)
        require(type(row.get("model_invocations_min")) is int
                and row["model_invocations_min"] == 1
                and row.get("exact_model_calls") is None
                and row.get("local_model_usage_tokens") is None
                and type(row.get("additional_api_spend_usd")) is int
                and row["additional_api_spend_usd"] == 0,
                "MODEL_OR_PAID_TOKENS_CLAIM_" + n)
        tasks.add(tid); bases.add(base); branches.add(row["branch"])
        receipts.add(raw_rec); pins.add(raw_pin); secs.append(value)
    require(len(tasks) == len(bases) == len(branches) == len(receipts) == len(pins) == 5,
            "DUPLICATE_ATTEMPT_OR_PROOF")
    stats = data.get("statistics") or {}
    ordered = sorted(secs)
    require(stats.get("n") == 5 and type(stats.get("verified_success_count")) is int
            and stats["verified_success_count"] == 5
            and stats.get("observed_seconds_in_task_order") == secs
            and stats.get("min_seconds") == ordered[0]
            and stats.get("max_seconds") == ordered[-1]
            and stats.get("median_seconds") == ordered[2]
            and stats.get("mean_seconds") == round(sum(secs)/len(secs), 3)
            and stats.get("p95_nearest_rank_seconds") ==
                ordered[math.ceil(len(ordered) * .95) - 1]
            and stats.get("percentile_basis") ==
                "NEAREST_RANK_N_5_EXPLORATORY_ONLY_NOT_RELIABLE_P95"
            and stats.get("qa_visible_each") == "3/3"
            and stats.get("qa_hidden_each") == "12/12"
            and stats.get("samples_are_sequential") is True,
            "FALSE_METRIC_OR_PERCENTILE")
    limits = data.get("limits") or {}
    require(type(limits.get("distinct_physical_hosts")) is int
            and limits["distinct_physical_hosts"] == 1
            and type(limits.get("distinct_worktrees")) is int
            and limits["distinct_worktrees"] == 5
            and type(limits.get("actual_new_task_envelopes")) is int
            and limits["actual_new_task_envelopes"] == 5
            and type(limits.get("paid_api_spend_usd")) is int
            and limits["paid_api_spend_usd"] == 0,
            "HOST_COUNT_OR_SPEND_INFLATED")
    for key in ("original_unknown_retried", "all_orphan_descendants_excluded",
                "autonomous_recovery_proven", "concurrent_workers_proven",
                "cross_host_throughput_proven", "production_writer",
                "scheduler_authority", "total_exact_model_calls_known",
                "exact_token_counts_available", "ram_vram_time_series_available",
                "operator_minutes_quantified", "percentiles_statistically_robust"):
        require(limits.get(key) is False, "FALSE_AUTHORITY_OR_CONFIDENCE_" + key)
    return {"status": "PASS_OFFLINE_HISTORICAL_RECORD_VALIDATED_NOT_LIVE_REPLAY",
            "samples": len(secs), "independent_worker_verifies_reported": 5,
            "median_seconds": ordered[2], "sample_p95_nearest_rank_seconds": ordered[-1],
            "model_calls_during_verification": 0,
            "automatic_retries_authorized": False,
            "production_or_scheduler_authority": False,
            "statistically_robust_p95": False}


def selftest(data):
    verify(data)
    checks = ["valid_five_sequential_claims_offline_only"]
    cases = [
        ("wrong_scope", lambda x: x.update(status="PASS_PRODUCTION")),
        ("wrong_host", lambda x: x["source"].update(host="Chris")),
        ("wrong_model", lambda x: x["source"].update(model="qwen3.5:9b")),
        ("wrong_source", lambda x: x["source"].update(worker_source_sha256="0"*64)),
        ("missing_sample", lambda x: x["attempts"].pop()),
        ("reuse_base", lambda x: x["attempts"][1].update(base_sha=x["attempts"][0]["base_sha"])),
        ("replace_receipt", lambda x: x["attempts"][0].update(raw_receipt_sha256="0"*64)),
        ("replace_birth_pin", lambda x: x["attempts"][1].update(raw_kernel_pin_sha256="0"*64)),
        ("fake_unit", lambda x: x["attempts"][2]["qa"].update(unit_3_verified=False)),
        ("fake_hidden", lambda x: x["attempts"][3]["qa"].update(hidden_12_verified=False)),
        ("fake_changed_path", lambda x: x["attempts"][3]["qa"].update(changed_paths=["tests/test_slug.py"])),
        ("unsupported_success", lambda x: x["attempts"][4].update(state="UNKNOWN_OUTCOME")),
        ("improper_model_count", lambda x: x["attempts"][0].update(exact_model_calls=5)),
        ("invented_tokens", lambda x: x["attempts"][0].update(local_model_usage_tokens=1000)),
        ("paid_api", lambda x: x["attempts"][0].update(additional_api_spend_usd=1)),
        ("fake_artifact", lambda x: x["attempts"][0].update(artifact_sha256="0"*64)),
        ("fake_p50", lambda x: x["statistics"].update(median_seconds=3)),
        ("fake_p95", lambda x: x["statistics"].update(p95_nearest_rank_seconds=35)),
        ("fake_mean", lambda x: x["statistics"].update(mean_seconds=46.4)),
        ("inflated_hosts", lambda x: x["limits"].update(distinct_physical_hosts=2)),
        ("false_auto_recovery", lambda x: x["limits"].update(autonomous_recovery_proven=True)),
        ("false_distributed_worker", lambda x: x["limits"].update(concurrent_workers_proven=True)),
        ("false_authority", lambda x: x["limits"].update(scheduler_authority=True)),
        ("false_p95_significance", lambda x: x["limits"].update(percentiles_statistically_robust=True)),
    ]
    for label, change in cases:
        fake = copy.deepcopy(data)
        change(fake)
        try:
            verify(fake)
        except Refused:
            checks.append(label + "_rejected")
        else:
            raise AssertionError("FALSE_HISTORICAL_MEASUREMENT_ACCEPTED:" + label)
    require(len(checks) == 25, "SELFTEST_COUNT_DRIFT")
    return {"status": "PASS_OFFLINE", "tests": len(checks), "cases": checks,
            "model_invocations": 0, "scheduler_authority": False,
            "automatic_retries": 0, "production_effects": 0,
            "statistically_robust_p95": False}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("selftest", "verify"):
        sub.add_parser(name).add_argument("--evidence", required=True)
    args = parser.parse_args()
    path = Path(args.evidence)
    require(path.is_file() and not path.is_symlink() and
            0 < path.stat().st_size <= 1024*1024, "UNSAFE_OR_ABSENT_EVIDENCE")
    value = json.loads(path.read_text(encoding="utf-8"))
    outcome = selftest(value) if args.mode == "selftest" else verify(value)
    print(json.dumps(outcome, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refused, ValueError, OSError, KeyError, TypeError, AssertionError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:180],
                          "no_model_calls": True, "no_automatic_retries": True}))
        raise SystemExit(2)
