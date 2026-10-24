#!/usr/bin/env python3
"""#612: bounded source-import -> LOCAL Git commit admission, never PR/merge/authority.

Only a previously verified, independently imported Claude source patch may be
committed in its own isolated Role A topic checkout. This is not independent QA,
a deployment, a remote push, or a distributed lease. An interrupted Git write
stays UNKNOWN; recover only by exact HEAD/postimage reconciliation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import vf_office_v2_p0_subscription_artifact as stage

SCHEMA = "velvetos.office-v2.p0-local-source-commit.v1"
JOURNAL_STATE = "LOCAL_COMMIT_OUTCOME_UNKNOWN_NO_BLIND_RETRY"
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
MAX_JSON = 262144


class Refused(Exception):
    pass


def require(ok, code):
    if not ok:
        raise Refused(code)


def git(root, *args, input_bytes=None, raw=False):
    # Inherited Git environment and hooks are external effects, not QA.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    command = ["git", "-C", str(root), "-c", "core.hooksPath=" + os.devnull,
               "-c", "commit.gpgsign=false", "-c", "core.fsmonitor=false",
               "-c", "core.autocrlf=false",  # preserve receipt-bound bytes on Windows
               *args]
    try:
        p = subprocess.run(command, input=input_bytes, capture_output=True,
                           timeout=25, env=env, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refused("LOCAL_GIT_OUTCOME_UNKNOWN_" + type(exc).__name__) from exc
    require(p.returncode == 0, "LOCAL_GIT_COMMAND_FAILED_" + args[0].upper())
    return p.stdout if raw else p.stdout.rstrip(b"\n")


COMMAND_CONFIG = re.compile(r"filter\..+|diff\..+\.(command|textconv)")


def require_no_command_config(root):
    # Tracked .gitattributes only select a driver by name; Git can execute one only
    # when config defines it. Refuse any such driver from every config scope
    # (repo-local, worktree, included, command) before a filter-capable Git call.
    raw = git(root, "config", "-z", "--list", raw=True)
    for entry in filter(None, raw.split(b"\0")):
        key = entry.split(b"\n", 1)[0].decode("utf-8", "replace").lower()
        require(COMMAND_CONFIG.fullmatch(key) is None,
                "LOCAL_GIT_COMMAND_CONFIG_REFUSED")


def checked_json(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size <= MAX_JSON,
            "EVIDENCE_MISSING_SYMLINK_OR_OVERSIZED")
    return stage.read_json(p)


def local_checks(task_path, origin_path, checkpoint_path, import_path, root):
    task = checked_json(task_path)
    origin = Path(origin_path).resolve()
    import_record = checked_json(import_path)
    proof = stage.verify_stage_portable(task_path, origin_path,
                                        checkpoint_path, root)
    require(import_record.get("schema") == stage.PORTABLE_STAGE_RECEIPT and
            import_record.get("state") == "PORTABLE_SOURCE_STAGED_FOR_QA",
            "IMPORT_RECEIPT_NOT_SOURCE_STAGE")
    received_hash = import_record.pop("import_receipt_sha256", None)
    require(received_hash == stage.digest(import_record),
            "IMPORT_RECEIPT_SELF_HASH_INVALID")
    require(import_record.get("task_id") == task["task_id"] and
            import_record.get("task_sha256") == stage.digest(task) and
            import_record.get("base_sha") == task["base_sha"] and
            import_record.get("proposal_sha256") == proof["proposal_sha256"] and
            import_record.get("original_stage_receipt_sha256") ==
                proof["stage_receipt_sha256"] and
            import_record.get("original_draft_file_sha256") ==
                stage.file_digest(origin),
            "IMPORT_RECEIPT_ORIGIN_BINDING_INVALID")
    require(all(import_record.get(key) is False for key in (
            "model_reinvoked", "committed", "pushed", "merged",
            "external_effects_authorized", "shared_lease_admitted",
            "distributed_fencing_proven", "production_admitted",
            "independent_quality_approved")) and
            import_record.get("source_modified") is True and
            import_record.get("source_only_uncommitted") is True,
            "IMPORT_ALREADY_ACTED_OR_AUTHORITY_ESCALATED")
    root = Path(root).resolve()
    require(root.is_dir() and not Path(import_record["target_checkout"]).is_symlink()
            and root == Path(import_record["target_checkout"]).resolve() and
            root != Path(task["repo_path"]).resolve() and
            (root / ".git").exists(), "TARGET_MUST_BE_INDEPENDENT_CHECKOUT")
    branch = git(root, "branch", "--show-current").decode()
    require(branch == import_record.get("target_branch") and
            branch.startswith("role-a/") and branch not in ("main", "master"),
            "LOCAL_COMMIT_NOT_OWNED_ROLE_A_TOPIC")
    allowed = stage.auto_stage_allowlist(task, required=True)
    require(import_record.get("changed_paths") == allowed,
            "LOCAL_COMMIT_PATH_SCOPE_MISMATCH")
    rows = import_record.get("files")
    require(isinstance(rows, list) and len(rows) == len(allowed) and
            sorted(row.get("path") for row in rows if isinstance(row, dict)) ==
                allowed, "LOCAL_COMMIT_FILE_ROWS_INVALID")
    for row in rows:
        require(set(row) == {"path", "before_blob", "after_blob", "after_sha256"},
                "LOCAL_COMMIT_ROW_FIELDS_INVALID")
        name = row["path"]
        current = root / name
        require(current.is_file() and not current.is_symlink() and
                current.stat().st_size < 1048576,
                "LOCAL_COMMIT_SOURCE_FILE_UNSAFE")
        payload = current.read_bytes()
        require(hashlib.sha256(payload).hexdigest() == row["after_sha256"] and
                git(root, "hash-object", "--stdin", input_bytes=payload).decode() ==
                    row["after_blob"], "LOCAL_COMMIT_POSTIMAGE_MISMATCH")
    return task, import_record, received_hash, allowed, branch


def check_committed(root, base_sha, paths, rows):
    head = git(root, "rev-parse", "HEAD").decode()
    require(bool(SHA40.fullmatch(head)) and head != base_sha,
            "LOCAL_COMMIT_HEAD_NOT_ADVANCED")
    require(git(root, "rev-list", "--parents", "-n", "1", "HEAD").decode() ==
            head + " " + base_sha, "LOCAL_COMMIT_PARENT_MISMATCH")
    changed = sorted(filter(None, git(root, "diff-tree",
                                      "--no-commit-id", "--name-only", "-r",
                                      "HEAD").decode().splitlines()))
    require(changed == paths, "LOCAL_COMMIT_WRONG_CHANGED_PATHS")
    require(git(root, "status", "--porcelain=v1", "--untracked-files=all") == b"",
            "LOCAL_COMMIT_WORKTREE_NOT_CLEAN")
    for row in rows:
        blob = git(root, "rev-parse", "HEAD:" + row["path"]).decode()
        require(blob == row["after_blob"] and
                hashlib.sha256(git(root, "show", "HEAD:" + row["path"], raw=True)).hexdigest()
                    == row["after_sha256"],
                "LOCAL_COMMIT_GIT_TREE_POSTIMAGE_MISMATCH")
    return head


def commit(task_path, origin_path, checkpoint_path, import_path,
           root_path, output_path, recover=False):
    root = Path(root_path).resolve()
    require_no_command_config(root)
    raw_out = Path(output_path)
    require(not raw_out.is_symlink(), "LOCAL_COMMIT_RECEIPT_SYMLINK")
    output = raw_out.resolve()
    inputs = {Path(x).resolve() for x in (
        task_path, origin_path, checkpoint_path, import_path)}
    require(output.parent.is_dir() and not output.is_relative_to(root) and
            output.parent != Path(origin_path).resolve().parent and
            output not in inputs,
            "LOCAL_COMMIT_RECEIPT_MUST_BE_EXTERNAL")
    journal = output.with_suffix(".committing")
    require(not output.exists() and not output.is_symlink(),
            "LOCAL_COMMIT_EXISTING_RECEIPT_NO_RETRY")
    task, evidence, import_hash, allowed, branch = local_checks(
        task_path, origin_path, checkpoint_path, import_path, root)
    intent = {
        "schema": SCHEMA, "state": JOURNAL_STATE,
        "task_sha256": stage.digest(task),
        "import_receipt_sha256": import_hash,
        "base_sha": task["base_sha"],
        "repo_path": str(root), "branch": branch, "paths": allowed,
    }
    raw_intent = stage.canonical(intent)
    if recover:
        require(journal.is_file() and not journal.is_symlink() and
                journal.read_bytes() == raw_intent,
                "LOCAL_COMMIT_RECOVERY_INTENT_MISMATCH")
    else:
        require(not journal.exists() and not journal.is_symlink(),
                "LOCAL_COMMIT_PREVIOUS_ATTEMPT_UNKNOWN")
        require(git(root, "rev-parse", "HEAD").decode() == task["base_sha"],
                "LOCAL_COMMIT_BASE_MOVED")
        require(git(root, "diff", "--cached", "--name-only") == b"",
                "LOCAL_COMMIT_INDEX_NOT_CLEAN")
        status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
        expected = sorted((" M " + path) for path in allowed)
        require(sorted(status.decode().splitlines()) == expected,
                "LOCAL_COMMIT_UNEXPECTED_WORKTREE_CHANGE")
        diff_names = sorted(filter(None,
            git(root, "diff", "--name-only", "--no-ext-diff").decode().splitlines()))
        require(diff_names == allowed, "LOCAL_COMMIT_DIFF_SCOPE_MISMATCH")
        require(git(root, "diff", "--check", "--no-ext-diff") == b"",
                "LOCAL_COMMIT_WHITESPACE_ERROR")
        stage.exclusive_write(journal, raw_intent)
        # Git is a local effect; never re-run this block after uncertain exit.
        git(root, "add", "--", *allowed)
        staged_names = sorted(filter(None,
            git(root, "diff", "--cached", "--name-only").decode().splitlines()))
        require(staged_names == allowed, "LOCAL_COMMIT_INDEX_SCOPE_DRIFT")
        message = "office612: locally stage verified model source " + task["task_id"]
        git(root, "-c", "user.name=VelvetOS-Office612-LAB",
            "-c", "user.email=office612-local@invalid",
            "commit", "-m", message)
    head = check_committed(root, task["base_sha"], allowed, evidence["files"])
    record = {
        **intent, "state": "LOCAL_COMMITTED_FOR_INDEPENDENT_QA_ONLY",
        "head_sha": head, "git_parent": task["base_sha"],
        "commit_written_in_this_command": not recover,
        "reconciled_after_crash": recover,
        "model_reinvoked": False, "local_commit": True,
        "independent_quality_approved": False, "ci_passed": False,
        "pushed": False, "pr_opened": False, "merged": False,
        "distributed_fencing_proven": False, "production_admitted": False,
    }
    stage.exclusive_write(output, stage.canonical({
        **record, "local_commit_receipt_sha256": stage.digest(record)}))
    require(journal.is_file() and not journal.is_symlink() and
            journal.read_bytes() == raw_intent,
            "LOCAL_COMMIT_JOURNAL_CHANGED")
    journal.unlink()
    return {"result": record["state"], "head_sha": head,
            "paths": allowed, "local_receipt": str(output),
            "reconciled_after_crash": recover,
            "independent_quality_approved": False,
            "distributed_fencing_proven": False, "production_admitted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--origin-receipt", required=True)
    parser.add_argument("--checkpoint-before", required=True)
    parser.add_argument("--import-receipt", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--commit-receipt", required=True)
    parser.add_argument("--recover", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(commit(
            args.task, args.origin_receipt, args.checkpoint_before,
            args.import_receipt, args.repo, args.commit_receipt,
            recover=args.recover), sort_keys=True))
    except (Refused, stage.Refused, OSError, ValueError, KeyError,
            TypeError, subprocess.TimeoutExpired) as exc:
        print("REFUSED:" + (str(exc) if isinstance(exc, (Refused, stage.Refused))
                             else type(exc).__name__), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
