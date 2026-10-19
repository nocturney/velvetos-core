"""Offline regression checks for CortenDesk 1.14.0 mobile source contract."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from subprocess import CompletedProcess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cortendesk_mobile_source_gate as gate


class MobileSourceGateTests(unittest.TestCase):
    def setUp(self):
        self.files = {
            "routes/web.php": b"web login required; web client",
            "mobile/touch.ts": b"onPointerDown; onPointerMove",
        }
        self.blobs = {name: gate.git_blob_id(blob) for name, blob in self.files.items()}
        self.pinner = patch.object(gate, "PINNED_BLOBS", self.blobs)
        self.signals = patch.object(gate, "FEATURE_RULES", {
            "web_auth": ("routes/web.php", ("login required", "web client")),
            "touch": ("mobile/touch.ts", ("onPointerDown", "onPointerMove")),
        })
        self.pinner.start()
        self.signals.start()
        self.addCleanup(self.pinner.stop)
        self.addCleanup(self.signals.stop)

    def test_pinned_source_signals_are_not_a_runtime_pass(self):
        report = gate.inspect_contents(self.files, gate.UPSTREAM_COMMIT)
        self.assertEqual(report["state"], "PINNED_SOURCE_SIGNALS_PRESENT_NOT_RUNTIME")
        self.assertTrue(report["source_exactly_pinned"])
        self.assertEqual(report["source_blob_count"], 2)
        self.assertEqual(report["features"]["touch"], "present_in_pinned_source")
        for name in (
            "container_started", "mobile_safari_verified", "remote_input_verified",
            "websocket_session_verified", "file_transfer_verified",
            "may_launch_container", "performed_mutation",
        ):
            self.assertIs(report[name], False, name)

    def test_git_blob_hash_has_size_prefix(self):
        self.assertEqual(
            gate.git_blob_id(b"hello"),
            "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0",
        )
        self.assertNotEqual(gate.git_blob_id(b"hello"), gate.git_blob_id(b"hello\n"))

    def test_old_commit_rejected_before_feature_checks(self):
        report = gate.inspect_contents(self.files, "9" * 40)
        self.assertEqual(report["reason"], "source_commit_mismatch")
        self.assertFalse(report["source_exactly_pinned"])

    def test_incomplete_manifest_rejected(self):
        report = gate.inspect_contents({"routes/web.php": self.files["routes/web.php"]}, gate.UPSTREAM_COMMIT)
        self.assertEqual(report["reason"], "source_file_set_invalid")

    def test_extra_unexpected_source_rejected(self):
        report = gate.inspect_contents({**self.files, "secrets.txt": b"secret"}, gate.UPSTREAM_COMMIT)
        self.assertEqual(report["reason"], "source_file_set_invalid")
        self.assertNotIn("secrets.txt", json.dumps(report))

    def test_forged_or_tampered_content_rejected(self):
        forged = {**self.files, "mobile/touch.ts": b"onPointerDown; onPointerMove; BAD"}
        report = gate.inspect_contents(forged, gate.UPSTREAM_COMMIT)
        self.assertEqual(report["reason"], "source_blob_mismatch")
        self.assertEqual(report["features"]["touch"], "not_verified")

    def test_wrong_source_type_rejected(self):
        forged = {**self.files, "mobile/touch.ts": "onPointerMove"}
        report = gate.inspect_contents(forged, gate.UPSTREAM_COMMIT)
        self.assertEqual(report["reason"], "source_blob_mismatch")

    def test_real_blob_without_required_source_signal_fails_closed(self):
        patched = dict(self.files)
        patched["mobile/touch.ts"] = b"onPointerDown, but move handler removed"
        with patch.object(gate, "PINNED_BLOBS", {
            k: gate.git_blob_id(v) for k, v in patched.items()
        }):
            report = gate.inspect_contents(patched, gate.UPSTREAM_COMMIT)
        self.assertEqual(report["state"], "SOURCE_CONTRACT_REJECTED")
        self.assertEqual(report["features"]["touch"], "source_signal_missing")
        self.assertFalse(report["mobile_safari_verified"])

    def test_oversized_source_rejected_before_hash(self):
        with patch.object(gate, "MAX_SOURCE_BYTES", 2):
            report = gate.inspect_contents(self.files, gate.UPSTREAM_COMMIT)
        self.assertEqual(report["reason"], "source_blob_mismatch")

    def test_checkout_read_only_and_static_success(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, data in self.files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            git = CompletedProcess([], 0, gate.UPSTREAM_COMMIT + "\n", "")
            with patch.object(gate.subprocess, "run", return_value=git) as runner:
                report = gate.inspect_checkout(root)
            self.assertEqual(report["state"], "PINNED_SOURCE_SIGNALS_PRESENT_NOT_RUNTIME")
            self.assertEqual(runner.call_count, 1)
            argv = runner.call_args.args[0]
            self.assertEqual(argv[0], "git")
            self.assertEqual(argv[-3:], ["rev-parse", "--verify", "HEAD"])
            self.assertFalse(runner.call_args.kwargs.get("shell", False))
            self.assertFalse(report["performed_mutation"])

    def test_checkout_rejects_symlinked_source(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, data in self.files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            link = root / "mobile" / "touch.ts"
            link.unlink()
            try:
                link.symlink_to(root / "routes" / "web.php")
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on this test filesystem")
            git = CompletedProcess([], 0, gate.UPSTREAM_COMMIT, "")
            with patch.object(gate.subprocess, "run", return_value=git):
                with self.assertRaisesRegex(gate.SourceGateError, "symlinked"):
                    gate.inspect_checkout(root)

    def test_cli_missing_checkout_does_not_leak_private_path(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "private-token-in-path"
            with redirect_stdout(StringIO()) as stream:
                result = gate.main(["--source-root", str(path)])
            parsed = json.loads(stream.getvalue())
            self.assertEqual(result, 2)
            self.assertEqual(parsed["state"], "SOURCE_UNAVAILABLE")
            self.assertFalse(parsed["may_launch_container"])
            self.assertNotIn(str(path), stream.getvalue())
            self.assertNotIn("private-token-in-path", stream.getvalue())

    def test_invalid_git_head_does_not_scan_files(self):
        with TemporaryDirectory() as tmp:
            git = CompletedProcess([], 0, "e" * 40 + "\n", "")
            with patch.object(gate.subprocess, "run", return_value=git):
                report = gate.inspect_checkout(Path(tmp))
            self.assertEqual(report["reason"], "source_commit_mismatch")
            self.assertFalse(report["source_exactly_pinned"])

    def test_static_report_never_claims_session_or_browser_pass(self):
        payload = json.dumps(gate.inspect_contents(self.files, gate.UPSTREAM_COMMIT))
        for bad in ("websocket_session_verified\": true",
                    "mobile_safari_verified\": true",
                    "container_started\": true"):
            self.assertNotIn(bad, payload)


if __name__ == "__main__":
    unittest.main()
