#!/usr/bin/env python3
"""Office #604. REAL temporary loopback etcd mTLS+RBAC deny lab.

No production credentials, no global trust, no GitHub ref, no server outside
127.0.0.1. Ephemeral CA, users, daemon, WAL and keys are created in a new
mode-0700 temporary directory and destroyed after the test. The peer channel
is intentionally loopback HTTP; no cluster-wide mTLS proof is claimed.
This is not OS principal separation, Git credential custody, atomic Git/etcd,
or production admission. The historical expired-actor GitHub write is unsafe.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
import uuid

SCHEMA = "vf604.real-etcd-mtls-rbac-loopback-deny.v1"
PINNED_ETCD = "dd2596ab902c23252da55e770cb7f7216522ae5599f84d2a20e0e7272d52fe82"
PINNED_CTL = "05f34d3be92b0ba78dfc5aa9fd5d63224d551a7f8c2eadfbaa7dc2f35ae625ad"
LAB_NAME = "vf604-auth-fence-lab"
FALSE_CLAIMS = (
    "production_authority", "git_credential_exclusivity_proven",
    "native_github_writer_fenced", "cross_store_atomicity_proven",
    "mid_push_expiry_proven", "worker_os_principal_isolation_proven",
    "provider_cluster_mtls_proven", "paid_model_used",
)


def verdict():
    return {
        "schema": SCHEMA,
        "scope": "EPHEMERAL_LOOPBACK_ETCD_MUTUAL_TLS_AND_RBAC",
        "portable_selftest_pass": False,
        "real_server_mtls_rbac_proven": False,
        "real_server_wal_recovery_proven": False,
        "native_github_writer_fenced": False,
        "git_credential_exclusivity_proven": False,
        "worker_os_principal_isolation_proven": False,
        "provider_cluster_mtls_proven": False,
        "mid_push_expiry_proven": False,
        "cross_store_atomicity_proven": False,
        "production_authority": False,
        "paid_model_used": False,
        "remote_github_writes": 0,
        "global_trust_store_mutations": 0,
        "system_account_mutations": 0,
        "created_scheduler": False,
        "provider_identity_security_ownership": "#604",
        "downstream_consumer": "#612",
        "etcd_binary_sha256": PINNED_ETCD,
        "etcdctl_binary_sha256": PINNED_CTL,
        "temporary_peer_transport": "HTTP_LOOPBACK_ONLY",
        "test_ca_stored_only_in_disposable_dir": True,
    }


def enc(s):
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])
    finally:
        s.close()


def pinned_executable(binary, sha):
    b = Path(binary).resolve()
    if not b.is_file() or hashlib.sha256(b.read_bytes()).hexdigest() != sha:
        raise ValueError("REFUSE_UNPINNED_ETCD_EXECUTABLE")
    return b


def subprocess_safe(args, *, cwd=None, timeout=10, data=None):
    p = subprocess.run(list(map(str, args)), cwd=str(cwd) if cwd else None,
                       env=dict(os.environ, GIT_TERMINAL_PROMPT="0"),
                       text=True, capture_output=True, timeout=timeout,
                       input=data)
    return p


def require(p, purpose):
    if p.returncode:
        # No private keys or passwords from captured subprocess stdout/stderr.
        raise RuntimeError("LAB_COMMAND_FAILED_" + purpose)
    return p.stdout.strip()


def openssl_exec(arguments, root):
    require(subprocess_safe(["openssl"] + list(arguments), cwd=root),
            "EPHEMERAL_OPENSSL")


class Certificates:
    def __init__(self, root):
        self.root = Path(root) / "certs"
        self.root.mkdir(mode=0o700)
        self.ca = self.root / "ca.crt"
        self.ca_key = self.root / "ca.key"
        self.roles = {}

    def write(self, name, text):
        p = self.root / name
        p.write_text(text, encoding="utf-8")
        p.chmod(0o600)
        return p

    def initialize(self):
        ca_cfg = self.write("ca.cnf",
            "[req]\n"
            "distinguished_name=dn\n"
            "x509_extensions=v3_ca\n"
            "prompt=no\n"
            "[dn]\n"
            "CN=vf604-temporary-disposable-ca\n"
            "[v3_ca]\n"
            "basicConstraints=critical,CA:TRUE\n"
            "keyUsage=critical,keyCertSign,cRLSign\n"
            "subjectKeyIdentifier=hash\n")
        openssl_exec(["req", "-x509", "-new", "-newkey", "rsa:2048",
                      "-nodes", "-days", "1", "-sha256",
                      "-config", ca_cfg, "-keyout", self.ca_key,
                      "-out", self.ca], self.root)
        self.ca_key.chmod(0o600)
        self.leaf("server", "127.0.0.1", server=True)
        self.leaf("root", "root")
        self.leaf("sink", "vf604-sink")
        self.leaf("worker", "vf604-worker")
        self.leaf("outsider", "vf604-outsider")
        # A forged sink CN issued by a DIFFERENT CA must fail TLS trust.
        rogue = self.root / "rogue"
        rogue.mkdir(mode=0o700)
        other = Certificates.__new__(Certificates)
        other.root = rogue
        other.ca = rogue / "ca.crt"
        other.ca_key = rogue / "ca.key"
        other.roles = {}
        other_cfg = other.write("ca.cnf",
            "[req]\n"
            "distinguished_name=dn\n"
            "x509_extensions=v3_ca\n"
            "prompt=no\n"
            "[dn]\nCN=vf604-rogue-untrusted-ca\n"
            "[v3_ca]\n"
            "basicConstraints=critical,CA:TRUE\n"
            "keyUsage=critical,keyCertSign,cRLSign\n")
        openssl_exec(["req", "-x509", "-new", "-newkey", "rsa:2048",
                      "-nodes", "-days", "1", "-sha256",
                      "-config", other_cfg, "-keyout", other.ca_key,
                      "-out", other.ca], other.root)
        other.ca_key.chmod(0o600)
        other.leaf("forged-sink", "vf604-sink")
        self.roles["forged-sink"] = other.roles["forged-sink"]
        return self

    def leaf(self, name, cn, *, server=False):
        out = self.root / (name + ".crt")
        key = self.root / (name + ".key")
        csr = self.root / (name + ".csr")
        ext = self.write(name + ".ext",
                         "[v3_cert]\n"
                         "basicConstraints=critical,CA:FALSE\n"
                         "keyUsage=digitalSignature,keyEncipherment\n"
                         "extendedKeyUsage=" + (
                             "serverAuth\nsubjectAltName=IP:127.0.0.1,DNS:localhost\n"
                             if server else "clientAuth\n"))
        openssl_exec(["req", "-new", "-newkey", "rsa:2048",
                      "-nodes", "-sha256", "-keyout", key,
                      "-out", csr, "-subj", "/CN=" + cn], self.root)
        openssl_exec(["x509", "-req", "-in", csr, "-CA", self.ca,
                      "-CAkey", self.ca_key, "-CAcreateserial",
                      "-out", out, "-days", "1", "-sha256",
                      "-extfile", ext, "-extensions", "v3_cert"], self.root)
        key.chmod(0o600)
        self.roles[name] = (out, key)
        return out, key


class AuthenticatedEtcd:
    def __init__(self, root, etcd, ctl):
        self.root = Path(root).resolve()
        self.etcd = pinned_executable(etcd, PINNED_ETCD)
        self.ctl = pinned_executable(ctl, PINNED_CTL)
        self.cert = Certificates(self.root).initialize()
        self.clientport, self.peerport = port(), port()
        if self.clientport == self.peerport:
            self.peerport = port()
        self.url = "https://127.0.0.1:" + str(self.clientport)
        self.peer = "http://127.0.0.1:" + str(self.peerport)
        self.server = None
        self.log = None
        self.args = [
            str(self.etcd), "--name", LAB_NAME,
            "--data-dir", str(self.root / "db"),
            "--listen-client-urls", self.url,
            "--advertise-client-urls", self.url,
            "--listen-peer-urls", self.peer,
            "--initial-advertise-peer-urls", self.peer,
            "--initial-cluster", LAB_NAME + "=" + self.peer,
            "--initial-cluster-token", "vf604-isolated-auth-only",
            "--cert-file", str(self.cert.roles["server"][0]),
            "--key-file", str(self.cert.roles["server"][1]),
            "--trusted-ca-file", str(self.cert.ca),
            "--client-cert-auth=true",
            "--log-level", "error",
        ]

    def client_ctx(self, who=None):
        ctx = ssl.create_default_context(cafile=str(self.cert.ca))
        ctx.check_hostname = True
        if who is not None:
            cert, key = self.cert.roles[who]
            ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
        return ctx

    def start(self):
        self.log = (self.root / "server.stderr").open("ab")
        self.server = subprocess.Popen(self.args, cwd=str(self.root),
                                       stdin=subprocess.DEVNULL,
                                       stdout=subprocess.DEVNULL,
                                       stderr=self.log)
        self.health()

    def health(self):
        until = time.monotonic() + 14
        while time.monotonic() < until:
            if not self.server or self.server.poll() is not None:
                raise RuntimeError("ISOLATED_ETCD_CHILD_CRASHED")
            try:
                req = urllib.request.Request(self.url + "/health",
                                             method="GET")
                with urllib.request.urlopen(
                        req, context=self.client_ctx("root"),
                        timeout=0.7) as h:
                    if json.loads(h.read().decode()).get("health") in (
                            "true", True):
                        return
            except (OSError, ValueError, urllib.error.URLError):
                time.sleep(0.08)
        raise RuntimeError("ISOLATED_ETCD_HEALTH_TIMEOUT")

    def ctl_run(self, who, *args, data=None):
        cmd = [
            str(self.ctl), "--endpoints", self.url,
            "--cacert", str(self.cert.ca), "-w", "json",
        ]
        if who is not None:
            crt, key = self.cert.roles[who]
            cmd += ["--cert", str(crt), "--key", str(key)]
        cmd += list(args)
        return subprocess_safe(cmd, cwd=self.root, timeout=8, data=data)

    def ctl_ok(self, who, *args):
        return require(self.ctl_run(who, *args), "ETCDCTL")

    def cli_range(self, who, key):
        out = json.loads(self.ctl_ok(who, "get", key))
        kvs = out.get("kvs", [])
        if not kvs:
            return None
        if len(kvs) != 1 or base64.b64decode(kvs[0]["key"]).decode() != key:
            raise RuntimeError("INVALID_ETCD_KV_READBACK")
        record = kvs[0]
        return {"mod_revision": int(record["mod_revision"]),
                "version": int(record["version"]),
                "lease": int(record.get("lease", "0")),
                "value": base64.b64decode(record["value"]).decode()}

    def cli_txn(self, who, conditions, success_commands):
        # etcdctl txn reads compare, success, then FAILURE section;
        # the final empty failure request line must be terminated as well.
        script = "\n".join(conditions) + "\n\n" + \
                 "\n".join(success_commands) + "\n\n\n"
        cmd = self.ctl_run(who, "txn", data=script)
        if cmd.returncode != 0:
            # Only report the sanitized parser error class, never key material.
            why = cmd.stderr.lower()
            if "invalid compare" in why or "compare" in why:
                cause = "COMPARE_SYNTAX"
            elif "invalid put" in why or "put" in why:
                cause = "PUT_SYNTAX"
            elif "permission" in why or "auth" in why:
                cause = "RBAC_PERMISSION"
            elif "parse" in why or "syntax" in why:
                cause = "TXN_PARSE"
            else:
                cause = "UNKNOWN"
            if cause == "UNKNOWN":
                # Only fixture grammar; no user or credential data.
                print("SANITIZED_TXN_PARSER_DIAG=" +
                      re.sub(r"/Users/[^ ]+", "<local-path>",
                             (cmd.stderr + cmd.stdout)[:220]),
                      file=sys.stderr, flush=True)
            raise RuntimeError("ETCDCTL_TXN_" + cause)
        out = cmd.stdout.strip()
        try:
            j = json.loads(out)
        except ValueError:
            raise RuntimeError("INVALID_GRPC_ETCDCTL_TXN_JSON")
        if not isinstance(j.get("header"), dict) or "revision" not in j["header"]:
            raise RuntimeError("INVALID_GRPC_ETCDCTL_TXN_HEADER")
        if "succeeded" not in j:
            return False
        if type(j["succeeded"]) is not bool:
            raise RuntimeError("INVALID_GRPC_ETCDCTL_TXN_BOOLEAN")
        return j["succeeded"]

    def post(self, *_args, **_kwargs):
        # The mTLS gRPC-JSON gateway returned HTTP 400 for a legitimate
        # certificate-CN scoped range after RBAC enablement. Never silently
        # replace an authenticated gRPC request with that ambiguous transport.
        raise RuntimeError("REFUSE_HTTP_JSON_GATEWAY_IDENTITY_NOT_PROVEN")

    @staticmethod
    def cmp(key, target, value):
        name = "mod_revision" if target == "MOD" else "version"
        return {"key": enc(key), "target": target,
                "result": "EQUAL", name: str(value)}

    @staticmethod
    def put(key, value, lease=None):
        v = {"key": enc(key), "value": enc(value)}
        if lease is not None:
            v["lease"] = str(lease)
        return {"request_put": v}

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
                self.log = None

    def crash_restart(self):
        if not self.server or self.server.poll() is not None:
            raise RuntimeError("NO_RUNNING_ETCD_TO_CRASH")
        self.server.kill()
        self.server.wait(timeout=6)
        if self.log:
            self.log.close()
        self.start()


def setup_rbac(e, prefix, owner):
    root = "root"
    # Real passwordless mTLS CN user identities, only in this fresh lab DB.
    e.ctl_ok(root, "user", "add", "root", "--no-password")
    e.ctl_ok(root, "role", "add", "root")
    e.ctl_ok(root, "user", "grant-role", "root", "root")
    e.ctl_ok(root, "role", "add", "vf604-sink-role")
    e.ctl_ok(root, "role", "grant-permission", "vf604-sink-role",
             "readwrite", prefix, "--prefix")
    e.ctl_ok(root, "user", "add", "vf604-sink", "--no-password")
    e.ctl_ok(root, "user", "grant-role", "vf604-sink", "vf604-sink-role")
    e.ctl_ok(root, "role", "add", "vf604-worker-role")
    e.ctl_ok(root, "role", "grant-permission", "vf604-worker-role",
             "read", owner)
    e.ctl_ok(root, "user", "add", "vf604-worker", "--no-password")
    e.ctl_ok(root, "user", "grant-role", "vf604-worker", "vf604-worker-role")
    e.ctl_ok(root, "auth", "enable")


def assert_cli_denied(e, who, *args):
    r = e.ctl_run(who, *args)
    if r.returncode == 0:
        raise AssertionError("UNTRUSTED_IDENTITY_ACTION_WAS_ACCEPTED")
    # A valid denial must be explained by TLS/auth/permission, not by a
    # dead server, bad command, timeout, missing file, or bad fixture input.
    message = (r.stdout + " " + r.stderr).lower()
    if not any(v in message for v in (
            "permission", "unauthenticated", "user name",
            "certificate", "tls", "authentication", "client cert",
            "unrecognized user")):
        raise AssertionError("UNEXPECTED_DENIAL_NOT_VERIFIED")


def integration(etcd, ctl, existing_root):
    root = Path(existing_root).resolve()
    if not root.is_dir() or root.is_symlink():
        raise RuntimeError("REFUSE_MISSING_TEST_ROOT")
    with tempfile.TemporaryDirectory(
            prefix="vf604-mtls-rbac-real-", dir=str(root)) as temp:
        p = Path(temp)
        p.chmod(0o700)
        e = AuthenticatedEtcd(p, etcd, ctl)
        checks = []

        def check(name, assertion):
            if assertion is not True:
                raise AssertionError("FAILED_REAL_CHECK_" + name)
            checks.append(name)
            print("LAB_CHECK_" + name, flush=True)

        try:
            e.start()
            check("01_real_loopback_TLS_server_healthy", True)
            # The mTLS-only server must deny a client with no certificate.
            assert_cli_denied(e, None, "get", "vf604-no-cert")
            check("02_no_client_certificate_denied", True)
            # Before enabling etcd RBAC, TLS already rejects wrong CA.
            assert_cli_denied(e, "forged-sink", "get", "vf604-rogue")
            check("03_untrusted_CA_same_sink_CN_denied", True)
            prefix = "/vf604/security-lab/" + uuid.uuid4().hex + "/"
            owner = prefix + "owner"
            intent = prefix + "unleased-intent"
            setup_rbac(e, prefix, owner)
            check("04_real_passwordless_certificate_CN_RBAC_enabled",
                  "true" in e.ctl_ok("root", "auth", "status").lower()
                  or "enabled" in e.ctl_ok(
                      "root", "auth", "status").lower())
            assert_cli_denied(e, "outsider", "get", owner)
            check("05_trusted_CA_but_unknown_CN_denied", True)
            e.ctl_ok("sink", "put", owner, "synthetic-owner-epoch7")
            check("06_sink_scoped_put_owner_allowed", True)
            e.ctl_ok("sink", "put", intent, "synthetic-probe-intent")
            check("07_sink_scoped_put_intent_allowed", True)
            w = e.ctl_ok("worker", "get", owner)
            check("08_worker_can_read_explicit_owner_key",
                  e.cli_range("worker", owner)["value"] ==
                      "synthetic-owner-epoch7")
            assert_cli_denied(e, "worker", "get", intent)
            check("09_worker_cannot_read_unleased_intent", True)
            assert_cli_denied(e, "worker", "put", owner, "forged")
            check("10_worker_cannot_change_owner_key", True)
            assert_cli_denied(e, "worker", "put", intent, "forged")
            check("11_worker_cannot_change_intent", True)
            assert_cli_denied(e, "worker", "get", prefix + "foreign")
            check("12_worker_read_permission_is_exact_key", True)
            assert_cli_denied(e, "worker", "put", prefix + "foreign",
                              "forged")
            check("13_worker_cannot_create_unassigned_key", True)
            assert_cli_denied(e, "sink", "put",
                              "/vf604/outside-scope/try", "forged")
            check("14_sink_cannot_write_outside_exact_prefix", True)
            assert_cli_denied(e, "sink", "user", "add", "vf604-evil",
                              "--no-password")
            check("15_sink_cannot_administer_RBAC", True)

            # Make the owner lease-backed, while the intent is explicitly
            # not lease-attached. No real business/production resource.
            e.ctl_ok("sink", "del", owner)
            e.ctl_ok("sink", "del", intent)
            lease_reply = json.loads(e.ctl_ok("sink", "lease", "grant", "4"))
            lease = int(lease_reply["ID"])
            if not lease:
                raise RuntimeError("INVALID_REAL_LEASE")
            e.ctl_ok("sink", "put", owner, "synthetic-live-owner-epoch7",
                     "--lease=" + format(lease, "x"))
            record = e.cli_range("sink", owner)
            check("16_owner_key_attached_to_real_etcd_lease",
                  record is not None and record["lease"] == lease)
            admit = e.cli_txn("sink", [
                'mod("'+ owner +'") = "'+ str(record["mod_revision"]) +'"',
                'version("'+ intent +'") = "0"',
            ], ['put "'+ intent +'" "EFFECT_IN_FLIGHT"'])
            check("17_real_provider_two_compare_durable_intent",
                  admit is True
                  and e.cli_range("sink", intent)["lease"] == 0)
            until = time.monotonic() + 11
            while e.cli_range("sink", owner) is not None \
                    and time.monotonic() < until:
                time.sleep(0.12)
            check("18_real_TTL_expiry_removes_owner_not_intent",
                  e.cli_range("sink", owner) is None
                  and e.cli_range("sink", intent)["value"] ==
                      "EFFECT_IN_FLIGHT")
            no_new_owner = e.cli_txn("sink", [
                'version("'+ owner +'") = "0"',
                'version("'+ intent +'") = "0"',
            ], ['put "'+ owner +'" "synthetic-new-epoch8"'])
            check("19_real_etcd_txn_blocks_new_owner_with_pending",
                  no_new_owner is False
                  and e.cli_range("sink", owner) is None)
            before = e.cli_range("sink", intent)
            e.crash_restart()  # actual SIGKILL then same disposable WAL
            after = e.cli_range("sink", intent)
            check("20_actual_etcd_SIGKILL_same_WAL_intent_survives",
                  before is not None and after == before)
            assert_cli_denied(e, "worker", "get", intent)
            assert_cli_denied(e, "worker", "put", intent,
                              "replayed-after-restart")
            check("21_RBAC_worker_rejected_after_provider_restart", True)
            check("22_root_auth_and_CA_identity_survive_restart",
                  bool(e.ctl_ok("root", "auth", "status")))
            assert_cli_denied(e, "sink", "put",
                              "/vf604/outside-scope/restarted", "forged")
            check("23_sink_scope_still_enforced_after_restart", True)
            check("24_pending_UNKNOWN_never_auto_replayed",
                  e.cli_range("sink", intent)["value"] == "EFFECT_IN_FLIGHT"
                  and e.cli_range("sink", owner) is None)
            # Explicit negative result: this protects only the etcd keyspace;
            # same Mac OS user can access disposable client key files. A Git
            # credentialed process elsewhere could bypass these roles.
            check("25_no_real_GitHub_effect_or_OS_custody_claim",
                  not verdict()["git_credential_exclusivity_proven"]
                  and verdict()["remote_github_writes"] == 0)
            if len(checks) != 25:
                raise AssertionError("NOT_ALL_EXPECTED_REAL_CHECKS")
            return {"status": "PASS_REAL_LOCAL_MTLS_RBAC",
                    "checks": len(checks),
                    "evidence": checks,
                    "real_server_mtls_rbac_proven": True,
                    "real_server_wal_recovery_proven": True}
        finally:
            e.stop()


class PortableDenialTests(unittest.TestCase):
    """No openssl, network listener, etcd server, or credential is needed."""

    def test_01_verify_all_prod_claims_false(self):
        v = verdict()
        for name in FALSE_CLAIMS:
            self.assertIs(v[name], False)
        self.assertFalse(v["real_server_mtls_rbac_proven"])

    def test_02_zero_remote_effects_and_no_trust_mutation(self):
        v = verdict()
        for k in ("remote_github_writes",
                  "global_trust_store_mutations", "system_account_mutations"):
            self.assertEqual(v[k], 0)
        self.assertFalse(v["created_scheduler"])

    def test_03_endpoint_only_created_by_real_server(self):
        self.assertTrue(AuthenticatedEtcd.__name__ == "AuthenticatedEtcd")
        self.assertEqual(LAB_NAME, "vf604-auth-fence-lab")

    def test_04_ca_is_disposable_not_global(self):
        self.assertTrue(verdict()["test_ca_stored_only_in_disposable_dir"])
        self.assertFalse(verdict()["provider_cluster_mtls_proven"])

    def test_05_real_binary_pins_are_literal_sha256(self):
        self.assertRegex(PINNED_ETCD, r"^[0-9a-f]{64}$")
        self.assertRegex(PINNED_CTL, r"^[0-9a-f]{64}$")

    def test_06_no_fake_proof_from_nonexecuting_verify(self):
        self.assertFalse(verdict()["real_server_wal_recovery_proven"])
        self.assertFalse(verdict()["real_server_mtls_rbac_proven"])

    def test_07_key_encodes_are_stable(self):
        self.assertEqual(enc("x/y"), "eC95")

    def test_08_txn_compare_targets_accurate(self):
        self.assertEqual(AuthenticatedEtcd.cmp("k", "MOD", 7)["mod_revision"], "7")
        self.assertEqual(AuthenticatedEtcd.cmp("k", "VERSION", 0)["version"], "0")

    def test_09_unleased_put_has_no_lease(self):
        self.assertNotIn("lease", AuthenticatedEtcd.put("k", "v")["request_put"])

    def test_10_wrong_binary_must_be_rejected(self):
        with tempfile.TemporaryDirectory(prefix="vf604-offline-") as p:
            f = Path(p) / "bad"
            f.write_bytes(b"NOT_OFFICIAL_ETCD_BINARY")
            with self.assertRaises(ValueError):
                pinned_executable(f, PINNED_ETCD)

    def test_11_test_authority_does_not_consume_provider_identity(self):
        self.assertEqual(verdict()["provider_identity_security_ownership"], "#604")
        self.assertEqual(verdict()["downstream_consumer"], "#612")

    def test_12_synthetic_role_does_not_claim_same_user_credential_isolation(self):
        self.assertFalse(verdict()["worker_os_principal_isolation_proven"])
        self.assertFalse(verdict()["git_credential_exclusivity_proven"])

    def test_13_unverified_http_gateway_fails_closed_no_network(self):
        fixture = AuthenticatedEtcd.__new__(AuthenticatedEtcd)
        with self.assertRaisesRegex(RuntimeError, "REFUSE_HTTP_JSON_GATEWAY"):
            fixture.post("sink", "/v3/kv/range", {"key": enc("no-effect")})


def selftest():
    import io
    out = io.StringIO()
    result = unittest.TextTestRunner(stream=out).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PortableDenialTests))
    if not result.wasSuccessful():
        print(out.getvalue(), file=sys.stderr)
        return 1
    print(json.dumps(dict(verdict(), status="PASS_PORTABLE_DENIAL",
                          portable_selftest_pass=True,
                          tests=result.testsRun), sort_keys=True))
    return 0


def main(argv):
    if len(argv) == 2 and argv[1] == "verify":
        print(json.dumps(dict(verdict(), status="DESIGN_ONLY_NOT_ADMITTED"),
                         sort_keys=True))
        return 0
    if len(argv) == 2 and argv[1] == "selftest":
        return selftest()
    if len(argv) == 5 and argv[1] == "integration":
        root = Path(argv[4]).resolve()
        if not root.is_dir() or root.is_symlink() or \
                root.name != "p0-604-mtls-rbac-identity-isolation-20261010":
            print("REFUSE_ROOT_NOT_OWNED_BY_THIS_LAB", file=sys.stderr)
            return 2
        old = os.umask(0o077)
        try:
            result = integration(argv[2], argv[3], root)
            print(json.dumps(dict(verdict(), **result), sort_keys=True))
            return 0
        except Exception as err:
            # Do not print external error details, file names or private keys.
            print("REAL_LAB_FAILED_" + type(err).__name__ +
                  "_" + str(err)[:90], file=sys.stderr)
            return 1
        finally:
            os.umask(old)
    print("OFFLINE: verify | selftest. Explicit local-only integration requires "
          "pinned etcd, etcdctl and the unique isolated lab directory.",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
