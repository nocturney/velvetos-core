#!/usr/bin/env python3
"""P0 offline execution envelope: pinned LAB task, durable journal, hashed receipt.

This is NOT a sandbox, live model agent, multi-host scheduler, or approval engine.
Callers must run only pre-reviewed Python fixtures in an isolated checkout without
production credentials. Uncertain effects stay UNKNOWN and never auto-retry.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import vf_office_v2_continuity as continuity

TASK_SCHEMA = "velvetos.office-v2.p0-task-envelope.v0"
RECEIPT_SCHEMA = "velvetos.office-v2.p0-worker-receipt.v0"
AUTHORITY = "LAB_LOCAL_NO_EXTERNAL_EFFECT"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class Rejected(Exception):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            block = handle.read(1 << 18)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        result = json.load(handle)
    if not isinstance(result, dict):
        raise Rejected("JSON_OBJECT_REQUIRED")
    return result


def save_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def git(worktree, *args):
    result = subprocess.run(
        ["git", "-C", str(worktree)] + list(args),
        capture_output=True, text=True, timeout=20,
    )
    if result.returncode != 0:
        raise Rejected("GIT_PRECONDITION_FAILED")
    return result.stdout.strip()


def contained(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise Rejected("INVALID_RELATIVE_PATH")
    candidate = Path(relative)
    if candidate.is_absolute() or any(p in (".", "..") for p in candidate.parts):
        raise Rejected("PATH_TRAVERSAL")
    full = (root / candidate).resolve()
    try:
        full.relative_to(root.resolve())
    except ValueError:
        raise Rejected("PATH_OUTSIDE_WORKTREE")
    return full


def git_changed(worktree):
    lines = git(worktree, "status", "--porcelain", "--untracked-files=all").splitlines()
    result = set()
    for line in lines:
        if line:
            # Deliberately fail closed on rename quoting or multi-path records.
            name = line[3:]
            if " -> " in name or name.startswith('"'):
                raise Rejected("UNSUPPORTED_GIT_STATUS_PATH")
            result.add(name)
    return result


def validate(envelope):
    if envelope.get("schema") != TASK_SCHEMA:
        raise Rejected("TASK_SCHEMA_MISMATCH")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,95}", str(envelope.get("task_id", ""))):
        raise Rejected("INVALID_TASK_ID")
    if envelope.get("authority") != AUTHORITY:
        raise Rejected("LAB_AUTHORITY_REQUIRED")
    if envelope.get("issue_url") != "https://github.com/nocturney/velvetos-core/issues/612":
        raise Rejected("CANONICAL_ISSUE_REQUIRED")
    base = envelope.get("base_sha")
    if not isinstance(base, str) or not SHA_PATTERN.fullmatch(base):
        raise Rejected("BASE_SHA_REQUIRED")
    if envelope.get("host") != platform.node():
        raise Rejected("HOST_MISMATCH")
    worktree = Path(envelope.get("worktree_path", "")).resolve()
    if not worktree.is_dir() or not (worktree / ".git").exists():
        raise Rejected("ISOLATED_WORKTREE_REQUIRED")
    if git(worktree, "rev-parse", "HEAD") != base:
        raise Rejected("STALE_BASE_SHA")
    if git(worktree, "branch", "--show-current") != envelope.get("branch"):
        raise Rejected("BRANCH_MISMATCH")
    if git_changed(worktree):
        raise Rejected("DIRTY_WORKTREE_BEFORE")
    budget = envelope.get("budget") or {}
    timeout = budget.get("timeout_seconds")
    if type(timeout) is not int or not (1 <= timeout <= 120):
        raise Rejected("TIMEOUT_OUT_OF_RANGE")
    if budget.get("max_attempts") != 1 or budget.get("max_cost_usd") != 0:
        raise Rejected("UNBOUNDED_OR_PAID_EXECUTION")
    executor = envelope.get("executor") or {}
    if executor.get("kind") != "PINNED_PYTHON_FIXTURE":
        raise Rejected("REAL_AGENT_NOT_YET_AUTHORIZED")
    script = contained(worktree, executor.get("script"))
    if not script.is_file() or script.suffix != ".py":
        raise Rejected("PINNED_SCRIPT_MISSING")
    if git(worktree, "ls-files", "--error-unmatch", executor["script"]) != executor["script"]:
        raise Rejected("UNTRACKED_EXECUTOR")
    if not HASH_PATTERN.fullmatch(str(executor.get("sha256", ""))) or file_hash(script) != executor["sha256"]:
        raise Rejected("EXECUTOR_HASH_MISMATCH")
    args = executor.get("args")
    if not isinstance(args, list) or len(args) > 12 or any(
        not isinstance(x, str) or len(x) > 256 or "\x00" in x for x in args
    ):
        raise Rejected("UNBOUNDED_EXECUTOR_ARGS")
    outputs = envelope.get("allowed_outputs")
    if not isinstance(outputs, list) or not (1 <= len(outputs) <= 12) or len(set(outputs)) != len(outputs):
        raise Rejected("INVALID_ALLOWED_OUTPUTS")
    for rel in outputs:
        full = contained(worktree, rel)
        if full == script:
            raise Rejected("EXECUTOR_CANNOT_BE_OUTPUT")
        if full.exists() and full.is_symlink():
            raise Rejected("SYMLINK_OUTPUT_DENIED")
    checkpoint = Path(envelope.get("context_checkpoint", "")).resolve()
    if not checkpoint.is_file() or checkpoint.is_relative_to(worktree):
        raise Rejected("EXTERNAL_CHECKPOINT_REQUIRED")
    manifest = read_json(checkpoint)
    if continuity.required_shape(manifest):
        raise Rejected("CONTINUITY_CHECKPOINT_INVALID")
    code = manifest.get("code_baseline") or {}
    for field, expected in (
        ("repo", "nocturney/velvetos-core"),
        ("base_sha", base),
        ("branch", envelope["branch"]),
        ("worktree_path", str(worktree)),
    ):
        if code.get(field) != expected:
            raise Rejected("CONTINUITY_BASELINE_MISMATCH:" + field)
    if manifest.get("active_external_effects"):
        raise Rejected("ACTIVE_EXTERNAL_EFFECTS_DENIED")
    return worktree, script, checkpoint, manifest


def seal_receipt(receipt):
    value = copy.deepcopy(receipt)
    value.pop("receipt_sha256", None)
    value["receipt_sha256"] = digest(value)
    return value


def verify(envelope, receipt):
    if receipt.get("schema") != RECEIPT_SCHEMA or receipt.get("state") != "SUCCEEDED":
        raise Rejected("RECEIPT_NOT_SUCCESS")
    if receipt.get("receipt_sha256") != digest({k: v for k, v in receipt.items() if k != "receipt_sha256"}):
        raise Rejected("RECEIPT_HASH_MISMATCH")
    if receipt.get("envelope_sha256") != digest(envelope):
        raise Rejected("ENVELOPE_HASH_MISMATCH")
    if receipt.get("model_invocations") != 0 or receipt.get("additional_spend_usd") != 0:
        raise Rejected("OFFLINE_PROOF_ONLY")
    if receipt.get("worker_host") != platform.node():
        raise Rejected("RECEIPT_HOST_MISMATCH")
    worktree = Path(envelope["worktree_path"]).resolve()
    if receipt.get("base_sha") != envelope.get("base_sha") or receipt.get("branch") != envelope.get("branch"):
        raise Rejected("RECEIPT_BASE_MISMATCH")
    if git(worktree, "rev-parse", "HEAD") != envelope["base_sha"]:
        raise Rejected("WORKTREE_BASE_DRIFT")
    expected = set(envelope["allowed_outputs"])
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, list) or {a.get("path") for a in artifacts} != expected:
        raise Rejected("ARTIFACT_SET_MISMATCH")
    if git_changed(worktree) != expected:
        raise Rejected("UNEXPECTED_WORKTREE_CHANGE")
    for row in artifacts:
        p = contained(worktree, row["path"])
        if not p.is_file() or p.is_symlink() or file_hash(p) != row["sha256"]:
            raise Rejected("ARTIFACT_HASH_MISMATCH")
    before = read_json(envelope["context_checkpoint"])
    after = read_json(receipt["checkpoint_after_path"])
    if file_hash(envelope["context_checkpoint"]) != receipt["checkpoint_before_file_sha256"]:
        raise Rejected("CHECKPOINT_BEFORE_DRIFT")
    if file_hash(receipt["checkpoint_after_path"]) != receipt["checkpoint_after_file_sha256"]:
        raise Rejected("CHECKPOINT_AFTER_DRIFT")
    result = continuity.verify(before, after)
    if result["status"] != "PASS":
        raise Rejected("CONTINUITY_RESTORE_NOT_PASS")
    return {"status": "PASS", "task_id": receipt["task_id"], "artifacts": len(artifacts),
            "offline_only": True, "autonomous_coding_agent_proven": False}


def run(envelope_path, receipt_path):
    envelope_path = Path(envelope_path).resolve()
    receipt_path = Path(receipt_path).resolve()
    journal_path = receipt_path.with_suffix(receipt_path.suffix + ".running")
    if receipt_path.exists() or journal_path.exists():
        raise Rejected("DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY")
    env = read_json(envelope_path)
    root, script, checkpoint_path, before = validate(env)
    if receipt_path.is_relative_to(root) or journal_path.is_relative_to(root):
        raise Rejected("RECEIPT_MUST_BE_OUTSIDE_WORKTREE")
    checkpoint_after = receipt_path.with_suffix(receipt_path.suffix + ".checkpoint.json")
    if checkpoint_after.exists():
        raise Rejected("EXISTING_CHECKPOINT_AFTER")
    start = time.monotonic()
    save_new(journal_path, {"state": "RUNNING", "task_id": env["task_id"],
                            "envelope_sha256": digest(env), "started_at": utc_now(),
                            "unknown_outcome_rule": "NO_BLIND_RETRY"})
    code = None
    outcome = "UNKNOWN_OUTCOME"
    stdout_hash = stderr_hash = None
    try:
        thin_env = {k: os.environ[k] for k in
                    ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR")
                    if k in os.environ}
        thin_env["PYTHONDONTWRITEBYTECODE"] = "1"
        thin_env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, "-B", str(script)] + env["executor"]["args"],
            cwd=str(root), env=thin_env, capture_output=True,
            timeout=env["budget"]["timeout_seconds"],
        )
        code = result.returncode
        stdout_hash = hashlib.sha256(result.stdout).hexdigest()
        stderr_hash = hashlib.sha256(result.stderr).hexdigest()
        outcome = "SUCCEEDED" if code == 0 else "EXECUTOR_FAILED"
    except subprocess.TimeoutExpired:
        outcome = "TIMED_OUT_UNKNOWN_EFFECTS"
    except OSError:
        outcome = "EXECUTOR_LAUNCH_FAILED"
    artifacts = []
    if outcome == "SUCCEEDED":
        if git_changed(root) != set(env["allowed_outputs"]):
            outcome = "UNEXPECTED_WORKTREE_CHANGE"
        else:
            for rel in env["allowed_outputs"]:
                artifact = contained(root, rel)
                if not artifact.is_file() or artifact.is_symlink():
                    outcome = "MISSING_OR_UNSAFE_ARTIFACT"
                    break
                artifacts.append({"path": rel, "sha256": file_hash(artifact)})
    if outcome == "SUCCEEDED":
        after = continuity.compact_manifest(before, pressure_score=0.0)
        if continuity.verify(before, after)["status"] != "PASS":
            outcome = "CONTINUITY_VERIFICATION_FAILED"
        else:
            save_new(checkpoint_after, after)
    receipt = seal_receipt({
        "schema": RECEIPT_SCHEMA, "task_id": env["task_id"],
        "state": outcome, "envelope_sha256": digest(env),
        "base_sha": env["base_sha"], "branch": env["branch"],
        "worker_host": platform.node(), "started_at": read_json(journal_path)["started_at"],
        "finished_at": utc_now(), "elapsed_ms": round(1000 * (time.monotonic() - start)),
        "exit_code": code, "stdout_sha256": stdout_hash, "stderr_sha256": stderr_hash,
        "artifacts": artifacts, "checkpoint_before_file_sha256": file_hash(checkpoint_path),
        "checkpoint_after_path": str(checkpoint_after) if outcome == "SUCCEEDED" else None,
        "checkpoint_after_file_sha256": file_hash(checkpoint_after) if outcome == "SUCCEEDED" else None,
        "model_invocations": 0, "additional_spend_usd": 0,
        "autonomous_coding_agent_proven": False, "external_effects": "NONE_ALLOWED",
    })
    save_new(receipt_path, receipt)
    # Journal remains on failures; only a verified success clears the RUNNING marker.
    if outcome == "SUCCEEDED":
        verify(env, receipt)
        journal_path.unlink()
    return {"task_id": env["task_id"], "state": outcome, "receipt": str(receipt_path),
            "elapsed_ms": receipt["elapsed_ms"], "artifacts": len(artifacts),
            "autonomous_coding_agent_proven": False}


def demo_selftest():
    tests = []
    with tempfile.TemporaryDirectory(prefix="vf-office-p0-worker-") as tmp:
        base = Path(tmp).resolve()
        worktree = base / "isolated-repo"
        worktree.mkdir()
        subprocess.run(["git", "init", "-q", str(worktree)], check=True)
        subprocess.run(["git", "-C", str(worktree), "checkout", "-q", "-b", "test-worker"], check=True)
        script = worktree / "job.py"
        script.write_text("from pathlib import Path\nPath('result.txt').write_text('safe output\\n', encoding='utf-8')\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(worktree), "add", "job.py"], check=True)
        subprocess.run(["git", "-C", str(worktree), "-c", "user.name=Fixture",
                        "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"], check=True)
        sha = git(worktree, "rev-parse", "HEAD")
        manifest = continuity.self_test_manifest()
        manifest["active_external_effects"] = []
        manifest["code_baseline"] = {"repo": "nocturney/velvetos-core", "base_sha": sha,
                                     "branch": "test-worker", "worktree_path": str(worktree)}
        manifest = continuity.seal(manifest)
        checkpoint = base / "checkpoint.json"
        continuity.write(checkpoint, manifest)
        env = {
            "schema": TASK_SCHEMA, "task_id": "fixture-agent-001",
            "issue_url": "https://github.com/nocturney/velvetos-core/issues/612",
            "authority": AUTHORITY, "base_sha": sha, "branch": "test-worker",
            "worktree_path": str(worktree), "host": platform.node(),
            "budget": {"timeout_seconds": 10, "max_attempts": 1, "max_cost_usd": 0},
            "executor": {"kind": "PINNED_PYTHON_FIXTURE", "script": "job.py",
                         "sha256": file_hash(script), "args": []},
            "allowed_outputs": ["result.txt"], "context_checkpoint": str(checkpoint),
        }
        task = base / "envelope.json"
        continuity.write(task, env)
        receipt_path = base / "receipt.json"
        actual = run(task, receipt_path)
        if actual["state"] != "SUCCEEDED":
            raise Rejected("POSITIVE_EXECUTION_FAILED")
        tests.append("positive_executable_receipt")
        verify(env, read_json(receipt_path))
        tests.append("independent_verification")
        try:
            run(task, receipt_path)
            raise AssertionError("duplicate accepted")
        except Rejected as exc:
            assert str(exc) == "DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY"
        tests.append("duplicate_rejected")
        output = worktree / "result.txt"
        output.write_text("TAMPERED\n", encoding="utf-8")
        try:
            verify(env, read_json(receipt_path))
            raise AssertionError("tamper accepted")
        except Rejected as exc:
            assert str(exc) == "ARTIFACT_HASH_MISMATCH"
        tests.append("tampered_artifact_rejected")
        output.write_text("safe output\\n", encoding="utf-8")
        # Negative controls validate fresh isolated preflight copies, not the now-dirty test repo.
        output.unlink()
        negative = [
            ("stale_base", {"base_sha": "0" * 40}, "STALE_BASE_SHA"),
            ("wrong_host", {"host": "wrong-host"}, "HOST_MISMATCH"),
            ("paid_model", {"budget": {"timeout_seconds": 10, "max_attempts": 1, "max_cost_usd": 1}}, "UNBOUNDED_OR_PAID_EXECUTION"),
            ("unapproved_model", {"executor": {"kind": "CODEX_CLI", "script": "job.py", "sha256": file_hash(script), "args": []}}, "REAL_AGENT_NOT_YET_AUTHORIZED"),
            ("path_escape", {"allowed_outputs": ["../escape.txt"]}, "PATH_TRAVERSAL"),
            ("checkpoint_mismatch", {"context_checkpoint": str(task)}, "CONTINUITY_CHECKPOINT_INVALID"),
        ]
        for name, mutation, expected in negative:
            changed = copy.deepcopy(env)
            changed.update(mutation)
            try:
                validate(changed)
                raise AssertionError(name + " accepted")
            except Rejected as exc:
                if str(exc) != expected:
                    raise AssertionError("%s: got %s expected %s" % (name, exc, expected))
            tests.append(name + "_rejected")
        journal = base / "interrupted.json.running"
        save_new(journal, {"state": "RUNNING", "unknown_outcome_rule": "NO_BLIND_RETRY"})
        try:
            run(task, base / "interrupted.json")
            raise AssertionError("crash/unknown retry accepted")
        except Rejected as exc:
            assert str(exc) == "DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY"
        tests.append("orphan_journal_no_blind_retry")
    return {"status": "PASS", "tests": len(tests), "cases": tests,
            "model_invocations": 0, "additional_spend_usd": 0,
            "autonomous_coding_agent_proven": False, "worker_fleet_proven": False}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("selftest")
    p = sub.add_parser("run")
    p.add_argument("--envelope", required=True)
    p.add_argument("--receipt", required=True)
    p = sub.add_parser("verify")
    p.add_argument("--envelope", required=True)
    p.add_argument("--receipt", required=True)
    args = parser.parse_args()
    try:
        if args.command == "selftest":
            result = demo_selftest()
        elif args.command == "run":
            result = run(args.envelope, args.receipt)
        else:
            result = verify(read_json(args.envelope), read_json(args.receipt))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result.get("status", result.get("state")) in ("PASS", "SUCCEEDED") else 1
    except (Rejected, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
