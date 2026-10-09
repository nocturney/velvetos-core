#!/usr/bin/env python3
"""#612: native same-host exclusive reservation / loss LAB, not a fleet lease.

Only entirely new owned synthetic directories under AgentEnvelopeLab or
WindowsJobObjectLab. O_EXCL enforces one local-filesystem claim; after the
claimant is terminated the reservation remains sticky until manual review.
No automatic recovery, scheduler, external effect or model execution.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import vf_office_v2_p0_kernel_identity as kernel

SCHEMA = "velvetos.office-v2.p0-local-singleflight-loss-lab.v0"
CLAIM_SCHEMA = "velvetos.office-v2.p0-local-exclusive-reservation.v0"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
TASK_ID = "p0-singleflight-owned-synthetic-20261009"
RESOURCE = "ONE_LOCAL_SYNTHETIC_RESOURCE_ONLY"
LIMIT = 1024 * 128


def require(condition, reason):
    if not condition:
        raise kernel.Refused(reason)


def digest(row):
    return hashlib.sha256(json.dumps(
        row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def sealed(row, key):
    value = copy.deepcopy(row)
    value.pop(key, None)
    value[key] = digest(value)
    return value


def read_json(path):
    target = Path(path)
    require(target.is_file() and not target.is_symlink()
            and 0 < target.stat().st_size <= LIMIT, "UNSAFE_INPUT")
    before = target.stat()
    data = target.read_bytes()
    after = target.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
            "INPUT_CHANGED")
    try:
        row = json.loads(data)
    except (ValueError, UnicodeDecodeError):
        raise kernel.Refused("INVALID_INPUT_JSON")
    require(isinstance(row, dict), "OBJECT_REQUIRED")
    return row


def save_new(path, row):
    target = Path(path)
    require(not target.exists() and not target.is_symlink(), "FILE_ALREADY_EXISTS")
    with target.open("x", encoding="utf-8") as out:
        json.dump(row, out, ensure_ascii=False, sort_keys=True, indent=2)
        out.write("\n")
        out.flush()
        os.fsync(out.fileno())


def lab_dir(raw, *, must_be_new=False):
    path = Path(raw)
    require(path.is_absolute() and not path.is_symlink()
            and path.name.startswith("p0-singleflight-probe-")
            and path.parent.name in {"AgentEnvelopeLab", "WindowsJobObjectLab"}
            and path.parent.is_dir() and not path.parent.is_symlink(),
            "OWNED_EXCLUSIVE_LAB_ROOT_ONLY")
    require(".." not in path.parts, "LAB_TRAVERSAL_DENIED")
    if must_be_new:
        require(not path.exists(), "FRESH_PROBE_ROOT_REQUIRED")
    else:
        require(path.is_dir(), "PROBE_ROOT_MISSING")
    return path


def claim_row(role, snapshot):
    kernel.require_row(snapshot)
    require(role in {"a", "b", "c"}, "UNSUPPORTED_CONTENDER")
    row = {"schema": CLAIM_SCHEMA, "issue": ISSUE,
           "host": platform.node(), "task_id": TASK_ID,
           "resource": RESOURCE, "contender": role,
           "kernel_identity": snapshot, "scope": "EXCLUSIVE_LOCAL_LAB_ONLY",
           "created_at_utc": datetime.now(timezone.utc).isoformat(),
           "canonical_fleet_lease": False, "production_effect": False,
           "original_unknown_retry_authorized": False,
           "new_job_execution_authorized": False}
    return sealed(row, "claim_sha256")


def verify_claim(row):
    require(isinstance(row, dict) and row.get("schema") == CLAIM_SCHEMA
            and row.get("issue") == ISSUE and row.get("task_id") == TASK_ID
            and row.get("resource") == RESOURCE and
            row.get("scope") == "EXCLUSIVE_LOCAL_LAB_ONLY",
            "CLAIM_BINDING_DRIFT")
    require(row.get("contender") in {"a", "b"}, "INITIAL_WINNER_REQUIRED")
    require(isinstance(row.get("host"), str) and bool(row["host"]),
            "HOST_BINDING_REQUIRED")
    kernel.require_row(row.get("kernel_identity"))
    require(row.get("canonical_fleet_lease") is False
            and row.get("production_effect") is False
            and row.get("original_unknown_retry_authorized") is False
            and row.get("new_job_execution_authorized") is False,
            "FALSE_AUTHORITY_CLAIM")
    require(isinstance(row.get("claim_sha256"), str) and
            len(row["claim_sha256"]) == 64 and row["claim_sha256"] ==
            digest({k: v for k, v in row.items() if k != "claim_sha256"}),
            "CLAIM_HASH_DRIFT")
    return True


def report_row(winner, loser, before_hash, after_hash, after_kill_status,
               elapsed_ms):
    require(winner in {"a", "b"} and loser in {"a", "b"} and winner != loser,
            "SINGLE_WINNER_REQUIRED")
    require(before_hash == after_hash and len(before_hash) == 64,
            "CLAIM_CHANGED_AFTER_OWNER_TERMINATED")
    row = {
        "schema": SCHEMA, "issue": ISSUE,
        "scope": "EXCLUSIVE_FRESH_SAME_HOST_SYNTHETIC_DIRECTORY",
        "host": platform.node(), "task_id": TASK_ID, "resource": RESOURCE,
        "winner": winner, "loser": loser,
        "owner_os_birth_pinned_before_termination": True,
        "original_claim_os_exclusive": True,
        "initial_exactly_one_winner": True,
        "concurrent_collision_refused": True,
        "terminated_owned_process_only": True,
        "original_owner_exited": True,
        "post_loss_collision_refused": after_kill_status == "DENIED_ALREADY_CLAIMED",
        "claim_bytes_unchanged_after_owner_exit": before_hash == after_hash,
        "claim_sha256_raw": before_hash,
        "elapsed_ms": elapsed_ms,
        "canonical_fleet_lease": False,
        "distributed_fencing_verified": False,
        "all_orphan_descendants_excluded": False,
        "original_unknown_retry_authorized": False,
        "new_job_execution_authorized": False,
        "autonomous_recovery_proven": False,
        "production_writer": False, "model_calls": 0,
        "additional_api_spend_usd": 0,
    }
    return sealed(row, "receipt_sha256")


def verify_report(row):
    require(isinstance(row, dict) and row.get("schema") == SCHEMA and
            row.get("issue") == ISSUE and
            row.get("scope") == "EXCLUSIVE_FRESH_SAME_HOST_SYNTHETIC_DIRECTORY",
            "REPORT_SCHEMA_OR_SCOPE_DRIFT")
    require(row.get("winner") in {"a", "b"} and
            row.get("loser") in {"a", "b"} and
            row["winner"] != row["loser"], "REPORT_SINGLE_WINNER_INVALID")
    for flag in ("owner_os_birth_pinned_before_termination",
                 "original_claim_os_exclusive", "initial_exactly_one_winner",
                 "concurrent_collision_refused", "terminated_owned_process_only",
                 "original_owner_exited", "post_loss_collision_refused",
                 "claim_bytes_unchanged_after_owner_exit"):
        require(row.get(flag) is True, "REQUIRED_PROOF_MISSING_" + flag)
    for flag in ("canonical_fleet_lease", "distributed_fencing_verified",
                 "all_orphan_descendants_excluded",
                 "original_unknown_retry_authorized",
                 "new_job_execution_authorized",
                 "autonomous_recovery_proven", "production_writer"):
        require(row.get(flag) is False, "FALSE_SAFETY_AUTHORITY_" + flag)
    require(type(row.get("model_calls")) is int and row["model_calls"] == 0
            and type(row.get("additional_api_spend_usd")) is int and
            row["additional_api_spend_usd"] == 0, "INFERRED_MODEL_OR_PAID_CALL")
    require(type(row.get("elapsed_ms")) is int and row["elapsed_ms"] > 0,
            "BOUNDED_OBSERVATION_REQUIRED")
    require(isinstance(row.get("claim_sha256_raw"), str) and
            len(row["claim_sha256_raw"]) == 64, "RAW_CLAIM_HASH_REQUIRED")
    require(row.get("receipt_sha256") == digest({k: v for k, v in row.items()
                                               if k != "receipt_sha256"}),
            "RECEIPT_SEAL_DRIFT")
    return True


def _contender(root, role):
    root = lab_dir(root)
    require(role in {"a", "b", "c"}, "UNKNOWN_CONTENDER")
    me = kernel.sample(os.getpid())
    require(me is not None, "CURRENT_OS_IDENTITY_MISSING")
    kernel.require_row(me)
    # Both first contenders must be ready before the parent releases the gate.
    save_new(root / ("ready-" + role + ".json"),
             {"role": role, "pid": os.getpid()})
    deadline = time.monotonic() + 18
    while not (root / "go.flag").exists() and time.monotonic() < deadline:
        time.sleep(.025)
    require((root / "go.flag").exists(), "CONTENDER_GATE_TIMEOUT")
    candidate = claim_row(role, me)
    target = root / "reservation.json"
    try:
        fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        verdict = "DENIED_ALREADY_CLAIMED"
    else:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(candidate, out, ensure_ascii=False, sort_keys=True, indent=2)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        verdict = "CREATED_EXCLUSIVE_CLAIM"
    save_new(root / ("result-" + role + ".json"),
             {"role": role, "pid": os.getpid(), "status": verdict})
    if verdict == "CREATED_EXCLUSIVE_CLAIM":
        deadline = time.monotonic() + 24
        while time.monotonic() < deadline:
            time.sleep(.05)


def await_result(root, name, children, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        path = root / name
        if path.is_file():
            try:
                return read_json(path)
            except (kernel.Refused, OSError):
                pass  # exclusive child may still be writing its own JSON
        require(any(p.poll() is None for p in children), "ALL_OWNED_PROCESSES_EXITED_EARLY")
        time.sleep(.03)
    raise kernel.Refused("EXCLUSIVE_PROBE_TIMEOUT_" + name)


def live(root_arg):
    root = lab_dir(root_arg, must_be_new=True)
    started = time.monotonic()
    root.mkdir(exist_ok=False)
    processes = {}
    try:
        for role in ("a", "b"):
            processes[role] = subprocess.Popen(
                [sys.executable, "-B", str(Path(__file__).resolve()), "_contender",
                 "--root", str(root), "--role", role],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, cwd=root)
        for role in ("a", "b"):
            ready = await_result(root, "ready-" + role + ".json",
                                 list(processes.values()))
            require(ready.get("role") == role and
                    ready.get("pid") == processes[role].pid, "READY_PID_MISMATCH")
        (root / "go.flag").touch(exist_ok=False)
        results = {role: await_result(root, "result-" + role + ".json",
                                     list(processes.values())) for role in ("a", "b")}
        winners = [role for role, result in results.items()
                   if result.get("status") == "CREATED_EXCLUSIVE_CLAIM"]
        denied = [role for role, result in results.items()
                  if result.get("status") == "DENIED_ALREADY_CLAIMED"]
        require(len(winners) == len(denied) == 1 and
                winners[0] != denied[0], "NOT_EXACTLY_ONE_NATIVE_WINNER")
        winner, loser = winners[0], denied[0]
        original = read_json(root / "reservation.json")
        verify_claim(original)
        identity = kernel.sample(processes[winner].pid)
        require(identity is not None and
                kernel.match(original["kernel_identity"], identity) ==
                "SAME_KERNEL_INSTANCE_AT_SNAPSHOT", "OWNED_WINNER_OS_BIRTH_DRIFT")
        require(processes[winner].poll() is None, "OWNED_WINNER_ALREADY_EXITED")
        require(original["contender"] == winner and
                original["kernel_identity"]["pid"] == processes[winner].pid,
                "CLAIM_NOT_BOUND_TO_EXCLUSIVE_WINNER")
        processes[loser].wait(timeout=7)
        before_bytes = (root / "reservation.json").read_bytes()
        # Only our exact Popen handle, never process-name matching or broad kills.
        processes[winner].terminate()
        processes[winner].wait(timeout=8)
        require(processes[winner].poll() is not None,
                "OWNED_WINNER_NOT_TERMINATED")
        processes["c"] = subprocess.Popen(
            [sys.executable, "-B", str(Path(__file__).resolve()), "_contender",
             "--root", str(root), "--role", "c"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, cwd=root)
        replay = await_result(root, "result-c.json", [processes["c"]])
        processes["c"].wait(timeout=7)
        require(replay.get("status") == "DENIED_ALREADY_CLAIMED",
                "POST_LOSS_STICKY_RESERVATION_BROKEN")
        after_bytes = (root / "reservation.json").read_bytes()
        require(before_bytes == after_bytes, "CLAIM_CHANGED_AFTER_OWNER_LOSS")
        claim_hash = hashlib.sha256(before_bytes).hexdigest()
        millis = max(1, int((time.monotonic() - started) * 1000))
        receipt = report_row(winner, loser, claim_hash, claim_hash,
                             replay["status"], millis)
        verify_report(receipt)
        save_new(root / "report.json", receipt)
        return {"status": "PASS_SCOPED_SAME_HOST_SINGLEFLIGHT_LOSS_LAB",
                "host": platform.node(), "winner_pid": processes[winner].pid,
                "winner_birth_us": original["kernel_identity"]["birth_us"],
                "kernel_identity_source": identity["source"],
                "winner": winner, "loser": loser,
                "initial_conflicts": 1, "post_owner_loss_conflicts": 1,
                "owner_dead_before_third_attempt": True,
                "raw_claim_sha256": claim_hash,
                "receipt_sha256": receipt["receipt_sha256"],
                "elapsed_ms": millis, "model_calls": 0,
                "canonical_fleet_lease": False,
                "distributed_fencing_verified": False,
                "automatic_recovery_proven": False,
                "new_job_execution_authorized": False}
    finally:
        for process in processes.values():
            if process.poll() is None:
                process.terminate()  # our own freshly spawned fixture only
                try:
                    process.wait(timeout=6)
                except subprocess.TimeoutExpired:
                    print("OWNED_CHILD_NOT_CONFIRMED_EXIT_MANUAL_REVIEW", file=sys.stderr)
        # Retain fresh scratch/claim/evidence; NEVER erase a possibly UNKNOWN lock.


def verify_files(root_arg):
    root = lab_dir(root_arg)
    claim = read_json(root / "reservation.json")
    report = read_json(root / "report.json")
    verify_claim(claim); verify_report(report)
    before = (root / "reservation.json").read_bytes()
    require(hashlib.sha256(before).hexdigest() ==
            report["claim_sha256_raw"], "HISTORICAL_CLAIM_HASH_MISMATCH")
    rows = [read_json(root / ("result-" + role + ".json"))
            for role in ("a", "b", "c")]
    require(len([x for x in rows[:2]
                 if x.get("status") == "CREATED_EXCLUSIVE_CLAIM"]) == 1
            and len([x for x in rows[:2]
                     if x.get("status") == "DENIED_ALREADY_CLAIMED"]) == 1
            and rows[2].get("status") == "DENIED_ALREADY_CLAIMED",
            "HISTORICAL_COLLISION_EVIDENCE_DRIFT")
    return {"status": "PASS_OFFLINE_SHAPE_AND_HASH_ONLY",
            "receipt_sha256": report["receipt_sha256"],
            "claim_raw_sha256": report["claim_sha256_raw"],
            "model_calls": 0, "new_job_execution_authorized": False,
            "distributed_fencing_verified": False,
            "kernel_processes_reobserved": False}


def selftest():
    worker = {"pid": 12012, "ppid": 12000,
              "birth_us": 1700000000000000, "pgid": None,
              "source": "WINDOWS_CIM_CREATION_DATE"}
    original = claim_row("a", worker)
    verify_claim(original)
    good = report_row("a", "b", "a" * 64, "a" * 64,
                      "DENIED_ALREADY_CLAIMED", 99)
    verify_report(good)
    cases = ["positive_claim_shape_not_live",
             "positive_report_shape_not_live"]
    deny_claim = [
        ("wrong_schema", "schema", "x"),
        ("wrong_task", "task_id", "unknown"),
        ("wrong_resource", "resource", "PRODUCTION"),
        ("fake_lease", "canonical_fleet_lease", True),
        ("fake_permission", "new_job_execution_authorized", True),
        ("bad_pid", "kernel_identity", dict(worker, birth_us=0)),
        ("wrong_scope", "scope", "FLEET"),
        ("invalid_contender", "contender", "c"),
    ]
    for label, key, value in deny_claim:
        altered = sealed(dict(original, **{key: value}), "claim_sha256")
        try:
            verify_claim(altered)
        except kernel.Refused:
            cases.append(label + "_rejected")
        else:
            raise AssertionError("FALSE_CLAIM_ACCEPTED:" + label)
    deny_report = [
        ("false_initial_winner", "initial_exactly_one_winner", False),
        ("fake_owner_died", "original_owner_exited", False),
        ("no_os_birth", "owner_os_birth_pinned_before_termination", False),
        ("replay_allowed", "original_unknown_retry_authorized", True),
        ("canonical_lease_spoofed", "canonical_fleet_lease", True),
        ("distributed_fencing_spoofed", "distributed_fencing_verified", True),
        ("global_orphans_spoofed", "all_orphan_descendants_excluded", True),
        ("automatic_recovery_spoofed", "autonomous_recovery_proven", True),
        ("false_collision", "post_loss_collision_refused", False),
        ("changed_claim", "claim_bytes_unchanged_after_owner_exit", False),
        ("bad_loser", "loser", "a"),
        ("paid_call", "additional_api_spend_usd", 1),
        ("model_called", "model_calls", 1),
        ("zero_elapsed", "elapsed_ms", 0),
    ]
    for label, key, value in deny_report:
        altered = sealed(dict(good, **{key: value}), "receipt_sha256")
        try:
            verify_report(altered)
        except kernel.Refused:
            cases.append(label + "_rejected")
        else:
            raise AssertionError("FALSE_REPORT_ACCEPTED:" + label)
    broken = dict(good, receipt_sha256="0"*64)
    try:
        verify_report(broken)
    except kernel.Refused:
        cases.append("raw_receipt_tamper_rejected")
    else:
        raise AssertionError("TAMPERED_REPORT_ACCEPTED")
    require(len(cases) == 25, "SELFTEST_COUNT_DRIFT")
    return {"status": "PASS_OFFLINE", "tests": len(cases),
            "cases": cases, "real_children_spawned": 0, "model_calls": 0,
            "canonical_fleet_lease": False, "distributed_fencing_verified": False,
            "original_unknown_retry_authorized": False,
            "new_job_execution_authorized": False,
            "production_effects": 0}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("selftest")
    run = sub.add_parser("live")
    run.add_argument("--root", required=True)
    kid = sub.add_parser("_contender", help=argparse.SUPPRESS)
    kid.add_argument("--root", required=True)
    kid.add_argument("--role", choices=["a", "b", "c"], required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--root", required=True)
    args = parser.parse_args()
    if args.mode == "_contender":
        _contender(args.root, args.role)
        return
    value = (selftest() if args.mode == "selftest" else
             live(args.root) if args.mode == "live" else verify_files(args.root))
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (kernel.Refused, OSError, ValueError, TypeError, KeyError,
            AssertionError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:180],
                          "canonical_fleet_lease": False,
                          "new_job_execution_authorized": False,
                          "original_unknown_retry_authorized": False}, sort_keys=True))
        raise SystemExit(2)
