#!/usr/bin/env python3
"""CP077 fixed LAB: real etcd mTLS lease + separate Linux UID Ed25519/Git sink.

DO NOT ADMIT MODEL SOURCE. Root guest only orchestrates ephemeral resources:
a genuine pinned etcd with client-cert identities, real leased owner, unleased
intent, separate signer UID62005, worker UID62002, writer UID62001. The writer
itself verifies real provider state immediately BEFORE a native LOCAL Git CAS.
This is NOT a provider/Git cross-store atomic fence or a GitHub remote writer.
"""
from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid

import vf_office_v2_604_linux_signed_uid_git_join_cp076 as cp076
import vf_office_v2_604_real_etcd_mtls_rbac_identity_lab as identity

SCHEMA = "velvetos.office-v2.604.cp077-etcd-mtls-osuid-localgit.v1"
PREFIX = "/vf604/cp077/synthetic/"
PROVIDER_MARK = "CP077_REAL_PROVIDER_INTENT_NOT_REMOTE_GITHUB_EFFECT"
PINNED_ETCD = "117cc09981c0f1eb378e7520be6969756c2d6a762f376944e53f7bc9800c0c59"
PINNED_CTL = "de07257495499384f91f028dbc0c8e0394e0bd572b728ac486bbadbfa1cdf275"
ARCHIVE_SHA = "567d9b8fa9e75b349600d2b64ef9bf6bc6d512cea75a2ce1c39b1b3046131244"
PIN_CP076 = "521fa48d10c3e95b91c98207dade1c5e8ad708ed5ba5afd9b9fb0cfdf167a547"
PIN_IDENTITY = "b74c4b8a1baee7cc534ee82f7abede8c9b0c154ea9693143bb36d7c09319948c"
ENV_KEY = "VF604_CP077_DISPOSABLE_GUEST_ONLY"
ENV_VAL = "VF604_CP077_EXPLICIT_LINUX_MTLS_UID_TEST"
PROVIDER_CONF = "cp077-provider-config.json"
ROOT_PREFIX = "vf604-cp076-signed-uid-cp077-"
ORIGINAL_GIT = cp076.git


def need(condition: bool, why: str) -> None:
    if not condition:
        raise cp076.Refuse(why)


def sha256(path: Path) -> str:
    dig = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            dig.update(chunk)
    return dig.hexdigest()


def dependencies() -> None:
    need(sha256(Path(cp076.__file__))==PIN_CP076, "CP076_BASE_NOT_EXACT")
    need(sha256(Path(identity.__file__))==PIN_IDENTITY, "IDENTITY_MODULE_CHANGED")


def selftest() -> dict:
    dependencies()
    prev=cp076.selftest()
    need(prev["claim_mutation_denials"]==19 and prev["peer_uid_denials"]==4,
         "CP076_BASE_SELFTEST_NOT_PINNED")
    forged = [
       {"schema":"NO"}, {"schema":SCHEMA},
       {"schema":SCHEMA,"owner":"refs/heads/main"},
       {"schema":SCHEMA,"owner":"x","lease":True},
       {"schema":SCHEMA,"owner":"x","lease":1,"mod":True},
       {"schema":SCHEMA,"owner":"x","lease":1,"mod":1},
    ]
    for x in forged:
        try:config_check(x)
        except cp076.Refuse: pass
        else:raise cp076.Refuse("FORGED_PROVIDER_CONF_ADMITTED")
    return {"schema":SCHEMA,"status":"PASS_CP077_OFFLINE_NO_PROVIDER_OR_OS_EFFECT",
            "provider_config_mutants_denied":len(forged),
            "inherited_cp076_claim_denials":19,
            "inherited_cp076_peer_uid_denials":4,
            "real_provider_started":False,"private_key_created":False,
            "native_git_effect":False,"github_remote_writes":0,
            "model_source_executed":False,"production_authority":False}


def config_check(x: object) -> dict:
    fields={"schema","owner","intent","owner_value","owner_modrev","lease",
            "endpoint","etcdctl","etcdctl_sha","cacert","cert","key"}
    need(type(x) is dict and set(x)==fields,"PROVIDER_CONFIG_FIELDS_REFUSED")
    need(x["schema"]==SCHEMA,"PROVIDER_CONFIG_SCHEMA_WRONG")
    for f in ("owner","intent","owner_value","endpoint",
              "etcdctl","etcdctl_sha","cacert","cert","key"):
        need(type(x[f]) is str and bool(x[f]),"PROVIDER_FIELD_WRONG_"+f)
    need(x["owner"].startswith(PREFIX) and x["owner"].endswith("/owner"),
         "OWNER_MUST_BE_SYNTHETIC_EXACT_NAMESPACE")
    need(x["intent"]==x["owner"][:-5]+"intent","INTENT_NOT_BOUND_TO_OWNER")
    need(x["owner_value"]==fixed_owner_value(),"OWNER_SCOPE_BINDING_WRONG")
    need(type(x["owner_modrev"]) is int and x["owner_modrev"]>0,
         "OWNER_REVISION_NOT_INTEGER")
    need(type(x["lease"]) is int and x["lease"]>0,
         "PROVIDER_LEASE_NOT_REAL")
    need(x["endpoint"].startswith("https://127.0.0.1:"),
         "NON_LOOPBACK_PROVIDER_REFUSED")
    need(x["etcdctl_sha"]==PINNED_CTL,"PROVIDER_CTL_PIN_NOT_EXACT")
    for k in ("etcdctl","cacert","cert","key"):
        need(Path(x[k]).is_absolute(),"RELATIVE_PRIVILEGED_PROVIDER_PATH")
    return x


def fixed_owner_value() -> str:
    return "|".join(("cp077-fixed",cp076.HOST,str(cp076.WORKER_UID),
                     cp076.SOURCE_SHA,cp076.TASK,"epoch7"))


def ctl(root: Path, conf: dict, *args: str, stdin: str | None = None) -> dict:
    # Already inside the sink's real Linux UID62001 process when used to
    # authorize a Git effect. Root fixture only calls identity.ctl_ok.
    cmd=[conf["etcdctl"],"--endpoints",conf["endpoint"],
         "--cacert",conf["cacert"],"--cert",conf["cert"],
         "--key",conf["key"],"-w","json",*args]
    p=cp076.run_cmd(cmd,input_bytes=stdin.encode() if stdin else None,
                    check=False,timeout=7)
    need(p.returncode==0, "REAL_PROVIDER_UNAVAILABLE_OR_RBAC_DENIED")
    try:
        out=json.loads(p.stdout)
    except (ValueError,UnicodeDecodeError):
        raise cp076.Refuse("REAL_ETCDCTL_JSON_INVALID")
    need(type(out) is dict,"REAL_ETCDCTL_NONOBJECT")
    return out


def read_key(root: Path, conf: dict, key: str) -> dict | None:
    data=ctl(root,conf,"get",key)
    kvs=data.get("kvs",[])
    need(type(kvs) is list and len(kvs)<=1,
         "PROVIDER_GET_WIDE_OR_INVALID")
    if not kvs:return None
    kv=kvs[0]
    try:
        actual=base64.b64decode(kv["key"],validate=True).decode("utf8")
        value=base64.b64decode(kv["value"],validate=True).decode("utf8")
    except (ValueError,TypeError,KeyError,UnicodeDecodeError):
        raise cp076.Refuse("PROVIDER_KEY_ENCODING_BAD")
    need(actual==key,"REAL_PROVIDER_WRONG_KEY")
    return {"value":value,"mod_revision":int(kv["mod_revision"]),
            "lease":int(kv.get("lease","0")),
            "version":int(kv["version"])}


def current_owner(root: Path, conf: dict) -> dict:
    row=read_key(root,conf,conf["owner"])
    need(row is not None
         and row["value"]==conf["owner_value"]
         and type(row["lease"]) is int and row["lease"]==conf["lease"]
         and type(row["mod_revision"]) is int
         and row["mod_revision"]==conf["owner_modrev"],
         "LIVE_PROVIDER_OWNER_ABSENT_EXPIRED_OR_REVOKED")
    return row


def durable_pending(root: Path, conf: dict) -> dict:
    before=current_owner(root,conf)
    conditions=[
        f'mod("{conf["owner"]}") = "{before["mod_revision"]}"',
        f'version("{conf["intent"]}") = "0"',
    ]
    commands=[f'put "{conf["intent"]}" "{PROVIDER_MARK}"']
    script="\n".join(conditions)+"\n\n"+"\n".join(commands)+"\n\n\n"
    response=ctl(root,conf,"txn",stdin=script)
    need(response.get("succeeded") is True,
         "REAL_PROVIDER_ATOMIC_INTENT_FENCE_REFUSED")
    intent=read_key(root,conf,conf["intent"])
    need(intent is not None
         and intent["value"]==PROVIDER_MARK
         and intent["lease"]==0,
         "UNLEASED_PROVIDER_INTENT_NOT_DURABLE")
    return intent


def real_provider_effect_gate(root: Path) -> None:
    # This function is invoked synchronously IN THE ONLY PRIVILEGED LOCAL
    # Git sink UID62001 process, at actual native Git update-ref boundary.
    cfg=root/"sink"/PROVIDER_CONF
    conf=config_check(json.loads(cfg.read_text()))
    need(os.geteuid()==cp076.SINK_UID, "SINK_OS_ID_NOT_PROVEN")
    need(sha256(Path(conf["etcdctl"]))==PINNED_CTL,
         "SINK_PRIVATE_ETCDCTL_BINARY_PIN_BAD")
    pending=durable_pending(root,conf)
    if root.name=="expired":
        # Deliberately expire genuine short TTL while the unleased intent
        # exists. Never issue native local Git after provider key disappears.
        time.sleep(3.2)
    elif root.name=="revoked":
        notify=root/"endpoint"/"cp077-before-effect"
        continue_file=root/"endpoint"/"cp077-root-revocation-complete"
        notify.write_text("DURABLE_PENDING_BEFORE_EFFECT\n")
        until=time.monotonic()+10
        while not continue_file.exists() and time.monotonic()<until:
            time.sleep(0.03)
        need(continue_file.is_file(),
             "ROOT_REVOCATION_HANDSHAKE_FAILED_CLOSED")
    # Provider check and Git effect are TWO separate stores; a revocation
    # between this read and native update-ref remains an unfenced race.
    current_owner(root,conf)
    again=read_key(root,conf,conf["intent"])
    need(again is not None and again["lease"]==0
         and again["value"]==PROVIDER_MARK
         and again["mod_revision"]==pending["mod_revision"],
         "PROVIDER_PENDING_INTENT_CHANGED")
    if root.name=="late-revoked":
        # EXPLICIT TOCTOU RED WITNESS in the disposable LOCAL Git only.
        # The root controller removes the real owner AFTER the final etcd
        # check, before the native Git ref-update call. This MUST NOT be
        # represented as a production-safe effect fence.
        marker=root/"endpoint"/"cp077-after-last-provider-read"
        resumed=root/"endpoint"/"cp077-revoke-finished-after-read"
        marker.write_text("FINAL_ETCD_OWNER_AND_INTENT_READ_PASSED\n")
        deadline=time.monotonic()+9
        while not resumed.exists() and time.monotonic()<deadline:
            time.sleep(0.02)
        need(resumed.is_file(),"POSTCHECK_ROOT_REVOCATION_BARRIER_MISSING")
    # Returning control to the original native Git call immediately below.


def guarded_git(root: Path,*args: str,
                input_bytes:bytes | None=None,
                allow_failure:bool=False) -> str | None:
    if len(args)==4 and args[0]=="update-ref" and args[1]==cp076.REF:
        need(not allow_failure,"NO_FAILURE_TOLERANCE_FOR_REAL_LOCAL_REF_EFFECT")
        real_provider_effect_gate(root)
    return ORIGINAL_GIT(root,*args,input_bytes=input_bytes,
                        allow_failure=allow_failure)


def serve(arg: str) -> None:
    # Reuse the EXACT SHA-pinned CP076 signature/peercred/SQLite/Git server;
    # extend ONLY its last irreversible local Git effect with provider check.
    need(os.geteuid()==cp076.SINK_UID,"PROVIDER_SINK_NOT_UID62001")
    cp076.git=guarded_git
    cp076.serve(arg)


def configure_roles(provider: identity.AuthenticatedEtcd,
                    owner: str, intent: str) -> None:
    # Unlike CP074's prefix-readwrite fixture, ONLY root may mutate owner;
    # sink gets READ owner + readwrite own durable intent, worker READ owner.
    e=provider
    for args in [
        ("user","add","root","--no-password"),
        ("role","add","root"),
        ("user","grant-role","root","root"),
        ("role","add","cp077-sink"),
        ("role","grant-permission","cp077-sink","read",owner),
        ("role","grant-permission","cp077-sink","readwrite",intent),
        ("user","add","vf604-sink","--no-password"),
        ("user","grant-role","vf604-sink","cp077-sink"),
        ("role","add","cp077-worker"),
        ("role","grant-permission","cp077-worker","read",owner),
        ("user","add","vf604-worker","--no-password"),
        ("user","grant-role","vf604-worker","cp077-worker"),
        ("auth","enable"),
    ]:
        e.ctl_ok("root",*args)


def copy_for_sink(root: Path, e:identity.AuthenticatedEtcd,
                  ctl_binary:Path,owner:str,intent:str,lease:int,
                  owner_modrev:int)->None:
    out=root/"sink"/"tls"
    out.mkdir(mode=0o700)
    os.chown(out,cp076.SINK_UID,cp076.SINK_UID)
    mapping={
        "etcdctl":ctl_binary,
        "ca.crt":e.cert.ca,
        "sink.crt":e.cert.roles["sink"][0],
        "sink.key":e.cert.roles["sink"][1],
    }
    for name,source in mapping.items():
        target=out/name
        shutil.copyfile(source,target)
        os.chown(target,cp076.SINK_UID,cp076.SINK_UID)
        target.chmod(0o700 if name=="etcdctl" else 0o600)
    need(sha256(out/"etcdctl")==PINNED_CTL,"PRIVATE_CTL_BINARY_NOT_EXACT")
    conf={
        "schema":SCHEMA,
        "owner":owner,"intent":intent,"owner_value":fixed_owner_value(),
        "owner_modrev":owner_modrev,"lease":lease,"endpoint":e.url,
        "etcdctl":str(out/"etcdctl"),
        "etcdctl_sha":PINNED_CTL,
        "cacert":str(out/"ca.crt"),
        "cert":str(out/"sink.crt"),
        "key":str(out/"sink.key"),
    }
    config_check(conf)
    target=root/"sink"/PROVIDER_CONF
    target.write_text(json.dumps(conf,sort_keys=True)+"\n")
    os.chown(target,cp076.SINK_UID,cp076.SINK_UID)
    target.chmod(0o600)


def start_sink(root: Path)->tuple[subprocess.Popen,str]:
    def drop():
        os.setgroups([])
        os.setgid(cp076.SINK_UID)
        os.setuid(cp076.SINK_UID)
    p=subprocess.Popen(
        ["/usr/bin/python3","-B",os.path.realpath(__file__),
         "_serve",str(root)],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
        preexec_fn=drop,env=cp076.ENV)
    import select
    wait,_,_=select.select([p.stdout],[],[],9)
    if not wait:
        p.terminate();p.wait(timeout=3)
        raise cp076.Refuse("SINK_PROVIDER_READINESS_TIMEOUT")
    out=p.stdout.readline().strip()
    if not out.startswith("READY "):
        p.kill();p.wait(timeout=3)
        raise cp076.Refuse("SINK_PROVIDER_NOT_READY_"+out[:110])
    need(cp076.is_sha(out[6:]),"INITIAL_LOCAL_REF_SHA_INVALID")
    return p,out[6:]


def exercise_case(root:Path,scenario:str,e:identity.AuthenticatedEtcd,
                  ctl_binary:Path,checks:list[str]) ->None:
    def ck(name:str, condition:bool)->None:
        need(condition is True,"CP077_REAL_CHECK_FAILED_"+name)
        checks.append(name)
        print("CP077_NATIVE_"+name,flush=True)
    dir=root/scenario
    dir.mkdir(mode=0o755)
    dir.chmod(0o755)
    cp076.create_roles(dir)
    prefix=PREFIX+uuid.uuid4().hex+"/"
    owner=prefix+"owner"
    intent=prefix+"intent"
    configure_roles(e,owner,intent)
    ttl=2 if scenario=="expired" else 90
    lease_data=json.loads(e.ctl_ok("root","lease","grant",str(ttl)))
    lease=int(lease_data["ID"])
    need(lease>0,"REAL_ROOT_ISSUED_LEASE_MISSING")
    e.ctl_ok("root","put",owner,fixed_owner_value(),
             "--lease="+format(lease,"x"))
    row=e.cli_range("root",owner)
    need(row is not None and row["lease"]==lease and row["value"]==fixed_owner_value(),
         "REAL_LEASE_OWNER_PROOF_FAILED")
    copy_for_sink(dir,e,ctl_binary,owner,intent,lease,row["mod_revision"])
    ck(scenario+"_root_owned_live_etcd_ttl_lease",
       row["lease"]==lease and row["mod_revision"]>0)
    identity.assert_cli_denied(e,"worker","put",owner,"worker-forgery")
    identity.assert_cli_denied(e,"sink","put",owner,"sink-forgery")
    identity.assert_cli_denied(e,"worker","get",intent)
    ck(scenario+"_real_etcd_mtls_sink_cannot_mutate_owner",True)
    ck(scenario+"_worker_cert_only_reads_exact_owner",
       e.cli_range("worker",owner)["value"]==fixed_owner_value())
    identity.assert_cli_denied(e,"outsider","get",owner)
    ck(scenario+"_unknown_CN_certificate_denied_by_RBAC",True)
    ck(scenario+"_no_credential_or_git_access_by_worker",
       all(cp076.probe_dac(dir,cp076.WORKER_UID)[k] for k in
           ("signer_private_key_denied","fake_sink_token_denied",
            "sink_git_head_denied","direct_git_write_denied")))
    for actor,who in ((cp076.WORKER_UID,"worker"),
                      (cp076.SIGNER_UID,"signer")):
        probe_code=("import sys\ntry:open(sys.argv[1], 'rb').close()\n"
                    "except PermissionError:sys.exit(13)\n"
                    "except OSError:sys.exit(14)\nsys.exit(0)\n")
        probe=cp076.run_cmd(["/usr/bin/python3","-B","-c",probe_code,
                  str(dir/"sink"/"tls"/"sink.key")],
                  uid=actor,check=False,timeout=5)
        ck(scenario+"_"+who+"_cannot_read_private_sink_mTLS_key",
           probe.returncode==13)
    sink,initial=start_sink(dir)
    try:
        body=cp076.claim(initial,expires_utc_ms=int(time.time()*1000)+60000)
        signed={"action":"effect","claim":body,
                "signature":cp076.signed_message(dir,body)}
        if scenario in ("revoked","late-revoked"):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future=executor.submit(cp076.os_request,dir,
                                       cp076.WORKER_UID,signed)
                until=time.monotonic()+8
                notified=(dir/"endpoint"/(
                    "cp077-after-last-provider-read" if scenario=="late-revoked"
                    else "cp077-before-effect"))
                while not notified.exists() and time.monotonic()<until:
                    time.sleep(0.03)
                need(notified.is_file(),
                     "SINK_NOT_STOPPED_BEFORE_EFFECT_REVOCATION")
                pre=e.cli_range("root",intent)
                ck("revoked_real_durable_intent_before_revocation",
                   pre is not None and pre["value"]==PROVIDER_MARK
                   and pre["lease"]==0)
                e.ctl_ok("root","del",owner)
                resume=(dir/"endpoint"/(
                    "cp077-revoke-finished-after-read"
                    if scenario=="late-revoked"
                    else "cp077-root-revocation-complete"))
                resume.write_text("PROVIDER_OWNER_REVOKED\n")
                denied=future.result(timeout=10)
            ck(scenario+"_root_revoked_owner_before_native_Git",
               e.cli_range("root",owner) is None)
        else:
            denied=cp076.os_request(dir,cp076.WORKER_UID,signed)
        pending=e.cli_range("root",intent)
        ck(scenario+"_provider_pending_unleased_survives",
           pending is not None and pending["value"]==PROVIDER_MARK
           and pending["lease"]==0)
        snap=cp076.request(dir,{"action":"snapshot"}) if sink.poll() is None else None
        if scenario=="normal":
            ck("normal_valid_crypto_kernel_uid_provider_allows_one_local_git",
               denied["status"]=="ONE_LOCAL_REF_EFFECT_VERIFIED"
               and snap["head"]!=initial and snap["state"]["effects"]==1)
            # Root test controller independently reconciles the provider
            # with exact live owner+pending modrev after source Git readback.
            txn=e.cli_txn("root",[
                f'mod("{owner}") = "{row["mod_revision"]}"',
                f'mod("{intent}") = "{pending["mod_revision"]}"',
            ],[f'put "{intent}" "VERIFIED_LOCAL_ONLY"'])
            ck("normal_exact_root_provider_intent_reconciled",
               txn is True and e.cli_range("root",intent)["value"]=="VERIFIED_LOCAL_ONLY")
            replay=cp076.os_request(dir,cp076.WORKER_UID,signed)
            ck("normal_replay_valid_signature_denied_after_effect",
               replay["status"]=="DENIED"
               and cp076.request(dir,{"action":"snapshot"})["head"]==snap["head"])
        elif scenario=="late-revoked":
            # This is a deliberate security FAILURE witness:
            # the store cannot atomically fence the Git ref after
            # a previously successful provider check.
            ck("late_revocation_after_last_read_still_allows_stale_local_Git",
               denied["status"]=="ONE_LOCAL_REF_EFFECT_VERIFIED"
               and snap["head"]!=initial and snap["state"]["effects"]==1
               and e.cli_range("root",owner) is None)
            ck("late_revocation_leaves_provider_pending_UNRECONCILED",
               pending["lease"]==0
               and e.cli_range("root",intent)["value"]==PROVIDER_MARK)
            ck("late_revocation_test_never_authorizes_remote_sink",
               len(cp076.ENV)>0 and cp076.REF.endswith("-local-only"))
        elif scenario in ("expired","revoked"):
            ck(scenario+"_no_git_effect_after_live_provider_denial",
               denied["status"]=="DENIED"
               and ("LIVE_PROVIDER_OWNER" in denied["reason"])
               and snap["head"]==initial
               and snap["state"]["phase"]=="EFFECT_IN_FLIGHT")
            ck(scenario+"_provider_owner_absent_after_cutoff",
               e.cli_range("root",owner) is None)
            reject_new=e.cli_txn("root",[
                f'version("{owner}") = "0"',
                f'version("{intent}") = "0"',
            ],[f'put "{owner}" "epoch8-forged"'])
            ck(scenario+"_new_owner_cannot_bypass_pending_UNKNOWN",
               reject_new is False)
        elif scenario=="after":
            sink.wait(timeout=8)
            ck("after_true_sink_crash_after_local_git_before_ACK",
               sink.returncode==72 and denied["status"]=="NO_ACK_UNKNOWN")
            sink,again=start_sink(dir)
            freeze=cp076.request(dir,{"action":"snapshot"})
            ck("after_recovered_SQLite_UNKNOWN_without_replaying",
               freeze["state"]["phase"]=="FROZEN_UNKNOWN"
               and freeze["head"]==freeze["state"]["candidate"]
               and freeze["head"]!=initial)
            againreq=cp076.os_request(dir,cp076.WORKER_UID,signed)
            ck("after_valid_signature_cannot_replay_in_UNKNOWN",
               againreq["status"]=="DENIED"
               and cp076.request(dir,{"action":"snapshot"})["head"]==freeze["head"])
            ck("after_provider_pending_durable_when_ACK_lost",
               e.cli_range("root",intent)["value"]==PROVIDER_MARK)
        else:raise cp076.Refuse("UNAUTHORIZED_SCENARIO")
    finally:
        cp076.close_sink(dir,sink)


def native(etcd_path:str,ctl_path:str)->dict:
    need(sys.platform=="linux" and platform.machine()=="aarch64"
         and os.geteuid()==0 and os.getenv(ENV_KEY)==ENV_VAL,
         "REFUSE_NON_DISPOSABLE_ROOT_LINUX_GUEST")
    need(Path("/run/containerd/containerd.sock").is_socket(),
         "EXPECTED_EXISTING_COLIMA_DISPOSABLE_GUEST_NOT_PROVEN")
    need(not any(os.environ.get(x) for x in
         ("GITHUB_TOKEN","GH_TOKEN","SSH_AUTH_SOCK","GIT_ASKPASS")),
         "REFUSE_REAL_CREDENTIAL_ENV")
    dependencies()
    import pwd
    for uid in (cp076.SIGNER_UID,cp076.SINK_UID,
                cp076.WORKER_UID,cp076.ATTACKER_UID):
        try:pwd.getpwuid(uid)
        except KeyError:continue
        raise cp076.Refuse("REFUSE_OCCUPIED_PRODUCTION_OS_UID")
    etcd=Path(etcd_path).resolve(strict=True)
    ctlbin=Path(ctl_path).resolve(strict=True)
    need(sha256(etcd)==PINNED_ETCD and sha256(ctlbin)==PINNED_CTL,
         "PINNED_OFFICIAL_ETCD_3_6_15_LINUX_BINARY_REQUIRED")
    identity.PINNED_ETCD=PINNED_ETCD
    identity.PINNED_CTL=PINNED_CTL
    checks=[]
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix=ROOT_PREFIX,dir="/tmp") as temp:
        owned=Path(temp)
        owned.chmod(0o755)
        for scenario in ("normal","revoked","expired","after","late-revoked"):
            # AuthenticatedEtcd is a fresh, real, independently rooted mTLS
            # provider per scenario. Each server and WAL is disposed after.
            p=owned/(scenario+"-provider")
            p.mkdir(mode=0o700)
            e=identity.AuthenticatedEtcd(p,etcd,ctlbin)
            try:
                e.start()
                exercise_case(owned,scenario,e,ctlbin,checks)
            finally:
                e.stop()
    need(len(checks)>=25 and all(isinstance(x,str) for x in checks),
         "CP077_LIVE_ACTUAL_CONTROLS_INCOMPLETE")
    return {"schema":SCHEMA,"status":"PASS_CP077_LIVE_MTLS_LEASE_OSUID_GIT_LAB",
        "real_controls_passed":len(checks),
        "real_controls_expected_minimum":25,
        "fixed_synthetic_host":cp076.HOST,
        "three_real_distinct_linux_uids":True,
        "real_ed25519_signatures":True,"real_so_peercred":True,
        "real_mtls_etcd_certificate_CN_rbac":True,
        "real_etcd_ttl_expiry_and_owner_revocation":True,
        "real_unleased_durable_pending_intent":True,
        "native_local_git_CAS_once":True,
        "post_git_before_ack_crash_UNKNOWN":True,
        "provider_to_git_atomicity_proven":False,
        "deliberate_postcheck_revocation_stale_local_git_effect_reproduced":True,
        "provider_is_canonical_core604":False,
        "os_privileged_root_trust_separate_host_proven":False,
        "provider_time_remote_git_effect_fenced":False,
        "credentialed_github_git_sink":False,
        "github_writes":0,"model_source_executed":False,
        "new_os_accounts":0,"new_schedulers":0,
        "production_authority":False,
        "source_sha256":sha256(Path(__file__)),
        "etcd_binary_sha256":PINNED_ETCD,
        "etcdctl_binary_sha256":PINNED_CTL}


def main(argv:list[str])->dict:
    need(len(argv)>=2,"MODE_REQUIRED")
    if argv[1]=="selftest" and len(argv)==2:return selftest()
    if argv[1]=="native" and len(argv)==4:return native(argv[2],argv[3])
    if argv[1]=="_serve" and len(argv)==3:
        serve(argv[2]);return {"status":"SINK_CLOSED"}
    raise cp076.Refuse("NO_UNSCOPED_CP077_MODE")


if __name__=="__main__":
    try:
        data=main(sys.argv)
        if sys.argv[1] in ("native","selftest"):
            print(json.dumps(data,sort_keys=True),flush=True)
        raise SystemExit(0)
    except (cp076.Refuse,OSError,ValueError,TypeError,KeyError,
            RuntimeError,subprocess.SubprocessError,AssertionError) as ex:
        print(json.dumps({"status":"FAIL_CLOSED",
                          "reason":type(ex).__name__+":"+str(ex)[:175],
                          "model_source_executed":False,
                          "github_writes":0,"production_authority":False},
                         sort_keys=True),flush=True)
        raise SystemExit(2)
