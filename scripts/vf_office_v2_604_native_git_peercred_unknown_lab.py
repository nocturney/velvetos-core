#!/usr/bin/env python3
"""#604 checkpoint47: real LOCAL bare-Git CAS behind Linux peer-UID sink.

OFFLINE / DANGEROUSLY EASY TO MISREAD: the authority is a sink-local SQLite
fixture, and the Git ref is a separate local bare repo. Neither is GitHub,
etcd, a credentialed API, Dagu, production fencing, or a network protocol.
Executes only with VF604_DISPOSABLE_LINUX_LAB=YES as root inside a disposable
Linux container. No real OS account creation, network socket, token or user
machine changes. An existing known-UID assignment fails closed.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import pwd
import select
import shutil
import socket
import sqlite3
import struct
import subprocess
import sys
import tempfile
import threading

SCHEMA = "vf604.native-git-peercred-unknown-offline.v1"
SINK_UID, WORKER_A_UID, WORKER_B_UID, ATTACKER_UID = 62001, 62002, 62003, 62004
BOUND_WORKERS = {WORKER_A_UID: "worker-a", WORKER_B_UID: "worker-b"}
REF = "refs/heads/vf604-local-checkpoint47-only"
JOB = "vf604-checkpoint47-fixed-logical-intent"
SOURCE_BYTES = b"vf604 CHECKPOINT47 PUBLIC SYNTHETIC INPUT - NOT USER CODE\n"
SOURCE_SHA256 = hashlib.sha256(SOURCE_BYTES).hexdigest()
INITIAL_BYTES = b"fixture-initial\n"
MAX_LINE = 8192
GIT_ENV = {
    "PATH": "/usr/bin:/bin", "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_ALLOW_PROTOCOL": "file",
    "GIT_AUTHOR_NAME": "VF604 offline sink", "GIT_AUTHOR_EMAIL": "vf604@example.invalid",
    "GIT_COMMITTER_NAME": "VF604 offline sink", "GIT_COMMITTER_EMAIL": "vf604@example.invalid",
    "GIT_AUTHOR_DATE": "2001-01-01T00:00:00 +0000",
    "GIT_COMMITTER_DATE": "2001-01-01T00:00:00 +0000",
}


def drop(uid):
    def cb():
        os.setgroups([])
        os.setgid(uid)
        os.setuid(uid)
    return cb


def lab_dir(value):
    # Limit effects to one of four fresh scenarios beneath an opaque marked
    # directory, never to an arbitrary path or a symlink.
    raw = Path(value)
    if raw.is_symlink():
        raise RuntimeError("SYMLINK_SCENARIO")
    x = raw.resolve(strict=True)
    if x.name not in ("race", "before", "after", "outage"):
        raise RuntimeError("SCENARIO_NOT_ALLOWED")
    base = x.parent
    if not base.name.startswith("vf604-git-peer-") or not (base / ".vf604-disposable").is_file():
        raise RuntimeError("NO_MARKED_ROOT")
    if not (x / ".vf604-disposable").is_file():
        raise RuntimeError("NO_SCENARIO_MARKER")
    return x


def git(repo, *args, input_text=None):
    p = subprocess.run(["git", "--git-dir", str(repo), *args], input=input_text,
                       text=True, capture_output=True, timeout=12, env=GIT_ENV)
    if p.returncode:
        raise RuntimeError("GIT_NATIVE_FAILED: " + " ".join(args) + " " + p.stderr[:160])
    return p.stdout.strip()


def commit(repo, body, parent=None):
    blob = git(repo, "hash-object", "-w", "--stdin", input_text=body.decode("utf-8"))
    tree = git(repo, "mktree", input_text=f"100644 blob {blob}\tproof.txt\n")
    args = ("commit-tree", tree, "-p", parent) if parent else ("commit-tree", tree)
    new_commit = git(repo, *args, input_text="fixed scoped source\n")
    if len(new_commit) != 40:
        raise RuntimeError("BAD_COMMIT_SHA")
    return new_commit


def connect_db(db):
    x = sqlite3.connect(str(db), isolation_level=None, timeout=12)
    x.execute("PRAGMA busy_timeout=12000")
    x.execute("PRAGMA synchronous=FULL")
    return x


def init_server(root):
    # Invoked under SINK_UID, NEVER under worker UID.
    store = root / "store"
    db = store / "intent.sqlite3"
    repo = store / "scratch.git"
    first = not db.exists()
    if first:
        (store / "FAKE_SINK_ONLY_CREDENTIAL").write_text("VF604_FALSE_SECRET_DO_NOT_USE\n")
        os.chmod(store / "FAKE_SINK_ONLY_CREDENTIAL", 0o600)
        p = subprocess.run(["git", "init", "--bare", "--quiet", str(repo)],
                           capture_output=True, text=True, timeout=12, env=GIT_ENV)
        if p.returncode:
            raise RuntimeError("GIT_INIT_FAILED: " + p.stderr[:100])
        os.chmod(repo, 0o700)
        initial = commit(repo, INITIAL_BYTES)
        git(repo, "update-ref", REF, initial)
        with connect_db(db) as con:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("CREATE TABLE state (id INTEGER PRIMARY KEY CHECK(id=1), actor TEXT, "
                        "epoch INTEGER, revision INTEGER, provider TEXT, phase TEXT, "
                        "initial_sha TEXT, intent_id TEXT, attempt_id TEXT, "
                        "expected_sha TEXT, candidate_sha TEXT, write_count INTEGER)")
            con.execute("INSERT INTO state VALUES(1,'worker-a',7,1,'UP','ACTIVE',?,NULL,NULL,NULL,NULL,0)",
                        (initial,))
            con.execute("CREATE TABLE audit (id INTEGER PRIMARY KEY, uid INTEGER, action TEXT, "
                        "reason TEXT, phase TEXT, epoch INTEGER)")
    else:
        # A killed or crashed writer may already have modified the Git ref.
        # A separately verified dead process precedes startup in lab controller.
        with connect_db(db) as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT phase FROM state WHERE id=1").fetchone()
            if row is None:
                raise RuntimeError("STATE_MISSING")
            if row[0] in ("INTENT_DURABLE", "EFFECT_IN_FLIGHT"):
                con.execute("UPDATE state SET phase='FROZEN_UNKNOWN', revision=revision+1 WHERE id=1")
                con.execute("INSERT INTO audit(uid,action,reason,phase,epoch) "
                            "SELECT ?, 'restart', 'UNKNOWN_NO_AUTOREPLAY', phase, epoch FROM state WHERE id=1",
                            (SINK_UID,))
            con.execute("COMMIT")
    return db, repo


def peer_uid(c):
    pid, uid, gid = struct.unpack("3i", c.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    return uid


def audit(con, uid, action, reason, phase, epoch):
    con.execute("INSERT INTO audit(uid,action,reason,phase,epoch) VALUES (?,?,?,?,?)",
                (uid, action or "invalid", reason, phase, epoch))


def examine(con):
    return dict(zip(("actor","epoch","revision","provider","phase","initial_sha",
                     "intent_id","attempt_id","expected_sha","candidate_sha","write_count"),
                    con.execute("SELECT actor,epoch,revision,provider,phase,initial_sha,intent_id,"
                                "attempt_id,expected_sha,candidate_sha,write_count FROM state WHERE id=1").fetchone()))


def payload(actor, epoch, expected, attempt):
    return {"action":"propose", "worker_id":actor, "capability":"local_git_ref_only",
            "source_sha256":SOURCE_SHA256, "intent_id":JOB, "attempt_id":attempt,
            "expected_sha":expected, "epoch":epoch}


def service(root):
    root = lab_dir(root)
    db, repo = init_server(root)
    sock = root / "endpoint" / "sink.sock"
    if sock.is_symlink():
        raise RuntimeError("SYMLINK_SOCKET_REFUSED")
    if sock.exists():
        # Trusted lab controller explicitly verified predecessor exited.
        sock.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock))
    os.chmod(sock, 0o666)
    server.listen(24)
    closing = threading.Event()
    print("READY " + git(repo, "rev-parse", REF), flush=True)

    def worker(c):
        with c:
            try:
                uid = peer_uid(c)
                data = bytearray()
                while len(data) <= MAX_LINE and b"\n" not in data:
                    x = c.recv(512)
                    if not x:
                        break
                    data.extend(x)
                if len(data) > MAX_LINE or b"\n" not in data:
                    reply = {"status":"DENIED", "reason":"BAD_REQUEST_LENGTH"}
                else:
                    req = json.loads(data.split(b"\n", 1)[0])
                    action = req.get("action") if isinstance(req, dict) else None
                    with connect_db(db) as con:
                        con.execute("BEGIN IMMEDIATE")
                        s = examine(con)
                        phase,epoch,actor = s["phase"],s["epoch"],s["actor"]
                        current = git(repo, "rev-parse", REF)
                        reply={"status":"DENIED", "reason":"INVALID_REQUEST", "ref_sha":current}
                        if uid == 0 and action in ("snapshot","rotate","outage","reconcile","shutdown"):
                            if action == "snapshot":
                                reply={"status":"CONTROLLER","reason":"SNAPSHOT", "state":s,
                                       "actual_git_sha":current}
                            elif action == "rotate":
                                if phase != "ACTIVE" or s["provider"] != "UP" or s["intent_id"] is not None:
                                    reply["reason"]="CANNOT_CUTOVER_INFLIGHT_OR_TERMINAL"
                                else:
                                    con.execute("UPDATE state SET actor='worker-b',epoch=8,revision=revision+1 WHERE id=1")
                                    reply["reason"]="ROTATED_REF_UNCHANGED"
                                    reply["status"]="CONTROLLER"
                            elif action == "outage":
                                con.execute("UPDATE state SET provider='DOWN',revision=revision+1 WHERE id=1")
                                reply["reason"]="PROVIDER_DOWN"
                                reply["status"]="CONTROLLER"
                            elif action == "reconcile":
                                # Independent caller must have verified the old sink exited;
                                # this function does NOT prove real external provider commit.
                                if phase != "FROZEN_UNKNOWN":
                                    reply["reason"]="NOT_UNKNOWN"
                                elif current == s["candidate_sha"]:
                                    con.execute("UPDATE state SET phase='COMMITTED_VERIFIED', "
                                                "write_count=write_count+1,revision=revision+1 WHERE id=1")
                                    reply.update(status="CONTROLLER",reason="MANUAL_VERIFIED_GIT_EFFECT")
                                elif current == s["expected_sha"]:
                                    con.execute("UPDATE state SET phase='MANUAL_CLOSED_NO_RETRY', "
                                                "revision=revision+1 WHERE id=1")
                                    reply.update(status="CONTROLLER",reason="MANUAL_NO_EFFECT_NO_RETRY")
                                else:
                                    reply["reason"]="GIT_CONFLICT_STILL_UNKNOWN"
                            elif action == "shutdown":
                                closing.set()
                                reply.update(status="CONTROLLER",reason="SHUTDOWN")
                        elif action == "propose":
                            bound=BOUND_WORKERS.get(uid)
                            if bound is None:
                                reply["reason"]="OS_PRINCIPAL_UNKNOWN"
                            elif req.get("worker_id")!=bound:
                                reply["reason"]="KERNEL_UID_WORKER_BINDING"
                            elif req.get("capability")!="local_git_ref_only":
                                reply["reason"]="CAPABILITY_DENIED"
                            elif req.get("source_sha256")!=SOURCE_SHA256 or req.get("intent_id")!=JOB:
                                reply["reason"]="UNTRUSTED_INPUT_SCOPE"
                            elif not isinstance(req.get("attempt_id"),str) or not 0 < len(req["attempt_id"]) < 60:
                                reply["reason"]="INVALID_ATTEMPT"
                            elif "inject_crash" in req:
                                reply["reason"]="WORKER_CANNOT_REQUEST_FAULT_INJECTION"
                            elif s["provider"]!="UP":
                                reply["reason"]="AUTHORITY_UNAVAILABLE"
                            elif phase != "ACTIVE":
                                reply["reason"]="FROZEN_UNKNOWN_OR_COMMITTED"
                            elif s["intent_id"] is not None:
                                reply["reason"]="DUPLICATE_LOGICAL_INTENT"
                            elif epoch!=req.get("epoch") or actor!=bound:
                                reply["reason"]="STALE_OR_FOREIGN_EPOCH_DENIED"
                            elif current!=req.get("expected_sha"):
                                reply["reason"]="NATIVE_GIT_CAS_MISMATCH"
                            else:
                                # Commit object is staged in LOCAL bare Git without ref change.
                                candidate = commit(repo, SOURCE_BYTES, current)
                                con.execute("UPDATE state SET phase='EFFECT_IN_FLIGHT', "
                                            "intent_id=?,attempt_id=?,expected_sha=?,candidate_sha=?, "
                                            "revision=revision+1 WHERE id=1",
                                            (JOB,req["attempt_id"],current,candidate))
                                audit(con,uid,action,"DURABLE_INTENT_BEFORE_GIT",phase,epoch)
                                con.execute("COMMIT")  # FULL SQLite durability; separate Git not atomic.
                                # The disposable scenario (set by the ROOT harness) owns
                                # fault injection. Untrusted workers cannot crash a sink.
                                if root.name == "before":
                                    os._exit(71)  # no response, no native Git ref update
                                git(repo, "update-ref", REF, candidate, current)  # REAL native Git CAS
                                if root.name == "after":
                                    os._exit(72)  # real effect, no ACK or terminal SQLite record
                                native = git(repo, "rev-parse", REF)
                                if native != candidate:
                                    raise RuntimeError("NATIVE_GIT_READBACK_CONFLICT")
                                con.execute("BEGIN IMMEDIATE")
                                con.execute("UPDATE state SET phase='COMMITTED_VERIFIED', "
                                            "write_count=write_count+1,revision=revision+1 WHERE id=1")
                                audit(con,uid,action,"ONE_NATIVE_GIT_EFFECT",phase,epoch)
                                con.execute("COMMIT")
                                c.sendall((json.dumps({"status":"LOCAL_GIT_EFFECT_VERIFIED",
                                    "reason":"ONE_NATIVE_GIT_REF_UPDATE", "ref_sha":native})+"\n").encode())
                                return
                        audit(con,uid,action,reply["reason"],phase,epoch)
                        con.execute("COMMIT")
                c.sendall((json.dumps(reply,sort_keys=True)+"\n").encode())
            except BaseException as e:
                try: c.sendall((json.dumps({"status":"DENIED","reason":"SERVER_EXCEPTION_"+
                    type(e).__name__})+"\n").encode())
                except (OSError,BrokenPipeError): pass
    try:
        while not closing.is_set():
            server.settimeout(0.3)
            try: c,_=server.accept()
            except socket.timeout: continue
            threading.Thread(target=worker,args=(c,),daemon=True).start()
    finally:
        server.close()
        if sock.exists(): sock.unlink()


def request(root, obj):
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    s.settimeout(8)
    try:
        s.connect(str(Path(root)/"endpoint"/"sink.sock"))
        s.sendall((json.dumps(obj,sort_keys=True)+"\n").encode())
        buf=b""
        while b"\n" not in buf and len(buf)<MAX_LINE:
            x=s.recv(2048)
            if not x: break
            buf+=x
        return json.loads(buf.split(b"\n")[0]) if buf else {"status":"NO_ACK_UNKNOWN","reason":"NO_ACK"}
    except (ConnectionError,BrokenPipeError):
        return {"status":"NO_ACK_UNKNOWN","reason":"NO_ACK"}
    finally:
        s.close()


def subprocess_client(root, uid, obj):
    p=subprocess.run([sys.executable,os.path.realpath(__file__),"_client",str(root),json.dumps(obj)],
        capture_output=True,text=True,timeout=16,preexec_fn=drop(uid),
        env={"PATH":"/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1"})
    if p.returncode or not p.stdout.strip():
        raise RuntimeError("CHILD_CLIENT_FAILED " + p.stderr[:160])
    return json.loads(p.stdout)


def direct_probe(root):
    root=lab_dir(root)
    store=root/"store"
    checks={}
    for name,p,mode in (
            ("fake_token",store/"FAKE_SINK_ONLY_CREDENTIAL","rb"),
            ("sink_sqlite",store/"intent.sqlite3","ab"),
            ("bare_git_head",store/"scratch.git"/"HEAD","rb")):
        try:
            with open(p,mode) as h:
                if mode=="ab": h.write(b"ILLEGAL_DIRECT_WRITE")
            checks[name]=False
        except PermissionError:
            checks[name]=True
    p=subprocess.run(["git","--git-dir",str(store/"scratch.git"),"update-ref",REF,"a"*40],
        capture_output=True,text=True,timeout=6,env=GIT_ENV)
    checks["native_git_direct_write_denied"]=(p.returncode!=0)
    print(json.dumps(checks,sort_keys=True))



def launch(root):
    server=subprocess.Popen([sys.executable,os.path.realpath(__file__),"_serve",str(root)],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
        preexec_fn=drop(SINK_UID),env={"PATH":"/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1"})
    ready,_,_=select.select([server.stdout],[],[],8)
    if not ready:
        server.terminate();server.wait(timeout=4)
        raise RuntimeError("SINK_READY_TIMEOUT")
    line=server.stdout.readline().strip()
    if not line.startswith("READY "):
        err=server.stderr.read()[:700]
        raise RuntimeError("SINK_FAILED: " + line + " " + err)
    return server,line.split(" ",1)[1]


def close(root, process):
    if process.poll() is None:
        try: request(root,{"action":"shutdown"});process.wait(timeout=6)
        except subprocess.TimeoutExpired: process.terminate();process.wait(timeout=5)
    return process.returncode


def main_lab():
    if sys.platform!="linux" or not hasattr(socket,"SO_PEERCRED") or os.geteuid()!=0 \
            or os.environ.get("VF604_DISPOSABLE_LINUX_LAB")!="YES" or not shutil.which("git"):
        print(json.dumps({"schema":SCHEMA,"status":"NOT_RUN_REQUIRES_EXPLICIT_LINUX_CONTAINER_GATE"}))
        return 3
    for uid in (SINK_UID,WORKER_A_UID,WORKER_B_UID,ATTACKER_UID):
        try: pwd.getpwuid(uid)
        except KeyError: continue
        print(json.dumps({"schema":SCHEMA,"status":"NOT_RUN_UID_ASSIGNED","uid":uid}))
        return 3
    outcome=[]
    def ck(name,condition,evidence=""):
        outcome.append({"case":name,"passed":bool(condition),"evidence":str(evidence)[:240]})
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix="vf604-git-peer-") as td:
        root=Path(td)
        # 1: Native bare Git, kernel UID admission, stale/latest SHA, cross-UID race.
        # Lab-root safety marker must be under immediate marked prefix path.
        (root / ".vf604-disposable").write_text("disposable root\n")
        os.chmod(root, 0o755)
        for sub in ("race","before","after","outage"):
            p=root/sub
            p.mkdir(exist_ok=True)
            os.chmod(p,0o755)
            # Named scenario is below a guaranteed unpredictable vf604-git-peer-*.
            (p/".vf604-disposable").write_text("scoped\n")
            os.chmod(p,0o755)
            setup_children(p)
        path=root/"race"
        process,head=launch(path)
        try:
            actual=git(path/"store"/"scratch.git","rev-parse",REF)
            ck("N01_NATIVE_INITIAL_GIT_OBJECT",actual==head and len(actual)==40,actual)
            direct_results=[]
            for uid in (WORKER_A_UID,WORKER_B_UID,ATTACKER_UID):
                p=subprocess.run([sys.executable,os.path.realpath(__file__),"_direct",str(path)],
                   capture_output=True,text=True,timeout=9,preexec_fn=drop(uid),env={"PATH":"/usr/bin:/bin"})
                direct_results.append((p.returncode,json.loads(p.stdout)))
            ck("N02_WORKERS_OS_BLOCK_GIT_AND_FAKE_TOKEN",
               all(ret==0 and all(x.values()) for ret,x in direct_results),direct_results)
            impostor=payload("worker-b",7,head,"false-ID")
            deny=subprocess_client(path,WORKER_A_UID,impostor)
            ck("N03_KERNEL_UID_REJECTS_SELF_ASSERTED_ID",deny["reason"]=="KERNEL_UID_WORKER_BINDING",deny)
            deny=subprocess_client(path,ATTACKER_UID,payload("worker-a",7,head,"unauthorized"))
            ck("N04_UNKNOWN_OS_UID_DENIED",deny["reason"]=="OS_PRINCIPAL_UNKNOWN",deny)
            deny=subprocess_client(path,WORKER_A_UID,dict(payload("worker-a",7,head,"capability"),capability="github_push"))
            ck("N05_REMOTE_CAPABILITY_DENIED",deny["reason"]=="CAPABILITY_DENIED",deny)
            deny=subprocess_client(path,WORKER_A_UID,{"action":"rotate"})
            ck("N06_WORKER_CANNOT_ROTATE_PROVIDER",deny["status"]=="DENIED",deny)
            # Root-only scenario controls fault injection; a worker cannot ask
            # the sink to crash after a ref update or force an ACK loss.
            adversarial=dict(payload("worker-a",7,head,"force-crash"),
                             inject_crash="after_write")
            refused=subprocess_client(path,WORKER_A_UID,adversarial)
            ck("N06B_WORKER_FAULT_INJECTION_DENIED",
               refused["reason"]=="WORKER_CANNOT_REQUEST_FAULT_INJECTION"
               and git(path/"store"/"scratch.git","rev-parse",REF)==head,refused)
            rot=request(path,{"action":"rotate"})
            ck("N07_CONTROLLER_CUTOVER_NO_GIT_CHANGE",rot["reason"]=="ROTATED_REF_UNCHANGED"
               and git(path/"store"/"scratch.git","rev-parse",REF)==head,rot)
            stale=subprocess_client(path,WORKER_A_UID,payload("worker-a",7,head,"old-latest-SHA"))
            ck("N08_STALE_OWNER_CURRENT_REAL_GIT_SHA_DENIED",
               stale["reason"]=="STALE_OR_FOREIGN_EPOCH_DENIED" and stale["ref_sha"]==head,stale)
            tasks=[(WORKER_B_UID,payload("worker-b",8,head,"b-race-1")),
                   (WORKER_B_UID,payload("worker-b",8,head,"b-race-2")),
                   (WORKER_A_UID,payload("worker-a",7,head,"old-race"))]
            procs=[subprocess.Popen([sys.executable,os.path.realpath(__file__),"_client",str(path),json.dumps(o)],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,preexec_fn=drop(u),
                env={"PATH":"/usr/bin:/bin"}) for u,o in tasks]
            vals=[]
            for q in procs:
                raw,err=q.communicate(timeout=16)
                vals.append(json.loads(raw))
            successes=sum(v["status"]=="LOCAL_GIT_EFFECT_VERIFIED" for v in vals)
            sha=git(path/"store"/"scratch.git","rev-parse",REF)
            snap=request(path,{"action":"snapshot"})
            ck("N09_TWO_UID_THREE_PROCESS_REAL_GIT_SINGLE_WRITER",
               successes==1 and vals[2]["status"]=="DENIED" and sha!=head,
               [v["reason"] for v in vals])
            ck("N10_GIT_READBACK_MATCHES_DURABLE_RECEIPT",snap["state"]["phase"]=="COMMITTED_VERIFIED"
               and snap["state"]["write_count"]==1 and snap["state"]["candidate_sha"]==sha,sha)
            second=subprocess_client(path,WORKER_B_UID,payload("worker-b",8,sha,"duplicate"))
            ck("N11_EXACT_LOGICAL_DUPLICATE_REFUSED",second["status"]=="DENIED" and
               git(path/"store"/"scratch.git","rev-parse",REF)==sha,second)
        finally: close(path,process)

        # 2: crash BEFORE native Git update, durable in-flight intent and NO replay.
        path=root/"before";process,head=launch(path)
        no_ack=subprocess_client(path,WORKER_A_UID,payload("worker-a",7,head,"before-crash"))
        process.wait(timeout=8)
        raw_phase=read_state(path)["phase"]
        actual=git(path/"store"/"scratch.git","rev-parse",REF)
        ck("N12_PRE_GIT_CRASH_DURABLE_UNLEASED_INTENT",process.returncode==71 and
           no_ack["status"]=="NO_ACK_UNKNOWN" and actual==head and raw_phase=="EFFECT_IN_FLIGHT",
           [process.returncode,no_ack,raw_phase])
        process, restarted_head=launch(path)
        try:
            snap=request(path,{"action":"snapshot"})
            reject=subprocess_client(path,WORKER_A_UID,payload("worker-a",7,head,"rerun-before"))
            ck("N13_PRE_GIT_RECOVERY_UNKNOWN_FREEZE",snap["state"]["phase"]=="FROZEN_UNKNOWN"
               and reject["status"]=="DENIED" and restarted_head==head, reject)
            recon=request(path,{"action":"reconcile"})
            ck("N14_MANUAL_NO_EFFECT_CLOSE_NO_RETRY",recon["reason"]=="MANUAL_NO_EFFECT_NO_RETRY"
               and git(path/"store"/"scratch.git","rev-parse",REF)==head,recon)
        finally: close(path,process)

        # 3: crash AFTER REAL Git ref update but before SQL receipt / ACK.
        path=root/"after";process,head=launch(path)
        no_ack=subprocess_client(path,WORKER_A_UID,payload("worker-a",7,head,"after-crash"))
        process.wait(timeout=8)
        actual=git(path/"store"/"scratch.git","rev-parse",REF)
        raw=read_state(path)
        ck("N15_POST_GIT_PRE_ACK_CRASH_IS_AMBIGUOUS",process.returncode==72 and
           no_ack["status"]=="NO_ACK_UNKNOWN" and actual!=head and
           raw["phase"]=="EFFECT_IN_FLIGHT" and raw["candidate_sha"]==actual,
           [process.returncode,raw["phase"],actual])
        process,new_head=launch(path)
        try:
            snap=request(path,{"action":"snapshot"})
            replay=subprocess_client(path,WORKER_A_UID,payload("worker-a",7,actual,"blind-retry"))
            ck("N16_NO_ACK_RESTART_NEVER_BLIND_REPLAYS",snap["state"]["phase"]=="FROZEN_UNKNOWN"
               and replay["status"]=="DENIED" and git(path/"store"/"scratch.git","rev-parse",REF)==actual,
               replay)
            recon=request(path,{"action":"reconcile"})
            post=request(path,{"action":"snapshot"})
            ck("N17_MANUAL_GIT_READBACK_VERIFIES_COMMIT",recon["reason"]=="MANUAL_VERIFIED_GIT_EFFECT"
               and post["state"]["phase"]=="COMMITTED_VERIFIED"
               and post["state"]["write_count"]==1,post["state"]["phase"])
            blocked=subprocess_client(path,WORKER_A_UID,payload("worker-a",7,actual,"after-close"))
            ck("N18_NO_SECOND_GIT_EFFECT_AFTER_MANUAL_RECOVERY",blocked["status"]=="DENIED"
               and git(path/"store"/"scratch.git","rev-parse",REF)==actual,blocked)
        finally:close(path,process)

        # 4: canonical provider outage never permits Git ref write.
        path=root/"outage";process,head=launch(path)
        try:
            outage=request(path,{"action":"outage"})
            denied=subprocess_client(path,WORKER_A_UID,payload("worker-a",7,head,"offline"))
            ck("N19_PROVIDER_UNAVAILABLE_DENIES_REAL_GIT",outage["reason"]=="PROVIDER_DOWN"
               and denied["reason"]=="AUTHORITY_UNAVAILABLE" and
               git(path/"store"/"scratch.git","rev-parse",REF)==head,denied)
        finally:close(path,process)

    good=all(x["passed"] for x in outcome) and len(outcome)==20
    receipt={"schema":SCHEMA, "status":"PASS_DISPOSABLE_LINUX_NATIVE_GIT_WITH_UNKNOWN" if good else
             "FAIL_CLOSED_DO_NOT_ADMIT", "tests":len(outcome),
             "passed":sum(x["passed"] for x in outcome), "cases":outcome,
             "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             "host_os":sys.platform,"kernel_release":os.uname().release,
             "python_version":sys.version.split()[0],"git_version":subprocess.run(["git","--version"],
                 capture_output=True,text=True,timeout=3).stdout.strip(),
             "native_local_bare_git_update_ref":True,"real_kernel_so_peercred":True,
             "separate_numeric_os_uids":True,"same_process_single_sink_git_and_sqlite":True,
             "external_github_effect":False,"real_lease_provider":False,
             "cross_store_atomicity_proven":False,"production_credential_custody_proven":False,
             "external_git_remote_tested":False,"multi_host_fence_proven":False,
             "mid_push_expiry_fenced":False,"mac_windows_isolation_proven":False,
             "dagu_worker_identity_proven":False,"production_worker_admitted":False,
             "external_network_effects":0,"new_os_users":0,"new_tcp_listeners":0,
             "paid_api_calls":0,"production_effects":0}
    print(json.dumps(receipt,sort_keys=True,indent=2))
    return 0 if good else 1


def setup_children(root):
    for name,mode in (("store",0o700),("endpoint",0o755)):
        p=root/name
        p.mkdir(mode=mode)
        os.chown(p,SINK_UID,SINK_UID)
        os.chmod(p,mode)


def read_state(root):
    with connect_db(root/"store"/"intent.sqlite3") as con:
        return examine(con)


def main():
    if len(sys.argv)>=3 and sys.argv[1]=="_serve":
        service(lab_dir(sys.argv[2]))
        return 0
    if len(sys.argv)>=4 and sys.argv[1]=="_client":
        print(json.dumps(request(sys.argv[2],json.loads(sys.argv[3])),sort_keys=True))
        return 0
    if len(sys.argv)>=3 and sys.argv[1]=="_direct":
        # Probe accepts only a scenario in the disposable root (not arbitrary paths).
        direct_probe(lab_dir(sys.argv[2]))
        return 0
    if sys.argv[1:]==["lab"]: return main_lab()
    if sys.argv[1:]==["verify"]:
        print(json.dumps({"schema":SCHEMA,"status":"NOT_ADMITTED_NONPRODUCTION",
             "real_github_stale_epoch_deny":False,"production_worker_admitted":False}))
        return 0
    print("usage: vf_office_v2_604_native_git_peercred_unknown_lab.py lab|verify",file=sys.stderr)
    return 2


if __name__=="__main__":sys.exit(main())
