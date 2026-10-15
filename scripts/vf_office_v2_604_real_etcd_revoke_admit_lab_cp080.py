#!/usr/bin/env python3
"""CP080: disposable real-etcd transaction ordering + native local Git lab.

Only explicit --provider-lab (separate env gate), Linux arm64, nonroot and
pinned offline etcd binaries. No remote Git, no live GitHub, no user data,
no autonomous agent, no CP058 model-generated source execution.
"""
from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from threading import Barrier

SCHEMA = "velvetos.office-v2.604.cp080.real-etcd-txn-localgit.lab.v1"
ENV = "VF604_CP080_DISPOSABLE_LOOPBACK_ONLY"
PERMIT = "VF604_CP080_EXPLICIT_NO_GITHUB_LAB"
TOOLS = Path("/tmp/vf604-cp077-tools-20261015/etcd-v3.6.15-linux-arm64")
PIN_ETCD = "117cc09981c0f1eb378e7520be6969756c2d6a762f376944e53f7bc9800c0c59"
PIN_CTL = "de07257495499384f91f028dbc0c8e0394e0bd572b728ac486bbadbfa1cdf275"
REF = "refs/heads/cp080-local-only"
PROVIDER_USER = "synthetic-G7"


class Denied(RuntimeError):
    pass


def require(v: bool, message: str) -> None:
    if not v:
        raise Denied(message)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class RealLab:
    def __init__(self) -> None:
        require(sys.platform == "linux" and platform.machine() == "aarch64", "LINUX_ARM64_GUEST_REQUIRED")
        require(os.geteuid() != 0 and os.environ.get(ENV) == PERMIT, "EXPLICIT_ROOTLESS_LAB_GATE_REQUIRED")
        for k in ("GH_TOKEN", "GITHUB_TOKEN", "GIT_ASKPASS", "SSH_AUTH_SOCK", "AWS_ACCESS_KEY_ID"):
            require(not os.environ.get(k), "AMBIENT_CREDENTIAL_PRESENT_" + k)
        require(sha256(TOOLS / "etcd") == PIN_ETCD and sha256(TOOLS / "etcdctl") == PIN_CTL,
                "EXACT_PINNED_ETCD_BINARY_REQUIRED")
        self.root = Path(tempfile.mkdtemp(prefix="vf604-cp080-", dir="/tmp"))
        self.root.chmod(0o700)
        (self.root / ".vf604-cp080-disposable").write_text("delete only this fixture\n")
        self.server = None
        self.env = {"PATH": "/usr/bin:/bin", "HOME": str(self.root), "LANG": "C",
                    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
                    "GIT_ALLOW_PROTOCOL": "", "GIT_TERMINAL_PROMPT": "0",
                    "GIT_AUTHOR_NAME": "CP080 Offline Lab", "GIT_AUTHOR_EMAIL": "cp080@example.invalid",
                    "GIT_COMMITTER_NAME": "CP080 Offline Lab", "GIT_COMMITTER_EMAIL": "cp080@example.invalid",
                    "ETCDCTL_API": "3"}
        self.client_port = port()
        self.peer_port = port()
        require(self.client_port != self.peer_port, "PORT_COLLISION")
        self.endpoint = f"http://127.0.0.1:{self.client_port}"
        self.base = f"/vf604/cp080/{self.root.name}"
        self.local_git = self.root / "local.git"
        self.cases: list[str] = []
        self.race_winners = {"admission_first": 0, "revoke_first": 0}
        self.negative_legacy_local_ref_observed = False

    def close(self) -> None:
        if self.server is not None:
            self.server.terminate()
            try:
                self.server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server.kill()
                self.server.wait(timeout=5)
            self.server = None
        require(self.root.parent == Path("/tmp") and self.root.name.startswith("vf604-cp080-")
                and (self.root / ".vf604-cp080-disposable").is_file(), "CLEANUP_SENTINEL_REQUIRED")
        shutil.rmtree(self.root)

    def exec(self, argv: list[str], *, data: str | None = None, timeout: float = 8) -> subprocess.CompletedProcess[str]:
        p = subprocess.run(argv, input=data, capture_output=True, text=True,
                           timeout=timeout, env=self.env, cwd=str(self.root))
        require(p.returncode == 0, "CHILD_FAILED_" + str(p.returncode) + ":" + p.stderr[-400:])
        return p

    def ctl(self, *args: str, input_text: str | None = None) -> dict:
        argv = [str(TOOLS / "etcdctl"), "--endpoints", self.endpoint, "-w", "json", *args]
        response = self.exec(argv, data=input_text)
        try:
            obj = json.loads(response.stdout)
        except json.JSONDecodeError as exc:
            raise Denied("NOT_JSON_ETCD_RESPONSE:" + response.stdout[-300:]) from exc
        require(isinstance(obj, dict), "ETCD_RESPONSE_NOT_OBJECT")
        return obj

    def boot(self) -> None:
        name = "vf604-cp080"
        peer = f"http://127.0.0.1:{self.peer_port}"
        log = (self.root / "etcd.log").open("w")
        argv = [str(TOOLS / "etcd"), "--name", name, "--data-dir", str(self.root / "data"),
                "--listen-client-urls", self.endpoint, "--advertise-client-urls", self.endpoint,
                "--listen-peer-urls", peer, "--initial-advertise-peer-urls", peer,
                "--initial-cluster", f"{name}={peer}", "--initial-cluster-state", "new",
                "--logger", "zap", "--log-level", "error"]
        self.server = subprocess.Popen(argv, env=self.env, cwd=str(self.root),
                                       stdout=log, stderr=subprocess.STDOUT)
        log.close()
        for _ in range(60):
            if self.server.poll() is not None:
                raise Denied("ETCD_EXITED_PREMATURELY")
            try:
                self.exec([str(TOOLS / "etcdctl"), "--endpoints", self.endpoint, "endpoint", "health"])
                break
            except (Denied, subprocess.TimeoutExpired):
                time.sleep(0.15)
        else:
            raise Denied("REAL_ETCD_NOT_HEALTHY")
        self.init_local_git()

    def txn(self, compares: list[str], then: list[str], otherwise: list[str] | None = None) -> bool:
        # etcdctl txn requires an empty line after each section, including else.
        script = "\n".join(compares) + "\n\n" + "\n".join(then) + "\n\n" + "\n".join(otherwise or []) + "\n\n"
        result = self.ctl("txn", input_text=script)
        require("header" in result and result.get("succeeded", False) in (True, False),
                "ETCD_TXN_INVALID_RESPONSE")
        # etcdctl/proto3 omits the default false field in JSON responses.
        return result.get("succeeded", False) is True

    def put(self, key: str, value: str, *, lease: int | None = None) -> None:
        args = ["put", key, value]
        if lease is not None:
            args += ["--lease=" + format(lease, "x")]
        self.ctl(*args)

    def get(self, key: str) -> tuple[str, int, int] | None:
        got = self.ctl("get", key)
        rows = got.get("kvs", [])
        require(isinstance(rows, list) and len(rows) <= 1, "ETCD_KEY_RESULT_INVALID")
        if not rows:
            return None
        row = rows[0]
        require(base64.b64decode(row["key"]).decode() == key, "WRONG_ETCD_KEY")
        return (base64.b64decode(row["value"]).decode(),
                int(row.get("mod_revision", 0)), int(row.get("lease", 0)))

    def lease(self, ttl: int = 30) -> int:
        got = self.ctl("lease", "grant", str(ttl))
        ident = int(got["ID"])
        require(ident > 0, "ETCD_LEASE_ID_WRONG")
        return ident

    def keys(self, name: str, *, resource: str | None = None) -> dict[str, str]:
        root = self.base + "/" + name
        shared = self.base + "/resources/" + (resource or name)
        return {"gen": root + "/generation", "owner": root + "/owner",
                "intent": root + "/intent", "task": shared + "/task",
                "host": shared + "/host", "gpu": shared + "/gpu",
                "ref": shared + "/ref"}

    def prepare(self, name: str, *, ttl: int = 30, resource: str | None = None) -> dict[str, str]:
        k = self.keys(name, resource=resource)
        self.put(k["gen"], "ACTIVE")
        lease = self.lease(ttl)
        self.put(k["owner"], PROVIDER_USER, lease=lease)
        read = self.get(k["owner"])
        require(read is not None and read[2] == lease, "REAL_LEASE_NOT_ATTACHED")
        # Pin the real provider revision; a re-created owner with the same value
        # is NOT the owner that received this grant.
        k["owner_modrev"] = str(read[1])
        return k

    def admit(self, k: dict[str, str]) -> bool:
        cmp = [f'value("{k["gen"]}") = "ACTIVE"',
               f'value("{k["owner"]}") = "{PROVIDER_USER}"',
               f'mod("{k["owner"]}") = "{k["owner_modrev"]}"']
        cmp += [f'version("{k[x]}") = "0"' for x in ("intent", "task", "host", "gpu", "ref")]
        ops = [f'put "{k["gen"]}" "COMMIT_ADMITTED"',
               f'put "{k["intent"]}" "COMMIT_ADMITTED"']
        ops += [f'put "{k[x]}" "RESERVED"' for x in ("task", "host", "gpu", "ref")]
        return self.txn(cmp, ops)

    def revoke_first(self, k: dict[str, str]) -> bool:
        return self.txn([f'value("{k["gen"]}") = "ACTIVE"'],
                        [f'put "{k["gen"]}" "REVOKE_REQUESTED_COMMITTED"',
                         f'del "{k["owner"]}"'])

    def revoke_admitted(self, k: dict[str, str]) -> bool:
        return self.txn([f'value("{k["gen"]}") = "COMMIT_ADMITTED"'],
                        [f'put "{k["gen"]}" "DRAINING_ADMITTED"',
                         f'del "{k["owner"]}"'])

    def send_start(self, k: dict[str, str]) -> bool:
        return self.txn([f'value("{k["intent"]}") = "COMMIT_ADMITTED"'],
                        [f'put "{k["intent"]}" "GIT_CALL_STARTED"'])

    def freeze(self, k: dict[str, str]) -> bool:
        return self.txn([f'value("{k["intent"]}") = "GIT_CALL_STARTED"'],
                        [f'put "{k["intent"]}" "FROZEN_UNKNOWN"'])

    def terminal(self, k: dict[str, str]) -> bool:
        return self.txn([f'value("{k["intent"]}") = "GIT_CALL_STARTED"'],
                        [f'put "{k["intent"]}" "VERIFIED_LOCAL_EFFECT"'])

    def effective(self, k: dict[str, str]) -> bool:
        return self.txn([f'value("{k["gen"]}") = "DRAINING_ADMITTED"',
                         f'value("{k["intent"]}") = "VERIFIED_LOCAL_EFFECT"'],
                        [f'put "{k["gen"]}" "REVOKED_EFFECTIVE"',
                         *[f'del "{k[x]}"' for x in ("task", "host", "gpu", "ref")]])

    def effective_no_work(self, k: dict[str, str]) -> bool:
        return self.txn([f'value("{k["gen"]}") = "REVOKE_REQUESTED_COMMITTED"',
                         f'version("{k["intent"]}") = "0"',
                         f'version("{k["ref"]}") = "0"'],
                        [f'put "{k["gen"]}" "REVOKED_EFFECTIVE"'])

    def successor(self, k: dict[str, str]) -> bool:
        return self.txn([f'version("{k["ref"]}") = "0"'],
                        [f'put "{k["ref"]}" "SUCCESSOR_RESERVED"'])

    def git(self, *args: str, data: str | None = None) -> str:
        command = ["/usr/bin/git", "--git-dir", str(self.local_git), *args]
        return self.exec(command, data=data).stdout.strip()

    def commit(self, data: str, parent: str | None = None) -> str:
        blob = self.git("hash-object", "-w", "--stdin", data=data)
        tree = self.git("mktree", data=f"100644 blob {blob}\tproof.txt\n")
        args = ["commit-tree", tree]
        if parent:
            args += ["-p", parent]
        return self.git(*args, data="CP080 disposable local commit\n")

    def init_local_git(self) -> None:
        self.exec(["/usr/bin/git", "init", "--quiet", "--bare", str(self.local_git)])
        self.git_initial = self.commit("CP080_INITIAL\n")
        self.git_candidate = self.commit("CP080_CANDIDATE\n", self.git_initial)
        self.git("update-ref", REF, self.git_initial)
        require(self.git("remote") == "", "GIT_REMOTE_PRESENT")

    def local_effect(self) -> None:
        self.git("update-ref", REF, self.git_candidate, self.git_initial)
        require(self.git("rev-parse", REF) == self.git_candidate, "LOCAL_GIT_REF_NOT_VERIFIED")

    def assert_case(self, label: str, condition: bool) -> None:
        require(condition, "CASE_FAILED_" + label)
        self.cases.append(label)

    def suite(self) -> dict:
        self.boot()

        k = self.prepare("admitted-first")
        self.assert_case("real-etcd-admission-then-revoke", self.admit(k) and self.revoke_admitted(k))
        self.assert_case("ack-denied-before-terminal", not self.effective(k) and not self.successor(k))
        self.assert_case("one-send-marker", self.send_start(k) and not self.send_start(k))
        self.local_effect()  # Native local Git AFTER real etcd committed revoke request: permitted Option A.
        self.assert_case("late-local-effect-after-request-but-before-effective",
                         self.terminal(k) and self.effective(k) and self.get(k["gen"])[0] == "REVOKED_EFFECTIVE")

        k = self.prepare("revoked-first")
        self.assert_case("real-etcd-revoke-before-admission", self.revoke_first(k) and not self.admit(k)
                         and self.get(k["intent"]) is None and self.get(k["owner"]) is None)
        self.assert_case("effective-without-admitted-work", self.effective_no_work(k))

        k = self.prepare("unknown-freeze")
        require(self.admit(k) and self.send_start(k) and self.freeze(k) and self.revoke_admitted(k), "FREEZE_SETUP")
        self.assert_case("unknown-blocks-ack-successor-and-retry",
                         not self.effective(k) and not self.successor(k) and not self.send_start(k))
        self.assert_case("durable-unleased-intent-after-revoke", self.get(k["intent"])[0] == "FROZEN_UNKNOWN"
                         and self.get(k["intent"])[2] == 0 and self.get(k["owner"]) is None)

        k = self.prepare("same-resource-A", resource="contended")
        other = self.prepare("same-resource-B", resource="contended")
        self.assert_case("multi-key-resource-reservation-fences-other-task",
                         self.admit(k) and not self.admit(other)
                         and self.get(other["intent"]) is None and
                         all(self.get(k[x]) is not None for x in ("task", "host", "gpu", "ref")))

        k = self.prepare("ttl-before-admit", ttl=2)
        until = time.monotonic() + 8
        while self.get(k["owner"]) is not None and time.monotonic() < until:
            time.sleep(0.2)
        self.assert_case("real-etcd-lease-expiry-before-admission-denies",
                         self.get(k["owner"]) is None and not self.admit(k))
        self.put(k["owner"], PROVIDER_USER, lease=self.lease(30))
        self.assert_case("expired-owner-same-value-ABA-denied", not self.admit(k))

        k = self.prepare("same-value-owner-rebind")
        self.ctl("del", k["owner"])
        self.put(k["owner"], PROVIDER_USER, lease=self.lease(30))
        self.assert_case("deleted-owner-recreated-with-same-value-denied", not self.admit(k))

        k = self.prepare("ttl-after-admit", ttl=2)
        require(self.admit(k), "TTL_AFTER_ADMIT_SETUP")
        until = time.monotonic() + 8
        while self.get(k["owner"]) is not None and time.monotonic() < until:
            time.sleep(0.2)
        require(self.get(k["owner"]) is None, "TTL_DID_NOT_EXPIRE")
        self.assert_case("real-etcd-lease-expiry-does-not-delete-intent",
                         self.get(k["intent"])[0] == "COMMIT_ADMITTED" and self.get(k["intent"])[2] == 0
                         and self.get(k["ref"]) is not None)
        require(self.revoke_admitted(k), "TTL_AFTER_ADMIT_REVOKE_SETUP")
        self.assert_case("ttl-after-admit-blocks-premature-effective", not self.effective(k))

        contenders = 12
        for i in range(contenders):
            k = self.prepare("race-" + str(i))
            gate = Barrier(3)
            def race(f):
                gate.wait(timeout=8)
                return f(k)
            with ThreadPoolExecutor(max_workers=2) as pool:
                admit = pool.submit(race, self.admit)
                revoke = pool.submit(race, self.revoke_first)
                gate.wait(timeout=8)
                grant, denied = admit.result(timeout=8), revoke.result(timeout=8)
            require(grant != denied, "REAL_ETCD_RACE_MUST_HAVE_ONE_WINNER")
            self.race_winners["admission_first" if grant else "revoke_first"] += 1
            if grant:
                require(self.get(k["gen"])[0] == "COMMIT_ADMITTED"
                        and self.get(k["intent"])[0] == "COMMIT_ADMITTED"
                        and self.get(k["ref"])[0] == "RESERVED", "RACE_GRANT_PARTIAL")
            else:
                require(self.get(k["gen"])[0] == "REVOKE_REQUESTED_COMMITTED"
                        and self.get(k["intent"]) is None and self.get(k["ref"]) is None,
                        "RACE_REVOKE_PARTIAL")
        self.assert_case("12-concurrent-real-quorum-txns-exactly-one-winner", sum(self.race_winners.values()) == contenders)

        k = self.prepare("send-race")
        require(self.admit(k), "SEND_RACE_SETUP")
        gate = Barrier(3)
        def run_send():
            gate.wait(timeout=8)
            return self.send_start(k)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a, b = pool.submit(run_send), pool.submit(run_send)
            gate.wait(timeout=8)
            first, second = a.result(timeout=8), b.result(timeout=8)
        self.assert_case("real-etcd-single-send-start-on-double-dispatch", first != second
                         and self.get(k["intent"])[0] == "GIT_CALL_STARTED")

        k = self.prepare("late-unfenced-legacy")
        require(self.revoke_first(k) and self.effective_no_work(k), "LEGACY_WITNESS_SETUP")
        # THIS IS THE INTENTIONALLY UNSAFE BYPASS: raw local Git without admission.
        # The separate fresh local repo is still at initial; the attack changes it.
        self.git("update-ref", REF, self.git_initial, self.git_candidate)
        self.local_effect()
        self.negative_legacy_local_ref_observed = self.git("rev-parse", REF) == self.git_candidate
        self.assert_case("known-unsafe-cp077-unfenced-local-git-witness",
                         self.negative_legacy_local_ref_observed)

        return {"schema": SCHEMA, "status": "PASS_REAL_ETCD_QUORUM_TXN_LOCAL_GIT_LAB_ONLY",
                "security_admission": "RED", "new_test_case_count": len(self.cases),
                "case_names": self.cases, "etcd_binary_sha256": PIN_ETCD,
                "etcdctl_binary_sha256": PIN_CTL, "real_etcd_3_6_15": True,
                "etcd_mtls_or_rbac_in_cp080": False, "real_native_local_git_effect": True,
                "actual_etcd_txn_concurrency_rounds": contenders,
                "etcd_concurrent_winner_counts": self.race_winners,
                "known_unfenced_local_git_after_effective": self.negative_legacy_local_ref_observed,
                "network_binding": "127.0.0.1-only-http-ephemeral", "ephemeral_storage_deleted": "on_process_exit",
                "real_github_remote_effect": False, "real_github_credentials": False,
                "real_multi_host_core_issuer": False, "model_cp058_source_executed": False,
                "production_authority": False}


def main(args: list[str]) -> int:
    if args == ["--selftest"]:
        print(json.dumps({"schema": SCHEMA, "status": "OFFLINE_STATIC_ONLY",
                          "real_etcd_started": False, "remote_github_access": False,
                          "security_admission": "RED"}, sort_keys=True))
        return 0
    if args != ["--provider-lab"]:
        print("DENIED: explicit --provider-lab or --selftest only", file=sys.stderr)
        return 2
    lab = RealLab()
    try:
        result = lab.suite()
        print(json.dumps(result, sort_keys=True))
        return 0
    finally:
        lab.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
