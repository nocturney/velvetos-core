#!/usr/bin/env python3
"""Unprivileged CP084 sink recovery rehearsal: native LOCAL Git and SQLite.

Test-only synthetic provider; uses a *single* kernel UID, not real mTLS,
external GitHub, trusted Core claims, or an authorized production sink.
There is no host privilege escalation, real worker or remote effect.
"""
from __future__ import annotations

import multiprocessing
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest

import vf_office_v2_604_cp083_hardened_candidate as cp083


def _synthetic_provider(_root):
    return {
        "actor": "worker-a", "epoch": 7, "phase": "ACTIVE",
        "ttl_seconds": 1, "revision": 7,
    }


@unittest.skipUnless(
    sys.platform == "linux" and hasattr(socket, "SO_PEERCRED")
    and os.geteuid() != 0,
    "requires non-root Linux SO_PEERCRED",
)
class NativeSinkRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="vf604-cp084-local-")
        self.root = Path(self.tmp.name) / "case"
        (self.root / "sink").mkdir(parents=True)
        (self.root / "endpoint").mkdir()
        self.process = None

        self.saved = (
            cp083.SINK_UID,
            cp083.WORKER_UID,
            cp083.local_cert_observation,
            cp083.offline.ENV,
        )
        uid = os.geteuid()
        cp083.SINK_UID = uid
        cp083.WORKER_UID = uid  # deliberate same-UID non-security fixture
        cp083.local_cert_observation = _synthetic_provider

        # No ambient cloud, SSH, Python or Git configuration reaches Git.
        # HOME and XDG_CONFIG_HOME come from the native empty directory.
        env = cp083.offline.git_subprocess_env()
        env["GIT_AUTHOR_NAME"] = "CP084 synthetic local fixture"
        env["GIT_AUTHOR_EMAIL"] = "cp084@example.invalid"
        env["GIT_COMMITTER_NAME"] = "CP084 synthetic local fixture"
        env["GIT_COMMITTER_EMAIL"] = "cp084@example.invalid"
        cp083.offline.ENV = env

    def tearDown(self):
        self.stop()
        (cp083.SINK_UID, cp083.WORKER_UID,
         cp083.local_cert_observation, cp083.offline.ENV) = self.saved
        self.tmp.cleanup()

    def stop(self):
        p = self.process
        if p is not None:
            if p.is_alive():
                p.terminate()
                p.join(timeout=2)
            if p.is_alive():
                p.kill()
                p.join(timeout=2)
        self.process = None

    def start(self, case):
        self.process = multiprocessing.get_context("fork").Process(
            target=cp083.serve, args=(str(self.root), case), daemon=True,
        )
        self.process.start()
        endpoint = self.root / "endpoint" / "sink.sock"
        until = time.monotonic() + 5
        while not endpoint.is_socket() and time.monotonic() < until:
            if not self.process.is_alive():
                break
            time.sleep(0.01)
        self.assertTrue(self.process.is_alive(),
                        f"sink exited early {self.process.exitcode}")
        self.assertTrue(endpoint.is_socket(), "sink did not bind socket")

    def request(self, case):
        return cp083.socket_exchange(
            str(self.root), {"action": "effect", "case": case})

    def lab(self):
        return cp083.offline.OfflineLab(self.root / "sink" / "native")

    def restart(self, case, *, stale_socket=False):
        self.stop()
        endpoint = self.root / "endpoint" / "sink.sock"
        if stale_socket:
            self.assertTrue(endpoint.is_socket())
        if endpoint.is_socket():
            # Test-only stale socket cleanup after the fixture process is dead.
            # Does not assert that a production supervisor would do this safely.
            endpoint.unlink()
        self.start(case)

    def assert_no_replay(self, case, expected_head):
        self.assertEqual(self.request(case)["status"], "NOT_ADMITTED")
        lab = self.lab()
        self.assertTrue(lab.frozen())
        self.assertEqual(lab.remote_sha(), expected_head)

    def test_01_normal_local_effect_and_duplicate_denied(self):
        self.start("normal")
        self.assertEqual(self.request("normal")["status"], "COMMITTED_READBACK")
        lab = self.lab()
        row = lab.status("normal")
        self.assertEqual(row["state"], "COMMITTED_READBACK")
        self.assertEqual(row["after_sha"], row["candidate"])
        self.assertEqual(lab.remote_sha(), row["candidate"])
        self.assertFalse(lab.frozen())
        self.assertEqual(self.request("normal")["status"], "NOT_ADMITTED")

    def test_02_lost_ack_before_git_freezes_and_survives_restart(self):
        self.start("ack-before")
        self.assertEqual(self.request("ack-before")["status"], "NO_ACK_UNKNOWN")
        lab = self.lab()
        row = lab.status("ack-before")
        self.assertEqual(row["state"], "UNKNOWN_EFFECT_RECONCILE")
        self.assertEqual(lab.remote_sha(), row["expected"])
        self.assertTrue(lab.frozen())
        self.assert_no_replay("ack-before", row["expected"])
        self.restart("ack-before")
        self.assert_no_replay("ack-before", row["expected"])
        self.assertEqual(self.lab().reconcile(
            "ack-before", process_terminated=True),
            "REMOTE_UNCHANGED_REVIEW_REQUIRED")
        self.assert_no_replay("ack-before", row["expected"])

    def test_03_lost_ack_after_git_freezes_and_survives_restart(self):
        self.start("ack-after")
        self.assertEqual(self.request("ack-after")["status"], "NO_ACK_UNKNOWN")
        lab = self.lab()
        row = lab.status("ack-after")
        self.assertEqual(row["state"], "UNKNOWN_EFFECT_RECONCILE")
        self.assertEqual(lab.remote_sha(), row["candidate"])
        self.assertTrue(lab.frozen())
        self.restart("ack-after")
        self.assert_no_replay("ack-after", row["candidate"])
        self.assertEqual(self.lab().reconcile(
            "ack-after", process_terminated=True),
            "REMOTE_ADVANCED_REVIEW_REQUIRED")
        self.assert_no_replay("ack-after", row["candidate"])

    def test_04_crash_after_local_git_restart_marks_unknown(self):
        self.start("crash-after")
        self.assertEqual(self.request("crash-after")["status"], "NO_ACK_UNKNOWN")
        self.process.join(timeout=5)
        self.assertEqual(self.process.exitcode, 92)
        lab = self.lab()
        row = lab.status("crash-after")
        self.assertEqual(row["state"], "EFFECT_IN_FLIGHT")
        self.assertEqual(lab.remote_sha(), row["candidate"])
        self.restart("crash-after", stale_socket=True)
        row = self.lab().status("crash-after")
        self.assertEqual(row["state"], "UNKNOWN_EFFECT_RECONCILE")
        self.assert_no_replay("crash-after", row["candidate"])
        self.assertEqual(self.lab().reconcile(
            "crash-after", process_terminated=True),
            "REMOTE_ADVANCED_REVIEW_REQUIRED")
        self.assert_no_replay("crash-after", row["candidate"])

    def test_05_unknown_conflicting_local_ref_stays_frozen(self):
        self.start("ack-before")
        self.assertEqual(self.request("ack-before")["status"], "NO_ACK_UNKNOWN")
        lab = self.lab()
        competing = lab.candidate("synthetic-conflict")
        lab.git("update-ref", cp083.offline.REF,
                competing.candidate, competing.expected)
        self.assertEqual(lab.reconcile(
            "ack-before", process_terminated=True),
            "REMOTE_CONFLICT_REVIEW_REQUIRED")
        self.assert_no_replay("ack-before", competing.candidate)
        self.restart("ack-before")
        self.assert_no_replay("ack-before", competing.candidate)


if __name__ == "__main__":
    unittest.main()
