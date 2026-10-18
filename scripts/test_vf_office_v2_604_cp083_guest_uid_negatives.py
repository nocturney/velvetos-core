#!/usr/bin/env python3
"""CP083 kernel-UID negatives. Disposable Linux guest only.

These five tests need distinct numeric UIDs or the effect-time fence inside
the disposable guest. They run only when this process is Linux root and
VF604_CP083_DISPOSABLE_GUEST_ONLY=VF604_CP083_EXPLICIT_NO_REMOTE, and never
on Chris. Every other host, including hosted CI and Windows, records
SKIP_NEEDS_GUEST. That skip is not a pass of the security assertions.

ChatGPT-069 marked only the revoke-between-observe-and-update-ref case GAP.
That test is expected-fail with reason
GAP_revoke_between_pre_git_check_and_update_ref_denies_effect.
The other four assert denial. A guest failure there means the hole is still
open. Do not describe the current hole as success.

security_admission stays RED. No admission and no deploy.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

PERMIT_ENV = "VF604_CP083_DISPOSABLE_GUEST_ONLY"
PERMIT_VAL = "VF604_CP083_EXPLICIT_NO_REMOTE"
SINK_UID = 62001
WORKER_UID = 62002
_CANDIDATE_MODULE = "vf_office_v2_604_cp083_hardened_candidate"
_OFFLINE_MODULE = "vf_office_v2_604_native_git_crash_reconcile_offline"
_GAP_REVOKE = "GAP_revoke_between_pre_git_check_and_update_ref_denies_effect"
_WIRE = {"action": "effect", "case": "normal"}


def _chris_host() -> bool:
    host = socket.gethostname().lower()
    user = (
        os.environ.get("USER")
        or os.environ.get("LOGNAME")
        or os.environ.get("USERNAME")
        or ""
    ).lower()
    return user == "chris" or "chris" in host


def guest_ready() -> bool:
    """Linux root plus the explicit disposable marker. Never Chris."""
    if sys.platform != "linux" or not hasattr(os, "geteuid"):
        return False
    if os.geteuid() != 0:
        return False
    if os.environ.get(PERMIT_ENV) != PERMIT_VAL:
        return False
    if _chris_host():
        return False
    return True


def _marker_ok() -> bool:
    return (
        sys.platform == "linux"
        and os.environ.get(PERMIT_ENV) == PERMIT_VAL
        and not _chris_host()
    )


def _load_candidate():
    import importlib
    return importlib.import_module(_CANDIDATE_MODULE)


def _load_offline():
    import importlib
    return importlib.import_module(_OFFLINE_MODULE)


def _drop(uid: int):
    def cb():
        os.setgroups([])
        os.setgid(uid)
        os.setuid(uid)
    return cb


def _child_env() -> dict:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "C",
        "LC_ALL": "C",
        "HOME": "/tmp",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        PERMIT_ENV: PERMIT_VAL,
    }


def _spawn(uid: int, args: list[str]) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-B", os.path.realpath(__file__), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_child_env(),
        preexec_fn=_drop(uid),
    )


def _readline(proc: subprocess.Popen, timeout: float) -> str:
    box: dict[str, str] = {}

    def read() -> None:
        if proc.stdout is not None:
            box["line"] = proc.stdout.readline()

    thread = threading.Thread(target=read, daemon=True)
    thread.start()
    thread.join(timeout)
    return box.get("line", "")


def _stop(proc: subprocess.Popen | None) -> str:
    if proc is None:
        return ""
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)
    err = ""
    if proc.stderr is not None:
        err = proc.stderr.read() or ""
    return err


def _prepare(root: Path) -> None:
    root.chmod(0o755)
    sink = root / "sink"
    endpoint = root / "endpoint"
    sink.mkdir(mode=0o700)
    endpoint.mkdir(mode=0o755)
    os.chown(sink, SINK_UID, SINK_UID)
    os.chown(endpoint, SINK_UID, SINK_UID)
    endpoint.chmod(0o755)


def _refuse_child(expected_uid: int) -> bool:
    if not _marker_ok() or not hasattr(os, "geteuid"):
        print("SKIP_NEEDS_GUEST", flush=True)
        return True
    if os.geteuid() != expected_uid:
        print("SKIP_NEEDS_GUEST", flush=True)
        return True
    return False


def _guest_sink(root: str, case: str) -> int:
    if _refuse_child(SINK_UID):
        return 0
    cand = _load_candidate()

    def admitted(_root):
        return {
            "actor": "worker-a",
            "epoch": 7,
            "phase": "ACTIVE",
            "ttl_seconds": 1,
            "revision": 10,
        }

    # Reach the kernel-UID decision without starting etcd. The patch is local
    # to this disposable sink process.
    cand.local_cert_observation = admitted
    offline = _load_offline()
    original_attempt = offline.OfflineLab.attempt

    def watched(self, intent, **kwargs):
        (Path(root) / "endpoint" / "attempt.seen").write_text("seen\n", encoding="utf-8")
        return original_attempt(self, intent, **kwargs)

    offline.OfflineLab.attempt = watched
    cand.serve(root, case)
    return 0


def _guest_request(root: str) -> int:
    if _refuse_child(WORKER_UID):
        return 0
    cand = _load_candidate()
    answer = cand.socket_exchange(root, dict(_WIRE))
    print(json.dumps({
        "pid": os.getpid(),
        "euid": os.geteuid(),
        "status": answer.get("status"),
        "wire": json.dumps(_WIRE, sort_keys=True),
    }, sort_keys=True), flush=True)
    return 0


def _guest_issued() -> int:
    if _refuse_child(WORKER_UID):
        return 0
    print(f"ISSUED {os.getpid()} {os.geteuid()}", flush=True)
    time.sleep(30)
    return 0


def _guest_fake_ack(root: str) -> int:
    if _refuse_child(SINK_UID):
        return 0
    endpoint = Path(root) / "endpoint"
    endpoint.mkdir(parents=True, exist_ok=True)
    sock_path = endpoint / "sink.sock"
    if sock_path.exists():
        sock_path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(str(sock_path))
        sock_path.chmod(0o666)
        server.listen(1)
        server.settimeout(5)
        print("READY", flush=True)
        try:
            conn, _ = server.accept()
        except socket.timeout:
            print("NO_PEER", flush=True)
            return 2
        with conn:
            conn.settimeout(2)
            try:
                got = conn.recv(2048)
            except OSError:
                got = b""
            # Lie. No SQLite journal and no Git ref exist for this reply.
            conn.sendall(b'{"status":"COMMITTED_READBACK"}\n')
        print(json.dumps({"received": got.decode("utf-8", "replace")}), flush=True)
    finally:
        server.close()
    return 0


def _guest_hold() -> int:
    if _refuse_child(SINK_UID):
        return 0
    print(f"HOLD {os.getpid()} {os.geteuid()}", flush=True)
    time.sleep(30)
    return 0


class GuestUidNegativeTests(unittest.TestCase):
    def _assert_no_effect(self, status, head, seed, reached, message):
        self.assertNotEqual(status, "COMMITTED_READBACK", message)
        self.assertEqual(head, seed, message)
        if not reached and status not in {
            "DENIED_OS_PRINCIPAL_OR_TASK_SCOPE",
            "DENIED_UNISSUED_PROCESS",
            "DENIED_REPLAY",
            "NOT_ADMITTED",
            "DENIED_STALE",
            "UNKNOWN_EFFECT_RECONCILE",
        }:
            self.fail("effect decision not reached: " + str(status))

    def setUp(self):
        candidate = Path(__file__).with_name(
            "vf_office_v2_604_cp083_hardened_candidate.py")
        text = candidate.read_text(encoding="utf-8")
        self.assertIn(f'PERMIT_ENV = "{PERMIT_ENV}"', text)
        self.assertIn(f'PERMIT_VAL = "{PERMIT_VAL}"', text)
        self.assertIn('"security_admission": "RED"', text)
        if not guest_ready():
            self.skipTest("SKIP_NEEDS_GUEST")

    def test_same_worker_uid_unissued_process_cannot_effect(self):
        """A second UID 62002 process is not the issued worker."""
        with tempfile.TemporaryDirectory(prefix="vf604-cp083-unissued-") as td:
            root = Path(td)
            _prepare(root)
            sink = _spawn(SINK_UID, ["--guest-sink", str(root), "normal"])
            issued = None
            requester = None
            try:
                ready = _readline(sink, 8)
                self.assertEqual(ready.strip(), "READY", _stop(sink))
                issued = _spawn(WORKER_UID, ["--guest-issued"])
                issued_line = _readline(issued, 3).split()
                self.assertEqual(issued_line[:2], ["ISSUED", str(issued.pid)])
                self.assertEqual(issued_line[2], str(WORKER_UID))
                offline = _load_offline()
                lab = offline.OfflineLab(root / "sink" / "native")
                seed = lab.remote_sha()
                requester = _spawn(WORKER_UID, ["--guest-request", str(root)])
                raw = _readline(requester, 8)
                self.assertTrue(raw.strip(), _stop(requester) or _stop(sink))
                answer = json.loads(raw)
                self.assertEqual(answer["euid"], WORKER_UID)
                self.assertNotEqual(answer["pid"], issued.pid)
                self._assert_no_effect(
                    answer["status"],
                    lab.remote_sha(),
                    seed,
                    (root / "endpoint" / "attempt.seen").is_file(),
                    "unissued same-UID process must not effect; "
                    "authorization is not bound to the issued process",
                )
            finally:
                _stop(requester)
                _stop(issued)
                _stop(sink)

    def test_same_sink_uid_fake_ack_not_accepted_without_effect_proof(self):
        """UID 62001 alone is not proof of a local Git/SQLite effect."""
        with tempfile.TemporaryDirectory(prefix="vf604-cp083-fake-ack-") as td:
            root = Path(td)
            root.chmod(0o755)
            rogue = _spawn(SINK_UID, ["--guest-fake-ack", str(root)])
            try:
                ready = _readline(rogue, 3)
                self.assertEqual(ready.strip(), "READY", _stop(rogue))
                status = Path(f"/proc/{rogue.pid}/status").read_text(encoding="utf-8")
                self.assertIn(f"\nUid:\t{SINK_UID}\t{SINK_UID}\t", status)
                cand = _load_candidate()
                self.assertEqual(cand.SINK_UID, SINK_UID)
                answer = cand.socket_exchange(str(root), dict(_WIRE))
                detail = _readline(rogue, 3)
                self.assertNotIn("NO_PEER", detail)
                parsed = json.loads(detail)
                self.assertIn('"action": "effect"', parsed["received"])
                self.assertFalse((root / "sink" / "native" / "receipt.sqlite3").exists())
                self.assertFalse((root / "sink" / "native" / "scratch.git").exists())
                self.assertNotEqual(
                    answer.get("status"),
                    "COMMITTED_READBACK",
                    "same-UID ACK without sqlite/ref readback must not be accepted",
                )
            finally:
                _stop(rogue)

    def test_live_unallocated_numeric_uid_does_not_pass_guard(self):
        """A live numeric UID with no passwd entry must not clear guard()."""
        holder = _spawn(SINK_UID, ["--guest-hold"])
        try:
            line = _readline(holder, 3).split()
            self.assertEqual(line, ["HOLD", str(holder.pid), str(SINK_UID)])
            import pwd
            with self.assertRaises(KeyError):
                pwd.getpwuid(SINK_UID)
            status = Path(f"/proc/{holder.pid}/status").read_text(encoding="utf-8")
            self.assertIn(f"\nUid:\t{SINK_UID}\t{SINK_UID}\t", status)
            cand = _load_candidate()
            try:
                cand.guard(Path("/nonexistent-etcd"), Path("/nonexistent-ctl"))
            except cand.Refuse as exc:
                reason = str(exc)
            else:
                self.fail(
                    "guard returned while live unallocated UID "
                    f"{SINK_UID} was running"
                )
            unrelated = {
                "LINUX_ARM64_DISPOSABLE_ONLY",
                "EXPLICIT_ROOT_FIXTURE_CONTROLLER_ONLY",
                "EXISTING_COLIMA_GUEST_REQUIRED",
                "AMBIENT_CREDENTIALS_REFUSED",
                "OFFICIAL_ETCD_BINARIES_PIN_DRIFT",
                "PINNED_IDENTITY_MODULE_DRIFT",
                "TEST_BINARIES_MISSING",
                "FIXTURE_UID_ALREADY_ALLOCATED",
            }
            self.assertNotIn(
                reason,
                unrelated,
                "live numeric UID occupancy was not the refusal: " + reason,
            )
            self.assertIn(str(SINK_UID), reason)
            self.assertTrue(
                any(tok in reason for tok in ("LIVE", "OCCUP", "PROCESS", "UNALLOCATED")),
                reason,
            )
        finally:
            _stop(holder)

    def test_replay_after_fresh_fixture_with_same_issuer_claim_denied(self):
        """The same action/case bytes must not effect a fresh fixture."""
        captured = self._admit_once()
        wire = captured["wire"]
        self.assertEqual(json.loads(wire), _WIRE)
        claim = captured["claim"]
        self.assertIsNone(claim.get("signed_nonce"))
        self.assertIs(claim.get("new_authority"), False)
        with tempfile.TemporaryDirectory(prefix="vf604-cp083-replay-") as td:
            root = Path(td)
            _prepare(root)
            (root / "issuer-claim.json").write_text(
                json.dumps(claim, sort_keys=True), encoding="utf-8")
            sink = _spawn(SINK_UID, ["--guest-sink", str(root), "normal"])
            requester = None
            try:
                ready = _readline(sink, 8)
                self.assertEqual(ready.strip(), "READY", _stop(sink))
                offline = _load_offline()
                lab = offline.OfflineLab(root / "sink" / "native")
                lab.set_provider(
                    actor=claim["actor"],
                    epoch=claim["epoch"],
                    phase=claim["phase"],
                    ttl=claim["ttl_seconds"],
                    revision=claim["revision"],
                )
                seed = lab.remote_sha()
                requester = _spawn(WORKER_UID, ["--guest-request", str(root)])
                raw = _readline(requester, 8)
                self.assertTrue(raw.strip(), _stop(requester) or _stop(sink))
                answer = json.loads(raw)
                self.assertEqual(answer["wire"], wire)
                self._assert_no_effect(
                    answer["status"],
                    lab.remote_sha(),
                    seed,
                    (root / "endpoint" / "attempt.seen").is_file(),
                    "replay onto a fresh fixture with the same issuer claim "
                    "and no new authority must be denied",
                )
            finally:
                _stop(requester)
                _stop(sink)

    def _admit_once(self) -> dict:
        with tempfile.TemporaryDirectory(prefix="vf604-cp083-capture-") as td:
            root = Path(td)
            _prepare(root)
            sink = _spawn(SINK_UID, ["--guest-sink", str(root), "normal"])
            requester = None
            try:
                ready = _readline(sink, 8)
                self.assertEqual(ready.strip(), "READY", _stop(sink))
                offline = _load_offline()
                lab = offline.OfflineLab(root / "sink" / "native")
                provider = json.loads(lab.provider.read_text(encoding="utf-8"))
                requester = _spawn(WORKER_UID, ["--guest-request", str(root)])
                raw = _readline(requester, 8)
                self.assertTrue(raw.strip(), _stop(requester) or _stop(sink))
                answer = json.loads(raw)
                if answer["status"] != "COMMITTED_READBACK":
                    self.fail(
                        "original request was not admitted; replay was not "
                        "reached: " + str(answer["status"])
                    )
                return {
                    "wire": answer["wire"],
                    "claim": {
                        "actor": provider["actor"],
                        "epoch": provider["epoch"],
                        "phase": provider["phase"],
                        "ttl_seconds": provider["ttl_seconds"],
                        "revision": provider["revision"],
                        "signed_nonce": None,
                        "new_authority": False,
                    },
                }
            finally:
                _stop(requester)
                _stop(sink)

    @unittest.expectedFailure
    def test_revoke_between_pre_git_check_and_update_ref_denies_effect(self):
        """Revoke after the last observe() and before update-ref.

        Admission requires zero post-revoke ref advancement. Current code can
        still advance the local ref. Expected RED failure until an effect-time
        fence exists.
        """
        offline = _load_offline()
        with tempfile.TemporaryDirectory(prefix="vf604-cp083-revoke-gap-") as td:
            lab = offline.OfflineLab.create(Path(td) / "native")
            intent = lab.candidate("revoke-gap")
            seen = {"update_ref": False}
            original = lab.git

            def wrapped(*args, **kwargs):
                if args and args[0] == "update-ref":
                    # This is after attempt()'s last pre-git observe().
                    lab.set_provider(phase="NOT_ADMITTED", ttl=0, revision=99)
                    seen["update_ref"] = True
                return original(*args, **kwargs)

            lab.git = wrapped
            result = lab.attempt(intent)
            self.assertTrue(seen["update_ref"], _GAP_REVOKE)
            self.assertEqual(lab.remote_sha(), intent.expected, _GAP_REVOKE)
            self.assertNotEqual(result, "COMMITTED_READBACK", _GAP_REVOKE)


def _guest_main(argv: list[str]) -> int:
    mode = argv[1]
    if mode == "--guest-sink" and len(argv) == 4:
        return _guest_sink(argv[2], argv[3])
    if mode == "--guest-request" and len(argv) == 3:
        return _guest_request(argv[2])
    if mode == "--guest-issued" and len(argv) == 2:
        return _guest_issued()
    if mode == "--guest-fake-ack" and len(argv) == 3:
        return _guest_fake_ack(argv[2])
    if mode == "--guest-hold" and len(argv) == 2:
        return _guest_hold()
    print("SKIP_NEEDS_GUEST", flush=True)
    return 2


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("--guest-"):
        raise SystemExit(_guest_main(sys.argv))
    unittest.main(verbosity=2)
