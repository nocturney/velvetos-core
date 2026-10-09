#!/usr/bin/env python3
"""#612 LAB-only Windows Job Object containment for a pinned local Aider worker.

This is ONE invocation, not a scheduler or host selector. The helper is placed
in an unnamed kill-on-close Job BEFORE it may launch the original pinned worker.
No UNKNOWN attempt may ever be retried. Never use for business/production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import ctypes

import vf_office_v2_p0_windows_job_object_lab as native

ALLOWED_LAB_NAME = "AgentEnvelopeLab"
ALLOWED_MODEL = "qwen3.5:9b"
ALLOWED_PORT = 11555
ALLOWED_MODE = "REQUIRE_OS_BIRTH_BEFORE_QA_V1"
MAX_READY_SECONDS = 40
OWNER_TIMEOUT_SECONDS = 14


class Refused(Exception):
    pass


def ensure(ok, why):
    if not ok:
        raise Refused(why)


def read_json(path):
    p = Path(path)
    ensure(not p.is_symlink() and p.is_file() and p.stat().st_size <= 65536,
           "MISSING_OR_UNSAFE_JSON")
    raw = p.read_bytes()
    ensure(len(raw) <= 65536, "JSON_TOO_LARGE")
    value = json.loads(raw.decode("utf-8"))
    ensure(isinstance(value, dict), "JSON_OBJECT_REQUIRED")
    return value


def save_new(path, value):
    path = Path(path)
    ensure(not path.exists(), "NEVER_OVERWRITE_EXISTING_RECORD")
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def sealed_sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,
                                  separators=(",",":")).encode()).hexdigest()


def thin_environment():
    allow = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP")
    result = {k: os.environ[k] for k in allow if k in os.environ}
    result.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8",
                   "GIT_TERMINAL_PROMPT": "0"})
    return result


def check_inputs(worker_script, envelope_path, receipt_path, scratch):
    ensure(os.name == "nt", "WINDOWS_ONLY")
    worker_script = Path(worker_script).resolve()
    env_path = Path(envelope_path).resolve()
    target = Path(receipt_path).resolve()
    directory = Path(scratch).absolute()
    ensure(worker_script.name=="vf_office_v2_p0_local_model_worker.py" and
           worker_script.is_file(), "PINNED_WORKER_SCRIPT_REQUIRED")
    ensure(directory.name.startswith("job-model-") and not directory.exists(),
           "NEW_EXCLUSIVE_SCRATCH_REQUIRED")
    data = read_json(env_path)
    root = Path(data.get("worktree_path", "")).resolve()
    ensure(ALLOWED_LAB_NAME in root.parts and "win-native-job-model-20261009" in root.parts,
           "EXCLUSIVE_SYNTHETIC_TASK_REQUIRED")
    executor = data.get("executor") or {}
    ensure(data.get("authority") == "LAB_LOCAL_MODEL_SYNTHETIC_ONLY_NO_EFFECT" and
           data.get("kernel_birth_capture") == ALLOWED_MODE and
           executor.get("kind") == "LOCAL_AIDER_OLLAMA_SYNTHETIC_V1" and
           executor.get("model") == ALLOWED_MODEL and
           executor.get("ollama_port") == ALLOWED_PORT, "ONLY_PINNED_LOCAL_MODEL_LAB")
    ensure(data.get("budget",{}).get("max_attempts")==1 and
           data.get("budget",{}).get("max_cost_usd")==0,
           "NO_RETRY_OR_PAID_EXECUTION")
    ensure(not target.exists() and
           not target.with_suffix(target.suffix + ".running").exists(),
           "TASK_ALREADY_STARTED_OR_UNKNOWN")
    ensure(target == env_path.parent / "output" / "receipt.json",
           "RECEIPT_SCOPE_MISMATCH")
    ensure(data["task_id"] in env_path.parent.name and
           data["task_id"].startswith("p0-win-job-guard-"),
           "TASK_ID_NOT_BOUNDED")
    ensure(not directory.is_relative_to(root), "SCRATCH_INSIDE_WORKTREE")
    # Existing canonical worker makes the actual model/executable/source trust checks.
    sys.path.insert(0, str(worker_script.parent))
    import vf_office_v2_p0_local_model_worker as worker
    worker.preflight(data)
    return data, worker


def _helper(worker_script, envelope, receipt, scratch):
    root = Path(scratch)
    gate = root / "go.flag"
    deadline = time.monotonic() + OWNER_TIMEOUT_SECONDS
    while not gate.exists() and time.monotonic() < deadline:
        time.sleep(.03)
    ensure(gate.exists(), "SUPERVISOR_DID_NOT_ASSIGN_JOB")
    with (root/"worker-stdout.log").open("xb") as stdout, (root/"worker-stderr.log").open("xb") as stderr:
        proc = subprocess.Popen(
            [sys.executable, "-B", str(worker_script), "run", "--envelope",
             str(envelope), "--receipt", str(receipt)],
            cwd=str(root), env=thin_environment(), stdin=subprocess.DEVNULL,
            stdout=stdout, stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        save_new(root/"worker-pid.json", {"pid": proc.pid})
        return proc.wait(timeout=200)


def owner_handle(api, pid):
    return native.os_success(api.OpenProcess(
        native.PROCESS_QUERY_LIMITED_INFORMATION | native.SYNCHRONIZE,
        False, pid), "PINNED_CHILD_OPEN_FAILED")


def await_json(path, timeout, living=None):
    path=Path(path)
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if living is not None:
            ensure(living.poll() is None, "HELPER_EXITED_BEFORE_MODEL_PIN")
        if path.is_file():
            try:
                return read_json(path)
            except (Refused, ValueError, json.JSONDecodeError):
                pass  # The exclusive writer may not have finished its fsync.
        time.sleep(.05)
    raise Refused("BOUNDED_MODEL_PROCESS_OBSERVATION_TIMEOUT")


def controller(args):
    env,worker=check_inputs(args.worker,args.envelope,args.receipt,args.scratch)
    scratch=Path(args.scratch).absolute()
    scratch.mkdir(parents=True, exist_ok=False)
    api=native.win32()
    ensure(ctypes.sizeof(native.JOBOBJECT_EXTENDED_LIMIT_INFORMATION)==144,
           "NATIVE_WINDOWS_JOB_LAYOUT_MISMATCH")
    obj=None
    helper=None
    worker_h=None
    aider_h=None
    assigned=False
    try:
        opts={"cwd":str(scratch),"env":thin_environment(),
              "stdin":subprocess.DEVNULL,"stdout":subprocess.DEVNULL,
              "stderr":subprocess.DEVNULL,
              "creationflags":subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP}
        helper=subprocess.Popen(
            [sys.executable,"-B",str(Path(__file__).resolve()),"_helper",
             "--worker",str(Path(args.worker).resolve()),"--envelope",str(Path(args.envelope).resolve()),
             "--receipt",str(Path(args.receipt).resolve()),"--scratch",str(scratch)],**opts)
        obj=native.os_success(api.CreateJobObjectW(None,None),"CREATE_JOB_FAILED")
        info=native.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags=native.KILL_ON_JOB_CLOSE
        native.os_success(api.SetInformationJobObject(obj,9,ctypes.byref(info),
                                             ctypes.sizeof(info)),"JOB_CLOSE_POLICY_FAILED")
        hhelper=native.wintypes.HANDLE(int(helper._handle))
        native.os_success(api.AssignProcessToJobObject(obj,hhelper),
                          "ISOLATED_HELPER_ASSIGNMENT_FAILED")
        assigned=True
        ensure(native.job_member(api,hhelper,obj),"HELPER_NOT_IN_JOB")
        helper_birth=native.kernel_birth_us(api,hhelper)
        (scratch/"go.flag").touch()
        meta=await_json(scratch/"worker-pid.json",18,living=helper)
        worker_pid=meta.get("pid")
        ensure(type(worker_pid) is int and worker_pid>1,"INVALID_WORKER_PID")
        worker_h=owner_handle(api,worker_pid)
        ensure(native.job_member(api,worker_h,obj),"MODEL_WORKER_OUTSIDE_JOB")
        worker_birth=native.kernel_birth_us(api,worker_h)
        pin_path=Path(args.receipt).resolve().parent/"kernel-pin.json"
        pin=await_json(pin_path,MAX_READY_SECONDS,living=helper)
        ensure(pin.get("schema")=="velvetos.office-v2.p0-kernel-process-pin.v1" and
               pin.get("task_id")==env["task_id"] and
               pin.get("envelope_sha256")==sealed_sha(env) and
               pin.get("worker",{}).get("pid")==worker_pid and
               pin.get("aider",{}).get("ppid")==worker_pid and
               pin.get("retry_permitted") is False,
               "MODEL_PROCESS_BIRTH_PIN_WRONG_ATTEMPT")
        aider_pid=pin["aider"]["pid"]
        ensure(type(aider_pid) is int and aider_pid>1 and aider_pid!=worker_pid,
               "MODEL_AIDER_PID_INVALID")
        aider_h=owner_handle(api,aider_pid)
        ensure(native.job_member(api,aider_h,obj),"MODEL_AIDER_OUTSIDE_JOB")
        aider_birth=native.kernel_birth_us(api,aider_h)
        ensure(abs(aider_birth-pin["aider"]["birth_us"])<=1_000_000 and
               abs(worker_birth-pin["worker"]["birth_us"])<=1_000_000,
               "NATIVE_JOB_KERNEL_BIRTH_DRIFT")
        ensure(api.WaitForSingleObject(worker_h,0)==native.WAIT_TIMEOUT and
               api.WaitForSingleObject(aider_h,0)==native.WAIT_TIMEOUT,
               "MODELS_EXITED_BEFORE_JOB_CAPTURE")
        record={
            "schema":"vf.office-v2.p0-job-contained-aider-attempt.v0",
            "task_id":env["task_id"],"host":env["host"],
            "mode":args.mode,"original_task_retry_allowed":False,
            "all_possible_escaped_processes_excluded":False,
            "production_authority":"NONE","fleet_scheduler_authority":False,
            "container":"WINDOWS_UNNAMED_JOB_KILL_ON_LAST_HANDLE_CLOSE",
            "helper_pid":helper.pid,"model_worker_pid":worker_pid,
            "aider_pid":aider_pid,"helper_birth_us":helper_birth,
            "model_worker_birth_us":worker_birth,"aider_birth_us":aider_birth,
            "helper_assigned_before_model_spawn":True,
            "all_three_job_members_observed":True,
            "pin_sha256":pin["pin_sha256"],
            "envelope_sha256":sealed_sha(env),
        }
        if args.mode=="interrupt":
            native.os_success(api.CloseHandle(obj),"OWNED_JOB_CLOSE_FAILED")
            obj=None
            waits=[api.WaitForSingleObject(h,5000) for h in
                   (hhelper,worker_h,aider_h)]
            ensure(waits==[native.WAIT_OBJECT_0]*3,
                   "MODEL_DESCENDANT_SURVIVED_OWNED_JOB_CLOSE")
            helper.wait(timeout=5)
            journal=Path(args.receipt).with_suffix(".json.running")
            ensure(journal.is_file() and not Path(args.receipt).exists(),
                   "ORIGINAL_UNKNOWN_JOURNAL_NOT_PRESERVED")
            record.update({"state":"INTERRUPTED_OWNED_JOB_TREE",
                           "same_envelope_reissue_permitted":False,
                           "running_journal_persists":True,
                           "final_receipt_absent":True,
                           "job_descendants_terminated":True,
                           "model_completion_claim":False})
        else:
            wait=helper.wait(timeout=env["budget"]["timeout_seconds"]+40)
            ensure(wait==0,"MODEL_WORKER_FAILED_OR_QA_RED")
            receipt=read_json(args.receipt)
            ensure(receipt.get("state")=="SUCCEEDED",
                   "MODEL_FINISHED_WITHOUT_SUCCESS_RECEIPT")
            verified=worker.check_run(env,receipt)
            ensure(verified.get("status")=="PASS",
                   "INDEPENDENT_MODEL_WORKER_VERIFY_FAILED")
            native.os_success(api.CloseHandle(obj),"OWNED_JOB_CLOSE_FAILED")
            obj=None
            record.update({"state":"SUCCEEDED_LOCAL_MODEL_QA_VERIFIED",
                           "worker_receipt_sha256":receipt["receipt_sha256"],
                           "model_invocations_min":1,
                           "original_task_reissue_permitted":False,
                           "model_completion_claim":True})
        record["selfhash_sha256"]=sealed_sha(record)
        save_new(args.output,record)
        return {"status":"PASS_SCOPED_JOB_CONTAINED_MODEL_LAB",
                "task_id":record["task_id"],"state":record["state"],
                "original_task_retry_allowed":False,
                "selfhash_sha256":record["selfhash_sha256"]}
    finally:
        if aider_h is not None:api.CloseHandle(aider_h)
        if worker_h is not None:api.CloseHandle(worker_h)
        if obj is not None:api.CloseHandle(obj)
        if helper is not None:
            try:helper.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("OWNED_JOB_HELPER_NOT_REAPED",file=sys.stderr)


def main():
    p=argparse.ArgumentParser()
    commands=p.add_subparsers(dest="command",required=True)
    helper=commands.add_parser("_helper",help=argparse.SUPPRESS)
    run=commands.add_parser("run")
    for a in (helper,run):
        a.add_argument("--worker",required=True)
        a.add_argument("--envelope",required=True)
        a.add_argument("--receipt",required=True)
        a.add_argument("--scratch",required=True)
    run.add_argument("--mode",choices=["complete","interrupt"],required=True)
    run.add_argument("--output",required=True)
    args=p.parse_args()
    if args.command=="_helper":
        raise SystemExit(_helper(args.worker,args.envelope,args.receipt,args.scratch))
    result=controller(args)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    try: main()
    except (Refused,native.Refused,ValueError,OSError,TypeError,KeyError,
            AssertionError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:180],
                          "original_task_retry_allowed":False}))
        raise SystemExit(2)
