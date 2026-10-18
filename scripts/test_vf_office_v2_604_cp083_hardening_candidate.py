#!/usr/bin/env python3
"""Unprivileged static checks only; NOT a substitute for fresh native CP083 receipts."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "scripts/vf_office_v2_604_cp083_osuid_tls_localgit_lab.py"
CANDIDATE = ROOT / "scripts/vf_office_v2_604_cp083_hardened_candidate.py"
EVIDENCE = ROOT / "docs/implementation/office-v2/phase2/p0-604-cp083-osuid-tls-localgit-2026-10-17.json"


class HardeningCandidateStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CANDIDATE.read_text(encoding="utf-8")
        cls.original = HISTORICAL.read_text(encoding="utf-8")

    def test_python_syntax(self):
        ast.parse(self.source, filename=str(CANDIDATE))

    def test_historical_seal_is_unchanged(self):
        self.assertEqual(
            hashlib.sha256(HISTORICAL.read_bytes()).hexdigest(),
            "ff7a648d99b2a4bdda057c0758017b90727c7ee637f660351b9bccaf2f42afe6",
        )
        self.assertEqual(
            hashlib.sha256(EVIDENCE.read_bytes()).hexdigest(),
            "cc6a576a57b76c6578c54af36c6d3306976cf92ea5814c3f28de7787285f69b0",
        )

    def _serve(self):
        return self.source.split("def serve(root, case):", 1)[1].split("\ndef probe(", 1)[0]

    def _frame(self):
        return self.source.split("def read_json_frame(", 1)[1].split(
            "\ndef socket_exchange(", 1)[0]

    def test_unauthorized_uid_rejected_before_socket_read(self):
        serve = self._serve()
        frame = self._frame()
        self.assertIn("socket.SO_PEERCRED", serve)
        self.assertIn("if uid not in (0, WORKER_UID):", serve)
        self.assertLess(serve.index("if uid not in (0, WORKER_UID):"),
                        serve.index("read_json_frame("))
        self.assertNotIn("c.recv(", serve[:serve.index("read_json_frame(")])
        self.assertIn("sock.recv(min(512, space))", frame)

    def test_authorized_socket_is_bounded(self):
        serve = self._serve()
        frame = self._frame()
        self.assertIn("c.settimeout(2.0)", serve)
        self.assertIn("except socket.timeout:", serve)
        self.assertLess(serve.index("c.settimeout(2.0)"), serve.index("read_json_frame("))
        self.assertIn("len(buffer) <= limit", frame)
        self.assertIn("sock.recv(min(512, space))", frame)

    def test_slow_drip_peer_cannot_reset_frame_timeout(self):
        serve = self._serve()
        frame = self._frame()
        call = "read_json_frame(c, MAX_MESSAGE, time.monotonic() + 2.0)"
        self.assertEqual(serve.count(call), 1)
        self.assertIn("remaining = deadline - time.monotonic()", frame)
        self.assertIn("if remaining <= 0:", frame)
        self.assertLess(frame.index('while b"\\n" not in buffer'),
                        frame.index("remaining = deadline - time.monotonic()"))
        self.assertLess(frame.index("remaining = deadline - time.monotonic()"),
                        frame.index("sock.settimeout(remaining)"))
        self.assertLess(frame.index("sock.settimeout(remaining)"),
                        frame.index("sock.recv(min(512, space))"))
        self.assertNotIn("sock.settimeout(2.0)", frame)

    def test_normal_committed_head_matches_journal(self):
        normal = self.source.split('if case == "normal":', 1)[-1]
        self.assertIn('snap["head"] == record["candidate"]', normal)
        self.assertIn('record["after_sha"] == record["candidate"]', normal)

    def test_client_peer_auth_and_absolute_ack_deadline(self):
        exchange = self.source.split("def socket_exchange(root, payload):", 1)[1].split("\ndef local_cert_observation(", 1)[0]
        self.assertIn('socket.SO_PEERCRED', exchange)
        # Platform capability gate must precede connect (non-Linux opens nothing).
        self.assertLess(
            exchange.index('sys.platform != "linux"'),
            exchange.index('sock.connect('),
        )
        self.assertLess(exchange.index('sock.connect('), exchange.index('peer_uid'))
        self.assertIn('peer_uid != SINK_UID', exchange)
        self.assertLess(exchange.index('peer_uid != SINK_UID'), exchange.index('sock.sendall('))
        self.assertIn(
            'read_json_frame(sock, MAX_MESSAGE, time.monotonic() + 3.0)', exchange)
        self.assertLess(exchange.index('sock.sendall('), exchange.index('read_json_frame('))
        frame = self._frame()
        self.assertIn('remaining = deadline - time.monotonic()', frame)
        self.assertLess(frame.index('remaining = deadline - time.monotonic()'),
                        frame.index('sock.recv('))
        self.assertIn('len(buffer) <= limit', frame)
        gate = (ROOT / "scripts/vf_office_v2_604_cp083_candidate_evidence_gate.py").read_text(
            encoding="utf-8")
        self.assertIn('require(len(raw) <= limit, "MESSAGE_SIZE_REFUSED")', gate)
        self.assertIn('"NO_ACK_UNKNOWN"', exchange)
        self.assertIn('_allowlisted_reply', exchange)

    def test_reply_allowlist_strips_unsolicited_keys(self):
        helper = self.source.split("def _allowlisted_reply(reply):", 1)[1].split(
            "\ndef read_json_frame(", 1)[0]
        self.assertIn('"status"', helper)
        self.assertIn('("head", "record", "frozen")', helper)
        self.assertNotIn("extra", helper)

    def test_red_only_no_production_promotion(self):
        self.assertIn('"production_authority": False', self.source)
        self.assertIn('"real_protected_core_issuer": False', self.source)
        self.assertIn('"remote_github_sink_proven": False', self.source)

    def test_worker_subprocess_environment_is_allowlisted(self):
        # No real credentials: simulate an unexpectedly named controller secret.
        tree = ast.parse(self.source, filename=str(CANDIDATE))
        defs = [node for node in tree.body
                if isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id == "SAFE_ENV"
                    for target in node.targets)]
        self.assertEqual(len(defs), 1)
        isolated = {}
        synthetic = {
            "VF_FAKE_SECRET_CANARY": "not-a-real-secret",
            "GITHUB_TOKEN": "synthetic",
            "PYTHONPATH": "/tmp/untrusted-python",
            "HOME": "/tmp/controller-home",
        }
        with mock.patch.dict(os.environ, synthetic, clear=True):
            exec(compile(ast.Module(body=defs, type_ignores=[]),
                         "<safe-env-assignment>", "exec"), {"os": os}, isolated)
        env = isolated["SAFE_ENV"]
        expected = {"PATH", "LANG", "LC_ALL", "HOME", "GIT_TERMINAL_PROMPT",
                    "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL"}
        self.assertEqual(set(env), expected)
        child = subprocess.run(
            [sys.executable, "-c", "import json, os; print(json.dumps(sorted(os.environ)))"],
            env=env, capture_output=True, text=True, timeout=5, check=True)
        child_keys = set(json.loads(child.stdout))
        # macOS may inject its CoreFoundation encoding marker at spawn time.
        extras = {"__CF_USER_TEXT_ENCODING"} if sys.platform == "darwin" else set()
        self.assertLessEqual(child_keys - expected, extras)
        for forbidden in ("VF_FAKE_SECRET_CANARY", "GITHUB_TOKEN", "PYTHONPATH"):
            self.assertNotIn(forbidden, child_keys)
        self.assertNotEqual(env["HOME"], synthetic["HOME"])
        self.assertEqual(env["HOME"], "/nonexistent")
        self.assertEqual(env["GIT_CONFIG_GLOBAL"], "/dev/null")


if __name__ == "__main__":
    unittest.main()
