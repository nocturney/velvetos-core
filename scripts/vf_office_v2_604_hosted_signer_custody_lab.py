#!/usr/bin/env python3
"""#604 hosted synthetic same-UID signer/worker custody separation pilot.

selftest NEVER launches generated code, Docker, Git, or models. Real lab runs
ONLY on fresh no-write-token GitHub-hosted PR Ubuntu runner. Tests two live
same-UID containers with disjoint mount namespaces: signer creates one fake
secret in its OWN tmpfs while worker attempts direct/hardlink/symlink theft.
No real keys, GitHub write credentials, user files or production effects.
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

import vf_office_v2_p0_hosted_container_boundary_lab as prior

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "velvetos.office-v2.p0-hosted-sameuid-synthetic-signer-custody.v0"
IMAGE = prior.EXPECTED_IMAGE_DIGEST
MESSAGE = "vf-office-p0-604-synthetic-effect-intent-v1\n"
CID = re.compile(r"[0-9a-f]{64}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")

# Each is controlled reference code written in this repository; no generated
# model source is in this experiment. Neither file has a Git/client secret.
SIGNER = r'''import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import time

if os.getuid() != 65534 or os.geteuid() != 65534:
    raise SystemExit("SIGNER_NOT_UNPRIVILEGED")
key_dir = Path("/sink")
if not key_dir.is_dir():
    raise SystemExit("PRIVATE_SINK_TMPFS_MISSING")
key = secrets.token_bytes(32)
secret_path = key_dir / "signer-only.key"
fd = os.open(str(secret_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd,"wb") as out:
    out.write(key)
message = Path("/public/intent.txt").read_bytes()
mac = hmac.new(key, message, hashlib.sha256).hexdigest()
print(json.dumps({"status":"READY_SYNTHETIC_SINK_ONLY",
                  "mac":mac, "uid":os.getuid(),
                  "private_key_in_sink_tmpfs":True,
                  "private_key_not_output":True,
                  "production_authority":False},sort_keys=True),flush=True)
time.sleep(28)
'''
WORKER = r'''import errno
import hashlib
import hmac
import json
import os
from pathlib import Path
import socket
import sys

mac = sys.argv[1]
message = Path("/public/intent.txt").read_bytes()
if os.getuid() != 65534 or os.geteuid() != 65534:
    raise RuntimeError("WORKER_NOT_SAME_LOW_UID")
if Path("/sink").exists():
    raise RuntimeError("PRIVATE_SINK_PATH_EXPOSED")
if Path("/var/run/docker.sock").exists():
    raise RuntimeError("DOCKER_SOCKET_EXPOSED")
if any(name in os.environ for name in ("GITHUB_TOKEN","GH_TOKEN","AWS_ACCESS_KEY_ID",
                                     "GOOGLE_APPLICATION_CREDENTIALS")):
    raise RuntimeError("SECRET_ENVIRONMENT_EXPORTED")
try:
    Path("/sink/signer-only.key").read_bytes()
except FileNotFoundError:
    pass
else:
    raise RuntimeError("PRIVATE_KEY_READ_SUCCEEDED")
try:
    os.link("/sink/signer-only.key", "/tmp/key-hardlink")
except FileNotFoundError:
    pass
else:
    raise RuntimeError("PRIVATE_KEY_HARDLINK_ALIAS_SUCCEEDED")
os.symlink("/sink/signer-only.key", "/tmp/key-symlink")
try:
    Path("/tmp/key-symlink").read_bytes()
except FileNotFoundError:
    pass
else:
    raise RuntimeError("PRIVATE_KEY_SYMLINK_ALIAS_SUCCEEDED")
fake_mac = hmac.new(b"not-the-private-key", message, hashlib.sha256).hexdigest()
if hmac.compare_digest(fake_mac,mac):
    raise RuntimeError("PUBLIC_FAKE_KEY_MATCHED_PRIVATE_HMAC")
if set(os.listdir("/sys/class/net")) != {"lo"}:
    raise RuntimeError("WORKER_UNEXPECTED_NETWORK_INTERFACE")
try:
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
        s.settimeout(2)
        s.connect(("1.1.1.1",443))
except OSError as exc:
    if exc.errno not in (errno.ENETUNREACH, errno.EHOSTUNREACH, errno.EPERM, errno.EACCES):
        raise RuntimeError("WORKER_EGRESS_PROBE_OTHER_ERROR")
else:
    raise RuntimeError("WORKER_NETWORK_EGRESS_SUCCEEDED")
print(json.dumps({"status":"PASS_SAME_UID_SYNTHETIC_PRIVATE_KEY_UNAVAILABLE",
                  "uid":os.getuid(), "sink_private_path_denied":True,
                  "hardlink_alias_denied":True,"symlink_alias_denied":True,
                  "fake_hmac_does_not_forge":True,
                  "egress_denied":True,"no_exported_git_write_token":True,
                  "no_docker_socket":True,"production_authority":False},sort_keys=True))
'''


class Refused(Exception):
    pass


def require(value, reason):
    if not value:
        raise Refused(reason)


def digest(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def argv_for(image_id, public_path, role, mac=None):
    require(role in ("signer", "worker"), "UNREGISTERED_SIGNER_OR_WORKER")
    base = [
        "docker", "create", "--network=none", "--read-only",
        "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
        "--user=65534:65534", "--ipc=none", "--pids-limit=32",
        "--memory=256m", "--cpus=1",
        "--tmpfs=/tmp:rw,noexec,nosuid,size=16m,mode=1777",
        "--mount=type=bind,src=" + str(public_path) + ",dst=/public,readonly",
        "--workdir=/public", "--env=PYTHONDONTWRITEBYTECODE=1",
    ]
    if role == "signer":
        base.append("--tmpfs=/sink:rw,noexec,nosuid,size=1m,mode=0700,uid=65534,gid=65534")
    args = [image_id, "python", "-B",
            "/public/signer.py" if role == "signer" else "/public/worker.py"]
    if role == "worker":
        require(type(mac) is str and SHA.fullmatch(mac), "BAD_SYNTHETIC_HMAC")
        args.append(mac)
    return base + args


def strict_plan(arguments, image_id, public_path, role, mac=None):
    require(arguments == argv_for(image_id, public_path, role, mac),
            "UNAPPROVED_DOCKER_ISOLATION_FLAG_OR_EXTRA_MOUNT")
    require(image_id.startswith("sha256:") and SHA.fullmatch(image_id[7:]),
            "NO_PINNED_OCI_IMAGE_ID")
    require(Path(public_path).is_absolute(), "PUBLIC_FIXTURE_PATH_NOT_ABSOLUTE")
    return True


def selftest():
    require(IMAGE.startswith("python@sha256:") and
            SHA.fullmatch(IMAGE.split("sha256:",1)[1]), "APPROVED_OCI_DIGEST_MISSING")
    require("secrets.token_bytes(32)" in SIGNER and
            "time.sleep(28)" in SIGNER and
            "os.link(" in WORKER and "os.symlink(" in WORKER,
            "SYNTHETIC_SINK_KEY_OR_ATTACK_NEGATIVES_MISSING")
    checks = ["immutable_oci_digest", "nonpersistent_private_key",
              "direct_and_alias_attack_source"]
    root = Path(tempfile.gettempdir()).resolve()/"vf-604-public-fixture-no-file-created"
    imageid = "sha256:"+"a"*64
    mac = "b"*64
    for role in ("signer","worker"):
        args = argv_for(imageid, root, role, mac if role=="worker" else None)
        strict_plan(args, imageid, root, role, mac if role=="worker" else None)
        checks.append("exact_"+role+"_config")
        tamper = [
            ("--network=none", "--network=host"),
            ("--read-only","--privileged"),
            ("--cap-drop=ALL","--cap-add=SYS_ADMIN"),
            ("--security-opt=no-new-privileges:true",
             "--security-opt=seccomp=unconfined"),
            ("--user=65534:65534","--user=0:0"),
            ("--ipc=none","--ipc=host"),
            ("--pids-limit=32","--pids-limit=1024"),
        ]
        for old,new in tamper:
            bad=copy.deepcopy(args)
            bad[bad.index(old)]=new
            try: strict_plan(bad,imageid,root,role,mac if role=="worker" else None)
            except Refused: checks.append("unsafe_"+role+"_flag_denied")
            else: raise Refused("UNSAFE_CONFIG_FALSE_ADMITTED")
    require(len(checks)==19, "SAMEUID_SIGNER_NEGATIVE_COUNT_DRIFT")
    return {"status":"PASS_STATIC_SIGNER_CUSTODY_DENIAL",
            "tests":len(checks),"docker_calls":0,"actual_key_created":False,
            "model_calls":0,"production_authority":False,
            "git_write_authority":False,"OS_SECRET_CUSTODY_PROVEN":False}


def docker(args, timeout=30):
    return prior.docker_command(args,timeout=timeout)


def inspect(cid, image_id, public_path, role):
    objs=json.loads(docker(["docker","inspect",cid],timeout=12))
    require(len(objs)==1,"INSPECT_CID_MISSING")
    data=objs[0]
    host=data["HostConfig"]
    mounts=data["Mounts"]
    require(data["Image"]==image_id and data["Config"]["User"]=="65534:65534",
            "SAME_LOW_UID_NOT_ATTESTED")
    require(host["NetworkMode"]=="none" and host["ReadonlyRootfs"] is True
            and host["Privileged"] is False and host["CapDrop"]==["ALL"]
            and any(str(x).startswith("no-new-privileges") for x in host["SecurityOpt"])
            and host["PidsLimit"]==32 and host["Memory"]==268435456
            and host["NanoCpus"]==1000000000 and host["IpcMode"]=="none"
            and host["PidMode"] in ("","private"),
            "CONTAINER_HOSTCONFIG_DENIAL")
    require(len(mounts)==1 and mounts[0]["Type"]=="bind"
            and mounts[0]["Source"]==str(public_path)
            and mounts[0]["Destination"]=="/public"
            and mounts[0]["RW"] is False,"HOST_PATH_OR_TOKEN_MOUNT_EXPOSED")
    tempfs=host["Tmpfs"] or {}
    require("/tmp" in tempfs and (("/sink" in tempfs)==(role=="signer")),
            "SIGNER_PRIVATE_TMPFS_NOT_EXCLUSIVE")
    require(not any(v.startswith("GITHUB_TOKEN=") or v.startswith("GH_TOKEN=")
                    for v in data["Config"].get("Env",[])),
            "GIT_WRITE_CREDENTIAL_EXPORTED")
    return {"mounts":len(mounts),"role":role,"uid":data["Config"]["User"],
            "network":"none","sink_only_private_tmpfs":role=="signer",
            "capabilities":"ALL_DROPPED"}


def ready_log(cid):
    for _ in range(60):
        lines=docker(["docker","logs",cid],timeout=8).splitlines()
        for line in lines:
            if line.startswith("{") and line.endswith("}"):
                data=json.loads(line)
                if data.get("status")=="READY_SYNTHETIC_SINK_ONLY":
                    return data
                raise Refused("SIGNER_DID_NOT_REPORT_EXPECTED_RESULT")
        state=json.loads(docker(["docker","inspect",cid],timeout=8))[0]["State"]
        require(state["Running"] is True, "SIGNER_EXITED_BEFORE_WORKER_TEST")
        time.sleep(.15)
    raise Refused("SIGNER_NOT_READY_WITHIN_BUDGET")


def execute():
    prior.hosted.runner_context_check(os.environ)
    prior.hosted.no_persisted_checkout_auth()
    require(os.environ.get("GITHUB_EVENT_NAME")=="pull_request"
            and os.environ.get("GITHUB_RUN_ID","").isdigit(),
            "SYNTHETIC_SIGNER_RUN_MUST_BE_GITHUB_PR_ONLY")
    docker(["docker","version","--format","{{.Server.Version}}"],timeout=12)
    docker(["docker","pull","--quiet",IMAGE],timeout=125)
    image=json.loads(docker(["docker","image","inspect",IMAGE],timeout=12))[0]
    image_id=image["Id"]
    require(image_id.startswith("sha256:") and
            SHA.fullmatch(image_id[7:]) and IMAGE in image["RepoDigests"],
            "OCI_SIGNER_IMAGE_PIN_NOT_MATCHING")
    with tempfile.TemporaryDirectory(prefix="vf-604-public-intent-") as scratch:
        public=Path(scratch)
        public.chmod(0o755)
        (public/"intent.txt").write_text(MESSAGE,encoding="utf-8")
        (public/"signer.py").write_text(SIGNER,encoding="utf-8")
        (public/"worker.py").write_text(WORKER,encoding="utf-8")
        for f in public.iterdir(): f.chmod(0o644)
        signer=worker=None
        try:
            args=argv_for(image_id,public,"signer")
            strict_plan(args,image_id,public,"signer")
            signer=docker(args,timeout=18)
            require(CID.fullmatch(signer),"SIGNER_CONTAINER_ID_MISSING")
            signer_config=inspect(signer,image_id,public,"signer")
            docker(["docker","start",signer],timeout=10)
            receipt=ready_log(signer)
            require(receipt["uid"]==65534
                    and receipt["private_key_in_sink_tmpfs"] is True
                    and receipt["private_key_not_output"] is True
                    and SHA.fullmatch(receipt["mac"]),
                    "SIGNER_FAKE_SECRET_INVALID")
            signer_state=json.loads(docker(["docker","inspect",signer],timeout=8))[0]["State"]
            require(signer_state["Running"] is True,"SIGNER_NOT_LIVE_AT_WORKER_START")
            args=argv_for(image_id,public,"worker",receipt["mac"])
            strict_plan(args,image_id,public,"worker",receipt["mac"])
            worker=docker(args,timeout=18)
            require(CID.fullmatch(worker),"WORKER_CONTAINER_ID_MISSING")
            worker_config=inspect(worker,image_id,public,"worker")
            log=docker(["docker","start","--attach",worker],timeout=26)
            result=json.loads(log.strip())
            worker_status=json.loads(docker(["docker","inspect",worker],timeout=8))[0]["State"]
            signer_after=json.loads(docker(["docker","inspect",signer],timeout=8))[0]["State"]
            require(worker_status["ExitCode"]==0
                    and result.get("status")=="PASS_SAME_UID_SYNTHETIC_PRIVATE_KEY_UNAVAILABLE"
                    and result.get("uid")==receipt["uid"]==65534
                    and signer_after["Running"] is True
                    and all(result.get(k) is True for k in
                            ("sink_private_path_denied","hardlink_alias_denied",
                             "symlink_alias_denied","fake_hmac_does_not_forge",
                             "egress_denied","no_exported_git_write_token",
                             "no_docker_socket")),
                    "SAMEUID_KEY_DENIAL_OR_CONCURRENT_SIGNER_FAILED")
            return {"schema":SCHEMA,
                    "status":"PASS_HOSTED_SAMEUID_SYNTHETIC_SIGNER_CUSTODY_NEGATIVE",
                    "github_run_id":os.environ["GITHUB_RUN_ID"],
                    "oci_digest":IMAGE,"image_id":image_id,
                    "signer_config":signer_config,"worker_config":worker_config,
                    "same_uid_concurrent_separate_mounts":True,
                    "signer_tmpfs_secret_generated_inside_guest":True,
                    "private_key_never_exported":True,
                    "worker_direct_hardlink_symlink_denied":True,
                    "worker_fake_hmac_rejected":True,
                    "worker_egress_denied":True,
                    "github_git_writer_credential_present":False,
                    "exclusive_native_git_sink_authority_proven":False,
                    "host_daemon_cannot_read_key_proven":False,
                    "kernel_escape_resistance_proven":False,
                    "provider_epoch_and_github_commit_fenced":False,
                    "production_authority":False,
                    "model_invocations":0,"paid_api_spend_usd":0}
        finally:
            for cid in (worker,signer):
                if cid is not None and CID.fullmatch(cid):
                    docker(["docker","rm","--force",cid],timeout=14)


def main():
    require(len(sys.argv)==2 and sys.argv[1] in ("selftest","run"),
            "EXPECTED_SELFTEST_OR_RUN")
    outcome=selftest() if sys.argv[1]=="selftest" else execute()
    print(json.dumps(outcome,sort_keys=True))


if __name__=="__main__":
    try: main()
    except (Refused,prior.Refused,prior.hosted.Refused,
            subprocess.TimeoutExpired,OSError,ValueError,KeyError,TypeError) as ex:
        print(json.dumps({"status":"FAIL_CLOSED",
                          "reason":str(ex)[:185],
                          "production_authority":False,
                          "git_write_authority":False},sort_keys=True))
        raise SystemExit(2)
