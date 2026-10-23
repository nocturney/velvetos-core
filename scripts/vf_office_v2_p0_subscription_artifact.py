#!/usr/bin/env python3
"""Office #612 one-shot subscription-backed code-proposal artifact adapter.

This is a producer for the existing Project State / evidence chain, NOT a
scheduler, autonomous editor, effect authority, PR writer, or OS sandbox.
Claude runs with ALL built-in tools disabled and no MCP configuration. Generated
text is untrusted; it must be reviewed and tested independently before use.

`stage` is a separate, explicitly operator-approved step: it applies a verified
proposal that is exactly a plain unified git diff of existing tracked text files
to the LOCAL isolated worktree, and writes an external tamper-evident
`<receipt>.staged.json`. It never commits, pushes, merges, runs generated code
or grants authority; SOURCE_STAGED_FOR_QA is not P0 or two-host admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time

import vf_office_v2_continuity as continuity

SCHEMA = "velvetos.office-v2.p0-subscription-artifact-task.v1"
RECEIPT = "velvetos.office-v2.p0-subscription-artifact-receipt.v1"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
TASK_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{2,95}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
TASK_FIELDS = frozenset({
    "schema", "issue_url", "task_id", "repo_path", "base_sha", "branch",
    "checkpoint_path", "prompt", "timeout_seconds",
})
FORBIDDEN_ENV = (
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
)
STAGE_RECEIPT = "velvetos.office-v2.p0-subscription-source-stage-receipt.v1"
PROPOSAL_SHA = re.compile(r"[0-9a-f]{64}\Z")
# Safe subset: no dot-leading components (.git, .., .gitattributes), no
# whitespace/quoting/pathspec magic, no absolute or empty components.
SAFE_PATH = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.+-]*(?:/[A-Za-z0-9_][A-Za-z0-9_.+-]*)*\Z")
DIFF_HEADER = re.compile(r"diff --git a/(\S+) b/(\S+)\Z")
INDEX_LINE = re.compile(r"index ([0-9a-f]{7,64})\.\.([0-9a-f]{7,64}) (100644|100755)\Z")
HUNK = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?\Z")
NO_EOL = "\\ No newline at end of file"
MAX_STAGE_FILES = 16


class Refused(Exception):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(131072), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Refused("JSON_OBJECT_REQUIRED")
    return value


def exclusive_write(path, value):
    dest = Path(path)
    with dest.open("xb") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def git(repo, *argv):
    p = subprocess.run(["git", "-C", str(repo), *argv],
                       capture_output=True, timeout=12)
    if p.returncode:
        raise Refused("GIT_READBACK_FAILED")
    return p.stdout.decode("utf-8", "replace").strip()


def validate_task(task, receipt_path):
    if set(task) != TASK_FIELDS or task["schema"] != SCHEMA or task["issue_url"] != ISSUE:
        raise Refused("TASK_SCHEMA_OR_SCOPE")
    if not isinstance(task["task_id"], str) or not TASK_ID.fullmatch(task["task_id"]):
        raise Refused("TASK_ID_INVALID")
    if not isinstance(task["base_sha"], str) or not SHA.fullmatch(task["base_sha"]):
        raise Refused("BASE_SHA_INVALID")
    if (not isinstance(task["branch"], str) or
            task["branch"] in ("main", "master", "HEAD") or
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{2,127}", task["branch"])):
        raise Refused("ISOLATED_TOPIC_BRANCH_REQUIRED")
    if not isinstance(task["prompt"], str) or not (25 <= len(task["prompt"].encode("utf-8")) <= 7000):
        raise Refused("PROMPT_LENGTH_INVALID")
    if "\x00" in task["prompt"]:
        raise Refused("PROMPT_NUL")
    if type(task["timeout_seconds"]) is not int or not 15 <= task["timeout_seconds"] <= 180:
        raise Refused("TIMEOUT_OUT_OF_RANGE")
    if os.name != "nt" and os.geteuid() == 0:
        raise Refused("ROOT_MODEL_EXECUTION_DENIED")
    if os.name == "nt" and "SYSTEM" in os.environ.get("USERNAME", "").upper():
        raise Refused("SYSTEM_MODEL_EXECUTION_DENIED")
    if any(key in os.environ for key in FORBIDDEN_ENV):
        raise Refused("METERED_API_OR_ALTERNATE_PROVIDER_ENV_DENIED")
    for key in ("repo_path", "checkpoint_path"):
        if not isinstance(task[key], str) or not Path(task[key]).is_absolute():
            raise Refused("ABSOLUTE_INPUT_PATH_REQUIRED")
    repo = Path(task["repo_path"]).resolve()
    checkpoint = Path(task["checkpoint_path"]).resolve()
    out = Path(receipt_path).resolve()
    if not repo.is_dir() or not (repo / ".git").exists() or not checkpoint.is_file():
        raise Refused("REPO_OR_CHECKPOINT_MISSING")
    if out.is_relative_to(repo) or checkpoint.is_relative_to(repo):
        raise Refused("RECEIPT_AND_CHECKPOINT_MUST_BE_EXTERNAL")
    if git(repo, "rev-parse", "HEAD") != task["base_sha"]:
        raise Refused("STALE_BASE_SHA")
    if git(repo, "branch", "--show-current") != task["branch"]:
        raise Refused("BRANCH_MISMATCH")
    if git(repo, "status", "--porcelain=v1", "--untracked-files=all"):
        raise Refused("WORKTREE_NOT_CLEAN")
    state = read_json(checkpoint)
    if continuity.required_shape(state):
        raise Refused("INVALID_CONTINUITY_CHECKPOINT")
    code = state.get("code_baseline") or {}
    for field, expected in (
        ("repo", "nocturney/velvetos-core"),
        ("base_sha", task["base_sha"]),
        ("branch", task["branch"]),
        ("worktree_path", str(repo)),
    ):
        if code.get(field) != expected:
            raise Refused("CONTINUITY_BASELINE_MISMATCH_" + field)
    if state.get("active_external_effects"):
        raise Refused("ACTIVE_EXTERNAL_EFFECTS_DENIED")
    return repo, checkpoint, state, out


def claude_cli():
    binary = shutil.which("claude")
    if not binary:
        raise Refused("CLAUDE_CLI_MISSING")
    auth = subprocess.run([binary, "auth", "status", "--json"],
                          capture_output=True, timeout=15)
    if auth.returncode:
        raise Refused("CLAUDE_LOGIN_REQUIRED")
    try:
        observed = json.loads(auth.stdout)
    except (ValueError, UnicodeError) as exc:
        raise Refused("CLAUDE_AUTH_UNREADABLE") from exc
    if (observed.get("loggedIn") is not True or
            observed.get("authMethod") != "claude.ai" or
            observed.get("apiProvider") != "firstParty"):
        raise Refused("CLAUDE_SUBSCRIPTION_NOT_VERIFIED")
    version = subprocess.run([binary, "--version"], capture_output=True, timeout=10)
    if version.returncode:
        raise Refused("CLAUDE_VERSION_UNAVAILABLE")
    return binary, version.stdout.decode("utf-8", "replace").strip()[:120]


def verify(task, receipt_path):
    receipt_path = Path(receipt_path).resolve()
    repo, checkpoint, before, _ = validate_task(task, receipt_path)
    receipt = read_json(receipt_path)
    checksum = receipt.pop("receipt_sha256", None)
    if checksum != digest(receipt):
        raise Refused("RECEIPT_TAMPERED")
    if (receipt.get("schema") != RECEIPT or
            receipt.get("state") != "MODEL_DRAFT_ONLY" or
            receipt.get("task_sha256") != digest(task) or
            receipt.get("auth_method") != "claude.ai" or
            receipt.get("tools_enabled") is not False or
            receipt.get("external_effects_authorized") is not False):
        raise Refused("RECEIPT_AUTHORITY_INVALID")
    proposal = receipt_path.with_suffix(".proposal.txt")
    after_path = receipt_path.with_suffix(".checkpoint.json")
    if (not proposal.is_file() or proposal.is_symlink() or
            not after_path.is_file() or after_path.is_symlink()):
        raise Refused("RECEIPT_ARTIFACT_MISSING")
    if (file_digest(proposal) != receipt["proposal_sha256"] or
            file_digest(checkpoint) != receipt["checkpoint_before_sha256"] or
            file_digest(after_path) != receipt["checkpoint_after_sha256"] or
            continuity.verify(before, read_json(after_path))["status"] != "PASS"):
        raise Refused("ARTIFACT_OR_CONTINUITY_MISMATCH")
    if git(repo, "status", "--porcelain=v1", "--untracked-files=all"):
        raise Refused("WORKTREE_CHANGED")
    return {"state": "MODEL_DRAFT_ONLY", "verified": True,
            "task_id": task["task_id"], "real_model_invoked": True,
            "source_edit": False, "two_host_admitted": False}


def run(task_path, receipt_path):
    task = read_json(task_path)
    repo, checkpoint, before, dest = validate_task(task, receipt_path)
    proposal = dest.with_suffix(".proposal.txt")
    after_path = dest.with_suffix(".checkpoint.json")
    journal = dest.with_suffix(".running")
    if any(x.exists() for x in (dest, proposal, after_path, journal)):
        raise Refused("EXISTING_ATTEMPT_NO_RETRY")
    binary, version = claude_cli()
    if not dest.parent.is_dir():
        raise Refused("EXTERNAL_RECEIPT_DIRECTORY_REQUIRED")
    exclusive_write(journal, canonical({"task": digest(task), "state": "RUNNING_NO_BLIND_RETRY"}))
    started = time.monotonic()
    result = subprocess.run(
        [binary, "-p", "--tools", "", "--strict-mcp-config", "--max-turns", "1",
         "--output-format", "json"],
        input=task["prompt"].encode("utf-8"), cwd=str(repo), capture_output=True,
        timeout=task["timeout_seconds"])
    if result.returncode or len(result.stdout) > 200000:
        raise Refused("MODEL_CLI_FAILED_OR_UNBOUNDED_UNKNOWN")
    try:
        payload = json.loads(result.stdout)
    except (ValueError, UnicodeError) as exc:
        raise Refused("MODEL_CLI_RESULT_NOT_JSON") from exc
    body = payload.get("result")
    if (payload.get("is_error") is not False or payload.get("subtype") != "success" or
            payload.get("num_turns") != 1 or not isinstance(body, str) or
            not 1 <= len(body.encode("utf-8")) <= 65536):
        raise Refused("MODEL_CLI_NOT_VERIFIABLY_SUCCESSFUL")
    if git(repo, "rev-parse", "HEAD") != task["base_sha"] or git(
            repo, "status", "--porcelain=v1", "--untracked-files=all"):
        raise Refused("UNEXPECTED_MODEL_WORKTREE_MUTATION")
    after = continuity.compact_manifest(before, pressure_score=0.0)
    if continuity.verify(before, after)["status"] != "PASS":
        raise Refused("CONTINUITY_VERIFY_FAILED")
    exclusive_write(proposal, body.encode("utf-8"))
    exclusive_write(after_path, (json.dumps(after, ensure_ascii=False, indent=2) + "\n").encode())
    receipt = {
        "schema": RECEIPT, "state": "MODEL_DRAFT_ONLY",
        "issue_url": ISSUE, "task_id": task["task_id"], "task_sha256": digest(task),
        "base_sha": task["base_sha"], "worker_host": platform.node(),
        "auth_method": "claude.ai", "cli_version": version,
        "tools_enabled": False, "external_effects_authorized": False,
        "model_invoked": True, "num_turns": 1,
        "elapsed_ms": round((time.monotonic() - started) * 1000),
        "proposal_sha256": file_digest(proposal),
        "checkpoint_before_sha256": file_digest(checkpoint),
        "checkpoint_after_sha256": file_digest(after_path),
        "git_writes": 0, "model_output_is_reviewed_code": False,
        "cross_host_lease_admitted": False,
    }
    exclusive_write(dest, canonical({**receipt, "receipt_sha256": digest(receipt)}))
    result = verify(task, dest)
    journal.unlink()
    return result


def git_bytes(repo, *argv):
    p = subprocess.run(["git", "-C", str(repo), *argv],
                       capture_output=True, timeout=12)
    if p.returncode:
        raise Refused("GIT_READBACK_FAILED")
    return p.stdout


def git_apply(repo, patch_bytes, check):
    """Argv-only `git apply` of the exact verified bytes; never --unsafe-paths."""
    argv = ["git", "-C", str(repo), "apply", "--whitespace=nowarn", "-p1"]
    if check:
        argv.append("--check")
    p = subprocess.run([*argv, "-"], input=patch_bytes,
                       capture_output=True, timeout=12)
    return p.returncode == 0


def allow_path(value):
    if not isinstance(value, str) or len(value) > 200 or not SAFE_PATH.fullmatch(value):
        raise Refused("ALLOW_PATH_INVALID")
    return value


def parse_git_diff(text):
    """Strictly parse a pure in-place git diff; every line must be accounted for."""
    if not text.strip():
        raise Refused("EMPTY_DIFF")
    if "\x00" in text or "\r" in text or not text.endswith("\n"):
        raise Refused("PATCH_ENCODING_OR_TERMINATION_INVALID")
    lines = text[:-1].split("\n")
    files, i = [], 0
    while i < len(lines):
        header = DIFF_HEADER.fullmatch(lines[i])
        if not header or header.group(1) != header.group(2):
            raise Refused("PATCH_FILE_HEADER_INVALID")
        path = header.group(1)
        if len(path) > 200 or not SAFE_PATH.fullmatch(path):
            raise Refused("PATCH_PATH_INVALID")
        if path in {f["path"] for f in files} or len(files) >= MAX_STAGE_FILES:
            raise Refused("PATCH_DUPLICATE_OR_TOO_MANY_FILES")
        # Mode, new/deleted file, rename/copy and similarity headers all fail
        # here because the line after `diff --git` must be a plain index line.
        index = INDEX_LINE.fullmatch(lines[i + 1]) if i + 1 < len(lines) else None
        if not index or index.group(1) == index.group(2):
            raise Refused("PATCH_INDEX_OR_MODE_HEADER_INVALID")
        if i + 2 < len(lines) and lines[i + 2].startswith(("GIT binary patch", "Binary files ")):
            raise Refused("BINARY_PATCH_DENIED")
        if lines[i + 2:i + 4] != ["--- a/" + path, "+++ b/" + path]:
            raise Refused("PATCH_FILE_HEADER_INVALID")
        i += 4
        hunks = 0
        while i < len(lines) and lines[i].startswith("@@"):
            hunk = HUNK.fullmatch(lines[i])
            if not hunk:
                raise Refused("PATCH_HUNK_HEADER_INVALID")
            old_n = 1 if hunk.group(2) is None else int(hunk.group(2))
            new_n = 1 if hunk.group(4) is None else int(hunk.group(4))
            i, hunks, changes, prev = i + 1, hunks + 1, 0, ""
            while old_n or new_n:
                if i >= len(lines):
                    raise Refused("PATCH_HUNK_TRUNCATED")
                line, tag = lines[i], lines[i][:1]
                if line == NO_EOL and prev in (" ", "-", "+"):
                    prev, i = "\\", i + 1
                    continue
                if tag == " ":
                    old_n, new_n = old_n - 1, new_n - 1
                elif tag == "-":
                    old_n, changes = old_n - 1, changes + 1
                elif tag == "+":
                    new_n, changes = new_n - 1, changes + 1
                else:
                    raise Refused("PATCH_HUNK_LINE_INVALID")
                if old_n < 0 or new_n < 0:
                    raise Refused("PATCH_HUNK_COUNT_MISMATCH")
                prev, i = tag, i + 1
            if i < len(lines) and lines[i] == NO_EOL and prev in (" ", "-", "+"):
                i += 1
            if not changes:
                raise Refused("PATCH_FILE_WITHOUT_CHANGES")
        if not hunks:
            raise Refused("PATCH_FILE_WITHOUT_CHANGES")
        files.append({"path": path, "old": index.group(1), "new": index.group(2),
                      "mode": index.group(3)})
    return files


def regular_text_file(repo, rel):
    current = repo
    for part in rel.split("/"):
        current = current / part
        if current.is_symlink():
            raise Refused("SYMLINK_PATH_DENIED")
    if not current.is_file() or b"\x00" in current.read_bytes():
        raise Refused("TARGET_NOT_REGULAR_TEXT_FILE")
    return current


def tracked_base_blob(repo, item):
    listed = re.fullmatch(r"(\d{6}) (\w+) ([0-9a-f]{40,64})\t(.+)",
                          git(repo, "ls-tree", "--full-tree", "HEAD", "--", item["path"]))
    if (not listed or listed.group(2) != "blob" or listed.group(4) != item["path"] or
            listed.group(1) not in ("100644", "100755")):
        raise Refused("PATH_NOT_TRACKED_REGULAR_FILE")
    if listed.group(1) != item["mode"]:
        raise Refused("PATCH_MODE_MISMATCH")
    if not listed.group(3).startswith(item["old"]):
        raise Refused("PATCH_INDEX_BASE_MISMATCH")
    regular_text_file(repo, item["path"])
    return listed.group(3)


def stage(task, receipt_path, proposal_sha256, allow_paths):
    receipt_path = Path(receipt_path).resolve()
    if not isinstance(proposal_sha256, str) or not PROPOSAL_SHA.fullmatch(proposal_sha256):
        raise Refused("PROPOSAL_SHA256_FORMAT")
    if not isinstance(allow_paths, (list, tuple)) or not 1 <= len(allow_paths) <= MAX_STAGE_FILES:
        raise Refused("ALLOW_PATH_COUNT")
    allowed = sorted(allow_path(p) for p in allow_paths)
    if len(set(allowed)) != len(allowed):
        raise Refused("ALLOW_PATH_DUPLICATE")
    staged = receipt_path.with_suffix(".staged.json")
    journal = receipt_path.with_suffix(".staging")
    if any(x.exists() or x.is_symlink() for x in (staged, journal)):
        raise Refused("EXISTING_STAGE_NO_REPLAY")
    verify(task, receipt_path)
    repo = Path(task["repo_path"]).resolve()
    draft_sha = file_digest(receipt_path)
    if read_json(receipt_path).get("proposal_sha256") != proposal_sha256:
        raise Refused("PROPOSAL_SHA256_MISMATCH")
    patch_bytes = receipt_path.with_suffix(".proposal.txt").read_bytes()
    if hashlib.sha256(patch_bytes).hexdigest() != proposal_sha256:
        raise Refused("PROPOSAL_SHA256_MISMATCH")
    try:
        files = parse_git_diff(patch_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise Refused("PROPOSAL_NOT_UTF8") from exc
    if sorted(f["path"] for f in files) != allowed:
        raise Refused("ALLOWLIST_NOT_EXACT_PATCH_SCOPE")
    for item in files:
        item["before_blob"] = tracked_base_blob(repo, item)
    if not git_apply(repo, patch_bytes, check=True):
        raise Refused("GIT_APPLY_CHECK_FAILED")
    if git(repo, "status", "--porcelain=v1", "--untracked-files=all"):
        raise Refused("WORKTREE_CHANGED")
    exclusive_write(journal, canonical({
        "task": digest(task), "proposal_sha256": proposal_sha256, "paths": allowed,
        "state": "STAGING_NO_BLIND_RETRY"}))
    # From here the effect outcome may be uncertain: every failure leaves the
    # journal in place and never retries, reverts or commits.
    if not git_apply(repo, patch_bytes, check=False):
        raise Refused("GIT_APPLY_FAILED_OUTCOME_UNKNOWN_JOURNAL_PRESERVED")
    if (git(repo, "rev-parse", "HEAD") != task["base_sha"] or
            git(repo, "branch", "--show-current") != task["branch"]):
        raise Refused("POST_STAGE_HEAD_OR_BRANCH_MOVED_JOURNAL_PRESERVED")
    expected_status = b"".join(b" M " + p.encode() + b"\x00" for p in allowed)
    if (git_bytes(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all",
                  "--no-renames") != expected_status or
            git(repo, "diff", "--name-only", "--no-renames").split("\n") != allowed or
            git(repo, "diff", "--cached", "--name-only") or
            git(repo, "diff", "--summary")):
        raise Refused("POST_STAGE_SCOPE_MISMATCH_JOURNAL_PRESERVED")
    for item in files:
        try:
            path = regular_text_file(repo, item["path"])
        except Refused as exc:
            raise Refused("POST_STAGE_FILE_INVALID_JOURNAL_PRESERVED") from exc
        item["after_blob"] = git(repo, "hash-object", "--", item["path"])
        # A no-tools model cannot calculate a Git blob SHA for its proposed
        # postimage. Allow only the explicit 0000000 placeholder; always
        # independently compute/store the real postimage blob and SHA-256.
        if item["new"] != "0000000" and not item["after_blob"].startswith(item["new"]):
            raise Refused("POST_STAGE_BLOB_MISMATCH_JOURNAL_PRESERVED")
        item["after_sha256"] = file_digest(path)
    record = {
        "schema": STAGE_RECEIPT, "state": "SOURCE_STAGED_FOR_QA",
        "issue_url": ISSUE, "task_id": task["task_id"], "task_sha256": digest(task),
        "draft_receipt_sha256": draft_sha, "proposal_sha256": proposal_sha256,
        "operator_supplied_proposal_sha256": proposal_sha256,
        "operator_supplied_allowlist": allowed, "changed_paths": allowed,
        "base_sha": task["base_sha"], "branch": task["branch"],
        "head_after": task["base_sha"], "worker_host": platform.node(),
        "files": [{k: item[k] for k in ("path", "mode", "before_blob", "after_blob",
                                         "after_sha256")} for item in files],
        "bounded_proof": {
            "git_apply_check_passed": True, "status_exactly_allowlist_modified": True,
            "diff_name_only_equals_allowlist": True, "index_unchanged": True,
            "no_mode_create_delete_rename": True,
            "after_blobs_independently_computed": True,
            "new_index_placeholders": sum(f["new"] == "0000000" for f in files),
        },
        "committed": False, "pushed": False, "merged": False,
        "generated_code_executed": False, "tools_enabled": False,
        "external_effects_authorized": False, "model_output_is_reviewed_code": False,
        "production": False, "p0_admitted": False, "two_host_admitted": False,
    }
    exclusive_write(staged, canonical({**record, "stage_receipt_sha256": digest(record)}))
    journal.unlink()
    return {"state": "SOURCE_STAGED_FOR_QA", "staged": True,
            "task_id": task["task_id"], "changed_paths": allowed,
            "stage_receipt": str(staged), "stage_receipt_sha256": digest(record),
            "committed": False, "pushed": False, "generated_code_executed": False,
            "p0_admitted": False, "two_host_admitted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("run", "verify"):
        p = sub.add_parser(command)
        p.add_argument("--task", required=True)
        p.add_argument("--receipt", required=True)
    p = sub.add_parser("stage")
    p.add_argument("--task", required=True)
    p.add_argument("--receipt", required=True)
    p.add_argument("--proposal-sha256", required=True)
    p.add_argument("--allow-path", action="append", required=True)
    args = parser.parse_args()
    try:
        task = read_json(args.task)
        if args.command == "run":
            result = run(args.task, args.receipt)
        elif args.command == "verify":
            result = verify(task, args.receipt)
        else:
            result = stage(task, args.receipt, args.proposal_sha256, args.allow_path)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    except (Refused, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print("REFUSED:" + (str(exc) if isinstance(exc, Refused) else type(exc).__name__),
              file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
