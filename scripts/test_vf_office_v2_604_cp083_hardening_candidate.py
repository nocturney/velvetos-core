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

    def test_unauthorized_uid_rejected_before_socket_read(self):
        serve = self.source.split("def serve(root, case):", 1)[1].split("\ndef probe(", 1)[0]
        self.assertIn("socket.SO_PEERCRED", serve)
        self.assertIn("if uid not in (0, WORKER_UID):", serve)
        self.assertLess(serve.index("if uid not in (0, WORKER_UID):"), serve.index("c.recv(512)"))

    def test_authorized_socket_is_bounded(self):
        serve = self.source.split("def serve(root, case):", 1)[1].split("\ndef probe(", 1)[0]
        self.assertIn("c.settimeout(2.0)", serve)
        self.assertIn("except socket.timeout:", serve)
        self.assertLess(serve.index("c.settimeout(2.0)"), serve.index("c.recv(512)"))

    def test_slow_drip_peer_cannot_reset_frame_timeout(self):
        serve = self.source.split("def serve(root, case):", 1)[1].split("\n" + "def probe(", 1)[0]
        deadline = "deadline = time.monotonic() + 2.0"
        remaining = "remaining = deadline - time.monotonic()"
        frame_loop = 'while b"\\n" not in incoming'
        self.assertEqual(serve.count(deadline), 1)
        self.assertLess(serve.index(deadline), serve.index(frame_loop))
        self.assertLess(serve.index(frame_loop), serve.index(remaining))
        self.assertLess(serve.index(remaining), serve.index("c.settimeout(remaining)"))
        self.assertLess(serve.index("c.settimeout(remaining)"), serve.index("c.recv(512)"))
        self.assertIn("if remaining <= 0:", serve)

    def test_normal_committed_head_matches_journal(self):
        normal = self.source.split('if case == "normal":', 1)[-1]
        self.assertIn('snap["head"] == record["candidate"]', normal)
        self.assertIn('record["after_sha"] == record["candidate"]', normal)

    def test_client_peer_auth_and_absolute_ack_deadline(self):
        exchange = self.source.split("def socket_exchange(root, payload):", 1)[1].split("\ndef local_cert_observation(", 1)[0]
        self.assertIn('socket.SO_PEERCRED', exchange)
        self.assertIn('peer_uid != SINK_UID', exchange)
        self.assertLess(exchange.index('peer_uid != SINK_UID'), exchange.index('sock.sendall('))
        self.assertIn('deadline = time.monotonic() + 3.0', exchange)
        self.assertIn('remaining = deadline - time.monotonic()', exchange)
        self.assertLess(exchange.index('remaining = deadline - time.monotonic()'), exchange.index('sock.recv('))
        self.assertIn('len(buffer) > MAX_MESSAGE', exchange)
        self.assertIn('"NO_ACK_UNKNOWN"', exchange)

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
