#!/usr/bin/env python3
"""Unprivileged static checks only; NOT a substitute for fresh native CP083 receipts."""
import ast
import hashlib
from pathlib import Path
import unittest

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

    def test_normal_committed_head_matches_journal(self):
        normal = self.source.split('if case == "normal":', 1)[-1]
        self.assertIn('snap["head"] == record["candidate"]', normal)
        self.assertIn('record["after_sha"] == record["candidate"]', normal)

    def test_red_only_no_production_promotion(self):
        self.assertIn('"production_authority": False', self.source)
        self.assertIn('"real_protected_core_issuer": False', self.source)
        self.assertIn('"remote_github_sink_proven": False', self.source)


if __name__ == "__main__":
    unittest.main()
