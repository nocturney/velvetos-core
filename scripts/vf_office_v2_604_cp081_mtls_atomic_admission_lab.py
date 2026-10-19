#!/usr/bin/env python3
"""CP081: disposable real mTLS/RBAC etcd atomic admit/revoke (NO Git or model).

This is a provider-only, nonroot lab. It does NOT prove cross-store atomicity,
OS-separated sink, canonical issuer authority or authenticated GitHub effects.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time
from threading import Barrier
import uuid

import vf_office_v2_604_real_etcd_mtls_rbac_identity_lab as identity

SCHEMA = "velvetos.office-v2.604.cp081.real-mtls-atomic-admission.lab.v1"
ENV = "VF604_CP081_DISPOSABLE_GUEST_ONLY"
PERMIT = "VF604_CP081_EXPLICIT_NO_GITHUB_TEST"
PIN_IDENTITY = "7fbd63b9f34ae8a4a465c6f2e78ea7ed89dd105650626712b4a080e58d75c299"
PIN_ETCD = "117cc09981c0f1eb378e7520be6969756c2d6a762f376944e53f7bc9800c0c59"
PIN_CTL = "de07257495499384f91f028dbc0c8e0394e0bd572b728ac486bbadbfa1cdf275"

class Denied(RuntimeError):
    pass

def require(ok: bool, name: str) -> None:
    if not ok:
        raise Denied(name)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def configuration_guard(etcd: Path, ctl: Path) -> None:
    require(sys.platform == "linux" and platform.machine() == "aarch64",
            "DISPOSABLE_LINUX_ARM64_ONLY")
    require(os.geteuid() != 0 and os.environ.get(ENV) == PERMIT,
            "ROOTLESS_EXPLICIT_LAB_GATE_REQUIRED")
    require(Path("/run/containerd/containerd.sock").is_socket(),
            "EXISTING_DISPOSABLE_COLIMA_PROFILE_REQUIRED")
    require(not any(os.getenv(k) for k in
        ("GH_TOKEN", "GITHUB_TOKEN", "GIT_ASKPASS", "SSH_AUTH_SOCK",
         "AWS_ACCESS_KEY_ID", "GOOGLE_APPLICATION_CREDENTIALS")),
        "AMBIENT_REMOTE_CREDENTIALS_REFUSED")
    require(sha(Path(identity.__file__)) == PIN_IDENTITY, "IDENTITY_HELPER_PIN_DRIFT")
    require(sha(etcd) == PIN_ETCD and sha(ctl) == PIN_CTL,
            "PINNED_OFFICIAL_ETCD_3615_BINARIES_REQUIRED")

def init_roles(e, owner: str, gen: str, intent: str, ref: str) -> None:
    for command in (
        ("user", "add", "root", "--no-password"),
        ("role", "add", "root"),
        ("user", "grant-role", "root", "root"),
        ("role", "add", "cp081-sink"),
        ("role", "grant-permission", "cp081-sink", "read", owner),
        ("role", "grant-permission", "cp081-sink", "read", gen),
        ("role", "grant-permission", "cp081-sink", "read", ref),
        ("role", "grant-permission", "cp081-sink", "readwrite", intent),
        ("user", "add", "vf604-sink", "--no-password"),
        ("user", "grant-role", "vf604-sink", "cp081-sink"),
        ("role", "add", "cp081-worker"),
        ("role", "grant-permission", "cp081-worker", "read", owner),
        ("user", "add", "vf604-worker", "--no-password"),
        ("user", "grant-role", "vf604-worker", "cp081-worker"),
        ("auth", "enable"),
    ):
        e.ctl_ok("root", *command)

def prepare(e, prefix: str, name: str, ttl: int = 25):
    root = prefix + name + "/"
    keys = {k: root + k for k in ("owner", "generation", "intent", "task", "host", "gpu", "ref")}
    lease = int(json.loads(e.ctl_ok("root", "lease", "grant", str(ttl)))["ID"])
    require(lease > 0, "REAL_ETCD_LEASE_REQUIRED")
    e.ctl_ok("root", "put", keys["generation"], "ACTIVE")
    e.ctl_ok("root", "put", keys["owner"], "owner-test-1", "--lease=" + format(lease, "x"))
    row = e.cli_range("root", keys["owner"])
    require(row is not None and row["value"] == "owner-test-1" and row["lease"] == lease,
            "REAL_LEASED_OWNER_READBACK_REQUIRED")
    keys["modrev"] = row["mod_revision"]
    return keys

def admit(e, k: dict) -> bool:
    conditions = [
        f'value("{k["generation"]}") = "ACTIVE"',
        f'value("{k["owner"]}") = "owner-test-1"',
        f'mod("{k["owner"]}") = "{k["modrev"]}"',
    ] + [f'version("{k[x]}") = "0"' for x in
         ("intent", "task", "host", "gpu", "ref")]
    operations = [
        f'put "{k["generation"]}" "COMMIT_ADMITTED"',
        f'put "{k["intent"]}" "COMMIT_ADMITTED"',
    ] + [f'put "{k[x]}" "RESERVED"' for x in ("task", "host", "gpu", "ref")]
    return e.cli_txn("root", conditions, operations)

def revoke_first(e, k: dict) -> bool:
    return e.cli_txn("root",
        [f'value("{k["generation"]}") = "ACTIVE"'],
        [f'put "{k["generation"]}" "REVOKE_REQUESTED_COMMITTED"',
         f'del "{k["owner"]}"'])

def revoke_admitted(e, k: dict) -> bool:
    return e.cli_txn("root",
        [f'value("{k["generation"]}") = "COMMIT_ADMITTED"'],
        [f'put "{k["generation"]}" "DRAINING_ADMITTED"',
         f'del "{k["owner"]}"'])

def native(etcd: Path, ctl: Path) -> dict:
    configuration_guard(etcd, ctl)
    identity.PINNED_ETCD, identity.PINNED_CTL = PIN_ETCD, PIN_CTL
    os.umask(0o077)
    cases: list[str] = []
    def yes(name: str, condition: bool) -> None:
        require(condition is True, "CASE_FAILED_" + name)
        cases.append(name)
    with tempfile.TemporaryDirectory(prefix="vf604-cp081-", dir="/tmp") as t:
        root = Path(t)
        root.chmod(0o700)
        e = identity.AuthenticatedEtcd(root, etcd, ctl)
        try:
            e.start()
            prefix = "/vf604/cp081/synthetic/" + uuid.uuid4().hex + "/"
            a = prepare(e, prefix, "admitted-first")
            init_roles(e, a["owner"], a["generation"], a["intent"], a["ref"])
            yes("live-synthetic-owner-with-genuine-etcd-lease",
                e.cli_range("worker", a["owner"])["lease"] > 0)
            identity.assert_cli_denied(e, "worker", "put", a["intent"], "FORGED")
            identity.assert_cli_denied(e, "sink", "put", a["owner"], "FORGED")
            identity.assert_cli_denied(e, "outsider", "get", a["owner"])
            yes("separate-mtls-roles-deny-worker-sink-and-outsider-writes", True)

            yes("atomic-admission-wins-before-revoke", admit(e, a))
            yes("single-atomic-grant-blocks-duplicate", not admit(e, a))
            yes("sink-only-observes-durable-unleased-intent",
                e.cli_range("sink", a["intent"])["value"] == "COMMIT_ADMITTED"
                and e.cli_range("root", a["intent"])["lease"] == 0)
            yes("admitted-revoke-starts-drain-not-immediate-release",
                revoke_admitted(e, a)
                and e.cli_range("root", a["generation"])["value"] == "DRAINING_ADMITTED"
                and e.cli_range("root", a["ref"])["value"] == "RESERVED")
            b = prepare(e, prefix, "revoked-first")
            yes("revoke-first-committed-by-authenticated-issuer", revoke_first(e, b))
            yes("late-admission-after-revoke-is-refused",
                not admit(e, b) and e.cli_range("root", b["intent"]) is None)

            aba = prepare(e, prefix, "same-value-aba")
            e.ctl_ok("root", "del", aba["owner"])
            lease = int(json.loads(e.ctl_ok("root", "lease", "grant", "25"))["ID"])
            e.ctl_ok("root", "put", aba["owner"], "owner-test-1",
                     "--lease=" + format(lease, "x"))
            yes("same-value-different-modrevision-aba-is-denied",
                not admit(e, aba) and e.cli_range("root", aba["intent"]) is None)

            contenders = {"admit": 0, "revoke": 0}
            for i in range(4):
                k = prepare(e, prefix, "race" + str(i))
                barrier = Barrier(3)
                def run(which: str) -> bool:
                    barrier.wait(timeout=5)
                    return admit(e, k) if which == "admit" else revoke_first(e, k)
                with ThreadPoolExecutor(max_workers=2) as executor:
                    future_a = executor.submit(run, "admit")
                    future_b = executor.submit(run, "revoke")
                    barrier.wait(timeout=5)
                    aw = future_a.result(timeout=12)
                    rw = future_b.result(timeout=12)
                yes("real-raft-exclusive-atomic-admit-or-revoke-" + str(i), aw != rw)
                contenders["admit" if aw else "revoke"] += 1
                yes("race-loser-never-commits-conflicting-intent-" + str(i),
                    (aw and e.cli_range("root", k["intent"]) is not None) or
                    (rw and e.cli_range("root", k["intent"]) is None))

            short = prepare(e, prefix, "ttl-pending", ttl=2)
            yes("real-lease-pending-admission", admit(e, short))
            end = time.monotonic() + 8
            while time.monotonic() < end and e.cli_range("root", short["owner"]) is not None:
                time.sleep(0.16)
            yes("ttl-expiry-retains-unleased-intent-and-reservation",
                e.cli_range("root", short["owner"]) is None
                and e.cli_range("root", short["intent"])["value"] == "COMMIT_ADMITTED"
                and e.cli_range("root", short["ref"])["value"] == "RESERVED")
        finally:
            e.stop()
    return {
        "schema": SCHEMA, "status": "PASS_REAL_MTLS_RBAC_ATOMIC_PROVIDER_LAB_ONLY",
        "security_admission": "RED", "cases": cases, "case_count": len(cases),
        "disposable_fixture_id_sha256": hashlib.sha256(prefix.encode("utf-8")).hexdigest(),
        "real_etcd_mtls_rbac": True, "real_etcd_atomic_issuer_transactions": True,
        "real_provider_race_rounds": 4, "race_winners": contenders,
        "unleased_intent_survives_ttl": True, "same_value_aba_denied": True,
        "disposable_guest_rootless": True, "ephemeral_test_ca_destroyed": True,
        "actual_core_issuer_proven": False, "os_separate_sink_proven": False,
        "remote_github_effect_proven": False, "git_or_github_writes": 0,
        "cp058_worker_application_source_executed": False, "production_authority": False,
    }

def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        print(json.dumps({
            "schema": SCHEMA, "status": "OFFLINE_STATIC_ONLY",
            "security_admission": "RED", "real_provider_started": False,
            "git_or_github_writes": 0, "production_authority": False,
        }, sort_keys=True))
        return 0
    if len(argv) != 3 or argv[0] != "--provider-lab":
        raise Denied("EXPLICIT_MODE_REQUIRED")
    result = native(Path(argv[1]), Path(argv[2]))
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (Denied, OSError, ValueError, RuntimeError, KeyError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":type(exc).__name__,
                          "security_admission":"RED","git_or_github_writes":0}))
        raise SystemExit(2)
