#!/usr/bin/env python3
"""#604 real ephemeral etcd lease/intent + native LOCAL Git crash LAB.

NOT production. The real etcd server is bound only to loopback, has NO
authentication, and owns an isolated disposable data-dir. A Git bare fixture
has NO remote. This demonstrates that an unleased, provider-owned intent
survives lease expiry and blocks new admission after crashes, while exposing
that Git can STILL accept a late write after lease expiry. Never infer true
credential exclusivity, live GitHub ref protection, cross-store atomicity,
mTLS authorization, or exactly-once.
"""
import base64
from concurrent.futures import ThreadPoolExecutor
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid

SCHEMA = "vf604.etcd-native-localgit-crash-intent.v1"
OFFLINE_REF = "refs/heads/vf604-provider-intent-offline"
OFFLINE_MARKER = ".vf604-etcd-intent-lab-no-remote"
ETCD_SHA256 = "dd2596ab902c23252da55e770cb7f7216522ae5599f84d2a20e0e7272d52fe82"
ZERO = "0" * 40
GIT_ENV = dict(os.environ, GIT_CONFIG_NOSYSTEM="1",
               GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0",
               GIT_AUTHOR_NAME="VF604 local provider lab",
               GIT_AUTHOR_EMAIL="vf604@example.invalid",
               GIT_COMMITTER_NAME="VF604 local provider lab",
               GIT_COMMITTER_EMAIL="vf604@example.invalid")


def b64(data):
    return base64.b64encode(data.encode("utf-8")).decode("ascii")


def unb64(data):
    return base64.b64decode(data, validate=True).decode("utf-8")


def is_sha(x):
    return isinstance(x, str) and re.fullmatch("[0-9a-f]{40}", x) is not None


def git_command(args, *, data=None):
    return subprocess.run(["git"] + list(args), input=data, text=True,
                          capture_output=True, timeout=12, env=GIT_ENV)


class LocalGit:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.gitdir = self.root / "local.git"

    @classmethod
    def initialize(cls, root):
        obj = cls(root)
        obj.root.mkdir(parents=True)
        (obj.root / OFFLINE_MARKER).write_text(
            "NO_REMOTE_NO_CREDENTIAL_NO_PRODUCTION\n", encoding="utf-8")
        c = git_command(["init", "--bare", "--quiet", str(obj.gitdir)])
        if c.returncode:
            raise RuntimeError("CANNOT_START_ISOLATED_BARE_GIT")
        tree = obj.run("mktree", stdin="").stdout.strip()
        seed = obj.run("commit-tree", tree, "-m", "VF604_LOCAL_ONLY_SEED").stdout.strip()
        if not is_sha(seed):
            raise RuntimeError("BAD_LOCAL_GIT_SEED")
        obj.run("update-ref", OFFLINE_REF, seed, ZERO)
        return obj

    def verified(self):
        return (self.root.is_dir() and not self.root.is_symlink()
                and (self.root / OFFLINE_MARKER).is_file()
                and (self.root / OFFLINE_MARKER).read_text(
                    encoding="utf-8") == "NO_REMOTE_NO_CREDENTIAL_NO_PRODUCTION\n"
                and self.gitdir.is_dir() and not self.gitdir.is_symlink()
                and (self.gitdir / "HEAD").is_file()
                and not (self.gitdir / "config").read_text(
                    encoding="utf-8").count('[remote "'))

    def run(self, *args, stdin=None, allow_failure=False):
        if not self.verified():
            raise RuntimeError("REFUSE_NON_ISOLATED_GIT")
        p = git_command(["--git-dir", str(self.gitdir)] + list(args), data=stdin)
        if p.returncode and not allow_failure:
            raise RuntimeError("NATIVE_LOCAL_GIT_FAILED")
        return p

    def head(self):
        s = self.run("rev-parse", "--verify", OFFLINE_REF).stdout.strip()
        if not is_sha(s):
            raise RuntimeError("LOCAL_REF_UNREADABLE")
        return s

    def candidate(self, expected, key, actor, epoch):
        if not is_sha(expected) or not re.fullmatch(r"[a-z0-9-]{1,40}", key):
            raise ValueError("INVALID_SYNTHETIC_CANDIDATE")
        tree = self.run("rev-parse", expected + "^{tree}").stdout.strip()
        body = "VF604_PROVIDER_INTENT=" + key + ";ACTOR=" + actor + ";EPOCH=" + str(epoch)
        c = self.run("commit-tree", tree, "-p", expected, "-m",
                     body + ";LOCAL_ONLY").stdout.strip()
        if not is_sha(c):
            raise ValueError("CANDIDATE_INVALID")
        return c

    def cas(self, expected, candidate):
        if not is_sha(expected) or not is_sha(candidate):
            return False
        return self.run("update-ref", OFFLINE_REF, candidate, expected,
                        allow_failure=True).returncode == 0


class EtcdClient:
    def __init__(self, url):
        p = urllib.parse.urlsplit(url)
        if p.scheme != "http" or p.hostname != "127.0.0.1" or p.username \
                or p.password or p.path or p.query or p.fragment or not p.port:
            raise ValueError("REFUSE_NON_LOOPBACK_PROVIDER")
        self.url = "http://127.0.0.1:" + str(p.port)

    def post(self, route, payload):
        if route not in ("/v3/kv/put", "/v3/kv/range", "/v3/kv/txn",
                         "/v3/lease/grant", "/v3/lease/revoke",
                         "/v3/lease/timetolive"):
            raise ValueError("REFUSE_NON_FIXTURE_ETCD_API")
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        req = urllib.request.Request(self.url + route, data=encoded,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=2.5) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError, urllib.error.URLError):
            raise RuntimeError("LOCAL_PROVIDER_UNAVAILABLE")

    def get(self, key):
        z = self.post("/v3/kv/range", {"key": b64(key)}).get("kvs", [])
        if not z:
            return None
        if len(z) != 1 or unb64(z[0]["key"]) != key:
            raise RuntimeError("INVALID_PROVIDER_KEY")
        d = z[0]
        return {"value": unb64(d["value"]),
                "version": int(d["version"]),
                "mod_revision": int(d["mod_revision"]),
                "lease": int(d.get("lease", "0"))}

    def lease(self, ttl=15):
        if type(ttl) is not int or not 3 <= ttl <= 30:
            raise ValueError("INVALID_TEST_TTL")
        r = self.post("/v3/lease/grant", {"TTL": ttl})
        lid = int(r["ID"])
        if not lid:
            raise RuntimeError("NO_PROVIDER_LEASE")
        return lid

    def revoke(self, lease_id):
        return self.post("/v3/lease/revoke", {"ID": str(lease_id)})

    def time_to_live(self, lease_id):
        return int(self.post("/v3/lease/timetolive",
                             {"ID": str(lease_id), "keys": False}).get("TTL", -1))

    @staticmethod
    def cmp(key, target, n):
        field = "version" if target == "VERSION" else "mod_revision"
        return {"key": b64(key), "target": target,
                "result": "EQUAL", field: str(n)}

    @staticmethod
    def put(key, value, lease_id=0):
        r = {"key": b64(key), "value": b64(value)}
        if lease_id:
            r["lease"] = str(lease_id)
        return {"request_put": r}

    def txn(self, compares, operations):
        r = self.post("/v3/kv/txn",
                      {"compare": compares, "success": operations, "failure": []})
        # etcd v3 gRPC JSON omits a false bool as its protobuf default.
        # Require a real revision-bearing response header; never interpret
        # an arbitrary malformed/failed HTTP response as a clean CAS denial.
        if not isinstance(r.get("header"), dict) or "revision" not in r["header"]:
            raise RuntimeError("INVALID_REAL_ETCD_TXN_RESPONSE")
        if "succeeded" not in r:
            return False
        if type(r["succeeded"]) is not bool:
            raise RuntimeError("INVALID_REAL_ETCD_TXN_BOOLEAN")
        return r["succeeded"]


class ProviderGitFixture:
    def __init__(self, client, root):
        self.etcd = client
        self.root = Path(root).resolve()
        self.ns = "/velvetos/offline-vf604/" + uuid.uuid4().hex
        self.owner = self.ns + "/owner"
        self.intent = self.ns + "/unleased-effect-intent"
        self.git = LocalGit.initialize(self.root)
        (self.root / "requests").mkdir()

    def acquire(self, actor="old", epoch=1, ttl=15):
        if actor not in ("old", "new") or type(epoch) is not int or epoch < 1:
            return (False, None)
        lid = self.etcd.lease(ttl)
        value = json.dumps({"actor": actor, "epoch": epoch}, sort_keys=True)
        ok = self.etcd.txn([
            self.etcd.cmp(self.owner, "VERSION", 0),
            self.etcd.cmp(self.intent, "VERSION", 0),
        ], [self.etcd.put(self.owner, value, lid)])
        if not ok:
            self.etcd.revoke(lid)
            return (False, None)
        return (True, lid)

    def make_request(self, *, key="request-1", actor="old",
                     epoch=1, expected=None):
        old = expected or self.git.head()
        candidate = self.git.candidate(old, key, actor, epoch)
        return {"key": key, "actor": actor, "epoch": epoch,
                "expected": old, "candidate": candidate, "ref": OFFLINE_REF}

    def save_request(self, req):
        key = req["key"]
        if not re.fullmatch(r"[a-z0-9-]{1,40}", key):
            raise ValueError("INVALID_REQUEST_KEY")
        f = self.root / "requests" / (key + ".json")
        with f.open("x", encoding="utf-8") as fh:
            json.dump(req, fh, sort_keys=True)

    def admission(self, req):
        if (set(req) != {"key", "actor", "epoch", "expected", "candidate", "ref"}
                or not re.fullmatch(r"[a-z0-9-]{1,40}", req["key"])
                or req["ref"] != OFFLINE_REF
                or not is_sha(req["expected"])
                or not is_sha(req["candidate"])
                or req["candidate"] == req["expected"]
                or type(req["epoch"]) is not int or req["epoch"] < 1
                or req["actor"] not in ("old", "new")):
            return "NOT_ADMITTED"
        try:
            if self.etcd.get(self.intent) is not None:
                return "BLOCKED_PENDING_DURABLE_INTENT"
            current = self.etcd.get(self.owner)
            if not current or current["lease"] <= 0:
                return "DENIED_NO_LEASE_OWNER"
            ident = json.loads(current["value"])
            if ident != {"actor": req["actor"], "epoch": req["epoch"]}:
                return "DENIED_STALE_OWNER"
            if self.etcd.time_to_live(current["lease"]) <= 0:
                return "DENIED_EXPIRED_LEASE"
            if self.git.head() != req["expected"]:
                return "DENIED_GIT_SHA_MISMATCH"
            if not self.git.run("cat-file", "-p", req["candidate"]).stdout.count(
                "parent " + req["expected"] + "\n"
            ):
                return "DENIED_CANDIDATE_PARENT"
            # Provider-owned durable intent does NOT carry the actor lease.
            value = json.dumps(dict(req, state="EFFECT_IN_FLIGHT",
                                    observed_owner_revision=current["mod_revision"]),
                               sort_keys=True)
            success = self.etcd.txn([
                self.etcd.cmp(self.owner, "MOD", current["mod_revision"]),
                self.etcd.cmp(self.intent, "VERSION", 0),
            ], [self.etcd.put(self.intent, value)])
            return "PERSISTED_INTENT" if success else "DENIED_PROVIDER_CAS"
        except (RuntimeError, ValueError, OSError, KeyError, TypeError):
            return "FROZEN_PROVIDER_OR_GIT_UNKNOWN"

    def reconcile(self):
        try:
            raw = self.etcd.get(self.intent)
            if raw is None:
                return "NO_UNLEASED_EFFECT_INTENT"
            record = json.loads(raw["value"])
            observed = self.git.head()
            if observed == record["candidate"]:
                return "REMOTE_ADVANCED_UNKNOWN_MANUAL_REVIEW"
            if observed == record["expected"]:
                return "REMOTE_UNCHANGED_UNKNOWN_MANUAL_REVIEW"
            return "REMOTE_CONFLICT_UNKNOWN_MANUAL_REVIEW"
        except (RuntimeError, ValueError, OSError, KeyError, TypeError):
            return "READBACK_UNAVAILABLE_KEEP_UNKNOWN"


def find_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
    finally:
        sock.close()


class EphemeralEtcd:
    def __init__(self, binary, lab_root):
        self.binary = Path(binary).resolve()
        self.lab_root = Path(lab_root).resolve()
        self.server = None
        self.log = None

    def start(self):
        if (not self.binary.is_file()
                or hashlib.sha256(self.binary.read_bytes()).hexdigest() != ETCD_SHA256):
            raise RuntimeError("ETCD_VERSION_SHA_NOT_PINNED")
        self.lab_root.mkdir(parents=True, exist_ok=False)
        cp, pp = find_port(), find_port()
        if cp == pp:
            pp = find_port()
        self.url = "http://127.0.0.1:" + str(cp)
        peer = "http://127.0.0.1:" + str(pp)
        self.log = (self.lab_root / "etcd.stderr").open("wb")
        args = [
            str(self.binary), "--name", "vf604-offline",
            "--data-dir", str(self.lab_root / "etcd-data"),
            "--listen-client-urls", self.url,
            "--advertise-client-urls", self.url,
            "--listen-peer-urls", peer,
            "--initial-advertise-peer-urls", peer,
            "--initial-cluster", "vf604-offline=" + peer,
            "--initial-cluster-token", "vf604-offline-only",
            "--log-level", "error",
        ]
        self.args = args
        self.server = subprocess.Popen(args, cwd=str(self.lab_root),
                                       stdin=subprocess.DEVNULL,
                                       stdout=subprocess.DEVNULL,
                                       stderr=self.log)
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if self.server.poll() is not None:
                raise RuntimeError("ETCD_CHILD_EXITED_DURING_STARTUP")
            try:
                with urllib.request.urlopen(self.url + "/health", timeout=0.3) as f:
                    if json.loads(f.read().decode("utf-8")).get("health") in (True, "true"):
                        return EtcdClient(self.url)
            except (OSError, ValueError):
                time.sleep(0.07)
        raise RuntimeError("ETCD_LOOPBACK_HEALTH_TIMEOUT")

    def crash_restart_same_data_dir(self):
        if not self.server or self.server.poll() is not None:
            raise RuntimeError("NO_RUNNING_EPHEMERAL_PROVIDER_TO_CRASH")
        self.server.kill()  # REAL SIGKILL: deliberately no graceful etcd stop.
        self.server.wait(timeout=6)
        if self.log:
            self.log.close()
        self.log = (self.lab_root / "etcd.stderr").open("ab")
        self.server = subprocess.Popen(self.args, cwd=str(self.lab_root),
                                       stdin=subprocess.DEVNULL,
                                       stdout=subprocess.DEVNULL,
                                       stderr=self.log)
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if self.server.poll() is not None:
                raise RuntimeError("ETCD_FAILED_TO_RESTART_SAME_WAL")
            try:
                with urllib.request.urlopen(self.url + "/health", timeout=0.4) as f:
                    if json.loads(f.read().decode("utf-8")).get("health") in (True, "true"):
                        return
            except (OSError, ValueError):
                time.sleep(0.08)
        raise RuntimeError("ETCD_SAME_WAL_RESTART_TIMEOUT")

    def stop(self):
        try:
            if self.server and self.server.poll() is None:
                self.server.terminate()
                try:
                    self.server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.server.kill()
                    self.server.wait(timeout=5)
        finally:
            if self.log:
                self.log.close()


class LiveEtcdLocalGitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not getattr(cls, "etcd_binary", None):
            raise RuntimeError("SPECIFY_PINNED_ETCD_BINARY_FOR_LIVE_LAB")
        cls.base_tmp = tempfile.TemporaryDirectory(
            prefix="vf604-real-etcd-localgit-",
            dir=cls.run_root)
        cls.server = EphemeralEtcd(cls.etcd_binary,
                                   Path(cls.base_tmp.name) / "provider")
        try:
            cls.client = cls.server.start()
        except Exception:
            cls.server.stop()
            cls.base_tmp.cleanup()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        cls.base_tmp.cleanup()

    def setUp(self):
        self.root = Path(self.base_tmp.name) / ("case-" + uuid.uuid4().hex)
        self.lab = ProviderGitFixture(self.client, self.root)

    def child(self, key="request-1", fault="none"):
        return subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "child",
             self.client.url, str(self.root), self.lab.ns, key, fault],
            text=True, capture_output=True, timeout=12)

    def prepare(self, **kw):
        ok, lid = self.lab.acquire()
        self.assertTrue(ok)
        req = self.lab.make_request(**kw)
        self.lab.save_request(req)
        return req, lid

    def test_01_real_etcd_lease_key_is_lease_bound(self):
        ok, lid = self.lab.acquire()
        self.assertTrue(ok)
        rec = self.client.get(self.lab.owner)
        self.assertIsNotNone(rec)
        self.assertEqual(rec["lease"], lid)
        self.assertGreater(self.client.time_to_live(lid), 0)

    def test_02_provider_intent_is_durable_and_not_lease_attached(self):
        req, lid = self.prepare()
        self.assertEqual(self.lab.admission(req), "PERSISTED_INTENT")
        rec = self.client.get(self.lab.intent)
        self.assertEqual(rec["lease"], 0)
        self.client.revoke(lid)
        self.assertIsNone(self.client.get(self.lab.owner))
        self.assertEqual(json.loads(self.client.get(self.lab.intent)["value"])["state"],
                         "EFFECT_IN_FLIGHT")
        self.assertEqual(self.lab.acquire("new", 2)[0], False)

    def test_03_process_crash_after_real_etcd_txn_before_local_git(self):
        req, lid = self.prepare()
        p = self.child(fault="crash_after_intent")
        self.assertEqual(p.returncode, 91, p.stderr)
        self.assertEqual(self.lab.git.head(), req["expected"])
        self.assertEqual(self.lab.reconcile(),
                         "REMOTE_UNCHANGED_UNKNOWN_MANUAL_REVIEW")
        self.client.revoke(lid)
        self.assertEqual(self.lab.acquire("new", 2)[0], False)

    def test_04_process_crash_after_native_git_before_provider_receipt(self):
        req, lid = self.prepare()
        p = self.child(fault="crash_after_git")
        self.assertEqual(p.returncode, 92, p.stderr)
        self.assertEqual(self.lab.git.head(), req["candidate"])
        self.assertEqual(self.lab.reconcile(),
                         "REMOTE_ADVANCED_UNKNOWN_MANUAL_REVIEW")
        self.client.revoke(lid)
        self.assertEqual(self.lab.acquire("new", 2)[0], False)

    def test_05_replay_after_crash_refused_even_with_live_old_lease(self):
        self.prepare()
        self.child(fault="crash_after_intent")
        self.assertEqual(self.child().stdout.strip(), "BLOCKED_PENDING_DURABLE_INTENT")
        self.assertEqual(self.lab.reconcile(),
                         "REMOTE_UNCHANGED_UNKNOWN_MANUAL_REVIEW")

    def test_06_old_actor_with_current_git_sha_real_etcd_owner_denial(self):
        ok, lid = self.lab.acquire()
        self.assertTrue(ok)
        self.client.revoke(lid)
        self.assertTrue(self.lab.acquire("new", 2)[0])
        req = self.lab.make_request(actor="old", epoch=1)
        self.assertEqual(req["expected"], self.lab.git.head())
        self.assertEqual(self.lab.admission(req), "DENIED_STALE_OWNER")

    def test_07_real_etcd_txn_atomic_concurrent_intent_one_winner(self):
        self.assertTrue(self.lab.acquire()[0])
        a = self.lab.make_request(key="race-a")
        b = self.lab.make_request(key="race-b")
        with ThreadPoolExecutor(max_workers=2) as pool:
            x, y = list(pool.map(self.lab.admission, [a, b]))
        self.assertEqual(sum(v == "PERSISTED_INTENT" for v in (x, y)), 1)
        self.assertEqual(sum(v in ("BLOCKED_PENDING_DURABLE_INTENT",
                                    "DENIED_PROVIDER_CAS") for v in (x, y)), 1)
        self.assertEqual(self.client.get(self.lab.intent)["lease"], 0)

    def test_08_expiry_via_REAL_TTL_does_not_clear_outstanding_intent(self):
        ok, _ = self.lab.acquire(ttl=3)
        self.assertTrue(ok)
        req = self.lab.make_request()
        self.assertEqual(self.lab.admission(req), "PERSISTED_INTENT")
        deadline = time.monotonic() + 9
        while self.client.get(self.lab.owner) is not None and time.monotonic() < deadline:
            time.sleep(0.12)
        self.assertIsNone(self.client.get(self.lab.owner))
        self.assertIsNotNone(self.client.get(self.lab.intent))
        self.assertEqual(self.lab.acquire("new", 2)[0], False)

    def test_09_negative_control_git_accepts_after_real_lease_revocation(self):
        req, lid = self.prepare()
        self.assertEqual(self.lab.admission(req), "PERSISTED_INTENT")
        self.client.revoke(lid)
        self.assertIsNone(self.client.get(self.lab.owner))
        # Deliberately BYPASS credential-less sink to demonstrate race.
        self.assertTrue(self.lab.git.cas(req["expected"], req["candidate"]))
        self.assertEqual(self.lab.reconcile(),
                         "REMOTE_ADVANCED_UNKNOWN_MANUAL_REVIEW")
        self.assertFalse(verdict()["git_credential_exclusivity_proven"])
        self.assertFalse(verdict()["mid_push_lease_expiry_fenced"])

    def test_10_native_local_git_third_party_bypass_with_no_provider_intent(self):
        self.assertTrue(self.lab.acquire()[0])
        req = self.lab.make_request(key="outside")
        self.assertTrue(self.lab.git.cas(req["expected"], req["candidate"]))
        self.assertIsNone(self.client.get(self.lab.intent))
        self.assertEqual(self.lab.git.head(), req["candidate"])

    def test_11_conflicting_native_ref_does_not_clear_provider_intent(self):
        req, _ = self.prepare()
        self.assertEqual(self.lab.admission(req), "PERSISTED_INTENT")
        x = self.lab.make_request(key="other")
        self.assertTrue(self.lab.git.cas(x["expected"], x["candidate"]))
        self.assertEqual(self.lab.reconcile(),
                         "REMOTE_CONFLICT_UNKNOWN_MANUAL_REVIEW")
        self.assertEqual(self.lab.acquire("new", 2)[0], False)

    def test_12_invalid_actor_epoch_branch_shas_never_create_intent(self):
        self.assertTrue(self.lab.acquire()[0])
        req = self.lab.make_request()
        for replace in ({"actor": "new"}, {"epoch": 0}, {"epoch": True},
                        {"ref": "refs/heads/main"}, {"expected": "junk"},
                        {"candidate": ZERO}, {"key": "../escape"}):
            modified = dict(req, **replace)
            self.assertNotEqual(self.lab.admission(modified), "PERSISTED_INTENT")
        self.assertIsNone(self.client.get(self.lab.intent))

    def test_13_unreachable_provider_fails_closed_before_local_git(self):
        self.assertTrue(self.lab.acquire()[0])
        request = self.lab.make_request()
        unused = find_port()
        no_provider = ProviderGitFixture.__new__(ProviderGitFixture)
        no_provider.etcd = EtcdClient("http://127.0.0.1:" + str(unused))
        no_provider.root = self.lab.root
        no_provider.ns = self.lab.ns
        no_provider.owner = self.lab.owner
        no_provider.intent = self.lab.intent
        no_provider.git = self.lab.git
        self.assertEqual(no_provider.admission(request),
                         "FROZEN_PROVIDER_OR_GIT_UNKNOWN")
        self.assertEqual(self.lab.git.head(), request["expected"])

    def test_14_after_native_git_ack_no_atomic_cross_store_completion(self):
        req, _ = self.prepare()
        p = self.child()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "UNKNOWN_PENDING_REMOTE_REVIEW")
        self.assertEqual(self.lab.git.head(), req["candidate"])
        self.assertIsNotNone(self.client.get(self.lab.intent))
        self.assertEqual(self.lab.reconcile(),
                         "REMOTE_ADVANCED_UNKNOWN_MANUAL_REVIEW")

    def test_15_no_credential_no_auth_no_remote_negative_authority(self):
        v = verdict()
        self.assertFalse(v["provider_mtls_rbac_proven"])
        self.assertFalse(v["git_credential_exclusivity_proven"])
        self.assertFalse(v["provider_git_atomicity_proven"])
        self.assertFalse(v["production_authority"])
        self.assertEqual(v["remote_github_writes"], 0)
        self.assertEqual(v["paid_model_calls"], 0)
        self.assertEqual(self.lab.git.run("remote").stdout.strip(), "")

    def test_16_real_provider_sigkill_restart_same_wal_pending_survives(self):
        req, lid = self.prepare()
        self.assertEqual(self.lab.admission(req), "PERSISTED_INTENT")
        before = self.client.get(self.lab.intent)
        self.assertIsNotNone(before)
        self.assertEqual(before["lease"], 0)
        # Kill the REAL etcd server and restart the exact same isolated WAL.
        self.__class__.server.crash_restart_same_data_dir()
        after = self.client.get(self.lab.intent)
        self.assertIsNotNone(after)
        self.assertEqual(after["value"], before["value"])
        self.assertEqual(after["mod_revision"], before["mod_revision"])
        self.assertEqual(after["lease"], 0)
        self.assertEqual(self.lab.acquire("new", 2)[0], False)
        self.assertEqual(self.lab.reconcile(),
                         "REMOTE_UNCHANGED_UNKNOWN_MANUAL_REVIEW")


class OfflineAdmissionContractTests(unittest.TestCase):
    """CI-safe negative tests. NO etcd binary, ports, network, or credentials."""

    def test_01_verify_never_claims_live_provider_execution(self):
        v = verdict()
        for k in ("real_etcd_lease_and_provider_txn",
                  "unleased_provider_pending_intent_survives_owner_expiry",
                  "etcd_sigkill_same_wal_recovery_proven",
                  "git_credential_exclusivity_proven", "provider_mtls_rbac_proven",
                  "provider_git_atomicity_proven", "production_authority"):
            self.assertIs(v[k], False, k)

    def test_02_external_url_rejected_before_network(self):
        for url in ("https://127.0.0.1:1234", "http://github.com:80",
                    "http://localhost:2379", "http://192.168.1.2:2379",
                    "http://127.0.0.1:2379/prefix",
                    "http://user:password@127.0.0.1:2379"):
            with self.assertRaises(ValueError):
                EtcdClient(url)

    def test_03_client_allows_only_loopback_when_explicit(self):
        c = EtcdClient("http://127.0.0.1:12345")
        self.assertEqual(c.url, "http://127.0.0.1:12345")

    def test_04_disallowed_provider_api_path_rejected(self):
        c = EtcdClient("http://127.0.0.1:12345")
        with self.assertRaises(ValueError):
            c.post("/v3/auth/authenticate", {})

    def test_05_false_txn_boolean_omitted_requires_valid_header(self):
        c = EtcdClient("http://127.0.0.1:12345")
        c.post = lambda route, payload: {"header": {"revision": "9"}}
        self.assertIs(c.txn([], []), False)

    def test_06_malformed_provider_reply_is_not_an_authority_denial(self):
        c = EtcdClient("http://127.0.0.1:12345")
        for payload in ({}, {"succeeded": False},
                        {"header": {"revision": "9"}, "succeeded": "false"}):
            c.post = lambda route, body, data=payload: data
            with self.assertRaises(RuntimeError):
                c.txn([], [])

    def test_07_boolean_true_from_valid_etcd_header(self):
        c = EtcdClient("http://127.0.0.1:12345")
        c.post = lambda route, payload: {
            "header": {"revision": "7"}, "succeeded": True
        }
        self.assertIs(c.txn([], []), True)

    def test_08_exact_sha_validation(self):
        self.assertTrue(is_sha("a" * 40))
        self.assertFalse(is_sha("A" * 40))
        self.assertFalse(is_sha("a" * 39))
        self.assertFalse(is_sha("../evil"))

    def test_09_native_local_git_cas_rejects_stale_sha(self):
        with tempfile.TemporaryDirectory(prefix="vf604-contract-only-") as t:
            git = LocalGit.initialize(Path(t) / "fixture")
            old = git.head()
            one = git.candidate(old, "first", "old", 1)
            two = git.candidate(old, "second", "old", 1)
            self.assertTrue(git.cas(old, one))
            self.assertFalse(git.cas(old, two))
            self.assertEqual(git.head(), one)
            self.assertEqual(git.run("remote").stdout.strip(), "")

    def test_10_tampered_fixture_or_added_remote_denied(self):
        with tempfile.TemporaryDirectory(prefix="vf604-contract-only-") as t:
            git = LocalGit.initialize(Path(t) / "fixture")
            with (git.gitdir / "config").open("a", encoding="utf-8") as f:
                f.write('\n[remote "origin"]\nurl = https://example.invalid/fake\n')
            self.assertFalse(git.verified())
            with self.assertRaises(RuntimeError):
                git.run("rev-parse", "--verify", OFFLINE_REF)
            # A different marker also refuses before any Git action.
            (git.gitdir / "config").write_text("[core]\n bare = true\n")
            (git.root / OFFLINE_MARKER).write_text("unsafe\n")
            self.assertFalse(git.verified())


def verdict():
    return {
        "schema": SCHEMA,
        "scope": "REAL_EPHEMERAL_LOCALHOST_ETCD_AND_NATIVE_LOCAL_BARE_GIT",
        "etcd_binary_sha256": ETCD_SHA256,
        # These are FALSE in non-executing verify mode. The integration
        # runner sets them TRUE only AFTER the real server/kill tests pass.
        "real_etcd_lease_and_provider_txn": False,
        "unleased_provider_pending_intent_survives_owner_expiry": False,
        "etcd_sigkill_same_wal_recovery_proven": False,
        "native_local_git_only": True,
        "provider_loopback_unauthenticated": True,
        "provider_mtls_rbac_proven": False,
        "git_credential_exclusivity_proven": False,
        "live_remote_github_provider_fencing_proven": False,
        "mid_push_lease_expiry_fenced": False,
        "provider_git_atomicity_proven": False,
        "globally_exactly_once_proven": False,
        "canonical_production_provider_selected": False,
        "new_scheduler_created": False,
        "production_authority": False,
        "remote_github_writes": 0,
        "paid_model_calls": 0,
        "untrusted_worker_autoreplay": 0,
        "ownership_issue": "#604",
        "consumer_issue": "#612",
    }


def child(url, root, ns, key, fault):
    if (not re.fullmatch(r"/velvetos/offline-vf604/[0-9a-f]{32}", ns)
            or not re.fullmatch(r"[a-z0-9-]{1,40}", key)):
        return 2
    git = LocalGit(root)
    if not git.verified():
        return 2
    with (Path(root) / "requests" / (key + ".json")).open(
        encoding="utf-8") as f:
        req = json.load(f)
    et = EtcdClient(url)
    obj = ProviderGitFixture.__new__(ProviderGitFixture)
    obj.etcd = et
    obj.root = Path(root).resolve()
    obj.ns = ns
    obj.owner = ns + "/owner"
    obj.intent = ns + "/unleased-effect-intent"
    obj.git = git
    allowed = obj.admission(req)
    if allowed != "PERSISTED_INTENT":
        print(allowed)
        return 0
    if fault == "crash_after_intent":
        os._exit(91)
    try:
        owner = et.get(obj.owner)
        if (owner is None or et.time_to_live(owner["lease"]) <= 0
                or obj.git.head() != req["expected"]):
            print("UNKNOWN_PENDING_REMOTE_REVIEW")
            return 0
        success = obj.git.cas(req["expected"], req["candidate"])
        if fault == "crash_after_git" and success:
            os._exit(92)
        print("UNKNOWN_PENDING_REMOTE_REVIEW")
        return 0
    except (RuntimeError, KeyError, OSError):
        print("UNKNOWN_PENDING_REMOTE_REVIEW")
        return 0


def main(argv):
    if len(argv) == 2 and argv[1] == "selftest":
        import io
        out = io.StringIO()
        result = unittest.TextTestRunner(stream=out, verbosity=1).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(
                OfflineAdmissionContractTests))
        if not result.wasSuccessful():
            print(out.getvalue(), file=sys.stderr)
            return 1
        print(json.dumps(dict(verdict(), status="PASS_OFFLINE_CONTRACT",
                              tests=result.testsRun), sort_keys=True))
        return 0
    if len(argv) == 2 and argv[1] == "verify":
        print(json.dumps(dict(verdict(), status="DESIGN_ONLY_NOT_ADMITTED"),
                         sort_keys=True))
        return 0
    if len(argv) == 4 and argv[1] == "integration":
        LiveEtcdLocalGitTests.etcd_binary = argv[2]
        root = Path(argv[3]).resolve()
        if not root.is_dir() or root.is_symlink():
            print("REFUSE_NONEXISTENT_ISOLATED_ROOT", file=sys.stderr)
            return 3
        LiveEtcdLocalGitTests.run_root = str(root)
        import io
        out = io.StringIO()
        result = unittest.TextTestRunner(stream=out, verbosity=1).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(LiveEtcdLocalGitTests))
        if not result.wasSuccessful():
            print(out.getvalue(), file=sys.stderr)
            return 1
        print(json.dumps(dict(
            verdict(), status="PASS_REAL_LOOPBACK_ETCD_LOCAL_GIT",
            tests=result.testsRun, real_etcd_lease_and_provider_txn=True,
            unleased_provider_pending_intent_survives_owner_expiry=True,
            etcd_sigkill_same_wal_recovery_proven=True), sort_keys=True))
        return 0
    if len(argv) == 7 and argv[1] == "child":
        return child(argv[2], argv[3], argv[4], argv[5], argv[6])
    print("NO LIVE WRITER. Usage: verify | integration <pinned-etcd> <new-lab-root>",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
