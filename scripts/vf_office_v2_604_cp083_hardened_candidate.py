#!/usr/bin/env python3
"""CP083 disposable joined proof: real mTLS etcd, OS-UID sink, LOCAL Git and SQLite.

Root is a TEST FIXTURE CONTROLLER ONLY inside an existing disposable Linux
Colima guest. The worker is a separate unprivileged UID, without sink keys,
Git or SQLite access. Only the sink can effect a private bare LOCAL ref.
No remote GitHub, cloud token, production authority, real Core issuer,
model-generated worker source, or claim of cross-store atomicity.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import pwd
import select
import shutil
import socket
import sqlite3
import struct
import subprocess
import sys
import tempfile
import time
import uuid

import vf_office_v2_604_cp081_mtls_atomic_admission_lab as cp081
import vf_office_v2_604_cp082_tls_native_git_reconcile_lab as cp082
import vf_office_v2_604_real_etcd_mtls_rbac_identity_lab as identity
import vf_office_v2_604_native_git_crash_reconcile_offline as offline

SCHEMA = "velvetos.office-v2.604.cp083.osuid-mtls-localgit-option-a.v1"
PERMIT_ENV = "VF604_CP083_DISPOSABLE_GUEST_ONLY"
PERMIT_VAL = "VF604_CP083_EXPLICIT_NO_REMOTE"
SINK_UID, WORKER_UID, ATTACKER_UID = 62001, 62002, 62004
CASES = ("normal", "revoke-first", "drain-before", "mid",
         "ack-before", "ack-after", "crash-after")
MAX_MESSAGE = 2048
# Only explicit, fixed values cross from the fixture controller to other UIDs.
# No inherited Python path, cloud credentials, sockets, Git config, or home.
SAFE_ENV = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "LC_ALL": "C",
    "HOME": "/nonexistent",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
}


class Refuse(RuntimeError):
    pass


def need(ok, label):
    if ok is not True:
        raise Refuse(label)


def digest(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def guard(etcd, ctl):
    need(sys.platform == "linux" and platform.machine() == "aarch64",
         "LINUX_ARM64_DISPOSABLE_ONLY")
    need(os.geteuid() == 0 and os.getenv(PERMIT_ENV) == PERMIT_VAL,
         "EXPLICIT_ROOT_FIXTURE_CONTROLLER_ONLY")
    need(Path("/run/containerd/containerd.sock").is_socket(),
         "EXISTING_COLIMA_GUEST_REQUIRED")
    need(not any(os.getenv(k) for k in (
         "GH_TOKEN", "GITHUB_TOKEN", "GIT_ASKPASS", "SSH_AUTH_SOCK",
         "AWS_ACCESS_KEY_ID", "GOOGLE_APPLICATION_CREDENTIALS")),
         "AMBIENT_CREDENTIALS_REFUSED")
    need(digest(etcd) == cp081.PIN_ETCD and digest(ctl) == cp081.PIN_CTL,
         "OFFICIAL_ETCD_BINARIES_PIN_DRIFT")
    need(digest(identity.__file__) == cp081.PIN_IDENTITY,
         "PINNED_IDENTITY_MODULE_DRIFT")
    for uid in (SINK_UID, WORKER_UID, ATTACKER_UID):
        try:
            pwd.getpwuid(uid)
        except KeyError:
            continue
        raise Refuse("FIXTURE_UID_ALREADY_ALLOCATED")
    need(Path(etcd).is_file() and Path(ctl).is_file(),
         "TEST_BINARIES_MISSING")


def drop(uid):
    def cb():
        os.setgroups([])
        os.setgid(uid)
        os.setuid(uid)
    return cb


def socket_exchange(root, payload):
    """One bounded response from the verified sink principal; never blind-retry."""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(3.5)
    try:
        sock.connect(str(Path(root) / "endpoint" / "sink.sock"))
        # Verify the server's *kernel* identity, not a user-supplied JSON claim.
        if sys.platform != "linux" or not hasattr(socket, "SO_PEERCRED"):
            return {"status": "NO_ACK_UNKNOWN"}
        peer_uid = struct.unpack("3i", sock.getsockopt(
            socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[1]
        if peer_uid != SINK_UID:
            return {"status": "NO_ACK_UNKNOWN"}
        sock.sendall((json.dumps(payload, sort_keys=True) + "\n").encode())
        deadline = time.monotonic() + 3.0
        buffer = bytearray()
        while b"\n" not in buffer and len(buffer) <= MAX_MESSAGE:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return {"status": "NO_ACK_UNKNOWN"}
            sock.settimeout(remaining)
            part = sock.recv(min(1024, MAX_MESSAGE + 1 - len(buffer)))
            if not part:
                break
            buffer.extend(part)
        if not buffer or len(buffer) > MAX_MESSAGE or b"\n" not in buffer:
            return {"status": "NO_ACK_UNKNOWN"}
        reply = json.loads(bytes(buffer.split(b"\n", 1)[0]))
        if type(reply) is not dict or type(reply.get("status")) is not str:
            return {"status": "NO_ACK_UNKNOWN"}
        return reply
    except (OSError, ValueError, TypeError, struct.error):
        return {"status": "NO_ACK_UNKNOWN"}
    finally:
        sock.close()


def local_cert_observation(root):
    cfg = json.loads((Path(root) / "sink" / "provider.json").read_text())
    need(cfg["schema"] == SCHEMA and cfg["case"] in CASES,
         "PROVIDER_CONFIG_NOT_SCOPED")
    def row(name):
        cmd = [cfg["etcdctl"], "--endpoints", cfg["endpoint"],
               "--cacert", cfg["ca"], "--cert", cfg["cert"],
               "--key", cfg["key"], "-w", "json", "get", cfg[name]]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True,
                               env=SAFE_ENV, timeout=7)
            if p.returncode:
                raise ValueError("REAL_ETCD_MTLS_OBSERVATION_UNAVAILABLE")
            value = json.loads(p.stdout)
            kvs = value.get("kvs", [])
            if not kvs:
                return None
            if len(kvs) != 1:
                raise ValueError("WIDE_OBSERVATION_REFUSED")
            kv = kvs[0]
            if base64.b64decode(kv["key"]).decode() != cfg[name]:
                raise ValueError("WRONG_PROVIDER_KEY")
            return {"value": base64.b64decode(kv["value"]).decode(),
                    "lease": int(kv.get("lease", 0)),
                    "mod_revision": int(kv["mod_revision"])}
        except (OSError, KeyError, TypeError, ValueError,
                subprocess.TimeoutExpired) as exc:
            raise ValueError("AUTHENTICATED_PROVIDER_UNAVAILABLE") from exc
    owner, gen, intent, reserved = (
        row("owner"), row("generation"), row("intent"), row("ref"))
    valid = bool(owner and owner["value"] == "owner-test-1"
        and owner["lease"] > 0
        and owner["mod_revision"] == cfg["owner_modrev"]
        and gen and gen["value"] == "COMMIT_ADMITTED"
        and intent and intent["value"] == "COMMIT_ADMITTED"
        and intent["lease"] == 0
        and reserved and reserved["value"] == "RESERVED"
        and reserved["lease"] == 0)
    return {
        "actor": "worker-a" if valid else "",
        "epoch": 7,
        "phase": "ACTIVE" if valid else "NOT_ADMITTED",
        "ttl_seconds": 1 if valid else 0,
        "revision": gen["mod_revision"] if gen else 1,
    }


def serve(root, case):
    need(os.geteuid() == SINK_UID and case in CASES,
         "NOT_PRIVILEGED_SINK_UID")
    root = Path(root)
    fixture = root / "sink" / "native"
    lab = offline.OfflineLab(fixture) if fixture.exists() else (
        offline.OfflineLab.create(fixture))
    lab.observe = lambda: local_cert_observation(root)
    previous = lab.status(case)
    if previous and previous["state"] == "EFFECT_IN_FLIGHT":
        need(lab.mark_unknown(case, "RESTART_FOUND_IN_FLIGHT") ==
             "UNKNOWN_EFFECT_RECONCILE", "RESTART_FREEZE_FAILED")
    endpoint = root / "endpoint" / "sink.sock"
    if endpoint.exists():
        raise Refuse("STALE_SOCKET_REFUSED")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(endpoint))
    endpoint.chmod(0o666)  # endpoint public, SO_PEERCRED checks identity
    server.listen(8)
    server.settimeout(0.5)
    print("READY", flush=True)
    stop = False
    try:
        while not stop:
            try:
                c, _ = server.accept()
            except socket.timeout:
                continue
            with c:
                uid = struct.unpack("3i", c.getsockopt(
                    socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[1]
                # Reject unrelated kernel principals before accepting any frame.
                if uid not in (0, WORKER_UID):
                    try:
                        c.sendall((json.dumps({
                            "status": "DENIED_OS_PRINCIPAL_OR_TASK_SCOPE",
                        }) + "\n").encode())
                    except OSError:
                        pass
                    continue
                # A per-recv timeout alone permits a slow-drip peer to hold
                # this single-threaded sink for up to MAX_MESSAGE frames.
                # Bound the *whole frame* with one monotonic deadline.
                c.settimeout(2.0)
                deadline = time.monotonic() + 2.0
                incoming = bytearray()
                while b"\n" not in incoming and len(incoming) <= MAX_MESSAGE:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    c.settimeout(remaining)
                    try:
                        bit = c.recv(512)
                    except socket.timeout:
                        break
                    if not bit:
                        break
                    incoming.extend(bit)
                try:
                    need(b"\n" in incoming and len(incoming) <= MAX_MESSAGE,
                         "MESSAGE_SIZE_REFUSED")
                    req = json.loads(bytes(incoming.split(b"\n", 1)[0]))
                    need(type(req) is dict and set(req) == {"action", "case"},
                         "EXACT_PROTOCOL_FIELDS_REQUIRED")
                    action = req["action"]
                    if uid == 0 and action in ("snapshot", "shutdown"):
                        if action == "shutdown":
                            out = {"status": "ROOT_CONTROL_SHUTDOWN"}
                            stop = True
                        else:
                            out = {"status": "ROOT_CONTROL_SNAPSHOT",
                                   "head": lab.remote_sha(),
                                   "frozen": lab.frozen(),
                                   "record": lab.status(case)}
                    elif uid == WORKER_UID and action == "effect" and (
                            req["case"] == case):
                        candidate = lab.candidate(case)
                        if case == "mid":
                            original = lab.git
                            def native_mid(*args, **kwargs):
                                p = original(*args, **kwargs)
                                if args and args[0] == "update-ref":
                                    need(p.returncode == 0, "NATIVE_LOCAL_GIT_FAILED")
                                    ready = root / "endpoint" / "after-git.ready"
                                    resume = root / "endpoint" / "revoke.done"
                                    ready.write_text("LOCAL_NATIVE_GIT_ALREADY_WROTE\n")
                                    limit = time.monotonic() + 10
                                    while not resume.is_file() and time.monotonic() < limit:
                                        time.sleep(0.03)
                                    need(resume.is_file(), "REVOCATION_TIMEOUT")
                                return p
                            lab.git = native_mid
                        fault = {
                            "ack-before": "lost_ack_before_git",
                            "ack-after": "lost_ack_after_git",
                            "crash-after": "crash_after_native_git",
                        }.get(case, "none")
                        result = lab.attempt(candidate, fault=fault)
                        # Deliberate lost transport ACK with durable freeze.
                        if (case in ("ack-before", "ack-after") and
                                result == "UNKNOWN_EFFECT_RECONCILE"):
                            # Only the first uncertain attempt drops the ACK.
                            # Frozen replays must receive an explicit refusal.
                            continue
                        out = {"status": result}
                    else:
                        out = {"status": "DENIED_OS_PRINCIPAL_OR_TASK_SCOPE"}
                except (Refuse, ValueError, OSError, KeyError, TypeError,
                        sqlite3.Error) as exc:
                    out = {"status": "FAIL_CLOSED",
                           "reason": type(exc).__name__}
                try:
                    c.sendall((json.dumps(out, sort_keys=True) + "\n").encode())
                except OSError:
                    pass
    finally:
        server.close()
        try:
            endpoint.unlink()
        except FileNotFoundError:
            pass


def probe(root):
    """Executed under the worker's real numeric Linux UID."""
    need(os.geteuid() == WORKER_UID, "PROBE_NOT_WORKER_UID")
    root = Path(root)
    paths = {
        "private_mtls_key": root / "sink" / "tls" / "sink.key",
        "native_git_head": root / "sink" / "native" / "scratch.git" / "HEAD",
        "durable_journal": root / "sink" / "native" / "receipt.sqlite3",
    }
    result = {}
    for label, file in paths.items():
        try:
            with file.open("rb"):
                result[label + "_denied"] = False
        except PermissionError:
            result[label + "_denied"] = True
        except OSError:
            result[label + "_denied"] = False
    print(json.dumps(result, sort_keys=True), flush=True)


def child_json(root, uid, msg):
    child = subprocess.run(
        ["/usr/bin/python3", "-B", os.path.realpath(__file__),
         "_request", str(root)],
        input=json.dumps(msg) + "\n", text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=SAFE_ENV, preexec_fn=drop(uid), timeout=13)
    need(child.returncode == 0, "WORKER_CALL_FAILED")
    return json.loads(child.stdout.strip())


def child_start(root, case):
    return subprocess.Popen(
        ["/usr/bin/python3", "-B", os.path.realpath(__file__),
         "_request", str(root)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, env=SAFE_ENV,
        preexec_fn=drop(WORKER_UID))


def root_control(root, action):
    return socket_exchange(root, {"action": action, "case": "controller"})


def start_sink(root, case):
    p = subprocess.Popen(
        ["/usr/bin/python3", "-B", os.path.realpath(__file__),
         "_serve", str(root), case],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=SAFE_ENV, preexec_fn=drop(SINK_UID))
    ready, _, _ = select.select([p.stdout], [], [], 12)
    if not ready or p.stdout.readline().strip() != "READY":
        p.kill()
        p.wait(timeout=4)
        raise Refuse("UID_SEPARATED_SINK_DID_NOT_START_" + case)
    return p


def close_sink(root, process):
    if process.poll() is None:
        root_control(root, "shutdown")
        try:
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=4)
    need(process.returncode == 0,
         "SINK_STOPPED_ABNORMALLY")


def setup_case(root, case, e, ctl, k):
    root.mkdir(mode=0o755)
    root.chmod(0o755)  # os.umask(077) otherwise blocks sink traversal
    (root / "sink").mkdir(mode=0o700)
    (root / "endpoint").mkdir(mode=0o755)
    (root / "sink" / "tls").mkdir(mode=0o700)
    for path in (root / "sink", root / "sink" / "tls",
                 root / "endpoint"):
        os.chown(path, SINK_UID, SINK_UID)
    (root / "endpoint").chmod(0o755)  # worker can reach socket, not private data
    for name, src in {
        "ca": e.cert.ca, "sink.crt": e.cert.roles["sink"][0],
        "sink.key": e.cert.roles["sink"][1],
        "etcdctl": ctl,
    }.items():
        target = root / "sink" / "tls" / name
        shutil.copyfile(src, target)
        os.chown(target, SINK_UID, SINK_UID)
        target.chmod(0o700 if name == "etcdctl" else 0o600)
    cfg = {
        "schema": SCHEMA, "case": case, "endpoint": e.url,
        "etcdctl": str(root / "sink" / "tls" / "etcdctl"),
        "ca": str(root / "sink" / "tls" / "ca"),
        "cert": str(root / "sink" / "tls" / "sink.crt"),
        "key": str(root / "sink" / "tls" / "sink.key"),
        "owner": k["owner"], "generation": k["generation"],
        "intent": k["intent"], "ref": k["ref"],
        "owner_modrev": k["modrev"],
    }
    dest = root / "sink" / "provider.json"
    dest.write_text(json.dumps(cfg, sort_keys=True))
    os.chown(dest, SINK_UID, SINK_UID)
    dest.chmod(0o600)


def native(etcd, ctl):
    guard(etcd, ctl)
    os.umask(0o077)
    identity.PINNED_ETCD, identity.PINNED_CTL = cp081.PIN_ETCD, cp081.PIN_CTL
    checks = []
    def yes(label, ok):
        need(ok is True, "FAIL_" + label)
        checks.append(label)
    with tempfile.TemporaryDirectory(prefix="vf604-cp083-", dir="/tmp") as t:
        root = Path(t)
        root.chmod(0o755)
        (root / ".vf604-test-only").write_text("DISPOSABLE_NO_REMOTE\n")
        provider_root = root / "issuer-only"
        provider_root.mkdir(mode=0o700)
        e = identity.AuthenticatedEtcd(provider_root, etcd, ctl)
        e.start()
        try:
            prefix = "/vf604/cp083/synthetic/" + uuid.uuid4().hex + "/"
            for index, case in enumerate(CASES):
                k = cp081.prepare(e, prefix, case, ttl=90)
                if index == 0:
                    cp081.init_roles(e, k["owner"], k["generation"],
                                    k["intent"], k["ref"])
                else:
                    cp082.enable_case_sink_read(e, k)
                if case == "revoke-first":
                    yes(case + "_revoke_committed_before_admit",
                        cp081.revoke_first(e, k))
                    yes(case + "_atomic_admission_denied",
                        not cp081.admit(e, k))
                else:
                    yes(case + "_real_provider_atomic_admit",
                        cp081.admit(e, k))
                fixture = root / case
                setup_case(fixture, case, e, ctl, k)
                identity.assert_cli_denied(e, "sink", "put",
                                           k["owner"], "FORGED_OWNER")
                yes(case + "_restricted_mtls_cannot_issue_owner", True)
                sink = start_sink(fixture, case)
                try:
                    if case == "normal":
                        p = subprocess.run(
                            ["/usr/bin/python3", "-B", os.path.realpath(__file__),
                             "_probe", str(fixture)],
                            stdout=subprocess.PIPE, text=True,
                            env=SAFE_ENV, preexec_fn=drop(WORKER_UID), timeout=6)
                        proof = json.loads(p.stdout)
                        yes("worker_cannot_read_sink_key_git_or_journal",
                            p.returncode == 0 and len(proof) == 3
                            and all(proof.values()))
                        attacker = child_json(fixture, ATTACKER_UID,
                            {"action": "effect", "case": case})
                        yes("attacker_cannot_spoof_worker_uid",
                            attacker["status"] == "DENIED_OS_PRINCIPAL_OR_TASK_SCOPE")
                        wrong = child_json(fixture, WORKER_UID,
                            {"action": "effect", "case": "other-task"})
                        yes("worker_cannot_change_task_scope",
                            wrong["status"] == "DENIED_OS_PRINCIPAL_OR_TASK_SCOPE")
                    if case == "drain-before":
                        yes(case + "_revoke_moves_to_draining",
                            cp081.revoke_admitted(e, k))
                        yes(case + "_ref_reservation_stays",
                            e.cli_range("root", k["ref"])["value"] == "RESERVED")
                    if case == "mid":
                        worker = child_start(fixture, case)
                        worker.stdin.write(json.dumps(
                            {"action": "effect", "case": case}) + "\n")
                        worker.stdin.flush()
                        worker.stdin.close()
                        notice = fixture / "endpoint" / "after-git.ready"
                        until = time.monotonic() + 15
                        while not notice.exists() and time.monotonic() < until:
                            time.sleep(0.025)
                        yes("mid_native_local_git_wrote_before_revoke",
                            notice.exists())
                        yes("mid_real_etcd_revoke_after_native_git",
                            cp081.revoke_admitted(e, k))
                        (fixture / "endpoint" / "revoke.done").write_text(
                            "REAL_ETCD_REVOKED\n")
                        worker.wait(timeout=15)
                        response = json.loads(worker.stdout.read().strip())
                    else:
                        response = child_json(fixture, WORKER_UID,
                            {"action": "effect", "case": case})
                    if case in ("ack-before", "ack-after", "crash-after"):
                        yes(case + "_worker_sees_actual_lost_ack",
                            response["status"] == "NO_ACK_UNKNOWN")
                    elif case == "normal":
                        yes("normal_private_sink_committed_native_local_git",
                            response["status"] == "COMMITTED_READBACK")
                    elif case in ("revoke-first", "drain-before"):
                        yes(case + "_worker_refused_stale_provider",
                            response["status"] == "DENIED_STALE")
                    elif case == "mid":
                        yes("mid_post_native_revoke_is_unknown_not_success",
                            response["status"] == "UNKNOWN_EFFECT_RECONCILE")
                    if case == "crash-after":
                        sink.wait(timeout=8)
                        yes("crash_after_real_git_killed_sink_before_ack",
                            sink.returncode == 92)
                        old_socket = fixture / "endpoint" / "sink.sock"
                        yes("crash_after_stale_unix_socket_is_isolated",
                            old_socket.is_socket())
                        old_socket.unlink()  # dead child only, unique fixture
                        sink = start_sink(fixture, case)
                    snap = root_control(fixture, "snapshot")
                    record = snap["record"]
                    yes(case + "_authoritative_local_readback_available",
                        snap["status"] == "ROOT_CONTROL_SNAPSHOT"
                        and len(snap["head"]) == 40)
                    if case in ("mid", "ack-before", "ack-after",
                                "crash-after"):
                        yes(case + "_durable_unknown_frozen",
                            snap["frozen"] and record["state"] ==
                            "UNKNOWN_EFFECT_RECONCILE")
                        yes(case + "_no_blind_retry",
                            child_json(fixture, WORKER_UID,
                                {"action": "effect", "case": case})["status"] ==
                            "NOT_ADMITTED")
                        yes(case + "_freeze_keeps_git_effect_truth",
                            (snap["head"] == record["expected"])
                            if case == "ack-before" else
                            (snap["head"] == record["candidate"]))
                        close_sink(fixture, sink)
                        sink = start_sink(fixture, case)
                        again = root_control(fixture, "snapshot")
                        yes(case + "_restart_does_not_unlock",
                            again["frozen"] and again["head"] == snap["head"])
                    if case in ("revoke-first", "drain-before"):
                        yes(case + "_never_written_git_ref",
                            snap["record"] is None and not snap["frozen"])
                    if case == "normal":
                        yes("normal_no_unknown_and_single_admitted_effect",
                            record["state"] == "COMMITTED_READBACK"
                            and snap["head"] == record["candidate"]
                            and record["after_sha"] == record["candidate"]
                            and not snap["frozen"])
                        yes("normal_revoke_keeps_reservation",
                            cp081.revoke_admitted(e, k)
                            and e.cli_range("root",k["ref"])["value"] ==
                            "RESERVED")
                        yes("normal_after_drain_blocks_new_request",
                            child_json(fixture, WORKER_UID,
                                {"action":"effect","case":case})["status"] in
                            ("NOT_ADMITTED", "DENIED_STALE")
                            and root_control(fixture, "snapshot")["head"] ==
                            snap["head"])
                finally:
                    if sink.poll() is None:
                        close_sink(fixture, sink)
        finally:
            e.stop()
    return {
        "schema": SCHEMA, "status": "PASS_CP083_TEST_ONLY",
        "checks": checks, "check_count": len(checks),
        "fixture_prefix_sha256": hashlib.sha256(prefix.encode()).hexdigest(),
        "security_admission": "RED",
        "distinct_kernel_os_uids": True,
        "root_test_fixture_controller": True,
        "real_mtls_rbac_provider": True,
        "real_atomic_etcd_admission": True,
        "native_local_bare_git_effect": True,
        "sink_only_tls_key_and_sqlite_git_dac": True,
        "durable_unknown_freeze": True,
        "real_external_github_writes": 0,
        "real_protected_core_issuer": False,
        "remote_github_sink_proven": False,
        "claim_signature_validated": False,
        "two_host_autonomous_coding_proven": False,
        "cross_store_atomicity_proven": False,
        "production_authority": False,
    }


def main(argv):
    if argv == ["--selftest"]:
        # No filesystem mutation, no provider or remote actions.
        need(len(set((0, SINK_UID, WORKER_UID, ATTACKER_UID))) == 4,
             "UID_ASSIGNMENT_NOT_DISTINCT")
        need(CASES.count("mid") == 1 and CASES.count("crash-after") == 1,
             "MANDATORY_FAULT_CASES_MISSING")
        print(json.dumps({"schema": SCHEMA, "status": "OFFLINE_STATIC_ONLY",
              "security_admission": "RED", "provider_started": False,
              "git_effects": 0, "remote_github_writes": 0,
              "production_authority": False}, sort_keys=True))
        return 0
    if len(argv) == 3 and argv[0] == "--disposable-lab":
        print(json.dumps(native(Path(argv[1]), Path(argv[2])),
                         sort_keys=True), flush=True)
        return 0
    if len(argv) == 3 and argv[0] == "_serve":
        serve(argv[1], argv[2])
        return 0
    if len(argv) == 2 and argv[0] == "_probe":
        probe(argv[1])
        return 0
    if len(argv) == 2 and argv[0] == "_request":
        payload = json.loads(sys.stdin.readline(MAX_MESSAGE + 1))
        print(json.dumps(socket_exchange(argv[1], payload), sort_keys=True),
              flush=True)
        return 0
    raise Refuse("EXPLICIT_MODE_REQUIRED")


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (Refuse, OSError, ValueError, KeyError, TypeError,
            RuntimeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "FAIL_CLOSED",
              "reason": str(exc)[:100], "security_admission": "RED",
              "remote_github_writes": 0}), flush=True)
        raise SystemExit(2)
