#!/usr/bin/env python3
"""#612 bounded Windows Job descendant inheritance LAB; no model or scheduler.

An OS-detached *grandchild* is created only after its owner is in an unnamed
KILL_ON_JOB_CLOSE Job. This proves exactly observed handles, never global absence
of escaped descendants. Neither a sandbox nor a retry/production authority.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import vf_office_v2_p0_windows_job_object_lab as native

SCHEMA = "vf.office-v2.p0-detached-descendant-native-job.v0"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"


def require(ok, message):
    if not ok:
        raise native.Refused(message)


def seal(row):
    clean = {k: v for k, v in row.items() if k != "receipt_sha256"}
    return dict(clean, receipt_sha256=hashlib.sha256(json.dumps(
        clean, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest())


def validated(row):
    require(isinstance(row, dict) and row.get("schema") == SCHEMA, "SCHEMA_DRIFT")
    require(row.get("receipt_sha256") == seal(row)["receipt_sha256"], "HASH_DRIFT")
    require(row.get("issue") == ISSUE and row.get("scope") ==
            "ONE_EXCLUSIVE_LOCAL_WINDOWS_DETACHED_GRANDCHILD", "SCOPE_DRIFT")
    for key in ("owner_assigned_before_descendant_spawn", "owner_in_job",
                "detached_descendant_in_job", "both_alive_before_close",
                "last_job_handle_closed", "both_exited_after_close"):
        require(row.get(key) is True, "UNVERIFIED_" + key)
    for key in ("original_unknown_retry_authorized",
                "all_possible_escaped_processes_excluded",
                "autonomous_recovery_proven", "fleet_scheduler_authority",
                "production_authority"):
        require(row.get(key) is False, "FALSE_AUTHORITY_" + key)
    require(row.get("model_calls") == 0 and type(row.get("model_calls")) is int,
            "MODEL_CALL_CLAIM_DRIFT")
    require(row.get("api_spend_usd") == 0 and
            type(row.get("api_spend_usd")) is int, "PAID_CALL_CLAIM_DRIFT")
    a, b = row.get("owner_pid"), row.get("descendant_pid")
    x, y = row.get("owner_birth_us"), row.get("descendant_birth_us")
    require(all(type(v) is int and v > 0 for v in (a, b, x, y)) and
            a != b and x <= y, "NATIVE_IDENTITY_DRIFT")
    return True


def selftest():
    sample = seal({
        "schema": SCHEMA, "issue": ISSUE,
        "scope": "ONE_EXCLUSIVE_LOCAL_WINDOWS_DETACHED_GRANDCHILD",
        "owner_pid": 31010, "descendant_pid": 31011,
        "owner_birth_us": 1700000000000000, "descendant_birth_us": 1700000000100000,
        "owner_assigned_before_descendant_spawn": True, "owner_in_job": True,
        "detached_descendant_in_job": True, "both_alive_before_close": True,
        "last_job_handle_closed": True, "both_exited_after_close": True,
        "original_unknown_retry_authorized": False,
        "all_possible_escaped_processes_excluded": False,
        "autonomous_recovery_proven": False, "fleet_scheduler_authority": False,
        "production_authority": False, "model_calls": 0, "api_spend_usd": 0,
    })
    validated(sample)
    cases = ["positive_shape_only_not_live_evidence"]
    negatives = [
        ("false_job_membership", "detached_descendant_in_job", False),
        ("owner_assigned_late", "owner_assigned_before_descendant_spawn", False),
        ("false_death", "both_exited_after_close", False),
        ("false_global_containment", "all_possible_escaped_processes_excluded", True),
        ("false_auto_recovery", "autonomous_recovery_proven", True),
        ("retry_unknown", "original_unknown_retry_authorized", True),
        ("false_fleet_authority", "fleet_scheduler_authority", True),
        ("false_production_authority", "production_authority", True),
        ("false_paid_call", "api_spend_usd", 1),
        ("false_model_call", "model_calls", 1),
        ("reused_pid", "descendant_pid", 31010),
        ("older_descendant", "descendant_birth_us", 1),
    ]
    for label, key, value in negatives:
        tampered = seal(dict(sample, **{key: value}))
        try:
            validated(tampered)
        except native.Refused:
            cases.append(label + "_rejected")
        else:
            raise AssertionError("RESEALED_FALSE_RECEIPT_ACCEPTED:" + label)
    tampered = dict(sample, receipt_sha256="0" * 64)
    try:
        validated(tampered)
    except native.Refused:
        cases.append("raw_hash_tamper_rejected")
    else:
        raise AssertionError("RAW_HASH_TAMPER_ACCEPTED")
    require(len(cases) == 14, "SELFTEST_COUNT_DRIFT")
    return {"status": "PASS_OFFLINE", "tests": len(cases), "checks": cases,
            "native_jobs_created": 0, "model_calls": 0,
            "all_possible_escaped_processes_excluded": False}


def _wait(path, max_seconds):
    deadline = time.monotonic() + max_seconds
    while time.monotonic() < deadline:
        if Path(path).is_file():
            return
        time.sleep(.04)
    raise native.Refused("SPAWN_GATE_TIMEOUT")


def _grandchild(root):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline and not (Path(root) / "stop").exists():
        time.sleep(.06)


def _owner(root):
    root = Path(root)
    _wait(root / "assigned.flag", 10)
    flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    child = subprocess.Popen(
        [sys.executable, "-B", str(Path(__file__).resolve()), "_grandchild", str(root)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        cwd=root, creationflags=flags)
    with (root / "descendant-pid.json").open("x", encoding="utf-8") as handle:
        json.dump({"pid": child.pid}, handle)
        handle.flush()
        os.fsync(handle.fileno())
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline and not (root / "stop").exists():
        time.sleep(.06)


def live(path):
    require(os.name == "nt", "WINDOWS_ONLY")
    require(os.path.normcase(os.path.normpath(sys.executable)) ==
            os.path.normcase(os.path.normpath(getattr(sys, "_base_executable", ""))),
            "DIRECT_WINDOWS_PYTHON_REQUIRED")
    output = Path(path).absolute()
    require(output.parent.parent.name == "WindowsJobObjectLab" and
            output.parent.name.startswith("20261009-gpt6-detached-") and
            output.name.startswith("detached-job-") and output.suffix == ".json" and
            output.parent.is_dir() and not output.exists() and not output.is_symlink(),
            "UNAUTHORIZED_OR_REUSED_LAB_OUTPUT")
    api = native.win32()
    require(ctypes.sizeof(native.JOBOBJECT_EXTENDED_LIMIT_INFORMATION) == 144,
            "JOB_LAYOUT_DRIFT")
    with tempfile.TemporaryDirectory(prefix="owned-job-", dir=output.parent) as temp:
        owner, job, descendant_handle = None, None, None
        root = Path(temp)
        try:
            owner = subprocess.Popen(
                [sys.executable, "-B", str(Path(__file__).resolve()), "_owner", str(root)],
                cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP |
                              subprocess.CREATE_NO_WINDOW)
            job = native.os_success(api.CreateJobObjectW(None, None),
                                    "NATIVE_JOB_CREATE_FAILED")
            info = native.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = native.KILL_ON_JOB_CLOSE
            native.os_success(api.SetInformationJobObject(
                job, 9, ctypes.byref(info), ctypes.sizeof(info)), "SET_JOB_LIMIT_FAILED")
            owner_handle = native.wintypes.HANDLE(int(owner._handle))
            native.os_success(api.AssignProcessToJobObject(job, owner_handle),
                              "ASSIGN_OWNER_FAILED")
            require(native.job_member(api, owner_handle, job), "OWNER_NOT_IN_JOB")
            owner_birth = native.kernel_birth_us(api, owner_handle)
            (root / "assigned.flag").touch()
            deadline = time.monotonic() + 8
            marker = root / "descendant-pid.json"
            while time.monotonic() < deadline and not marker.is_file():
                require(owner.poll() is None, "OWNER_EXITED_BEFORE_DESCENDANT")
                time.sleep(.04)
            require(marker.is_file(), "NO_DETACHED_DESCENDANT")
            payload = json.loads(marker.read_text(encoding="utf-8"))
            desc_pid = payload.get("pid")
            require(type(desc_pid) is int and desc_pid > 1 and desc_pid != owner.pid,
                    "DESCENDANT_PID_INVALID")
            descendant_handle = native.os_success(api.OpenProcess(
                native.PROCESS_QUERY_LIMITED_INFORMATION | native.SYNCHRONIZE,
                False, desc_pid), "OPEN_DESCENDANT_FAILED")
            desc_birth = native.kernel_birth_us(api, descendant_handle)
            require(desc_birth >= owner_birth and
                    native.job_member(api, descendant_handle, job),
                    "DETACHED_DESCENDANT_ESCAPED_JOB")
            require(api.WaitForSingleObject(owner_handle, 0) == native.WAIT_TIMEOUT and
                    api.WaitForSingleObject(descendant_handle, 0) == native.WAIT_TIMEOUT,
                    "PROCESS_NOT_ALIVE_BEFORE_CLOSE")
            native.os_success(api.CloseHandle(job), "JOB_CLOSE_FAILED")
            job = None
            require(api.WaitForSingleObject(owner_handle, 5000) == native.WAIT_OBJECT_0 and
                    api.WaitForSingleObject(descendant_handle, 5000) ==
                    native.WAIT_OBJECT_0, "OWNED_DESCENDANT_SURVIVED_JOB_CLOSE")
            owner.wait(timeout=5)
            record = seal({
                "schema": SCHEMA, "issue": ISSUE,
                "scope": "ONE_EXCLUSIVE_LOCAL_WINDOWS_DETACHED_GRANDCHILD",
                "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                "owner_pid": owner.pid, "descendant_pid": desc_pid,
                "owner_birth_us": owner_birth, "descendant_birth_us": desc_birth,
                "owner_assigned_before_descendant_spawn": True, "owner_in_job": True,
                "detached_descendant_in_job": True, "both_alive_before_close": True,
                "last_job_handle_closed": True, "both_exited_after_close": True,
                "original_unknown_retry_authorized": False,
                "all_possible_escaped_processes_excluded": False,
                "autonomous_recovery_proven": False, "fleet_scheduler_authority": False,
                "production_authority": False, "model_calls": 0, "api_spend_usd": 0,
            })
            validated(record)
            with output.open("x", encoding="utf-8") as handle:
                json.dump(record, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            return {"status": "PASS_EXACT_DETACHED_DESCENDANT_JOB_ONLY",
                    "owner_pid": owner.pid, "descendant_pid": desc_pid,
                    "receipt_sha256": record["receipt_sha256"],
                    "all_possible_escaped_processes_excluded": False}
        finally:
            (root / "stop").touch()
            if job is not None:
                api.CloseHandle(job)
            if descendant_handle is not None:
                api.CloseHandle(descendant_handle)
            if owner is not None:
                try:
                    owner.wait(timeout=21)
                except subprocess.TimeoutExpired:
                    print("OWNER_LIVENESS_UNKNOWN_MANUAL_REVIEW", file=sys.stderr)


def verify(path):
    evidence = Path(path)
    require(evidence.is_file() and not evidence.is_symlink() and
            evidence.stat().st_size <= 65536, "RECEIPT_UNSAFE")
    validated(json.loads(evidence.read_text(encoding="utf-8")))
    return {"status": "PASS_SHAPE_SELF_HASH_ONLY_NOT_INDEPENDENT_OS_ATTESTATION",
            "model_calls": 0, "all_possible_escaped_processes_excluded": False}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    sub.add_parser("_owner", help=argparse.SUPPRESS).add_argument("root")
    sub.add_parser("_grandchild", help=argparse.SUPPRESS).add_argument("root")
    action = sub.add_parser("live")
    action.add_argument("--output", required=True)
    check = sub.add_parser("verify")
    check.add_argument("--evidence", required=True)
    args = parser.parse_args()
    if args.cmd == "_owner":
        _owner(args.root)
        return
    if args.cmd == "_grandchild":
        _grandchild(args.root)
        return
    value = (selftest() if args.cmd == "selftest" else
             live(args.output) if args.cmd == "live" else verify(args.evidence))
    print(json.dumps(value, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (native.Refused, OSError, ValueError, TypeError, KeyError,
            AssertionError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:180],
                          "all_possible_escaped_processes_excluded": False}))
        raise SystemExit(2)
