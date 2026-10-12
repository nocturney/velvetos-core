#!/usr/bin/env python3
"""#604: real Linux kernel peer-UID isolation, fixture-only sink (OFFLINE).

Explicitly NON-PRODUCTION. The effect and provider are synthetic rows in the
SAME local SQLite database, not GitHub, etcd or Dagu. This proves no cross-store
atomicity, no production Git credential security, and no Mac/Windows security.
Runs only as root in an isolated disposable Linux container. No user accounts
are created, no TCP sockets, no Git, no external calls or model inference.
"""
import hashlib
import json
import os
import pwd
import select
from pathlib import Path
import socket
import sqlite3
import struct
import subprocess
import sys
import tempfile
import threading

SCHEMA = "vf604.linux-peercred-sink-offline.v1"
SINK_UID = 62001
WORKER_A_UID = 62002
WORKER_B_UID = 62003
ATTACKER_UID = 62004
UID_TO_WORKER = {WORKER_A_UID: "worker-a", WORKER_B_UID: "worker-b"}
REF_A, REF_B = "a" * 40, "b" * 40
JOB = "vf604-peercred-single-logical-intent"
SOURCE = hashlib.sha256(b"vf604-fixed-public-synthetic-source-v1").hexdigest()
MAX_LINE = 8192


def drop(uid):
    def cb():
        os.setgroups([])
        os.setgid(uid)
        os.setuid(uid)
    return cb


def root_dir(p):
    raw = Path(p)
    if raw.is_symlink():
        raise RuntimeError("symbolic link is not a lab root")
    p = raw.resolve(strict=True)
    if not p.name.startswith("vf604-peercred-") or not (p / ".vf604-test-only").is_file():
        raise RuntimeError("unsafe lab directory")
    return p


def init_db(path):
    with sqlite3.connect(str(path), timeout=5, isolation_level=None) as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        con.execute("CREATE TABLE state (k INTEGER PRIMARY KEY CHECK(k=1), "
                    "lease_actor TEXT, epoch INTEGER, revision INTEGER, "
                    "provider TEXT, phase TEXT, ref_sha TEXT, accepted INTEGER, "
                    "intent_id TEXT, attempt_id TEXT)")
        con.execute("INSERT INTO state VALUES (1,'worker-a',7,1,'UP','ACTIVE',?,0,NULL,NULL)", (REF_A,))
        con.execute("CREATE TABLE audit (n INTEGER PRIMARY KEY, uid INTEGER, action TEXT, "
                    "decision TEXT, phase TEXT, epoch INTEGER)")


def record(con, uid, action, decision, phase, epoch):
    con.execute("INSERT INTO audit(uid, action, decision, phase, epoch) VALUES (?,?,?,?,?)",
                (uid, action, decision, phase, epoch))


def handle(con, uid, msg):
    con.execute("BEGIN IMMEDIATE")
    try:
        row = con.execute("SELECT lease_actor,epoch,revision,provider,phase,ref_sha,accepted,intent_id,attempt_id FROM state WHERE k=1").fetchone()
        actor, epoch, revision, provider, phase, ref, accepted, intent, attempt = row
        action = msg.get("action") if isinstance(msg, dict) else None
        result = {"status": "DENIED", "reason": "INVALID_REQUEST", "ref_sha": ref}
        if uid == 0 and action in ("rotate", "freeze", "partition", "snapshot", "shutdown"):
            if action == "rotate":
                if phase != "ACTIVE" or provider != "UP" or accepted:
                    result["reason"] = "ROTATE_DISALLOWED"
                else:
                    con.execute("UPDATE state SET lease_actor='worker-b', epoch=8, revision=revision+1 WHERE k=1")
                    result.update(status="CONTROLLER_ONLY", reason="ROTATED_EPOCH_REF_UNCHANGED")
            elif action in ("freeze", "partition"):
                if action == "freeze":
                    con.execute("UPDATE state SET phase='FROZEN_UNKNOWN', revision=revision+1 WHERE k=1")
                    result.update(status="CONTROLLER_ONLY", reason="FROZEN_UNKNOWN")
                else:
                    con.execute("UPDATE state SET provider='DOWN', revision=revision+1 WHERE k=1")
                    result.update(status="CONTROLLER_ONLY", reason="PROVIDER_UNAVAILABLE")
            elif action == "snapshot":
                result.update(status="CONTROLLER_ONLY", reason="SNAPSHOT", state={
                    "actor": actor, "epoch": epoch, "revision": revision, "provider": provider,
                    "phase": phase, "ref_sha": ref, "accepted": accepted, "intent_id": intent,
                    "attempt_id": attempt})
            else:
                result.update(status="CONTROLLER_ONLY", reason="SHUTDOWN")
        elif action == "propose":
            expected_actor = UID_TO_WORKER.get(uid)
            if expected_actor is None:
                result["reason"] = "OS_PRINCIPAL_NOT_ALLOWED"
            elif msg.get("worker_id") != expected_actor:
                result["reason"] = "OS_PRINCIPAL_WORKER_ID_MISMATCH"
            elif msg.get("capability") != "synthetic_local_ref":
                result["reason"] = "CAPABILITY_DENIED"
            elif msg.get("label") != ("host-" + expected_actor):
                result["reason"] = "UNTRUSTED_LABEL_DENIED"
            elif msg.get("source_sha256") != SOURCE or msg.get("intent_id") != JOB:
                result["reason"] = "INPUT_SCOPE_NOT_BOUND"
            elif not isinstance(msg.get("attempt_id"), str) or not 0 < len(msg["attempt_id"]) < 80:
                result["reason"] = "ATTEMPT_ID_INVALID"
            elif provider != "UP":
                result["reason"] = "PROVIDER_UNAVAILABLE"
            elif phase != "ACTIVE":
                result["reason"] = "FROZEN_UNKNOWN"
            elif accepted or intent is not None:
                result["reason"] = "DUPLICATE_LOGICAL_INTENT_DENIED"
            elif msg.get("epoch") != epoch or expected_actor != actor:
                result["reason"] = "STALE_OR_FOREIGN_EPOCH_DENIED"
            elif msg.get("expected_ref_sha") != ref:
                result["reason"] = "REF_CAS_MISMATCH"
            elif msg.get("proposed_ref_sha") != REF_B:
                result["reason"] = "TARGET_SHA_NOT_ALLOWED"
            else:
                # ONLY an atomic, local synthetic effect. Never Git/GitHub.
                con.execute("UPDATE state SET ref_sha=?, accepted=1, intent_id=?, attempt_id=? WHERE k=1",
                            (REF_B, JOB, msg["attempt_id"]))
                result.update(status="SYNTHETIC_LOCAL_EFFECT", reason="ONE_ATOMIC_LOCAL_EFFECT", ref_sha=REF_B)
        record(con, uid, action or "invalid", result["reason"], phase, epoch)
        con.execute("COMMIT")
        return result
    except BaseException:
        con.execute("ROLLBACK")
        raise


def peer_uid(c):
    if not hasattr(socket, "SO_PEERCRED"):
        raise RuntimeError("SO_PEERCRED required")
    _pid, uid, _gid = struct.unpack("3i", c.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    return uid


def serving(root):
    root = root_dir(root)
    sock = root / "sink.sock"
    db = root / "store" / "fixture.sqlite3"
    init_db(db)
    socket_server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    socket_server.bind(str(sock))
    os.chmod(sock, 0o666)  # open synthetic endpoint; peer-UID checks remain mandatory
    socket_server.listen(32)
    print("READY", flush=True)
    done = threading.Event()
    def serve_one(c):
        with c:
            try:
                uid = peer_uid(c)
                raw = bytearray()
                while len(raw) <= MAX_LINE:
                    packet = c.recv(min(1024, MAX_LINE + 1 - len(raw)))
                    if not packet: break
                    raw.extend(packet)
                    if b"\n" in raw: break
                if len(raw) > MAX_LINE or b"\n" not in raw:
                    reply = {"status":"DENIED","reason":"REQUEST_SIZE_OR_TERMINATION"}
                else:
                    parsed = json.loads(raw.split(b"\n", 1)[0])
                    with sqlite3.connect(str(db), timeout=10, isolation_level=None) as con:
                        reply = handle(con, uid, parsed)
                    if reply["reason"] == "SHUTDOWN" and uid == 0:
                        done.set()
            except BaseException as e:
                reply = {"status":"DENIED","reason":"SERVER_ERROR_" + type(e).__name__}
            c.sendall((json.dumps(reply,sort_keys=True) + "\n").encode())
    try:
        while not done.is_set():
            socket_server.settimeout(0.3)
            try: c, _ = socket_server.accept()
            except socket.timeout: continue
            threading.Thread(target=serve_one, args=(c,), daemon=True).start()
    finally:
        socket_server.close()
        try: sock.unlink()
        except FileNotFoundError: pass


def request(root, msg):
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    s.settimeout(4)
    try:
        s.connect(str(Path(root)/"sink.sock"))
        s.sendall((json.dumps(msg, sort_keys=True) + "\n").encode())
        data=bytearray()
        while b"\n" not in data and len(data)<MAX_LINE:
            part=s.recv(4096)
            if not part: break
            data.extend(part)
        return json.loads(data.split(b"\n",1)[0])
    finally: s.close()


def worker_payload(worker, epoch, expected_ref, attempt):
    return {"action":"propose", "worker_id":worker, "label":"host-"+worker,
            "capability":"synthetic_local_ref", "source_sha256":SOURCE,
            "intent_id":JOB, "attempt_id":attempt, "epoch":epoch,
            "expected_ref_sha":expected_ref, "proposed_ref_sha":REF_B}


def child_client(root, payload):
    print(json.dumps(request(root, json.loads(payload)),sort_keys=True))


def child_direct(root):
    # The two attempts below must BOTH be denied at actual OS filesystem boundary.
    root=Path(root)
    failures=[]
    for p, mode in [(root/"store"/"fake-git-token", "read"),
                    (root/"store"/"fixture.sqlite3", "write")]:
        try:
            with open(p, "rb" if mode=="read" else "ab") as f:
                if mode == "write": f.write(b"BAD_WRITE")
            failures.append({"operation":mode,"denied":False})
        except (PermissionError, FileNotFoundError):
            failures.append({"operation":mode,"denied":True})
    print(json.dumps(failures))


def child_run(root, uid, payload=None, direct=False):
    args=[sys.executable,os.path.realpath(__file__), "_direct" if direct else "_client", str(root)]
    if not direct: args.append(json.dumps(payload))
    return subprocess.run(args, capture_output=True, text=True, timeout=12,
                          preexec_fn=drop(uid), env={"PATH":"/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE":"1"})


def main_lab():
    if not (sys.platform.startswith("linux") and os.geteuid()==0 and hasattr(socket,"SO_PEERCRED")
            and os.environ.get("VF604_DISPOSABLE_LINUX_LAB")=="YES"):
        print(json.dumps({"schema":SCHEMA,"status":"NOT_RUN_REQUIRES_EXPLICIT_DISPOSABLE_LINUX_ROOT_GATE"}))
        return 3
    for uid in (SINK_UID, WORKER_A_UID, WORKER_B_UID, ATTACKER_UID):
        try: user=pwd.getpwuid(uid)
        except KeyError: continue
        print(json.dumps({"schema":SCHEMA,"status":"NOT_RUN_UID_ALREADY_ASSIGNED", "uid":uid}))
        return 3
    os.umask(0o077)
    outcomes=[]
    def check(key, verdict, detail=""):
        outcomes.append({"id":key,"pass":bool(verdict),"detail":detail})
    with tempfile.TemporaryDirectory(prefix="vf604-peercred-") as t:
        root=Path(t)
        (root/".vf604-test-only").write_text("test-only\n")
        store=root/"store"
        store.mkdir(mode=0o700)
        os.chown(store,SINK_UID,SINK_UID)
        secret=store/"fake-git-token"
        secret.write_text("VF604_FIXTURE_NOT_A_REAL_SECRET")
        os.chown(secret,SINK_UID,SINK_UID)
        os.chmod(secret,0o600)
        initial_secret_digest=hashlib.sha256(secret.read_bytes()).hexdigest()
        os.chown(root,SINK_UID,SINK_UID)
        os.chmod(root,0o755)
        child=subprocess.Popen([sys.executable, os.path.realpath(__file__), "_serve", str(root)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                               preexec_fn=drop(SINK_UID),env={"PATH":"/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1"})
        try:
            readable, _, _ = select.select([child.stdout], [], [], 6)
            if not readable:
                raise RuntimeError("sink start timed out without READY")
            if child.stdout.readline().strip() != "READY":
                raise RuntimeError("sink start exited without READY: " + child.stderr.read()[:1600])
            db=store/"fixture.sqlite3"
            def invoke(uid, payload):
                x=child_run(root,uid,payload)
                if x.returncode!=0: raise RuntimeError("client failed: " + x.stderr[:300])
                return json.loads(x.stdout)
            a=worker_payload("worker-a",7,REF_A,"a-preflight")
            b=worker_payload("worker-b",8,REF_A,"b-valid")
            c=worker_payload("worker-a",7,REF_A,"a-fake-b")
            c["worker_id"]="worker-b"
            res=invoke(WORKER_A_UID,c)
            check("L01_KERNEL_UID_MISMATCH",res["reason"]=="OS_PRINCIPAL_WORKER_ID_MISMATCH",res["reason"])
            res=invoke(ATTACKER_UID,a)
            check("L02_UNKNOWN_PRINCIPAL",res["reason"]=="OS_PRINCIPAL_NOT_ALLOWED",res["reason"])
            for key, value, eid in [("label","host-worker-b","L03_FALSE_LABEL"),
                                     ("capability","git_ref_write","L04_CAPABILITY_SCOPE"),
                                     ("source_sha256","0"*64,"L05_SOURCE_DIGEST")]:
                bad=a.copy();bad[key]=value
                res=invoke(WORKER_A_UID,bad)
                check(eid,res["status"]=="DENIED",res["reason"])
            root_only=invoke(WORKER_A_UID,{"action":"rotate"})
            check("L05B_WORKER_CANNOT_ROTATE_LEASE",root_only["status"]=="DENIED" and
                  root_only["reason"]=="INVALID_REQUEST")
            for uid, prefix in [(WORKER_A_UID,"A"),(WORKER_B_UID,"B"),(ATTACKER_UID,"C")]:
                out=child_run(root,uid,direct=True)
                results=json.loads(out.stdout)
                check("L06_OS_FILESYSTEM_DENY_"+prefix, out.returncode==0 and all(x["denied"] for x in results),str(results))
            # Rotate ownership on trusted controller while exact fake remote ref remains CURRENT.
            rot=request(root,{"action":"rotate"})
            snap=request(root,{"action":"snapshot"})["state"]
            check("L07_PROVIDER_EPOCH_ROTATED_REF_UNCHANGED",
                  rot["reason"]=="ROTATED_EPOCH_REF_UNCHANGED" and snap["ref_sha"]==REF_A
                  and snap["epoch"]==8 and snap["actor"]=="worker-b")
            # The former owner has the LATEST SHA, yet is denied before effect.
            stale=invoke(WORKER_A_UID,a)
            check("L08_STALE_OWNER_CURRENT_REF_DENIED", stale["reason"]=="STALE_OR_FOREIGN_EPOCH_DENIED"
                  and stale["ref_sha"]==REF_A,stale["reason"])
            # Concurrent separate processes, TWO distinct worker UIDs; only one local effect.
            cmd=[sys.executable,os.path.realpath(__file__),"_client",str(root)]
            p1=subprocess.Popen(cmd+[json.dumps(dict(b, attempt_id="b-race1"))],
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                                preexec_fn=drop(WORKER_B_UID),env={"PATH":"/usr/bin:/bin"})
            p2=subprocess.Popen(cmd+[json.dumps(dict(b, attempt_id="b-race2"))],
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                                preexec_fn=drop(WORKER_B_UID),env={"PATH":"/usr/bin:/bin"})
            p3=subprocess.Popen(cmd+[json.dumps(dict(a,attempt_id="a-race-expired"))],
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                                preexec_fn=drop(WORKER_A_UID),env={"PATH":"/usr/bin:/bin"})
            x1,e1=p1.communicate(timeout=12);x2,e2=p2.communicate(timeout=12)
            x3,e3=p3.communicate(timeout=12)
            z1,z2,z3=json.loads(x1),json.loads(x2),json.loads(x3)
            cnt=sum(z["reason"]=="ONE_ATOMIC_LOCAL_EFFECT" for z in (z1,z2,z3))
            check("L09_THREE_PROCESS_TWO_UID_LOCAL_SINGLE_EFFECT",
                  p1.returncode==0 and p2.returncode==0 and p3.returncode==0
                  and cnt==1
                  and {z1["reason"],z2["reason"]} == {
                      "ONE_ATOMIC_LOCAL_EFFECT","DUPLICATE_LOGICAL_INTENT_DENIED"}
                  and z3["reason"] in ("DUPLICATE_LOGICAL_INTENT_DENIED",
                                       "STALE_OR_FOREIGN_EPOCH_DENIED"),
                  z1["reason"]+"/"+z2["reason"]+"/"+z3["reason"])
            snap=request(root,{"action":"snapshot"})["state"]
            check("L10_READBACK_COMMIT_TARGET",snap["accepted"]==1 and snap["ref_sha"]==REF_B
                  and snap["intent_id"]==JOB and snap["attempt_id"] in ("b-race1","b-race2"))
            unknown=request(root,{"action":"freeze"})
            frozen=invoke(WORKER_B_UID,dict(b,expected_ref_sha=REF_B,attempt_id="b-after-freeze"))
            check("L11_UNKNOWN_FREEZE_DENY",unknown["reason"]=="FROZEN_UNKNOWN"
                  and frozen["reason"]=="FROZEN_UNKNOWN")
            part=request(root,{"action":"partition"})
            outage=invoke(WORKER_B_UID,dict(b,expected_ref_sha=REF_B,attempt_id="b-after-partition"))
            check("L12_PROVIDER_UNAVAILABLE_DENY",part["reason"]=="PROVIDER_UNAVAILABLE"
                  and outage["reason"]=="PROVIDER_UNAVAILABLE")
            with sqlite3.connect(str(db)) as con:
                row=con.execute("SELECT count(*) FROM audit WHERE decision='ONE_ATOMIC_LOCAL_EFFECT'").fetchone()[0]
                events=con.execute("SELECT count(*) FROM audit").fetchone()[0]
            after=hashlib.sha256(secret.read_bytes()).hexdigest()
            check("L13_ONLY_ONE_SINK_ACCEPTANCE",row==1 and initial_secret_digest==after and events>=10)
            stop=request(root,{"action":"shutdown"})
            try: child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                child.terminate();child.wait(timeout=5)
            check("L14_CLEAN_SHUTDOWN",stop["reason"]=="SHUTDOWN" and child.returncode==0
                  and not (root/"sink.sock").exists())
        finally:
            if child.poll() is None:
                child.terminate();child.wait(timeout=5)
    successful=all(x["pass"] for x in outcomes) and len(outcomes)==17
    report={"schema":SCHEMA,"status":"PASS_ISOLATED_LINUX_KERNEL_UID_SYNTHETIC_SINK" if successful
            else "FAIL_CLOSED_INCOMPLETE_LAB","tests":len(outcomes),"passed":sum(x["pass"] for x in outcomes),
            "cases":outcomes,"host_os":sys.platform,"kernel_release":os.uname().release,
            "python_version":sys.version.split()[0],"source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "real_kernel_so_peercred":True,
            "separate_numeric_uids_without_creating_accounts":True,"local_sqlite_effect_only":True,
            "uses_git":False,"uses_github":False,"uses_etcd":False,"uses_dagu":False,
            "remote_effects":0,"new_os_users":0,"tcp_listeners":0,
            "native_github_epoch_fence_proven":False,"cross_store_atomicity_proven":False,
            "mac_windows_security_isolation_proven":False,"production_credential_custody_proven":False,
            "production_worker_admitted":False}
    print(json.dumps(report,sort_keys=True,indent=2))
    return 0 if successful else 1


def main():
    if len(sys.argv)>=3 and sys.argv[1]=="_serve": serving(sys.argv[2]);return 0
    if len(sys.argv)>=4 and sys.argv[1]=="_client": child_client(sys.argv[2],sys.argv[3]);return 0
    if len(sys.argv)>=3 and sys.argv[1]=="_direct": child_direct(sys.argv[2]);return 0
    if sys.argv[1:]==["lab"]: return main_lab()
    if sys.argv[1:]==["verify"]:
        print(json.dumps({"schema":SCHEMA,"status":"DESIGN_ONLY_NOT_ADMITTED",
                          "native_github_fence_proven":False,"production_worker_admitted":False}))
        return 0
    print("usage: python vf_office_v2_604_linux_peercred_sink_lab.py lab|verify",file=sys.stderr)
    return 2

if __name__=="__main__": sys.exit(main())
