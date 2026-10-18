#!/usr/bin/env python3
"""#604 manual LAB: real TLS/RBAC etcd owner+pending epoch Git cutover.

One provider owner key. A future production protocol requires stronger sink
authorization and liveness semantics; this lab NEVER claims atomicity across
etcd and GitHub. Selftest has no live external operations.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

SLUG="p0-epoch604-etcd-github-cutover-20261010"
ROOT=next((p for p in Path(__file__).resolve().parents if p.name==SLUG),None)
PREFIX="/velvet-office2/lab604/epoch-github-20261010"
KEY=PREFIX+"/owner"
REF="refs/heads/office-v2-lab-604-epoch-cutover-20261010"
MAIN="04ba7ae09d8c4197fd02afe496e15aad755af3cb"
PHASES=("seed","unsafe_expired","cutover","stale_denied","fresh_new","cleanup")
FIXTURES={
 "seed":("old","ACTIVE"),
 "unsafe_expired":("old","EXPIRED"),
 "cutover":("new","PENDING_CUTOVER"),
 "stale_denied":("old","STALE_DENIAL_EXPECTED"),
 "fresh_new":("new","ACTIVE"),
 "cleanup":("new","ACTIVE"),
}

class Refuse(Exception):pass

def need(ok,message):
    if not ok:raise Refuse(message)

def encoded(obj):
    return base64.b64encode(json.dumps(obj,sort_keys=True,
           separators=(",",":")).encode()).decode()

def decoded(data):
    return json.loads(base64.b64decode(data,validate=True))

def run_etcd(*args,txn=None):
    need(ROOT is not None and ROOT.name==SLUG,"WRONG_LAB_ROOT")
    base=[str(ROOT/"runtime/bin/etcdctl"),
          "--endpoints=https://127.0.0.1:32779",
          "--cacert="+str(ROOT/"private/ca.crt"),
          "--cert="+str(ROOT/"private/controller.crt"),
          "--key="+str(ROOT/"private/controller.key"),
          "--write-out=json"]
    try:
        p=subprocess.run(base+list(args),input=txn,text=True,
                         capture_output=True,timeout=12)
    except (OSError,subprocess.TimeoutExpired):raise Refuse("PROVIDER_UNKNOWN")
    need(p.returncode==0,"PROVIDER_DENIED_UNAVAILABLE_OR_UNKNOWN")
    try:return json.loads(p.stdout)
    except ValueError:raise Refuse("PROVIDER_INVALID_RESPONSE")

def owner():
    result=run_etcd("get",KEY)
    need(type(result.get("header")) is dict and
         type(result["header"].get("revision")) is int,
         "MISSING_PROVIDER_REVISION")
    rows=result.get("kvs",[])
    need(type(rows) is list and len(rows)<=1,"INVALID_PROVIDER_KEY_SET")
    if not rows:return None,int(result["header"]["revision"])
    data=rows[0]
    value=base64.b64decode(data["value"],validate=True).decode()
    info=decoded(value)
    create=int(data["create_revision"])
    need(info.get("actor") in ("old","new") and
         info.get("state") in ("ACTIVE","PENDING_CUTOVER") and
         info.get("generation")==create and
         int(data.get("lease",0))>0 and
         info.get("schema")=="vf604.real-provider-owner.v1",
         "OWNER_GENERATION_OR_VALUE_UNVERIFIED")
    return {"actor":info["actor"],"generation":create,
            "state":info["state"],"encoded_value":value,
            "mod_revision":int(data["mod_revision"]),
            "lease_id":int(data["lease"])},int(result["header"]["revision"])

def transaction(compares,ops):
    need(compares and ops and all("\n" not in x and '"' not in x[3:]
         for x in ops),"UNSAFE_TRANSACTION_COMMAND")
    request="\n".join(compares)+"\n\n"+"\n".join(ops)+"\n\n\n"
    result=run_etcd("txn",txn=request)
    need(type(result.get("succeeded")) is bool and
         type((result.get("header") or {}).get("revision")) is int,
         "UNVERIFIED_PROVIDER_TXN")
    return result

def claim(actor,ttl):
    need(actor in ("old","new"),"INVALID_CLAIMANT")
    need(type(ttl) is int and 6<=ttl<=360,"TTL_OUT_OF_BOUNDS")
    existing,_=owner()
    need(existing is None,"ACTIVE_OWNER_EXISTS")
    granted=run_etcd("lease","grant",str(ttl))
    lease=int(granted["ID"])
    need(lease>0 and int(granted["TTL"])>=6,"BAD_PROVIDER_LEASE")
    # create revision is provider-chosen generation. Value cannot know
    # creation revision before atomic put, so this initial placeholder is
    # verified then replaced with same lease in one compare-and-swap.
    pending={"schema":"vf604.real-provider-owner.v1",
             "actor":actor,"generation":0,
             "state":"ACTIVE" if actor=="old" else "PENDING_CUTOVER"}
    value=encoded(pending)
    request=transaction(
        ['version("'+KEY+'") = "0"'],
        ["put "+KEY+" "+value+" --lease="+format(lease,"x")])
    if not request["succeeded"]:
        try:run_etcd("lease","revoke",format(lease,"x"))
        except Refuse:pass
        raise Refuse("OTHER_OWNER_ALREADY_GRANTED")
    snapshot=run_etcd("get",KEY)
    rows=snapshot.get("kvs",[])
    need(len(rows)==1,"CLAIM_MISSING_AFTER_COMMIT")
    generation=int(rows[0]["create_revision"])
    need(int(rows[0]["lease"])==lease and
         int(rows[0]["mod_revision"])==generation,
         "CLAIM_LEASE_OR_REVISION_MISMATCH")
    pending["generation"]=generation
    tagged=encoded(pending)
    changed=transaction(
        ['mod("'+KEY+'") = "'+str(generation)+'"',
         'value("'+KEY+'") = "'+value+'"'],
        ["put "+KEY+" "+tagged+" --lease="+format(lease,"x")])
    need(changed["succeeded"],"OWNER_TAGGING_UNKNOWN_OUTCOME")
    current,_=owner()
    need(current is not None and current["generation"]==generation
         and current["actor"]==actor and
         current["state"]==pending["state"],"OWNER_TAG_NOT_CONFIRMED")
    record={"actor":actor,"generation":generation,
            "lease_id":lease,"state":current["state"],
            "ttl":ttl,"evidence_kind":"LIVE_PROVIDER_TXN_CREATED"}
    f=ROOT/"runtime/evidence"/(actor+"-owner.json")
    with f.open("x") as out:json.dump(record,out,indent=2,sort_keys=True)
    print(json.dumps({"status":"REAL_ETCD_LEASE_OWNER_CLAIM",
                      "actor":actor,"generation":generation,
                      "ttl":ttl,"state":current["state"]},sort_keys=True))

def read():
    current,rev=owner()
    print(json.dumps({"status":"REAL_PROVIDER_READ",
                      "owner":{k:v for k,v in current.items()
                          if k not in ("encoded_value","lease_id")}
                          if current else None,
                      "revision":rev},sort_keys=True))

def git_head():
    cmd=["git","-C",str(ROOT/"source"),"ls-remote",
         "--heads","origin",REF]
    try:
        p=subprocess.run(cmd,text=True,capture_output=True,timeout=12)
    except (OSError,subprocess.TimeoutExpired):raise Refuse("GITHUB_READ_UNKNOWN")
    need(p.returncode==0,"REMOTE_GITHUB_READ_DENIED")
    items=p.stdout.strip().splitlines()
    need(len(items)<=1,"AMBIGUOUS_GIT_REF")
    if not items:return ""
    fields=items[0].split()
    need(len(fields)==2 and fields[1]==REF and
         bool(re.fullmatch("[0-9a-f]{40}",fields[0])),
         "GITHUB_REF_NOT_EXACT")
    return fields[0]

def activate(marker):
    need(bool(re.fullmatch("[0-9a-f]{40}",marker or "")),
         "CUTOVER_MARKER_SHA_REQUIRED")
    current,_=owner()
    need(current is not None and current["actor"]=="new"
         and current["state"]=="PENDING_CUTOVER",
         "ONLY_PENDING_NEW_OWNER_ACTIVATABLE")
    need(git_head()==marker,"GITHUB_CUTOVER_MARKER_NOT_CURRENT")
    # Verify actual remote Git commit message embeds the provider epoch.
    check=subprocess.run(["git","-C",str(ROOT/"source"),"fetch",
                          "--quiet","--no-tags","origin",REF],
                         text=True,capture_output=True,timeout=25)
    need(check.returncode==0,"CUTOVER_MARKER_FETCH_UNVERIFIED")
    desc=subprocess.run(["git","-C",str(ROOT/"source"),
                         "show","-s","--format=%B",marker],
                        text=True,capture_output=True,timeout=8)
    need(desc.returncode==0 and
         "VF604_EPOCH_MARKER_NEW_GENERATION="+str(current["generation"])
         in desc.stdout and
         "VF604_ONLY_SYNTHETIC_GIT_SCRATCH_LAB" in desc.stdout,
         "CUTOVER_MARKER_DOES_NOT_BIND_PROVIDER_GENERATION")
    before=decoded(current["encoded_value"])
    tagged=dict(before,state="ACTIVE")
    done=transaction(
        ['mod("'+KEY+'") = "'+str(current["mod_revision"])+'"',
         'value("'+KEY+'") = "'+current["encoded_value"]+'"'],
        ["put "+KEY+" "+encoded(tagged)+" --lease="+format(current["lease_id"],"x")])
    need(done["succeeded"],"ACTIVATION_CAS_DENIED_OR_UNKNOWN")
    fresh,_=owner()
    need(fresh is not None and fresh["state"]=="ACTIVE"
         and fresh["generation"]==current["generation"],
         "ACTIVATION_NOT_CONFIRMED")
    f=ROOT/"runtime/evidence/activation.json"
    with f.open("x") as out:
        json.dump({"owner_generation":fresh["generation"],
                   "marker_sha":marker,"prior_state":"PENDING_CUTOVER",
                   "active_state":"ACTIVE"},out,sort_keys=True,indent=2)
    print(json.dumps({"status":"NEW_OWNER_ACTIVATED_ONLY_AFTER_GIT_MARKER",
                      "generation":fresh["generation"],"git_ref_sha":marker,
                      "etcd_revision":done["header"]["revision"]},sort_keys=True))

def revoke():
    current,_=owner()
    need(current is not None and current["actor"]=="new",
         "ONLY_EXACT_NEW_OWNER_REVOKE")
    run_etcd("lease","revoke",format(current["lease_id"],"x"))
    later,_=owner()
    need(later is None,"REVOKE_NOT_CONFIRMED")
    print(json.dumps({"status":"LAB_NEW_LEASE_REVOKED",
                      "generation":current["generation"]}))

def issue(phase,expected):
    need(phase in PHASES,"PHASE_NOT_ALLOWED")
    need(type(expected) is str and
         (expected=="" if phase=="seed"
          else bool(re.fullmatch("[0-9a-f]{40}",expected))),
         "EXPECTED_GITHUB_SHA_MISSING")
    actual=git_head()
    old_rec=json.loads((ROOT/"runtime/evidence/old-owner.json").read_text())
    old_gen=old_rec["generation"]
    owner_rec,revision=owner()
    new_rec=(ROOT/"runtime/evidence/new-owner.json")
    new_gen=json.loads(new_rec.read_text())["generation"] if new_rec.exists() else None
    if phase=="seed":
        need(owner_rec is not None and owner_rec["actor"]=="old" and
             owner_rec["state"]=="ACTIVE" and
             owner_rec["generation"]==old_gen and actual=="",
             "UNVERIFIED_OLD_PROVIDER_OWNER_OR_ABSENT_REF")
        gen=old_gen
        condition="LIVE_OLD_LEASE_ACTIVE"
    elif phase=="unsafe_expired":
        need(owner_rec is None and actual==expected,
             "UNSAFE_DIAGNOSTIC_REQUIRES_ACTUALLY_EXPIRED_PROVIDER_LEASE")
        gen=old_gen
        condition="EXPIRED_OWNER_NO_AUTHORITATIVE_PROVIDER_LEASE"
    elif phase=="cutover":
        need(owner_rec is not None and owner_rec["actor"]=="new" and
             owner_rec["state"]=="PENDING_CUTOVER" and
             owner_rec["generation"]==new_gen and
             actual==expected,"NO_PENDING_OWNER_OR_CURRENT_GIT_SHA")
        gen=new_gen
        condition="PENDING_NEW_OWNER_NOT_YET_ADMITTED"
        path=ROOT/"runtime/evidence/old-tip-before-cutover.json"
        need(not path.exists(),"REFUSE_SECOND_CUTOVER")
        with path.open("x") as f:
            json.dump({"pre_cutover_sha":actual,
                       "new_generation":gen},f,sort_keys=True)
    elif phase=="stale_denied":
        old_tip=json.loads((ROOT/"runtime/evidence/old-tip-before-cutover.json").read_text())["pre_cutover_sha"]
        need(owner_rec is not None and owner_rec["actor"]=="new" and
             owner_rec["state"]=="ACTIVE" and
             owner_rec["generation"]==new_gen and
             expected==old_tip and actual!=old_tip,
             "STALE_DENIAL_ONLY_AFTER_VERIFIED_EPOCH_MARKER")
        gen=old_gen
        condition="STALE_OWNER_AFTER_NEW_EPOCH_ACTIVE"
    else:
        need(owner_rec is not None and owner_rec["actor"]=="new" and
             owner_rec["state"]=="ACTIVE" and
             owner_rec["generation"]==new_gen and
             actual==expected,"ONLY_VERIFIED_ACTIVE_NEW_OWNER_AND_GIT_REF")
        gen=new_gen
        condition="ACTIVE_NEW_EPOCH_WITH_CURRENT_GIT_REF"
    data={
        "schema":"vf604.epoch-github-mtls-fixture.v1",
        "repo":"nocturney/velvetos-core",
        "ref":REF,"base_sha":MAIN,
        "phase":phase,"expected_sha":expected,
        "generation":gen,"owner_actor":"old" if phase in
        ("seed","unsafe_expired","stale_denied") else "new",
        "provider_condition":condition,
        "provider_observed_revision":revision,
        "expected_result":"rejected_stale" if phase=="stale_denied"
            else "accepted",
        "production_authority":False,
    }
    file=ROOT/"runtime/fixtures"/(phase+".json")
    need(not file.exists(),"REFUSE_SECOND_FIXTURE_ISSUANCE")
    with file.open("x") as f:json.dump(data,f,indent=2,sort_keys=True)
    print(json.dumps({"status":"REAL_ETCD_PROVIDER_STATE_READ_MAC_FIXTURE_ISSUED",
                      "phase":phase,"generation":gen,
                      "provider_condition":condition,
                      "expected_sha":expected,
                      "actual_github_sha":actual,
                      "provider_revision":revision},sort_keys=True))

def selftest():
    tests=0
    need(KEY.startswith(PREFIX) and REF.startswith("refs/heads/office-v2-lab-604-"),"DRIFT");tests+=1
    for k in ("ACTIVE","PENDING_CUTOVER"):
        test={"schema":"vf604.real-provider-owner.v1","actor":"old",
              "state":k,"generation":1}
        need(decoded(encoded(test))==test,"ENCODING_ERROR");tests+=1
    for s in ("../main","refs/heads/main",""):
        need(s!=REF,"FORBIDDEN_REF");tests+=1
    return {"status":"PASS_OFFLINE","tests":tests,
            "provider_calls":0,"git_remote_calls":0,
            "git_effect_writes":0,"secret_files_read":0,
            "production_authority":False,
            "cross_store_atomicity":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("selftest","claim","read","activate","revoke","issue"))
    p.add_argument("--actor",choices=("old","new"))
    p.add_argument("--ttl",type=int,default=6)
    p.add_argument("--marker")
    p.add_argument("--phase",choices=PHASES)
    p.add_argument("--expected",default="")
    args=p.parse_args()
    if args.mode=="selftest":print(json.dumps(selftest(),sort_keys=True))
    else:
        need(ROOT is not None and ROOT.name==SLUG,"NO_LAB_ROOT")
        if args.mode=="claim":claim(args.actor,args.ttl)
        elif args.mode=="read":read()
        elif args.mode=="activate":activate(args.marker)
        elif args.mode=="issue":issue(args.phase,args.expected)
        else:revoke()

if __name__=="__main__":
    try:main()
    except (Refuse,TypeError,ValueError,OSError) as e:
        print(json.dumps({"result":"FAIL_CLOSED","reason":str(e)[:180],
                          "blind_retry":False},sort_keys=True))
        sys.exit(3)
