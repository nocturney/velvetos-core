#!/usr/bin/env python3
"""Static negatives for CP083 Option A reconciliation / UNKNOWN-after-ACK.

Does not start etcd, Git, root, or sockets. Pins that the hardening candidate
keeps revoke-first DENY, admit-first DRAIN, lost-ACK → UNKNOWN, and no blind
retry — without claiming full-chain security admission.
"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "scripts/vf_office_v2_604_cp083_hardened_candidate.py"


class ReconcileNegativeStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CANDIDATE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source, filename=str(CANDIDATE))

    def test_no_retry_loop_in_socket_exchange(self):
        exchange = None
        for node in self.tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "socket_exchange":
                exchange = node
                break
        self.assertIsNotNone(exchange)
        for node in ast.walk(exchange):
            if isinstance(node, ast.Call):
                func = node.func
                name = getattr(func, "attr", None) or getattr(func, "id", None)
                self.assertNotIn(name, {"retry", "sleep"},
                                 "socket_exchange must not sleep/retry")
        text = ast.get_source_segment(self.source, exchange) or ""
        self.assertNotIn("for _ in range", text)
        self.assertNotIn("while True", text)
        self.assertIn("NO_ACK_UNKNOWN", text)

    def test_ack_loss_cases_require_unknown_not_success(self):
        self.assertIn('"ack-before"', self.source)
        self.assertIn('"ack-after"', self.source)
        self.assertIn('case in ("ack-before", "ack-after")', self.source)
        self.assertIn('response["status"] == "NO_ACK_UNKNOWN"', self.source)
        self.assertIn('"UNKNOWN_EFFECT_RECONCILE"', self.source)
        self.assertIn("_no_blind_retry", self.source)
        self.assertIn('"NOT_ADMITTED"', self.source)

    def test_option_a_revoke_and_drain_labels_present(self):
        self.assertIn("revoke-first", self.source)
        self.assertIn("drain-before", self.source)
        self.assertIn("_revoke_committed_before_admit", self.source)
        self.assertIn("_revoke_moves_to_draining", self.source)
        self.assertIn("_ref_reservation_stays", self.source)
        self.assertIn("RESERVED", self.source)

    def test_mid_revoke_after_effect_is_unknown_reconcile(self):
        self.assertIn("mid_post_native_revoke_is_unknown_not_success", self.source)
        self.assertIn('response["status"] == "UNKNOWN_EFFECT_RECONCILE"', self.source)
        self.assertIn("_durable_unknown_frozen", self.source)
        self.assertIn("_restart_does_not_unlock", self.source)

    def test_security_admission_remains_red(self):
        self.assertIn('"security_admission": "RED"', self.source)
        self.assertIn('"production_authority": False', self.source)
        self.assertIn('"real_external_github_writes": 0', self.source)


if __name__ == "__main__":
    unittest.main()
