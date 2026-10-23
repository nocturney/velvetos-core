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


if __name__ == "__main__":
    unittest.main()
