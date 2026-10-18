#!/usr/bin/env python3
"""#612 read-only fixture-hash/timing/negative-outcome gate.

This validates a sanitized, host-observed sample. It CANNOT authenticate raw
receipts that live on the two machines, provide process isolation or certify a
fleet, Git credential, recovery or model-level speedup. No model, shell, Git
network, external effect or production authority is invoked by this script.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/implementation/office-v2/phase2/p0-612-two-host-same-fixture-throughput-negative-2026-10-10.json"
SCHEMA = "velvetos.office-v2.p0-same-fixture-two-physical-host-observation.v1"
MAIN = "823caed3ed04893f462009b28571afea09eb1e8c"
WORKER = "9ed3f0b495008c44249867c87b664aa7b75178049b1c7d53f37d557bd12cfafb"
SHA = re.compile(r"[0-9a-f]{64}\Z")
FIXTURE_PINS = {
    "source_seed_sha256": "49db6ebbd729b352f6ad23db29081d32968fe1b5d2b63e1d73928b997b9b56f1",
    "visible_test_sha256": "55ada6c9ae4bca3cba1633010795dae2e02dabed3071aca56ea1fdcede17d668",
    "hidden_qa_sha256": "fd3b286041bfe835416ab14e89dc6b56195c807f01bcc9bbe843095c463009db",
    "prompt_sha256": "4b97af9e8df68441cb1381729471b7315308e97e0a7efc917a0fc59954cd592e",
}
WIN_CODE = "72056d73f9781ddb3c8c07bf7a5df4710eefbe70f6d17706aac8c8c05450bc70"
MAC_CODE = "b2ec92fed514a5e0e37aeca31155fe0d04cdfde70a3d46fafeeb9a09b0ef1ccb"
EXPECTED = {
    "win-a1": ("Chris", "solo", 91.638, WIN_CODE,
               "c63a725920dbfc5466ae429ea012fbbf18f2fdec163a01c3ec075cbef498a08d"),
    "mac-b1": ("MacMiniOffice.local", "solo", 62.343, MAC_CODE,
               "e849841e6e7673c174f25cef1b89cf13274e8121f884f8d5ac6ce7c2cc691974"),
    "win-b1": ("Chris", "parallel", 41.877, WIN_CODE,
               "fae125b872378704c4e327546e2a0644fe75e114fe16d83e8bc1ac45a81bc007"),
    "mac-c1": ("MacMiniOffice.local", "parallel", 60.451, MAC_CODE,
               "a52459ee3511dcefacae6b063fb27f40f83c0653dd148266f58c778bb27b760e"),
}


class Refused(Exception):
    pass


def require(value, reason):
    if not value:
        raise Refused(reason)


def sha64(value):
    return isinstance(value, str) and bool(SHA.fullmatch(value))


def parse_utc(value):
    # Windows .NET emits seven fractional decimal places; Python 3.9's
    # fromisoformat accepts up to six. The discarded 100-ns digit cannot
    # affect our explicitly millisecond-rounded overlap observation.
    match = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,7}))?Z", value or "")
    require(match is not None, "INVALID_EXACT_UTC_TIMESTAMP")
    fraction = (match.group(2) or "")[:6].ljust(6, "0")
    return datetime.fromisoformat(match.group(1) + "." + fraction + "+00:00")


def read(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink()
            and 0 < path.stat().st_size < 1024 * 1024, "UNSAFE_REPORT_FILE")
    return json.loads(path.read_text(encoding="utf-8"))


def validate(report):
    require(type(report) is dict and report.get("schema") == SCHEMA
            and report.get("canonical_main_start_sha") == MAIN
            and report.get("worker_source_sha256") == WORKER
            and report.get("scope") == "LOCAL_SYNTHETIC_MODEL_NO_PRODUCTION_EFFECT"
            and report.get("owner_issue") ==
            "https://github.com/nocturney/velvetos-core/issues/612",
            "FALSE_REPORT_OR_BASE")
    fixture = report.get("fixture")
    require(type(fixture) is dict and
            fixture.get("fixture_id") == "canonical-tag-v1" and
            fixture.get("prompt_profile") == "PUBLIC_SPEC_STATE_MACHINE_V2"
            and all(fixture.get(k) == v for k, v in FIXTURE_PINS.items())
            and fixture.get("timeout_seconds") == 175
            and type(fixture.get("max_attempts")) is int
            and fixture["max_attempts"] == 1
            and type(fixture.get("incremental_paid_api_spend_usd")) is int
            and fixture["incremental_paid_api_spend_usd"] == 0,
            "FIXTURE_TASK_CONTRACT_CHANGED")
    rows = report.get("samples")
    require(type(rows) is list and len(rows) == 4
            and [r.get("id") for r in rows] == list(EXPECTED),
            "NOT_FOUR_UNIQUE_ORDERED_ATTEMPTS")
    for row in rows:
        name = row["id"]
        host, phase, duration, artifact, receipt = EXPECTED[name]
        win = host == "Chris"
        require(row.get("physical_host") == host and row.get("wave") == phase
                and type(row.get("host_shell_wall_seconds")) is float
                and row["host_shell_wall_seconds"] == duration
                and row.get("artifact_sha256") == artifact
                and row.get("changed_paths") == ["canonical_tag.py"]
                and row.get("production_authority") is False
                and row.get("original_attempt_retried") is False
                and type(row.get("additional_api_spend_usd")) is int
                and row["additional_api_spend_usd"] == 0,
                "SAMPLE_IDENTITY_OR_COST_FALSE_" + name)
        require(row.get("model") == ("qwen3.5:9b" if win else "qwen3.5:4b")
                and row.get("execution_principal") ==
                ("NT_AUTHORITY_SYSTEM_SESSION_0" if win else "chris_UID_501")
                and row.get("base_sha") == (
                    "215cfe493eb50070aa09699cfb9f6b41c1d2c8b4" if win
                    else "c4e9417e7a2a4303260e5f08253be4cd5cbe2529"),
                "MODEL_HOST_BASE_OR_OS_IDENTITY_" + name)
        for field in ("envelope_raw_sha256", "model_digest"):
            require(sha64(row.get(field)), "SOURCE_PIN_ABSENT_" + field)
        require(row["model_digest"] == (
                "56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90"
                if win else
                "7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13"),
                "MODEL_DIGEST_DRIFT_" + name)
        try:
            when = parse_utc(row["observed_start_utc"])
        except (TypeError, ValueError, KeyError):
            raise Refused("BAD_OBSERVED_TIME_" + name)
        require(when.tzinfo is not None, "UNZONED_OBSERVED_TIME")
        if win:
            require(row.get("qa_result") == "FAILED_INDEPENDENT_QA_NO_SUCCESS"
                    and row.get("visible_tests_passed") is False
                    and row.get("hidden_tests_passed") is False
                    and row.get("visible_exit") == row.get("hidden_exit") == 1
                    and row.get("worker_elapsed_seconds") is None
                    and row.get("sealed_audit_sha256") == receipt
                    and row.get("original_running_journal_preserved") is True
                    and row.get("final_success_receipt_absent") is True
                    and sha64(row.get("audit_raw_sha256"))
                    and sha64(row.get("journal_raw_sha256")),
                    "FALSE_WINDOWS_QA_SUCCESS_" + name)
        else:
            require(row.get("qa_result") == "SUCCEEDED_INDEPENDENT_QA"
                    and row.get("visible_tests_passed") is True
                    and row.get("hidden_tests_passed") is True
                    and row.get("visible_exit") == row.get("hidden_exit") == 0
                    and type(row.get("worker_elapsed_seconds")) is float
                    and row["worker_elapsed_seconds"] > 0
                    and row.get("sealed_worker_receipt_sha256") == receipt
                    and row.get("model_invocations_min") == 1
                    and row.get("model_invocations_exact") is None
                    and sha64(row.get("receipt_raw_sha256"))
                    and sha64(row.get("kernel_pin_raw_sha256")),
                    "FALSE_MAC_QA_OR_MODEL_COUNT_" + name)
    failure = report.get("excluded_preflight_failure")
    require(type(failure) is dict and failure.get("id") == "mac-a1"
            and failure.get("reason") == "PSUTIL_REQUIRED_NO_FALLBACK_TO_UNPINNED_PS"
            and failure.get("duration_seconds") == 1.386
            and failure.get("kernel_pin_written") is False
            and failure.get("final_receipt_present") is False
            and failure.get("original_attempt_retried") is False
            and failure.get("model_invocations_exact") is None
            and sha64(failure.get("original_journal_raw_sha256")),
            "FALSE_PRE_PIN_SUCCESS_OR_CALL_COUNT")
    lim = report.get("limits")
    expected_limits = {
        "distinct_physical_hosts": 2,
        "qa_accepted_windows": 0,
        "qa_accepted_mac": 2,
        "distinct_successful_artifact_hashes": 1,
        "concurrent_wave_qa_accepted_total": 1,
        "repeated_source_artifact_is_not_new_algorithm": True,
        "percentile_p95_estimate_admissible": False,
        "throughput_speedup_proven": False,
        "autonomous_recovery_proven": False,
        "autonomous_agent_git_pr_proven": False,
        "git_credential_isolation_verified": False,
        "os_isolation_for_generated_code_verified": False,
        "untrusted_code_executed_as_system_on_windows": True,
        "model_server_resource_peak_measured": False,
        "full_end_to_end_cost_measured": False,
        "exact_model_token_count_known": False,
        "original_raw_receipts_replayable_inside_ci": False,
        "independent_host_readback_observed": True,
        "all_historical_unknown_journals_preserved": True,
        "local_model_only": True,
        "production_authority": False,
    }
    require(type(lim) is dict and
            all(type(lim.get(k)) is type(v) and lim[k] == v
                for k, v in expected_limits.items()), "FALSE_P0_ACCEPTANCE_OR_QUALITY_CLAIM")
    # POSIX and Windows start times were read from separately observed hosts;
    # apparent overlap does NOT prove a shared scheduler or stable p95.
    a, b = rows[2], rows[3]
    aw = parse_utc(a["observed_start_utc"]).timestamp()
    bw = parse_utc(b["observed_start_utc"]).timestamp()
    overlap = round(max(0.0, min(aw + a["host_shell_wall_seconds"],
                                  bw + b["host_shell_wall_seconds"]) -
                           max(aw, bw)), 3)
    require(overlap == 36.195, "OVERLAP_WINDOW_NOT_CORROBORATED")
    return {"status": "PASS_SCOPED_SAMPLE_NOT_P0_ADMISSION",
            "physical_hosts": 2, "model_attempts_qa_successful": 2,
            "windows_qa_successes": 0, "mac_qa_successes": 2,
            "distinct_accepted_source_hashes": 1,
            "parallel_overlap_seconds_observed": overlap,
            "statistical_speedup_proven": False,
            "os_isolation_proven": False, "autonomous_git_sink_proven": False,
            "production_authority": False,
            "raw_host_receipt_bytes_authenticated_by_ci": False}


def selftest():
    original = read(REPORT)
    outcome = validate(original)
    cases = [
        ("false_windows_green", lambda x: x["samples"][0].update(qa_result="SUCCEEDED")),
        ("false_mac_hidden", lambda x: x["samples"][1].update(hidden_tests_passed=False)),
        ("fake_two_solutions", lambda x: x["limits"].update(distinct_successful_artifact_hashes=2)),
        ("false_parallel_green", lambda x: x["limits"].update(concurrent_wave_qa_accepted_total=2)),
        ("promote_p0", lambda x: x["limits"].update(production_authority=True)),
        ("git_sink_proven", lambda x: x["limits"].update(git_credential_isolation_verified=True)),
        ("os_isolated", lambda x: x["limits"].update(os_isolation_for_generated_code_verified=True)),
        ("speedup_claim", lambda x: x["limits"].update(throughput_speedup_proven=True)),
        ("false_p95", lambda x: x["limits"].update(percentile_p95_estimate_admissible=True)),
        ("model_tokens_claim", lambda x: x["limits"].update(exact_model_token_count_known=True)),
        ("false_preflight_receipt", lambda x: x["excluded_preflight_failure"].update(final_receipt_present=True)),
        ("preflight_retried", lambda x: x["excluded_preflight_failure"].update(original_attempt_retried=True)),
        ("new_fixture", lambda x: x["fixture"].update(prompt_sha256="0" * 64)),
        ("same_task_id", lambda x: x["samples"][2].update(id="win-a1")),
        ("false_os_host", lambda x: x["samples"][1].update(physical_host="Chris")),
        ("wrong_time", lambda x: x["samples"][3].update(observed_start_utc="2026-10-10T20:32:00Z")),
        ("false_windows_audit", lambda x: x["samples"][2].update(sealed_audit_sha256="0" * 64)),
        ("untrusted_privilege_hidden", lambda x: x["limits"].update(untrusted_code_executed_as_system_on_windows=False)),
    ]
    for name, mutate in cases:
        row = copy.deepcopy(original)
        mutate(row)
        try:
            validate(row)
        except Refused:
            pass
        else:
            raise AssertionError("FALSE_ACCEPTED_" + name)
    return dict(outcome, tests=len(cases)+1, negatives=len(cases),
                model_calls_during_validator=0,
                external_writes_during_validator=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("verify", "selftest"))
    args = ap.parse_args()
    result = selftest() if args.command == "selftest" else validate(read(REPORT))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refused, ValueError, KeyError, TypeError, OSError, AssertionError) as e:
        print(json.dumps({"status": "FAIL_CLOSED",
                          "reason": str(e)[:160], "production_authority": False},
                         sort_keys=True))
        raise SystemExit(2)
