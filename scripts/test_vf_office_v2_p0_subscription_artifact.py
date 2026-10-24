#!/usr/bin/env python3
"""Negative and positive contract tests; the live Claude proof is separate."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import vf_office_v2_continuity as continuity
import vf_office_v2_p0_subscription_artifact as target


def config_path(path):
    """Quote a path for synthetic Git config; Windows backslashes must be escaped."""
    return '"' + str(path).replace("\\", "\\\\").replace('"', '\\"') + '"'


class SubscriptionArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        saved = {key: os.environ.pop(key) for key in target.FORBIDDEN_ENV if key in os.environ}
        self.addCleanup(os.environ.update, saved)
        base = Path(self.temp.name)
        self.repo = (base / "repo").resolve()
        self.repo.mkdir()
        def git(*args):
            subprocess.run(["git", "-C", str(self.repo), *args],
                           check=True, capture_output=True)
        git("init", "-q")
        git("checkout", "-q", "-b", "role-a/isolated-test")
        self.git = git
        self.original_run = subprocess.run
        self.model_body = "def bounded_add(a, b):\n    return a + b\n"
        (self.repo / "entry.txt").write_text("baseline\n", encoding="utf-8")
        (self.repo / "notes").mkdir()
        (self.repo / "notes" / "alpha.txt").write_bytes(b"alpha one\nalpha two\nalpha three\n")
        (self.repo / "beta.txt").write_bytes(b"beta\n")
        # Tracked attribute only: it names a filter driver that no config defines.
        (self.repo / ".gitattributes").write_text("beta.txt filter=marker\n", encoding="utf-8")
        try:
            os.symlink("beta.txt", self.repo / "link.txt")
        except (OSError, NotImplementedError):
            pass
        git("add", "-A")
        git("-c", "user.name=local-unit", "-c", "user.email=local@example.invalid",
            "commit", "-qm", "baseline")
        self.base_sha = target.git(self.repo, "rev-parse", "HEAD")
        self.state = continuity.self_test_manifest()
        self.state.update({
            "project_id": "office612",
            "current_goal": "generate a bounded real model-authored source proposal",
            "scope_and_constraints": ["one turn", "no tools", "no external effect"],
            "active_external_effects": [],
            "code_baseline": {
                "repo": "nocturney/velvetos-core",
                "base_sha": self.base_sha,
                "branch": "role-a/isolated-test",
                "worktree_path": str(self.repo),
            },
        })
        self.state = continuity.seal(self.state)
        self.checkpoint = base / "checkpoint.json"
        self.checkpoint.write_text(json.dumps(self.state), encoding="utf-8")
        self.task = {
            "schema": target.SCHEMA, "issue_url": target.ISSUE,
            "task_id": "office612-contract-001", "repo_path": str(self.repo),
            "base_sha": self.base_sha, "branch": "role-a/isolated-test",
            "checkpoint_path": str(self.checkpoint),
            "prompt": "Give an exact Python source-code proposal with no executable tool call.",
            "timeout_seconds": 30,
        }
        self.task_path = base / "task.json"
        self.task_path.write_text(json.dumps(self.task), encoding="utf-8")
        self.receipt = base / "receipt.json"

    def fake_model(self, cmd, **kwargs):
        self.assertIn("--tools", cmd)
        self.assertEqual(cmd[cmd.index("--tools") + 1], "")
        self.assertIn("--strict-mcp-config", cmd)
        self.assertIn("--system-prompt", cmd)
        self.assertIn("Never request tools", cmd[cmd.index("--system-prompt") + 1])
        self.assertNotIn("--dangerously-skip-permissions", cmd)
        self.assertEqual(kwargs.get("cwd"), str(self.repo))
        return subprocess.CompletedProcess(
            cmd, 0,
            stdout=json.dumps({
                "result": self.model_body,
                "subtype": "success", "is_error": False, "num_turns": 1,
            }).encode("utf-8"),
            stderr=b"",
        )

    def success(self):
        with patch.object(target, "claude_cli", return_value=("fake-claude", "fake-version")):
            with patch.object(target.subprocess, "run", side_effect=self.proxy_subprocess):
                result = target.run(self.task_path, self.receipt)
        return result

    def proxy_subprocess(self, cmd, **kwargs):
        if cmd[0] == "fake-claude":
            return self.fake_model(cmd, **kwargs)
        return self.original_run(cmd, **kwargs)

    def draft(self, body, name):
        """A verified no-tools draft whose model output is exactly `body`."""
        self.model_body = body
        receipt = Path(self.temp.name) / (name + ".json")
        with patch.object(target, "claude_cli", return_value=("fake-claude", "fake-version")):
            with patch.object(target.subprocess, "run", side_effect=self.proxy_subprocess):
                target.run(self.task_path, receipt)
        return receipt, hashlib.sha256(body.encode("utf-8")).hexdigest()

    def real_diff(self, edits):
        """Real `git diff` of edits, then restore the clean baseline."""
        for name, data in edits.items():
            (self.repo / name).write_bytes(data)
        diff = subprocess.run(
            ["git", "-C", str(self.repo), "diff", "--no-color", "--no-ext-diff",
             "--src-prefix=a/", "--dst-prefix=b/"],
            check=True, capture_output=True).stdout.decode("utf-8")
        self.git("checkout", "-q", "--", *edits)
        return diff

    def assert_not_staged(self, receipt):
        self.assertEqual(target.git(self.repo, "status", "--porcelain=v1",
                                    "--untracked-files=all"), "")
        self.assertFalse(receipt.with_suffix(".staging").exists())
        self.assertFalse(receipt.with_suffix(".staged.json").exists())

    def test_real_artifact_contract_and_integrity(self):
        self.original_run = subprocess.run
        result = self.success()
        self.assertTrue(result["verified"])
        self.assertTrue(result["real_model_invoked"])
        self.assertFalse(result["source_edit"])
        self.assertFalse((self.receipt.with_suffix(".running")).exists())
        self.assertEqual(target.verify(self.task, self.receipt)["state"], "MODEL_DRAFT_ONLY")
        self.assertFalse(target.git(self.repo, "status", "--porcelain=v1"))
        with self.assertRaisesRegex(target.Refused, "EXISTING_ATTEMPT"):
            target.run(self.task_path, self.receipt)
        # A verified draft that is not a pure git diff is never staged.
        prose_sha = target.file_digest(self.receipt.with_suffix(".proposal.txt"))
        with self.assertRaisesRegex(target.Refused, "PATCH_FILE_HEADER_INVALID"):
            target.stage(self.task, self.receipt, prose_sha, ["entry.txt"])
        self.assert_not_staged(self.receipt)
        self.receipt.with_suffix(".proposal.txt").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(target.Refused, "ARTIFACT_OR_CONTINUITY_MISMATCH"):
            target.verify(self.task, self.receipt)
        with self.assertRaisesRegex(target.Refused, "ARTIFACT_OR_CONTINUITY_MISMATCH"):
            target.stage(self.task, self.receipt, prose_sha, ["entry.txt"])

        # Positive: operator-approved exact SHA + exact allowlist stages locally.
        diff = self.real_diff({
            "notes/alpha.txt": b"alpha one\nalpha 2\nalpha three\n",
            "beta.txt": b"beta\nstaged\n",
        })
        # A no-tools Claude proposal cannot know the SHA of its own future
        # postimage. Exercise the explicit 0000000 index placeholder.
        diff = "\n".join(
            line.split("..", 1)[0] + "..0000000 " + line.split(" ")[-1]
            if line.startswith("index ") else line
            for line in diff.splitlines()
        ) + "\n"
        receipt, sha = self.draft(diff, "stage-ok")
        staged = target.stage(self.task, receipt, sha, ["notes/alpha.txt", "beta.txt"])
        self.assertEqual(staged["state"], "SOURCE_STAGED_FOR_QA")
        self.assertEqual(staged["changed_paths"], ["beta.txt", "notes/alpha.txt"])
        for flag in ("committed", "pushed", "generated_code_executed",
                     "p0_admitted", "two_host_admitted"):
            self.assertIs(staged[flag], False)
        self.assertEqual(target.git(self.repo, "rev-parse", "HEAD"), self.base_sha)
        self.assertEqual(target.git(self.repo, "diff", "--name-only"),
                         "beta.txt\nnotes/alpha.txt")
        self.assertEqual(target.git(self.repo, "diff", "--cached", "--name-only"), "")
        self.assertEqual((self.repo / "beta.txt").read_bytes(), b"beta\nstaged\n")
        self.assertEqual((self.repo / "notes" / "alpha.txt").read_bytes(),
                         b"alpha one\nalpha 2\nalpha three\n")
        self.assertFalse(receipt.with_suffix(".staging").exists())
        record = json.loads(receipt.with_suffix(".staged.json").read_text(encoding="utf-8"))
        checksum = record.pop("stage_receipt_sha256")
        self.assertEqual(checksum, target.digest(record))
        self.assertEqual(checksum, staged["stage_receipt_sha256"])
        self.assertEqual(record["state"], "SOURCE_STAGED_FOR_QA")
        self.assertEqual(record["proposal_sha256"], sha)
        self.assertEqual(record["draft_receipt_sha256"], target.file_digest(receipt))
        self.assertEqual([f["path"] for f in record["files"]], ["beta.txt", "notes/alpha.txt"])
        self.assertEqual(record["files"][0]["after_sha256"],
                         target.file_digest(self.repo / "beta.txt"))
        self.assertIs(record["external_effects_authorized"], False)
        self.assertIs(record["committed"], False)
        with self.assertRaisesRegex(target.Refused, "EXISTING_STAGE_NO_REPLAY"):
            target.stage(self.task, receipt, sha, ["notes/alpha.txt", "beta.txt"])
        # The original draft verify contract is unchanged: a staged tree is not a draft.
        with self.assertRaisesRegex(target.Refused, "WORKTREE_NOT_CLEAN"):
            target.verify(self.task, receipt)

    def test_portable_real_stage_replay_on_foreign_checkout_and_tamper(self):
        # The producer's worktree is DIRTY after stage. A second checkout
        # must independently reconstruct the exact Git postimages without
        # rerunning the model, editing its checkout or trusting SHA claims.
        self.task["source_spans"] = [
            {"path": "notes/alpha.txt", "start_line": 1, "end_line": 3}
        ]
        self.task_path.write_text(json.dumps(self.task), encoding="utf-8")
        patch_text = self.real_diff({
            "notes/alpha.txt": b"alpha one\nalpha 2\nalpha three\n",
            "beta.txt": b"beta\nstaged\n",
        })
        patch_text = "\n".join(
            line.split("..", 1)[0] + "..0000000 " + line.split(" ")[-1]
            if line.startswith("index ") else line
            for line in patch_text.splitlines()
        ) + "\n"
        receipt, proposal_sha = self.draft(patch_text, "portable-verified")
        target.stage(self.task, receipt, proposal_sha,
                     ["notes/alpha.txt", "beta.txt"])
        foreign = Path(self.temp.name) / "qa-other-checkout"
        subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(self.repo),
                        str(foreign)], check=True, capture_output=True)
        source_state = target.git(self.repo, "status", "--porcelain=v1")
        verifier_state = target.git(foreign, "status", "--porcelain=v1")
        before_copy = Path(self.temp.name) / "checkpoint-copy.json"
        before_copy.write_bytes(self.checkpoint.read_bytes())
        with patch.object(target, "claude_cli",
                          side_effect=AssertionError("NO_MODEL_REINVOCATION")):
            result = target.verify_stage_portable(
                self.task_path, receipt, before_copy, foreign)
        self.assertEqual(result["status"], "PASS_PORTABLE_REPLAY_REAL_RECEIPT")
        self.assertEqual(result["files_verified"], 2)
        self.assertFalse(result["verifier_reran_model"])
        self.assertFalse(result["independent_code_quality_approved"])
        self.assertFalse(result["cross_host_lease_admitted"])
        self.assertEqual(target.git(foreign, "status", "--porcelain=v1"),
                         verifier_state)
        self.assertEqual(target.git(self.repo, "status", "--porcelain=v1"),
                         source_state)
        stage_path = receipt.with_suffix(".staged.json")
        original = stage_path.read_bytes()
        data = json.loads(original)
        data["files"][0]["after_sha256"] = "0" * 64
        data.pop("stage_receipt_sha256")
        data["stage_receipt_sha256"] = target.digest(data)
        stage_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(target.Refused, "PORTABLE_POSTIMAGE_MISMATCH"):
            target.verify_stage_portable(self.task_path, receipt,
                                         before_copy, foreign)
        stage_path.write_bytes(original)
        before_copy.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(target.Refused, "ARTIFACT_HASH_MISMATCH"):
            target.verify_stage_portable(self.task_path, receipt,
                                         before_copy, foreign)

    def portable_import_fixture(self):
        """Prepare an already staged source receipt and a fresh topic checkout."""
        self.task["source_spans"] = [
            {"path": "beta.txt", "start_line": 1, "end_line": 1},
        ]
        self.task["auto_stage_paths"] = ["beta.txt"]
        self.task_path.write_text(json.dumps(self.task), encoding="utf-8")
        patch_text = self.real_diff({"beta.txt": b"beta\nportable-import\n"})
        receipt, proposal_sha = self.draft(patch_text, "portable-import-origin")
        target.stage(self.task, receipt, proposal_sha, ["beta.txt"])
        foreign = Path(self.temp.name) / "foreign-topic"
        subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(self.repo),
                        str(foreign)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(foreign), "checkout", "-q", "-b",
                        "role-a/foreign-import"], check=True, capture_output=True)
        evidence_dir = Path(self.temp.name) / "import-evidence"
        evidence_dir.mkdir()
        return receipt, foreign, evidence_dir / "import.json"

    def test_portable_import_real_postimages_without_model_or_git_authority(self):
        receipt, foreign, result_path = self.portable_import_fixture()
        origin_before = self.repo.joinpath("beta.txt").read_bytes()
        source_receipt_hash = target.file_digest(receipt)
        with patch.object(target, "claude_cli",
                          side_effect=AssertionError("MODEL_MUST_NOT_RUN")):
            result = target.import_stage_portable(
                self.task_path, receipt, self.checkpoint, foreign, result_path)
        self.assertEqual(result["state"], "PORTABLE_SOURCE_STAGED_FOR_QA")
        self.assertFalse(result["shared_lease_admitted"])
        self.assertFalse(result["model_reinvoked"])
        self.assertEqual((foreign / "beta.txt").read_bytes(),
                         b"beta\nportable-import\n")
        self.assertEqual((self.repo / "beta.txt").read_bytes(), origin_before)
        self.assertEqual(source_receipt_hash, target.file_digest(receipt))
        self.assertEqual(target.git(foreign, "rev-parse", "HEAD"), self.base_sha)
        self.assertEqual(target.git(foreign, "diff", "--cached", "--name-only"), "")
        self.assertEqual(target.git(foreign, "diff", "--name-only"), "beta.txt")
        record = target.read_json(result_path)
        value = record.pop("import_receipt_sha256")
        self.assertEqual(value, target.digest(record))
        self.assertFalse(record["production_admitted"])
        self.assertFalse(record["distributed_fencing_proven"])
        self.assertFalse(result_path.with_suffix(".importing").exists())
        with self.assertRaisesRegex(target.Refused, "EXISTING_RECEIPT_NO_RETRY"):
            target.import_stage_portable(self.task_path, receipt,
                                         self.checkpoint, foreign, result_path)

    def test_portable_import_crash_reconciles_without_reapplying(self):
        receipt, foreign, result_path = self.portable_import_fixture()
        with patch.object(target, "validate_stage_postconditions",
                          side_effect=target.Refused("INJECTED_AFTER_APPLY")):
            with self.assertRaisesRegex(target.Refused, "INJECTED_AFTER_APPLY"):
                target.import_stage_portable(self.task_path, receipt,
                                             self.checkpoint, foreign, result_path)
        self.assertEqual((foreign / "beta.txt").read_bytes(),
                         b"beta\nportable-import\n")
        self.assertTrue(result_path.with_suffix(".importing").exists())
        with patch.object(target, "git_apply",
                          side_effect=AssertionError("NO_SECOND_APPLY")):
            result = target.import_stage_portable(
                self.task_path, receipt, self.checkpoint,
                foreign, result_path, recover=True)
        self.assertTrue(result["reconciled_after_crash"])
        self.assertFalse(result["model_reinvoked"])
        self.assertFalse(result_path.with_suffix(".importing").exists())
        self.assertFalse(target.read_json(result_path)["external_effects_authorized"])

    def test_portable_import_resealed_corruption_and_foreign_branch_denied(self):
        receipt, foreign, result_path = self.portable_import_fixture()
        stage_path = receipt.with_suffix(".staged.json")
        original = stage_path.read_bytes()
        record = target.read_json(stage_path)
        record["files"][0]["after_sha256"] = "0" * 64
        record.pop("stage_receipt_sha256")
        record["stage_receipt_sha256"] = target.digest(record)
        stage_path.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(target.Refused, "PORTABLE_POSTIMAGE_MISMATCH"):
            target.import_stage_portable(self.task_path, receipt,
                                         self.checkpoint, foreign, result_path)
        self.assertEqual(target.git(foreign, "status", "--porcelain=v1"), "")
        self.assertFalse(result_path.with_suffix(".importing").exists())
        stage_path.write_bytes(original)
        subprocess.run(["git", "-C", str(foreign), "checkout", "-q", "--detach"],
                       check=True, capture_output=True)
        with self.assertRaisesRegex(target.Refused, "PINNED_TOPIC_HEAD_REQUIRED"):
            target.import_stage_portable(self.task_path, receipt,
                                         self.checkpoint, foreign, result_path)
        self.assertEqual(target.git(foreign, "status", "--porcelain=v1"), "")

    def test_model_diff_without_terminal_lf_stages_with_original_sha(self):
        # Role B observed this exact failure mode with a real Claude Code
        # proposal: a valid, complete unified diff without its final LF.
        diff = self.real_diff({"beta.txt": b"beta\nstaged\n"})
        self.assertTrue(diff.endswith("\n"))
        raw = diff[:-1]
        receipt, sha = self.draft(raw, "model-no-terminal-lf")
        original_path = receipt.with_suffix(".proposal.txt")
        self.assertEqual(original_path.read_bytes(), raw.encode("utf-8"))
        self.assertEqual(target.file_digest(original_path), sha)
        self.assertEqual([f["path"] for f in target.parse_git_diff(raw)],
                         ["beta.txt"])
        # Missing a complete hunk line or smuggling CRLF still fails closed.
        with self.assertRaisesRegex(target.Refused, "PATCH_HUNK_TRUNCATED"):
            target.parse_git_diff(raw.rsplit("\n+", 1)[0])
        with self.assertRaisesRegex(target.Refused,
                                    "PATCH_ENCODING_OR_TERMINATION_INVALID"):
            target.parse_git_diff(raw.replace("\n", "\r\n"))
        staged = target.stage(self.task, receipt, sha, ["beta.txt"])
        self.assertEqual(staged["state"], "SOURCE_STAGED_FOR_QA")
        self.assertEqual((self.repo / "beta.txt").read_bytes(),
                         b"beta\nstaged\n")
        self.assertEqual(original_path.read_bytes(), raw.encode("utf-8"))
        data = json.loads(receipt.with_suffix(".staged.json").read_text(encoding="utf-8"))
        self.assertEqual(data["proposal_sha256"], sha)
        self.assertTrue(data["bounded_proof"]["proposal_bytes_preserved"])
        self.assertTrue(data["bounded_proof"]["terminal_lf_added_for_git_apply"])
        self.assertEqual(data["bounded_proof"]["git_apply_sha256"],
                         hashlib.sha256(diff.encode("utf-8")).hexdigest())
        self.assertFalse(data["generated_code_executed"])
        self.assertFalse(data["committed"])

    def test_run_stage_real_patch_single_model_call_and_no_external_effect(self):
        # #612 P0 bridge: a task-owned allowlist drives one model invocation
        # and one local source-stage attempt, without an operator-side second
        # command, code execution, commit, push, merge or lease promotion.
        self.task["source_spans"] = [
            {"path": "beta.txt", "start_line": 1, "end_line": 1}
        ]
        self.task["auto_stage_paths"] = ["beta.txt"]
        self.task_path.write_text(json.dumps(self.task), encoding="utf-8")
        self.model_body = self.real_diff({"beta.txt": b"beta\nauto-staged\n"})
        with patch.object(target, "claude_cli", return_value=("fake-claude", "fake-version")) as auth:
            with patch.object(target.subprocess, "run", side_effect=self.proxy_subprocess):
                with patch.object(self, "fake_model", wraps=self.fake_model) as model:
                    result = target.run_stage(self.task_path, self.receipt)
        self.assertEqual(auth.call_count, 1)
        self.assertEqual(model.call_count, 1)
        self.assertEqual(result["state"], "SOURCE_STAGED_FOR_QA")
        self.assertTrue(result["model_invoked_in_this_command"])
        self.assertTrue(result["task_allowlist_bound"])
        self.assertFalse(result["shared_lease_admitted"])
        self.assertFalse(result["committed"])
        self.assertFalse(result["pushed"])
        self.assertFalse(result["generated_code_executed"])
        self.assertEqual((self.repo / "beta.txt").read_bytes(), b"beta\nauto-staged\n")
        self.assertEqual(target.git(self.repo, "rev-parse", "HEAD"), self.base_sha)
        self.assertEqual(target.git(self.repo, "diff", "--cached", "--name-only"), "")
        self.assertFalse(self.receipt.with_suffix(".running").exists())
        self.assertFalse(self.receipt.with_suffix(".staging").exists())
        staged = target.read_json(self.receipt.with_suffix(".staged.json"))
        self.assertEqual(staged["task_sha256"], target.digest(self.task))
        self.assertEqual(staged["operator_supplied_allowlist"], ["beta.txt"])
        self.assertIs(staged["production"], False)
        # After staging the checkout is intentionally dirty. The clean-tree
        # precondition must reject a repeated attempt before calling Claude.
        with patch.object(target, "claude_cli", side_effect=AssertionError("NO_SECOND_MODEL_CALL")):
            with self.assertRaisesRegex(target.Refused, "WORKTREE_NOT_CLEAN"):
                target.run_stage(self.task_path, self.receipt)
        self.assertEqual((self.repo / "beta.txt").read_bytes(), b"beta\nauto-staged\n")

    def test_run_stage_prose_draft_is_retained(self):
        self.task["source_spans"] = [
            {"path": "beta.txt", "start_line": 1, "end_line": 1}
        ]
        self.task["auto_stage_paths"] = ["beta.txt"]
        self.task_path.write_text(json.dumps(self.task), encoding="utf-8")
        self.model_body = "Here is a prose answer, not a patch.\n"
        with patch.object(target, "claude_cli", return_value=("fake-claude", "fake-version")):
            with patch.object(target.subprocess, "run", side_effect=self.proxy_subprocess):
                with self.assertRaisesRegex(target.Refused, "PATCH_FILE_HEADER_INVALID"):
                    target.run_stage(self.task_path, self.receipt)
        self.assertTrue(self.receipt.is_file())
        self.assertTrue(self.receipt.with_suffix(".proposal.txt").is_file())
        self.assertEqual(target.verify(self.task, self.receipt)["state"], "MODEL_DRAFT_ONLY")
        self.assertEqual((self.repo / "beta.txt").read_bytes(), b"beta\n")
        self.assertEqual(target.git(self.repo, "status", "--porcelain=v1"), "")
        self.assertFalse(self.receipt.with_suffix(".staging").exists())
        self.assertFalse(self.receipt.with_suffix(".staged.json").exists())
        with patch.object(target, "claude_cli",
                          side_effect=AssertionError("NO_BLIND_MODEL_RETRY")):
            with self.assertRaisesRegex(target.Refused, "EXISTING_ATTEMPT_NO_RETRY"):
                target.run_stage(self.task_path, self.receipt)

    def test_run_stage_missing_or_unsafe_scope_refused_before_model(self):
        base = dict(self.task)
        source = [{"path": "beta.txt", "start_line": 1, "end_line": 1}]
        cases = [
            ({}, "AUTO_STAGE_SCOPE_REQUIRED"),
            ({"source_spans": source, "auto_stage_paths": []}, "AUTO_STAGE_PATH_COUNT"),
            ({"source_spans": source, "auto_stage_paths": ["beta.txt", "beta.txt"]},
             "AUTO_STAGE_PATH_DUPLICATE"),
            ({"source_spans": source, "auto_stage_paths": ["../beta.txt"]},
             "ALLOW_PATH_INVALID"),
            ({"source_spans": source, "auto_stage_paths": ["notes/alpha.txt"]},
             "AUTO_STAGE_PATH_NOT_CONTEXT_PINNED"),
            ({"auto_stage_paths": ["beta.txt"]}, "AUTO_STAGE_CONTEXT_INVALID"),
        ]
        for n, (extra, reason) in enumerate(cases):
            with self.subTest(index=n, reason=reason):
                self.task_path.write_text(json.dumps(dict(base, **extra)), encoding="utf-8")
                receipt = Path(self.temp.name) / ("blocked-%s.json" % n)
                with patch.object(target, "claude_cli",
                                  side_effect=AssertionError("MODEL_MUST_NOT_RUN")):
                    with self.assertRaisesRegex(target.Refused, reason):
                        target.run_stage(self.task_path, receipt)
                self.assertFalse(receipt.exists())
                self.assertFalse(receipt.with_suffix(".running").exists())
        self.assertEqual(target.git(self.repo, "status", "--porcelain=v1"), "")

    def test_run_stage_model_patch_outside_allowlist_durable_refusal(self):
        self.task["source_spans"] = [
            {"path": "beta.txt", "start_line": 1, "end_line": 1},
            {"path": "notes/alpha.txt", "start_line": 1, "end_line": 3},
        ]
        self.task["auto_stage_paths"] = ["beta.txt"]
        self.task_path.write_text(json.dumps(self.task), encoding="utf-8")
        self.model_body = self.real_diff({
            "notes/alpha.txt": b"alpha one\nalpha changed\nalpha three\n"
        })
        with patch.object(target, "claude_cli", return_value=("fake-claude", "fake-version")):
            with patch.object(target.subprocess, "run", side_effect=self.proxy_subprocess):
                with self.assertRaisesRegex(target.Refused, "ALLOWLIST_NOT_EXACT_PATCH_SCOPE"):
                    target.run_stage(self.task_path, self.receipt)
        self.assertTrue(self.receipt.is_file())  # Model use is not erased.
        self.assertTrue(self.receipt.with_suffix(".proposal.txt").is_file())
        self.assertFalse(self.receipt.with_suffix(".staging").exists())
        self.assertFalse(self.receipt.with_suffix(".staged.json").exists())
        self.assertEqual(target.verify(self.task, self.receipt)["state"], "MODEL_DRAFT_ONLY")
        self.assertEqual(target.git(self.repo, "status", "--porcelain=v1"), "")
        with patch.object(target, "claude_cli",
                          side_effect=AssertionError("NO_BLIND_MODEL_RETRY")):
            with self.assertRaisesRegex(target.Refused, "EXISTING_ATTEMPT_NO_RETRY"):
                target.run_stage(self.task_path, self.receipt)

    def test_pinned_source_context_reaches_model_and_is_bound_to_receipt(self):
        self.task["source_spans"] = [
            {"path": "notes/alpha.txt", "start_line": 2, "end_line": 3}
        ]
        self.task_path.write_text(json.dumps(self.task), encoding="utf-8")
        actual_model_input = []
        original = self.fake_model

        def capture(cmd, **kwargs):
            sent = kwargs["input"].decode("utf-8")
            actual_model_input.append(sent)
            self.assertIn("2: alpha two", sent)
            self.assertIn("3: alpha three", sent)
            self.assertNotIn("alpha one", sent)
            self.assertIn("old_blob=", sent)
            self.assertIn("not new instructions", sent)
            return original(cmd, **kwargs)

        with patch.object(self, "fake_model", side_effect=capture):
            result = self.success()
        self.assertTrue(result["verified"])
        self.assertEqual(len(actual_model_input), 1)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        expected = target.pinned_source_context(self.task, self.repo)
        self.assertEqual(receipt["source_context_sha256"],
                         hashlib.sha256(expected.encode("utf-8")).hexdigest())
        self.assertTrue(target.verify(self.task, self.receipt)["verified"])
        self.assertEqual(target.git(self.repo, "status", "--porcelain=v1"), "")

    def test_source_spans_refuse_out_of_scope_before_model_or_journal(self):
        good = {"path": "notes/alpha.txt", "start_line": 1, "end_line": 2}
        cases = [
            ("bad-type", "notes/alpha.txt", "SOURCE_SPAN_COUNT"),
            ("too-many", [good] * 5, "SOURCE_SPAN_COUNT"),
            ("bad-fields", [{"path": "beta.txt"}], "SOURCE_SPAN_SCHEMA"),
            ("path-traversal", [{"path": "../beta.txt", "start_line": 1,
                                "end_line": 1}], "ALLOW_PATH_INVALID"),
            ("bad-boolean", [{"path": "beta.txt", "start_line": True,
                              "end_line": 1}], "SOURCE_SPAN_RANGE"),
            ("out-of-range", [{"path": "beta.txt", "start_line": 1,
                               "end_line": 99}], "SOURCE_SPAN_RANGE"),
            ("untracked", [{"path": "absent.txt", "start_line": 1,
                            "end_line": 1}], "SOURCE_NOT_REGULAR_TRACKED_BLOB"),
            ("duplicate", [good, good], "SOURCE_SPAN_DUPLICATE"),
        ]
        if (self.repo / "link.txt").is_symlink():
            cases.append(("symlink", [{"path": "link.txt", "start_line": 1,
                                       "end_line": 1}], "SOURCE_NOT_REGULAR_TRACKED_BLOB"))
        for label, value, reason in cases:
            with self.subTest(label=label):
                candidate = dict(self.task, source_spans=value)
                with self.assertRaisesRegex(target.Refused, reason):
                    target.validate_task(candidate, self.receipt)
                self.assertFalse(self.receipt.with_suffix(".running").exists())
        with self.assertRaisesRegex(target.Refused, "TASK_SCHEMA_OR_SCOPE"):
            target.validate_task(dict(self.task, context_filenames=["beta.txt"]),
                                 self.receipt)

    def test_forbidden_provider_env_never_invokes_model(self):
        for name in target.FORBIDDEN_ENV:
            with self.subTest(env=name):
                with patch.dict(os.environ, {name: "present"}):
                    with self.assertRaisesRegex(target.Refused, "METERED_API"):
                        target.validate_task(self.task, self.receipt)

    def test_refuse_cross_host_or_dirty_branch(self):
        wrong = dict(self.task, branch="main")
        with self.assertRaisesRegex(target.Refused, "ISOLATED_TOPIC_BRANCH"):
            target.validate_task(wrong, self.receipt)
        receipt, sha = self.draft(self.real_diff({"beta.txt": b"beta\nstaged\n"}), "pre")
        for proposal_sha, allow, reason in (
            (sha.upper(), ["beta.txt"], "PROPOSAL_SHA256_FORMAT"),
            (sha[:40], ["beta.txt"], "PROPOSAL_SHA256_FORMAT"),
            ("0" * 64, ["beta.txt"], "PROPOSAL_SHA256_MISMATCH"),
            (sha, [], "ALLOW_PATH_COUNT"),
            (sha, ["beta.txt", "beta.txt"], "ALLOW_PATH_DUPLICATE"),
            (sha, [str(self.repo / "beta.txt")], "ALLOW_PATH_INVALID"),
            (sha, ["../beta.txt"], "ALLOW_PATH_INVALID"),
            (sha, [".git/config"], "ALLOW_PATH_INVALID"),
            (sha, ["notes//alpha.txt"], "ALLOW_PATH_INVALID"),
            (sha, ["notes/./alpha.txt"], "ALLOW_PATH_INVALID"),
            (sha, ["beta.txt\x00"], "ALLOW_PATH_INVALID"),
            (sha, ["notes/alpha.txt"], "ALLOWLIST_NOT_EXACT_PATCH_SCOPE"),
            (sha, ["beta.txt", "notes/alpha.txt"], "ALLOWLIST_NOT_EXACT_PATCH_SCOPE"),
        ):
            with self.subTest(reason=reason, allow=allow):
                with self.assertRaisesRegex(target.Refused, reason):
                    target.stage(self.task, receipt, proposal_sha, allow)
                self.assert_not_staged(receipt)
        with self.assertRaisesRegex(target.Refused, "BRANCH_MISMATCH"):
            target.stage(dict(self.task, branch="role-a/other-branch"), receipt, sha, ["beta.txt"])
        self.assert_not_staged(receipt)
        (self.repo / "entry.txt").write_text("dirty", encoding="utf-8")
        with self.assertRaisesRegex(target.Refused, "WORKTREE_NOT_CLEAN"):
            target.validate_task(self.task, self.receipt)
        with self.assertRaisesRegex(target.Refused, "WORKTREE_NOT_CLEAN"):
            target.stage(self.task, receipt, sha, ["beta.txt"])
        self.assertFalse(receipt.with_suffix(".staging").exists())
        self.assertEqual((self.repo / "beta.txt").read_bytes(), b"beta\n")

    def test_checkpoint_active_effect_refused(self):
        state = copy.deepcopy(self.state)
        state["active_external_effects"] = [{"intent_id": "unsafe"}]
        self.checkpoint.write_text(json.dumps(continuity.seal(state)), encoding="utf-8")
        with self.assertRaisesRegex(target.Refused, "ACTIVE_EXTERNAL_EFFECTS"):
            target.validate_task(self.task, self.receipt)

    def test_failed_model_is_unknown_no_retry(self):
        self.original_run = subprocess.run
        def failed(cmd, **kwargs):
            if cmd[0] == "fake-claude":
                return subprocess.CompletedProcess(cmd, 1, stdout=b"", stderr=b"failed")
            return self.original_run(cmd, **kwargs)
        with patch.object(target, "claude_cli", return_value=("fake-claude", "fake-version")):
            with patch.object(target.subprocess, "run", side_effect=failed):
                with self.assertRaisesRegex(target.Refused, "MODEL_CLI_FAILED"):
                    target.run(self.task_path, self.receipt)
        self.assertTrue((self.receipt.with_suffix(".running")).is_file())
        self.assertFalse(self.receipt.exists())
        with self.assertRaisesRegex(target.Refused, "EXISTING_ATTEMPT"):
            target.run(self.task_path, self.receipt)
        with self.assertRaisesRegex(target.Refused,
                                    "RUN_OUTCOME_UNKNOWN_OPERATOR_REVIEW_REQUIRED"):
            target.recover_run(self.task, self.receipt)
        self.assertTrue(self.receipt.with_suffix(".running").exists())

        # Staging with an uncertain effect outcome keeps its journal, writes no
        # stage receipt and is never blindly replayed.
        diff = self.real_diff({"beta.txt": b"beta\nstaged\n"})
        original_apply = target.git_apply
        receipt, sha = self.draft(diff, "apply-unknown")
        with patch.object(target, "git_apply",
                          side_effect=lambda repo, data, check: check and original_apply(
                              repo, data, check)):
            with self.assertRaisesRegex(target.Refused, "OUTCOME_UNKNOWN_JOURNAL_PRESERVED"):
                target.stage(self.task, receipt, sha, ["beta.txt"])
        self.assertTrue(receipt.with_suffix(".staging").is_file())
        self.assertFalse(receipt.with_suffix(".staged.json").exists())
        with self.assertRaisesRegex(target.Refused, "EXISTING_STAGE_NO_REPLAY"):
            target.stage(self.task, receipt, sha, ["beta.txt"])

        receipt, sha = self.draft(diff, "overreach")
        def overreach(repo, data, check):
            applied = original_apply(repo, data, check)
            if not check:
                (self.repo / "entry.txt").write_bytes(b"out of scope\n")
            return applied
        with patch.object(target, "git_apply", side_effect=overreach):
            with self.assertRaisesRegex(target.Refused,
                                        "POST_STAGE_SCOPE_MISMATCH_JOURNAL_PRESERVED"):
                target.stage(self.task, receipt, sha, ["beta.txt"])
        self.assertTrue(receipt.with_suffix(".staging").is_file())
        self.assertFalse(receipt.with_suffix(".staged.json").exists())
        self.assertEqual(target.git(self.repo, "rev-parse", "HEAD"), self.base_sha)
        self.git("checkout", "-q", "--", "entry.txt", "beta.txt")
        with self.assertRaisesRegex(target.Refused, "EXISTING_STAGE_NO_REPLAY"):
            target.stage(self.task, receipt, sha, ["beta.txt"])
        self.assertEqual((self.repo / "beta.txt").read_bytes(), b"beta\n")

    def test_interrupted_stage_recovery_is_exact_and_never_reapplies(self):
        # Simulate a process death AFTER git apply but BEFORE the stage receipt.
        # A placeholder post-SHA must not permit extra in-scope edits.
        diff = self.real_diff({"beta.txt": b"beta\nstaged\n"})
        diff = "\n".join(
            line.split("..", 1)[0] + "..0000000 " + line.split(" ")[-1]
            if line.startswith("index ") else line
            for line in diff.splitlines()
        ) + "\n"
        receipt, sha = self.draft(diff, "recover-after-apply")
        receipt_stage = receipt.with_suffix(".staged.json")
        journal = receipt.with_suffix(".staging")
        original_write = target.exclusive_write

        def crash_before_receipt(path, value):
            if Path(path).resolve() == receipt_stage.resolve():
                raise OSError("simulated process crash after patch apply")
            return original_write(path, value)

        with patch.object(target, "exclusive_write", side_effect=crash_before_receipt):
            with self.assertRaisesRegex(OSError, "simulated process crash"):
                target.stage(self.task, receipt, sha, ["beta.txt"])
        self.assertTrue(journal.is_file())
        self.assertFalse(receipt_stage.exists())
        self.assertEqual((self.repo / "beta.txt").read_bytes(), b"beta\nstaged\n")
        original_journal = journal.read_bytes()
        forged = json.loads(original_journal)
        forged["paths"] = ["entry.txt"]
        journal.write_text(json.dumps(forged), encoding="utf-8")
        with self.assertRaisesRegex(target.Refused, "RECOVERY_JOURNAL_MISMATCH"):
            target.recover_stage(self.task, receipt, sha, ["beta.txt"])
        journal.write_bytes(original_journal)

        # A malicious/concurrent extra edit inside the SAME allowed file must
        # NOT be mistaken for successful staging merely by path allowlisting.
        (self.repo / "beta.txt").write_bytes(b"beta\nstaged\nEXTRA\n")
        with self.assertRaisesRegex(target.Refused, "POST_STAGE_POSTIMAGE_MISMATCH"):
            target.recover_stage(self.task, receipt, sha, ["beta.txt"])
        self.assertTrue(journal.exists())
        self.assertFalse(receipt_stage.exists())
        self.assertEqual(journal.read_bytes(), original_journal)

        (self.repo / "beta.txt").write_bytes(b"beta\nstaged\n")
        recovered = target.recover_stage(self.task, receipt, sha, ["beta.txt"])
        self.assertEqual(recovered["state"], "SOURCE_STAGED_FOR_QA")
        self.assertFalse(recovered["committed"])
        self.assertFalse(recovered["p0_admitted"])
        self.assertFalse(journal.exists())
        stage_receipt = json.loads(receipt_stage.read_text(encoding="utf-8"))
        checksum = stage_receipt.pop("stage_receipt_sha256")
        self.assertEqual(checksum, target.digest(stage_receipt))
        self.assertIs(stage_receipt["bounded_proof"]["recovered_after_interrupted_stage"], True)
        self.assertEqual(stage_receipt["files"][0]["after_blob"],
                         target.git(self.repo, "hash-object", "--", "beta.txt"))
        with self.assertRaisesRegex(target.Refused, "EXISTING_STAGE_NO_REPLAY"):
            target.recover_stage(self.task, receipt, sha, ["beta.txt"])

        self.git("checkout", "-q", "--", "beta.txt")
        no_effect, sha2 = self.draft(diff, "recover-before-apply")
        original_apply = target.git_apply
        with patch.object(target, "git_apply",
                          side_effect=lambda repo, data, check: (
                              original_apply(repo, data, check) if check else False)):
            with self.assertRaisesRegex(target.Refused, "OUTCOME_UNKNOWN_JOURNAL_PRESERVED"):
                target.stage(self.task, no_effect, sha2, ["beta.txt"])
        with self.assertRaisesRegex(target.Refused, "POST_STAGE_SCOPE_MISMATCH"):
            target.recover_stage(self.task, no_effect, sha2, ["beta.txt"])
        self.assertTrue(no_effect.with_suffix(".staging").exists())
        self.assertFalse(no_effect.with_suffix(".staged.json").exists())
        self.assertEqual((self.repo / "beta.txt").read_bytes(), b"beta\n")

    def test_interrupted_completed_run_recovers_without_model_replay(self):
        # Crash after the sealed draft and verified checkpoint are on disk,
        # but before deleting the durable RUNNING journal.
        journal = self.receipt.resolve().with_suffix(".running")
        unlink_original = Path.unlink

        def crash_on_run_journal(path, *args, **kwargs):
            if path == journal:
                raise OSError("simulated crash at run journal unlink")
            return unlink_original(path, *args, **kwargs)

        with patch.object(target.Path, "unlink", new=crash_on_run_journal):
            with self.assertRaisesRegex(OSError, "simulated crash"):
                self.success()
        self.assertTrue(journal.is_file())
        self.assertTrue(self.receipt.is_file())
        receipt_before = self.receipt.read_bytes()
        proposal = self.receipt.with_suffix(".proposal.txt")
        proposal_before = proposal.read_bytes()
        journal_before = journal.read_bytes()
        self.assertTrue(target.verify(self.task, self.receipt)["verified"])
        self.assertEqual(target.git(self.repo, "status", "--porcelain=v1"), "")

        journal.write_bytes(b"forged journal")
        with self.assertRaisesRegex(target.Refused, "RUN_JOURNAL_MISMATCH"):
            target.recover_run(self.task, self.receipt)
        journal.write_bytes(journal_before)
        with self.assertRaisesRegex(target.Refused, "RUN_JOURNAL_MISMATCH"):
            target.recover_run(dict(self.task, prompt=self.task["prompt"] + "changed"),
                               self.receipt)
        proposal.write_bytes(b"corrupted")
        with self.assertRaisesRegex(target.Refused, "ARTIFACT_OR_CONTINUITY_MISMATCH"):
            target.recover_run(self.task, self.receipt)
        proposal.write_bytes(proposal_before)
        (self.repo / "entry.txt").write_text("unauthorized", encoding="utf-8")
        with self.assertRaisesRegex(target.Refused, "WORKTREE_NOT_CLEAN"):
            target.recover_run(self.task, self.receipt)
        self.git("checkout", "-q", "--", "entry.txt")
        self.assertEqual(journal.read_bytes(), journal_before)

        # Reconciliation never re-invokes Claude, rewrites a source file or
        # replaces the original SHA-bound receipt/proposal.
        with patch.object(target, "claude_cli",
                          side_effect=AssertionError("model replay forbidden")):
            result = target.recover_run(self.task, self.receipt)
        self.assertTrue(result["verified"])
        self.assertTrue(result["interrupted_run_reconciled"])
        self.assertIs(result["model_reinvoked"], False)
        self.assertIs(result["source_edit"], False)
        self.assertEqual(self.receipt.read_bytes(), receipt_before)
        self.assertEqual(proposal.read_bytes(), proposal_before)
        self.assertEqual(target.git(self.repo, "status", "--porcelain=v1"), "")
        self.assertFalse(journal.exists())
        with self.assertRaisesRegex(target.Refused, "NO_INTERRUPTED_RUN_JOURNAL"):
            target.recover_run(self.task, self.receipt)
        with self.assertRaisesRegex(target.Refused, "EXISTING_ATTEMPT"):
            target.run(self.task_path, self.receipt)

    def test_bad_model_turn_and_unexpected_code_write_refused(self):
        self.original_run = subprocess.run
        def bad(cmd, **kwargs):
            if cmd[0] == "fake-claude":
                (self.repo / "entry.txt").write_text("unapproved edit", encoding="utf-8")
                return self.fake_model(cmd, **kwargs)
            return self.original_run(cmd, **kwargs)
        with patch.object(target, "claude_cli", return_value=("fake-claude", "fake-version")):
            with patch.object(target.subprocess, "run", side_effect=bad):
                with self.assertRaisesRegex(target.Refused, "UNEXPECTED_MODEL_WORKTREE_MUTATION"):
                    target.run(self.task_path, self.receipt)
        self.assertFalse(self.receipt.exists())
        self.assertTrue(self.receipt.with_suffix(".running").exists())
        self.git("checkout", "-q", "--", "entry.txt")

        # Verified-but-unsafe model diffs are refused before any worktree write.
        good = self.real_diff({"beta.txt": b"beta\nstaged\n"})
        old, new = good.split("\nindex ", 1)[1].split(" ", 1)[0].split("..")
        two = self.real_diff({"beta.txt": b"beta\nstaged\n",
                              "notes/alpha.txt": b"alpha one\nalpha 2\nalpha three\n"})
        hunk = "--- a/beta.txt\n+++ b/beta.txt\n@@ -1 +1,2 @@\n beta\n+staged\n"
        cases = [
            ("   \n", ["beta.txt"], "EMPTY_DIFF"),
            ("Here is the patch:\n" + good, ["beta.txt"], "PATCH_FILE_HEADER_INVALID"),
            (good + "+smuggled\n", ["beta.txt"], "PATCH_FILE_HEADER_INVALID"),
            (good.replace(" beta\n+staged\n", " beta\n"), ["beta.txt"],
             "PATCH_HUNK_TRUNCATED"),
            (good.replace("@@ -1 +1,2 @@\n beta\n+staged\n", "@@ -1 +1 @@\n beta\n"),
             ["beta.txt"], "PATCH_FILE_WITHOUT_CHANGES"),
            (good.replace("@@ -1 +1,2 @@", "@@ -1,0 +1,2 @@"), ["beta.txt"],
             "PATCH_HUNK_COUNT_MISMATCH"),
            (two, ["beta.txt"], "ALLOWLIST_NOT_EXACT_PATCH_SCOPE"),
            (good.replace("index " + old, "index 0000000"), ["beta.txt"],
             "PATCH_INDEX_BASE_MISMATCH"),
            (good.replace(" 100644\n", " 100755\n"), ["beta.txt"], "PATCH_MODE_MISMATCH"),
            (good.replace("\nindex ", "\nold mode 100644\nnew mode 100755\nindex ", 1),
             ["beta.txt"], "PATCH_INDEX_OR_MODE_HEADER_INVALID"),
            ("diff --git a/new.txt b/new.txt\nnew file mode 100644\nindex 0000000.." + new +
             "\n--- /dev/null\n+++ b/new.txt\n@@ -0,0 +1 @@\n+new\n", ["new.txt"],
             "PATCH_INDEX_OR_MODE_HEADER_INVALID"),
            ("diff --git a/beta.txt b/beta.txt\ndeleted file mode 100644\nindex " + old +
             "..0000000\n--- a/beta.txt\n+++ /dev/null\n@@ -1 +0,0 @@\n-beta\n",
             ["beta.txt"], "PATCH_INDEX_OR_MODE_HEADER_INVALID"),
            ("diff --git a/beta.txt b/gamma.txt\nsimilarity index 100%\n"
             "rename from beta.txt\nrename to gamma.txt\n", ["beta.txt"],
             "PATCH_FILE_HEADER_INVALID"),
            ("diff --git a/beta.txt b/beta.txt\nindex " + old + "..1234567 100644\n"
             "GIT binary patch\nliteral 3\nKcmZ?wa{vGU\n\n", ["beta.txt"],
             "BINARY_PATCH_DENIED"),
            (good.replace("beta.txt", "../beta.txt"), ["beta.txt"], "PATCH_PATH_INVALID"),
            (good.replace("beta.txt", ".git/config"), ["beta.txt"], "PATCH_PATH_INVALID"),
            (good.replace("a/beta.txt", "a//tmp/beta.txt").replace(
                "b/beta.txt", "b//tmp/beta.txt"), ["beta.txt"], "PATCH_PATH_INVALID"),
            (good + good, ["beta.txt"], "PATCH_DUPLICATE_OR_TOO_MANY_FILES"),
            ("diff --git a/beta.txt b/beta.txt\nindex " + old + ".." + new + " 100644\n" +
             hunk.replace(" beta\n", " BETA\n"), ["beta.txt"], "GIT_APPLY_CHECK_FAILED"),
        ]
        if (self.repo / "link.txt").is_symlink():
            cases.append((
                "diff --git a/link.txt b/link.txt\nindex 1234567..7654321 100644\n"
                "--- a/link.txt\n+++ b/link.txt\n@@ -1 +1 @@\n-beta.txt\n+entry.txt\n",
                ["link.txt"], "PATH_NOT_TRACKED_REGULAR_FILE"))
        for number, (body, allow, reason) in enumerate(cases):
            with self.subTest(reason=reason, number=number):
                receipt, sha = self.draft(body, "unsafe-%02d" % number)
                with self.assertRaisesRegex(target.Refused, reason):
                    target.stage(self.task, receipt, sha, allow)
                self.assert_not_staged(receipt)
                self.assertEqual((self.repo / "beta.txt").read_bytes(), b"beta\n")

    def test_repo_filter_config_never_runs_in_preflight_stage_or_recovery(self):
        # The tracked .gitattributes names filter=marker; only config can define
        # the driver. A harmless clean filter that appends a marker would have run
        # during stage postconditions (`git diff`) before the guard existed.
        diff = self.real_diff({"beta.txt": b"beta\nstaged\n"})
        receipt, sha = self.draft(diff, "filter-guard")
        marker = Path(self.temp.name) / "filter-marker.txt"
        script = Path(self.temp.name) / "marker-filter.sh"
        script.write_text(f"#!/bin/sh\necho ran >> '{marker}'\ncat\n", encoding="utf-8")
        script.chmod(0o755)
        self.git("config", "filter.marker.clean", str(script))
        refusal = "EXECUTABLE_GIT_CONFIG_REFUSED"
        journal = receipt.with_suffix(".staging")
        with self.assertRaisesRegex(target.Refused, refusal):
            target.validate_task(self.task, receipt)
        self.assertFalse(marker.exists())
        with self.assertRaisesRegex(target.Refused, refusal):
            target.stage(self.task, receipt, sha, ["beta.txt"])
        self.assertFalse(marker.exists())
        self.assertFalse(journal.exists())
        self.assertFalse(receipt.with_suffix(".staged.json").exists())
        self.assertEqual((self.repo / "beta.txt").read_bytes(), b"beta\n")
        journal.write_bytes(target.canonical({
            "task": target.digest(self.task), "proposal_sha256": sha,
            "paths": ["beta.txt"], "state": "STAGING_NO_BLIND_RETRY"}))
        journal_before = journal.read_bytes()
        with self.assertRaisesRegex(target.Refused, refusal):
            target.recover_stage(self.task, receipt, sha, ["beta.txt"])
        self.assertFalse(marker.exists())
        self.assertEqual(journal.read_bytes(), journal_before)
        self.assertEqual((self.repo / "beta.txt").read_bytes(), b"beta\n")

        # Positive: with repo config removed, an inherited GIT_CONFIG_* driver is
        # stripped from the environment, so the same stage succeeds without running it.
        journal.unlink()
        self.git("config", "--unset", "filter.marker.clean")
        injected = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "filter.marker.clean",
                    "GIT_CONFIG_VALUE_0": str(script)}
        with patch.dict(os.environ, injected):
            staged = target.stage(self.task, receipt, sha, ["beta.txt"])
        self.assertEqual(staged["state"], "SOURCE_STAGED_FOR_QA")
        self.assertEqual(staged["changed_paths"], ["beta.txt"])
        self.assertFalse(marker.exists())
        self.assertEqual((self.repo / "beta.txt").read_bytes(), b"beta\nstaged\n")

    def test_windows_autocrlf_system_config_clean_checkout_matches_git(self):
        # Git for Windows: system core.autocrlf=true, LF blobs, CRLF worktree and
        # a tracked .gitattributes. Only a process-local GIT_CONFIG_SYSTEM is used.
        system = Path(self.temp.name) / "windows-system-gitconfig"
        system.write_text("[core]\n\tautocrlf = true\n", encoding="utf-8")
        repo = Path(self.temp.name) / "crlf-repo"
        repo.mkdir()
        pinned = {"GIT_CONFIG_SYSTEM": str(system), "GIT_CONFIG_NOSYSTEM": "0",
                  "GIT_CONFIG_GLOBAL": os.devnull}
        with patch.dict(os.environ, pinned):
            def plain(*args):
                return subprocess.run(["git", "-C", str(repo), *args],
                                      check=True, capture_output=True).stdout
            plain("init", "-q")
            (repo / ".gitattributes").write_bytes(b"beta.txt filter=marker\r\n")
            (repo / "entry.txt").write_bytes(b"baseline\r\nsecond\r\n")
            (repo / "beta.txt").write_bytes(b"beta\r\n")
            plain("add", "-A")
            plain("-c", "user.name=local-unit", "-c", "user.email=local@example.invalid",
                  "commit", "-qm", "crlf-baseline")
            self.assertEqual(plain("show", "HEAD:entry.txt"), b"baseline\nsecond\n")
            self.assertEqual(plain("status", "--porcelain=v1", "--untracked-files=all"), b"")

            self.assertEqual(target.eol_git_args(repo), ["-c", "core.autocrlf=true"])
            self.assertEqual(target.git(repo, "status", "--porcelain=v1",
                                        "--untracked-files=all"), "")
            base = target.git(repo, "rev-parse", "HEAD")
            context = target.pinned_source_context(
                {"base_sha": base, "source_spans": [
                    {"path": "entry.txt", "start_line": 1, "end_line": 2}]}, repo)
            self.assertIn("1: baseline", context)
            self.assertIn("2: second", context)

            # Real edits are still seen: the EOL fix does not weaken dirty detection.
            # Raw run_git keeps porcelain's leading status-column space (target.git strips).
            (repo / "entry.txt").write_bytes(b"changed\r\nsecond\r\n")
            raw = target.run_git(repo, ["status", "--porcelain=v1"]).stdout
            self.assertIn(b" M entry.txt", raw)

    def test_system_config_executables_never_run_and_eol_values_are_exact(self):
        marker = Path(self.temp.name) / "system-config-marker.txt"
        script = Path(self.temp.name) / "system-config-marker.sh"
        script.write_text(f"#!/bin/sh\necho ran >> '{marker}'\ncat\n", encoding="utf-8")
        script.chmod(0o755)
        system = Path(self.temp.name) / "hostile-system-gitconfig"
        # A real change to beta.txt forces the tracked filter=marker to be hashed.
        (self.repo / "beta.txt").write_bytes(b"beta\nchanged\n")
        quoted = config_path(script)
        hostile = (f"[core]\n\tautocrlf = true\n\tfsmonitor = {quoted}\n"
                   f"[filter \"marker\"]\n\tclean = {quoted}\n\tsmudge = cat\n")
        pinned = {"GIT_CONFIG_SYSTEM": str(system), "GIT_CONFIG_NOSYSTEM": "0",
                  "GIT_CONFIG_GLOBAL": os.devnull}
        with patch.dict(os.environ, pinned):
            system.write_text(hostile, encoding="utf-8")
            status = target.git(self.repo, "status", "--porcelain=v1", "--untracked-files=all")
            self.assertIn("beta.txt", status)
            self.assertFalse(marker.exists())

            # Non-EOL or malformed EOL values refuse before any git status runs.
            for body in ("[core]\n\tautocrlf = !" + config_path(script) + "\n",
                         "[core]\n\tautocrlf\n",
                         "[core]\n\teol = !" + config_path(script) + "\n"):
                with self.subTest(body=body):
                    system.write_text(body, encoding="utf-8")
                    with self.assertRaisesRegex(target.Refused, "EOL_GIT_CONFIG_UNSUPPORTED"):
                        target.git(self.repo, "status", "--porcelain=v1")
                    self.assertFalse(marker.exists())

            # Inherited GIT_CONFIG_COUNT drivers are stripped, never forwarded.
            system.write_text("[core]\n\tautocrlf = true\n", encoding="utf-8")
            injected = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "filter.marker.clean",
                        "GIT_CONFIG_VALUE_0": str(script)}
            with patch.dict(os.environ, injected):
                status = target.git(self.repo, "status", "--porcelain=v1")
            self.assertIn("beta.txt", status)
            self.assertFalse(marker.exists())

    def test_eol_discovery_honors_inherited_no_system_switch(self):
        # Process-local only: a temporary system file says autocrlf=true. An inherited
        # GIT_CONFIG_NOSYSTEM=1 must suppress it in discovery, as ordinary Git does;
        # without that switch the same file must be honored.
        system = Path(self.temp.name) / "eol-system-gitconfig"
        system.write_text("[core]\n\tautocrlf = true\n", encoding="utf-8")
        base = {"GIT_CONFIG_SYSTEM": str(system), "GIT_CONFIG_GLOBAL": os.devnull}
        with patch.dict(os.environ, {**base, "GIT_CONFIG_NOSYSTEM": "1"}):
            self.assertEqual(target.eol_git_args(self.repo), [])
            self.assertEqual(target.git(self.repo, "status", "--porcelain=v1"), "")
        with patch.dict(os.environ, base):
            os.environ.pop("GIT_CONFIG_NOSYSTEM", None)
            self.assertEqual(target.eol_git_args(self.repo), ["-c", "core.autocrlf=true"])
        # Injected command config is still stripped even when NOSYSTEM is inherited.
        injected = {**base, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "core.autocrlf", "GIT_CONFIG_VALUE_0": "input"}
        with patch.dict(os.environ, injected):
            self.assertEqual(target.eol_git_args(self.repo), [])


if __name__ == "__main__":
    unittest.main()
