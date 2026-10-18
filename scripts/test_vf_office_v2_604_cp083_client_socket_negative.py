#!/usr/bin/env python3
"""Credential-free Linux Unix client negatives for CP083 candidate.

A synthetic socket endpoint under the current unprivileged UID impersonates
the sink. It cannot commit any Git effect. Root, secrets and etcd are absent.

Pins Cursor independent QA properties @ 85de7e7e (PR #749):
positive matching-UID control, slow-ACK lower bound, malformed replies,
symlink impostor, extra-field stripping, and platform guard before connect.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

import vf_office_v2_604_cp083_hardened_candidate as candidate


class _SinkState:
    def __init__(self):
        self.received = b""
        self.accepted = False


def fake_sink(endpoint: Path, ready: threading.Event, mode: str, state: _SinkState):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(endpoint))
        server.listen(1)
        server.settimeout(5)
        ready.set()
        try:
            peer, _ = server.accept()
        except socket.timeout:
            return
        state.accepted = True
        with peer:
            peer.settimeout(1)
            try:
                state.received = peer.recv(1024)
            except (OSError, socket.timeout):
                pass
            try:
                if mode == "forged-success":
                    peer.sendall(b'{"status":"COMMITTED_READBACK"}\n')
                elif mode == "immediate-success":
                    peer.sendall(b'{"status":"COMMITTED_READBACK"}\n')
                elif mode == "extra-fields":
                    peer.sendall(
                        b'{"status":"COMMITTED_READBACK","extra":"kept","token":"x"}\n')
                elif mode == "malformed":
                    peer.sendall(b'{not-json\n')
                elif mode == "json-array":
                    peer.sendall(b'[{"status":"COMMITTED_READBACK"}]\n')
                elif mode == "json-null":
                    peer.sendall(b'null\n')
                elif mode == "non-string-status":
                    peer.sendall(b'{"status":1}\n')
                elif mode == "empty-line":
                    peer.sendall(b'\n')
                elif mode == "two-json":
                    peer.sendall(
                        b'{"status":"COMMITTED_READBACK"}\n'
                        b'{"status":"COMMITTED_READBACK"}\n')
                elif mode == "oversize":
                    peer.sendall(b' ' * (candidate.MAX_MESSAGE + 5) +
                                 b'{"status":"COMMITTED_READBACK"}\n')
                elif mode == "slow-ack":
                    until = time.monotonic() + 3.8
                    while time.monotonic() < until:
                        peer.sendall(b' ')
                        time.sleep(0.09)
                    peer.sendall(b'{"status":"COMMITTED_READBACK"}\n')
                elif mode == "partial-then-late":
                    peer.sendall(b'{"status":')
                    time.sleep(3.2)
                    peer.sendall(b'"COMMITTED_READBACK"}\n')
            except OSError:
                pass


@unittest.skipUnless(sys.platform == "linux" and hasattr(socket, "SO_PEERCRED"),
                     "Linux SO_PEERCRED required")
class ClientNegativeTests(unittest.TestCase):
    def exercise(self, mode: str, expected_uid: int, *, symlink=False):
        with tempfile.TemporaryDirectory(prefix="vf604-cp083-client-neg-") as td:
            endpoint_dir = Path(td) / "endpoint"
            endpoint_dir.mkdir()
            listen_path = endpoint_dir / ("real.sock" if symlink else "sink.sock")
            if symlink:
                # Listener lives beside the expected path; symlink retargets the name.
                pass
            ready = threading.Event()
            state = _SinkState()
            worker = threading.Thread(
                target=fake_sink,
                args=(listen_path, ready, mode, state),
                daemon=True,
            )
            worker.start()
            self.assertTrue(ready.wait(2), "fake socket did not listen")
            if symlink:
                (endpoint_dir / "sink.sock").symlink_to(listen_path)
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
            return answer, elapsed, state

    def test_impostor_sink_cannot_forge_committed_ack(self):
        # Actual peer is the current Linux user, never SINK_UID 62001.
        response, elapsed, state = self.exercise("forged-success", 62001)
        self.assertEqual(response, {"status": "NO_ACK_UNKNOWN"})
        self.assertLess(elapsed, 2.0)
        self.assertEqual(state.received, b"",
                         "request must not be sent before peer UID verify")

    def test_symlink_impostor_sink_sends_zero_request_bytes(self):
        response, elapsed, state = self.exercise(
            "forged-success", 62001, symlink=True)
        self.assertEqual(response, {"status": "NO_ACK_UNKNOWN"})
        self.assertLess(elapsed, 2.0)
        self.assertEqual(state.received, b"")

    def test_matching_uid_immediate_ack_is_accepted(self):
        # Positive control: a build that always returns NO_ACK_UNKNOWN fails here.
        response, elapsed, state = self.exercise(
            "immediate-success", os.geteuid())
        self.assertEqual(response, {"status": "COMMITTED_READBACK"})
        self.assertLess(elapsed, 2.0)
        self.assertIn(b'"action": "effect"', state.received)
        self.assertIn(b'"case": "normal"', state.received)

    def test_extra_reply_fields_are_stripped(self):
        response, _, state = self.exercise("extra-fields", os.geteuid())
        self.assertEqual(response, {"status": "COMMITTED_READBACK"})
        self.assertNotIn("extra", response)
        self.assertNotIn("token", response)
        self.assertTrue(state.received)

    def test_oversized_ack_cannot_be_accepted(self):
        response, elapsed, _ = self.exercise("oversize", os.geteuid())
        self.assertEqual(response, {"status": "NO_ACK_UNKNOWN"})
        self.assertLess(elapsed, 2.0)

    def test_slow_drip_ack_is_bounded_and_uncertain(self):
        response, elapsed, state = self.exercise("slow-ack", os.geteuid())
        self.assertEqual(response, {"status": "NO_ACK_UNKNOWN"})
        self.assertGreater(elapsed, 2.5)
        self.assertLess(elapsed, 3.5)
        self.assertTrue(state.received, "request must have been sent for a matching UID")

    def test_partial_then_late_ack_is_uncertain(self):
        response, elapsed, state = self.exercise(
            "partial-then-late", os.geteuid())
        self.assertEqual(response, {"status": "NO_ACK_UNKNOWN"})
        self.assertGreater(elapsed, 2.5)
        self.assertLess(elapsed, 3.5)
        self.assertTrue(state.received)

    def test_malformed_and_non_dict_acks_are_uncertain(self):
        for mode in ("malformed", "json-array", "json-null",
                     "non-string-status", "empty-line"):
            with self.subTest(mode=mode):
                response, elapsed, state = self.exercise(mode, os.geteuid())
                self.assertEqual(response, {"status": "NO_ACK_UNKNOWN"})
                self.assertLess(elapsed, 2.0)
                self.assertTrue(state.received)

    def test_two_json_values_on_one_stream_use_first_line_only(self):
        # First line is well-formed; a second frame is trailing payload and is refused.
        response, _, state = self.exercise("two-json", os.geteuid())
        self.assertEqual(response, {"status": "NO_ACK_UNKNOWN"})
        self.assertTrue(state.received)

    def test_platform_guard_skips_connect_on_non_linux(self):
        with tempfile.TemporaryDirectory(prefix="vf604-cp083-nolinux-") as td:
            endpoint_dir = Path(td) / "endpoint"
            endpoint_dir.mkdir()
            ready = threading.Event()
            state = _SinkState()
            worker = threading.Thread(
                target=fake_sink,
                args=(endpoint_dir / "sink.sock", ready, "immediate-success", state),
                daemon=True,
            )
            worker.start()
            self.assertTrue(ready.wait(2))
            with mock.patch.object(candidate.sys, "platform", "darwin"):
                answer = candidate.socket_exchange(
                    td, {"action": "effect", "case": "normal"})
            worker.join(timeout=1)
            self.assertEqual(answer, {"status": "NO_ACK_UNKNOWN"})
            self.assertFalse(state.accepted, "non-Linux must not connect")


if __name__ == "__main__":
    unittest.main()
