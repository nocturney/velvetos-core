#!/usr/bin/env python3
"""Credential-free CP085 remote GitHub READ-ONLY reconciliation controls."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

import vf_office_v2_604_cp085_public_git_readback as r


REF = "refs/heads/lab/office604-cp084-nonroot-sink-recovery-20261018"
EXPECTED = "85de7e7e42c8e427204a0f32143193d3377597fb"
CANDIDATE = "313767104158023c365bce9b012588490a56e7ce"
CONFLICT = "f" * 40


class ReadbackTests(unittest.TestCase):
    def setUp(self):
        self.intent = r.Intent(task="cp085-synthetic", ref=REF,
                               expected=EXPECTED, candidate=CANDIDATE)

    def require_posix_permissions(self):
        """Directory mode bits are a POSIX privacy gate. Elsewhere they are not."""
        if os.name != "posix":
            print("SKIP_NON_POSIX", flush=True)
            self.skipTest("SKIP_NON_POSIX")

    def _mode_dir(self, root: Path, name: str, mode: int) -> Path:
        directory = root / name
        directory.mkdir(mode=0o700)
        directory.chmod(mode)
        self.assertEqual(directory.stat().st_mode & 0o777, mode)
        return directory

    def _receipt_dir_result(self, module, directory: Path, value: dict) -> str:
        try:
            module.write_private_receipt(directory / "proof.json", value)
        except module.Refuse as exc:
            return str(exc)
        return "ACCEPTED"

    def test_01_candidate_seen_means_review_not_release(self):
        v = r.classify(self.intent, CANDIDATE)
        self.assertEqual(v["classification"], "REMOTE_ADVANCED_REVIEW_REQUIRED")
        self.assertEqual(v["journal_state"], "UNKNOWN_EFFECT_RECONCILE")
        self.assertIs(v["frozen"], True)
        self.assertIs(v["retry_allowed"], False)
        self.assertIs(v["release_allowed"], False)
        self.assertIs(v["effect_proven"], False)

    def test_02_expected_seen_never_causes_blind_retry(self):
        v = r.classify(self.intent, EXPECTED)
        self.assertEqual(v["classification"], "REMOTE_UNCHANGED_REVIEW_REQUIRED")
        self.assertIs(v["frozen"], True)
        self.assertIs(v["retry_allowed"], False)

    def test_03_conflict_stays_unknown_frozen(self):
        v = r.classify(self.intent, CONFLICT)
        self.assertEqual(v["classification"], "REMOTE_CONFLICT_REVIEW_REQUIRED")
        self.assertIs(v["frozen"], True)

    def test_04_no_observation_still_requires_review(self):
        v = r.classify(self.intent, None)
        self.assertEqual(v["classification"], "READBACK_UNAVAILABLE_REVIEW_REQUIRED")
        self.assertIs(v["release_allowed"], False)

    def test_05_never_trust_caller_authentication_flag(self):
        with self.assertRaises(r.Refuse):
            r.classify(self.intent, CANDIDATE, authenticated_writer_evidence=True)

    def test_06_invalid_or_mixed_case_observation_fails(self):
        for value in (True, False, 1, [], {}, "abc", "a" * 39, "A" * 40,
                      CANDIDATE + "\n", ""):
            with self.subTest(value=value), self.assertRaises(r.Refuse):
                r.classify(self.intent, value)

    def test_07_ref_validation_drops_protected_and_injection(self):
        for ref in ("refs/heads/main", "refs/heads/lab/../main",
                    "refs/heads/lab/a//b", "refs/heads/lab/any\n--upload-pack",
                    "refs/tags/test", "refs/heads/lab/UPPER",
                    "refs/heads/lab/a/", "refs/heads/lab/a..b",
                    "refs/heads/lab/-"):
            with self.subTest(ref=ref), self.assertRaises(r.Refuse):
                r.Intent(task="test", ref=ref,
                         expected=EXPECTED, candidate=CANDIDATE).validate()

    def test_08_scope_cannot_change_repo(self):
        with self.assertRaises(r.Refuse):
            r.Intent(task="x", ref=REF, expected=EXPECTED,
                     candidate=CANDIDATE, repository="other/repo").validate()

    def test_09_expected_candidate_must_differ(self):
        with self.assertRaises(r.Refuse):
            r.Intent(task="x", ref=REF, expected=EXPECTED,
                     candidate=EXPECTED).validate()

    def test_10_task_identity_must_be_exact(self):
        for task in ("", "bad task", "../owner", "A", 123, "x" * 65):
            with self.subTest(task=task), self.assertRaises(r.Refuse):
                r.Intent(task=task, ref=REF, expected=EXPECTED,
                         candidate=CANDIDATE).validate()

    def test_11_accept_one_exact_native_readback(self):
        self.assertEqual(r.parse_readback(CANDIDATE + "\t" + REF + "\n", REF),
                         CANDIDATE)

    def test_12_reject_empty_duplicate_other_ref_or_partial(self):
        for txt in ("", CANDIDATE + "\t" + REF + "\n" +
                    CANDIDATE + "\t" + REF + "\n",
                    CANDIDATE + "\trefs/heads/main\n",
                    CANDIDATE[:30] + "\t" + REF + "\n",
                    CANDIDATE + " " + REF + "\n",
                    CANDIDATE + "\t" + REF + "\textra\n",
                    CONFLICT + "\t" + REF + "\n" + CANDIDATE + "\t" + REF):
            with self.subTest(txt=txt[:50]), self.assertRaises(r.Refuse):
                r.parse_readback(txt, REF)

    def test_13_reject_cr_nul_and_oversized_payload(self):
        for text in (CANDIDATE + "\t" + REF + "\r\n",
                     CANDIDATE + "\t" + REF + "\x00",
                     "x" * (r.MAX_OUTPUT_BYTES + 1)):
            with self.subTest(text=text[:30]), self.assertRaises(r.Refuse):
                r.parse_readback(text, REF)

    def test_14_run_is_fixed_public_read_only_no_secret_inheritance(self):
        valid = types.SimpleNamespace(
            returncode=0, stdout=CANDIDATE + "\t" + REF + "\n",
            stderr="injected-error-with-fake-secret")
        with mock.patch.dict(os.environ, {
                "VF_SUPER_PRIVATE_CANARY": "NOT-REAL", "GITHUB_TOKEN": "fake",
                "HOME": "/private/home", "PYTHONPATH": "/private/python",
                "GIT_CONFIG_GLOBAL": "/private/gitconfig"}, clear=True):
            with mock.patch.object(r.subprocess, "run", return_value=valid) as run:
                self.assertEqual(r.observe_public_ref(self.intent), CANDIDATE)
                kwargs = run.call_args.kwargs
                args = run.call_args.args[0]
                self.assertEqual(args, ["/usr/bin/git", "-c", "credential.helper=",
                                        "ls-remote", "--exit-code", r.ORIGIN, REF])
                self.assertFalse(kwargs["check"])
                self.assertEqual(kwargs["timeout"], 12)
                self.assertEqual(kwargs["env"], r._sandboxed_env())
                self.assertFalse(set(kwargs["env"]) &
                                 {"VF_SUPER_PRIVATE_CANARY", "GITHUB_TOKEN", "PYTHONPATH"})
                self.assertNotEqual(kwargs["env"]["HOME"], "/private/home")
                observer = Path(kwargs["cwd"])
                self.assertTrue(
                    any(part.startswith("vf604-cp085-public-observer-")
                        for part in observer.parts),
                    observer)
                self.assertIn(
                    os.sep + "vf604-cp085-public-observer-",
                    os.sep + os.sep.join(observer.parts),
                )
                self.assertTrue(kwargs["capture_output"])

    def test_15_external_command_error_denied_without_stderr_leak(self):
        mock_run = types.SimpleNamespace(returncode=128, stdout="", stderr="sensitive")
        with mock.patch.object(r.subprocess, "run", return_value=mock_run):
            with self.assertRaisesRegex(r.Refuse, "^READBACK_UNAVAILABLE$"):
                r.observe_public_ref(self.intent)

    def test_16_command_timeout_denied_without_retry(self):
        with mock.patch.object(r.subprocess, "run",
                               side_effect=subprocess.TimeoutExpired("git", 12)) as run:
            with self.assertRaises(r.Refuse):
                r.observe_public_ref(self.intent)
            self.assertEqual(run.call_count, 1)

    def test_17_wrong_ref_from_git_denied(self):
        mock_run = types.SimpleNamespace(
            returncode=0, stdout=CANDIDATE + "\trefs/heads/main\n", stderr="")
        with mock.patch.object(r.subprocess, "run", return_value=mock_run):
            with self.assertRaises(r.Refuse):
                r.observe_public_ref(self.intent)

    def test_18_receipt_canonical_roundtrip_and_digest(self):
        self.require_posix_permissions()
        value = r.classify(self.intent, CANDIDATE)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "proof.json"
            digest = r.write_private_receipt(path, value)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(r.read_private_receipt(path), value)

    def test_19_receipt_creation_is_one_shot_not_mutable(self):
        self.require_posix_permissions()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "proof.json"
            r.write_private_receipt(path, r.classify(self.intent, EXPECTED))
            old = path.read_bytes()
            with self.assertRaises(r.Refuse):
                r.write_private_receipt(path, r.classify(self.intent, CANDIDATE))
            self.assertEqual(path.read_bytes(), old)

    def test_20_tampered_freeze_and_false_green_denied(self):
        good = r.classify(self.intent, EXPECTED)
        for field, replacement in (("frozen", False),
                                   ("retry_allowed", True),
                                   ("release_allowed", True),
                                   ("effect_proven", True),
                                   ("production_authority", True),
                                   ("remote_github_writes", 1),
                                   ("journal_state", "COMMITTED_READBACK"),
                                   ("classification", "PASS")):
            with self.subTest(field=field):
                bad = dict(good, **{field: replacement})
                with self.assertRaises(r.Refuse):
                    r.receipt_bytes(bad)

    def test_21_unknown_or_missing_receipt_key_denied(self):
        value = r.classify(self.intent, CANDIDATE)
        with self.assertRaises(r.Refuse):
            r.receipt_bytes({**value, "access_token": "synthetic"})
        value.pop("task")
        with self.assertRaises(r.Refuse):
            r.receipt_bytes(value)

    def test_22_mutated_and_truncated_local_receipt_denied(self):
        self.require_posix_permissions()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "proof.json"
            r.write_private_receipt(path, r.classify(self.intent, CANDIDATE))
            source = path.read_bytes()
            for text in (source[:-1], source + b"\n",
                         source.replace(b"true", b"false", 1),
                         source + b"{}",
                         b"not-json"):
                path.write_bytes(text)
                with self.assertRaises(r.Refuse):
                    r.read_private_receipt(path)

    def test_23_symlink_receipt_refused(self):
        self.require_posix_permissions()
        with tempfile.TemporaryDirectory() as td:
            old = Path(td) / "proof.json"
            link = Path(td) / "pointer.json"
            r.write_private_receipt(old, r.classify(self.intent, CANDIDATE))
            link.symlink_to(old)
            with self.assertRaises(r.Refuse):
                r.read_private_receipt(link)
            with self.assertRaises(r.Refuse):
                r.write_private_receipt(link, r.classify(self.intent, EXPECTED))

    def test_24_world_readable_receipt_directory_denied(self):
        self.require_posix_permissions()
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td) / "unsafe"
            directory.mkdir(mode=0o755)
            directory.chmod(0o755)
            with self.assertRaisesRegex(r.Refuse, "^RECEIPT_DIR_MUST_BE_PRIVATE$"):
                r.write_private_receipt(directory / "proof.json",
                                        r.classify(self.intent, CANDIDATE))

    def test_27_posix_world_readable_dir_still_refuses(self):
        """A 0700 directory accepts a receipt. A 0755 directory is refused."""
        self.require_posix_permissions()
        value = r.classify(self.intent, CANDIDATE)
        with tempfile.TemporaryDirectory() as td:
            private = Path(td) / "private"
            private.mkdir(mode=0o700)
            private.chmod(0o700)
            written = private / "proof.json"
            r.write_private_receipt(written, value)
            self.assertEqual(written.stat().st_mode & 0o777, 0o600)
            world = Path(td) / "world"
            world.mkdir(mode=0o700)
            world.chmod(0o755)
            self.assertTrue(world.stat().st_mode & 0o077)
            with self.assertRaisesRegex(r.Refuse, "^RECEIPT_DIR_MUST_BE_PRIVATE$"):
                r.write_private_receipt(world / "proof.json", value)

    def test_25_selftest_and_cli_unknown_args_fail_closed(self):
        self.assertEqual(r.main(["tool", "--unexpected"]), 2)
        self.assertEqual(r.main(["tool", "--observe", "task", "refs/heads/main",
                                 EXPECTED, CANDIDATE, "-"]), 2)

    def test_26_cli_output_is_observation_not_admission(self):
        with mock.patch.object(r, "observe_public_ref", return_value=CANDIDATE):
            with mock.patch("builtins.print") as out:
                rc = r.main(["tool", "--observe", "cp085-synthetic", REF,
                             EXPECTED, CANDIDATE, "-"])
            self.assertEqual(rc, 0)
            printed = json.loads(out.call_args.args[0])
            self.assertEqual(printed["status"], "OBSERVATION_ONLY")
            self.assertIs(printed["frozen"], True)
            self.assertIs(printed["effect_proven"], False)
            self.assertEqual(printed["remote_github_writes"], 0)

    def test_28_group_readable_receipt_directory_denied(self):
        """0750 and 0740 are group-readable. 0700 stays private and is accepted."""
        self.require_posix_permissions()
        value = r.classify(self.intent, CANDIDATE)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for mode in (0o750, 0o740):
                with self.subTest(mode=oct(mode)):
                    directory = self._mode_dir(root, f"group-{mode:o}", mode)
                    self.assertEqual(
                        self._receipt_dir_result(r, directory, value),
                        "RECEIPT_DIR_MUST_BE_PRIVATE",
                    )
            private = self._mode_dir(root, "private", 0o700)
            self.assertEqual(
                self._receipt_dir_result(r, private, value), "ACCEPTED")
            self.assertEqual(
                (private / "proof.json").stat().st_mode & 0o777, 0o600)

    def test_29_weakened_receipt_dir_mask_is_caught(self):
        """Mask 0o077→0o007 accepts a group-readable directory. The live gate must not."""
        self.require_posix_permissions()
        source = Path(r.__file__).resolve().read_text(encoding="utf-8")
        needle = "path.parent.stat().st_mode & 0o077"
        weakened = "path.parent.stat().st_mode & 0o007"
        self.assertEqual(source.count(needle), 1)
        mutated_source = source.replace(needle, weakened, 1)
        self.assertNotIn(needle, mutated_source)
        self.assertIn(weakened, mutated_source)
        value = r.classify(self.intent, CANDIDATE)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mutant_path = root / "cp085_mask_007.py"
            mutant_path.write_text(mutated_source, encoding="utf-8")
            spec = importlib.util.spec_from_file_location(
                "cp085_receipt_dir_mask_007", mutant_path)
            if spec is None or spec.loader is None:
                self.fail("cannot load weakened receipt-dir mask")
            mutant = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mutant
            try:
                spec.loader.exec_module(mutant)
            except Exception:
                sys.modules.pop(spec.name, None)
                raise
            try:
                for mode in (0o750, 0o740):
                    with self.subTest(mode=oct(mode)):
                        opened = self._mode_dir(root, f"weak-{mode:o}", mode)
                        self.assertEqual(
                            self._receipt_dir_result(mutant, opened, value),
                            "ACCEPTED",
                        )
                        live = self._mode_dir(root, f"live-{mode:o}", mode)
                        self.assertEqual(
                            self._receipt_dir_result(r, live, value),
                            "RECEIPT_DIR_MUST_BE_PRIVATE",
                        )
            finally:
                sys.modules.pop(spec.name, None)


if __name__ == "__main__":
    unittest.main()
