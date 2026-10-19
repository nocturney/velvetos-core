#!/usr/bin/env python3
"""Live pins and historical receipt pins stay apart.

Each moved constant has a check that fails when the live pin and the receipt
pin are the same value, and a check that fails when a sealed receipt byte
changes. This does not start etcd, and it does not admit.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import vf_office_v2_604_cp081_mtls_atomic_admission_lab as cp081
import vf_office_v2_604_cp083_native_lostack_receipt_gate as lostack
import vf_office_v2_604_cp083_osuid_evidence_gate as osuid
import vf_office_v2_604_native_git_crash_reconcile_offline as native
import vf_office_v2_604_real_etcd_mtls_rbac_identity_lab as identity
import vf_office_v2_604_sameuid_sink_key_bypass_lab as sameuid

ROOT = Path(__file__).resolve().parents[1]
SENSOR = ROOT / "scripts" / "check-office-v2-contracts.py"
PHASE2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"

IDENTITY_RECEIPT = "b74c4b8a1baee7cc534ee82f7abede8c9b0c154ea9693143bb36d7c09319948c"
CP081_RECEIPT = "eaab28424989b4b3a7a5de58f5571d9938b21c8c17c3dfb4c5d2eaa1d73670e2"
NATIVE_RECEIPT = "2bbd81c9c7f59c1b28937286d1c365ca46c0ceb9db96157859f7225e0dd6d632"
SAMEUID_HISTORICAL = "7e2380e361e0595d817ba9ae1d217f841af36976246e246dff4a1b6f915b18fb"

SEALED = {
    "docs/implementation/office-v2/phase2/p0-604-cp081-mtls-atomic-2026-10-16.json":
        "c9db2a91406fd3083c8390634c9b9b32d0e1055c66c6fb6cf79963f4ca7b4762",
    "docs/implementation/office-v2/phase2/p0-604-cp081-mtls-atomic-2026-10-16.md":
        "152fd2fd7def07b35628249f2db836f66b5a20bd81b2a0688c5b280cc23e9c78",
    "docs/implementation/office-v2/phase2/p0-604-cp082-tls-localgit-unknown-2026-10-16.json":
        "091c2f92daf6eb8084d0c5b763b6f443097e54b46ca874cc39c3ddd119f57639",
    "docs/implementation/office-v2/phase2/p0-604-cp082-tls-localgit-unknown-2026-10-16.md":
        "73ab413d8ee28df47c0680208a0cf3d5c7ad57acf9dfa25e09f6fb558fc586c8",
    "docs/implementation/office-v2/phase2/p0-604-cp083-osuid-tls-localgit-2026-10-17.json":
        "cc6a576a57b76c6578c54af36c6d3306976cf92ea5814c3f28de7787285f69b0",
    "docs/implementation/office-v2/phase2/p0-604-cp083-osuid-tls-localgit-2026-10-17.md":
        "5445919ae14695e029c142f9a1f7c95a62a4c137c9026afea74145667f0c57a6",
    "docs/implementation/office-v2/phase2/p0-604-cp083-native-lostack-two-receipts-2026-10-18.json":
        "c2149a2257a0a7a660793ffc6e82708d718124b0cc63c399843d82f7327e551d",
    "docs/implementation/office-v2/phase2/p0-604-cp083-native-lostack-two-receipts-2026-10-18.md":
        "15b9d3e96bb0dbd8f30b4ca69465b0ab7b7fb5dd11cddf0c1c2e82cc8f554f98",
    "docs/implementation/office-v2/phase2/p0-native-git-crash-durable-unknown-reconcile-2026-10-10.md":
        "a13b543057ef2945feb3344b114635365cb48ccfb9e244d75835d7edf74b7040",
    "docs/implementation/office-v2/phase2/p0-real-etcd-mtls-rbac-identity-denial-2026-10-10.md":
        "d7a6dc94678964dabc2029afbd185f3e127658e2b4580f3ebfbd8ed9eaa05e58",
    "docs/implementation/office-v2/phase2/p0-sameuid-sink-key-disposable-bypass-real-2026-10-10.md":
        "cfac0044b16eac8e7ee47b97ae4ebf0f5d64d256620be379fe02c75665de3256",
    "docs/implementation/office-v2/phase2/p0-604-owner-option-a-revocation-2026-10-16.json":
        "15a1c513f2dbc2da438d977e41f3c5c14a6929e7ec4499199116ed714c250271",
    "scripts/vf_office_v2_604_cp083_osuid_tls_localgit_lab.py":
        "ff7a648d99b2a4bdda057c0758017b90727c7ee637f660351b9bccaf2f42afe6",
    "scripts/vf_office_v2_604_cp083_native_lostack_two_receipts.py":
        "0d38f4e45f1d94a64167b72e0f57ca44efa73a758fc72fe368705294de737251",
    "scripts/vf_office_v2_604_cp082_tls_native_git_reconcile_lab.py":
        "fa108cfd9bea1aec38a9e7e4c1a3e369e6ba4be94eef413ea0ec0304bb1a8eee",
    "scripts/vf_office_v2_604_cp083_hardened_candidate.py":
        "83260c77846b34c4f459eaa812f477e51764fa1eee261af1d542a39dd561cd2c",
    "scripts/vf_office_v2_604_cp083_candidate_evidence_gate.py":
        "f9a7be4a854bd04634085ef6b91555941f05c78c78d4f12ae05180f15fb4b774",
    "scripts/vf_office_v2_604_owner_option_a_policy_gate.py":
        "33f42ccb00bb7d5ad407a24f1c315fc5b060cf9ce8188e55edd08d4d41309162",
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sealed_key(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def assigned(source, name):
    found = re.search(
        rf"{name} = \(\n\s*\"([0-9a-f]{{64}})\"", source)
    if found is None:
        found = re.search(rf"{name} = \"([0-9a-f]{{64}})\"", source)
    if found is None:
        raise AssertionError(name + " pin missing")
    return found.group(1)


def sensor_text():
    return SENSOR.read_text(encoding="utf-8")


class Gap6PinSplitTests(unittest.TestCase):
    def test_etcd_server_child_sees_only_allowlisted_keys(self):
        script = (
            "import json, os, pathlib, sys\n"
            "pathlib.Path(sys.argv[1]).write_text("
            "json.dumps(dict(os.environ), sort_keys=True))\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "child-env.json"
            lab = identity.AuthenticatedEtcd.__new__(identity.AuthenticatedEtcd)
            lab.root = root
            lab.args = [sys.executable, "-c", script, str(out)]
            lab.server = None
            lab.log = None
            poison = {
                "VF_CANARY_SECRET": "not-a-real-secret",
                "ETCDCTL_API": "2",
            }
            with mock.patch.dict(os.environ, poison, clear=False):
                with mock.patch.object(lab, "health", lambda: None):
                    lab.start()
            self.assertEqual(lab.server.wait(timeout=5), 0)
            lab.log.close()
            child = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(set(child), set(identity.ETCD_SERVER_ENV_REQUIRED))
        self.assertEqual(child["PATH"], "/usr/bin:/bin")
        self.assertEqual(child["HOME"], "/nonexistent")
        for name in poison:
            self.assertNotIn(name, child)
        source = Path(identity.__file__).read_text(encoding="utf-8")
        self.assertIn("env=env", source)
        self.assertNotIn("os.environ.copy()", source)

    def test_etcd_server_missing_or_extra_name_refuses_before_popen(self):
        def spawned(*args, **kwargs):
            raise AssertionError("etcd server spawned without a closed env")

        lab = identity.AuthenticatedEtcd.__new__(identity.AuthenticatedEtcd)
        lab.root = Path(".")
        lab.args = [sys.executable, "-c", "raise SystemExit(9)"]
        broken = dict(identity.etcd_server_env())
        del broken["PATH"]
        with mock.patch.object(identity, "etcd_server_env", lambda: broken):
            with mock.patch.object(identity.subprocess, "Popen", spawned):
                with self.assertRaises(RuntimeError) as caught:
                    lab.start()
        self.assertEqual(str(caught.exception), "REQUIRED_ENV_MISSING")
        extra = identity.etcd_server_env()
        extra["VF_CANARY_SECRET"] = "not-a-real-secret"
        with self.assertRaises(RuntimeError) as caught:
            identity.require_closed_env(extra, identity.ETCD_SERVER_ENV_REQUIRED)
        self.assertEqual(str(caught.exception), "REQUIRED_ENV_MISSING")

    def test_native_worker_env_hides_parent_names(self):
        script = (
            "import json, os, sys\n"
            "sys.stdout.write(json.dumps(dict(os.environ), sort_keys=True))\n"
        )
        source = Path(native.__file__).read_text(encoding="utf-8")
        self.assertEqual(source.count("env=require_git_env(bound_env())"), 3)
        self.assertNotIn("\nENV = git_subprocess_env()\n", source)
        self.assertNotIn("os.environ", source)
        poison = {
            "VF_CANARY_SECRET": "not-a-real-secret",
            "GIT_CONFIG_PARAMETERS": "'core.fsmonitor=/tmp/not-run'",
            "GIT_SSH_COMMAND": "/tmp/not-run",
        }
        with mock.patch.dict(os.environ, poison, clear=False):
            env = native.require_git_env(native.git_subprocess_env())
            proc = subprocess.run(
                [sys.executable, "-c", script],
                env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        child = json.loads(proc.stdout)
        self.assertEqual(set(child), set(native.GIT_ENV_REQUIRED))
        for name in poison:
            self.assertNotIn(name, child)
        self.assertNotEqual(child.get("PATH"), os.environ.get("PATH"))
        self.assertEqual(child["GIT_CONFIG_NOSYSTEM"], "1")
        self.assertEqual(child["GIT_CONFIG_COUNT"], "0")
        self.assertIn("vf604-git-home-", child["HOME"])
        self.assertTrue(Path(child["HOME"]).is_dir())
        self.assertFalse((Path(child["HOME"]) / ".gitconfig").exists())
        self.assertTrue(Path(child["XDG_CONFIG_HOME"]).is_dir())
        self.assertFalse((Path(child["XDG_CONFIG_HOME"]) / "git" / "config").exists())
        self.assertEqual(Path(child["GIT_CONFIG_GLOBAL"]).read_bytes(), b"")
        self.assertTrue(Path(child["GIT_EXEC_PATH"]).is_dir())
        self.assertEqual(child["GIT_AUTHOR_EMAIL"], "vf604@example.invalid")

    def test_poisoned_path_cannot_select_git(self):
        source = Path(native.__file__).read_text(encoding="utf-8")
        self.assertNotIn("shutil", source)
        self.assertNotIn("os.environ", source)
        self.assertEqual(native.FIXED_GIT_PATH, "/usr/bin:/bin")
        self.assertEqual(native.ENV["PATH"], native.FIXED_GIT_PATH)
        closed = native.require_git_env(native.git_subprocess_env())
        self.assertEqual(closed["PATH"], native.FIXED_GIT_PATH)
        self.assertEqual(set(closed), set(native.GIT_ENV_REQUIRED))
        resolved = Path(native.GIT_EXECUTABLE)
        self.assertTrue(resolved.is_absolute())
        if os.name == "nt":
            allowed = (
                Path(r"C:\Program Files\Git\cmd\git.exe"),
                Path(r"C:\Program Files\Git\bin\git.exe"),
            )
        else:
            allowed = (Path("/usr/bin/git"), Path("/bin/git"))
        self.assertIn(resolved, allowed)
        self.assertTrue(resolved.is_file())
        self.assertTrue(os.access(resolved, os.X_OK))
        self.assertIn("subprocess.run([GIT_EXECUTABLE]", source)
        probe = (
            "import json, subprocess, sys\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import vf_office_v2_604_native_git_crash_reconcile_offline as native\n"
            "env = native.require_git_env(native.ENV)\n"
            "proc = subprocess.run(['git', '--version'], env=env,\n"
            "    capture_output=True, text=True, timeout=10)\n"
            "sys.stdout.write(json.dumps({\n"
            "    'path': env['PATH'],\n"
            "    'built': native.git_subprocess_env()['PATH'],\n"
            "    'git': native.GIT_EXECUTABLE,\n"
            "    'rc': proc.returncode,\n"
            "    'out': proc.stdout + proc.stderr,\n"
            "}))\n"
        )
        with tempfile.TemporaryDirectory(prefix="vf604-path-poison-") as tmp:
            root = Path(tmp)
            poison = root / "poison-git-bin"
            poison.mkdir()
            fake = poison / "git"
            fake.write_text("#!/bin/sh\necho MALICIOUS_GIT_RAN\nexit 9\n", encoding="ascii")
            fake.chmod(0o755)
            if os.name == "nt":
                (poison / "git.cmd").write_text(
                    "@echo MALICIOUS_GIT_RAN\r\n@exit /b 9\r\n", encoding="ascii")
            probe_path = root / "probe.py"
            probe_path.write_text(probe, encoding="utf-8")
            child_env = dict(os.environ)
            child_env["PATH"] = str(poison) + os.pathsep + child_env.get("PATH", "")
            proc = subprocess.run(
                [sys.executable, "-B", str(probe_path), str(ROOT / "scripts")],
                env=child_env,
                cwd=str(ROOT / "scripts"),
                capture_output=True,
                text=True,
                timeout=15,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["path"], "/usr/bin:/bin")
        self.assertEqual(payload["built"], "/usr/bin:/bin")
        self.assertNotIn(str(poison), payload["path"])
        self.assertNotIn("MALICIOUS_GIT_RAN", payload["out"])
        self.assertIn(Path(payload["git"]), allowed)
        if os.name != "nt":
            self.assertEqual(payload["rc"], 0)
            self.assertIn("git version", payload["out"])

    def test_poisoned_home_cannot_run_gitconfig(self):
        source = Path(native.__file__).read_text(encoding="utf-8")
        self.assertNotIn("os.environ", source)
        self.assertNotIn("os.getenv", source)
        with tempfile.TemporaryDirectory(prefix="vf604-home-poison-") as tmp:
            root = Path(tmp)
            home = root / "home"
            home.mkdir()
            xdg = root / "xdg"
            (xdg / "git").mkdir(parents=True)
            marker = root / "marker"
            if os.name == "nt":
                hook = root / "hook.py"
                hook.write_text(
                    "import pathlib, sys\n"
                    "pathlib.Path(sys.argv[1]).write_text('MALICIOUS_HOME_RAN')\n",
                    encoding="ascii",
                )
                hook_cmd = subprocess.list2cmdline([sys.executable, str(hook), str(marker)])
            else:
                hook = root / "hook.sh"
                hook.write_text(
                    "#!/bin/sh\necho MALICIOUS_HOME_RAN >> \"$1\"\n",
                    encoding="ascii",
                )
                hook.chmod(0o755)
                hook_cmd = f"{hook} {marker}"
            config = f"[core]\n\tfsmonitor = {hook_cmd}\n"
            (home / ".gitconfig").write_text(config, encoding="ascii")
            (xdg / "git" / "config").write_text(config, encoding="ascii")
            system = root / "system.gitconfig"
            system.write_text(config, encoding="ascii")
            fake_exec = root / "fake-exec"
            fake_exec.mkdir()
            repo = root / "repo"
            repo.mkdir()
            if os.name != "nt":
                control_env = {
                    "PATH": "/usr/bin:/bin",
                    "LC_ALL": "C",
                    "HOME": str(home),
                    "GIT_TERMINAL_PROMPT": "0",
                }
                subprocess.run(
                    [native.GIT_EXECUTABLE, "init", "-q", str(repo)],
                    env=control_env, check=True, timeout=10,
                )
                control = subprocess.run(
                    [native.GIT_EXECUTABLE, "-C", str(repo), "status", "--porcelain"],
                    env=control_env, capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(control.returncode, 0, control.stderr)
                self.assertTrue(marker.is_file(), "fsmonitor fixture did not run")
                marker.unlink()
            probe = (
                "import json, subprocess, sys, tempfile\n"
                "from pathlib import Path\n"
                "sys.path.insert(0, sys.argv[1])\n"
                "import vf_office_v2_604_native_git_crash_reconcile_offline as native\n"
                "env = native.require_git_env(native.ENV)\n"
                "repo = Path(tempfile.mkdtemp(prefix='vf604-home-repo-'))\n"
                "init = subprocess.run([native.GIT_EXECUTABLE, 'init', '-q', str(repo)],\n"
                "    env=env, capture_output=True, text=True, timeout=10)\n"
                "status = subprocess.run([native.GIT_EXECUTABLE, '-C', str(repo), 'status', '--porcelain'],\n"
                "    env=env, capture_output=True, text=True, timeout=10)\n"
                "marker = Path(sys.argv[2])\n"
                "out = (init.stdout or '') + (init.stderr or '') + (status.stdout or '') + (status.stderr or '')\n"
                "sys.stdout.write(json.dumps({\n"
                "    'keys': sorted(env),\n"
                "    'home': env['HOME'],\n"
                "    'xdg': env['XDG_CONFIG_HOME'],\n"
                "    'global': env['GIT_CONFIG_GLOBAL'],\n"
                "    'nosystem': env['GIT_CONFIG_NOSYSTEM'],\n"
                "    'count': env['GIT_CONFIG_COUNT'],\n"
                "    'exec': env['GIT_EXEC_PATH'],\n"
                "    'home_dir': Path(env['HOME']).is_dir(),\n"
                "    'home_gitconfig': (Path(env['HOME']) / '.gitconfig').exists(),\n"
                "    'xdg_dir': Path(env['XDG_CONFIG_HOME']).is_dir(),\n"
                "    'xdg_git_config': (Path(env['XDG_CONFIG_HOME']) / 'git' / 'config').exists(),\n"
                "    'global_empty': Path(env['GIT_CONFIG_GLOBAL']).read_bytes() == b'',\n"
                "    'exec_dir': Path(env['GIT_EXEC_PATH']).is_dir(),\n"
                "    'rc': status.returncode,\n"
                "    'marker': marker.is_file(),\n"
                "    'out': out,\n"
                "}))\n"
            )
            probe_path = root / "probe.py"
            probe_path.write_text(probe, encoding="utf-8")
            child_env = dict(os.environ)
            child_env.update({
                "HOME": str(home),
                "USERPROFILE": str(home),
                "XDG_CONFIG_HOME": str(xdg),
                "GIT_EXEC_PATH": str(fake_exec),
                "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
                "GIT_CONFIG_SYSTEM": str(system),
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.fsmonitor",
                "GIT_CONFIG_VALUE_0": hook_cmd,
                "GIT_CONFIG_PARAMETERS": "'core.fsmonitor=" + hook_cmd + "'",
                "GIT_SSH_COMMAND": hook_cmd,
            })
            proc = subprocess.run(
                [sys.executable, "-B", str(probe_path), str(ROOT / "scripts"), str(marker)],
                env=child_env,
                cwd=str(ROOT / "scripts"),
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["keys"], sorted(native.GIT_ENV_REQUIRED))
        self.assertNotEqual(payload["home"], str(home))
        self.assertIn("vf604-git-home-", payload["home"])
        self.assertTrue(payload["home_dir"])
        self.assertFalse(payload["home_gitconfig"])
        self.assertFalse(Path(payload["home"]).exists())
        self.assertNotEqual(payload["xdg"], str(xdg))
        self.assertTrue(payload["xdg_dir"])
        self.assertFalse(payload["xdg_git_config"])
        self.assertEqual(payload["nosystem"], "1")
        self.assertEqual(payload["count"], "0")
        self.assertTrue(payload["global_empty"])
        self.assertNotEqual(payload["global"], str(home / ".gitconfig"))
        self.assertNotEqual(payload["exec"], str(fake_exec))
        self.assertTrue(payload["exec_dir"])
        self.assertFalse(payload["marker"])
        self.assertNotIn("MALICIOUS_HOME_RAN", payload["out"])
        self.assertEqual(payload["rc"], 0)
        for leaked in (
            "USERPROFILE", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_KEY_0",
            "GIT_CONFIG_VALUE_0", "GIT_CONFIG_PARAMETERS", "GIT_SSH_COMMAND",
        ):
            self.assertNotIn(leaked, payload["keys"])

    def test_native_missing_or_extra_name_refuses_before_spawn(self):
        def spawned(*args, **kwargs):
            raise AssertionError("git spawned without a closed env")

        broken = dict(native.git_subprocess_env())
        del broken["PATH"]
        with mock.patch.object(native, "ENV", broken):
            with mock.patch.object(native.subprocess, "run", spawned):
                with self.assertRaises(RuntimeError) as caught:
                    native.git_raw(["--version"])
        self.assertEqual(str(caught.exception), "REQUIRED_ENV_MISSING")
        extra = native.git_subprocess_env()
        extra["VF_CANARY_SECRET"] = "not-a-real-secret"
        with self.assertRaises(RuntimeError) as caught:
            native.require_git_env(extra)
        self.assertEqual(str(caught.exception), "REQUIRED_ENV_MISSING")

    def test_identity_live_pin_differs_from_receipt_pin(self):
        sensor = sensor_text()
        live = assigned(sensor, "identity_live_sha")
        receipt = assigned(sensor, "identity_receipt_sha")
        self.assertEqual(live, sha256(identity.__file__))
        self.assertEqual(cp081.PIN_IDENTITY, live)
        self.assertEqual(sameuid.BASE_SOURCE_SHA, live)
        self.assertEqual(receipt, IDENTITY_RECEIPT)
        self.assertNotEqual(live, receipt)
        self.assertIn("!= identity_live_sha", sensor)
        self.assertIn("!= identity_receipt_sha", sensor)

    def test_merging_identity_pins_fails(self):
        sensor = sensor_text()
        live = assigned(sensor, "identity_live_sha")
        receipt = assigned(sensor, "identity_receipt_sha")
        self.assertNotEqual(sha256(identity.__file__), receipt)
        self.assertNotEqual(live, receipt)
        drift = sensor.split("#604 ephemeral mTLS/RBAC denial source SHA drift", 1)[0]
        self.assertIn("!= identity_live_sha", drift[-180:])
        self.assertNotIn("!= identity_receipt_sha", drift[-180:])
        cp081_json = json.loads((PHASE2 / "p0-604-cp081-mtls-atomic-2026-10-16.json").read_text(encoding="utf-8"))
        cp082_json = json.loads((PHASE2 / "p0-604-cp082-tls-localgit-unknown-2026-10-16.json").read_text(encoding="utf-8"))
        self.assertEqual(cp081_json["identity_helper_sha256"], receipt)
        self.assertEqual(
            cp082_json["preexisting_dependencies"]["tls_rbac_identity_source_sha256"],
            receipt)
        self.assertNotEqual(cp081_json["identity_helper_sha256"], live)

    def test_identity_receipt_byte_change_fails(self):
        path = PHASE2 / "p0-604-cp081-mtls-atomic-2026-10-16.json"
        raw = path.read_bytes()
        self.assertEqual(sha256(path), SEALED[sealed_key(path)])
        self.assertIn(IDENTITY_RECEIPT.encode("ascii"), raw)
        flipped = bytes([raw[0] ^ 1]) + raw[1:]
        self.assertNotEqual(hashlib.sha256(flipped).hexdigest(), SEALED[sealed_key(path)])

    def test_cp081_live_pin_differs_from_receipt_pin(self):
        sensor = sensor_text()
        live = assigned(sensor, "cp081_live_sha")
        receipt = assigned(sensor, "cp081_receipt_sha")
        self.assertEqual(live, sha256(cp081.__file__))
        self.assertEqual(receipt, CP081_RECEIPT)
        self.assertEqual(osuid.CP081_LIVE_SHA, live)
        self.assertEqual(osuid.CP081_RECEIPT_SHA, receipt)
        self.assertNotEqual(live, receipt)
        gate = Path(osuid.__file__).read_text(encoding="utf-8")
        self.assertIn('payload.get("cp081_source_sha256") == CP081_RECEIPT_SHA', gate)
        self.assertIn("sha(P81.read_bytes()) == CP081_LIVE_SHA", gate)
        self.assertNotIn('("cp081_source_sha256", P81)', gate)
        self.assertIn("!= cp081_live_sha", sensor)
        self.assertIn("!= cp081_receipt_sha", sensor)

    def test_merging_cp081_pins_fails(self):
        self.assertNotEqual(osuid.CP081_LIVE_SHA, osuid.CP081_RECEIPT_SHA)
        evidence = json.loads(osuid.EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(osuid.validate(evidence)["security_admission"], "RED")
        with mock.patch.object(osuid, "CP081_LIVE_SHA", osuid.CP081_RECEIPT_SHA):
            with self.assertRaises(osuid.Rejected) as caught:
                osuid.validate(evidence)
        self.assertEqual(str(caught.exception), "CP081_PINS_MERGED")

    def test_osuid_evidence_byte_change_fails(self):
        raw = osuid.EVIDENCE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), osuid.EXPECTED_EVIDENCE_SHA)
        self.assertEqual(osuid.EXPECTED_EVIDENCE_SHA, SEALED[
            "docs/implementation/office-v2/phase2/p0-604-cp083-osuid-tls-localgit-2026-10-17.json"])
        self.assertIn(CP081_RECEIPT.encode("ascii"), raw)
        flipped = bytes([raw[10] ^ 1]) + raw[11:]
        self.assertNotEqual(hashlib.sha256(flipped).hexdigest(), osuid.EXPECTED_EVIDENCE_SHA)

    def test_native_live_pin_differs_from_receipt_pin(self):
        sensor = sensor_text()
        live = assigned(sensor, "native_live_sha")
        receipt = assigned(sensor, "native_receipt_sha")
        self.assertEqual(live, sha256(native.__file__))
        self.assertEqual(receipt, NATIVE_RECEIPT)
        self.assertEqual(lostack.NATIVE_LIVE_SHA, live)
        self.assertEqual(lostack.NATIVE_RECEIPT_SHA, receipt)
        self.assertNotEqual(live, receipt)
        gate = Path(lostack.__file__).read_text(encoding="utf-8")
        self.assertIn("(NATIVE, NATIVE_LIVE_SHA)", gate)
        self.assertIn("NATIVE_RECEIPT_SHA", gate)
        self.assertNotIn("(NATIVE, NATIVE_RECEIPT_SHA)", gate)
        self.assertNotIn("(NATIVE, NATIVE_SHA)", gate)
        self.assertIn("!= native_live_sha", sensor)
        self.assertIn("!= native_receipt_sha", sensor)

    def test_merging_native_pins_fails(self):
        self.assertNotEqual(lostack.NATIVE_LIVE_SHA, lostack.NATIVE_RECEIPT_SHA)
        evidence = lostack.read_evidence(lostack.EVIDENCE)
        result = lostack.validate(evidence)
        self.assertEqual(result["security_admission"], "RED")
        with mock.patch.object(lostack, "NATIVE_LIVE_SHA", lostack.NATIVE_RECEIPT_SHA):
            with self.assertRaises(lostack.Refused) as caught:
                lostack.validate(evidence)
        self.assertEqual(str(caught.exception), "NATIVE_PINS_MERGED")

    def test_lostack_receipt_byte_change_fails(self):
        raw = lostack.EVIDENCE.read_bytes()
        sealed = SEALED[
            "docs/implementation/office-v2/phase2/p0-604-cp083-native-lostack-two-receipts-2026-10-18.json"]
        self.assertEqual(hashlib.sha256(raw).hexdigest(), sealed)
        self.assertEqual(raw.count(NATIVE_RECEIPT.encode("ascii")), 3)
        flipped = bytes([raw[20] ^ 1]) + raw[21:]
        self.assertNotEqual(hashlib.sha256(flipped).hexdigest(), sealed)

    def test_sameuid_live_pin_differs_from_historical_receipt(self):
        sensor = sensor_text()
        live = assigned(sensor, "sameuid_live_sha")
        self.assertEqual(live, sha256(sameuid.__file__))
        self.assertNotEqual(live, SAMEUID_HISTORICAL)
        self.assertNotEqual(sameuid.BASE_SOURCE_SHA, IDENTITY_RECEIPT)
        note = PHASE2 / "p0-sameuid-sink-key-disposable-bypass-real-2026-10-10.md"
        text = note.read_text(encoding="utf-8")
        self.assertIn(SAMEUID_HISTORICAL, text)
        self.assertIn(IDENTITY_RECEIPT, text)
        self.assertEqual(sha256(note), SEALED[sealed_key(note)])

    def test_sealed_comparison_files_stay_byte_identical(self):
        for rel, digest in SEALED.items():
            self.assertEqual(sha256(ROOT / rel), digest, rel)

    def test_sealed_key_uses_forward_slashes(self):
        source = Path(__file__).read_text(encoding="utf-8")
        body = source.split("def sealed_key", 1)[1].split("def assigned", 1)[0]
        self.assertIn(".as_posix()", body)
        self.assertNotIn("str(", body)
        note = PHASE2 / "p0-sameuid-sink-key-disposable-bypass-real-2026-10-10.md"
        key = sealed_key(note)
        self.assertEqual(
            key,
            "docs/implementation/office-v2/phase2/"
            "p0-sameuid-sink-key-disposable-bypass-real-2026-10-10.md")
        self.assertNotIn("\\", key)
        self.assertNotIn(key.replace("/", "\\"), SEALED)

    def test_sensor_receipt_fields_stay_on_receipt_pins(self):
        sensor = sensor_text()
        for line in (
            'test_script_sha256") != cp081_receipt_sha',
            'identity_helper_sha256") != identity_receipt_sha',
            'cp081_source_sha256") != cp081_receipt_sha',
            'tls_rbac_identity_source_sha256") != identity_receipt_sha',
            'native_local_git_sqlite_source_sha256") != native_receipt_sha',
        ):
            self.assertIn(line, sensor)
        self.assertNotIn('identity_helper_sha256") != identity_live_sha', sensor)
        self.assertNotIn('test_script_sha256") != cp081_live_sha', sensor)

    def test_lostack_raw_native_hash_uses_receipt_pin(self):
        gate = Path(lostack.__file__).read_text(encoding="utf-8")
        self.assertIn(
            'r.get("native_implementation_sha256") == NATIVE_RECEIPT_SHA', gate)
        self.assertNotIn(
            'r.get("native_implementation_sha256") == NATIVE_LIVE_SHA', gate)


if __name__ == "__main__":
    unittest.main()
