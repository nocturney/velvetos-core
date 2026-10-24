#!/usr/bin/env python3
"""#612 local source-import -> QA-only Git commit: real Git effects, never model/PR."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_vf_office_v2_p0_subscription_artifact as existing
import vf_office_v2_p0_subscription_artifact as stage
import vf_office_v2_p0_subscription_local_commit as local


class LocalCommitContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture = existing.SubscriptionArtifactTests(
            methodName="test_portable_import_real_postimages_without_model_or_git_authority")
        # A throwaway Git fixture must not inherit the host default EOL policy.
        # Windows core.autocrlf=true otherwise changes checkout byte postimages
        # before the source-import contract can be exercised.
        with patch.dict(os.environ, {
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull}):
            self.fixture.setUp()
            self.addCleanup(self.fixture.doCleanups)
            self.origin, self.repo, self.import_receipt = (
                self.fixture.portable_import_fixture())
            stage.import_stage_portable(
                self.fixture.task_path, self.origin, self.fixture.checkpoint,
                self.repo, self.import_receipt)
        commit_dir = Path(self.fixture.temp.name) / "commit-evidence"
        commit_dir.mkdir()
        self.output = commit_dir / "commit.json"

    def run_commit(self, recover=False):
        with patch.object(stage, "claude_cli",
                          side_effect=AssertionError("NO_MODEL_REINVOCATION")):
            return local.commit(
                self.fixture.task_path, self.origin, self.fixture.checkpoint,
                self.import_receipt, self.repo, self.output, recover=recover)

    def test_local_commit_exact_real_git_tree_and_no_false_qa(self):
        result = self.run_commit()
        self.assertEqual(result["result"],
                         "LOCAL_COMMITTED_FOR_INDEPENDENT_QA_ONLY")
        self.assertNotEqual(result["head_sha"], self.fixture.base_sha)
        self.assertEqual(local.git(self.repo, "rev-parse", "HEAD^").decode(),
                         self.fixture.base_sha)
        self.assertEqual(local.git(self.repo, "status", "--porcelain=v1"), b"")
        self.assertEqual(local.git(self.repo, "diff-tree", "--no-commit-id",
                                   "--name-only", "-r", "HEAD"), b"beta.txt")
        self.assertEqual(self.repo.joinpath("beta.txt").read_bytes(),
                         b"beta\nportable-import\n")
        record = stage.read_json(self.output)
        digest = record.pop("local_commit_receipt_sha256")
        self.assertEqual(digest, stage.digest(record))
        for field in ("independent_quality_approved", "ci_passed", "pushed",
                      "pr_opened", "merged", "distributed_fencing_proven",
                      "production_admitted", "model_reinvoked"):
            self.assertIs(record[field], False)
        self.assertFalse(self.output.with_suffix(".committing").exists())
        with self.assertRaisesRegex(local.Refused,
                                    "EXISTING_RECEIPT_NO_RETRY"):
            self.run_commit()

    def test_unexpected_local_file_blocks_without_index_or_journal(self):
        self.repo.joinpath("entry.txt").write_text("unauthorized\n", encoding="utf-8")
        with self.assertRaisesRegex(local.Refused,
                                    "UNEXPECTED_WORKTREE_CHANGE"):
            self.run_commit()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.output.with_suffix(".committing").exists())
        self.assertEqual(local.git(self.repo, "diff", "--cached", "--name-only"), b"")
        self.assertEqual(local.git(self.repo, "rev-parse", "HEAD").decode(),
                         self.fixture.base_sha)

    def test_resealed_import_receipt_and_postimage_tamper_refused(self):
        record = stage.read_json(self.import_receipt)
        record["files"][0]["after_sha256"] = "0" * 64
        record.pop("import_receipt_sha256")
        record["import_receipt_sha256"] = stage.digest(record)
        self.import_receipt.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(local.Refused, "POSTIMAGE_MISMATCH"):
            self.run_commit()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.output.with_suffix(".committing").exists())

    def test_index_retains_exact_crlf_bytes_even_with_local_autocrlf_true(self):
        # The receipt binds raw file bytes, not host-dependent EOL filters.
        subprocess.run(["git", "-C", str(self.repo), "config", "--local",
                        "core.autocrlf", "true"], check=True, capture_output=True)
        raw = bytes.fromhex("66697273740d0a7365636f6e640d0a")
        # Not *.txt: the fixture's tracked `text eol=lf` rule would normalize it.
        target = self.repo / "exact-crlf.bin"
        target.write_bytes(raw)
        local.git(self.repo, "add", "--", target.name)
        self.assertEqual(local.git(self.repo, "show", ":" + target.name,
                                   raw=True), raw)
        self.assertEqual(target.read_bytes(), raw)

    def test_attribute_eol_rewrite_refused_before_git_write(self):
        # Tracked `*.txt text eol=lf` makes `git add` store LF for CRLF bytes; the
        # receipt binds the raw CRLF postimage, so refuse before any index write.
        raw = b"beta\r\nportable-import\r\n"
        self.repo.joinpath("beta.txt").write_bytes(raw)
        record = stage.read_json(self.import_receipt)
        row = record["files"][0]
        row["after_sha256"] = hashlib.sha256(raw).hexdigest()
        row["after_blob"] = local.git(self.repo, "hash-object", "--stdin",
                                      input_bytes=raw).decode()
        record.pop("import_receipt_sha256")
        record["import_receipt_sha256"] = stage.digest(record)
        self.import_receipt.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(local.Refused,
                                    "ATTRIBUTE_FILTER_ALTERS_POSTIMAGE"):
            self.run_commit()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.output.with_suffix(".committing").exists())
        self.assertEqual(local.git(self.repo, "diff", "--cached", "--name-only"), b"")
        self.assertEqual(local.git(self.repo, "rev-parse", "HEAD").decode(),
                         self.fixture.base_sha)

    def test_crash_after_commit_reconciles_without_recommit(self):
        original = local.check_committed
        with patch.object(local, "check_committed",
                          side_effect=local.Refused("INJECTED_AFTER_COMMIT")):
            with self.assertRaisesRegex(local.Refused, "INJECTED_AFTER_COMMIT"):
                self.run_commit()
        self.assertTrue(self.output.with_suffix(".committing").exists())
        head = local.git(self.repo, "rev-parse", "HEAD")
        with patch.object(local, "git", wraps=local.git) as git_monitor:
            result = self.run_commit(recover=True)
        self.assertEqual(result["head_sha"].encode(), head)
        self.assertTrue(result["reconciled_after_crash"])
        self.assertEqual(local.git(self.repo, "rev-parse", "HEAD"), head)
        self.assertFalse(self.output.with_suffix(".committing").exists())
        self.assertFalse(any("commit" in call.args[1:] for call in
                             git_monitor.call_args_list))
        self.assertIs(original, local.check_committed)

    def assert_malicious_clean_filter_never_runs(self, configure):
        commit_dir = self.output.parent
        marker = commit_dir / "FILTER_RAN"
        script = commit_dir / "evil_filter.py"
        script.write_text(
            "import sys\n"
            "with open(%r, 'w') as f:\n"
            "    f.write('ran')\n"
            "sys.stdout.buffer.write(sys.stdin.buffer.read())\n" % str(marker),
            encoding="utf-8")
        configure('"%s" "%s"' % (sys.executable, script))
        # .git/info/attributes is untracked metadata: without the new guard,
        # preflight reaches git diff and actually executes this clean filter.
        info_attrs = self.repo / ".git" / "info" / "attributes"
        info_attrs.write_text("beta.txt filter=evil\n", encoding="utf-8")
        with self.assertRaisesRegex(local.Refused, "COMMAND_CONFIG_REFUSED"):
            self.run_commit()
        self.assertFalse(marker.exists())
        self.assertFalse(self.output.exists())
        self.assertFalse(self.output.with_suffix(".committing").exists())
        self.assertEqual(local.git(self.repo, "rev-parse", "HEAD").decode(),
                         self.fixture.base_sha)

    def test_repo_local_malicious_clean_filter_never_runs(self):
        self.assert_malicious_clean_filter_never_runs(
            lambda cmd: local.git(self.repo, "config", "--local",
                                  "filter.evil.clean", cmd))

    def test_included_malicious_clean_filter_never_runs(self):
        def configure(cmd):
            included = self.output.parent / "included.cfg"
            local.git(self.repo, "config", "--file", str(included),
                      "filter.evil.clean", cmd)
            local.git(self.repo, "config", "--local", "include.path",
                      str(included))
        self.assert_malicious_clean_filter_never_runs(configure)

    def test_recovery_before_commit_does_not_blindly_retry(self):
        original_git = local.git
        def refuse_commit(root, *args, **kwargs):
            if "add" in args:
                raise local.Refused("INJECTED_BEFORE_INDEX_WRITE")
            return original_git(root, *args, **kwargs)
        with patch.object(local, "git", side_effect=refuse_commit):
            with self.assertRaisesRegex(local.Refused, "INJECTED_BEFORE_INDEX"):
                self.run_commit()
        self.assertTrue(self.output.with_suffix(".committing").exists())
        with self.assertRaisesRegex(local.Refused,
                                    "LOCAL_COMMIT_HEAD_NOT_ADVANCED"):
            self.run_commit(recover=True)
        self.assertEqual(local.git(self.repo, "rev-parse", "HEAD").decode(),
                         self.fixture.base_sha)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
