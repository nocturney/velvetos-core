#!/usr/bin/env python3
"""CP083 kernel socket negative tests; no etcd, Git effect, credentials, or root.

This test runs the candidate Unix socket framing inside a same-UID synthetic
harness. It is NOT a separate-UID/security admission proof. Linux only.
"""
from __future__ import annotations

import json
import multiprocessing
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest

SCRIPT_DIR = Path(__file__).resolve().parent


def _serve_synthetic(root: str, admit_current_uid: bool) -> None:
    sys.path.insert(0, str(SCRIPT_DIR))
    import vf_office_v2_604_cp083_hardened_candidate as cp083

    class StubLab:
        def status(self, _case: str):
            return None

    # Never construct an actual Git journal/provider; only parse negative IPC.
    cp083.offline.OfflineLab = lambda _fixture: StubLab()
    cp083.SINK_UID = os.geteuid()
    cp083.WORKER_UID = os.geteuid() if admit_current_uid else 62002
    cp083.serve(root, "normal")


@unittest.skipUnless(sys.platform == "linux" and hasattr(socket, "SO_PEERCRED"),
                     "requires Linux kernel SO_PEERCRED")
class NativeSocketNegativeTests(unittest.TestCase):
    def _start(self, admit_current_uid: bool) -> Path:
        td = tempfile.TemporaryDirectory(prefix="vf-cp083-ipc-negative-")
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        (root / "sink" / "native").mkdir(parents=True)
        (root / "endpoint").mkdir()
        proc = multiprocessing.get_context("fork").Process(
            target=_serve_synthetic, args=(str(root), admit_current_uid),
            daemon=True,
        )
        proc.start()

        def stop():
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=2)
            if proc.is_alive():
                proc.kill()
                proc.join(timeout=2)
        self.addCleanup(stop)

        endpoint = root / "endpoint" / "sink.sock"
        deadline = time.monotonic() + 3
        while not endpoint.is_socket() and proc.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(proc.is_alive(), "synthetic sink process did not start")
        self.assertTrue(endpoint.is_socket(), "synthetic sink socket absent")
        return endpoint

    def test_unknown_kernel_uid_rejected_before_frame(self):
        endpoint = self._start(admit_current_uid=False)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            sock.connect(str(endpoint))
            started = time.monotonic()
            # No request bytes at all: rejection must precede the read.
            result = json.loads(sock.recv(2048).decode())
        self.assertLess(time.monotonic() - started, 0.8)
        self.assertEqual(result["status"], "DENIED_OS_PRINCIPAL_OR_TASK_SCOPE")

    def test_allowed_peer_slow_drip_is_time_bounded_and_next_request_works(self):
        endpoint = self._start(admit_current_uid=True)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.06)
            sock.connect(str(endpoint))
            started = time.monotonic()
            received = b""
            # Continuously send partial frame data faster than a recv timeout.
            # A reset-on-every-recv implementation would be pinned indefinitely.
            while time.monotonic() - started < 3.3:
                try:
                    sock.sendall(b"x")
                except (BrokenPipeError, OSError):
                    pass
                try:
                    received += sock.recv(2048)
                    if b"\n" in received:
                        break
                except socket.timeout:
                    pass
                time.sleep(0.09)
        elapsed = time.monotonic() - started
        self.assertTrue(received, "slow-drip connection never failed closed")
        reply = json.loads(received.split(b"\n", 1)[0])
        self.assertEqual(reply["status"], "FAIL_CLOSED")
        self.assertGreater(elapsed, 1.6)
        self.assertLess(elapsed, 3.3)

        # Same synthetic UID, but wrong task: prove the listener is not pinned.
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            sock.connect(str(endpoint))
            sock.sendall(b'{"action":"effect","case":"other-task"}\n')
            reply = json.loads(sock.recv(2048).decode())
        self.assertEqual(reply["status"], "DENIED_OS_PRINCIPAL_OR_TASK_SCOPE")


if __name__ == "__main__":
    unittest.main()
