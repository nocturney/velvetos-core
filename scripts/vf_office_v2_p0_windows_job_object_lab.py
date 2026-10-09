#!/usr/bin/env python3
"""#612: tightly scoped Windows Job Object inheritance/close LAB.

Only the explicitly created, temporary Python fixture is ever associated with
the unnamed Job Object. This is NOT a worker/scheduler, production containment,
or authority to retry an UNKNOWN model task. Real mode is opt-in Windows only.
"""
from __future__ import annotations

import argparse
import copy
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

SCHEMA = "vf.office-v2.p0-native-win-job-containment.v0"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9
KILL_ON_JOB_CLOSE = 0x00002000
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258


class Refused(Exception):
    pass


def require(ok, why):
    if not ok:
        raise Refused(why)


def digest(obj):
    return hashlib.sha256(json.dumps(
        obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def seal(record):
    record = copy.deepcopy(record)
    record.pop("receipt_sha256", None)
    record["receipt_sha256"] = digest(record)
    return record


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class FILETIME(ctypes.Structure):
    _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]


def win32():
    require(os.name == "nt", "WINDOWS_ONLY_NATIVE_JOB_EXPERIMENT")
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    def bind(name, argtypes, restype):
        fn = getattr(api, name)
        fn.argtypes = argtypes
        fn.restype = restype
        return fn
    handles = wintypes.HANDLE
    bind("CreateJobObjectW", [ctypes.c_void_p, wintypes.LPCWSTR], handles)
    bind("SetInformationJobObject", [handles, wintypes.INT, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL)
    bind("AssignProcessToJobObject", [handles, handles], wintypes.BOOL)
    bind("IsProcessInJob", [handles, handles, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL)
    bind("OpenProcess", [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], handles)
    bind("GetProcessTimes", [handles, ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME),
                             ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME)], wintypes.BOOL)
    bind("WaitForSingleObject", [handles, wintypes.DWORD], wintypes.DWORD)
    bind("CloseHandle", [handles], wintypes.BOOL)
    return api


def os_success(value, code):
    if not value:
        raise Refused(code + "_WINERROR_" + str(ctypes.get_last_error()))
    return value


def kernel_birth_us(api, handle):
    created, exited, kernel, user = FILETIME(), FILETIME(), FILETIME(), FILETIME()
    os_success(api.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                                  ctypes.byref(kernel), ctypes.byref(user)), "GET_PROCESS_TIMES_FAILED")
    ticks = ((int(created.high) << 32) | int(created.low))
    us = (ticks - 116444736000000000) // 10
    require(us > 0, "KERNEL_BIRTH_UNAVAILABLE")
    return us


def job_member(api, process_handle, job):
    belongs = wintypes.BOOL()
    os_success(api.IsProcessInJob(process_handle, job, ctypes.byref(belongs)),
               "IS_PROCESS_IN_JOB_FAILED")
    return bool(belongs.value)


def verified_record(value):
    require(isinstance(value, dict) and value.get("schema") == SCHEMA, "SCHEMA_DRIFT")
    require(value.get("receipt_sha256") == digest({
        k: v for k, v in value.items() if k != "receipt_sha256"
    }), "RECEIPT_HASH_DRIFT")
    require(value.get("issue") == ISSUE and
            value.get("scope") == "EXCLUSIVE_TEMP_PYTHON_JOB_ONLY", "SCOPE_DRIFT")
    for field, expected in (
        ("owner_assigned_before_child_spawn", True),
        ("owner_in_job_before_close", True),
        ("child_in_job_before_close", True),
        ("owner_alive_before_close", True),
        ("child_alive_before_close", True),
        ("last_owned_job_handle_closed", True),
        ("both_processes_exited_after_close", True),
        ("native_job_limit", KILL_ON_JOB_CLOSE),
        ("autonomous_model_recovery_proven", False),
        ("all_possible_escaped_processes_excluded", False),
        ("original_task_retry_allowed", False),
        ("fleet_scheduler_authority", False),
        ("production_writer", False),
        ("model_invocations", 0),
        ("additional_api_spend_usd", 0),
    ):
        require(type(value.get(field)) is type(expected) and value.get(field) == expected,
                "FALSE_OR_MISSING_ASSERTION_" + field)
    for key in ("owner_pid", "child_pid", "owner_birth_us", "child_birth_us"):
        require(type(value.get(key)) is int and value[key] > 0,
                "NATIVE_PROCESS_IDENTITY_REQUIRED_" + key)
    require(value["owner_pid"] != value["child_pid"] and
            value["owner_birth_us"] <= value["child_birth_us"],
            "WRONG_NATIVE_PROCESS_LINEAGE")
    return True


def sample_success():
    return seal({
        "schema": SCHEMA, "issue": ISSUE, "scope": "EXCLUSIVE_TEMP_PYTHON_JOB_ONLY",
        "observed_at_utc": "2026-10-09T00:00:00+00:00",
        "owner_pid": 31100, "child_pid": 31101,
        "owner_birth_us": 1791500000100000, "child_birth_us": 1791500000110000,
        "owner_assigned_before_child_spawn": True,
        "owner_in_job_before_close": True, "child_in_job_before_close": True,
        "owner_alive_before_close": True, "child_alive_before_close": True,
        "last_owned_job_handle_closed": True, "both_processes_exited_after_close": True,
        "native_job_limit": KILL_ON_JOB_CLOSE, "autonomous_model_recovery_proven": False,
        "all_possible_escaped_processes_excluded": False,
        "original_task_retry_allowed": False, "fleet_scheduler_authority": False,
        "production_writer": False, "model_invocations": 0,
        "additional_api_spend_usd": 0,
    })


def selftest():
    good = sample_success()
    verified_record(good)
    checks = ["positive_native_contract_without_launch"]
    cases = (
        ("false_member_owner", lambda x: x.update(owner_in_job_before_close=False)),
        ("false_member_child", lambda x: x.update(child_in_job_before_close=False)),
        ("owner_died_early", lambda x: x.update(owner_alive_before_close=False)),
        ("child_died_early", lambda x: x.update(child_alive_before_close=False)),
        ("false_job_close", lambda x: x.update(last_owned_job_handle_closed=False)),
        ("false_process_exit", lambda x: x.update(both_processes_exited_after_close=False)),
        ("unauthorized_requeue", lambda x: x.update(original_task_retry_allowed=True)),
        ("false_global_orphans_clear", lambda x: x.update(all_possible_escaped_processes_excluded=True)),
        ("false_fleet_authority", lambda x: x.update(fleet_scheduler_authority=True)),
        ("false_production_writer", lambda x: x.update(production_writer=True)),
        ("false_model_inference", lambda x: x.update(model_invocations=1)),
        ("job_limit_disabled", lambda x: x.update(native_job_limit=0)),
        ("same_pid", lambda x: x.update(child_pid=31100)),
        ("bad_kernel_birth", lambda x: x.update(child_birth_us=0)),
        ("child_older_than_owner", lambda x: x.update(child_birth_us=1)),
    )
    for name, change in cases:
        altered = copy.deepcopy(good)
        change(altered)
        altered = seal(altered)  # negative remains rejected even if re-sealed
        try:
            verified_record(altered)
        except Refused:
            checks.append(name + "_rejected")
        else:
            raise AssertionError("RESEALED_FALSE_CONTAINMENT_ACCEPTED:" + name)
    tamper = copy.deepcopy(good)
    tamper["receipt_sha256"] = "0" * 64
    try:
        verified_record(tamper)
    except Refused:
        checks.append("broken_self_hash_rejected")
    else:
        raise AssertionError("BROKEN_HASH_ACCEPTED")
    require(len(checks) == 17, "SELFTEST_COUNT_DRIFT")
    return {"status": "PASS", "tests": len(checks), "cases": checks,
            "live_processes_launched": 0, "model_invocations": 0,
            "original_task_retry_allowed": False,
            "all_possible_escaped_processes_excluded": False}


def _child(root):
    stop = Path(root) / "stop"
    deadline = time.monotonic() + 16
    while time.monotonic() < deadline:
        if stop.exists():
            return
        time.sleep(.06)


def _owner(root):
    root = Path(root)
    go = root / "assigned-to-job.flag"
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline and not go.exists():
        time.sleep(.03)
    require(go.exists(), "JOB_ASSIGNMENT_NOT_CONFIRMED")
    flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    child = subprocess.Popen(
        [sys.executable, "-B", str(Path(__file__).resolve()), "_child", str(root)],
        cwd=root, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags,
    )
    marker = root / "child-pid.json"
    with marker.open("x", encoding="utf-8") as fp:
        json.dump({"child_pid": child.pid}, fp)
        fp.write("\n")
        fp.flush()
        os.fsync(fp.fileno())
    deadline = time.monotonic() + 16
    while time.monotonic() < deadline:
        if (root / "stop").exists():
            return
        time.sleep(.06)


def live(out):
    require(os.name == "nt", "REAL_JOB_OBJECT_PROOF_WINDOWS_ONLY")
    target = Path(out).absolute()
    require(not target.exists() and not target.is_symlink(),
            "NEVER_OVERWRITE_NATIVE_PROOF")
    api = win32()
    require(ctypes.sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION) == 144,
            "UNSUPPORTED_WINDOWS_NATIVE_STRUCT_LAYOUT")
    with tempfile.TemporaryDirectory(prefix="p0-native-job-safe-") as td:
        root = Path(td)
        owner = None
        job = None
        child_handle = None
        assigned = False
        try:
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            owner = subprocess.Popen(
                [sys.executable, "-B", str(Path(__file__).resolve()), "_owner", td],
                cwd=td, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=flags,
            )
            job = os_success(api.CreateJobObjectW(None, None), "CREATE_JOB_FAILED")
            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = KILL_ON_JOB_CLOSE
            os_success(api.SetInformationJobObject(
                job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
                ctypes.byref(info), ctypes.sizeof(info)), "SET_KILL_ON_CLOSE_FAILED")
            os_success(api.AssignProcessToJobObject(job, wintypes.HANDLE(int(owner._handle))),
                       "ASSIGN_EXCLUSIVE_OWNER_FAILED")
            assigned = True
            require(job_member(api, wintypes.HANDLE(int(owner._handle)), job),
                    "OWNER_NOT_IN_OWNED_JOB")
            owner_birth = kernel_birth_us(api, wintypes.HANDLE(int(owner._handle)))
            (root / "assigned-to-job.flag").touch()
            marker = root / "child-pid.json"
            deadline = time.monotonic() + 8
            while not marker.is_file() and time.monotonic() < deadline:
                require(owner.poll() is None, "OWNER_EXITED_BEFORE_CHILD_SPAWN")
                time.sleep(.035)
            require(marker.is_file(), "NO_CHILD_CREATED_IN_BOUNDED_WINDOW")
            payload = json.loads(marker.read_text(encoding="utf-8"))
            child_pid = payload.get("child_pid")
            require(type(child_pid) is int and 1 <= child_pid < 2**31 and
                    child_pid != owner.pid, "CHILD_PID_INVALID")
            child_handle = os_success(api.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, child_pid),
                "OPEN_OWNED_CHILD_FAILED")
            child_birth = kernel_birth_us(api, child_handle)
            require(child_birth >= owner_birth, "CHILD_PRECEDED_OWNER")
            require(job_member(api, child_handle, job), "CHILD_DID_NOT_INHERIT_JOB")
            require(api.WaitForSingleObject(wintypes.HANDLE(int(owner._handle)), 0) == WAIT_TIMEOUT and
                    api.WaitForSingleObject(child_handle, 0) == WAIT_TIMEOUT,
                    "PROCESS_EXITED_BEFORE_CONTAINMENT_TEST")
            os_success(api.CloseHandle(job), "JOB_HANDLE_CLOSE_FAILED")
            job = None
            owner_done = api.WaitForSingleObject(wintypes.HANDLE(int(owner._handle)), 5000)
            child_done = api.WaitForSingleObject(child_handle, 5000)
            require(owner_done == WAIT_OBJECT_0 and child_done == WAIT_OBJECT_0,
                    "OWNED_JOB_CHILDREN_SURVIVED_HANDLE_CLOSE")
            owner.wait(timeout=5)
            report = seal({
                "schema": SCHEMA, "issue": ISSUE,
                "scope": "EXCLUSIVE_TEMP_PYTHON_JOB_ONLY",
                "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                "owner_pid": owner.pid, "child_pid": child_pid,
                "owner_birth_us": owner_birth, "child_birth_us": child_birth,
                "owner_assigned_before_child_spawn": True,
                "owner_in_job_before_close": True, "child_in_job_before_close": True,
                "owner_alive_before_close": True, "child_alive_before_close": True,
                "last_owned_job_handle_closed": True,
                "both_processes_exited_after_close": True,
                "native_job_limit": KILL_ON_JOB_CLOSE,
                "autonomous_model_recovery_proven": False,
                "all_possible_escaped_processes_excluded": False,
                "original_task_retry_allowed": False,
                "fleet_scheduler_authority": False,
                "production_writer": False, "model_invocations": 0,
                "additional_api_spend_usd": 0,
            })
            verified_record(report)
            with target.open("x", encoding="utf-8") as fp:
                json.dump(report, fp, ensure_ascii=False, indent=2, sort_keys=True)
                fp.write("\n")
                fp.flush()
                os.fsync(fp.fileno())
            return report
        finally:
            (root / "stop").touch()
            if child_handle is not None:
                api.CloseHandle(child_handle)
            if job is not None:
                api.CloseHandle(job)  # ONLY this new unnamed fixture's job handle
            if owner is not None:
                try:
                    owner.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # If no job assignment occurred, the fixture exits after 12s.
                    print("LAB_OWNER_EXIT_NOT_YET_CONFIRMED", file=sys.stderr)


def verify(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink(), "RECEIPT_MISSING_OR_SYMLINK")
    data = p.read_bytes()
    require(1 <= len(data) <= 65536, "RECEIPT_SIZE_INVALID")
    row = json.loads(data.decode("utf-8"))
    verified_record(row)
    return {"status": "PASS", "independent_offline_verification": True,
            "job_child_inherited_containment": True,
            "original_task_retry_allowed": False,
            "all_possible_escaped_processes_excluded": False,
            "model_invocations": 0, "receipt_sha256": row["receipt_sha256"]}


def main():
    p = argparse.ArgumentParser()
    cmds = p.add_subparsers(dest="mode", required=True)
    cmds.add_parser("selftest")
    cmds.add_parser("_owner", help=argparse.SUPPRESS).add_argument("root")
    cmds.add_parser("_child", help=argparse.SUPPRESS).add_argument("root")
    run = cmds.add_parser("live")
    run.add_argument("--output", required=True)
    read = cmds.add_parser("verify")
    read.add_argument("--evidence", required=True)
    args = p.parse_args()
    if args.mode == "_owner":
        _owner(args.root)
        return
    if args.mode == "_child":
        _child(args.root)
        return
    result = (selftest() if args.mode == "selftest" else
              verify(args.evidence) if args.mode == "verify" else
              live(args.output))
    if args.mode == "live":
        print(json.dumps({"status": "PASS_BOUNDED_WINDOWS_JOB_LAB",
                          "owner_pid": result["owner_pid"], "child_pid": result["child_pid"],
                          "two_processes_exited_after_close": True,
                          "original_task_retry_allowed": False,
                          "receipt_sha256": result["receipt_sha256"]}, sort_keys=True))
    else:
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refused, ValueError, OSError, TypeError, KeyError,
            AssertionError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:170],
                          "original_task_retry_allowed": False,
                          "all_possible_escaped_processes_excluded": False}))
        raise SystemExit(2)
