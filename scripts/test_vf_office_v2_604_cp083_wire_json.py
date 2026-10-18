#!/usr/bin/env python3
"""CP083 GAP_9 wire JSON. Synthetic Unix sockets only.

No guest root, no etcd, no remote GitHub, no admission change.
A matching-UID fake sink cannot turn CRLF, duplicate keys, NaN, a second
frame, or an oversize frame into COMMITTED_READBACK. The sink request path
refuses those frames before any Git call.
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

import vf_office_v2_604_cp083_candidate_evidence_gate as gate
import vf_office_v2_604_cp083_hardened_candidate as candidate


class _SinkState:
    def __init__(self):
        self.received = b""


def fake_sink(endpoint: Path, ready: threading.Event, payload: bytes, state: _SinkState):
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
            peer.settimeout(2)
            try:
                state.received = peer.recv(4096)
            except (OSError, socket.timeout):
                pass
            try:
                peer.sendall(payload)
            except OSError:
                pass


class _Lab:
    """Stand-in sink journal. Records Git and attempt calls. Does not run Git."""

    def __init__(self):
        self.git_calls = []
        self.attempt_calls = []

    def status(self, case):
        return None

    def git(self, *args, **kwargs):
        self.git_calls.append(args)
        return type("Git", (), {"returncode": 0, "stdout": "a" * 40 + "\n"})()

    def candidate(self, key, expected=None, epoch=7, actor="worker-a"):
        self.git("commit-tree")
        return {"key": key}

    def attempt(self, intent, *, fault="none"):
        self.attempt_calls.append(fault)
        self.git("update-ref")
        return "COMMITTED_READBACK"

    def remote_sha(self):
        return "a" * 40

    def frozen(self):
        return False


@unittest.skipUnless(sys.platform == "linux" and hasattr(socket, "SO_PEERCRED"),
                     "Linux SO_PEERCRED required")
class WireJsonTests(unittest.TestCase):
    def exercise_ack(self, payload: bytes):
        with tempfile.TemporaryDirectory(prefix="vf604-cp083-wire-ack-") as td:
            endpoint_dir = Path(td) / "endpoint"
            endpoint_dir.mkdir()
            ready = threading.Event()
            state = _SinkState()
            worker = threading.Thread(
                target=fake_sink,
                args=(endpoint_dir / "sink.sock", ready, payload, state),
                daemon=True,
            )
            worker.start()
            self.assertTrue(ready.wait(2), "fake socket did not listen")
            original = candidate.SINK_UID
            candidate.SINK_UID = os.geteuid()
            git = mock.Mock(side_effect=AssertionError("git"))
            try:
                with mock.patch.object(candidate.offline, "git_raw", git):
                    answer = candidate.socket_exchange(
                        td, {"action": "effect", "case": "normal"})
            finally:
                candidate.SINK_UID = original
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive(), "synthetic endpoint leaked thread")
            self.assertEqual(git.call_count, 0)
            return answer, state

    def assert_frame_reason(self, payload: bytes, reason: str):
        left, right = socket.socketpair()
        git = mock.Mock(side_effect=AssertionError("git"))
        try:
            right.sendall(payload)
            with mock.patch.object(candidate.offline, "git_raw", git):
                with self.assertRaises(gate.Refused) as caught:
                    candidate.read_json_frame(
                        left, candidate.MAX_MESSAGE, time.monotonic() + 2.0)
        finally:
            left.close()
            right.close()
        self.assertEqual(str(caught.exception), reason)
        self.assertEqual(git.call_count, 0)

    def serve_payload(self, payload: bytes, *, uid: int):
        """One frame through serve(), then a root shutdown. Returns reply, lab."""
        lab = _Lab()
        errors = []
        ready = threading.Event()
        real_print = print

        def spy(*args, **kwargs):
            if args and args[0] == "READY":
                ready.set()
            return real_print(*args, **kwargs)

        seen = {"n": 0}
        real_unpack = candidate.struct.unpack

        def unpack(fmt, data):
            if fmt == "3i":
                seen["n"] += 1
                peer = uid if seen["n"] == 1 else 0
                return (0, peer, 0)
            return real_unpack(fmt, data)

        def forbidden_git(*args, **kwargs):
            lab.git_calls.append(("git_raw", args))
            raise AssertionError("git")

        with tempfile.TemporaryDirectory(prefix="vf604-cp083-wire-req-") as td:
            root = Path(td)
            (root / "endpoint").mkdir()
            with mock.patch.object(candidate.os, "geteuid", return_value=candidate.SINK_UID), \
                    mock.patch.object(candidate.struct, "unpack", unpack), \
                    mock.patch.object(candidate.offline.OfflineLab, "create", lambda path: lab), \
                    mock.patch.object(candidate.offline, "git_raw", forbidden_git), \
                    mock.patch("builtins.print", spy):
                worker = threading.Thread(
                    target=self._run_serve, args=(root, errors), daemon=True)
                worker.start()
                self.assertTrue(ready.wait(2), "sink did not become ready: " + repr(errors))
                reply = self._once(root, payload)
                shutdown = self._once(
                    root, b'{"action":"shutdown","case":"controller"}\n')
            worker.join(timeout=3)
        self.assertFalse(worker.is_alive(), "sink thread leaked")
        self.assertEqual(errors, [])
        self.assertIn(b"ROOT_CONTROL_SHUTDOWN", shutdown)
        return reply, lab

    @staticmethod
    def _run_serve(root, errors):
        try:
            candidate.serve(root, "normal")
        except Exception as exc:
            errors.append(repr(exc))

    @staticmethod
    def _once(root, payload: bytes) -> bytes:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(3)
        try:
            sock.connect(str(Path(root) / "endpoint" / "sink.sock"))
            sock.sendall(payload)
            data = bytearray()
            while b"\n" not in data:
                part = sock.recv(4096)
                if not part:
                    break
                data.extend(part)
            return bytes(data)
        finally:
            sock.close()

    def test_wire_request_crlf_or_duplicate_key_refused_without_effect(self):
        samples = (
            (b'{"action":"effect","case":"normal"}\r\n', "CR_IN_CANONICAL_JSON"),
            (b'{"action":"effect","case":"normal","action":"effect"}\n',
             "DUPLICATE_JSON_KEY"),
            (b'{"action":"effect","case":"normal","nested":{"k":1,"k":2}}\n',
             "DUPLICATE_JSON_KEY"),
            (b'{"action":"effect","case":"normal","n":NaN}\n', "NON_FINITE_JSON"),
            (b"null\n", "JSON_OBJECT_REQUIRED"),
            (b"{not-json\n", "INVALID_UTF8_OR_JSON"),
        )
        for payload, reason in samples:
            with self.subTest(reason=reason):
                self.assert_frame_reason(payload, reason)
        # These two are otherwise a valid effect. Last-key-wins or a CR
        # treated as whitespace would reach Git.
        for payload in (
            b'{"action":"effect","case":"normal"}\r\n',
            b'{"action":"effect","case":"normal","action":"effect"}\n',
        ):
            with self.subTest(serve=payload):
                reply, lab = self.serve_payload(payload, uid=candidate.WORKER_UID)
                self.assertEqual(lab.git_calls, [])
                self.assertEqual(lab.attempt_calls, [])
                self.assertEqual(
                    json.loads(reply.decode()),
                    {"reason": "Refused", "status": "FAIL_CLOSED"})
                self.assertNotIn(b"COMMITTED_READBACK", reply)

    def test_wire_ack_crlf_or_duplicate_key_refused_without_success(self):
        payloads = (
            b'{"status":"COMMITTED_READBACK"}\r\n',
            b'{"status":"NO_ACK_UNKNOWN","status":"COMMITTED_READBACK"}\n',
            b'{"status":"COMMITTED_READBACK","n":NaN}\n',
            b'{"status":"COMMITTED_READBACK","n":Infinity}\n',
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                answer, state = self.exercise_ack(payload)
                self.assertEqual(answer, {"status": "NO_ACK_UNKNOWN"})
                self.assertNotEqual(answer.get("status"), "COMMITTED_READBACK")
                self.assertTrue(state.received)

    def test_wire_two_frames_or_oversize_refused(self):
        two = (b'{"status":"COMMITTED_READBACK"}\n'
               b'{"status":"COMMITTED_READBACK"}\n')
        oversize = b" " * (candidate.MAX_MESSAGE + 5) + b'{"status":"COMMITTED_READBACK"}\n'
        for payload in (two, oversize):
            with self.subTest(size=len(payload)):
                answer, state = self.exercise_ack(payload)
                self.assertEqual(answer, {"status": "NO_ACK_UNKNOWN"})
                self.assertNotIn("COMMITTED_READBACK", answer.values())
                self.assertTrue(state.received)

    def test_wire_canonical_lf_roundtrip(self):
        answer, state = self.exercise_ack(b'{"status":"COMMITTED_READBACK"}\n')
        self.assertEqual(answer, {"status": "COMMITTED_READBACK"})
        self.assertIn(b'"action": "effect"', state.received)
        left, right = socket.socketpair()
        git = mock.Mock(side_effect=AssertionError("git"))
        try:
            right.sendall(b'{"action":"effect","case":"normal"}\n')
            with mock.patch.object(candidate.offline, "git_raw", git):
                got = candidate.read_json_frame(
                    left, candidate.MAX_MESSAGE, time.monotonic() + 2.0)
        finally:
            left.close()
            right.close()
        self.assertEqual(got, {"action": "effect", "case": "normal"})
        self.assertEqual(git.call_count, 0)
        reply, lab = self.serve_payload(
            b'{"action":"snapshot","case":"controller"}\n', uid=0)
        self.assertEqual(lab.git_calls, [])
        self.assertEqual(lab.attempt_calls, [])
        parsed = json.loads(reply.decode())
        self.assertEqual(parsed["status"], "ROOT_CONTROL_SNAPSHOT")
        self.assertEqual(parsed["head"], "a" * 40)
        self.assertIs(parsed["frozen"], False)

    def test_overflow_float_refused_on_request_and_ack(self):
        # 1e999 is a finite-looking token. float() turns it into Infinity.
        requests = (
            b'{"action":"effect","case":"normal","n":1e999}\n',
            b'{"action":"effect","case":"normal","n":-1e999}\n',
        )
        for payload in requests:
            with self.subTest(request=payload):
                self.assert_frame_reason(payload, "NON_FINITE_JSON")
            with self.subTest(serve=payload):
                reply, lab = self.serve_payload(payload, uid=candidate.WORKER_UID)
                self.assertEqual(lab.git_calls, [])
                self.assertEqual(lab.attempt_calls, [])
                self.assertEqual(
                    json.loads(reply.decode()),
                    {"reason": "Refused", "status": "FAIL_CLOSED"})
        for payload in (
            b'{"status":"COMMITTED_READBACK","n":1e999}\n',
            b'{"status":"COMMITTED_READBACK","n":-1e999}\n',
        ):
            with self.subTest(ack=payload):
                answer, state = self.exercise_ack(payload)
                self.assertEqual(answer, {"status": "NO_ACK_UNKNOWN"})
                self.assertTrue(state.received)

    def test_later_trailing_byte_refused_without_effect(self):
        # The extra byte is not in the first recv. Only the post-frame peek sees it.
        self._ack_later_byte()
        reply, lab = self._serve_later_byte()
        self.assertEqual(lab.git_calls, [])
        self.assertEqual(lab.attempt_calls, [])
        self.assertEqual(
            json.loads(reply.decode()),
            {"reason": "Refused", "status": "FAIL_CLOSED"})
        self.assertNotIn(b"COMMITTED_READBACK", reply)

    def _ack_later_byte(self):
        release = threading.Event()
        extra_sent = threading.Event()
        real_decode = candidate.evidence_gate.decode_wire_frame

        def wrapped(raw, limit):
            obj = real_decode(raw, limit)
            release.set()
            if not extra_sent.wait(2):
                raise AssertionError("trailing byte missing")
            return obj

        with tempfile.TemporaryDirectory(prefix="vf604-cp083-wire-trail-") as td:
            endpoint_dir = Path(td) / "endpoint"
            endpoint_dir.mkdir()
            ready = threading.Event()
            state = _SinkState()

            def sink():
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
                    server.bind(str(endpoint_dir / "sink.sock"))
                    server.listen(1)
                    server.settimeout(5)
                    ready.set()
                    try:
                        peer, _ = server.accept()
                    except socket.timeout:
                        return
                    with peer:
                        peer.settimeout(2)
                        try:
                            state.received = peer.recv(4096)
                        except OSError:
                            state.received = b""
                        peer.sendall(b'{"status":"COMMITTED_READBACK"}\n')
                        if not release.wait(2):
                            return
                        peer.sendall(b'x')
                        extra_sent.set()

            worker = threading.Thread(target=sink, daemon=True)
            worker.start()
            self.assertTrue(ready.wait(2), "fake socket did not listen")
            original = candidate.SINK_UID
            candidate.SINK_UID = os.geteuid()
            try:
                with mock.patch.object(
                        candidate.evidence_gate, "decode_wire_frame", wrapped):
                    answer = candidate.socket_exchange(
                        td, {"action": "effect", "case": "normal"})
            finally:
                candidate.SINK_UID = original
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive(), "synthetic endpoint leaked thread")
        self.assertEqual(answer, {"status": "NO_ACK_UNKNOWN"})
        self.assertTrue(state.received)
        self.assertTrue(extra_sent.is_set(), "peek ran before the later byte")

    def _serve_later_byte(self):
        lab = _Lab()
        errors = []
        ready = threading.Event()
        release = threading.Event()
        extra_sent = threading.Event()
        real_print = print
        real_decode = candidate.evidence_gate.decode_wire_frame
        frames = {"n": 0}

        def spy(*args, **kwargs):
            if args and args[0] == "READY":
                ready.set()
            return real_print(*args, **kwargs)

        def wrapped(raw, limit):
            obj = real_decode(raw, limit)
            frames["n"] += 1
            if frames["n"] == 1:
                release.set()
                if not extra_sent.wait(2):
                    raise AssertionError("trailing byte missing")
            return obj

        seen = {"n": 0}
        real_unpack = candidate.struct.unpack

        def unpack(fmt, data):
            if fmt == "3i":
                seen["n"] += 1
                peer = candidate.WORKER_UID if seen["n"] == 1 else 0
                return (0, peer, 0)
            return real_unpack(fmt, data)

        def forbidden_git(*args, **kwargs):
            lab.git_calls.append(("git_raw", args))
            raise AssertionError("git")

        def client(root):
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(3)
            try:
                sock.connect(str(Path(root) / "endpoint" / "sink.sock"))
                sock.sendall(b'{"action":"effect","case":"normal"}\n')
                if not release.wait(2):
                    return b""
                sock.sendall(b"x")
                extra_sent.set()
                data = bytearray()
                while b"\n" not in data:
                    part = sock.recv(4096)
                    if not part:
                        break
                    data.extend(part)
                return bytes(data)
            finally:
                sock.close()

        with tempfile.TemporaryDirectory(prefix="vf604-cp083-wire-trail-req-") as td:
            root = Path(td)
            (root / "endpoint").mkdir()
            with mock.patch.object(candidate.os, "geteuid", return_value=candidate.SINK_UID), \
                    mock.patch.object(candidate.struct, "unpack", unpack), \
                    mock.patch.object(candidate.offline.OfflineLab, "create", lambda path: lab), \
                    mock.patch.object(candidate.offline, "git_raw", forbidden_git), \
                    mock.patch.object(candidate.evidence_gate, "decode_wire_frame", wrapped), \
                    mock.patch("builtins.print", spy):
                worker = threading.Thread(
                    target=self._run_serve, args=(root, errors), daemon=True)
                worker.start()
                self.assertTrue(ready.wait(2), "sink did not become ready: " + repr(errors))
                reply = client(root)
                shutdown = self._once(
                    root, b'{"action":"shutdown","case":"controller"}\n')
            worker.join(timeout=3)
        self.assertFalse(worker.is_alive(), "sink thread leaked")
        self.assertEqual(errors, [])
        self.assertIn(b"ROOT_CONTROL_SHUTDOWN", shutdown)
        self.assertTrue(extra_sent.is_set(), "peek ran before the later byte")
        return reply, lab

    def test_serve_non_string_action_or_case_fail_closed(self):
        payloads = (
            b'{"action":1,"case":"normal"}\n',
            b'{"action":"effect","case":1}\n',
            b'{"action":true,"case":"normal"}\n',
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                reply, lab = self.serve_payload(payload, uid=candidate.WORKER_UID)
                self.assertEqual(lab.git_calls, [])
                self.assertEqual(lab.attempt_calls, [])
                self.assertEqual(
                    json.loads(reply.decode()),
                    {"reason": "Refuse", "status": "FAIL_CLOSED"})
                self.assertNotIn(b"COMMITTED_READBACK", reply)


if __name__ == "__main__":
    unittest.main()
