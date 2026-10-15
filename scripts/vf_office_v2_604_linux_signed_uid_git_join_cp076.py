#!/usr/bin/env python3
"""CP076: separate OS signer, peercred worker and local Git sink (LAB only).

Run ONLY in an existing disposable Linux aarch64 guest with explicit opt-in,
as guest root (for ephemeral numeric UID drop). Fixed synthetic signed source,
OpenSSL Ed25519 detached signatures, SO_PEERCRED, real native local bare Git
CAS and crash/UNKNOWN. No Core-issued lease, GitHub credential/remote,
generated model code, global account, scheduler or production effect.
"""
from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import pwd
import select
import socket
import sqlite3
import stat
import struct
import subprocess
import sys
import tempfile
import time

SCHEMA = "velvetos.office-v2.604.cp076-separate-uid-signer-localgit.v1"
CLAIM_SCHEMA = "velvetos.office-v2.604.cp076-synthetic-signed-scope.v1"
REF = "refs/heads/vf604-cp076-local-only"
TASK = "cp076-one-fixed-logical-source-intent"
HOST = "MacMiniOffice2.local/colima-velvet-qa"
SIGNER_UID, SINK_UID, WORKER_UID, ATTACKER_UID = 62005, 62001, 62002, 62003
NAMESPACE = "vf604-cp076-synthetic-scope"
SIGNER_NAME = "vf604-cp076-ephemeral-signer"
SOURCE_SHA = hashlib.sha256(b"CP076 FIXED PUBLIC NOT MODEL GENERATED").hexdigest()
MAX_REQUEST = 16384
ENV = {
    "PATH": "/usr/bin:/bin",
    "HOME": "/tmp",
    "LANG": "C",
    "PYTHONDONTWRITEBYTECODE": "1",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_ALLOW_PROTOCOL": "file",
    "GIT_AUTHOR_NAME": "VF604 synthetic sink",
    "GIT_AUTHOR_EMAIL": "no-user@invalid.example",
    "GIT_COMMITTER_NAME": "VF604 synthetic sink",
    "GIT_COMMITTER_EMAIL": "no-user@invalid.example",
    "GIT_AUTHOR_DATE": "2001-01-01T00:00:00 +0000",
    "GIT_COMMITTER_DATE": "2001-01-01T00:00:00 +0000",
}
ALLOWED_ROOT_PREFIX = "vf604-cp076-signed-uid-"
NEGATIVE_FIELDS = ("schema", "issuer", "task_id", "host", "worker_uid",
                   "ref", "effect", "source_sha256", "expected_sha",
                   "epoch", "nonce", "expires_utc_ms")
EXPECTED_REASON = {
    "signed_wrong_host": "WRONG_TASK_OR_EFFECT_SCOPE",
    "signed_wrong_worker": "WRONG_OS_WORKER_SCOPE",
    "signed_wrong_ref": "WRONG_TASK_OR_EFFECT_SCOPE",
    "signed_escalated_effect": "WRONG_TASK_OR_EFFECT_SCOPE",
    "signed_expired": "SYNTHETIC_DEADLINE_NOT_CURRENT",
    "tampered_after_signing": "CRYPTO_SIGNATURE_REJECTED",
}


class Refuse(Exception):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise Refuse(msg)


def data_bytes(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode("ascii")


def is_sha(value: object) -> bool:
    return (type(value) is str and len(value) == 40
            and all(c in "0123456789abcdef" for c in value))


def claim(original: str, *, expires_utc_ms: int) -> dict:
    return {
        "schema": CLAIM_SCHEMA,
        "issuer": "vf604-cp076-synthetic-not-core",
        "task_id": TASK,
        "host": HOST,
        "worker_uid": WORKER_UID,
        "ref": REF,
        "effect": "LOCAL_BARE_GIT_CAS_ONLY",
        "source_sha256": SOURCE_SHA,
        "expected_sha": original,
        "epoch": 7,
        "nonce": "cp076-fixed-attempt-1",
        "expires_utc_ms": expires_utc_ms,
    }


def strict_claim(obj: object, initial: str, uid: int, at_ms: int) -> None:
    need(type(obj) is dict and set(obj) == set(NEGATIVE_FIELDS),
         "CLAIM_SCHEMA_OR_EXTRA_KEYS_DENIED")
    need(type(uid) is int and uid == WORKER_UID
         and type(obj["worker_uid"]) is int
         and obj["worker_uid"] == uid, "WRONG_OS_WORKER_SCOPE")
    need(all(type(obj[k]) is str for k in (
         "schema", "issuer", "task_id", "host", "ref", "effect",
         "source_sha256", "expected_sha", "nonce")),
         "NON_STRING_TASK_SCOPE")
    need(obj["schema"] == CLAIM_SCHEMA
         and obj["issuer"] == "vf604-cp076-synthetic-not-core"
         and obj["task_id"] == TASK
         and obj["host"] == HOST
         and obj["ref"] == REF
         and obj["effect"] == "LOCAL_BARE_GIT_CAS_ONLY"
         and obj["source_sha256"] == SOURCE_SHA
         and obj["expected_sha"] == initial
         and obj["nonce"] == "cp076-fixed-attempt-1",
         "WRONG_TASK_OR_EFFECT_SCOPE")
    need(type(obj["epoch"]) is int and obj["epoch"] == 7,
         "STALE_OR_FORGED_EPOCH")
    need(type(obj["expires_utc_ms"]) is int
         and at_ms < obj["expires_utc_ms"] <= at_ms + 90000,
         "SYNTHETIC_DEADLINE_NOT_CURRENT")


def selftest() -> dict:
    expected = claim("a" * 40, expires_utc_ms=30000)
    strict_claim(expected, "a" * 40, WORKER_UID, 20000)
    mutants = []
    for key, value in expected.items():
        change = dict(expected)
        change[key] = (not value if type(value) is bool
                       else 0 if key == "expires_utc_ms"
                       else value + 1 if type(value) is int
                       else value + "_forged")
        mutants.append((key, change))
    mutants.extend([
        ("extra_keys", dict(expected, git_token="forged")),
        ("missing_ref", {k:v for k,v in expected.items() if k != "ref"}),
        ("wrong_credential_actor", dict(expected, worker_uid=SIGNER_UID)),
        ("numeric_string_epoch", dict(expected, epoch="7")),
        ("bool_epoch", dict(expected, epoch=True)),
        ("zero_deadline", dict(expected, expires_utc_ms=0)),
        ("far_future_deadline", dict(expected, expires_utc_ms=99999999999)),
    ])
    need(len(mutants) == 19, "CP076_NEGATIVE_MUTANT_COUNT_DRIFT")
    for name, change in mutants:
        try: strict_claim(change, "a" * 40, WORKER_UID, 20000)
        except Refuse: pass
        else: raise Refuse("FALSE_SYNTHETIC_SIGNED_CLAIM_ADMITTED_"+name)
    for uid in (0, SIGNER_UID, SINK_UID, ATTACKER_UID):
        try: strict_claim(expected, "a" * 40, uid, 20000)
        except Refuse: pass
        else: raise Refuse("WRONG_KERNEL_PEER_UID_ADMITTED")
    need(len(NEGATIVE_FIELDS)==12 and len(set(NEGATIVE_FIELDS))==12,
         "CLAIM_FIELDS_DRIFT")
    return {
        "schema": SCHEMA,
        "status": "PASS_CP076_STATIC_23_NEGATIVES",
        "claim_mutation_denials": len(mutants),
        "peer_uid_denials": 4,
        "real_signer_created": False, "real_sink_launched": False,
        "model_source_executed": False, "remote_git_writes": 0,
        "provider_lease": False, "production_authority": False,
    }


def roots(value: str) -> Path:
    raw = Path(value)
    need(raw.is_absolute() and str(raw).startswith("/tmp/" + ALLOWED_ROOT_PREFIX)
         and not raw.is_symlink(), "UNOWNED_OR_SYMLINK_ROOT")
    root = raw.resolve(strict=True)
    need(root == raw and root.is_dir()
         and (root / ".vf604-cp076-disposable").is_file(),
         "NOT_EXACT_DISPOSABLE_ROOT")
    return root


def run_cmd(args: list[str], *, uid: int | None = None,
            input_bytes: bytes | None = None, timeout: int = 10,
            check: bool = True) -> subprocess.CompletedProcess:
    def drop() -> None:
        if uid is not None:
            os.setgroups([])
            os.setgid(uid)
            os.setuid(uid)
    p = subprocess.run(args, input=input_bytes, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=timeout, env=ENV,
                       preexec_fn=drop if uid is not None else None)
    if check and p.returncode != 0:
        detail=p.stderr.decode("utf-8","replace")[:145].replace("\\n"," ").replace("\n"," ")
        raise Refuse("FIXED_CHILD_COMMAND_FAILED_" +
                     Path(args[0]).name + "_" + str(p.returncode) + "_" + detail)
    return p


def git(root: Path, *args: str, input_bytes: bytes | None = None,
        allow_failure: bool = False) -> str | None:
    cmd = ["/usr/bin/git", "--git-dir", str(root / "sink" / "local.git"), *args]
    p = run_cmd(cmd, input_bytes=input_bytes, check=not allow_failure)
    return p.stdout.decode().strip() if p.returncode == 0 else None


def message_for_signature(payload: dict) -> bytes:
    return (b"VELVETOS-CP076-DETACHED-SCOPE-V1\0"
            + NAMESPACE.encode("ascii") + b"\0" + data_bytes(payload))


def signed_message(root: Path, payload: dict) -> str:
    key = root / "signer" / "ephemeral_ed25519"
    # Ed25519 pkeyutl is one-shot and needs a seekable -in file, not stdin.
    # The signer UID can read only this scratch message in its private dir.
    with tempfile.NamedTemporaryFile(prefix="vf604-sign-data-",
         dir=str(root/"signer"),delete=False) as f:
        f.write(message_for_signature(payload))
        os.fchown(f.fileno(),SIGNER_UID,SIGNER_UID)
        temporary=f.name
    try:
        p=run_cmd(["/usr/bin/openssl","pkeyutl","-sign","-rawin",
                   "-inkey",str(key),"-in",temporary],
                  uid=SIGNER_UID,timeout=8)
        need(len(p.stdout)==64, "INVALID_ED25519_SIGNATURE_LENGTH")
        return base64.b64encode(p.stdout).decode("ascii")
    finally:
        os.unlink(temporary)


def verify_signature(root: Path, payload: object, signature: object) -> bool:
    if type(payload) is not dict or type(signature) is not str:
        return False
    try:
        raw=base64.b64decode(signature,validate=True)
    except (ValueError,base64.binascii.Error):
        return False
    if len(raw)!=64:
        return False
    # Called ONLY in the dedicated sink UID private dir.
    with tempfile.NamedTemporaryFile(prefix="vf604-sig-", suffix=".bin",
        dir=str(root/"sink"),delete=False) as f:
        f.write(raw)
        path=f.name
    with tempfile.NamedTemporaryFile(prefix="vf604-verify-",
        dir=str(root/"sink"),delete=False) as f:
        f.write(message_for_signature(payload))
        message=f.name
    try:
        result=run_cmd([
            "/usr/bin/openssl","pkeyutl","-verify","-rawin",
            "-pubin","-inkey",str(root/"public"/"signer_ed25519.pub.pem"),
            "-sigfile",path,"-in",message
        ],check=False,timeout=8)
        return result.returncode==0
    finally:
        os.unlink(path)
        os.unlink(message)


def peeruid(c: socket.socket) -> int:
    _, uid, _ = struct.unpack("3i", c.getsockopt(
        socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    return uid


def db(root: Path) -> sqlite3.Connection:
    c = sqlite3.connect(str(root / "sink" / "state.sqlite3"),
                        isolation_level=None, timeout=10)
    c.execute("PRAGMA synchronous=FULL")
    c.execute("PRAGMA busy_timeout=10000")
    return c


def git_commit(root: Path, text: bytes, parent: str | None = None) -> str:
    blob = git(root, "hash-object", "-w", "--stdin", input_bytes=text)
    need(is_sha(blob), "LOCAL_BLOB_CREATION_FAILED")
    tree = git(root, "mktree", input_bytes=(
        "100644 blob "+blob+"\tproof.txt\n").encode("ascii"))
    need(is_sha(tree), "LOCAL_TREE_CREATION_FAILED")
    command = ["commit-tree", tree]
    if parent is not None:
        command += ["-p", parent]
    ident = git(root, *command, input_bytes=b"vf604 fixed signed lab\n")
    need(is_sha(ident), "LOCAL_COMMIT_CREATION_FAILED")
    return ident


def prepare_sink(root: Path) -> str:
    repo = root / "sink" / "local.git"
    if not repo.exists():
        run_cmd(["/usr/bin/git", "init", "--quiet", "--bare", str(repo)])
        repo.chmod(0o700)
        secret = root / "sink" / "FAKE_CREDENTIAL_NOT_REAL"
        secret.write_text("VF604 CP076 PUBLIC CANARY NOT A CREDENTIAL\n")
        secret.chmod(0o600)
        original = git_commit(root, b"CP076_INITIAL_PUBLIC_TEST\n")
        git(root, "update-ref", REF, original)
        with db(root) as c:
            c.execute("CREATE TABLE s (id INTEGER PRIMARY KEY CHECK(id=1), phase TEXT,"
                      "epoch INTEGER,initial TEXT,expected TEXT,candidate TEXT,"
                      "effects INTEGER)")
            c.execute("INSERT INTO s VALUES(1,'ACTIVE',7,?,NULL,NULL,0)",
                      (original,))
    with db(root) as c:
        c.execute("BEGIN IMMEDIATE")
        phase=c.execute("SELECT phase FROM s WHERE id=1").fetchone()[0]
        if phase=="EFFECT_IN_FLIGHT":
            c.execute("UPDATE s SET phase='FROZEN_UNKNOWN' WHERE id=1")
        c.execute("COMMIT")
    out = git(root, "rev-parse", REF)
    need(is_sha(out), "LOCAL_REF_MISSING")
    return out


def snapshot(root: Path) -> dict:
    with db(root) as c:
        row = c.execute("SELECT phase,epoch,initial,expected,candidate,effects "
                        "FROM s WHERE id=1").fetchone()
    need(row is not None, "SINK_RECORD_MISSING")
    return dict(zip(("phase","epoch","initial","expected","candidate","effects"),
                    row))


def serve(value: str) -> None:
    root=roots(value)
    need(os.geteuid()==SINK_UID, "SINK_NOT_DEDICATED_OS_PRINCIPAL")
    start=prepare_sink(root)
    server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    endpoint=root/"endpoint"/"sink.sock"
    if endpoint.exists():endpoint.unlink()
    server.bind(str(endpoint))
    os.chmod(endpoint,0o666)
    server.listen(16)
    server.settimeout(0.4)
    print("READY "+start,flush=True)
    shutdown=False
    try:
        while not shutdown:
            try: connection,_=server.accept()
            except socket.timeout:continue
            with connection:
                try:
                    uid=peeruid(connection)
                    chunk=bytearray()
                    while b"\n" not in chunk and len(chunk)<=MAX_REQUEST:
                        buf=connection.recv(512)
                        if not buf:break
                        chunk.extend(buf)
                    need(b"\n" in chunk and len(chunk)<=MAX_REQUEST,
                         "UNBOUNDED_REQUEST")
                    req=json.loads(chunk.split(b"\n",1)[0])
                    need(type(req) is dict,"NON_OBJECT_REQUEST")
                    action=req.get("action")
                    result={"status":"DENIED","reason":"FORBIDDEN_ACTION"}
                    if uid==0 and action in ("snapshot","shutdown","reconcile"):
                        if action=="snapshot":
                            result={"status":"ROOT_CONTROL","reason":"SNAPSHOT",
                                    "state":snapshot(root),"head":git(root,"rev-parse",REF)}
                        elif action=="shutdown":
                            result={"status":"ROOT_CONTROL","reason":"SHUTDOWN"}
                            shutdown=True
                        else:
                            s=snapshot(root)
                            head=git(root,"rev-parse",REF)
                            if (s["phase"]=="FROZEN_UNKNOWN"
                                and head==s["candidate"] and is_sha(head)):
                                with db(root) as c:
                                    c.execute("BEGIN IMMEDIATE")
                                    c.execute("UPDATE s SET phase='COMMITTED_VERIFIED',"
                                              "effects=effects+1 WHERE id=1 "
                                              "AND phase='FROZEN_UNKNOWN'")
                                    c.execute("COMMIT")
                                result={"status":"ROOT_CONTROL",
                                        "reason":"MANUAL_READBACK_CONFIRMED"}
                            else:
                                result={"status":"DENIED",
                                        "reason":"NOT_EXACT_UNKNOWN_CANDIDATE"}
                    elif action=="effect":
                        body=req.get("claim")
                        signature=req.get("signature")
                        # Verify crypto BEFORE trusting signer-supplied metadata.
                        need(verify_signature(root,body,signature),
                             "CRYPTO_SIGNATURE_REJECTED")
                        s=snapshot(root)
                        strict_claim(body,s["initial"],uid,int(time.time()*1000))
                        need(s["phase"]=="ACTIVE","FROZEN_OR_ALREADY_COMMITTED")
                        need(s["epoch"]==body["epoch"],"STALE_SYNTHETIC_EPOCH")
                        before=git(root,"rev-parse",REF)
                        need(before==body["expected_sha"],
                             "CURRENT_GIT_REF_CHANGED")
                        candidate=git_commit(root,b"CP076_FIXED_ONLY_SIGNED_CAS\n",
                                             before)
                        with db(root) as c:
                            c.execute("BEGIN IMMEDIATE")
                            c.execute("UPDATE s SET phase='EFFECT_IN_FLIGHT',"
                                      "expected=?,candidate=? WHERE id=1 "
                                      "AND phase='ACTIVE'",
                                      (before,candidate))
                            need(c.total_changes>0,"DURABLE_INTENT_NOT_WRITTEN")
                            c.execute("COMMIT")
                        need(git(root,"rev-parse",REF)==before,
                             "LAST_MINUTE_LOCAL_REF_CHANGED")
                        git(root,"update-ref",REF,candidate,before)
                        if root.name == "after":
                            os._exit(72)  # NO ACK after real ref effect.
                        need(git(root,"rev-parse",REF)==candidate,
                             "NATIVE_REF_READBACK_NOT_MATCHED")
                        with db(root) as c:
                            c.execute("BEGIN IMMEDIATE")
                            c.execute("UPDATE s SET phase='COMMITTED_VERIFIED',"
                                      "effects=effects+1 WHERE id=1 "
                                      "AND phase='EFFECT_IN_FLIGHT'")
                            c.execute("COMMIT")
                        result={"status":"ONE_LOCAL_REF_EFFECT_VERIFIED",
                                "reason":"VALID_CRYPTO_AND_OS_UID",
                                "head":candidate}
                    connection.sendall(data_bytes(result))
                except (Refuse,OSError,ValueError,KeyError,TypeError) as e:
                    try:connection.sendall(data_bytes({
                        "status":"DENIED","reason":str(e)[:115]}))
                    except OSError:pass
    finally:
        server.close()
        if endpoint.exists():endpoint.unlink()


def request(root: Path, msg: dict) -> dict:
    sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        sock.connect(str(root/"endpoint"/"sink.sock"))
        sock.sendall(data_bytes(msg))
        data=bytearray()
        while b"\n" not in data and len(data)<MAX_REQUEST:
            x=sock.recv(512)
            if not x:break
            data.extend(x)
        if not data:return {"status":"NO_ACK_UNKNOWN","reason":"SINK_DIED"}
        return json.loads(data.split(b"\n",1)[0])
    except (BrokenPipeError,ConnectionResetError,ConnectionRefusedError,
            FileNotFoundError):
        return {"status":"NO_ACK_UNKNOWN","reason":"NO_ACK"}
    finally:sock.close()


def start_sink(root: Path) -> tuple[subprocess.Popen,str]:
    script=os.path.realpath(__file__)
    def drop() -> None:
        os.setgroups([])
        os.setgid(SINK_UID)
        os.setuid(SINK_UID)
    child=subprocess.Popen([
        "/usr/bin/python3","-B",script,"_serve",str(root)],
        env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,preexec_fn=drop)
    ready,_,_=select.select([child.stdout],[],[],9)
    if not ready:
        child.terminate()
        child.wait(timeout=5)
        raise Refuse("SINK_FAILED_TO_START")
    output=child.stdout.readline().strip()
    if not output.startswith("READY ") or not is_sha(output[6:]):
        err=child.stderr.read()[-300:]
        raise Refuse("SINK_NOT_READY_"+output[:160]+"_"+err)
    return child, output[6:]


def close_sink(root: Path, proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        try:
            request(root,{"action":"shutdown"})
            proc.wait(timeout=5)
        except (OSError,subprocess.TimeoutExpired):
            proc.terminate()
            proc.wait(timeout=4)


def os_request(root: Path, uid: int, body: dict) -> dict:
    def drop() -> None:
        os.setgroups([])
        os.setgid(uid)
        os.setuid(uid)
    command=["/usr/bin/python3","-B",os.path.realpath(__file__),
             "_request",str(root)]
    p=subprocess.run(command,env=ENV,preexec_fn=drop,
                     input=data_bytes(body),capture_output=True,timeout=9)
    need(p.returncode==0 and bool(p.stdout.strip()),
         "UNTRUSTED_WORKER_CLIENT_FAILED")
    return json.loads(p.stdout)


def probe_dac(root: Path, uid: int) -> dict:
    def drop() -> None:
        os.setgroups([])
        os.setgid(uid)
        os.setuid(uid)
    p=subprocess.run(
        ["/usr/bin/python3","-B",os.path.realpath(__file__),
         "_probe",str(root)], env=ENV,preexec_fn=drop,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=7)
    need(p.returncode==0, "PROBE_CLIENT_FAILED")
    return json.loads(p.stdout)


def create_roles(root: Path) -> None:
    root.chmod(0o755)
    (root/".vf604-cp076-disposable").write_text("FIXED_NO_REMOTE\n")
    (root/"signer").mkdir(mode=0o700)
    os.chown(root/"signer",SIGNER_UID,SIGNER_UID)
    (root/"public").mkdir(mode=0o755)
    (root/"public").chmod(0o755)
    (root/"endpoint").mkdir(mode=0o755)
    (root/"endpoint").chmod(0o755)
    os.chown(root/"endpoint",SINK_UID,SINK_UID)
    (root/"sink").mkdir(mode=0o700)
    os.chown(root/"sink",SINK_UID,SINK_UID)
    # OpenSSL Ed25519 works with ephemeral numeric UIDs without OS accounts;
    # ssh-keygen refuses getpwuid() for an unregistered numeric principal.
    key=root/"signer"/"ephemeral_ed25519"
    pub=root/"signer"/"ephemeral_ed25519.pub.pem"
    run_cmd(["/usr/bin/openssl","genpkey","-algorithm","ED25519",
             "-out",str(key)],uid=SIGNER_UID)
    run_cmd(["/usr/bin/openssl","pkey","-in",str(key),
             "-pubout","-out",str(pub)],uid=SIGNER_UID)
    st=key.stat()
    need(st.st_uid==SIGNER_UID and stat.S_IMODE(st.st_mode)==0o600,
         "SIGNER_KEY_CUSTODY_NOT_UID_SEPARATED")
    pubkey=pub.read_text()
    need(pubkey.startswith("-----BEGIN PUBLIC KEY-----\n")
         and pubkey.rstrip().endswith("-----END PUBLIC KEY-----")
         and len(pubkey)<240, "NOT_EXPECTED_EPHEMERAL_ED25519_PUBLIC_KEY")
    target=root/"public"/"signer_ed25519.pub.pem"
    target.write_text(pubkey)
    target.chmod(0o644)


def run_native() -> dict:
    need(sys.platform=="linux" and platform.machine()=="aarch64"
         and os.geteuid()==0
         and os.environ.get("VF604_CP076_DISPOSABLE_GUEST_ONLY")
             =="VF604_CP076_EXPLICIT_FIXED_OS_TEST",
         "REFUSE_OUTSIDE_DISPOSABLE_LINUX_ARM64_GUEST")
    need(os.path.exists("/run/containerd/containerd.sock"),
         "EXPECTED_EXISTING_COLIMA_GUEST_NOT_EVIDENCED")
    for uid in (SIGNER_UID,SINK_UID,WORKER_UID,ATTACKER_UID):
        try:pwd.getpwuid(uid)
        except KeyError:pass
        else:raise Refuse("NUMERIC_LAB_UID_IS_ALREADY_AN_ACCOUNT")
    need(not any(os.environ.get(k) for k in
                 ("GITHUB_TOKEN","GH_TOKEN","SSH_AUTH_SOCK","GIT_ASKPASS")),
         "REFUSE_REAL_CREDENTIALS_IN_LAB_CONTEXT")
    cases={}
    def ck(name: str, status: bool) -> None:
        cases[name]=(status is True)
        need(cases[name], "REAL_OS_SIGNED_GIT_DENIAL_FAILED_"+name)
        print("CP076_NATIVE_"+name,flush=True)
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix=ALLOWED_ROOT_PREFIX,dir="/tmp") as work:
        root=Path(work)
        root.chmod(0o755)  # root-owned, workers may traverse but never write.
        # Scenario-specific dirs root-owned and nonwritable by other UIDs.
        for scenario in ("normal","after"):
            p=root/scenario
            p.mkdir(mode=0o755)
            create_roles(p)
        normal=root/"normal"
        priv=(normal/"signer"/"ephemeral_ed25519")
        fake=(normal/"sink"/"FAKE_CREDENTIAL_NOT_REAL")
        st=priv.stat()
        ck("01_ed25519_key_owned_only_by_signer_uid",
           st.st_uid==SIGNER_UID and stat.S_IMODE(st.st_mode)==0o600)
        ck("02_sink_and_worker_distinct_kernel_numeric_uids",
           len({SIGNER_UID,SINK_UID,WORKER_UID,ATTACKER_UID})==4)
        p,initial=start_sink(normal)
        try:
            sink=probe_dac(normal,SINK_UID)
            worker=probe_dac(normal,WORKER_UID)
            signer=probe_dac(normal,SIGNER_UID)
            ck("03_sink_cannot_read_signer_private_key",
               sink["signer_private_key_denied"])
            ck("04_worker_cannot_read_signer_private_key",
               worker["signer_private_key_denied"])
            ck("05_worker_cannot_read_sink_only_fake_credential",
               worker["fake_sink_token_denied"])
            ck("06_worker_cannot_read_or_write_bare_git",
               worker["sink_git_head_denied"] and
               worker["direct_git_write_denied"])
            ck("07_signer_cannot_read_bare_git",
               signer["sink_git_head_denied"])
            now=int(time.time()*1000)
            original=claim(initial,expires_utc_ms=now+60000)
            good={"action":"effect","claim":original,
                  "signature":signed_message(normal,original)}
            # All wrong scopes carry a VALID detached signature; the sink
            # must reject them on authoritative OS ID/task/effect/deadline.
            cases_wrong={
                "signed_wrong_host":dict(original,host="Wrong-Host"),
                "signed_wrong_worker":dict(original,worker_uid=ATTACKER_UID),
                "signed_wrong_ref":dict(original,ref="refs/heads/main"),
                "signed_escalated_effect":dict(original,effect="GITHUB_PUSH"),
                "signed_expired":dict(original,expires_utc_ms=now-1000),
            }
            for name,payload in cases_wrong.items():
                req={"action":"effect","claim":payload,
                     "signature":signed_message(normal,payload)}
                out=os_request(normal,WORKER_UID,req)
                ck("08_"+name,out["status"]=="DENIED"
                   and out["reason"]==EXPECTED_REASON[name])
            tampered=dict(original,source_sha256="0"*64)
            attack={"action":"effect","claim":tampered,
                    "signature":good["signature"]}
            no=os_request(normal,WORKER_UID,attack)
            ck("09_detached_signature_tamper_denied",
               no["status"]=="DENIED"
               and no["reason"]=="CRYPTO_SIGNATURE_REJECTED")
            other=os_request(normal,ATTACKER_UID,good)
            ck("10_valid_signature_wrong_kernel_uid_denied",
               other["status"]=="DENIED"
               and other["reason"]=="WRONG_OS_WORKER_SCOPE")
            before=request(normal,{"action":"snapshot"})
            need("head" in before,"CONTROLLER_SNAPSHOT_FAILURE_"+repr(before)[:150])
            ck("11_valid_wrong_claims_left_local_git_unchanged",
               before["head"]==initial
               and before["state"]["phase"]=="ACTIVE")
            ok=os_request(normal,WORKER_UID,good)
            changed=request(normal,{"action":"snapshot"})
            ck("12_one_valid_signed_worker_writes_local_git_ref",
               ok["status"]=="ONE_LOCAL_REF_EFFECT_VERIFIED"
               and changed["head"]!=initial
               and changed["state"]["effects"]==1)
            second=os_request(normal,WORKER_UID,good)
            ck("13_replay_valid_signature_after_effect_denied",
               second["status"]=="DENIED"
               and second["reason"]=="FROZEN_OR_ALREADY_COMMITTED")
            third=request(normal,{"action":"snapshot"})
            ck("14_no_second_ref_effect_after_replay",
               third["head"]==changed["head"]
               and third["state"]["effects"]==1)
        finally:close_sink(normal,p)
        crash=root/"after"
        proc,original_after=start_sink(crash)
        crash_body=claim(original_after,
                         expires_utc_ms=int(time.time()*1000)+60000)
        crash_req={"action":"effect","claim":crash_body,
                   "signature":signed_message(crash,crash_body)}
        lost=os_request(crash,WORKER_UID,crash_req)
        proc.wait(timeout=8)
        ck("15_actual_sink_process_dies_after_native_git_write",
           proc.returncode==72 and lost["status"]=="NO_ACK_UNKNOWN")
        process,recovered=start_sink(crash)
        try:
            snap=request(crash,{"action":"snapshot"})
            ck("16_restart_freezes_pending_UNKNOWN_durably",
               snap["state"]["phase"]=="FROZEN_UNKNOWN"
               and snap["head"]==snap["state"]["candidate"]
               and snap["head"]!=original_after)
            denied=os_request(crash,WORKER_UID,crash_req)
            ck("17_crash_surviving_signature_cannot_blind_retry",
               denied["status"]=="DENIED"
               and denied["reason"]=="FROZEN_OR_ALREADY_COMMITTED")
            root_only=request(crash,{"action":"reconcile"})
            ck("18_explicit_kernel_root_reconciliation_verifies_git",
               root_only["status"]=="ROOT_CONTROL"
               and root_only["reason"]=="MANUAL_READBACK_CONFIRMED")
            final=request(crash,{"action":"snapshot"})
            ck("19_native_local_git_one_effect_after_lost_ack",
               final["state"]["phase"]=="COMMITTED_VERIFIED"
               and final["state"]["effects"]==1
               and final["head"]==snap["head"])
            last=os_request(crash,WORKER_UID,crash_req)
            ck("20_no_reexecution_after_independent_reconciliation",
               last["status"]=="DENIED"
               and request(crash,{"action":"snapshot"})["head"]==final["head"])
        finally:close_sink(crash,process)
    need(len(cases)==24 and all(cases.values()),
         "CP076_ALL_NATIVE_DENIAL_CONTROLS_NOT_PASSED")
    return {
        "schema":SCHEMA,
        "status":"PASS_CP076_REAL_DIFFERENT_UID_CRYPTO_AND_LOCAL_GIT",
        "real_checks":len(cases),"real_passes":sum(cases.values()),
        "separate_signer_uid":SIGNER_UID,"separate_sink_uid":SINK_UID,
        "worker_uid":WORKER_UID,"worker_no_git_or_signer_key_dac":True,
        "linux_so_peercred":True,"real_ed25519_sign_and_verify":True,
        "real_local_git_ref_effect":True,
        "lost_ack_sqlite_UNKNOWN_no_retry":True,
        "canonical_core604_lease_issuer":False,
        "provider_live_revocation_consulted":False,
        "remote_github_git_sink_authority":False,
        "github_credentials":False,"remote_git_writes":0,
        "model_generated_source_executed":False,
        "new_os_accounts_created":False,"production_authority":False,
        "new_schedulers":False,"source_sha256":hashlib.sha256(
             Path(__file__).read_bytes()).hexdigest(),
    }


def main(argv: list[str]) -> dict:
    need(len(argv)>=2,"MODE_REQUIRED")
    if argv[1]=="selftest" and len(argv)==2:return selftest()
    if argv[1]=="native" and len(argv)==2:return run_native()
    if argv[1]=="_serve" and len(argv)==3:
        serve(argv[2]);return {"status":"SERVER_CLOSED"}
    if argv[1]=="_request" and len(argv)==3:
        obj=json.loads(sys.stdin.buffer.readline(MAX_REQUEST))
        print(json.dumps(request(roots(argv[2]),obj),sort_keys=True))
        return {"status":"SINGLE_CALL_ONLY"}
    if argv[1]=="_probe" and len(argv)==3:
        root=roots(argv[2])
        probes={}
        for n,file,mode in (
            ("signer_private_key_denied",root/"signer"/"ephemeral_ed25519","rb"),
            ("fake_sink_token_denied",root/"sink"/"FAKE_CREDENTIAL_NOT_REAL","rb"),
            ("sink_git_head_denied",root/"sink"/"local.git"/"HEAD","rb"),
        ):
            try:
                with open(file,mode):pass
            except PermissionError:probes[n]=True
            else:probes[n]=False
        # Never target the real ref even in a negative probe. A failing
        # ref delete can disturb a repository on some Git backends.
        lock=(root/"sink"/"local.git"/"refs"/"heads"/"cp076-forbidden.lock")
        try:
            with open(lock,"xb") as fd:fd.write(b"UNAUTHORIZED")
        except PermissionError:
            probes["direct_git_write_denied"]=True
        else:
            probes["direct_git_write_denied"]=False
        print(json.dumps(probes,sort_keys=True))
        return {"status":"PROBE_DONE"}
    raise Refuse("UNAUTHORIZED_MODE")


if __name__=="__main__":
    try:
        result=main(sys.argv)
        if sys.argv[1] in ("selftest","native"):
            print(json.dumps(result,sort_keys=True),flush=True)
        raise SystemExit(0)
    except (Refuse,KeyError,TypeError,ValueError,RuntimeError,
            OSError,subprocess.SubprocessError) as e:
        print(json.dumps({"status":"FAIL_CLOSED",
                          "reason":str(e)[:180],"remote_git_writes":0,
                          "production_authority":False},
                         sort_keys=True),flush=True)
        raise SystemExit(2)
