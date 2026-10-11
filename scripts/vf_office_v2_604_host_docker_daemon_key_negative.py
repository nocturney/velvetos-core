#!/usr/bin/env python3
"""#604: prove the Docker HOST daemon, unlike a sibling guest, can
initiate synthetic key USE inside the signer guest without exporting bytes.
NEVER access real secrets or model outputs.
Only admitted on a temporary GitHub-hosted PR runner with permissions:{}.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import vf_office_v2_604_hosted_signer_custody_lab as signer

SHA = re.compile(r"[0-9a-f]{64}\Z")
CID = re.compile(r"[0-9a-f]{64}\Z")
SCHEMA = "velvetos.office-v2.p0-host-docker-daemon-key-custody-negative.v0"


class Refused(Exception):
    pass


def require(value, reason):
    if not value:
        raise Refused(reason)


def daemon_command_args(container_id):
    """Daemon-initiated code running as signer UID, never exporting key bytes."""
    require(type(container_id) is str and CID.fullmatch(container_id),
            "INVALID_OWNED_SYNTHETIC_CONTAINER_ID")
    statement = (
        "import hashlib,hmac,json,os,pathlib;"
        "key=pathlib.Path('/sink/signer-only.key').read_bytes();"
        "assert len(key)==32;"
        "msg=" + repr(signer.MESSAGE.encode("utf-8")) + ";"
        "print(json.dumps({'uid':os.getuid(),'key_length':len(key),"
        "'mac':hmac.new(key,msg,hashlib.sha256).hexdigest()}))"
    )
    return ["docker", "exec", "--user=65534:65534", container_id,
            "python", "-B", "-c", statement]


def selftest():
    require(signer.IMAGE.startswith("python@sha256:") and
            SHA.fullmatch(signer.IMAGE.split("sha256:", 1)[-1]),
            "PINNED_IMAGE_ABSENT")
    require("secrets.token_bytes(32)" in signer.SIGNER and
            "secret_path = key_dir / \"signer-only.key\"" in signer.SIGNER,
            "FRESH_ONLY_SYNTHETIC_KEY_SOURCE_NOT_PRESENT")
    tests = ["pinned_image", "synthetic_only_fresh_key"]
    cid = "a" * 64
    args = daemon_command_args(cid)
    require(args[:6] == ["docker", "exec", "--user=65534:65534",
                          cid, "python", "-B"]
            and args[6] == "-c"
            and "read_bytes()" in args[7]
            and "key_length" in args[7],
            "DAEMON_EXEC_SOURCE_OR_CLI_CHANGED")
    tests.append("exact_daemon_initiated_signer_key_use")
    for bad in ("", "0", "xyz", cid + "a", "c" * 63,
                "a" * 20 + ";/etc/passwd", "sha256:" + "a" * 64):
        try:
            daemon_command_args(bad)
        except Refused:
            tests.append("invalid_cid_denied")
        else:
            raise AssertionError("BAD_CID_ADMITTED")
    key = bytes(range(32))
    message = b"vf-office-p0-604-synthetic-effect-intent-v1\n"
    fake = hmac.new(key, message, hashlib.sha256).hexdigest()
    require(SHA.fullmatch(fake), "SYNTHETIC_HMAC_UNEXPECTED")
    tests.append("synthetic_hmac_only")
    require(len(tests) == 11, "SELFTEST_NUMBER_DRIFT")
    return {"status": "PASS_PURE_DAEMON_NEGATIVE_PREFLIGHT",
            "tests": len(tests), "docker_invocations": 0,
            "private_keys_created": 0, "model_invocations": 0,
            "git_write_authority": False,
            "production_authority": False,
            "host_docker_daemon_key_exposure_measured_live": False}


def run():
    signer.prior.hosted.runner_context_check(os.environ)
    signer.prior.hosted.no_persisted_checkout_auth()
    require(os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
            and os.environ.get("GITHUB_RUN_ID", "").isdigit(),
            "ONLY_EXISTING_PR_HOSTED_RUNNER_ALLOWED")
    signer.docker(["docker", "version", "--format", "{{.Server.Version}}"],
                  timeout=12)
    signer.docker(["docker", "pull", "--quiet", signer.IMAGE], timeout=125)
    image = json.loads(signer.docker([
        "docker", "image", "inspect", signer.IMAGE], timeout=12))[0]
    image_id = image["Id"]
    require(image_id.startswith("sha256:") and SHA.fullmatch(image_id[7:])
            and signer.IMAGE in image["RepoDigests"], "OCI_DIGEST_CHANGED")
    with tempfile.TemporaryDirectory(prefix="vf-604-daemon-public-") as temporary:
        public = Path(temporary)
        public.chmod(0o755)
        (public / "intent.txt").write_text(signer.MESSAGE, encoding="utf-8")
        (public / "signer.py").write_text(signer.SIGNER, encoding="utf-8")
        for f in public.iterdir():
            f.chmod(0o644)
        cid = None
        try:
            args = signer.argv_for(image_id, public, "signer")
            signer.strict_plan(args, image_id, public, "signer")
            cid = signer.docker(args, timeout=16)
            require(CID.fullmatch(cid), "CREATED_CONTAINER_ID_INVALID")
            config = signer.inspect(cid, image_id, public, "signer")
            signer.docker(["docker", "start", cid], timeout=12)
            receipt = signer.ready_log(cid)
            require(receipt["status"] == "READY_SYNTHETIC_SINK_ONLY"
                    and receipt["private_key_not_output"] is True
                    and receipt["uid"] == 65534
                    and SHA.fullmatch(receipt["mac"]), "SIGNER_NOT_READY")
            before = json.loads(signer.docker(["docker", "inspect", cid],
                                              timeout=12))[0]["State"]
            require(before["Running"] is True, "SIGNER_NOT_RUNNING_WHILE_DAEMON_ATTACKS")
            # The first PR-head Docker cp archive probe was refused by Docker.
            # Instead, test the more direct HOST privilege: daemon-initiated
            # process creation INSIDE the owned signer namespace as its UID.
            # The process signs the fixed synthetic challenge without exporting
            # the secret key or TAR bytes. Its printed HMAC is kept in RAM.
            invoked = subprocess.run(daemon_command_args(cid),
                                     stdin=subprocess.DEVNULL,
                                     capture_output=True, text=True, timeout=15)
            require(invoked.returncode == 0,
                    "DAEMON_REFUSED_INITIATED_SIGNER_KEY_USE")
            used = json.loads(invoked.stdout.strip())
            require(used.get("uid") == 65534
                    and used.get("key_length") == 32
                    and type(used.get("mac")) is str
                    and SHA.fullmatch(used["mac"])
                    and hmac.compare_digest(used["mac"], receipt["mac"]),
                    "DAEMON_EXEC_DID_NOT_USE_CURRENT_SYNTHETIC_SIGNER_KEY")
            after = json.loads(signer.docker(["docker", "inspect", cid],
                                             timeout=12))[0]["State"]
            require(after["Running"] is True, "SIGNER_EXITED_DURING_DAEMON_ATTACK")
            return {
                "schema": SCHEMA,
                "status": "PASS_EXPECTED_NEGATIVE_DAEMON_CAN_INVOKE_SYNTHETIC_SIGNER_KEY_USE",
                "github_run_id": os.environ["GITHUB_RUN_ID"],
                "oci_digest": signer.IMAGE,
                "image_id": image_id,
                "signer_uid": config["uid"],
                "signer_mounts": config["mounts"],
                "signer_only_tmpfs": config["sink_only_private_tmpfs"],
                "host_daemon_initiated_live_signer_key_use": True,
                "raw_key_bytes_logged_or_exported": False,
                "docker_cp_archive_test_succeeded": False,
                "private_synthetic_key_generated_inside_guest_only": True,
                "signer_live_before_and_after_daemon_exec": True,
                "same_uid_sibling_guest_cannot_read_key_proven_by_prior_pr": True,
                "production_git_secret_custody_safe": False,
                "host_daemon_trust_required_for_signer": True,
                "kernel_escape_resistance_proven": False,
                "cross_host_epoch_git_fencing_proven": False,
                "model_invocations": 0,
                "git_write_authority": False,
                "production_authority": False,
                "incremental_paid_api_usd": 0,
            }
        finally:
            if cid is not None and CID.fullmatch(cid):
                signer.docker(["docker", "rm", "--force", cid], timeout=14)


def main():
    require(len(sys.argv) == 2 and sys.argv[1] in ("selftest", "run"),
            "INVALID_COMMAND")
    result = selftest() if sys.argv[1] == "selftest" else run()
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refused, signer.Refused, signer.prior.Refused,
            signer.prior.hosted.Refused, OSError, ValueError, KeyError,
            TypeError, subprocess.TimeoutExpired) as err:
        print(json.dumps({"status": "FAIL_CLOSED",
                          "reason": str(err)[:180],
                          "production_authority": False,
                          "git_write_authority": False}, sort_keys=True))
        raise SystemExit(2)
