#!/usr/bin/env python3
"""#604 offline audit of an exact owned idle Dagu LAB shutdown receipt.

Pure verification of a historical, operator-observed cleanup. CI MUST NOT
kill/stop workers, alter services, launch models, access machines or requeue.
An unsigned JSON receipt is a historical witness, not ownership authority.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import json
from pathlib import Path

import vf_office_v2_604_dagu_raw_log_audit as original

EVIDENCE = original.P2 / "p0-dagu-fleet-idle-cleanup-2026-10-10.json"
SCHEMA = "velvetos.office-v2.fleet.dagu-idle-lab-cleanup.v0"
EXPECTED = {
    ("Chris Windows", 49084): ("vf604-win-1423z", "Stop-Process"),
    ("MacMiniOffice.local", 14840): ("vf604-mac-1423z", "SIGTERM"),
    ("MacMiniOffice.local", 15073): ("vf604-fair-1423z", "SIGTERM"),
    ("MacMiniOffice.local", 15248): ("vf604-loss-1423z", "SIGTERM"),
    ("MacMiniOffice.local", 14782): ("vf604-synthetic-coordinator", "SIGTERM"),
}


def validate(v: dict):
    original.need(type(v) is dict and v.get("schema") == SCHEMA
                  and v.get("status") ==
                  "SCOPED_IDLE_DAGU_604_PILOT_STOPPED_EVIDENCE_PRESERVED_NOT_PRODUCTION"
                  and v.get("date_utc") == "2026-10-10",
                  "CLEANUP_RECEIPT_SCOPE_INVALID")
    scope = v.get("scope") or {}
    original.need(scope.get("lab_name") == "fleet-placement-20261008-1423z"
                  and scope.get("version") == "Dagu 2.18.2"
                  and scope.get("issue") ==
                  "https://github.com/nocturney/velvetos-core/issues/604"
                  and scope.get("other_fleet_services_touched") is False
                  and scope.get("remote_desktop_bridge_touched") is False
                  and scope.get("source_files_deleted") is False
                  and scope.get("existing_worker_sched_authority_promoted") is False,
                  "CLEANUP_SCOPE_OVERSTATED")
    pre = v.get("preflight") or {}
    original.need(
        pre.get("coordinator_host") == "MacMiniOffice.local"
        and pre.get("model_or_business_jobs") == 0
        and pre.get("active_dagu_process_store") == []
        and pre.get("history_total") == 14
        and pre.get("history_terminal_succeeded") == 14
        and pre.get("history_nonterminal") == 0
        and pre.get("queue_nonlock_items") == 0
        and pre.get("distributed_active_nonlock_items") == 0
        and pre.get("exclusive_synthetic_dags_only") is True
        and pre.get("last_history_is_not_provider_lease") is True,
        "IDLE_GATE_NOT_RECORDED")
    stopped = v.get("stopped")
    original.need(type(stopped) is list and len(stopped) == len(EXPECTED),
                  "EXACT_STOPPED_WORKER_SET_REQUIRED")
    seen = set()
    for row in stopped:
        original.need(type(row) is dict, "STOPPED_ROW_INVALID")
        key = (row.get("host"), row.get("pid"))
        original.need(key in EXPECTED and key not in seen,
                      "WRONG_OR_DUPLICATE_WORKER")
        seen.add(key)
        want_role, stop_style = EXPECTED[key]
        born = row.get("birth_local")
        original.need(
            row.get("role") == want_role
            and row.get("path_scope", "").startswith(
                "fleet-placement-20261008-1423z/")
            and isinstance(born, str)
            and born.startswith("2026-10-08T17:")
            and born.endswith("+03:00")
            and (stop_style in row.get("method", ""))
            and "exact PID/birth" in row.get("method", "")
            and row.get("readback_absent") is True,
            "PROCESS_IDENTITY_OR_SAFE_STOP_NOT_PROVEN")
    original.need(seen == set(EXPECTED), "SOME_PROCESS_NOT_RECORDED")

    post = v.get("postcondition") or {}
    for name in ("mac_utc", "windows_utc", "windows_cross_host_port_check_utc"):
        s = post.get(name)
        original.need(type(s) is str and
                      original.timestamp(s).date().isoformat()
                      == "2026-10-10", "POST_READBACK_TIMESTAMP_INVALID_" + name)
    original.need(
        post.get("mac_all_exact_pids_absent") is True
        and post.get("windows_exact_worker_pid_absent") is True
        and post.get("windows_lab_worker_process_count") == 0
        and post.get("mac_local_port_31810_listeners") == 0
        and post.get("mac_coordinator_port_31557_listeners") == 0
        and post.get("windows_tcp_to_mac_31557_connected") is False
        and post.get("original_mac_lab_audit_source_sha256_unchanged")
            == original.SOURCE_HASHES
        and post.get("untouched_active_windows_pid_checks") ==
            {"Ollama_43272": True, "Maya_24392": True}
        and post.get("current_production_fleet_state_not_claimed") is True,
        "POST_SHUTDOWN_ABSENCE_OR_DATA_INTEGRITY_MISSING")
    example_paths = post.get(
        "accidental_dagu_readonly_cli_bootstrap_examples_removed_after_exact_creation_time_six_file_allowlist")
    original.need(
        example_paths == [
            r"C:\Users\Chris\dags",
            r"D:\Velvet\Tools\ComputerUseFleet\DaguPilot\v2.18.2\fleet-placement-20261008-1423z\win-worker-home\dags"],
        "CLI_BOOTSTRAP_SIDE_EFFECT_NOT_RECONCILED")
    for k in ("canonical_provider_lease", "provider_atomic_monotonic_fencing",
              "full_worker_loss_recovery", "automatic_retry_approved",
              "worker_pid_reuse_impossible", "production_authority",
              "customer_print_social_effects", "host_reboot_or_global_service_mutation",
              "new_scheduler_or_daemon_started", "subsequent_new_lab_run"):
        original.need((v.get("nonclaims") or {}).get(k) is False,
                      "FALSE_CLEANUP_AUTHORITY_" + k)
    return {"status":"PASS_HISTORICAL_SCOPED_LAB_CLEANUP",
            "stopped_exact_synthetic_process_count":5,
            "historical_source_files_preserved":True,
            "windows_mac_absence_readback_recorded":True,
            "production_authority":False,
            "provider_lease":False,"model_calls":0,"effect_writes":0}


def selftest(data):
    validate(data)
    cases = ["original_scoped_clean_stop_receipt_valid"]
    changes = [
        ("wrong_lifecycle", lambda x:x.update(status="PRODUCTION_READY")),
        ("wrong_id", lambda x:x["stopped"][0].update(pid=49085)),
        ("duplicate_id", lambda x:x["stopped"][0].update(pid=14840,host="MacMiniOffice.local")),
        ("wrong_host", lambda x:x["stopped"][3].update(host="Chris Windows")),
        ("wrong_method", lambda x:x["stopped"][0].update(method="external process force-clean")),
        ("false_absence", lambda x:x["stopped"][0].update(readback_absent=False)),
        ("nonidle", lambda x:x["preflight"].update(history_nonterminal=1)),
        ("queued", lambda x:x["preflight"].update(queue_nonlock_items=1)),
        ("extra_dag", lambda x:x["preflight"].update(exclusive_synthetic_dags_only=False)),
        ("still_mac", lambda x:x["postcondition"].update(mac_all_exact_pids_absent=False)),
        ("still_windows", lambda x:x["postcondition"].update(windows_lab_worker_process_count=1)),
        ("remote_listening", lambda x:x["postcondition"].update(windows_tcp_to_mac_31557_connected=True)),
        ("source_drifts", lambda x:x["postcondition"]["original_mac_lab_audit_source_sha256_unchanged"].update({"manifest.json":"0"*64})),
        ("fake_lease", lambda x:x["nonclaims"].update(canonical_provider_lease=True)),
        ("fake_fence", lambda x:x["nonclaims"].update(provider_atomic_monotonic_fencing=True)),
        ("fake_recovery", lambda x:x["nonclaims"].update(full_worker_loss_recovery=True)),
        ("fake_prod", lambda x:x["nonclaims"].update(production_authority=True)),
        ("global_mutation", lambda x:x["nonclaims"].update(host_reboot_or_global_service_mutation=True)),
        ("false_untouched", lambda x:x["scope"].update(other_fleet_services_touched=True)),
        ("example_artifacts", lambda x:x["postcondition"].update(accidental_dagu_readonly_cli_bootstrap_examples_removed_after_exact_creation_time_six_file_allowlist=[])),
    ]
    for label, mutate in changes:
        x = copy.deepcopy(data)
        mutate(x)
        try:
            validate(x)
        except original.Refused:
            cases.append(label + "_DENIED")
        else:
            raise AssertionError("FALSE_SUCCESS_" + label)
    original.need(len(cases) == 21, "CLEANUP_TEST_COUNT_CHANGED")
    return {"status":"PASS_OFFLINE", "tests":len(cases),
            "stopped_processes_by_test":0,"git_effects":0,
            "production_authority":False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("verify","selftest"))
    args = ap.parse_args()
    first = original.load_strict_json(original.EVIDENCE)
    original.verify_json(first)
    receipt = original.load_strict_json(EVIDENCE)
    answer = validate(receipt) if args.mode == "verify" else selftest(receipt)
    print(json.dumps(answer, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (original.Refused, AssertionError, ValueError, KeyError,
            AttributeError, TypeError, OSError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:180],
                          "git_effects":0,"stopped_processes_by_test":0},sort_keys=True))
        raise SystemExit(2)
