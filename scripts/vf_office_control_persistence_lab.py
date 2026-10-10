#!/usr/bin/env python3
"""Offline execution of the ACTUAL Office Control Plane persistence Bash step.

Isolated temporary Git repository and synthetic no-network push stub. Never
touches main, credentials, Office state, real machine writer or external APIs.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "office-control-plane.yml"
SIGNAL = "packages/velvetos/living-studio/data/signal-room.jsonl"
RECEIPTS = "packages/velvetos/living-studio/data/receipts.jsonl"
LATEST = "packages/velvetos/living-studio/data/activation-latest.json"
HISTORY = "packages/velvetos/living-studio/data/activation-history.jsonl"
MUSEUM = "office/learning/failure-museum/entries.jsonl"
HANDOFF = "office/control/HANDOFF.json"
HANDOFF_HE = "office/control/HANDOFF-he.md"
CANDIDATE = "packages/vfharness/state/learning-candidates/learn-ci-synthetic.json"
STUB = "scripts/push-main-with-check-all.sh"

def require(value, reason):
    if not value:
        raise AssertionError(reason)

def git(repo, *args):
    cmd = subprocess.run(["git", *args], cwd=repo, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
    if cmd.returncode:
        raise AssertionError("FIXTURE_GIT_FAILED:" + " ".join(args) + ":" + cmd.stderr[-350:])
    return cmd.stdout.strip()

def write(repo, rel, body):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")

def bash_binary():
    if os.name == "nt":
        p = Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Git" / "bin" / "bash.exe"
        require(p.is_file(), "WINDOWS_GIT_BASH_UNAVAILABLE")
        return str(p)
    p = shutil.which("bash")
    require(p, "BASH_UNAVAILABLE")
    return p

def actual_workflow_stage():
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    heading = "      - name: Persist activation evidence only when materially changed"
    require(lines.count(heading) == 1, "PERSIST_STEP_IDENTITY_CHANGED")
    start = lines.index(heading)
    boundary = next((i for i in range(start + 1, len(lines))
                     if lines[i].startswith("      - name: ")), len(lines))
    run_at = next((i for i in range(start + 1, boundary)
                   if lines[i] == "        run: |"), None)
    require(run_at is not None, "PERSIST_RUN_BLOCK_MISSING")
    block = "\n".join(line[10:] for line in lines[run_at + 1:boundary] if line.strip()) + "\n"
    marker = next((line.split(":", 1)[1].strip().split()
                   for line in lines if line.startswith("# VELVET_MACHINE_WRITER_ALLOW:")), [])
    require(set((HANDOFF, HANDOFF_HE, LATEST, HISTORY, MUSEUM,
                 "packages/vfharness/state/learning-candidates")).issubset(set(marker)),
            "PROTECTED_MACHINE_WRITER_HANDOFF_ALLOWLIST_MISSING")
    require(SIGNAL not in marker and RECEIPTS not in marker,
            "IGNORED_CACHES_SHOULD_NOT_BE_WRITER_ALLOWLISTED")
    for required in ('git check-ignore -q -- "$p"',
                     'git add --ignore-removal -- "$learning"',
                     'git diff --cached --quiet',
                     'git diff --name-only',
                     'office/control/HANDOFF.json',
                     'office/control/HANDOFF-he.md',
                     'bash scripts/push-main-with-check-all.sh main'):
        require(required in block, "PERSIST_FAIL_CLOSED_GUARD_MISSING:" + required)
    require("git add -f" not in block and "git push -f" not in block,
            "PERSIST_FORCE_STAGING_OR_PUSH_FORBIDDEN")
    return block

def execute(shell, repo, block):
    result = subprocess.run([shell, "-c", block], cwd=repo, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=40)
    if result.returncode:
        raise AssertionError("WORKFLOW_PERSIST_FIXTURE_FAILED:" +
                             result.stdout[-500:] + result.stderr[-600:])
    return result.stdout + result.stderr

def files_in_commit(repo):
    return set(git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines())

def execute_refused(shell, repo, block, expected):
    result = subprocess.run([shell, "-c", block], cwd=repo, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=40)
    require(result.returncode != 0 and expected in (result.stdout + result.stderr),
            "EXPECTED_DIRTY_WORKTREE_REFUSAL_MISSING:" + expected)
    return result.stdout + result.stderr

def selftest():
    shell = bash_binary()
    block = actual_workflow_stage()
    checks = []
    with tempfile.TemporaryDirectory(prefix="office-control-persist-test-") as t:
        repo = Path(t)
        git(repo, "init", "-q")
        git(repo, "config", "user.name", "fixture-owner")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "core.autocrlf", "false")
        write(repo, "packages/velvetos/living-studio/.gitignore",
              "data/signal-room.jsonl\ndata/receipts.jsonl\n")
        write(repo, STUB, "#!/usr/bin/env bash\nset -e\ntest \"$1\" = main\nprintf 'NO_NETWORK_PUSH\\n' > scripts/fake-push-receipt.txt\n")
        write(repo, HANDOFF, '{"updatedAt":"synthetic-base"}\n')
        write(repo, HANDOFF_HE, "# Synthetic canonical handoff baseline\n")
        write(repo, "misc/foreign-policy.json", '{"control":"protected"}\n')
        git(repo, "add", "--", "packages/velvetos/living-studio/.gitignore", STUB, HANDOFF, HANDOFF_HE,
            "misc/foreign-policy.json")
        git(repo, "commit", "-qm", "synthetic baseline")
        initial = git(repo, "rev-parse", "HEAD")
        # Ignored-only stream must never force Git writes or a new commit.
        write(repo, SIGNAL, "{\"ephemeral\":true}\n")
        write(repo, RECEIPTS, "{\"temporary\":true}\n")
        output = execute(shell, repo, block)
        require("No material eligible" in output and git(repo, "rev-parse", "HEAD") == initial,
                "IGNORED_RUNTIME_ONLY_SHOULD_NOT_COMMIT")
        checks.append("ignored_runtime_streams_alone_do_not_commit")
        # A new untracked (nonignored) allowlisted file MUST be staged.
        for rel, text in ((LATEST, "{\"state\":\"lab\"}\n"),
                          (HISTORY, "{\"event\":\"fixture\"}\n"),
                          (MUSEUM, "{\"incident\":\"fixture\"}\n"),
                          (CANDIDATE, "{\"candidate_id\":\"synthetic\"}\n"),
                          (HANDOFF, '{"updatedAt":"new-lab-snapshot"}\n'),
                          (HANDOFF_HE, "# Synthetic canonical handoff refreshed\n")):
            write(repo, rel, text)
        execute(shell, repo, block)
        require(git(repo, "rev-parse", "HEAD") != initial,
                "NEW_ALLOWLISTED_FILES_NOT_COMMITTED")
        require(files_in_commit(repo) == {LATEST, HISTORY, MUSEUM, CANDIDATE,
                                          HANDOFF, HANDOFF_HE},
                "INCORRECT_ALLOWLISTED_COMMIT_PATHS:" + str(files_in_commit(repo)))
        require((repo/"scripts/fake-push-receipt.txt").read_text() == "NO_NETWORK_PUSH\n",
                "REAL_PUSH_STUB_NOT_USED")
        checks.append("fresh_allowlisted_evidence_and_ci_candidate_committed")
        require((repo / HANDOFF).read_text(encoding="utf-8") ==
                '{"updatedAt":"new-lab-snapshot"}\n' and
                (repo / HANDOFF_HE).read_text(encoding="utf-8") ==
                "# Synthetic canonical handoff refreshed\n",
                "CANONICAL_HANDOFF_PAIR_NOT_PRESERVED")
        checks.append("canonical_handoff_json_and_hebrew_are_staged_together")
        # The originally ignored caches remain out of Git.
        require(not (set((SIGNAL, RECEIPTS)) & files_in_commit(repo)) and
                not git(repo, "ls-files", "--", SIGNAL, RECEIPTS),
                "IGNORED_CACHE_ACCIDENTALLY_PERSISTED")
        checks.append("ignored_signal_and_receipts_never_staged")
        current = git(repo, "rev-parse", "HEAD")
        output = execute(shell, repo, block)
        require("No material eligible" in output and git(repo, "rev-parse", "HEAD") == current,
                "STABLE_NOOP_CREATED_COMMIT")
        checks.append("unchanged_material_is_idempotent_noop")
        # Automatic ingestion cannot stage deletions of canonical candidates.
        (repo/CANDIDATE).unlink()
        execute_refused(shell, repo, block, "unapproved unstaged tracked files")
        require(git(repo, "rev-parse", "HEAD") == current and
                not git(repo, "diff", "--cached", "--name-only"),
                "CANDIDATE_AUTO_DELETION_STAGED")
        git(repo, "restore", "--", CANDIDATE)
        checks.append("candidate_deletion_refused_not_staged")
        # Changes to explicitly allowed files should still advance one commit.
        write(repo, LATEST, "{\"state\":\"updated\"}\n")
        write(repo, CANDIDATE, "{\"candidate_id\":\"synthetic\",\"evidence\":[1]}\n")
        execute(shell, repo, block)
        require(files_in_commit(repo) == {LATEST, CANDIDATE},
                "UPDATED_ALLOWLISTED_MATERIAL_NOT_PERSISTED")
        checks.append("tracked_allowlisted_updates_committed")
        # A non-allowlisted file may exist but cannot be staged by this workflow.
        current = git(repo, "rev-parse", "HEAD")
        write(repo, "secrets.env", "synthetic-not-a-secret\n")
        output = execute(shell, repo, block)
        require("No material eligible" in output and git(repo, "rev-parse", "HEAD") == current
                and not git(repo, "ls-files", "--", "secrets.env"),
                "UNAUTHORIZED_PATH_STAGED")
        checks.append("unrelated_untracked_file_not_staged")
        # A modified tracked policy artifact not in the per-writer allowlist
        # MUST fail before commit or protected precheck; never stash it away.
        write(repo, "misc/foreign-policy.json", '{"control":"tampered"}\n')
        execute_refused(shell, repo, block, "unapproved unstaged tracked files")
        require(git(repo, "rev-parse", "HEAD") == current,
                "UNAPPROVED_TRACKED_CHANGE_WAS_COMMITTED")
        checks.append("unknown_tracked_policy_change_blocks_writer")
        git(repo, "restore", "--", "misc/foreign-policy.json")
        output = execute(shell, repo, block)
        require("No material eligible" in output and git(repo, "rev-parse", "HEAD") == current,
                "DIRTY_WORKTREE_REFUSAL_DID_NOT_RECOVER")
        checks.append("clean_state_after_refusal_still_idempotent")
    require(len(checks) == 10, "PERSIST_TEST_COUNT_DRIFT")
    return {"status":"PASS_OFFLINE", "tests":len(checks), "cases":checks,
            "real_git_pushes":0, "production_effects":0, "office_writes":0}

def main():
    if sys.argv[1:] != ["selftest"]:
        raise SystemExit("only selftest is permitted")
    print(json.dumps(selftest(), sort_keys=True))

if __name__ == "__main__":
    main()
