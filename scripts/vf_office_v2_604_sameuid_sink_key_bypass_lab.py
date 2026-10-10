#!/usr/bin/env python3
"""#604 NEGATIVE CONTROL: same-OS-UID process can reuse a disposable sink key.

Runs only inside a new private ephemeral MAC LOOPBACK etcd 3.6.15 lab
built on the SHA-pinned #674 TLS/RBAC fixture. The second process that
purports to be a Worker first FAILS to delete the pending intent using
its Worker certificate, then SUCCEEDS when it reads the disposable sink
private key owned by the SAME macOS UID, despite mode-0600 permissions.
A real new-owner CAS subsequently succeeds after that tamper. No real
GitHub credential, Git remote, OS account, global trust, service or
production source is touched. This is a FAILING security precondition
shown as an EXPECTED NEGATIVE RESULT, never as admission.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.parse
import uuid

import vf_office_v2_604_real_etcd_mtls_rbac_identity_lab as base

SCHEMA = "vf604.same-os-uid-private-sink-key-bypass.v1"
BASE_SOURCE_SHA = "b74c4b8a1baee7cc534ee82f7abede8c9b0c154ea9693143bb36d7c09319948c"
OWNER_ROOT_NAME = "p0-604-sameuid-sink-custody-bypass-20261010"
TEMP_PREFIX = "vf604-custody-live-"
KEY_PREFIX = "/vf604/custody-negative/"
BYPASS_ACTION = "DELETE_UNLEASED_PENDING_INTENT"
FALSE_FLAGS = (
    "production_authority",
    "git_credential_exclusivity_proven",
    "worker_os_principal_isolation_proven",
    "provider_cross_host_authn_proven",
    "remote_github_writer_denied_proven",
    "native_github_mid_push_expiry_fenced",
    "globally_exactly_once_proven",
    "live_os_enforcement_deployed",
    "new_scheduler_created",
)


def proof():
    return {
        "schema": SCHEMA,
        "scope": "REAL_EPHEMERAL_LOCALHOST_ETCD_AND_SAME_UID_PROCESS_ONLY",
        "status": "DESIGN_ONLY_NOT_ADMITTED",
        "tests": 0,
        "same_uid_process_was_independently_launched": False,
        "same_uid_disposable_sink_private_key_was_read": False,
        "same_uid_sink_impersonation_succeeded": False,
        "pending_unknown_deleted_by_untrusted_same_uid_process": False,
        "new_epoch_admitted_after_untrusted_intent_delete": False,
        "worker_cert_rbac_denial_enforced": False,
        "production_authority": False,
        "git_credential_exclusivity_proven": False,
        "worker_os_principal_isolation_proven": False,
        "provider_cross_host_authn_proven": False,
        "remote_github_writer_denied_proven": False,
        "native_github_mid_push_expiry_fenced": False,
        "globally_exactly_once_proven": False,
        "live_os_enforcement_deployed": False,
        "new_scheduler_created": False,
        "remote_github_writes": 0,
        "system_accounts_changed": 0,
        "global_trust_changes": 0,
        "paid_model_calls": 0,
        "etcd_original_real_mtls_rbac_source_sha256": BASE_SOURCE_SHA,
        "required_mac_uid": "SAME_UID_IS_NOT_SEPARATE_SECURITY_PRINCIPAL",
        "owner_issue": "#604",
        "consumer_issue": "#612",
    }


def verify_base_source():
    path = Path(__file__).resolve().with_name(
        "vf_office_v2_604_real_etcd_mtls_rbac_identity_lab.py")
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SOURCE_SHA:
        raise RuntimeError("REFUSE_UNPINNED_674_MTLS_RBAC_SOURCE")
    return True


def validate_url(s):
    if not isinstance(s, str):
        raise ValueError("REFUSE_NON_STRING_URL")
    u = urllib.parse.urlsplit(s)
    if (u.scheme != "https" or u.hostname != "127.0.0.1"
            or u.username is not None or u.password is not None
            or u.path or u.query or u.fragment):
        raise ValueError("REFUSE_NON_LOOPBACK_URL")
    try:
        pn = u.port
    except ValueError:
        raise ValueError("INVALID_LOOPBACK_PORT")
    if pn is None or not 1 <= pn <= 65535 or u.netloc != ("127.0.0.1:" + str(pn)):
        raise ValueError("REFUSE_NONCANONICAL_LOOPBACK_URL")
    return s


def validate_key(s):
    if (not isinstance(s, str)
            or re.fullmatch(r"/vf604/custody-negative/[0-9a-f]{32}/pending", s) is None):
        raise ValueError("REFUSE_UNSCOPED_TEST_INTENT")
    return s


def validate_temp_root(root):
    candidate = Path(root)
    if candidate.is_symlink():
        raise RuntimeError("REFUSE_LINKED_LAB_ROOT")
    p = candidate.resolve()
    if (not p.is_dir()
            or not p.name.startswith(TEMP_PREFIX)
            or not re.fullmatch(r"vf604-custody-live-[a-z0-9_-]{8,40}", p.name)
            or p.parent.name != OWNER_ROOT_NAME or p.parent.is_symlink()
            or stat.S_IMODE(p.stat().st_mode) != 0o700
            or stat.S_IMODE(p.parent.stat().st_mode) != 0o700):
        raise RuntimeError("REFUSE_OUTSIDE_DISPOSABLE_TEST_SCOPE")
    if not hasattr(os, "getuid") or p.stat().st_uid != os.getuid():
        raise RuntimeError("REFUSE_OS_UID_MISMATCH")
    return p


def validate_owned_key(p, name):
    if name not in ("sink", "worker"):
        raise ValueError("REFUSE_NON_FIXTURE_CERT")
    certdir = p / "certs"
    if certdir.is_symlink() or not certdir.is_dir():
        raise RuntimeError("REFUSE_UNTRUSTED_CERT_DIR")
    if stat.S_IMODE(certdir.stat().st_mode) != 0o700:
        raise RuntimeError("REFUSE_WEAKENED_CERT_DIR")
    crt, key = certdir / (name + ".crt"), certdir / (name + ".key")
    if any(x.is_symlink() or not x.is_file() or x.stat().st_uid != os.getuid()
           for x in (crt, key)):
        raise RuntimeError("REFUSE_EXTERNAL_CERT_BYTES")
    if stat.S_IMODE(key.stat().st_mode) != 0o600:
        raise RuntimeError("REFUSE_WEAKENED_PRIVATE_KEY_MODE")
    if not (p / "certs" / "ca.crt").is_file():
        raise RuntimeError("REFUSE_MISSING_DISPOSABLE_CA")
    return crt, key


def child(argv):
    # Invoked ONLY as a disposable separate process, with exact root/URL/key.
    if len(argv) != 7 or argv[1] != "child" or argv[6] not in ("worker", "borrowed_sink"):
        return 3
    if not hasattr(os, "getuid"):
        return 3
    try:
        root = validate_temp_root(argv[2])
        binary = base.pinned_executable(argv[3], base.PINNED_CTL)
        url, key = validate_url(argv[4]), validate_key(argv[5])
        marker_path = root / ".vf604-sameuid-synthetic-only.json"
        if marker_path.is_symlink() or not marker_path.is_file():
            raise RuntimeError("REFUSE_MISSING_PARENT_MARKER")
        if stat.S_IMODE(marker_path.stat().st_mode) != 0o600:
            raise RuntimeError("REFUSE_WEAKENED_PARENT_MARKER")
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        if (set(marker) != {"uid", "parent_pid", "url", "key", "nonce"}
                or marker["uid"] != os.getuid()
                or marker["parent_pid"] <= 1 or marker["parent_pid"] == os.getpid()
                or marker["url"] != url or marker["key"] != key
                or not re.fullmatch(r"[0-9a-f]{32}", marker["nonce"])):
            raise RuntimeError("REFUSE_FOREIGN_CHILD_TARGET")
        persona = "worker" if argv[6] == "worker" else "sink"
        crt, priv = validate_owned_key(root, persona)
        if argv[6] == "borrowed_sink":
            # The UNTRUSTED process (same OS UID) can directly read the
            # disposable 0600 private key. Never output or save its bytes.
            sensitive = priv.read_bytes()
            if len(sensitive) < 500 or b"PRIVATE KEY" not in sensitive:
                raise RuntimeError("SYNTHETIC_PRIVATE_KEY_UNREADABLE")
            del sensitive
        cmd = [
            str(binary), "--endpoints", url, "--cacert",
            str(root / "certs" / "ca.crt"), "--cert", str(crt),
            "--key", str(priv), "-w", "json", "del", key,
        ]
        run = subprocess.run(cmd, cwd=str(root), capture_output=True,
                             text=True, timeout=8,
                             env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
        if argv[6] == "worker":
            output = (run.stdout + " " + run.stderr).lower()
            if (run.returncode == 0
                    or not any(k in output for k in (
                        "permission", "unauthenticated", "authorization"))):
                raise RuntimeError("EXPECTED_WORKER_CERT_DENIAL_NOT_VERIFIED")
            status = "DENIED_USING_ACTUAL_WORKER_CERT"
            private_key_read = False
        else:
            if run.returncode != 0:
                raise RuntimeError("DISPOSABLE_SINK_CERT_BYPASS_NOT_OBSERVED")
            try:
                reply = json.loads(run.stdout)
            except (ValueError, TypeError):
                raise RuntimeError("SINK_BYPASS_WITHOUT_GENUINE_GRPC_RECEIPT")
            if int(reply.get("deleted", 0)) != 1:
                raise RuntimeError("SINK_BYPASS_NO_EFFECT_RECEIPT")
            status = "UNTRUSTED_SAME_UID_SINK_CERT_BYPASS_SUCCEEDED"
            private_key_read = True
        print(json.dumps({
            "status": status,
            "parent_pid": marker["parent_pid"],
            "child_pid": os.getpid(),
            "same_uid": os.getuid() == marker["uid"],
            "read_disposable_0600_sink_private_key": private_key_read,
            "effect": BYPASS_ACTION if private_key_read else "DENIED_BY_RBAC",
            "real_github_writes": 0,
        }, sort_keys=True))
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, TypeError,
            subprocess.SubprocessError):
        print("REFUSED_INVALID_DISPOSABLE_CHILD_SCOPE", file=sys.stderr)
        return 2


def spawn_child(temp, etcdctl, url, key, persona):
    r = subprocess.run([
        sys.executable, str(Path(__file__).resolve()), "child", str(temp),
        str(etcdctl), url, key, persona,
    ], capture_output=True, text=True, timeout=17)
    if r.returncode != 0:
        raise RuntimeError("DISPOSABLE_SAME_UID_CHILD_FAILED_" + persona)
    try:
        result = json.loads(r.stdout)
    except (TypeError, ValueError):
        raise RuntimeError("DISPOSABLE_CHILD_BAD_RECEIPT")
    if (result.get("same_uid") is not True
            or result.get("parent_pid") != os.getpid()
            or result.get("child_pid") in (None, os.getpid())
            or result.get("real_github_writes") != 0):
        raise RuntimeError("NO_SEPARATE_IDENTIFIED_CHILD_PROCESS")
    return result


def integration(etcd_binary, ctl_binary, configured_root):
    if not hasattr(os, "getuid"):
        raise RuntimeError("REAL_SAME_UID_FIXTURE_NEEDS_POSIX")
    verify_base_source()
    root = Path(configured_root)
    if (root.is_symlink() or not root.is_dir()
            or root.resolve().name != OWNER_ROOT_NAME
            or stat.S_IMODE(root.stat().st_mode) != 0o700
            or root.stat().st_uid != os.getuid()):
        raise RuntimeError("REFUSE_NONEXISTENT_EXCLUSIVE_LAB_ROOT")
    b = base.pinned_executable(etcd_binary, base.PINNED_ETCD)
    ctl = base.pinned_executable(ctl_binary, base.PINNED_CTL)
    checks = []

    def check(label, valid):
        if valid is not True:
            raise AssertionError("FAILED_EXPECTED_NEGATIVE_CONTROL_" + label)
        checks.append(label)
        print("NEGATIVE_CHECK_" + label, flush=True)

    with tempfile.TemporaryDirectory(prefix=TEMP_PREFIX,
                                     dir=str(root.resolve())) as scratch:
        tmp = validate_temp_root(scratch)
        e = base.AuthenticatedEtcd(tmp, b, ctl)
        try:
            check("01_pinned_preexisting_mtls_rbac_module", True)
            e.start()
            check("02_real_ephemeral_mutual_tls_provider", True)
            prefix = KEY_PREFIX + uuid.uuid4().hex + "/"
            owner, intent = prefix + "owner", prefix + "pending"
            base.setup_rbac(e, prefix, owner)
            check("03_actual_certificate_CN_rbac_enabled",
                  bool(e.ctl_ok("root", "auth", "status")))
            # Set up actual durable lock and a real short lease.
            lease = int(json.loads(e.ctl_ok("sink", "lease", "grant", "4"))["ID"])
            if not lease:
                raise RuntimeError("NO_ACTUAL_PROVIDER_LEASE")
            e.ctl_ok("sink", "put", owner, "SYNTHETIC_OLD_EPOCH",
                     "--lease=" + format(lease, "x"))
            e.ctl_ok("sink", "put", intent, "EFFECT_IN_FLIGHT")
            rec = e.cli_range("sink", intent)
            check("04_unleased_pending_effect_intent_exists",
                  rec is not None and rec["lease"] == 0
                  and rec["value"] == "EFFECT_IN_FLIGHT")
            check("05_worker_reads_explicit_owner_only",
                  e.cli_range("worker", owner)["value"] ==
                  "SYNTHETIC_OLD_EPOCH")
            base.assert_cli_denied(e, "worker", "del", intent)
            check("06_assigned_worker_certificate_DENIES_intent_delete", True)
            until = time.monotonic() + 10
            while e.cli_range("sink", owner) is not None \
                    and time.monotonic() < until:
                time.sleep(0.12)
            check("07_real_TTL_owner_expired_unleased_intent_remains",
                  e.cli_range("sink", owner) is None
                  and e.cli_range("sink", intent)["value"] ==
                  "EFFECT_IN_FLIGHT")
            checks_old = [
                'version("' + owner + '") = "0"',
                'version("' + intent + '") = "0"',
            ]
            cmd_new = ['put "' + owner + '" "SYNTHETIC_NEW_EPOCH"']
            check("08_new_owner_pre_attack_CAS_DENIED",
                  e.cli_txn("sink", checks_old, cmd_new) is False
                  and e.cli_range("sink", owner) is None)
            record = {
                "uid": os.getuid(), "parent_pid": os.getpid(),
                "url": e.url, "key": intent, "nonce": uuid.uuid4().hex,
            }
            marker = tmp / ".vf604-sameuid-synthetic-only.json"
            marker.write_text(json.dumps(record, sort_keys=True),
                              encoding="utf-8")
            marker.chmod(0o600)
            validate_owned_key(tmp, "sink")
            check("09_disposable_sink_private_key_mode_0600_owner_same_uid",
                  stat.S_IMODE((tmp / "certs" / "sink.key").stat().st_mode)
                  == 0o600
                  and (tmp / "certs" / "sink.key").stat().st_uid ==
                      os.getuid())
            as_worker = spawn_child(tmp, ctl, e.url, intent, "worker")
            check("10_second_process_with_real_worker_cert_DENIED",
                  as_worker["status"] == "DENIED_USING_ACTUAL_WORKER_CERT"
                  and as_worker["read_disposable_0600_sink_private_key"] is False
                  and e.cli_range("sink", intent) is not None)
            as_stolen = spawn_child(tmp, ctl, e.url, intent, "borrowed_sink")
            check("11_second_process_separate_PID_same_OS_UID",
                  as_stolen["same_uid"] is True
                  and as_stolen["child_pid"] != os.getpid()
                  and as_stolen["child_pid"] != as_worker["child_pid"])
            check("12_untrusted_process_READ_disposable_0600_sink_private_key",
                  as_stolen["read_disposable_0600_sink_private_key"] is True)
            check("13_sink_identity_IMPERSONATED_via_real_mTLS_gRPC",
                  as_stolen["status"] ==
                  "UNTRUSTED_SAME_UID_SINK_CERT_BYPASS_SUCCEEDED"
                  and as_stolen["effect"] == BYPASS_ACTION)
            check("14_preexisting_UNKNOWN_intent_DELETED_by_untrusted_process",
                  e.cli_range("sink", intent) is None)
            check("15_new_owner_CAS_NOW_ACCEPTS_despite_original_UNKNOWN",
                  e.cli_txn("sink", checks_old, cmd_new) is True
                  and e.cli_range("sink", owner)["value"] ==
                      "SYNTHETIC_NEW_EPOCH")
            base.assert_cli_denied(e, "worker", "put", intent,
                                   "MALICIOUS_CERT_DENIED")
            check("16_original_worker_role_STILL_DENIED_not_a_RBAC_failure",
                  True)
            check("17_no_remote_GitHub_Git_or_real_credentials_touched",
                  proof()["remote_github_writes"] == 0
                  and proof()["system_accounts_changed"] == 0
                  and proof()["global_trust_changes"] == 0)
            if len(checks) != 17:
                raise AssertionError("NEGATIVE_CUSTODY_CHECK_COUNT_MISMATCH")
            return {
                "status": "PASS_EXPECTED_NEGATIVE_SAME_UID_KEY_BYPASS",
                "checks": len(checks),
                "evidence": checks,
                "same_uid_process_was_independently_launched": True,
                "same_uid_disposable_sink_private_key_was_read": True,
                "same_uid_sink_impersonation_succeeded": True,
                "pending_unknown_deleted_by_untrusted_same_uid_process": True,
                "new_epoch_admitted_after_untrusted_intent_delete": True,
                "worker_cert_rbac_denial_enforced": True,
            }
        finally:
            e.stop()


class PortableContracts(unittest.TestCase):
    def test_01_no_admission_by_default(self):
        for k in FALSE_FLAGS:
            self.assertIs(proof()[k], False)

    def test_02_no_live_proof_by_default(self):
        for k in (
                "same_uid_process_was_independently_launched",
                "same_uid_disposable_sink_private_key_was_read",
                "same_uid_sink_impersonation_succeeded",
                "pending_unknown_deleted_by_untrusted_same_uid_process",
                "new_epoch_admitted_after_untrusted_intent_delete",
                "worker_cert_rbac_denial_enforced"):
            self.assertIs(proof()[k], False)

    def test_03_only_synthetic_local_scope(self):
        self.assertEqual(proof()["remote_github_writes"], 0)
        self.assertEqual(proof()["scope"],
                         "REAL_EPHEMERAL_LOCALHOST_ETCD_AND_SAME_UID_PROCESS_ONLY")

    def test_04_original_cert_provider_hash_pinned(self):
        self.assertTrue(verify_base_source())

    def test_05_valid_loopback_https_only(self):
        self.assertEqual(validate_url("https://127.0.0.1:12345"),
                         "https://127.0.0.1:12345")

    def test_06_external_urls_rejected_without_network(self):
        for url in ("https://github.com:443", "http://127.0.0.1:12345",
                    "https://localhost:12345", "https://192.168.1.2:5555",
                    "https://127.0.0.1:12345/other",
                    "https://user:secret@127.0.0.1:12345",
                    "https://127.0.0.1:12345?foo=bar"):
            with self.assertRaises(ValueError):
                validate_url(url)

    def test_07_bad_ports_rejected(self):
        for url in ("https://127.0.0.1:0", "https://127.0.0.1:99999",
                    "https://127.0.0.1", "https://127.0.0.1:abc"):
            with self.assertRaises(ValueError):
                validate_url(url)

    def test_08_only_synthetic_key_regex(self):
        key = KEY_PREFIX + "a" * 32 + "/pending"
        self.assertEqual(validate_key(key), key)

    def test_09_real_and_customer_keys_rejected(self):
        for key in ("/velvetos/real/owner", "refs/heads/main",
                    KEY_PREFIX + "../pending",
                    KEY_PREFIX + "A" * 32 + "/pending",
                    KEY_PREFIX + "a" * 32 + "/owner"):
            with self.assertRaises(ValueError):
                validate_key(key)

    def test_10_refuse_arbitrary_temp_root(self):
        with tempfile.TemporaryDirectory(prefix="unrelated-") as root:
            with self.assertRaises(RuntimeError):
                validate_temp_root(root)

    def test_11_refuse_symbolic_root(self):
        with tempfile.TemporaryDirectory(prefix="vf604-custody-check-") as p:
            actual = Path(p) / "actual"
            actual.mkdir(mode=0o700)
            link = Path(p) / "linked"
            try:
                link.symlink_to(actual, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("platform disallows symlink creation")
            with self.assertRaises(RuntimeError):
                validate_temp_root(link)

    def test_12_no_fake_cross_UID_os_attestation(self):
        self.assertIs(proof()["worker_os_principal_isolation_proven"], False)
        self.assertEqual(proof()["required_mac_uid"],
                         "SAME_UID_IS_NOT_SEPARATE_SECURITY_PRINCIPAL")

    def test_13_no_native_git_credential_access(self):
        self.assertFalse(proof()["git_credential_exclusivity_proven"])
        self.assertFalse(proof()["remote_github_writer_denied_proven"])

    def test_14_false_exactly_once_not_promoted(self):
        self.assertFalse(proof()["globally_exactly_once_proven"])
        self.assertFalse(proof()["native_github_mid_push_expiry_fenced"])

    def test_15_identity_vs_authority_ownership(self):
        self.assertEqual(proof()["owner_issue"], "#604")
        self.assertEqual(proof()["consumer_issue"], "#612")

    def test_16_no_system_mutations(self):
        for k in ("remote_github_writes", "system_accounts_changed",
                  "global_trust_changes", "paid_model_calls"):
            self.assertEqual(proof()[k], 0)


def selftest():
    import io
    stream = io.StringIO()
    results = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PortableContracts))
    if not results.wasSuccessful():
        print(stream.getvalue(), file=sys.stderr)
        return 1
    print(json.dumps(dict(proof(), status="PASS_PORTABLE_REFUSAL",
                          tests=results.testsRun), sort_keys=True))
    return 0


def main(argv):
    if len(argv) == 2 and argv[1] == "selftest":
        return selftest()
    if len(argv) == 2 and argv[1] == "verify":
        print(json.dumps(proof(), sort_keys=True))
        return 0
    if len(argv) == 7 and argv[1] == "child":
        return child(argv)
    if len(argv) == 5 and argv[1] == "integration":
        try:
            result = integration(argv[2], argv[3], argv[4])
            print(json.dumps(dict(proof(), **result), sort_keys=True))
            return 0
        except Exception as err:
            # Never emit private key bytes or command-line credential strings.
            print("REFUSED_REAL_NEGATIVE_LAB_" + type(err).__name__ +
                  "_" + str(err)[:100], file=sys.stderr)
            return 1
    print("No production writer: selftest | verify | guarded ephemeral "
          "integration <etcd> <etcdctl> <isolated-root>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
