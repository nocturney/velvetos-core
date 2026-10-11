#!/usr/bin/env python3
"""#612: tightly scoped hosted Docker OS-boundary negative lab.

selftest: static hashes, Docker arg checks and negative mutations only; does
NOT start Docker, models or generated code on a user's machine.
run: only on an ephemeral GitHub-hosted Ubuntu 24.04 runner with no repository
write permissions; three fixed public synthetic fixtures run in isolated
non-root, no-network containers. This does NOT attest against kernel escapes,
supply an exclusive Git Sink, or authorize arbitrary untrusted source.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

import vf_office_v2_p0_diverse_task_fixtures as fixtures
import vf_office_v2_p0_hosted_synthetic_qa_lab as hosted

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "velvetos.office-v2.p0-hosted-docker-boundary-negative.v0"
IMAGE_TAG = "python:3.11-slim-bookworm"
# Discover image digest on a throwaway CI runner first. Do not call that a
# cross-run image pin. Replace with exact observed manifest digest after
# independently verifying the first read-only lab; then re-run exact head.
EXPECTED_IMAGE_DIGEST = ""
SOURCE_CASES = (
    {"label": "mac-existing-tag", "fixture": "canonical-tag-v1",
     "source": "docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10/parallel-mac-tag-20261010.py",
     "sha256": "b2ec92fed514a5e0e37aeca31155fe0d04cdfde70a3d46fafeeb9a09b0ef1ccb",
     "expected_good": True},
    {"label": "win-existing-merge", "fixture": "merge-windows-v1",
     "source": "docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10/parallel-win-merge-20261010.py",
     "sha256": "e625ea816531000df82d15144f3155ebd59a868a2dd89c81c1f254115bafb2b9",
     "expected_good": True},
    {"label": "known-broken-public-seed", "fixture": "canonical-tag-v1",
     "source": None, "sha256": None, "expected_good": False},
)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
DOCKER_ID = re.compile(r"[0-9a-f]{64}\Z")

# This is human-authored verifier code, NOT model-generated production source.
# All imports/execution of pinned generated code occur only inside a temporary
# Linux container configured with no network or host credentials.
INNER = r'''import errno
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    label, target_name, source_sha, test_sha, hidden_sha, expected, host_only_path = sys.argv[1:]
    root = Path("/fixture")
    source = root / target_name
    test = next((root / "tests").glob("test_*.py"))
    hidden = root / "hidden.py"
    require(source.is_file() and sha(source.read_bytes()) == source_sha, "SOURCE_SHA_CHANGED")
    require(sha(test.read_bytes()) == test_sha, "VISIBLE_TEST_SHA_CHANGED")
    require(sha(hidden.read_bytes()) == hidden_sha, "HIDDEN_TEST_SHA_CHANGED")
    require(os.getuid() == os.geteuid() == 65534, "WORKER_IS_NOT_NOBODY")
    require(not Path("/var/run/docker.sock").exists(), "DOCKER_SOCKET_VISIBLE")
    require(not any(k in os.environ for k in
            ("GITHUB_TOKEN", "GH_TOKEN", "GIT_ASKPASS", "SSH_ASKPASS",
             "AWS_ACCESS_KEY_ID", "GOOGLE_APPLICATION_CREDENTIALS")),
            "SENSITIVE_TOKEN_VISIBLE")
    require(not Path(host_only_path).exists(), "HOST_CANARY_PATH_VISIBLE")
    try:
        os.setuid(0)
    except PermissionError:
        privilege_escalation_denied = True
    else:
        raise RuntimeError("SETUID_ROOT_WAS_ALLOWED")
    for p in (root / "forbidden.write", Path("/etc/forbidden.vf-office")):
        try:
            p.write_bytes(b"should be refused")
        except OSError:
            pass
        else:
            raise RuntimeError("READ_ONLY_WRITE_SUCCEEDED_" + str(p))
    require(Path("/tmp").is_dir(), "TMPFS_MISSING")
    temp_probe = Path("/tmp/isolated-tmpfs-probe")
    temp_probe.write_bytes(b"local-only")
    require(temp_probe.read_bytes() == b"local-only", "TMPFS_WRITE_DENIED")
    temp_probe.unlink()
    require(set(os.listdir("/sys/class/net")) == {"lo"}, "EXTRA_NETWORK_INTERFACE_PRESENT")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            sock.connect(("1.1.1.1", 443))
    except OSError as exc:
        require(exc.errno in (errno.ENETUNREACH, errno.EHOSTUNREACH,
                errno.EPERM, errno.EACCES), "NETWORK_PROBE_OTHER_FAILURE")
        network_denied = True
    else:
        raise RuntimeError("NETWORK_EGRESS_ALLOWED")
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin",
           "HOME": "/tmp", "TMPDIR": "/tmp",
           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    def qa(argv):
        return subprocess.run(argv, cwd="/fixture", env=env,
                              stdin=subprocess.DEVNULL, capture_output=True,
                              timeout=12)
    unit = qa([sys.executable, "-B", "-m", "unittest", "discover",
               "-s", "tests", "-q"])
    hidden_run = qa([sys.executable, "-B", str(hidden)])
    visible_pass = unit.returncode == 0 and b"Ran 3 tests" in unit.stderr
    hidden_pass = hidden_run.returncode == 0 and hidden_run.stdout.strip() == b"QA_HIDDEN_12_PASS"
    good = expected == "true"
    require(visible_pass == good and hidden_pass == good,
            "INDEPENDENT_QA_UNEXPECTED_" + label)
    return {"status": "PASS_CONTAINER_ISOLATION_NEGATIVES_AND_QA",
            "label": label, "source_sha256": source_sha,
            "visible_3": visible_pass, "hidden_12": hidden_pass,
            "negative_seed_expected": not good,
            "network_denied": network_denied,
            "read_only_root_and_mount": True,
            "host_canary_invisible": True,
            "no_docker_socket": True,
            "no_exported_github_token": True,
            "uid_65534": True,
            "setuid_root_denied": privilege_escalation_denied,
            "tmpfs_only_write": True,
            "model_calls": 0, "production_authority": False}

if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True))
    except Exception as e:
        print(json.dumps({"status":"FAIL_CLOSED", "reason": str(e)[:150],
                          "production_authority":False}, sort_keys=True))
        raise SystemExit(2)
'''


class Refused(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Refused(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def docker_args(image_id, fixture_dir, host_only_path, entry):
    # No shell interpolation; argv is a fixed contract and every file mount is
    # read-only. Image ID comes from a pull validated by OCI RepoDigest.
    return [
        "docker", "create", "--network=none", "--read-only",
        "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
        "--pids-limit=32", "--memory=256m", "--cpus=1",
        "--user=65534:65534", "--pid=private", "--ipc=none",
        "--tmpfs=/tmp:rw,noexec,nosuid,size=32m,mode=1777",
        "--ulimit=nofile=64:64", "--ulimit=fsize=2097152:2097152",
        "--mount=type=bind,src=" + str(fixture_dir) + ",dst=/fixture,readonly",
        "--workdir=/fixture", "--env=PYTHONDONTWRITEBYTECODE=1",
        "--env=PYTHONUNBUFFERED=1", image_id,
        "python", "-B", "/fixture/qa_inner.py",
        entry["label"], fixtures.catalog()[entry["fixture"]]["target"],
        entry["sha256"], entry["test_sha256"], entry["hidden_sha256"],
        "true" if entry["expected_good"] else "false", str(host_only_path),
    ]


def assert_docker_plan(candidate, image_id, fixture_dir, host_only_path, entry):
    require(candidate == docker_args(image_id, fixture_dir, host_only_path, entry),
            "DOCKER_SECURE_ARGS_DRIFT_OR_EXTRA_CAPABILITY")
    require(image_id.startswith("sha256:") and
            SHA256.fullmatch(image_id[7:]), "IMAGE_ID_IS_NOT_DIGEST_PINNED")
    require(Path(fixture_dir).is_absolute() and Path(host_only_path).is_absolute()
            and Path(host_only_path) != Path(fixture_dir),
            "HOST_CANARY_NOT_SEPARATE")
    return True


def check_case(entry):
    require(entry in SOURCE_CASES and type(entry) is dict, "UNREGISTERED_ARTIFACT")
    row = fixtures.catalog()[entry["fixture"]]
    if entry["source"] is None:
        code = row["source"].encode("utf-8")
    else:
        src = ROOT / entry["source"]
        require(src.is_file() and not src.is_symlink(), "SOURCE_NOT_LOCAL_REGULAR")
        code = src.read_bytes()
        require(sha(code) == entry["sha256"], "SOURCE_SHA_MISMATCH")
    require(len(code) < 16384, "SOURCE_BUDGET_EXCEEDED")
    return dict(entry, sha256=sha(code),
                test_sha256=sha(row["visible"].encode()),
                hidden_sha256=sha(row["hidden"].encode())), code, row


def local_selftest():
    checks = []
    for entry in SOURCE_CASES:
        recorded, code, row = check_case(entry)
        require(recorded["sha256"] == sha(code), "SOURCE_INCONSISTENT")
        checks.append("pinned_" + entry["label"])
    for change in (
        {"source": "/root/private.py"}, {"sha256": "0"*64},
        {"fixture": "not-a-task"}, {"label": "production"},
        {"expected_good": False}, {"root_token": "secret"},
    ):
        bad = dict(SOURCE_CASES[0], **change)
        try: check_case(bad)
        except (Refused, KeyError): checks.append("source_tamper_denied")
        else: raise Refused("FALSE_ACCEPTED_UNPINNED_SOURCE")
    valid, code, row = check_case(SOURCE_CASES[0])
    valid_image = "sha256:" + "a"*64
    # Synthetic paths must be native absolute paths on Windows and macOS;
    # no actual directory or Docker mount is created by selftest.
    synthetic_root = Path(tempfile.gettempdir()).resolve()
    fdir = synthetic_root / "vf-office-fixture-synthetic"
    canary = synthetic_root / "vf-office-hostonly-synthetic" / "canary.key"
    good = docker_args(valid_image, fdir, canary, valid)
    assert_docker_plan(good, valid_image, fdir, canary, valid)
    checks.append("exact_docker_flags")
    tamper = (
        ("--network=none", "--network=bridge"),
        ("--read-only", "--privileged"),
        ("--cap-drop=ALL", "--cap-add=SYS_ADMIN"),
        ("--security-opt=no-new-privileges:true", "--security-opt=seccomp=unconfined"),
        ("--pids-limit=32", "--pids-limit=4096"),
        ("--memory=256m", "--memory=16g"),
        ("--cpus=1", "--cpus=8"),
        ("--user=65534:65534", "--user=0:0"),
        ("--pid=private", "--pid=host"),
        ("--ipc=none", "--ipc=host"),
        ("--tmpfs=/tmp:rw,noexec,nosuid,size=32m,mode=1777",
         "--tmpfs=/tmp:rw,exec,size=2g"),
        ("--workdir=/fixture", "--workdir=/root"),
        ("--env=PYTHONDONTWRITEBYTECODE=1", "--env=GITHUB_TOKEN=fake"),
    )
    for old, new in tamper:
        wrong = copy.deepcopy(good)
        wrong[wrong.index(old)] = new
        try: assert_docker_plan(wrong, valid_image, fdir, canary, valid)
        except Refused: checks.append("unsafe_docker_flag_denied")
        else: raise Refused("FALSE_ACCEPTED_DOCKER_FLAG_" + old)
    require(len(checks) == 23, "SELFTEST_NEGATIVE_COUNT_DRIFT")
    return {"status": "PASS_STATIC_NO_UNTRUSTED_EXECUTION",
            "tests": len(checks), "docker_invocations": 0,
            "generated_source_subprocesses": 0, "git_write_calls": 0,
            "model_invocations": 0, "image_digest_crossrun_pin_present":
            bool(EXPECTED_IMAGE_DIGEST), "production_authority": False}


def docker_command(args, timeout=35):
    x = subprocess.run(args, capture_output=True, text=True,
                       errors="replace", timeout=timeout,
                       stdin=subprocess.DEVNULL)
    require(x.returncode == 0, "DOCKER_OP_FAILED_" + args[1] +
            "_" + x.stderr[:140].replace("\n", " "))
    return x.stdout.strip()


def inspect_cid(cid, host_dir, image_id):
    obj = json.loads(docker_command(["docker", "inspect", cid], timeout=12))
    require(type(obj) is list and len(obj) == 1, "DOCKER_INSPECT_MISSING")
    val = obj[0]
    host = val["HostConfig"]
    conf = val["Config"]
    mounts = val["Mounts"]
    require(val["Image"] == image_id and conf["User"] == "65534:65534",
            "IMAGE_OR_WORKER_UID_WRONG")
    require(host["NetworkMode"] == "none" and host["ReadonlyRootfs"] is True
            and host["Privileged"] is False
            and host["CapDrop"] == ["ALL"]
            and any(str(i).startswith("no-new-privileges") for i in host["SecurityOpt"])
            and host["PidsLimit"] == 32 and host["Memory"] == 268435456
            and host["NanoCpus"] == 1000000000
            and host["IpcMode"] == "none" and host["PidMode"] == "private",
            "HOST_DOCKER_SECURITY_CONFIG_DRIFT")
    require(type(mounts) is list and len(mounts) == 1
            and mounts[0]["Type"] == "bind"
            and mounts[0]["Source"] == str(host_dir)
            and mounts[0]["Destination"] == "/fixture"
            and mounts[0]["RW"] is False, "UNEXPECTED_HOST_MOUNT")
    require(not any(s.startswith("GITHUB_TOKEN=") or s.startswith("GH_TOKEN=")
                    or s.startswith("AWS_ACCESS_KEY_ID=")
                    for s in conf.get("Env", [])), "CONTAINER_TOKEN_EXPORT")
    return {"network": host["NetworkMode"], "read_only": True,
            "uid": conf["User"], "cap_drop": host["CapDrop"],
            "security_opt": host["SecurityOpt"],
            "pids_limit": host["PidsLimit"], "memory_bytes": host["Memory"],
            "cpu_nano": host["NanoCpus"], "mount_count": len(mounts)}


def run_real_hosted_lab():
    hosted.runner_context_check(os.environ)
    hosted.no_persisted_checkout_auth()
    require(os.environ.get("RUNNER_OS") == "Linux"
            and os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
            and os.environ.get("GITHUB_EVENT_NAME") == "pull_request",
            "PR_ONLY_INITIAL_CONTAINER_EXPERIMENT")
    require(os.environ.get("GITHUB_RUN_ID", "").isdigit(),
            "NO_GITHUB_WORKFLOW_EVIDENCE_ID")
    start = time.monotonic()
    require(docker_command(["docker", "version", "--format", "{{.Server.Version}}"],
                           timeout=12), "DOCKER_DAEMON_NOT_AVAILABLE")
    docker_command(["docker", "pull", "--quiet", IMAGE_TAG], timeout=125)
    image = json.loads(docker_command(["docker", "image", "inspect", IMAGE_TAG],
                                      timeout=12))[0]
    image_id = image["Id"]
    digs = image["RepoDigests"]
    require(image_id.startswith("sha256:") and SHA256.fullmatch(image_id[7:])
            and type(digs) is list and len(digs) >= 1, "BAD_OCI_IMAGE_ID")
    matching = [x for x in digs if x.startswith("python@sha256:")
                and SHA256.fullmatch(x.split("sha256:", 1)[-1])]
    require(len(matching) >= 1, "OCI_REPODIGEST_UNAVAILABLE")
    digest = sorted(matching)[0]
    image_is_crossrun_pinned = bool(EXPECTED_IMAGE_DIGEST) and digest == EXPECTED_IMAGE_DIGEST
    require(not EXPECTED_IMAGE_DIGEST or image_is_crossrun_pinned,
            "PULLED_OCI_DIGEST_CHANGED_FROM_APPROVED_PIN")
    results = []
    for raw in SOURCE_CASES:
        entry, source, row = check_case(raw)
        with tempfile.TemporaryDirectory(prefix="vf-p0-container-fixture-") as td, \
             tempfile.TemporaryDirectory(prefix="vf-p0-host-only-canary-") as secret_dir:
            work = Path(td)
            canary = Path(secret_dir) / "sink-canary.key"
            canary.write_text("SYNTHETIC_NO_REAL_TOKEN", encoding="ascii")
            test = work / row["test"]
            test.parent.mkdir(parents=True)
            target = work / row["target"]
            target.write_bytes(source)
            test.write_text(row["visible"], encoding="utf-8")
            (work / "hidden.py").write_text(row["hidden"], encoding="utf-8")
            (work / "qa_inner.py").write_text(INNER, encoding="utf-8")
            for p in [target, test, work / "hidden.py", work / "qa_inner.py"]:
                p.chmod(0o644)
            (work / "tests").chmod(0o755)
            work.chmod(0o755)
            args = docker_args(image_id, work, canary, entry)
            assert_docker_plan(args, image_id, work, canary, entry)
            cid = None
            try:
                cid = docker_command(args, timeout=18)
                require(DOCKER_ID.fullmatch(cid), "BAD_OWNED_CONTAINER_ID")
                config = inspect_cid(cid, work, image_id)
                reply = docker_command(["docker", "start", "--attach", cid], timeout=38)
                recorded = json.loads(docker_command(
                    ["docker", "inspect", cid], timeout=12))[0]
                require(recorded["State"]["ExitCode"] == 0
                        and recorded["State"]["Status"] == "exited",
                        "CONTAINER_PROCESS_DID_NOT_EXIT_ZERO")
                parsed = [json.loads(line) for line in reply.splitlines()
                          if line.startswith("{") and line.endswith("}")]
                require(len(parsed) == 1 and
                        parsed[0]["status"] == "PASS_CONTAINER_ISOLATION_NEGATIVES_AND_QA"
                        and parsed[0]["source_sha256"] == entry["sha256"]
                        and parsed[0]["visible_3"] is entry["expected_good"]
                        and parsed[0]["hidden_12"] is entry["expected_good"]
                        and parsed[0]["network_denied"] is True
                        and parsed[0]["host_canary_invisible"] is True
                        and parsed[0]["no_exported_github_token"] is True
                        and parsed[0]["setuid_root_denied"] is True
                        and parsed[0]["uid_65534"] is True,
                        "CHILD_QA_OR_SECURITY_NEGATIVES_FAILED")
                results.append({"label": entry["label"],
                                "source_sha256": entry["sha256"],
                                "visible_3": parsed[0]["visible_3"],
                                "hidden_12": parsed[0]["hidden_12"],
                                "negative_control": not entry["expected_good"],
                                "network_denied": True,
                                "host_canary_invisible": True,
                                "docker_inspection": config})
            finally:
                if cid and DOCKER_ID.fullmatch(cid):
                    docker_command(["docker", "rm", "--force", cid], timeout=16)
    return {"schema": SCHEMA,
            "status": ("PASS_PINNED_CONTAINER_BOUNDARY_LAB" if
                       image_is_crossrun_pinned else
                       "PASS_DISCOVERY_ONLY_IMAGE_NOT_CROSSRUN_PINNED"),
            "github_run_id": os.environ["GITHUB_RUN_ID"],
            "image_repo_digest": digest,
            "image_id": image_id,
            "image_crossrun_digest_pinned": image_is_crossrun_pinned,
            "results": results,
            "accepted_historical_sources": 2,
            "new_model_outputs": 0,
            "negative_seed_qa_rejected": True,
            "network_isolation_probe_pass": True,
            "no_host_git_credentials_mounted": True,
            "no_cross_host_lease_or_git_sink": True,
            "arbitrary_untrusted_code_proven_secure": False,
            "host_kernel_escape_resistance_proven": False,
            "customer_or_production_authority": False,
            "local_windows_system_execution_unblocked": False,
            "model_invocations": 0, "incremental_paid_api_usd": 0,
            "elapsed_seconds": round(time.monotonic()-start, 3)}


def main():
    require(len(sys.argv) == 2 and sys.argv[1] in ("selftest", "run"),
            "EXPECTED_SELFTEST_OR_RUN")
    result = local_selftest() if sys.argv[1] == "selftest" else run_real_hosted_lab()
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refused, hosted.Refused, OSError, ValueError, KeyError,
            TypeError, TimeoutError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:180],
                          "model_invocations": 0, "production_authority": False},
                         sort_keys=True))
        raise SystemExit(2)
