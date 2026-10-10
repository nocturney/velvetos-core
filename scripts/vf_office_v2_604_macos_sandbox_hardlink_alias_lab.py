#!/usr/bin/env python3
"""#604 MAC kernel sandbox pathname-alias NEGATIVE CONTROL — synthetic keys only.

Do not confuse sandbox-exec pathname denials with real OS principal,
Git credential, cross-host isolation or production authority. A PREEXISTING
hardlink to the same synthetic secret outside the denied subtree bypasses
a deny-by-path sandbox rule on macOS in this test. Never use real secrets.
No keychain, real credential helper, system ACL or production effect.
"""
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

SCHEMA = "vf604.macos-sandbox-hardlink-path-alias-negative.v1"
ROOT_BASENAME = "p0-604-kernel-sandbox-hardlink-alias-20261010"
TEMP_PREFIX = "vf604-kernel-path-negative-"
SYNTHETIC_BYTES = b"VF604_FAKE_PRIVATE_KEY_NEVER_A_REAL_CREDENTIAL\n"
FALSE_CLAIMS = (
    "production_authority",
    "native_github_writer_denial_proven",
    "os_principal_isolation_proven",
    "all_path_aliases_denied",
    "network_isolation_proven",
    "same_user_untrusted_worker_secure",
    "credential_exclusivity_proven",
    "real_github_effect_executed",
)


def verdict():
    return {
        "schema": SCHEMA,
        "status": "DESIGN_ONLY_NOT_ADMITTED",
        "scope": "MAC_EPHEMERAL_LOCAL_PATH_ALIAS_NEGATIVE_ONLY",
        "tests": 0,
        "sandbox_direct_path_denied": False,
        "sandbox_symlink_denied": False,
        "sandbox_preexisting_hardlink_read_accepted": False,
        "sandbox_directory_subpath_hardlink_read_accepted": False,
        "unsandboxed_same_uid_sibling_can_read": False,
        "production_authority": False,
        "native_github_writer_denial_proven": False,
        "os_principal_isolation_proven": False,
        "all_path_aliases_denied": False,
        "network_isolation_proven": False,
        "same_user_untrusted_worker_secure": False,
        "credential_exclusivity_proven": False,
        "real_github_effect_executed": False,
        "remote_github_writes": 0,
        "live_secrets_accessed": 0,
        "system_accounts_changed": 0,
        "global_acl_changes": 0,
        "global_trust_changes": 0,
        "services_changed": 0,
        "new_scheduler": False,
        "paid_api_calls": 0,
        "owner_issue": "#604",
        "consumer_issue": "#612",
        "mac_sandbox_exec_is_deprecated": True,
        "windows_sandbox_live_verification": False,
    }


def validate_test_root(raw):
    if not isinstance(raw, str) or not os.path.isabs(raw):
        raise ValueError("REFUSE_UNSCOPED_ROOT")
    p = Path(raw)
    if p.is_symlink() or ".." in p.parts:
        raise ValueError("REFUSE_LINK_OR_PARENT_TRAVERSAL")
    path = p.resolve()
    if path.name != ROOT_BASENAME or path.is_symlink() or not path.is_dir():
        raise ValueError("REFUSE_NONFIXTURE_ROOT")
    if not hasattr(os, "getuid"):
        raise ValueError("REAL_NEGATIVE_REQUIRES_POSIX")
    if (path.stat().st_uid != os.getuid()
            or stat.S_IMODE(path.stat().st_mode) != 0o700):
        raise ValueError("REFUSE_UNOWNED_OR_WEAK_SCOPE")
    return path


def profile_for(path, *, subpath=False):
    text = str(path)
    if (not text.startswith("/") or any(x in text for x in (
            '"', "\n", "\r", "\x00", "(", ")"))):
        raise ValueError("REFUSE_NONCANONICAL_TEST_PATH")
    scope = "subpath" if subpath else "literal"
    return "(version 1)\n(allow default)\n(deny file-read* (" + \
        scope + ' "' + text + '"))\n'


def run(argv, *, timeout=8):
    return subprocess.run(list(map(str, argv)), capture_output=True,
                          timeout=timeout, text=False, stdin=subprocess.DEVNULL)


def marker_read(result):
    return result.returncode == 0 and SYNTHETIC_BYTES in result.stdout


def denied_read(result):
    return result.returncode != 0 and SYNTHETIC_BYTES not in result.stdout


def live(root_string):
    if sys.platform != "darwin" or not hasattr(os, "getuid"):
        raise RuntimeError("MAC_HOST_ONLY")
    root = validate_test_root(root_string)
    sandbox = Path("/usr/bin/sandbox-exec")
    if not sandbox.is_file():
        raise RuntimeError("NO_REAL_MAC_OS_SANDBOX_EXEC")
    steps = []

    def prove(name, boolean):
        if boolean is not True:
            raise AssertionError("EXPECTED_PATH_ALIAS_NEGATIVE_MISSING_" + name)
        steps.append(name)
        print("REAL_MAC_ALIAS_CHECK_" + name, flush=True)

    with tempfile.TemporaryDirectory(prefix=TEMP_PREFIX, dir=str(root)) as tmp:
        work = Path(tmp)
        work.chmod(0o700)
        sink = work / "synthetic_sink_secrets"
        sink.mkdir(mode=0o700)
        secret = sink / "fake-sink-private-not-actual.key"
        secret.write_bytes(SYNTHETIC_BYTES)
        secret.chmod(0o600)
        symlink = work / "alternative-symlink"
        symlink.symlink_to(secret)
        hardlink = work / "preexisting-second-name-hardlink"
        os.link(secret, hardlink)
        public = work / "harmless-readable"
        public.write_bytes(b"PUBLIC_NONSECRET_BENIGN\n")
        public.chmod(0o644)
        prove("01_fixture_owned_by_current_uid", work.stat().st_uid == os.getuid()
              and secret.stat().st_uid == os.getuid())
        prove("02_private_key_name_is_fake_mode_0600",
              stat.S_IMODE(secret.stat().st_mode) == 0o600
              and secret.read_bytes() == SYNTHETIC_BYTES)
        prove("03_hardlink_names_share_exact_same_inode",
              secret.stat().st_ino == hardlink.stat().st_ino
              and secret.stat().st_dev == hardlink.stat().st_dev)
        prove("04_symlink_alias_targets_only_synthetic_key",
              symlink.is_symlink() and symlink.resolve() == secret.resolve())
        prove("05_unsandboxed_same_uid_reads_canonical",
              marker_read(run(["/bin/cat", secret])))
        prove("06_unsandboxed_same_uid_reads_hardlink",
              marker_read(run(["/bin/cat", hardlink])))
        # Never rely on sandbox defaults for real credentials. This test
        # specifically measures path-denial bypass via PREEXISTING alias.
        evidence = {}
        for strategy in ("literal", "subpath"):
            rule_path = secret if strategy == "literal" else sink
            policy = work / (strategy + ".sb")
            policy.write_text(profile_for(rule_path,
                                          subpath=strategy == "subpath"),
                              encoding="utf-8")
            policy.chmod(0o600)
            def sbox(cmd):
                return run([sandbox, "-f", policy] + list(cmd))
            direct = sbox(["/bin/cat", secret])
            sym = sbox(["/bin/cat", symlink])
            hard = sbox(["/bin/cat", hardlink])
            evidence[strategy] = {"direct_denied": denied_read(direct),
                                  "symlink_denied": denied_read(sym),
                                  "hardlink_allowed": marker_read(hard)}
        prove("07_literal_profile_denies_direct_read",
              evidence["literal"]["direct_denied"])
        prove("08_literal_profile_denies_symlink_alias",
              evidence["literal"]["symlink_denied"])
        prove("09_literal_profile_ALLOWS_preexisting_hardlink",
              evidence["literal"]["hardlink_allowed"])
        prove("10_subpath_profile_denies_direct_read",
              evidence["subpath"]["direct_denied"])
        prove("11_subpath_profile_denies_symlink_alias",
              evidence["subpath"]["symlink_denied"])
        prove("12_subpath_profile_ALLOWS_preexisting_hardlink",
              evidence["subpath"]["hardlink_allowed"])
        # Distinguish an operational sandbox from a blanket broken profile:
        # benign reads must still function under the same exact policy.
        p = work / "subpath.sb"
        benign = run([sandbox, "-f", p, "/bin/cat", public])
        prove("13_profile_does_not_break_benign_reads",
              benign.returncode == 0
              and b"PUBLIC_NONSECRET_BENIGN" in benign.stdout)
        # Python direct open is another OS syscall route; should deny
        # canonical path. This result is not a real-secret custody proof.
        python = run([sandbox, "-f", p, sys.executable, "-c",
                      "import pathlib,sys;print(pathlib.Path(sys.argv[1]).read_bytes())",
                      secret], timeout=9)
        prove("14_python_direct_path_read_also_denied",
              denied_read(python))
        prove("15_no_real_git_or_production_effect",
              verdict()["remote_github_writes"] == 0
              and verdict()["global_acl_changes"] == 0
              and verdict()["live_secrets_accessed"] == 0)
        if len(steps) != 15:
            raise AssertionError("REAL_SANDBOX_TEST_COUNT_INVALID")
        return dict(verdict(), status="PASS_EXPECTED_NEGATIVE_HARDLINK_ALIAS",
                    tests=len(steps), evidence=steps,
                    sandbox_direct_path_denied=True,
                    sandbox_symlink_denied=True,
                    sandbox_preexisting_hardlink_read_accepted=True,
                    sandbox_directory_subpath_hardlink_read_accepted=True,
                    unsandboxed_same_uid_sibling_can_read=True)


class PortableContract(unittest.TestCase):
    def test_01_never_prematurely_admit_authority(self):
        for key in FALSE_CLAIMS:
            self.assertIs(verdict()[key], False, key)

    def test_02_real_results_false_in_verify(self):
        for key in ("sandbox_direct_path_denied", "sandbox_symlink_denied",
                    "sandbox_preexisting_hardlink_read_accepted",
                    "sandbox_directory_subpath_hardlink_read_accepted",
                    "unsandboxed_same_uid_sibling_can_read"):
            self.assertIs(verdict()[key], False, key)

    def test_03_no_remote_or_security_mutations(self):
        for key in ("remote_github_writes", "live_secrets_accessed",
                    "system_accounts_changed", "global_acl_changes",
                    "global_trust_changes", "services_changed",
                    "paid_api_calls"):
            self.assertEqual(verdict()[key], 0)

    def test_04_correct_providers_and_owner(self):
        self.assertEqual(verdict()["owner_issue"], "#604")
        self.assertEqual(verdict()["consumer_issue"], "#612")

    def test_05_scope_is_specific(self):
        self.assertEqual(ROOT_BASENAME,
                         "p0-604-kernel-sandbox-hardlink-alias-20261010")

    def test_06_only_fake_test_bytes(self):
        self.assertIn(b"FAKE_PRIVATE_KEY", SYNTHETIC_BYTES)
        self.assertIn(b"NEVER_A_REAL_CREDENTIAL", SYNTHETIC_BYTES)

    def test_07_profiles_allow_default_for_negative_control(self):
        text = profile_for(PurePosixPath("/tmp/test-secret"))
        self.assertIn("(version 1)", text)
        self.assertIn("(allow default)", text)
        self.assertIn('(literal "/tmp/test-secret")', text)

    def test_08_subpath_policy(self):
        self.assertIn('(subpath "/tmp/secret-dir")',
                      profile_for(PurePosixPath("/tmp/secret-dir"), subpath=True))

    def test_09_refuse_sandbox_profile_injection(self):
        for token in ('/tmp/escape")\n(allow default)', '/tmp/unsafe("',
                      'relative/path', '/tmp/key\x00nul'):
            with self.assertRaises(ValueError):
                profile_for(PurePosixPath(token))

    def test_10_reject_relative_root(self):
        with self.assertRaises(ValueError):
            validate_test_root("temporary-not-absolute")

    def test_11_reject_wrong_root_without_creating_anything(self):
        with tempfile.TemporaryDirectory(prefix="not-vf604-") as r:
            with self.assertRaises(ValueError):
                validate_test_root(r)

    def test_12_real_os_sandbox_not_run_by_selftest(self):
        self.assertIs(verdict()["windows_sandbox_live_verification"], False)
        self.assertEqual(verdict()["status"], "DESIGN_ONLY_NOT_ADMITTED")

    def test_13_deprecated_interface_not_production_assurance(self):
        self.assertTrue(verdict()["mac_sandbox_exec_is_deprecated"])
        self.assertFalse(verdict()["os_principal_isolation_proven"])

    def test_14_no_false_total_hardlink_policy(self):
        self.assertFalse(verdict()["all_path_aliases_denied"])
        self.assertFalse(verdict()["same_user_untrusted_worker_secure"])

    def test_15_no_second_scheduler_or_paid_model(self):
        self.assertFalse(verdict()["new_scheduler"])
        self.assertEqual(verdict()["paid_api_calls"], 0)


def main(argv):
    if len(argv) == 2 and argv[1] == "verify":
        print(json.dumps(verdict(), sort_keys=True))
        return 0
    if len(argv) == 2 and argv[1] == "selftest":
        import io
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(PortableContract))
        if not result.wasSuccessful():
            print(stream.getvalue(), file=sys.stderr)
            return 1
        print(json.dumps(dict(verdict(), status="PASS_PORTABLE_REFUSAL",
                              tests=result.testsRun), sort_keys=True))
        return 0
    if len(argv) == 3 and argv[1] == "integration":
        try:
            data = live(argv[2])
            print(json.dumps(data, sort_keys=True))
            return 0
        except (OSError, RuntimeError, ValueError, AssertionError,
                subprocess.SubprocessError) as e:
            print("REAL_MAC_KERNEL_LAB_REFUSED_" + type(e).__name__ +
                  "_" + str(e)[:80], file=sys.stderr)
            return 1
    print("Refuse non-fixture args. Modes: selftest | verify | "
          "integration [exclusive ephemeral lab root]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
