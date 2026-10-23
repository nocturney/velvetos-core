#!/usr/bin/env python3
"""Negative and positive contract tests; the live Claude proof is separate."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import vf_office_v2_continuity as continuity
import vf_office_v2_p0_subscription_artifact as target


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
        (self.repo / "entry.txt").write_text("baseline\n", encoding="utf-8")
        git("add", "entry.txt")
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
        self.assertNotIn("--dangerously-skip-permissions", cmd)
        self.assertEqual(kwargs.get("cwd"), str(self.repo))
        return subprocess.CompletedProcess(
            cmd, 0,
            stdout=json.dumps({
                "result": "def bounded_add(a, b):\n    return a + b\n",
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
        self.receipt.with_suffix(".proposal.txt").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(target.Refused, "ARTIFACT_OR_CONTINUITY_MISMATCH"):
            target.verify(self.task, self.receipt)

    def test_api_key_env_never_invokes_model(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "present"}):
            with self.assertRaisesRegex(target.Refused, "METERED_API"):
                target.validate_task(self.task, self.receipt)

    def test_refuse_cross_host_or_dirty_branch(self):
        wrong = dict(self.task, branch="main")
        with self.assertRaisesRegex(target.Refused, "ISOLATED_TOPIC_BRANCH"):
            target.validate_task(wrong, self.receipt)
        (self.repo / "entry.txt").write_text("dirty", encoding="utf-8")
        with self.assertRaisesRegex(target.Refused, "WORKTREE_NOT_CLEAN"):
            target.validate_task(self.task, self.receipt)

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


if __name__ == "__main__":
    unittest.main()
