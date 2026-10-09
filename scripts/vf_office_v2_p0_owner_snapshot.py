#!/usr/bin/env python3
"""#612 read-only observation of historical LAB worker PIDs (NOT ownership proof).

Inputs: exact canonical LAB envelope + external signed-by-hash forced-loss
observation. No signals, no calls to Aider/Ollama, no new task, no scheduler.
Absence of an old PID does NOT prove no descendant is alive or authorize retry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform
import subprocess
import tempfile
from datetime import datetime, timezone

import vf_office_v2_p0_unknown_reconcile as reconcile

SCHEMA = "vf.office-v2.p0-owner-snapshot-v0"
KILL_SCHEMA = "vf.office-v2.p0-live-model-agent-sigkill-lab.v1"
MAX_PROCESS_TEXT = 5_000_000


def require(ok, why):
    if not ok:
        raise reconcile.Refused(why)


def validate(env, killed):
    reconcile.checked_envelope(env)
    require(killed.get("schema") == KILL_SCHEMA, "KILL_OBSERVATION_SCHEMA")
    require(killed.get("task_id") == env["task_id"] and
            killed.get("envelope_sha256") == reconcile.digest(env) and
            killed.get("host") == env["host"], "KILL_OBSERVATION_NOT_BOUND")
    require(killed.get("model") == env["executor"]["model"] and
            killed.get("model_digest") == env["executor"]["model_digest"],
            "KILL_MODEL_NOT_BOUND")
    seal = killed.get("receipt_sha256")
    require(isinstance(seal, str) and bool(reconcile.SHA256.fullmatch(seal)) and
            seal == reconcile.digest({k: v for k, v in killed.items() if k != "receipt_sha256"}),
            "KILL_OBSERVATION_SELF_SEAL_INVALID")
    require(isinstance(killed.get("journal_sha256"), str) and
            bool(reconcile.SHA256.fullmatch(killed["journal_sha256"])),
            "KILL_JOURNAL_HASH_INVALID")
    for key in ("owned_worker_pid", "owned_aider_pid", "owned_aider_process_group"):
        require(type(killed.get(key)) is int and 1 <= killed[key] < 2**31,
                "KILL_PID_INVALID")
    require(killed["owned_worker_pid"] != killed["owned_aider_pid"] and
            killed["owned_aider_pid"] == killed["owned_aider_process_group"],
            "KILL_PARENT_GROUP_MISMATCH")
    require(killed.get("worker_killed_by_sigkill") is True and
            killed.get("aider_group_killed_by_sigkill") is True and
            killed.get("live_model_executable_seen_before_kill") is True,
            "KILL_NOT_ACTUALLY_OBSERVED")
    require(killed.get("journal_preserved") is True and
            killed.get("old_final_receipt_absent") is True and
            killed.get("retry_rejected_reason") == "DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY" and
            killed.get("cross_host_failover_proven") is False,
            "KILL_OR_RETRY_GATE_DRIFT")
    return True


def collect_rows():
    """Local OS process query only, never returns raw commands to the operator."""
    if os.name == "nt":
        command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                   "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,CreationDate,CommandLine | ConvertTo-Json -Compress -Depth 2"]
        query = subprocess.run(command, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=20)
        require(query.returncode == 0 and len(query.stdout) <= MAX_PROCESS_TEXT,
                "WINDOWS_PROCESS_LIST_UNAVAILABLE")
        try:
            raw = json.loads(query.stdout)
        except ValueError:
            raise reconcile.Refused("WINDOWS_PROCESS_LIST_JSON_INVALID")
        data = raw if isinstance(raw, list) else [raw]
        return [{"pid": int(row["ProcessId"]), "ppid": int(row.get("ParentProcessId") or 0),
                 "command": row.get("CommandLine") or "", "started": row.get("CreationDate")}
                for row in data if isinstance(row, dict) and row.get("ProcessId") is not None]
    command = ["ps", "-axww", "-o", "pid=,ppid=,lstart=,command="]
    query = subprocess.run(command, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=15)
    require(query.returncode == 0 and len(query.stdout) <= MAX_PROCESS_TEXT,
            "POSIX_PROCESS_LIST_UNAVAILABLE")
    rows = []
    for line in query.stdout.splitlines():
        parts = line.split(None, 7)
        if len(parts) != 8 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        rows.append({"pid": int(parts[0]), "ppid": int(parts[1]),
                     "started": " ".join(parts[2:7]), "command": parts[7]})
    return rows


def evaluate(env, killed, rows, host):
    validate(env, killed)
    require(host == env["host"], "HISTORICAL_HOST_NOT_LOCAL")
    ids = {"worker": killed["owned_worker_pid"], "aider": killed["owned_aider_pid"]}
    found = {}
    for role, old_pid in ids.items():
        candidates = [row for row in rows if row.get("pid") == old_pid]
        require(len(candidates) <= 1, "DUPLICATE_PID_PROCESS_SNAPSHOT")
        if not candidates:
            found[role] = {"historical_pid": old_pid, "status": "NO_PID_AT_SNAPSHOT"}
            continue
        row = candidates[0]
        cmd = str(row.get("command", ""))
        start = str(row.get("started", ""))
        if role == "worker":
            resembles = ("vf_office_v2_p0_local_model_worker.py" in cmd and
                         "run" in cmd and env["task_id"] in cmd)
        else:
            resembles = ("aider" in cmd.lower() and
                         "ollama_chat/" + env["executor"]["model"] in cmd and
                         row.get("ppid") == killed["owned_worker_pid"])
        found[role] = {
            "historical_pid": old_pid,
            "status": "POSSIBLE_MATCH_NO_PROCESS_START_PIN" if resembles else "PID_REUSED_OR_UNRELATED",
            "observed_ppid": row.get("ppid"),
            "command_sha256": hashlib.sha256(cmd.encode("utf-8", "replace")).hexdigest(),
            "start_text_sha256": hashlib.sha256(start.encode("utf-8", "replace")).hexdigest(),
        }
    return {
        "schema": SCHEMA, "task_id": env["task_id"], "host": host,
        "envelope_sha256": reconcile.digest(env),
        "observation_kind": "HISTORICAL_PID_CURRENT_SNAPSHOT_NOT_LEASE",
        "historical_pids": found,
        "historical_worker_currently_proven_active": False,
        "all_orphan_descendants_excluded": False,
        "safe_to_retry_original": False, "automatic_requeue_allowed": False,
        "new_task_authorized": False, "scheduler_authority_granted": False,
        "production_effects": "NONE", "model_calls": 0, "read_only": True,
        "next_gate": "OPERATOR_RECONCILIATION_AND_BOUND_OS_START_IDENTITY_REQUIRED",
    }


def selftest():
    checks = []
    with tempfile.TemporaryDirectory(prefix="p0-owner-snapshot-") as root:
        env = {"schema": reconcile.SCHEMA, "authority": reconcile.AUTHORITY,
               "issue_url": reconcile.ISSUE, "task_id": "p0-owner-lab-001",
               "host": "synthetic-host", "base_sha": "a" * 40,
               "branch": "lab-p0-agent-owner", "worktree_path": root + "/fixture",
               "context_checkpoint": root + "/checkpoint.json",
               "budget": {"max_attempts": 1, "max_cost_usd": 0},
               "executor": {"kind": reconcile.KIND, "model": "qwen3.5:4b",
                            "model_digest": "b" * 64}}
        killed = {"schema": KILL_SCHEMA, "task_id": env["task_id"],
                  "envelope_sha256": reconcile.digest(env), "host": env["host"],
                  "model": "qwen3.5:4b", "model_digest": "b" * 64,
                  "owned_worker_pid": 23001, "owned_aider_pid": 23002,
                  "owned_aider_process_group": 23002,
                  "worker_killed_by_sigkill": True,
                  "aider_group_killed_by_sigkill": True,
                  "live_model_executable_seen_before_kill": True,
                  "journal_sha256": "c" * 64,
                  "journal_preserved": True, "old_final_receipt_absent": True,
                  "retry_rejected_reason": "DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY",
                  "cross_host_failover_proven": False}
        def seal(data):
            obj = dict(data)
            obj.pop("receipt_sha256", None)
            obj["receipt_sha256"] = reconcile.digest(obj)
            return obj
        killed = seal(killed)
        assert evaluate(env, killed, [], "synthetic-host")["historical_pids"]["worker"]["status"] == "NO_PID_AT_SNAPSHOT"
        checks.append("absent_pid_is_not_safe_to_retry")
        worker = {"pid": 23001, "ppid": 1, "started": "time1",
                  "command": "python vf_office_v2_p0_local_model_worker.py run --envelope /foo/p0-owner-lab-001/envelope.json"}
        aide = {"pid": 23002, "ppid": 23001, "started": "time2",
                "command": "aider --model ollama_chat/qwen3.5:4b --file slug.py"}
        cases = [
            ("both_matching_but_not_pinned", [worker, aide], "POSSIBLE_MATCH_NO_PROCESS_START_PIN", "POSSIBLE_MATCH_NO_PROCESS_START_PIN"),
            ("pid_reuse_both", [dict(worker, command="unrelated"), dict(aide, command="unrelated")], "PID_REUSED_OR_UNRELATED", "PID_REUSED_OR_UNRELATED"),
            ("worker_only", [worker], "POSSIBLE_MATCH_NO_PROCESS_START_PIN", "NO_PID_AT_SNAPSHOT"),
            ("child_wrong_parent", [dict(aide, ppid=999)], "NO_PID_AT_SNAPSHOT", "PID_REUSED_OR_UNRELATED"),
            ("worker_wrong_task", [dict(worker, command="python vf_office_v2_p0_local_model_worker.py run --envelope /foo/other-task/envelope.json")], "PID_REUSED_OR_UNRELATED", "NO_PID_AT_SNAPSHOT"),
        ]
        for name, rows, w_expected, a_expected in cases:
            out = evaluate(env, killed, rows, "synthetic-host")
            assert out["historical_pids"]["worker"]["status"] == w_expected
            assert out["historical_pids"]["aider"]["status"] == a_expected
            assert out["safe_to_retry_original"] is False and out["automatic_requeue_allowed"] is False
            assert out["all_orphan_descendants_excluded"] is False
            checks.append(name)
        for label,field,val in (
            ("wrong_task", "task_id", "other-task"),
            ("wrong_hash", "envelope_sha256", "c" * 64),
            ("wrong_model", "model", "qwen3.5:9b"),
            ("fake_kill", "worker_killed_by_sigkill", False),
            ("fake_requeue", "retry_rejected_reason", "RETRY_ALLOWED"),
            ("bool_pid", "owned_worker_pid", True),
        ):
            modified=dict(killed);modified[field]=val;modified=seal(modified)
            try: evaluate(env, modified, [], "synthetic-host")
            except reconcile.Refused: checks.append("resealed_" + label + "_denied")
            else: raise AssertionError(label + "_ACCEPTED")
        malformed=dict(killed);malformed["journal_sha256"]="bad"
        malformed=seal(malformed)
        try: evaluate(env, malformed, [], "synthetic-host")
        except reconcile.Refused: checks.append("invalid_journal_hash_denied")
        else: raise AssertionError("INVALID_JOURNAL_HASH_ACCEPTED")
        invalid=dict(killed);invalid["receipt_sha256"]="0"*64
        try: evaluate(env, invalid, [], "synthetic-host")
        except reconcile.Refused: checks.append("invalid_hash_denied")
        else: raise AssertionError("INVALID_HASH_ACCEPTED")
        try: evaluate(env, killed, [], "wrong-host")
        except reconcile.Refused: checks.append("wrong_host_denied")
        else: raise AssertionError("WRONG_HOST_ACCEPTED")
        try: evaluate(env, killed, [worker, worker], "synthetic-host")
        except reconcile.Refused: checks.append("duplicate_pid_denied")
        else: raise AssertionError("DUPLICATE_PID_ACCEPTED")
    return {"status": "PASS", "tests": len(checks), "cases": checks,
            "model_invocations": 0, "processes_killed": 0,
            "new_task_authorized": False, "orphan_exclusion_proven": False}


def main():
    p = argparse.ArgumentParser(description="No-authority worker PID observation")
    commands = p.add_subparsers(dest="command", required=True)
    commands.add_parser("selftest")
    live = commands.add_parser("observe")
    live.add_argument("--envelope", required=True)
    live.add_argument("--kill-observation", required=True)
    live.add_argument("--receipt", required=True)
    args = p.parse_args()
    if args.command == "selftest":
        result = selftest()
    else:
        env = reconcile.checked_envelope(reconcile.read_optional(pathlib.Path(args.envelope).absolute()))
        killed = reconcile.read_optional(pathlib.Path(args.kill_observation).absolute())
        require(killed is not None, "KILL_OBSERVATION_MISSING")
        validate(env, killed)
        require(env["host"] == platform.node(), "NOT_ORIGINAL_HOST")
        before = reconcile.reconcile(args.envelope, args.receipt)
        require(before["status"] == "UNKNOWN_RUNNING_JOURNAL_NO_BLIND_RETRY" and
                before["envelope_sha256"] == reconcile.digest(env),
                "ORIGINAL_UNKNOWN_JOURNAL_NOT_PRESERVED")
        journal = pathlib.Path(args.receipt).absolute().with_suffix(
            pathlib.Path(args.receipt).suffix + ".running")
        require(not journal.is_symlink(), "SYMLINK_JOURNAL_REFUSE")
        journal_dict = reconcile.read_optional(journal)
        require(journal_dict is not None, "MISSING_ORIGINAL_JOURNAL")
        journal_sha = hashlib.sha256(journal.read_bytes()).hexdigest()
        require(journal_sha == killed["journal_sha256"],
                "HISTORICAL_JOURNAL_HASH_CHANGED")
        result = evaluate(env, killed, collect_rows(), platform.node())
        after = reconcile.reconcile(args.envelope, args.receipt)
        require(after == before and hashlib.sha256(journal.read_bytes()).hexdigest() == journal_sha,
                "JOURNAL_CHANGED_DURING_PROCESS_SNAPSHOT")
        result["observed_utc"] = datetime.now(timezone.utc).isoformat()
        result["original_unknown_journal_still_present"] = True
        result["receipt_sha256"] = reconcile.digest(result)
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (reconcile.Refused, ValueError, OSError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:150],
                          "safe_to_retry_original":False,"automatic_requeue_allowed":False}))
        raise SystemExit(2)
