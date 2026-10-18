#!/usr/bin/env python3
"""Credential-free Linux Unix client negatives for CP083 candidate.

A synthetic socket endpoint under the current unprivileged UID impersonates
the sink. It cannot commit any Git effect. Root, secrets and etcd are absent.
"""
from __future__ import annotations

import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest

import vf_office_v2_604_cp083_hardened_candidate as candidate


def fake_sink(endpoint: Path, ready: threading.Event, mode: str):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(endpoint))
        server.listen(1)
        server.settimeout(5)
        ready.set()
        try:
            peer, _ = server.accept()
        except socket.timeout:
            return
        with peer:
            peer.settimeout(1)
            try:
                peer.recv(1024)
            except (OSError, socket.timeout):
                pass
            try:
                if mode == "forged-success":
                    peer.sendall(b'{"status":"COMMITTED_READBACK"}\n')
                elif mode == "oversize":
                    peer.sendall(b' ' * (candidate.MAX_MESSAGE + 5) +
                                 b'{"status":"COMMITTED_READBACK"}\n')
                elif mode == "slow-ack":
                    until = time.monotonic() + 3.8
                    while time.monotonic() < until:
                        peer.sendall(b' ')
                        time.sleep(0.09)
                    peer.sendall(b'{"status":"COMMITTED_READBACK"}\n')
            except OSError:
                pass


@unittest.skipUnless(sys.platform == "linux" and hasattr(socket, "SO_PEERCRED"),
                     "Linux SO_PEERCRED required")
class ClientNegativeTests(unittest.TestCase):
    def exercise(self, mode: str, expected_uid: int):
        with tempfile.TemporaryDirectory(prefix="vf604-cp083-client-neg-") as td:
            endpoint_dir = Path(td) / "endpoint"
            endpoint_dir.mkdir()
            ready = threading.Event()
            worker = threading.Thread(
                target=fake_sink,
                args=(endpoint_dir / "sink.sock", ready, mode),
                daemon=True,
            )
            worker.start()
            self.assertTrue(ready.wait(2), "fake socket did not listen")
            original = candidate.SINK_UID
            candidate.SINK_UID = expected_uid
            try:
                started = time.monotonic()
                answer = candidate.socket_exchange(
                    td, {"action": "effect", "case": "normal"})
                elapsed = time.monotonic() - started
            finally:
                candidate.SINK_UID = original
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive(), "synthetic endpoint leaked thread")
            return answer, elapsed

    def test_impostor_sink_cannot_forge_committed_ack(self):
        # Actual peer is the current Linux user, never SINK_UID 62001.
        response, elapsed = self.exercise("forged-success", 62001)
        self.assertEqual(response, {"status": "NO_ACK_UNKNOWN"})
        self.assertLess(elapsed, 2.0)

    def test_oversized_ack_cannot_be_accepted(self):
        response, elapsed = self.exercise("oversize", os.geteuid())
        self.assertEqual(response, {"status": "NO_ACK_UNKNOWN"})
        self.assertLess(elapsed, 2.0)

    def test_slow_drip_ack_is_bounded_and_uncertain(self):
        response, elapsed = self.exercise("slow-ack", os.geteuid())
        self.assertEqual(response, {"status": "NO_ACK_UNKNOWN"})
        self.assertLess(elapsed, 3.5)


if __name__ == "__main__":
    unittest.main()
