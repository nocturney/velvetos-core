#!/usr/bin/env python3
"""P0 #612: kernel process birth identity and conservative group observations.

LAB-only, never starts/kills/retries a worker and never grants #604 placement.
A process ID without its captured OS creation identity cannot prove ownership.
The v1 model-worker journal does NOT contain this historical pin. Do not
retroactively certify a killed worker: capture only while both PIDs are alive.
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
import re
import subprocess
import sys
import tempfile

SCHEMA = "velvetos.office-v2.p0-kernel-process-pin.v1"
ENVELOPE = "velvetos.office-v2.p0-local-model-envelope.v1"
KIND = "LOCAL_AIDER_OLLAMA_SYNTHETIC_V1"
AUTHORITY = "LAB_LOCAL_MODEL_SYNTHETIC_ONLY_NO_EFFECT"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
SHA = re.compile(r"[0-9a-f]{64}\Z")
MAX_JSON = 1024 * 1024


class Refused(Exception):
    pass


def require(ok, code):
    if not ok:
        raise Refused(code)


def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def raw_file(path):
    path = Path(path)
    require(not path.is_symlink() and path.is_file(), "INPUT_MISSING_OR_SYMLINK")
    before = path.stat()
    require(0 < before.st_size <= MAX_JSON, "INPUT_SIZE_INVALID")
    data = path.read_bytes()
    after = path.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
            "INPUT_CHANGED_DURING_READ")
    require(len(data) <= MAX_JSON, "INPUT_TOO_LARGE")
    return data


def read(path):
    try:
        obj = json.loads(raw_file(path).decode("utf-8"))
    except (ValueError, UnicodeError):
        raise Refused("INPUT_JSON_INVALID")
    require(isinstance(obj, dict), "OBJECT_REQUIRED")
    return obj


def checked_env(env, *, local=False):
    require(isinstance(env, dict) and env.get("schema") == ENVELOPE and
            env.get("authority") == AUTHORITY and env.get("issue_url") == ISSUE,
            "ENVELOPE_SCOPE")
    require(isinstance(env.get("task_id"), str) and
            bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,95}", env["task_id"])),
            "TASK_ID_INVALID")
    require(isinstance(env.get("host"), str) and bool(env["host"]),
            "HOST_MISSING")
    if local:
        require(env["host"] == platform.node(), "WRONG_LOCAL_HOST")
    require(isinstance(env.get("executor"), dict) and
            env["executor"].get("kind") == KIND, "EXECUTOR_NOT_LOCAL_AIDER_LAB")
    require(env.get("budget", {}).get("max_attempts") == 1 and
            type(env.get("budget", {}).get("max_cost_usd")) in (int, float) and
            env["budget"]["max_cost_usd"] == 0, "RETRY_OR_COST_DENIED")
    require(isinstance(env.get("worktree_path"), str) and env["worktree_path"],
            "WORKTREE_REFERENCE_MISSING")
    return env


def checked_journal(journal, env):
    require(isinstance(journal, dict), "JOURNAL_REQUIRED")
    expected = {
        "state": "RUNNING", "unknown_outcome_rule": "NO_BLIND_RETRY",
        "kind": KIND, "task_id": env["task_id"], "host": env["host"],
        "envelope_sha256": digest(env),
    }
    for key, expected_value in expected.items():
        require(journal.get(key) == expected_value, "JOURNAL_" + key.upper() + "_DRIFT")
    require(isinstance(journal.get("started_at"), str) and journal["started_at"],
            "JOURNAL_START_REQUIRED")
    return journal


def sample(pid):
    """Read creation time from OS-managed process metadata, not argv strings."""
    require(type(pid) is int and 1 <= pid < 2**31, "PID_INVALID")
    if os.name == "nt":
        # CIM CreationDate is kernel-sourced. No command lines or credentials read.
        statement = (
            "$p=Get-CimInstance Win32_Process -Filter 'ProcessId = " + str(pid) + "';"
            "if($null -eq $p){'null'} else {"
            "@{pid=[int]$p.ProcessId;ppid=[int]$p.ParentProcessId;"
            "utc=$p.CreationDate.ToUniversalTime().ToString('o')} | "
            "ConvertTo-Json -Compress}"
        )
        try:
            result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive",
                                     "-Command", statement], capture_output=True,
                                    encoding="utf-8", errors="replace", timeout=12)
        except (OSError, subprocess.TimeoutExpired):
            raise Refused("WINDOWS_CIM_UNAVAILABLE")
        require(result.returncode == 0 and len(result.stdout) < 4096,
                "WINDOWS_CIM_FAILURE")
        try:
            payload = json.loads(result.stdout.strip())
        except ValueError:
            raise Refused("WINDOWS_CIM_INVALID_JSON")
        if payload is None:
            return None
        require(isinstance(payload, dict) and payload.get("pid") == pid and
                type(payload.get("ppid")) is int, "WINDOWS_CIM_IDENTITY_INVALID")
        try:
            timestamp = datetime.fromisoformat(payload["utc"].replace("Z", "+00:00"))
            require(timestamp.tzinfo is not None, "WINDOWS_START_TZ_MISSING")
            started_us = round(timestamp.timestamp() * 1_000_000)
        except (TypeError, ValueError, KeyError, OverflowError):
            raise Refused("WINDOWS_START_INVALID")
        return {"pid": pid, "ppid": payload["ppid"], "birth_us": started_us,
                "pgid": None, "source": "WINDOWS_CIM_CREATION_DATE"}
    try:
        import psutil
    except ImportError:
        raise Refused("PSUTIL_REQUIRED_NO_FALLBACK_TO_UNPINNED_PS")
    try:
        first = psutil.Process(pid)
        birthday = first.create_time()
        parent = first.ppid()
        pgid = os.getpgid(pid)
        second = psutil.Process(pid)  # fresh process handle avoids a cached PID reuse
        if second.create_time() != birthday or second.ppid() != parent:
            raise Refused("PID_CHANGED_DURING_SNAPSHOT")
        if second.status() == psutil.STATUS_ZOMBIE:
            raise Refused("ZOMBIE_IS_NOT_LIVE_OWNER")
    except (psutil.NoSuchProcess, ProcessLookupError):
        return None
    except (psutil.AccessDenied, PermissionError):
        raise Refused("OS_PROCESS_IDENTITY_ACCESS_DENIED")
    return {"pid": pid, "ppid": parent, "birth_us": round(birthday * 1_000_000),
            "pgid": pgid, "source": "PSUTIL_OS_CREATE_TIME"}


def require_row(row):
    require(isinstance(row, dict), "OS_IDENTITY_NOT_OBJECT")
    require(type(row.get("pid")) is int and row["pid"] > 0 and
            type(row.get("ppid")) is int and row["ppid"] >= 0,
            "OS_PID_FIELDS")
    require(type(row.get("birth_us")) is int and row["birth_us"] > 0,
            "UNPINNED_OR_INVALID_OS_BIRTH")
    require(row.get("source") in ("PSUTIL_OS_CREATE_TIME",
                                  "WINDOWS_CIM_CREATION_DATE"), "BIRTH_SOURCE")
    pgid = row.get("pgid")
    if row["source"] == "PSUTIL_OS_CREATE_TIME":
        require(type(pgid) is int and pgid > 0, "POSIX_GROUP_UNAVAILABLE")
    else:
        require(pgid is None, "WINDOWS_GROUP_SPOOFED")
    return row


def make_pin(env, journal, worker, aider):
    checked_env(env)
    checked_journal(journal, env)
    require_row(worker)
    require_row(aider)
    require(worker["source"] == aider["source"], "MIXED_OS_IDENTITY_BACKENDS")
    require(worker["pid"] != aider["pid"] and
            aider["ppid"] == worker["pid"] and
            aider["birth_us"] >= worker["birth_us"], "CHILD_NOT_BOUND_TO_WORKER")
    if worker["source"] == "PSUTIL_OS_CREATE_TIME":
        require(aider["pgid"] == aider["pid"], "AIDER_NEW_SESSION_NOT_OBSERVED")
    pin = {
        "schema": SCHEMA, "task_id": env["task_id"],
        "host": env["host"], "envelope_sha256": digest(env),
        "journal_sha256": digest(journal), "kind": KIND,
        "worker": copy.deepcopy(worker), "aider": copy.deepcopy(aider),
        "capture_time_utc": datetime.now(timezone.utc).isoformat(),
        "authority": "READ_ONLY_PROCESS_IDENTITY_NO_RECOVERY",
        "retry_permitted": False, "all_orphans_excluded": False,
    }
    pin["pin_sha256"] = digest(pin)
    return pin


def checked_pin(env, journal, pin):
    checked_env(env)
    checked_journal(journal, env)
    require(isinstance(pin, dict) and pin.get("schema") == SCHEMA and
            pin.get("kind") == KIND and pin.get("task_id") == env["task_id"] and
            pin.get("host") == env["host"] and
            pin.get("envelope_sha256") == digest(env) and
            pin.get("journal_sha256") == digest(journal),
            "PROCESS_PIN_NOT_BOUND_TO_ATTEMPT")
    require(pin.get("authority") == "READ_ONLY_PROCESS_IDENTITY_NO_RECOVERY" and
            pin.get("retry_permitted") is False and
            pin.get("all_orphans_excluded") is False, "PIN_AUTHORITY_ESCALATION")
    seal = pin.get("pin_sha256")
    require(isinstance(seal, str) and bool(SHA.fullmatch(seal)) and
            digest({k: v for k, v in pin.items() if k != "pin_sha256"}) == seal,
            "PROCESS_PIN_SEAL_DRIFT")
    # Re-check child lineage even for a correctly re-sealed forged payload.
    worker, aider = pin.get("worker"), pin.get("aider")
    require_row(worker); require_row(aider)
    require(worker["source"] == aider["source"] and worker["pid"] != aider["pid"] and
            aider["ppid"] == worker["pid"] and aider["birth_us"] >= worker["birth_us"],
            "PIN_LINEAGE_INVALID")
    if worker["source"] == "PSUTIL_OS_CREATE_TIME":
        require(aider["pgid"] == aider["pid"], "PIN_GROUP_INVALID")
    return True


def match(expected, actual):
    if actual is None:
        return "HISTORICAL_PID_ABSENT"
    require_row(actual)
    require(actual["pid"] == expected["pid"], "UNEXPECTED_OS_PID")
    if actual["source"] != expected["source"]:
        return "OS_IDENTITY_BACKEND_CHANGED"
    if actual["birth_us"] != expected["birth_us"]:
        return "PID_REUSED_DIFFERENT_BIRTH"
    if actual["ppid"] != expected["ppid"]:
        return "SAME_KERNEL_INSTANCE_REPARENTED_OR_PARENT_CHANGED"
    if actual["pgid"] != expected["pgid"]:
        return "SAME_BIRTH_PROCESS_GROUP_CHANGED"
    return "SAME_KERNEL_INSTANCE_AT_SNAPSHOT"


def group_members(pgid, *, limit=10000):
    """Potential POSIX group survivors, NEVER exhaustive descendant attestation."""
    if os.name == "nt":
        return {"status": "NO_WINDOWS_JOB_OBJECT_IDENTITY", "candidate_count": None}
    try:
        import psutil
    except ImportError:
        return {"status": "GROUP_SCAN_NOT_AVAILABLE", "candidate_count": None}
    count = 0
    try:
        processes = list(psutil.process_iter(attrs=["pid"]))
        if len(processes) > limit:
            return {"status": "GROUP_SCAN_CAP_EXCEEDED", "candidate_count": None}
        for process in processes:
            try:
                if os.getpgid(process.pid) == pgid:
                    count += 1
            except (OSError, psutil.NoSuchProcess, psutil.AccessDenied):
                # A vanished/inaccessible entry prevents a complete negative claim.
                return {"status": "GROUP_SCAN_INCOMPLETE", "candidate_count": None}
    except (OSError, psutil.Error):
        return {"status": "GROUP_SCAN_INCOMPLETE", "candidate_count": None}
    return {"status": "POSSIBLE_GROUP_MEMBERS" if count else "NO_GROUP_MEMBERS_SEEN",
            "candidate_count": count}


def assess(env, journal, pin, actual_worker, actual_aider, group):
    checked_pin(env, journal, pin)
    results = {
        "worker": match(pin["worker"], actual_worker),
        "aider": match(pin["aider"], actual_aider),
    }
    require(isinstance(group, dict) and isinstance(group.get("status"), str),
            "GROUP_OBSERVATION_INVALID")
    return {
        "schema": "velvetos.office-v2.p0-process-birth-readback.v1",
        "task_id": env["task_id"], "host": env["host"],
        "envelope_sha256": digest(env), "pin_sha256": pin["pin_sha256"],
        "historical_processes": results, "group_observation": group,
        "kernel_birth_pin_available": True,
        "live_process_claim_only_at_snapshot": True,
        "historical_journal_stays_unknown": True,
        "all_orphans_excluded": False, "original_retry_permitted": False,
        "automatic_requeue_allowed": False, "new_task_authorized": False,
        "production_writer": False, "fleet_scheduler_authority": False,
        "model_invocations": 0, "read_only": True,
    }


def selftest():
    checks = []
    env = {"schema": ENVELOPE, "authority": AUTHORITY,
           "issue_url": ISSUE, "task_id": "p0-kernel-probe-001",
           "host": "synthetic-host", "worktree_path": "/LAB/repo",
           "executor": {"kind": KIND},
           "budget": {"max_attempts": 1, "max_cost_usd": 0}}
    journal = {"state": "RUNNING", "unknown_outcome_rule": "NO_BLIND_RETRY",
               "task_id": env["task_id"], "host": env["host"],
               "kind": KIND, "envelope_sha256": digest(env),
               "started_at": "2026-10-09T10:00:00+00:00"}
    worker = {"pid": 21100, "ppid": 1, "birth_us": 1791540000100000,
              "pgid": 21000, "source": "PSUTIL_OS_CREATE_TIME"}
    aider = {"pid": 21101, "ppid": 21100, "birth_us": 1791540000110000,
             "pgid": 21101, "source": "PSUTIL_OS_CREATE_TIME"}
    pin = make_pin(env, journal, worker, aider)
    checked_pin(env, journal, pin);checks.append("legitimate_birth_and_lineage_pin")
    scenarios = [
        ("same_both", worker, aider, "SAME_KERNEL_INSTANCE_AT_SNAPSHOT",
         "SAME_KERNEL_INSTANCE_AT_SNAPSHOT"),
        ("pid_absent", None, None, "HISTORICAL_PID_ABSENT", "HISTORICAL_PID_ABSENT"),
        ("pid_reuse", dict(worker, birth_us=worker["birth_us"]+1), aider,
         "PID_REUSED_DIFFERENT_BIRTH", "SAME_KERNEL_INSTANCE_AT_SNAPSHOT"),
        ("reparented_child", worker, dict(aider, ppid=1),
         "SAME_KERNEL_INSTANCE_AT_SNAPSHOT", "SAME_KERNEL_INSTANCE_REPARENTED_OR_PARENT_CHANGED"),
        ("group_changed", worker, dict(aider, pgid=21212),
         "SAME_KERNEL_INSTANCE_AT_SNAPSHOT", "SAME_BIRTH_PROCESS_GROUP_CHANGED"),
        ("source_swapped", dict(worker, source="WINDOWS_CIM_CREATION_DATE", pgid=None), aider,
         "OS_IDENTITY_BACKEND_CHANGED", "SAME_KERNEL_INSTANCE_AT_SNAPSHOT"),
    ]
    for name, wa, aa, expect_w, expect_a in scenarios:
        x = assess(env, journal, pin, wa, aa, {"status":"NO_GROUP_MEMBERS_SEEN","candidate_count":0})
        assert x["historical_processes"] == {"worker":expect_w,"aider":expect_a}
        assert x["original_retry_permitted"] is False and x["all_orphans_excluded"] is False
        checks.append(name)
    # The same model runner on Windows has no reliable Job Object birth grouping.
    ww = dict(worker, pgid=None, source="WINDOWS_CIM_CREATION_DATE")
    wa = dict(aider, pgid=None, source="WINDOWS_CIM_CREATION_DATE")
    wp = make_pin(env, journal, ww, wa)
    assert assess(env,journal,wp,ww,wa,{"status":"NO_WINDOWS_JOB_OBJECT_IDENTITY"})["original_retry_permitted"] is False
    checks.append("windows_native_birth_without_job_identity")
    # Correctly re-sealed false ownership and falsified retry are still rejected.
    for name, mutated in (
        ("host_change",lambda x:x.update(host="other-host")),
        ("task_change",lambda x:x.update(task_id="different-task")),
        ("journal_change",lambda x:x.update(journal_sha256="1"*64)),
        ("wrong_parent",lambda x:x["aider"].update(ppid=20000)),
        ("backwards_birth",lambda x:x["aider"].update(birth_us=1)),
        ("missing_birth",lambda x:x["aider"].pop("birth_us")),
        ("bad_group",lambda x:x["aider"].update(pgid=12345)),
        ("forged_retry",lambda x:x.update(retry_permitted=True)),
        ("false_orphan_exclusion",lambda x:x.update(all_orphans_excluded=True)),
        ("false_kind",lambda x:x.update(kind="CODEX_CLI")),
    ):
        cloned=copy.deepcopy(pin);mutated(cloned)
        cloned.pop("pin_sha256",None);cloned["pin_sha256"]=digest(cloned)
        try:checked_pin(env,journal,cloned)
        except Refused:checks.append("resealed_"+name+"_denied")
        else:raise AssertionError("UNSAFE_PIN_ACCEPTED_"+name)
    invalid=copy.deepcopy(pin);invalid["pin_sha256"]="0"*64
    try:checked_pin(env,journal,invalid)
    except Refused:checks.append("broken_selfhash_rejected")
    else:raise AssertionError("BROKEN_SEAL_ACCEPTED")
    mismatched=copy.deepcopy(journal);mismatched["envelope_sha256"]="a"*64
    try:make_pin(env,mismatched,worker,aider)
    except Refused:checks.append("foreign_journal_rejected")
    else:raise AssertionError("FOREIGN_JOURNAL_ACCEPTED")
    for name, bad_worker, bad_aider in (
        ("bool_pid", dict(worker,pid=True), aider),
        ("same_pid", worker, dict(aider,pid=21100,pgid=21100)),
        ("child_older_than_parent", worker, dict(aider,birth_us=worker["birth_us"]-1)),
        ("non_kernel_source", dict(worker,source="ARGV_HINT"), aider),
    ):
        try:make_pin(env,journal,bad_worker,bad_aider)
        except Refused:checks.append(name+"_rejected")
        else:raise AssertionError("WRONG_PROCESS_IDENTITY_ACCEPTED_"+name)
    assert len(checks)==24, checks
    return {"status":"PASS","tests":len(checks),"cases":checks,
            "model_invocations":0,"processes_killed":0,"new_tasks_started":0,
            "no_auto_retries":True,"all_orphans_excluded":False}


def cli():
    ap=argparse.ArgumentParser(description="Read-only OS-birth identity for P0 LAB")
    commands=ap.add_subparsers(dest="command",required=True)
    commands.add_parser("selftest")
    commands.add_parser("sample-self")
    cap=commands.add_parser("capture")
    obs=commands.add_parser("observe")
    for cmd in (cap,obs):
        cmd.add_argument("--envelope",required=True)
        cmd.add_argument("--receipt",required=True)
    cap.add_argument("--worker-pid",required=True,type=int)
    cap.add_argument("--aider-pid",required=True,type=int)
    cap.add_argument("--output",required=True)
    obs.add_argument("--pin",required=True)
    args=ap.parse_args()
    if args.command=="selftest":
        return selftest()
    if args.command=="sample-self":
        first=sample(os.getpid());second=sample(os.getpid())
        require(first is not None and first==second, "SELF_IDENTITY_NOT_STABLE")
        return {"status":"PASS","source":first["source"],"birth_pinned":first["birth_us"]>0,
                "pid":first["pid"],"ppid":first["ppid"],"model_invocations":0,
                "read_only":True,"all_orphans_excluded":False}
    env=checked_env(read(args.envelope),local=True)
    receipt=Path(args.receipt).absolute()
    journal_path=receipt.with_suffix(receipt.suffix+".running")
    require(not receipt.exists(), "ATTEMPT_ALREADY_HAS_FINAL_RECEIPT")
    journal_raw=raw_file(journal_path)
    journal=read(journal_path)
    checked_journal(journal,env)
    if args.command=="capture":
        pin_out=Path(args.output).absolute()
        require(pin_out.parent == receipt.parent and pin_out.name == "kernel-pin.json",
                "PIN_DESTINATION_NOT_DEDICATED_RECEIPT_LANE")
        require(pin_out != journal_path and pin_out != receipt and
                not pin_out.is_symlink() and not pin_out.exists(), "OUTPUT_COLLISION")
        worker=sample(args.worker_pid);aider=sample(args.aider_pid)
        require(worker is not None and aider is not None, "PROCESSES_NOT_BOTH_ALIVE")
        pin=make_pin(env,journal,worker,aider)
        require(sample(args.worker_pid)==worker and sample(args.aider_pid)==aider,
                "PROCESS_CHANGED_BEFORE_PIN_WRITE")
        require(raw_file(journal_path)==journal_raw and not receipt.exists(),
                "ATTEMPT_CHANGED_BEFORE_PIN_WRITE")
        output=Path(args.output).absolute()
        require(not output.is_relative_to(Path(env["worktree_path"]).resolve()),
                "PIN_INSIDE_WORKTREE_DENIED")
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open("x",encoding="utf-8") as f:
            json.dump(pin,f,sort_keys=True,indent=2);f.write("\n");f.flush();os.fsync(f.fileno())
        return {"status":"PINNED_LAB_EVIDENCE_ONLY","task_id":env["task_id"],
                "pin_sha256":pin["pin_sha256"],"retry_permitted":False}
    pin_path=Path(args.pin).absolute()
    require(pin_path.parent == receipt.parent and pin_path.name == "kernel-pin.json",
            "PIN_NOT_IN_EXCLUSIVE_RECEIPT_LANE")
    pin=read(pin_path)
    checked_pin(env,journal,pin)
    worker=sample(pin["worker"]["pid"]);aider=sample(pin["aider"]["pid"])
    if pin["aider"]["source"]=="PSUTIL_OS_CREATE_TIME":
        group=group_members(pin["aider"]["pgid"])
    else:
        group={"status":"NO_WINDOWS_JOB_OBJECT_IDENTITY","candidate_count":None}
    result=assess(env,journal,pin,worker,aider,group)
    require(raw_file(journal_path)==journal_raw and not receipt.exists(),
            "ATTEMPT_CHANGED_DURING_READBACK")
    result["observed_at_utc"]=datetime.now(timezone.utc).isoformat()
    result["observation_sha256"]=digest(result)
    return result


if __name__=="__main__":
    try:
        print(json.dumps(cli(),sort_keys=True))
    except (Refused,OSError,ValueError,KeyError,TypeError,AssertionError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:160],
                          "retry_permitted":False,"all_orphans_excluded":False}))
        raise SystemExit(2)
