#!/usr/bin/env python3
"""P0 #612: isolated local Qwen+Aider worker for TWO different synthetic tasks.

Does not change the original v1 Worker. An original PREPARED_ONLY candidate
can only be read and rechecked; admission copies it into a NEW unique Git
clone and creates a separately controlled, one-attempt LAB Task Envelope.
No scheduler, lease, production effects, automatic retry or blind recovery.
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
import signal
import subprocess
import sys
import tempfile
import time
import vf_office_v2_p0_local_model_worker as old
import vf_office_v2_p0_diverse_task_fixtures as fixtures
import vf_office_v2_p0_kernel_identity as kernel
import vf_office_v2_continuity as continuity

SCHEMA = "velvetos.office-v2.p0-diverse-execution-envelope.v0"
RECEIPT = "velvetos.office-v2.p0-diverse-execution-receipt.v0"
AUTH = "LAB_DIVERSE_SYNTHETIC_QWEN_ONE_ATTEMPT_NO_EFFECT"
TASK = re.compile(r"p0-diverse-run-[A-Za-z0-9_.-]{8,94}\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
HOST_MODEL = {"Chris": ("qwen3.5:9b", 11555),
              "MacMiniOffice.local": ("qwen3.5:4b", 11556)}


PUBLIC_SPEC_PROFILE = "PUBLIC_SPEC_REMINDER_V1"
PUBLIC_SPEC_STATE_PROFILE = "PUBLIC_SPEC_STATE_MACHINE_V2"
PUBLIC_SPEC_INT_PROFILE = "PUBLIC_SPEC_EXACT_INT_ENDPOINT_V3"
# Only reminders already contained in the public fixture specification.
# Do NOT expose private hidden QA, source solutions or user/business data.
PUBLIC_SPEC_APPENDICES = {
    "canonical-tag-v1": (
        "PUBLIC SPEC REMINDER (not hidden tests): Lowercase the entire input "
        "BEFORE testing for ASCII a-z/0-9. A maximal run of other characters "
        "becomes exactly one underscore, including repeated punctuation and "
        "non-ASCII characters. Strip underscores from both ends. Return "
        "untitled only when the resulting tag has no ASCII letters/digits. "
        "Change only canonical_tag.py; preserve the function signature."
    ),
    "merge-windows-v1": (
        "PUBLIC SPEC REMINDER (not hidden tests): First validate each interval "
        "is a TUPLE of exactly two elements, NOT a list. Both endpoints must "
        "have type exactly int (bool is not permitted), and start must not "
        "exceed end; otherwise raise ValueError. Sorting precedes merging. "
        "For inclusive integer intervals, directly adjacent windows merge "
        "when next_start <= previous_end + 1. Return a new list of tuples. "
        "Change only windows_merge.py; preserve the function signature."
    ),
}


def approved_prompt_bytes(fixture_id, profile):
    require(fixture_id in PUBLIC_SPEC_APPENDICES, "UNAPPROVED_FIXTURE")
    base = fixtures.catalog()[fixture_id]["prompt"]
    require(profile in (None, PUBLIC_SPEC_PROFILE, PUBLIC_SPEC_STATE_PROFILE,
                        PUBLIC_SPEC_INT_PROFILE),
            "UNAPPROVED_PUBLIC_SPEC_PROMPT_PROFILE")
    if profile == PUBLIC_SPEC_PROFILE:
        base += "\n\n" + PUBLIC_SPEC_APPENDICES[fixture_id]
    if profile == PUBLIC_SPEC_STATE_PROFILE:
        require(fixture_id == "canonical-tag-v1",
                "STATE_MACHINE_ONLY_CANONICAL_TAG")
        base += (
            "\n\nPUBLIC SPEC STATE REMINDER (not hidden QA): After lowering "
            "the whole input, scan one character at a time. On the FIRST "
            "non-ASCII-alphanumeric character immediately after a letter "
            "or digit, emit ONE underscore separator. On any additional "
            "non-alphanumeric characters in the SAME consecutive run, "
            "emit nothing else. Do not reverse that first-separator "
            "condition. Remove leading/trailing separators, and use "
            "untitled for an all-separator input. Treat Unicode letters "
            "as non-ASCII separators. Change only canonical_tag.py."
        )
    if profile == PUBLIC_SPEC_INT_PROFILE:
        require(fixture_id == "merge-windows-v1",
                "EXACT_INT_ONLY_MERGE_WINDOWS")
        base += (
            "\n\nPUBLIC EXACT-TYPE REMINDER (already in task specification, "
            "NOT hidden QA): Every endpoint must be a Python integer with "
            "type(endpoint) is int, exactly. Do not rely on "
            "isinstance(endpoint, int) because int subclasses also pass "
            "that test but violate the exact-type contract. Reject bool, "
            "int subclasses, floats, non-tuple pairs, non-pairs, and "
            "reversed intervals with ValueError before sorting or merging. "
            "Keep the documented inclusive adjacent merge behavior. "
            "Change only windows_merge.py, not any tests."
        )
    return base.encode("utf-8")


class Refused(Exception):
    pass


def require(ok, reason):
    if not ok: raise Refused(reason)


def seal(row):
    return old.digest(row)


def read(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink() and
            0<p.stat().st_size<=1048576,"PINNED_JSON_MISSING_OR_UNSAFE")
    return old.get_json(p)


def birth_same(row):
    actual=kernel.sample(row["pid"])
    return actual is not None and kernel.match(row,actual)=="SAME_KERNEL_INSTANCE_AT_SNAPSHOT"


def task_file(p):
    p=Path(p)
    require(p.is_absolute() and p.name=="envelope.json"
            and TASK.fullmatch(p.parent.name)
            and p.parent.parent.name.startswith("p0-diverse-execution-")
            and p.parent.parent.parent.name=="AgentEnvelopeLab"
            and not any(x.is_symlink() for x in
                        (p,p.parent,p.parent.parent,p.parent.parent.parent)),
            "DIVERSE_NEW_LAB_ENVELOPE_ONLY")
    return p


def candidate_check(path):
    p=Path(path)
    result=fixtures.verify_candidate(str(p))
    require(result.get("status")==
            "PASS_PREPARED_ONLY_INDEPENDENT_BYTE_GIT_QA_READBACK",
            "PREPARED_CANDIDATE_INVALID")
    original=read(p)
    require(original.get("model_invocations")==0 and
            original.get("approved_model_executor") is None and
            original.get("host")==platform.node(),
            "CANDIDATE_HOST_OR_AUTHORITY_CHANGED")
    return original,fixtures.catalog()[original["fixture_id"]]


def check(env, fresh):
    require(isinstance(env,dict) and env.get("schema")==SCHEMA
            and env.get("authority")==AUTH
            and env.get("issue_url")==old.ISSUE
            and isinstance(env.get("task_id"),str)
            and TASK.fullmatch(env["task_id"])
            and env.get("host")==platform.node(),
            "BAD_TASK_ENVELOPE_OR_HOST")
    for key in ("production_authority","automatic_retry",
                "canonical_fleet_lease","distributed_fencing_verified"):
        require(env.get(key) is False,"UNGRANTED_AUTHORITY_"+key)
    repo=Path(env["worktree_path"])
    require(repo.is_absolute() and repo.name=="repo"
            and repo.parent.name==env["task_id"]
            and repo.parent.parent.name.startswith("p0-diverse-execution-")
            and repo.parent.parent.parent.name=="AgentEnvelopeLab"
            and repo.is_dir() and (repo/".git").is_dir()
            and not repo.is_symlink(), "NOT_NEW_ISOLATED_GIT_REPO")
    original_path=Path(env["candidate_file"])
    require(original_path.is_absolute() and
            old.hash_file(original_path)==env.get("candidate_raw_sha256"),
            "ORIGINAL_CANDIDATE_BYTES_CHANGED")
    origin,spec=candidate_check(original_path)
    require(env.get("candidate_proof_sha256")==origin["proof_sha256"]
            and env.get("fixture_id")==origin["fixture_id"]
            and env.get("base_sha")==origin["base_sha"]
            and env.get("target_file")==spec["target"]
            and env.get("test_file")==spec["test"]
            and env.get("seed_sha256")==origin["target_seed_sha256"]
            and env.get("visible_test_sha256")==origin["visible_test_sha256"]
            and env.get("branch")=="lab-p0-diverse-run-"+env["task_id"],
            "WRONG_ORIGINAL_TARGET_OR_GIT_BASE")
    require(old.git(repo,"rev-parse","HEAD")==env["base_sha"]
            and old.git(repo,"branch","--show-current")==env["branch"]
            and old.modified(repo)==([] if fresh else [spec["target"]]),
            "BASE_BRANCH_OR_EXACT_CHANGED_PATHS_DRIFT")
    target,test=repo/spec["target"],repo/spec["test"]
    require(target.is_file() and test.is_file()
            and not target.is_symlink() and not test.is_symlink()
            and old.hash_file(test)==env["visible_test_sha256"]
            and (not fresh or old.hash_file(target)==env["seed_sha256"]),
            "TARGET_OR_TEST_BYTES_DRIFT")
    for field,filename in (("prompt_file","task.prompt.txt"),
                           ("hidden_file","hidden.qa.py"),
                           ("checkpoint_file","checkpoint.json")):
        p=repo.parent/filename
        require(env.get(field)==str(p.resolve()) and p.is_file() and
                not p.is_symlink(),"PINNED_TASK_INPUT_LOCATION_DRIFT")
    require(old.hash_file(repo.parent/"task.prompt.txt")==env.get("prompt_sha256")
            and old.hash_file(repo.parent/"hidden.qa.py")==env.get("hidden_sha256")
            and old.hash_file(repo.parent/"checkpoint.json")==env.get("checkpoint_sha256"),
            "PINNED_TASK_INPUT_BYTES_CHANGED")
    require((repo.parent/"task.prompt.txt").read_bytes() ==
            approved_prompt_bytes(env["fixture_id"], env.get("prompt_profile")),
            "PUBLIC_SPEC_PROMPT_PROVENANCE_DRIFT")
    require((repo.parent/"hidden.qa.py").read_bytes() ==
            spec["hidden"].encode("utf-8"),
            "ORIGINAL_QA_FIXTURE_PROVENANCE_DRIFT")
    before=read(repo.parent/"checkpoint.json")
    require(not continuity.required_shape(before)
            and before.get("active_external_effects")==[]
            and before.get("code_baseline")=={
              "repo":"nocturney/velvetos-core","base_sha":env["base_sha"],
              "branch":env["branch"],"worktree_path":str(repo.resolve())},
            "CONTINUITY_BASE_DRIFT")
    model,port=HOST_MODEL.get(platform.node(),(None,None))
    exe=env.get("executor") or {}
    require(exe.get("kind")=="LOCAL_AIDER_OLLAMA_DIVERSE_LAB_V0"
            and exe.get("model")==model and exe.get("ollama_port")==port
            and isinstance(exe.get("model_digest"),str)
            and SHA.fullmatch(exe["model_digest"]),
            "WRONG_LOCAL_EXECUTOR_OR_PORT")
    aider=old.abs_file(exe["aider_binary"],outside=repo)
    require(aider.name.lower() in ("aider","aider.exe")
            and old.hash_file(aider)==exe.get("aider_sha256"),
            "AIDER_EXACT_BINARY_CHANGED")
    budget=env.get("budget") or {}
    require(type(budget.get("timeout_seconds")) is int
            and 40<=budget["timeout_seconds"]<=180
            and type(budget.get("max_attempts")) is int
            and budget["max_attempts"]==1
            and type(budget.get("max_cost_usd")) is int
            and budget["max_cost_usd"]==0,"COST_OR_UNSAFE_AUTO_ATTEMPTS")
    return repo,spec


def admit(root_raw,task,candidate_raw,aider_raw,model,port,timeout,prompt_profile=None):
    parent=Path(root_raw)
    require(parent.is_absolute() and
            parent.parent.name=="AgentEnvelopeLab"
            and parent.name.startswith("p0-diverse-execution-")
            and not parent.exists() and not parent.is_symlink()
            and isinstance(task,str) and TASK.fullmatch(task)
            and (model,port)==HOST_MODEL.get(platform.node())
            and type(timeout) is int and 40<=timeout<=180,
            "FRESH_LAB_HOST_MODEL_ADMISSION_DENIED")
    candidate_path=Path(candidate_raw)
    origin,spec=candidate_check(candidate_path)
    prompt_bytes=approved_prompt_bytes(origin["fixture_id"], prompt_profile)
    aider=old.abs_file(aider_raw)
    require(aider.name.lower() in ("aider","aider.exe"),
            "EXPECTED_AIDER_BINARY_REQUIRED")
    model_digest=old.remote_model_tag(model,port)
    require(bool(SHA.fullmatch(model_digest)),"MODEL_DIGEST_NOT_PINNED")
    parent.mkdir(exist_ok=False)
    dest=parent/task
    dest.mkdir(exist_ok=False)
    root=dest/"repo"
    cp=subprocess.run(["git","-c","core.autocrlf=false","clone","--quiet","--no-hardlinks","--local",
                       str(candidate_path.parent/"repo"),str(root)],
                      capture_output=True,timeout=28)
    require(cp.returncode==0 and (root/".git").is_dir(),
            "EXCLUSIVE_GIT_CLONE_FAILED")
    require(old.git(root,"rev-parse","HEAD")==origin["base_sha"],
            "PREPARED_COMMIT_NOT_PRESERVED")
    branch="lab-p0-diverse-run-"+task
    cp=subprocess.run(["git","-C",str(root),"switch","-c",branch],
                      capture_output=True,timeout=14)
    require(cp.returncode==0 and not old.modified(root),
            "EXECUTION_GIT_BRANCH_NOT_FRESH")
    (dest/"task.prompt.txt").write_bytes(prompt_bytes)
    (dest/"hidden.qa.py").write_bytes((candidate_path.parent/"hidden.qa.py").read_bytes())
    need_seed=root/spec["target"]
    require(old.hash_file(need_seed)==origin["target_seed_sha256"]
            and old.hash_file(root/spec["test"])==origin["visible_test_sha256"],
            "PREPARED_GIT_SEED_DRIFT")
    before=continuity.self_test_manifest()
    before["active_external_effects"]=[]
    before["code_baseline"]={"repo":"nocturney/velvetos-core",
                             "base_sha":origin["base_sha"],
                             "branch":branch,"worktree_path":str(root.resolve())}
    checkpoint=dest/"checkpoint.json"
    continuity.write(checkpoint,continuity.seal(before))
    env={
      "schema":SCHEMA,"authority":AUTH,"issue_url":old.ISSUE,
      "task_id":task,"host":platform.node(),
      "worktree_path":str(root.resolve()),"base_sha":origin["base_sha"],
      "branch":branch,"fixture_id":origin["fixture_id"],
      "target_file":spec["target"],"test_file":spec["test"],
      "seed_sha256":origin["target_seed_sha256"],
      "visible_test_sha256":origin["visible_test_sha256"],
      "candidate_file":str(candidate_path.resolve()),
      "candidate_raw_sha256":old.hash_file(candidate_path),
      "candidate_proof_sha256":origin["proof_sha256"],
      "prompt_file":str((dest/"task.prompt.txt").resolve()),
      "prompt_sha256":old.hash_file(dest/"task.prompt.txt"),
      "hidden_file":str((dest/"hidden.qa.py").resolve()),
      "hidden_sha256":old.hash_file(dest/"hidden.qa.py"),
      "checkpoint_file":str(checkpoint.resolve()),
      "checkpoint_sha256":old.hash_file(checkpoint),
      "executor":{"kind":"LOCAL_AIDER_OLLAMA_DIVERSE_LAB_V0",
                  "model":model,"model_digest":model_digest,"ollama_port":port,
                  "aider_binary":str(aider.resolve()),
                  "aider_sha256":old.hash_file(aider)},
      "budget":{"timeout_seconds":timeout,"max_attempts":1,"max_cost_usd":0},
      "production_authority":False,"automatic_retry":False,
      "canonical_fleet_lease":False,"distributed_fencing_verified":False,
    }
    if prompt_profile is not None:
        env["prompt_profile"]=prompt_profile
    check(env,fresh=True)
    old.save_new(dest/"envelope.json",env)
    return {"status":"ADMITTED_FRESH_LAB_ONLY_NO_MODEL_EXECUTION",
            "task_id":task,"envelope":str(dest/"envelope.json"),
            "receipt":str(dest/"output"/"receipt.json"),
            "model_invocations":0,"production_authority":False}


def independent_qa(root,spec,hidden_path,code):
    with tempfile.TemporaryDirectory(prefix="vf-office-p0-diverse-qa-") as td:
        replay=Path(td)/"checkout"
        clone=subprocess.run(["git","clone","--quiet","--local",
                              "--no-hardlinks",str(root),str(replay)],
                             capture_output=True,timeout=26)
        require(clone.returncode==0,"INDEPENDENT_GIT_QA_CLONE_FAILED")
        (replay/spec["target"]).write_bytes(code)
        env={k:os.environ[k] for k in
             ("PATH","SYSTEMROOT","WINDIR","TEMP","TMP","TMPDIR")
             if k in os.environ}
        env["PYTHONDONTWRITEBYTECODE"]="1"
        env["PYTHONIOENCODING"]="utf-8"
        unit=subprocess.run([sys.executable,"-B","-m","unittest",
                             "discover","-s","tests","-q"],
                            cwd=replay,env=env,capture_output=True,timeout=22)
        hidden=subprocess.run([sys.executable,"-B","-c",
                               Path(hidden_path).read_text(encoding="utf-8")],
                              cwd=replay,env=env,capture_output=True,timeout=22)
        paths=old.modified(replay)
        matched="Ran 3 tests" in unit.stderr.decode("utf-8","replace")
        hidden_ok=hidden.stdout.strip()==b"QA_HIDDEN_12_PASS"
        return {"pass":unit.returncode==0 and hidden.returncode==0
                       and matched and hidden_ok and paths==[spec["target"]],
                "unit_3_verified":matched,"hidden_12_verified":hidden_ok,
                "unit_exit":unit.returncode,"hidden_exit":hidden.returncode,
                "replay_changed_paths":paths,
                "artifact_sha256":old.hash_file(replay/spec["target"]),
                "hidden_stdout_sha256":hashlib.sha256(hidden.stdout).hexdigest()}


def born_pin(env,running,child):
    worker=kernel.sample(os.getpid())
    aider=kernel.sample(child.pid)
    require(worker is not None and aider is not None
            and aider["ppid"]==worker["pid"]
            and aider["birth_us"]>=worker["birth_us"],
            "OS_BIRTH_CHILD_LINEAGE_MISSING")
    row={"schema":"velvetos.office-v2.p0-diverse-worker-birth-pin.v0",
         "task_id":env["task_id"],
         "envelope_sha256":seal(env),"journal_sha256":seal(running),
         "worker":worker,"aider":aider,"all_orphans_excluded":False,
         "retry_permitted":False,
         "authority":"READ_ONLY_BIRTH_NO_RECOVERY"}
    row["pin_sha256"]=seal(row)
    require(birth_same(worker) and birth_same(aider),
            "KERNEL_BIRTH_CHANGED_DURING_CAPTURE")
    return row


def _stop_owned_direct_child(child):
    """Bounded Popen-handle cleanup; POSIX group only with live OS lineage.

    A verified new session may contain ordinary descendants. Detached/reparented
    descendants and Windows processes outside the Popen handle remain UNKNOWN.
    Never issue a PID-only kill or assert that all orphans were excluded.
    """
    real = isinstance(child, subprocess.Popen)
    if real and os.name != "nt":
        try:
            # The live, unreaped Popen leader prevents accidental PID reuse.
            if child.poll() is None:
                observed = kernel.sample(child.pid)
                if (observed is not None and observed["ppid"] == os.getpid()
                        and observed["pgid"] == child.pid
                        and os.getsid(child.pid) == child.pid):
                    os.killpg(child.pid, signal.SIGKILL)
        except (OSError, kernel.Refused):
            pass  # Uncertain OS identity: stop the direct handle only.
    try:
        if not real or child.poll() is None:
            child.kill()
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        child.communicate(timeout=3)
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return bool(real and child.poll() is not None)


def _persist_unknown_child(out, env, child, phase, reaped):
    """Best-effort additive evidence; the original RUNNING journal is immutable."""
    record = {
        "schema": "velvetos.office-v2.p0-aider-child-cleanup-unknown.v1",
        "state": "UNKNOWN", "task_id": env["task_id"],
        "envelope_sha256": seal(env), "phase": phase,
        "direct_child_pid": child.pid,
        "direct_child_reaped": bool(reaped),
        "all_orphans_excluded": False,
        "retry_permitted": False, "production_authority": False,
        "original_running_journal_preserved": (out/"receipt.json.running").is_file(),
        "observed_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        old.save_new(out/"child-cleanup.unknown.json", record)
    except (OSError, old.Refuse, ValueError):
        # The fsynced RUNNING journal already denies replay, even on disk errors.
        pass


def _guarded_capture_and_wait(child, capture, wait):
    """Stop the owned process on pre-guard errors and unexpected IO failures."""
    try:
        pin = capture()
    except BaseException:
        _stop_owned_direct_child(child)
        raise
    try:
        stdout, stderr = wait()
    except subprocess.TimeoutExpired:
        raise  # The caller records UNKNOWN and performs bounded owned cleanup.
    except BaseException:
        _stop_owned_direct_child(child)
        raise
    return pin, stdout, stderr


def verify_receipt(env,receipt):
    require(receipt.get("schema")==RECEIPT
            and receipt.get("state")=="SUCCEEDED"
            and receipt.get("receipt_sha256")==
                seal({k:v for k,v in receipt.items() if k!="receipt_sha256"})
            and receipt.get("task_id")==env["task_id"]
            and receipt.get("envelope_sha256")==seal(env)
            and receipt.get("model_invocations_min")==1
            and receipt.get("exact_model_calls") is None
            and receipt.get("additional_api_spend_usd")==0
            and receipt.get("production_authority") is False,
            "NOT_INDEPENDENTLY_VALID_RECEIPT")
    root,spec=check(env,fresh=False)
    output=root.parent/"output"
    require(receipt.get("base_sha")==env["base_sha"]
            and receipt.get("branch")==env["branch"]
            and receipt.get("model")==env["executor"]["model"]
            and receipt.get("model_digest")==env["executor"]["model_digest"]
            and receipt.get("changed_paths")==[spec["target"]]
            and receipt.get("source_sha256")==old.hash_file(root/spec["target"]),
            "SOURCE_BRANCH_OR_MODEL_RECEIPT_DRIFT")
    pin=read(output/"kernel-pin.json")
    require(pin.get("schema")=="velvetos.office-v2.p0-diverse-worker-birth-pin.v0"
            and pin.get("task_id")==env["task_id"]
            and pin.get("envelope_sha256")==seal(env)
            and pin.get("pin_sha256")==
                seal({k:v for k,v in pin.items() if k!="pin_sha256"})
            and pin.get("all_orphans_excluded") is False
            and pin.get("retry_permitted") is False
            and pin.get("aider",{}).get("ppid")==pin.get("worker",{}).get("pid")
            and receipt.get("kernel_pin_sha256")==pin["pin_sha256"]
            and receipt.get("kernel_pin_file_sha256")==
                old.hash_file(output/"kernel-pin.json"),
            "PIN_OR_NATIVE_BIRTH_RECEIPT_DRIFT")
    kernel.require_row(pin["worker"])
    kernel.require_row(pin["aider"])
    original_running={"state":"RUNNING","task_id":env["task_id"],
                      "envelope_sha256":seal(env),"host":env["host"],
                      "started_at":receipt["started_at"],
                      "unknown_outcome_rule":"NO_BLIND_RETRY"}
    require(pin.get("journal_sha256")==seal(original_running)
            and pin["worker"]["source"]==pin["aider"]["source"],
            "ORIGINAL_FSYNC_RUNNING_JOURNAL_OR_BACKEND_CHANGED")
    for log in ("stdout.log","stderr.log","llm.history.log"):
        key=log.replace(".","_")+"_sha256"
        require((output/log).is_file() and
                old.hash_file(output/log)==receipt.get(key),
                "AIDER_LOG_CHANGED_"+log)
    after=output/"checkpoint.after.json"
    before=Path(env["checkpoint_file"])
    require(after.is_file() and
            old.hash_file(before)==receipt.get("checkpoint_before_sha256")
            and old.hash_file(after)==receipt.get("checkpoint_after_sha256")
            and continuity.verify(read(before),read(after))["status"]=="PASS",
            "CONTINUITY_REPLAY_FAILED")
    qa=independent_qa(root,spec,env["hidden_file"],
                      (root/spec["target"]).read_bytes())
    require(qa["pass"] and qa==receipt.get("independent_qa"),
            "INDEPENDENT_HIDDEN_QA_DRIFT")
    return {"status":"PASS","task_id":env["task_id"],
            "model_invocations_min":1,"exact_model_calls_known":False,
            "production_authority":False,"cross_host_lease_proven":False}


def execute(raw_env,raw_receipt):
    epath=task_file(raw_env)
    out=epath.parent/"output"
    receipt_path=Path(raw_receipt)
    require(receipt_path==out/"receipt.json"
            and not receipt_path.exists()
            and not (out/"receipt.json.running").exists(),
            "NO_DUPLICATE_OR_UNKNOWN_RETRY")
    env=read(epath)
    root,spec=check(env,fresh=True)
    require(old.remote_model_tag(env["executor"]["model"],
            env["executor"]["ollama_port"])==env["executor"]["model_digest"],
            "PINNED_LOCAL_MODEL_CHANGED")
    require(not out.exists() or not any(out.iterdir()),
            "OUTPUT_ALREADY_USED_OR_UNKNOWN")
    out.mkdir(exist_ok=True)
    running={"state":"RUNNING","task_id":env["task_id"],
             "envelope_sha256":seal(env),"host":platform.node(),
             "started_at":datetime.now(timezone.utc).isoformat(),
             "unknown_outcome_rule":"NO_BLIND_RETRY"}
    old.save_new(out/"receipt.json.running",running)
    for name in ("home","config","data","cache","tmp","roaming","local","programdata"):
        (out/name).mkdir()
    (out/"empty.env").write_bytes(b"")
    (out/"empty.yml").write_bytes(b"{}\n")
    args=old.command(Path(env["executor"]["aider_binary"]),
                     env["executor"]["model"],Path(env["prompt_file"]),out)
    for flag,rel in (("--file",spec["target"]),("--read",spec["test"])):
        require(args.count(flag)==1,"UNEXPECTED_ORIGINAL_AIDER_CLI_FORMAT")
        args[args.index(flag)+1]=rel
    kw={"cwd":root,
        "env":old.safe_executor_environment(out,env["executor"]["ollama_port"]),
        "stdin":subprocess.DEVNULL,
        "stdout":subprocess.PIPE,
        "stderr":subprocess.PIPE}
    if os.name=="nt":kw["creationflags"]=subprocess.CREATE_NEW_PROCESS_GROUP
    else:kw["start_new_session"]=True
    started=time.monotonic()
    child=subprocess.Popen(args,**kw)
    def capture_pin():
        pin=born_pin(env,running,child)
        old.save_new(out/"kernel-pin.json",pin)
        return pin
    try:
        pin,stdout,stderr=_guarded_capture_and_wait(
            child,capture_pin,
            lambda:child.communicate(timeout=env["budget"]["timeout_seconds"]))
    except subprocess.TimeoutExpired:
        reaped=_stop_owned_direct_child(child)
        _persist_unknown_child(out,env,child,"TIMEOUT",reaped)
        # Detached descendants may survive; never remove journal or auto retry.
        return {"status":"TIMED_OUT_UNKNOWN_OUTCOME","task_id":env["task_id"],
                "original_running_journal_preserved":True,
                "direct_child_reaped":reaped,"all_orphans_excluded":False}
    except BaseException:
        # The guarded helper already stopped the Popen child where possible.
        # Record the uncertainty without overwriting the fsynced RUNNING journal.
        _persist_unknown_child(out,env,child,"PRE_PIN_OR_COMMUNICATE",child.poll() is not None)
        raise
    for filename,contents in (("stdout.log",stdout),("stderr.log",stderr)):
        (out/filename).write_bytes(contents)
    log=out/"llm.history.log"
    if not log.exists():log.write_bytes(b"")
    require(child.returncode==0 and old.modified(root)==[spec["target"]]
            and old.hash_file(root/spec["target"])!=env["seed_sha256"],
            "MODEL_EXIT_OR_CHANGED_PATHS_UNKNOWN")
    qa=independent_qa(root,spec,env["hidden_file"],
                      (root/spec["target"]).read_bytes())
    require(qa["pass"] is True,"INDEPENDENT_QA_FAILED_UNKNOWN_JOURNAL")
    before=read(env["checkpoint_file"])
    after=continuity.compact_manifest(before,pressure_score=0.0)
    require(continuity.verify(before,after)["status"]=="PASS",
            "NEW_CONTEXT_CHECKPOINT_FAILED")
    old.save_new(out/"checkpoint.after.json",after)
    result={
      "schema":RECEIPT,"state":"SUCCEEDED","task_id":env["task_id"],
      "envelope_sha256":seal(env),"base_sha":env["base_sha"],
      "branch":env["branch"],"model":env["executor"]["model"],
      "model_digest":env["executor"]["model_digest"],
      "started_at":running["started_at"],
      "elapsed_seconds":round(time.monotonic()-started,3),
      "exit_code":child.returncode,"changed_paths":[spec["target"]],
      "source_sha256":old.hash_file(root/spec["target"]),
      "stdout_log_sha256":old.hash_file(out/"stdout.log"),
      "stderr_log_sha256":old.hash_file(out/"stderr.log"),
      "llm_history_log_sha256":old.hash_file(log),
      "kernel_pin_sha256":pin["pin_sha256"],
      "kernel_pin_file_sha256":old.hash_file(out/"kernel-pin.json"),
      "checkpoint_before_sha256":old.hash_file(env["checkpoint_file"]),
      "checkpoint_after_sha256":old.hash_file(out/"checkpoint.after.json"),
      "independent_qa":qa,
      "model_invocations_min":1,"exact_model_calls":None,
      "local_model_usage_tokens":None,"additional_api_spend_usd":0,
      "production_authority":False,"autonomous_recovery_proven":False,
      "distributed_fencing_verified":False,"all_orphans_excluded":False,
    }
    result["receipt_sha256"]=seal(result)
    verify_receipt(env,result) # replays independent QA BEFORE publishing SUCCESS
    old.save_new(receipt_path,result)
    (out/"receipt.json.running").unlink()
    return {"status":"SUCCEEDED","task_id":env["task_id"],
            "elapsed_seconds":result["elapsed_seconds"],
            "source_sha256":result["source_sha256"],
            "receipt_sha256":result["receipt_sha256"],
            "independent_qa_pass":qa["pass"],
            "production_authority":False}



AUDIT_SCHEMA = "velvetos.office-v2.p0-diverse-manual-failed-qa-readback.v0"


def audit_record_validate(row):
    require(isinstance(row,dict) and row.get("schema")==AUDIT_SCHEMA
            and row.get("status")=="FAILED_INDEPENDENT_QA_NO_SUCCESS"
            and row.get("authority")=="READ_ONLY_DIAGNOSIS_NO_RECOVERY",
            "NOT_OWNED_QA_FAILURE_AUDIT")
    require(row.get("original_journal_preserved") is True
            and row.get("original_success_receipt_absent") is True
            and row.get("original_attempt_retried") is False
            and row.get("automatic_requeue_authorized") is False
            and row.get("all_detached_descendants_excluded") is False
            and row.get("production_authority") is False
            and row.get("model_calls_during_audit")==0,
            "FALSE_RECOVERY_AUTHORITY")
    for field in ("envelope_sha256","journal_sha256_raw","kernel_pin_sha256_raw",
                  "observed_source_sha256"):
        require(isinstance(row.get(field),str) and SHA.fullmatch(row[field]),
                "MISSING_OR_FALSE_ORIGINAL_RAW_HASH")
    qa=row.get("independent_failed_qa") or {}
    require(qa.get("pass") is False
            and qa.get("unit_exit") in (0,1)
            and qa.get("hidden_exit") in (0,1)
            and (qa["unit_exit"] or qa["hidden_exit"]),
            "NOT_A_CONFIRMED_FAILED_QA")
    for owner in ("worker","aider"):
        state=(row.get("historical_native_process_readback") or {}).get(owner)
        require(state in ("HISTORICAL_PID_ABSENT",
                          "PID_REUSED_DIFFERENT_BIRTH"),
                "LIVE_OR_UNKNOWN_HISTORIC_PROCESS")
    require(row.get("audit_sha256")==
            seal({k:v for k,v in row.items() if k!="audit_sha256"}),
            "READ_ONLY_AUDIT_SEAL_DRIFT")
    return True


def audit_failed_qa(raw_env,raw_audit_root):
    task=task_file(raw_env)
    env=read(task)
    root,spec=check(env,fresh=False)
    out=root.parent/"output"
    journal_path=out/"receipt.json.running"
    pin_path=out/"kernel-pin.json"
    require(journal_path.is_file() and pin_path.is_file()
            and not (out/"receipt.json").exists(),
            "NOT_ORIGINAL_NO_SUCCESS_RUNNING_JOURNAL")
    original={
        "envelope_sha256":old.hash_file(task),
        "journal_sha256_raw":old.hash_file(journal_path),
        "kernel_pin_sha256_raw":old.hash_file(pin_path),
        "observed_source_sha256":old.hash_file(root/spec["target"]),
    }
    journal=read(journal_path)
    pin=read(pin_path)
    require(journal.get("state")=="RUNNING"
            and journal.get("unknown_outcome_rule")=="NO_BLIND_RETRY"
            and journal.get("task_id")==env["task_id"]
            and journal.get("envelope_sha256")==seal(env)
            and pin.get("journal_sha256")==seal(journal)
            and pin.get("envelope_sha256")==seal(env)
            and pin.get("task_id")==env["task_id"]
            and pin.get("pin_sha256")==
                seal({k:v for k,v in pin.items() if k!="pin_sha256"}),
            "NATIVE_PIN_OR_RUNNING_JOURNAL_DRIFT")
    results={}
    for label in ("worker","aider"):
        expected=pin[label]
        kernel.require_row(expected)
        actual=kernel.sample(expected["pid"])
        verdict=kernel.match(expected,actual)
        require(verdict!="SAME_KERNEL_INSTANCE_AT_SNAPSHOT",
                "ORIGINAL_MODEL_CHILD_STILL_RUNNING")
        results[label]=verdict
    qa=independent_qa(root,spec,env["hidden_file"],
                      (root/spec["target"]).read_bytes())
    require(qa["pass"] is False,
            "DO_NOT_MARK_WORKING_CODE_A_FAILED_QA")
    report={
        "schema":AUDIT_SCHEMA,
        "status":"FAILED_INDEPENDENT_QA_NO_SUCCESS",
        "authority":"READ_ONLY_DIAGNOSIS_NO_RECOVERY",
        "task_id":env["task_id"],"host":platform.node(),
        "fixture_id":env["fixture_id"],"base_sha":env["base_sha"],
        "branch":env["branch"],"model":env["executor"]["model"],
        "model_digest":env["executor"]["model_digest"],
        "observed_utc":datetime.now(timezone.utc).isoformat(),
        **original,
        "kernel_pin_selfhash":pin["pin_sha256"],
        "historical_native_process_readback":results,
        "independent_failed_qa":qa,
        "original_journal_preserved":True,
        "original_success_receipt_absent":True,
        "original_attempt_retried":False,
        "automatic_requeue_authorized":False,
        "all_detached_descendants_excluded":False,
        "production_authority":False,"model_calls_during_audit":0,
    }
    for field,path in (("envelope_sha256",task),
                       ("journal_sha256_raw",journal_path),
                       ("kernel_pin_sha256_raw",pin_path),
                       ("observed_source_sha256",root/spec["target"])):
        require(old.hash_file(path)==original[field],
                "ORIGINAL_FAILED_SOURCE_CHANGED_DURING_READ")
    require(not (out/"receipt.json").exists(),
            "SUCCESS_RECEIPT_CREATED_WHILE_AUDITING")
    report["audit_sha256"]=seal(report)
    audit_record_validate(report)
    dest=Path(raw_audit_root)
    require(dest.is_absolute()
            and dest.parent.name=="AgentEnvelopeLab"
            and dest.name.startswith("p0-diverse-audit-")
            and not dest.exists() and not dest.is_symlink(),
            "FRESH_AUDIT_STORAGE_ONLY")
    dest.mkdir(exist_ok=False)
    old.save_new(dest/"audit.json",report)
    return {"status":report["status"],"task_id":report["task_id"],
            "audit_file":str(dest/"audit.json"),
            "audit_sha256":report["audit_sha256"],
            "unit_exit":qa["unit_exit"],"hidden_exit":qa["hidden_exit"],
            "original_journal_preserved":True,"new_model_calls":0,
            "automatic_requeue_authorized":False}


def verify_failed_qa_audit(raw):
    report=read(raw)
    audit_record_validate(report)
    return {"status":"PASS_OFFLINE_HISTORICAL_FAILED_QA_REPORT",
            "task_id":report["task_id"],
            "audit_sha256":report["audit_sha256"],
            "native_process_currently_attested":False,
            "original_retry_authorized":False,
            "model_calls":0}

def selftest():
    checks=[
      SCHEMA!=old.SCHEMA, AUTH!=old.AUTHORITY,
      fixtures.AUTHORITY=="PREPARATION_ONLY_NOT_A_MODEL_TASK_ENVELOPE",
      set(fixtures.catalog())=={"canonical-tag-v1","merge-windows-v1"},
      not bool(TASK.fullmatch("customer-order")),
      not bool(TASK.fullmatch("p0-observed-worker-mac-20261009-01")),
      bool(TASK.fullmatch("p0-diverse-run-mac-merge-20261009-a")),
      not bool(TASK.fullmatch("p0-diverse-run-../outside")),
      set(HOST_MODEL)=={"Chris","MacMiniOffice.local"},
      all(p in (11555,11556) for _,p in HOST_MODEL.values()),
      AUTH.endswith("NO_EFFECT"),
    ]
    require(all(checks) and len(checks)==11,"OFFLINE_DIVERSE_ADMISSION_FAILED")
    example={
      "schema":AUDIT_SCHEMA,"status":"FAILED_INDEPENDENT_QA_NO_SUCCESS",
      "authority":"READ_ONLY_DIAGNOSIS_NO_RECOVERY",
      "task_id":"p0-diverse-run-mac-merge-20261009-a",
      "envelope_sha256":"a"*64,"journal_sha256_raw":"b"*64,
      "kernel_pin_sha256_raw":"c"*64,"observed_source_sha256":"d"*64,
      "original_journal_preserved":True,
      "original_success_receipt_absent":True,
      "original_attempt_retried":False,
      "automatic_requeue_authorized":False,
      "all_detached_descendants_excluded":False,
      "production_authority":False,"model_calls_during_audit":0,
      "historical_native_process_readback":{
        "worker":"HISTORICAL_PID_ABSENT",
        "aider":"HISTORICAL_PID_ABSENT"},
      "independent_failed_qa":{"pass":False,"unit_exit":0,"hidden_exit":1},
    }
    example["audit_sha256"]=seal(example)
    audit_record_validate(example)
    checks.append(True)
    negatives=[
      ("journal_cleared",lambda d:d.update(original_journal_preserved=False)),
      ("fake_final_receipt",lambda d:d.update(original_success_receipt_absent=False)),
      ("blind_retry",lambda d:d.update(original_attempt_retried=True)),
      ("auto_requeue",lambda d:d.update(automatic_requeue_authorized=True)),
      ("all_orphans",lambda d:d.update(all_detached_descendants_excluded=True)),
      ("production",lambda d:d.update(production_authority=True)),
      ("model_call",lambda d:d.update(model_calls_during_audit=1)),
      ("qa_pass",lambda d:d["independent_failed_qa"].update(pass_=True)),
      ("no_qa_failure",lambda d:d["independent_failed_qa"].update(unit_exit=0,hidden_exit=0)),
      ("live_original",lambda d:d["historical_native_process_readback"].update(
                         aider="SAME_KERNEL_INSTANCE_AT_SNAPSHOT")),
      ("raw_hash_corrupt",lambda d:d.update(journal_sha256_raw="invalid")),
      ("fake_schema",lambda d:d.update(schema="PRODUCTION")),
    ]
    for label,mutate in negatives:
        altered=copy.deepcopy(example)
        mutate(altered)
        if label=="qa_pass":
            altered["independent_failed_qa"]["pass"]=True
        altered["audit_sha256"]=seal({k:v for k,v in altered.items()
                                      if k!="audit_sha256"})
        try: audit_record_validate(altered)
        except Refused: checks.append(True)
        else: raise AssertionError("FALSE_RESEALED_FAILED_QA_ACCEPTED:"+label)
    directly_corrupt=copy.deepcopy(example)
    directly_corrupt["audit_sha256"]="0"*64
    try: audit_record_validate(directly_corrupt)
    except Refused: checks.append(True)
    else: raise AssertionError("RAW_AUDIT_TAMPER_ACCEPTED")
    for variant in ("canonical-tag-v1", "merge-windows-v1"):
        base = fixtures.catalog()[variant]["prompt"].encode("utf-8")
        require(approved_prompt_bytes(variant, None) == base,
                "DEFAULT_PROFILE_CHANGED_LEGACY_CANDIDATE")
        checks.append(True)
        extra = approved_prompt_bytes(variant, PUBLIC_SPEC_PROFILE)
        require(extra.startswith(base + bytes((10, 10)))
                and len(extra) > len(base)
                and b"PUBLIC SPEC REMINDER" in extra,
                "PUBLIC_SPEC_PROFILE_NOT_PINNED")
        checks.append(True)
    for bad_profile in ("arbitrary-user-prompt", "", "AUTO_RETRY"):
        try:
            approved_prompt_bytes("canonical-tag-v1", bad_profile)
        except Refused:
            checks.append(True)
        else:
            raise AssertionError("UNAPPROVED_PROFILE_ACCEPTED")
    v2 = approved_prompt_bytes("canonical-tag-v1", PUBLIC_SPEC_STATE_PROFILE)
    require(v2.startswith(fixtures.catalog()["canonical-tag-v1"]["prompt"].encode("utf-8"))
            and b"PUBLIC SPEC STATE REMINDER" in v2,
            "PUBLIC_STATE_PROFILE_NOT_PINN")
    checks.append(True)
    require(v2 != approved_prompt_bytes("canonical-tag-v1", PUBLIC_SPEC_PROFILE),
            "STATE_PROFILE_NOT_DISTINCT")
    checks.append(True)
    try:
        approved_prompt_bytes("merge-windows-v1", PUBLIC_SPEC_STATE_PROFILE)
    except Refused:
        checks.append(True)
    else:
        raise AssertionError("STATE_PROFILE_WRONG_FIXTURE_ACCEPTED")
    v3 = approved_prompt_bytes("merge-windows-v1", PUBLIC_SPEC_INT_PROFILE)
    require(v3.startswith(fixtures.catalog()["merge-windows-v1"]["prompt"].encode("utf-8"))
            and b"PUBLIC EXACT-TYPE REMINDER" in v3
            and b"type(endpoint) is int" in v3,
            "EXACT_INT_PROFILE_NOT_PINNED")
    checks.append(True)
    require(v3 != approved_prompt_bytes("merge-windows-v1", PUBLIC_SPEC_PROFILE),
            "EXACT_INT_PROFILE_NOT_DISTINCT")
    checks.append(True)
    try:
        approved_prompt_bytes("canonical-tag-v1", PUBLIC_SPEC_INT_PROFILE)
    except Refused:
        checks.append(True)
    else:
        raise AssertionError("EXACT_INT_PROFILE_ON_WRONG_FIXTURE_ACCEPTED")
    # Synthetic process-handle injections: model=0, no external effects.
    class FakeChild:
        def __init__(self, cleanup_fault=False):
            self.kills=0
            self.reaps=0
            self.cleanup_fault=cleanup_fault
        def kill(self):
            self.kills+=1
            if self.cleanup_fault: raise OSError("injected cleanup failure")
        def communicate(self, timeout=None):
            self.reaps+=1
            if self.cleanup_fault:
                raise subprocess.TimeoutExpired("synthetic child",timeout)
            return b"",b""
    for stage,expected in (("birth",Refused),("persist",OSError),
                           ("communicate",RuntimeError)):
        child=FakeChild()
        journal={"state":"RUNNING","unknown_outcome_rule":"NO_BLIND_RETRY"}
        def capture(stage=stage):
            if stage=="birth": raise Refused("injected birth pin failure")
            if stage=="persist": raise OSError("injected pin write failure")
            return {"pin":"synthetic"}
        def wait(stage=stage):
            if stage=="communicate": raise RuntimeError("injected IO failure")
            return b"",b""
        try: _guarded_capture_and_wait(child,capture,wait)
        except expected:
            checks.append(child.kills==1 and child.reaps==1
                          and journal=={"state":"RUNNING",
                                       "unknown_outcome_rule":"NO_BLIND_RETRY"})
        else: raise AssertionError("PRE_GUARD_FALSE_SUCCESS:"+stage)
    child=FakeChild()
    try: _guarded_capture_and_wait(
        child,lambda:{"pin":"synthetic"},
        lambda:(_ for _ in ()).throw(subprocess.TimeoutExpired("synthetic",1)))
    except subprocess.TimeoutExpired:
        checks.append(child.kills==0 and child.reaps==0)
    else: raise AssertionError("TIMEOUT_FALSE_SUCCESS")
    child=FakeChild()
    checks.append(_guarded_capture_and_wait(
        child,lambda:{"pin":"synthetic"},lambda:(b"out",b"err"))==
        ({"pin":"synthetic"},b"out",b"err") and child.kills==0)
    child=FakeChild(cleanup_fault=True)
    try: _guarded_capture_and_wait(
        child,lambda:(_ for _ in ()).throw(Refused("injected birth failure")),
        lambda:(b"",b""))
    except Refused:
        checks.append(child.kills==1 and child.reaps==1)
    else: raise AssertionError("CLEANUP_FAILURE_FALSE_SUCCESS")
    require(all(checks) and len(checks)==44,"NEGATIVE_TEST_COUNT_DRIFT")
    return {"status":"PASS_OFFLINE","tests":len(checks),
            "model_invocations":0,"different_tasks_model_proven":False,
            "automatic_retry":False,"production_authority":False,
            "distributed_fencing_verified":False}


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="mode",required=True)
    sub.add_parser("selftest")
    prepare=sub.add_parser("admit")
    for k in ("root","task-id","candidate","aider","model"):
        prepare.add_argument("--"+k,required=True)
    prepare.add_argument("--port",type=int,required=True)
    prepare.add_argument("--timeout",type=int,default=140)
    prepare.add_argument("--prompt-profile",choices=("default", "public-spec-v1", "state-separator-v2", "exact-int-v3"),default="default")
    run=sub.add_parser("run")
    verify=sub.add_parser("verify")
    audit=sub.add_parser("audit-failed-qa")
    audit.add_argument("--envelope",required=True)
    audit.add_argument("--root",required=True)
    audit_read=sub.add_parser("verify-failed-audit")
    audit_read.add_argument("--audit",required=True)
    for op in (run,verify):
        op.add_argument("--envelope",required=True)
        op.add_argument("--receipt",required=True)
    args=p.parse_args()
    if args.mode=="selftest": result=selftest()
    elif args.mode=="admit":
        result=admit(args.root,args.task_id,args.candidate,
                     args.aider,args.model,args.port,args.timeout,
                     (None if args.prompt_profile=="default" else
                      PUBLIC_SPEC_STATE_PROFILE if args.prompt_profile=="state-separator-v2" else
                      PUBLIC_SPEC_INT_PROFILE if args.prompt_profile=="exact-int-v3" else
                      PUBLIC_SPEC_PROFILE))
    elif args.mode=="run":result=execute(args.envelope,args.receipt)
    elif args.mode=="audit-failed-qa":
        result=audit_failed_qa(args.envelope,args.root)
    elif args.mode=="verify-failed-audit":
        result=verify_failed_qa_audit(args.audit)
    else:
        task=task_file(args.envelope)
        require(Path(args.receipt)==task.parent/"output"/"receipt.json",
                "EXACT_ORIGINAL_RECEIPT_LOCATION_REQUIRED")
        result=verify_receipt(read(task),read(args.receipt))
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    try:main()
    except (Refused,old.Refuse,kernel.Refused,OSError,ValueError,
            TypeError,KeyError,AssertionError,subprocess.TimeoutExpired) as e:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(e)[:170],
                          "automatic_retry":False,
                          "production_authority":False},sort_keys=True))
        raise SystemExit(2)
