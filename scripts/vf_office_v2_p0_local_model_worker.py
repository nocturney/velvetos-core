#!/usr/bin/env python3
"""Office 2.0 #612 P0: real local Aider/Ollama LAB task-envelope worker.

NOT a sandbox, scheduler, approval surface, autonomous failover, production writer,
or general-purpose tool. v1 admits ONLY the committed synthetic slug.py fixture.
A true model invocation is never labeled as the offline fixture worker type.
An interrupted/uncertain attempt keeps its running journal; never blind-retry.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import pathlib
import platform
import re
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone

import vf_office_v2_continuity as continuity
import vf_office_v2_p0_kernel_identity as kernel

SCHEMA = "velvetos.office-v2.p0-local-model-envelope.v1"
RECEIPT = "velvetos.office-v2.p0-local-model-receipt.v1"
AUTHORITY = "LAB_LOCAL_MODEL_SYNTHETIC_ONLY_NO_EFFECT"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
SOURCE_SHA256 = "b97dfdee85fdb6f083acf9372cb50b42534ce1e4b16535d395e60a5004bdd430"
TEST_SHA256 = "81134cc5640d34646e2419bcc4c4be737dac1a6ca98b35ba9282bd69fa7b5f60"
MODELS = {"qwen3.5:4b", "qwen3.5:9b"}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,95}\Z")


class Refuse(Exception):
    pass


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def hash_file(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open("rb") as f:
        for block in iter(lambda: f.read(131072), b""):
            h.update(block)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def get_json(path):
    obj = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise Refuse("JSON_OBJECT_REQUIRED")
    return obj


def save_new(path, obj):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def git(root, *cmd):
    try:
        p = subprocess.run(["git", "-C", str(root), *cmd], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        raise Refuse("GIT_UNAVAILABLE")
    if p.returncode:
        raise Refuse("GIT_PRECONDITION_FAILED")
    return p.stdout.rstrip("\n")


def modified(root):
    names = []
    for line in git(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if not line or len(line) < 4 or line[2] != " ":
            raise Refuse("UNSUPPORTED_PORCELAIN_RECORD")
        name = line[3:]
        if '"' in name or " -> " in name or name.startswith("../") or "\\" in name:
            raise Refuse("UNSAFE_PORCELAIN_PATH")
        names.append(name)
    return names


def remote_model_tag(model, port):
    url = "http://127.0.0.1:%d/api/tags" % port
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=4) as response:
            assert response.status == 200
            payload = json.loads(response.read(200000))
    except (OSError, ValueError, AssertionError):
        raise Refuse("LOCAL_OLLAMA_UNAVAILABLE")
    items = [x for x in payload.get("models", []) if isinstance(x, dict) and x.get("name") == model]
    if len(items) != 1 or not re.fullmatch(r"[0-9a-f]{64}", str(items[0].get("digest", ""))):
        raise Refuse("PINNED_MODEL_NOT_FOUND")
    return items[0]["digest"]


def abs_file(value, outside=None):
    if not isinstance(value, str) or not pathlib.Path(value).is_absolute():
        raise Refuse("ABSOLUTE_FILE_REQUIRED")
    raw = pathlib.Path(value)
    if raw.is_symlink():
        raise Refuse("FILE_MISSING_OR_SYMLINK")
    p = raw.resolve()
    if not p.is_file():
        raise Refuse("FILE_MISSING_OR_SYMLINK")
    if outside and p.is_relative_to(outside):
        raise Refuse("INPUT_MUST_BE_OUTSIDE_WORKTREE")
    return p


def preflight(env, *, network=True):
    if env.get("schema") != SCHEMA or env.get("authority") != AUTHORITY or env.get("issue_url") != ISSUE:
        raise Refuse("SCHEMA_AUTHORITY_OR_ISSUE")
    if not isinstance(env.get("task_id"), str) or not TASK_ID.fullmatch(env["task_id"]):
        raise Refuse("TASK_ID_INVALID")
    if env.get("host") != platform.node():
        raise Refuse("HOST_MISMATCH")
    if not isinstance(env.get("worktree_path"), str) or not pathlib.Path(env["worktree_path"]).is_absolute():
        raise Refuse("ABSOLUTE_WORKTREE_REQUIRED")
    root = pathlib.Path(env["worktree_path"]).resolve()
    if not root.is_dir() or not (root / ".git").is_dir():
        raise Refuse("ISOLATED_GIT_REPO_REQUIRED")
    if pathlib.Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise Refuse("TOP_LEVEL_GIT_MISMATCH")
    base = env.get("base_sha")
    if not isinstance(base, str) or not SHA1.fullmatch(base) or git(root, "rev-parse", "HEAD") != base:
        raise Refuse("BASE_DRIFT")
    branch = env.get("branch")
    if not isinstance(branch, str) or not branch.startswith("lab-p0-agent-"):
        raise Refuse("NON_LAB_BRANCH_DENIED")
    if git(root, "branch", "--show-current") != branch:
        raise Refuse("BRANCH_DRIFT")
    if modified(root):
        raise Refuse("DIRTY_WORKTREE")
    target, test = root / "slug.py", root / "tests" / "test_slug.py"
    for rel, p, sha in [("slug.py", target, SOURCE_SHA256),
                        ("tests/test_slug.py", test, TEST_SHA256)]:
        if not p.is_file() or p.is_symlink() or hash_file(p) != sha:
            raise Refuse("SYNTHETIC_FIXTURE_HASH_DRIFT")
        if git(root, "ls-files", "--error-unmatch", "--", rel) != rel:
            raise Refuse("UNTRACKED_INPUT")
    birth_mode = env.get("kernel_birth_capture")
    if birth_mode not in (None, BIRTH_MODE):
        raise Refuse("UNAPPROVED_OS_BIRTH_CAPTURE_MODE")
    budget = env.get("budget") or {}
    timeout = budget.get("timeout_seconds")
    if type(timeout) is not int or not 25 <= timeout <= 180:
        raise Refuse("MODEL_TIMEOUT_INVALID")
    if budget.get("max_attempts") != 1 or budget.get("max_cost_usd") != 0:
        raise Refuse("PAID_OR_MULTIPLE_ATTEMPTS")
    executor = env.get("executor") or {}
    if executor.get("kind") != "LOCAL_AIDER_OLLAMA_SYNTHETIC_V1":
        raise Refuse("UNAPPROVED_EXECUTOR_KIND")
    model, port = executor.get("model"), executor.get("ollama_port")
    if model not in MODELS or type(port) is not int or port not in (11555, 11556):
        raise Refuse("UNAPPROVED_MODEL_OR_PORT")
    pin = executor.get("model_digest")
    if not isinstance(pin, str) or not SHA256.fullmatch(pin):
        raise Refuse("MODEL_DIGEST_REQUIRED")
    if network and remote_model_tag(model, port) != pin:
        raise Refuse("LOCAL_MODEL_DIGEST_DRIFT")
    aider = abs_file(executor.get("aider_binary"), outside=root)
    if aider.name.lower() not in ("aider", "aider.exe"):
        raise Refuse("WRONG_EXECUTOR_BINARY")
    expected_binary = executor.get("aider_sha256")
    if not isinstance(expected_binary, str) or not SHA256.fullmatch(expected_binary) or hash_file(aider) != expected_binary:
        raise Refuse("AIDER_BINARY_DRIFT")
    prompt = abs_file(executor.get("prompt_file"), outside=root)
    qa = abs_file(executor.get("hidden_qa_file"), outside=root)
    for key, source, min_size, max_size in (
        ("prompt_sha256", prompt, 100, 3000), ("hidden_qa_sha256", qa, 100, 4500)
    ):
        expected = executor.get(key)
        if not isinstance(expected, str) or not SHA256.fullmatch(expected) or hash_file(source) != expected:
            raise Refuse("PINNED_INPUT_DRIFT")
        if not min_size <= source.stat().st_size <= max_size:
            raise Refuse("PINNED_INPUT_SIZE_INVALID")
    prompt_text = prompt.read_text(encoding="utf-8")
    if "slug.py" not in prompt_text:
        raise Refuse("PROMPT_NOT_SYNTHETIC")
    checkpoint = abs_file(env.get("context_checkpoint"), outside=root)
    before = get_json(checkpoint)
    if continuity.required_shape(before):
        raise Refuse("CONTINUITY_SHAPE_INVALID")
    baseline = before.get("code_baseline") or {}
    for key, expected in (("repo", "nocturney/velvetos-core"), ("base_sha", base),
                          ("branch", branch), ("worktree_path", str(root))):
        if baseline.get(key) != expected:
            raise Refuse("CONTINUITY_BASE_DRIFT:" + key)
    if before.get("active_external_effects"):
        raise Refuse("EXTERNAL_EFFECT_ACTIVE")
    return root, target, test, aider, prompt, qa, checkpoint, before


def qa_fresh(root, candidate, hidden):
    """A separate clean local Git clone; no model or network; original tests plus blind QA."""
    with tempfile.TemporaryDirectory(prefix="vf-office-p0-aider-qa-") as tmp:
        clone = pathlib.Path(tmp) / "replay"
        p = subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", "--local",
                            str(root), str(clone)], capture_output=True, timeout=22)
        if p.returncode:
            return {"pass": False, "reason": "CLONE_ERROR"}
        (clone / "slug.py").write_bytes(candidate)
        env = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR") if k in os.environ}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            unit = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover",
                                   "-s", "tests", "-q"], cwd=clone, env=env,
                                  capture_output=True, timeout=18)
            hidden_run = subprocess.run([sys.executable, "-B", "-c",
                                         hidden.read_text(encoding="utf-8")], cwd=clone, env=env,
                                         capture_output=True, timeout=18)
        except (OSError, subprocess.TimeoutExpired):
            return {"pass": False, "reason": "QA_LAUNCH_OR_TIMEOUT"}
        paths = modified(clone)
        summary = unit.stderr.decode("utf-8", "replace")
        return {
            "pass": unit.returncode == 0 and hidden_run.returncode == 0
                    and b"QA_HIDDEN_12_PASS" in hidden_run.stdout
                    and "Ran 3 tests" in summary and paths == ["slug.py"],
            "unit_exit": unit.returncode, "hidden_exit": hidden_run.returncode,
            "unit_3_verified": "Ran 3 tests" in summary,
            "hidden_12_verified": b"QA_HIDDEN_12_PASS" in hidden_run.stdout,
            "replay_changed_paths": paths,
            "replay_source_sha256": hash_file(clone / "slug.py"),
            "hidden_stdout_sha256": hashlib.sha256(hidden_run.stdout).hexdigest(),
        }


def check_run(env, receipt):
    """Readback verification replays independent QA; never reruns the model."""
    if receipt.get("schema") != RECEIPT or receipt.get("state") != "SUCCEEDED":
        raise Refuse("RECEIPT_NOT_SUCCEEDED")
    if receipt.get("receipt_sha256") != digest({k: v for k, v in receipt.items() if k != "receipt_sha256"}):
        raise Refuse("RECEIPT_HASH_DRIFT")
    if receipt.get("envelope_sha256") != digest(env):
        raise Refuse("ENVELOPE_DRIFT")
    if receipt.get("task_id") != env.get("task_id") or receipt.get("host") != platform.node():
        raise Refuse("RECEIPT_TASK_HOST")
    root, target, _, aider, _, qa, checkpoint, before = preflight_for_verify(env)
    if receipt.get("base_sha") != env["base_sha"] or receipt.get("branch") != env["branch"]:
        raise Refuse("RECEIPT_BASE_DRIFT")
    if receipt.get("model_invocations_min") != 1 or receipt.get("exact_model_calls") is not None:
        raise Refuse("MODEL_CALL_PROOF_INCORRECT")
    if receipt.get("model") != env["executor"]["model"] or receipt.get("model_digest") != env["executor"]["model_digest"]:
        raise Refuse("MODEL_IDENTITY_DRIFT")
    if receipt.get("additional_api_spend_usd") != 0 or receipt.get("production_authority") != "NONE":
        raise Refuse("AUTHORITY_OR_SPEND_DRIFT")
    verify_kernel_birth_pin(env, receipt)
    if modified(root) != ["slug.py"] or hash_file(target) != receipt.get("artifact_sha256"):
        raise Refuse("SOURCE_EDIT_DRIFT")
    for key, field in (("stdout.log", "stdout_sha256"), ("stderr.log", "stderr_sha256"),
                       ("llm.history.log", "llm_history_sha256")):
        log = pathlib.Path(receipt["receipt_directory"]) / key
        if not log.is_file() or hash_file(log) != receipt.get(field):
            raise Refuse("MODEL_LOG_HASH_DRIFT")
    if hash_file(checkpoint) != receipt.get("checkpoint_before_sha256"):
        raise Refuse("OLD_CHECKPOINT_DRIFT")
    after_path = pathlib.Path(receipt.get("checkpoint_after_path", ""))
    if not after_path.is_file() or hash_file(after_path) != receipt.get("checkpoint_after_sha256"):
        raise Refuse("NEW_CHECKPOINT_DRIFT")
    if continuity.verify(before, get_json(after_path))["status"] != "PASS":
        raise Refuse("CONTINUITY_REPLAY_FAILED")
    verified = qa_fresh(root, target.read_bytes(), qa)
    if not verified["pass"] or verified != receipt.get("independent_qa"):
        raise Refuse("INDEPENDENT_QA_REPLAY_DRIFT")
    return {"status": "PASS", "task_id": env["task_id"], "real_local_model_min_invocations": 1,
            "model_calls_exact": None, "offline_fixture": False, "scheduler_proven": False}


def preflight_for_verify(env):
    """Same pinned identity without expecting the now-edited source to be clean."""
    root = pathlib.Path(env["worktree_path"]).resolve()
    if git(root, "rev-parse", "HEAD") != env["base_sha"]:
        raise Refuse("BASE_DRIFT_DURING_VERIFY")
    if git(root, "branch", "--show-current") != env["branch"]:
        raise Refuse("BRANCH_DRIFT_DURING_VERIFY")
    if modified(root) != ["slug.py"]:
        raise Refuse("UNEXPECTED_SOURCE_CHANGE")
    executor = env["executor"]
    aider = abs_file(executor["aider_binary"], outside=root)
    if hash_file(aider) != executor["aider_sha256"]:
        raise Refuse("AIDER_BINARY_DRIFT")
    prompt = abs_file(executor["prompt_file"], outside=root)
    qa = abs_file(executor["hidden_qa_file"], outside=root)
    if hash_file(prompt) != executor["prompt_sha256"] or hash_file(qa) != executor["hidden_qa_sha256"]:
        raise Refuse("PROMPT_OR_QA_DRIFT")
    test = root / "tests" / "test_slug.py"
    if hash_file(test) != TEST_SHA256:
        raise Refuse("UNIT_INPUT_DRIFT")
    checkpoint = abs_file(env["context_checkpoint"], outside=root)
    before = get_json(checkpoint)
    if continuity.required_shape(before):
        raise Refuse("CONTINUITY_INVALID")
    return root, root / "slug.py", test, aider, prompt, qa, checkpoint, before


def safe_executor_environment(out, port):
    keys = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "TMPDIR", "LANG", "LC_ALL")
    env = {k: os.environ[k] for k in keys if k in os.environ}
    env.update({
        "HOME": str(out / "home"), "USERPROFILE": str(out / "home"),
        "XDG_CONFIG_HOME": str(out / "config"),
        "XDG_DATA_HOME": str(out / "data"),
        "XDG_CACHE_HOME": str(out / "cache"),
        "APPDATA": str(out / "roaming"), "LOCALAPPDATA": str(out / "local"),
        "PROGRAMDATA": str(out / "programdata"), "TMPDIR": str(out / "tmp"),
        "OLLAMA_API_BASE": "http://127.0.0.1:%d" % port,
        "NO_PROXY": "127.0.0.1,localhost,::1",
        "no_proxy": "127.0.0.1,localhost,::1",
        "PYTHONDONTWRITEBYTECODE": "1", "GIT_TERMINAL_PROMPT": "0",
        "AIDER_ANALYTICS": "false", "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1", "TERM": "dumb", "NO_COLOR": "1",
    })
    return env


def command(aider, model, prompt, out):
    return [str(aider), "--model", "ollama_chat/" + model, "--edit-format", "whole",
        "--file", "slug.py", "--read", "tests/test_slug.py",
        "--message", prompt.read_text(encoding="utf-8"),
        "--no-auto-commits", "--no-dirty-commits", "--no-auto-lint", "--no-auto-test",
        "--no-gitignore", "--no-analytics", "--no-check-update", "--no-show-model-warnings",
        "--no-suggest-shell-commands", "--no-browser", "--no-pretty", "--no-stream",
        "--no-fancy-input", "--no-multiline", "--no-detect-urls", "--no-restore-chat-history",
        "--no-watch-files", "--disable-playwright", "--yes-always", "--map-tokens", "0",
        "--env-file", str(out / "empty.env"), "--config", str(out / "empty.yml"),
        "--input-history-file", str(out / "input.history"),
        "--chat-history-file", str(out / "chat.history.md"),
        "--llm-history-file", str(out / "llm.history.log")]



BIRTH_MODE = "REQUIRE_OS_BIRTH_BEFORE_QA_V1"


def capture_kernel_birth_pin(env, journal_path, out, process):
    """At original Aider spawn, pin both actual OS births to the fsynced journal."""
    worker_birth = kernel.sample(os.getpid())
    child_birth = kernel.sample(process.pid)
    if worker_birth is None or child_birth is None:
        raise Refuse("OS_BIRTH_CHILD_NOT_LIVE")
    bound = kernel.make_pin(env, get_json(journal_path), worker_birth, child_birth)
    destination = out / "kernel-pin.json"
    save_new(destination, bound)
    # PID reuse between the two observations leaves the task UNKNOWN, never green.
    if kernel.sample(os.getpid()) != worker_birth or kernel.sample(process.pid) != child_birth:
        raise Refuse("OS_PROCESS_BIRTH_CHANGED_DURING_CAPTURE")
    return bound


def verify_kernel_birth_pin(env, receipt):
    """Pure readback; never samples the live process again or invokes a model."""
    requested = env.get("kernel_birth_capture")
    if requested is None:
        if receipt.get("kernel_birth_mode") is not None or receipt.get("kernel_pin_sha256") is not None:
            raise Refuse("UNREQUESTED_KERNEL_PIN_EVIDENCE")
        return
    if requested != BIRTH_MODE or receipt.get("kernel_birth_mode") != BIRTH_MODE:
        raise Refuse("KERNEL_BIRTH_MODE_DRIFT")
    out = pathlib.Path(receipt["receipt_directory"]).resolve()
    root = pathlib.Path(env["worktree_path"]).resolve()
    if out.is_relative_to(root):
        raise Refuse("KERNEL_PIN_INSIDE_WORKTREE")
    target = out / "kernel-pin.json"
    if not target.is_file() or target.is_symlink() or hash_file(target) != receipt.get("kernel_pin_file_sha256"):
        raise Refuse("KERNEL_PIN_FILE_DRIFT")
    pin = get_json(target)
    if pin.get("pin_sha256") != receipt.get("kernel_pin_sha256"):
        raise Refuse("KERNEL_PIN_SELF_HASH_DRIFT")
    original_journal = {
        "state": "RUNNING", "task_id": env["task_id"],
        "envelope_sha256": digest(env), "host": env["host"],
        "started_at": receipt["started_at"], "unknown_outcome_rule": "NO_BLIND_RETRY",
        "kind": "LOCAL_AIDER_OLLAMA_SYNTHETIC_V1",
    }
    try:
        kernel.checked_pin(env, original_journal, pin)
    except kernel.Refused:
        raise Refuse("KERNEL_PIN_BINDING_NOT_VERIFIED")

def run(task, output):
    task = pathlib.Path(task).resolve()
    receipt = pathlib.Path(output).resolve()
    journal = receipt.with_suffix(receipt.suffix + ".running")
    if receipt.exists() or journal.exists():
        raise Refuse("DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY")
    env = get_json(task)
    root, target, _, aider, prompt, qa, checkpoint, before = preflight(env)
    if receipt.is_relative_to(root) or task.is_relative_to(root):
        raise Refuse("ENVELOPE_RECEIPT_OUTSIDE_WORKTREE")
    out = receipt.parent
    if out.exists():
        # Avoid mixed or reused log destinations in this dedicated synthetic LAB.
        if any(out.iterdir()):
            raise Refuse("OUTPUT_DIRECTORY_NOT_FRESH")
    else:
        out.mkdir(parents=True)
    journal.parent.mkdir(parents=True, exist_ok=True)
    started = now()
    save_new(journal, {"state": "RUNNING", "task_id": env["task_id"],
        "envelope_sha256": digest(env), "host": platform.node(), "started_at": started,
        "unknown_outcome_rule": "NO_BLIND_RETRY", "kind": "LOCAL_AIDER_OLLAMA_SYNTHETIC_V1"})
    for name in ("home", "config", "data", "cache", "tmp", "roaming", "local", "programdata"):
        (out / name).mkdir()
    (out / "empty.env").write_bytes(b"")
    (out / "empty.yml").write_bytes(b"{}\n")
    before_run = time.monotonic()
    proc = None
    kernel_birth_pin = None
    kernel_birth_failed = False
    exit_code = None
    stdout = stderr = b""
    state = "UNKNOWN_OUTCOME"
    try:
        opts = {"cwd": str(root), "env": safe_executor_environment(out, env["executor"]["ollama_port"]),
                "stdin": subprocess.DEVNULL, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
        if os.name == "nt":
            opts["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            opts["start_new_session"] = True
        proc = subprocess.Popen(command(aider, env["executor"]["model"], prompt, out), **opts)
        if env.get("kernel_birth_capture") == BIRTH_MODE:
            try:
                kernel_birth_pin = capture_kernel_birth_pin(env, journal, out, proc)
            except (kernel.Refused, Refuse, OSError, ValueError, TypeError, KeyError):
                kernel_birth_failed = True
        try:
            stdout, stderr = proc.communicate(timeout=env["budget"]["timeout_seconds"])
            exit_code = proc.returncode
            state = "EXECUTOR_FINISHED" if exit_code == 0 else "EXECUTOR_NONZERO"
        except subprocess.TimeoutExpired:
            state = "TIMED_OUT_UNKNOWN_OUTCOME"
            if os.name != "nt":
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                               capture_output=True, timeout=8)
            stdout, stderr = proc.communicate(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        state = "EXECUTOR_LAUNCH_OR_CLEANUP_ERROR"
    for name, contents in (("stdout.log", stdout), ("stderr.log", stderr)):
        (out / name).write_bytes(contents)
    llm_log = out / "llm.history.log"
    if not llm_log.is_file():
        llm_log.write_bytes(b"")
    changed = modified(root)
    candidate = target.read_bytes()
    if kernel_birth_failed and state == "EXECUTOR_FINISHED":
        state = "OS_BIRTH_PIN_NOT_VERIFIED"
    qa_result = {"pass": False, "reason": "NOT_RUN"}
    if state == "EXECUTOR_FINISHED" and changed == ["slug.py"] and hash_file(target) != SOURCE_SHA256:
        qa_result = qa_fresh(root, candidate, qa)
        state = "SUCCEEDED" if qa_result["pass"] else "INDEPENDENT_QA_FAILED"
    elif state == "EXECUTOR_FINISHED":
        state = "NO_VALID_TARGET_EDIT"
    after_path = receipt.with_suffix(receipt.suffix + ".checkpoint.json")
    if state == "SUCCEEDED":
        after = continuity.compact_manifest(before, pressure_score=0.0)
        if continuity.verify(before, after)["status"] == "PASS":
            save_new(after_path, after)
        else:
            state = "CONTINUITY_FAILED"
    record = {
        "schema": RECEIPT, "task_id": env["task_id"], "state": state,
        "envelope_sha256": digest(env), "base_sha": env["base_sha"],
        "branch": env["branch"], "host": platform.node(),
        "started_at": started, "finished_at": now(), "elapsed_seconds": round(time.monotonic() - before_run, 3),
        "exit_code": exit_code, "changed_paths": changed,
        "artifact_sha256": hash_file(target), "stdout_sha256": hash_file(out / "stdout.log"),
        "stderr_sha256": hash_file(out / "stderr.log"), "llm_history_sha256": hash_file(llm_log),
        "receipt_directory": str(out), "model": env["executor"]["model"],
        "model_digest": env["executor"]["model_digest"],
        "model_invocations_min": 1 if proc and state in ("SUCCEEDED", "INDEPENDENT_QA_FAILED") else 0,
        "exact_model_calls": None, "additional_api_spend_usd": 0,
        "local_model_usage_tokens": None,
        "checkpoint_before_sha256": hash_file(checkpoint),
        "checkpoint_after_path": str(after_path) if state == "SUCCEEDED" else None,
        "checkpoint_after_sha256": hash_file(after_path) if state == "SUCCEEDED" else None,
        "independent_qa": qa_result,
        "production_authority": "NONE", "scheduler_proven": False,
        "autonomous_retry": False, "os_network_sandbox_proven": False,
        "kernel_birth_mode": env.get("kernel_birth_capture"),
        "kernel_pin_sha256": kernel_birth_pin["pin_sha256"] if kernel_birth_pin else None,
        "kernel_pin_file_sha256": hash_file(out / "kernel-pin.json") if kernel_birth_pin else None,
    }
    record["receipt_sha256"] = digest(record)
    # Verify the full independent replay BEFORE exposing a success receipt.
    # An unexpectedly failed verification keeps only the unknown RUNNING journal.
    if state == "SUCCEEDED":
        check_run(env, record)
    save_new(receipt, record)
    if state == "SUCCEEDED":
        journal.unlink()
    return {"status": state, "task_id": env["task_id"],
            "artifact_sha256": record["artifact_sha256"],
            "model_invocations_min": record["model_invocations_min"],
            "receipt_sha256": record["receipt_sha256"],
            "qa": qa_result["pass"], "elapsed_seconds": record["elapsed_seconds"]}


def selftest():
    checks = []
    with tempfile.TemporaryDirectory(prefix="vf-office-p0-local-agent-contract-") as td:
        root = (pathlib.Path(td) / "repo").resolve()
        root.mkdir()
        for arg in (["git", "init", "-q", str(root)],
                    ["git", "-C", str(root), "checkout", "-q", "-b", "lab-p0-agent-test"]):
            subprocess.run(arg, check=True, capture_output=True)
        (root / "tests").mkdir()
        (root / "slug.py").write_bytes(
            b'import re\n\ndef slugify(value: str) -> str:\n    """Lowercase ASCII; collapse punctuation/whitespace to hyphens, strip, default untitled."""\n    return value.lower().replace(" ", "-")\n')
        (root / "tests" / "test_slug.py").write_bytes(
            b'import unittest\nfrom slug import slugify\n\nclass SlugTests(unittest.TestCase):\n    def test_basic(self): self.assertEqual(slugify("Hello   World!!"), "hello-world")\n    def test_edges(self): self.assertEqual(slugify(" _ABC_ 42_ "), "abc-42")\n    def test_empty(self): self.assertEqual(slugify("!?"), "untitled")\n')
        assert hash_file(root / "slug.py") == SOURCE_SHA256
        assert hash_file(root / "tests" / "test_slug.py") == TEST_SHA256
        checks.append("fixture_hash_pinned")
        git(root, "add", "slug.py", "tests/test_slug.py")
        git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
            "commit", "-qm", "p0 fixture")
        branch = git(root, "branch", "--show-current")
        sha = git(root, "rev-parse", "HEAD")
        prompt = pathlib.Path(td) / "prompt.txt"
        prompt.write_text("Fix slug.py to meet its docstring, lowercase ASCII, collapse repeated punctuation "
                          "and whitespace into hyphens; only edit slug.py, never tests. "
                          "This is a synthetic local coding fixture; do not run commands.", encoding="utf-8")
        qa = pathlib.Path(td) / "qa.py"
        qa.write_text(
            "from slug import slugify\n"
            "cases=[('a  b','a-b'),('HELLO','hello'),('!_A_-B!','a-b'),"
            "('2026/Oct/08','2026-oct-08'),('  ','untitled'),"
            "('A..B','a-b'),('A_B','a-b'),('a---b','a-b'),"
            "('mixed Case','mixed-case'),('!?','untitled'),('Hi!','hi'),('42','42')]\n"
            "assert len(cases)==12\n"
            "for inp,expected in cases:\n"
            "    actual=slugify(inp)\n"
            "    assert actual==expected,(inp,expected,actual)\n"
            "print('QA_HIDDEN_12_PASS')\n", encoding="utf-8")
        fake = pathlib.Path(td) / "aider"
        fake.write_text("# pinned test placeholder, never executed\n", encoding="utf-8")
        cp = pathlib.Path(td) / "checkpoint.json"
        before = continuity.self_test_manifest()
        before["active_external_effects"] = []
        before["code_baseline"] = {"repo": "nocturney/velvetos-core", "base_sha": sha,
                                   "branch": branch, "worktree_path": str(root)}
        continuity.write(cp, continuity.seal(before))
        env = {
            "schema": SCHEMA, "task_id": "selftest-local-aider-001",
            "authority": AUTHORITY, "issue_url": ISSUE, "host": platform.node(),
            "base_sha": sha, "branch": branch, "worktree_path": str(root),
            "budget": {"timeout_seconds": 60, "max_attempts": 1, "max_cost_usd": 0},
            "executor": {
                "kind": "LOCAL_AIDER_OLLAMA_SYNTHETIC_V1", "model": "qwen3.5:4b",
                "model_digest": "a" * 64, "ollama_port": 11556,
                "aider_binary": str(fake), "aider_sha256": hash_file(fake),
                "prompt_file": str(prompt), "prompt_sha256": hash_file(prompt),
                "hidden_qa_file": str(qa), "hidden_qa_sha256": hash_file(qa),
            }, "context_checkpoint": str(cp),
        }
        preflight(env, network=False)
        checks.append("positive_offline_preflight")
        opt_in = copy.deepcopy(env)
        opt_in["kernel_birth_capture"] = BIRTH_MODE
        preflight(opt_in, network=False)
        checks.append("native_birth_opt_in_preflight")
        opt_bad = copy.deepcopy(env)
        opt_bad["kernel_birth_capture"] = "AUTO_REQUEUE"
        try:
            preflight(opt_bad, network=False)
        except Refuse as exc:
            assert str(exc) == "UNAPPROVED_OS_BIRTH_CAPTURE_MODE"
        else:
            raise AssertionError("UNSAFE_BIRTH_MODE_ACCEPTED")
        checks.append("invalid_birth_mode_denied")
        # Regression: hidden QA lives outside the clone, but imports slug from it.
        # Running the hidden file by absolute path would incorrectly fail imports.
        fixed_source = (
            b"import re\n\ndef slugify(value: str) -> str:\n"
            b"    cleaned = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')\n"
            b"    return cleaned or 'untitled'\n"
        )
        replay_good = qa_fresh(root, fixed_source, qa)
        assert replay_good["pass"] is True, replay_good
        checks.append("external_hidden_qa_imports_fresh_clone")
        replay_bad = qa_fresh(root, (root / "slug.py").read_bytes(), qa)
        assert replay_bad["pass"] is False, replay_bad
        checks.append("bad_source_fails_independent_qa")
        scenarios = [
            ("wrong_kind", ("executor", "kind", "CODEX_CLI"), "UNAPPROVED_EXECUTOR_KIND"),
            ("cloud_url", ("executor", "ollama_port", 8443), "UNAPPROVED_MODEL_OR_PORT"),
            ("wrong_model", ("executor", "model", "gpt-5"), "UNAPPROVED_MODEL_OR_PORT"),
            ("cost", ("budget", "max_cost_usd", 1), "PAID_OR_MULTIPLE_ATTEMPTS"),
            ("repeat", ("budget", "max_attempts", 2), "PAID_OR_MULTIPLE_ATTEMPTS"),
            ("model_drift", ("executor", "model_digest", ""), "MODEL_DIGEST_REQUIRED"),
            ("prompt_tamper", ("executor", "prompt_sha256", "a" * 64), "PINNED_INPUT_DRIFT"),
            ("wrong_host", ("", "host", "other"), "HOST_MISMATCH"),
            ("wrong_branch", ("", "branch", "main"), "NON_LAB_BRANCH_DENIED"),
            ("missing_effect_gate", ("", "authority", "PRODUCTION"), "SCHEMA_AUTHORITY_OR_ISSUE"),
        ]
        for name, (group, key, value), expected in scenarios:
            bad = copy.deepcopy(env)
            if group: bad[group][key] = value
            else: bad[key] = value
            try:
                preflight(bad, network=False)
            except Refuse as exc:
                assert str(exc) == expected, (name, str(exc), expected)
            else:
                raise AssertionError("NEGATIVE_ACCEPTED: " + name)
            checks.append(name + "_rejected")
        (root / "stray.txt").write_text("unexpected", encoding="utf-8")
        try:
            preflight(env, network=False)
            raise AssertionError("DIRTY_REPO_ACCEPTED")
        except Refuse as exc:
            assert str(exc) == "DIRTY_WORKTREE"
        checks.append("dirty_repo_rejected")
        changed = root / "stray.txt"
        changed.unlink()
        assert modified(root) == []
        checks.append("clean_fixture_confirmed")
        # A sealed receipt must not be reported as real proof when no model ran.
        forged = {"model_invocations_min": 0, "state": "SUCCEEDED"}
        assert forged.get("model_invocations_min") != 1
        checks.append("model_proof_not_fabricated")
    return {"status": "PASS", "tests": len(checks),
            "checks": checks, "actual_model_invocations": 0,
            "live_model_agent_proven_by_selftest": False, "paid_api_calls": 0}


def main():
    parser = argparse.ArgumentParser(description="Bounded real-local-model Task Envelope LAB")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("selftest")
    r = sub.add_parser("run")
    r.add_argument("--envelope", required=True)
    r.add_argument("--receipt", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--envelope", required=True)
    v.add_argument("--receipt", required=True)
    args = parser.parse_args()
    if args.command == "selftest":
        res = selftest()
    elif args.command == "run":
        res = run(args.envelope, args.receipt)
    else:
        res = check_run(get_json(args.envelope), get_json(args.receipt))
    print(json.dumps(res, sort_keys=True, ensure_ascii=False))
    return 0 if res.get("status") in ("PASS", "SUCCEEDED") else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Refuse, ValueError, OSError, KeyError, TypeError, AssertionError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:220]}))
        raise SystemExit(2)
