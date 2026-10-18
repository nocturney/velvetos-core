#!/usr/bin/env python3
"""Manual LAB: physical Windows sole native Git writer, Mac provider epoch probe.

This experiment deliberately proves that expected GitHub SHA CAS alone
ACCEPTS an expired worker if the ref is unchanged. Then it moves an
explicit GitHub epoch marker before activating a new etcd owner; stale
expected-SHA requests are then rejected. It is NOT globally atomic across
etcd and GitHub and must NEVER be deployed as production fencing.
Offline selftest has ZERO network, filesystem effect or credentials.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request

SLUG="p0-epoch604-etcd-github-cutover-20261010"
ROOT=next((p for p in Path(__file__).resolve().parents if p.name==SLUG),None)
BASE="04ba7ae09d8c4197fd02afe496e15aad755af3cb"
REF="refs/heads/office-v2-lab-604-epoch-cutover-20261010"
REPO="nocturney/velvetos-core"
REMOTE="https://github.com/nocturney/velvetos-core.git"
FIXTURE="https://192.168.0.217:32781"
PHASES=("seed","unsafe_expired","cutover","stale_denied","fresh_new","cleanup")
CONDITIONS={
 "seed":("old","LIVE_OLD_LEASE_ACTIVE","accepted"),
 "unsafe_expired":("old","EXPIRED_OWNER_NO_AUTHORITATIVE_PROVIDER_LEASE","accepted"),
 "cutover":("new","PENDING_NEW_OWNER_NOT_YET_ADMITTED","accepted"),
 "stale_denied":("old","STALE_OWNER_AFTER_NEW_EPOCH_ACTIVE","rejected_stale"),
 "fresh_new":("new","ACTIVE_NEW_EPOCH_WITH_CURRENT_GIT_REF","accepted"),
 "cleanup":("new","ACTIVE_NEW_EPOCH_WITH_CURRENT_GIT_REF","accepted"),
}
MESSAGES={
 "seed":"VF604_EPOCH_MARKER_OLD_GENERATION=",
 "unsafe_expired":"VF604_UNSAFE_EXPIRED_PROVIDER_GENERATION=",
 "cutover":"VF604_EPOCH_MARKER_NEW_GENERATION=",
 "stale_denied":"VF604_STALE_OLD_OWNER_GENERATION=",
 "fresh_new":"VF604_VALID_NEW_OWNER_GENERATION=",
}

class Refuse(Exception):pass
def need(ok,message):
 if not ok:raise Refuse(message)

def valid_fixture(phase,v):
 need(type(v) is dict and set(v)=={
      "schema","repo","ref","base_sha","phase","expected_sha",
      "generation","owner_actor","provider_condition",
      "provider_observed_revision","expected_result",
      "production_authority"},"INVALID_EXACT_GIT_SINK_INPUT")
 need(phase in PHASES and
      v["schema"]=="vf604.epoch-github-mtls-fixture.v1" and
      v["repo"]==REPO and v["ref"]==REF and v["base_sha"]==BASE and
      v["phase"]==phase and v["production_authority"] is False,
      "UNTRUSTED_REPO_REF_OR_AUTHORITY")
 need(type(v["generation"]) is int and
      0<v["generation"]<10**11 and
      type(v["provider_observed_revision"]) is int and
      v["provider_observed_revision"]>=v["generation"],
      "INVALID_PROVIDER_EPOCH_REPORTED")
 need((v["owner_actor"],v["provider_condition"],v["expected_result"])
      ==CONDITIONS[phase],"RECEIVER_NOT_AUTHORIZED_FOR_OWNER_STATE")
 old=v["expected_sha"]
 need(type(old) is str and
      (old=="" if phase=="seed"
       else bool(re.fullmatch("[0-9a-f]{40}",old))),
       "INVALID_EXACT_EXPECTED_SHA")
 return v

def git(args,*,commit=False,timeout=28):
 need(ROOT is not None and ROOT.name==SLUG and
      (ROOT/"repo/.git").is_dir(),"ONLY_ISOLATED_WINDOWS_REPO")
 env=os.environ.copy()
 env["GIT_TERMINAL_PROMPT"]="0"
 if commit:
  env.update({"GIT_AUTHOR_NAME":"VF604 synthetic epoch LAB",
     "GIT_AUTHOR_EMAIL":"vf604-epoch-lab@example.invalid",
     "GIT_COMMITTER_NAME":"VF604 synthetic epoch LAB",
     "GIT_COMMITTER_EMAIL":"vf604-epoch-lab@example.invalid",
     "GIT_AUTHOR_DATE":"2026-10-10T14:01:00+0000",
     "GIT_COMMITTER_DATE":"2026-10-10T14:01:00+0000"})
 try:
  return subprocess.run(["git","-C",str(ROOT/"repo")]+list(args),
          env=env,capture_output=True,text=True,timeout=timeout)
 except (OSError,subprocess.TimeoutExpired):
  raise Refuse("GIT_EFFECT_OR_CHECK_OUTCOME_UNKNOWN")

def git_read(*args):
 r=git(args)
 need(r.returncode==0,"GIT_READ_NOT_VERIFIED")
 return r.stdout.strip()

def remote_ref():
 r=git(("ls-remote","--heads","origin",REF),timeout=18)
 need(r.returncode==0,"LIVE_GITHUB_REF_READ_UNAVAILABLE")
 items=r.stdout.strip().splitlines()
 need(len(items)<=1,"UNEXPECTED_MULTIPLE_REMOTE_HEADS")
 if not items:return ""
 a=items[0].split()
 need(len(a)==2 and a[1]==REF and
      bool(re.fullmatch("[0-9a-f]{40}",a[0])),
      "REMOTE_GITHUB_RETURNED_WRONG_REF")
 return a[0]

def precheck(phase):
 need(phase in PHASES and ROOT is not None and ROOT.name==SLUG,
      "ONLY_MANUAL_ALLOWLISTED_LAB_PHASE")
 need(git_read("remote","get-url","origin")==REMOTE
      and git_read("rev-parse","HEAD")==BASE
      and git_read("status","--porcelain")=="",
      "WINDOWS_SINK_UNEXPECTED_REPO_OR_DIRTY_CHECKOUT")
 receipts=ROOT/"runtime/receipts"
 receipts.mkdir(parents=True,exist_ok=True)
 need(not (receipts/(phase+".json")).exists(),
      "LIVE_GIT_PHASE_ALREADY_SUBMITTED_NO_BLIND_RETRY")

def request(phase):
 root=ROOT/"runtime/tls"
 need(root.is_dir() and all((root/f).is_file() and
      not (root/f).is_symlink() and
      500<(root/f).stat().st_size<8000
      for f in ("ca.crt","win.crt","win.key")),
      "EPHEMERAL_CLIENT_CERT_REQUIRED")
 ctx=ssl.create_default_context(cafile=str(root/"ca.crt"))
 ctx.minimum_version=ssl.TLSVersion.TLSv1_2
 ctx.load_cert_chain(str(root/"win.crt"),str(root/"win.key"))
 opener=urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.ProxyHandler({}))
 req=urllib.request.Request(FIXTURE+"/v1/fixture/"+phase,method="GET")
 try:
  with opener.open(req,timeout=9) as response:
   raw=response.read(2400)
   need(response.status==200 and 80<len(raw)<2200,
        "MAC_EPOCH_FIXTURE_BODY_NOT_AUTHORITATIVE")
   obj=json.loads(raw)
 except (urllib.error.URLError,urllib.error.HTTPError,
         ssl.SSLError,TimeoutError,ValueError,OSError):
  raise Refuse("MAC_PROVIDER_OBSERVED_FIXTURE_UNAVAILABLE_FAIL_CLOSED")
 return valid_fixture(phase,obj),hashlib.sha256(raw).hexdigest()

def commit(phase,expected,gen):
 tree=git_read("rev-parse",BASE+"^{tree}")
 need(bool(re.fullmatch("[0-9a-f]{40}",tree)),
      "UNKNOWN_GIT_TREE")
 parent=BASE if phase=="seed" else expected
 need(bool(re.fullmatch("[0-9a-f]{40}",parent)),
      "BAD_PARENT_SHA")
 message=MESSAGES[phase]+str(gen)+"\nVF604_ONLY_SYNTHETIC_GIT_SCRATCH_LAB\n"
 c=git(("commit-tree",tree,"-p",parent,"-m",message),commit=True)
 need(c.returncode==0 and
      bool(re.fullmatch("[0-9a-f]{40}",c.stdout.strip())),
      "CANNOT_BUILD_EXACT_SYNTHETIC_EPOCH_COMMIT")
 return c.stdout.strip()

def execute(phase):
 precheck(phase)
 obj,request_sha=request(phase)
 expected=obj["expected_sha"]
 prior=remote_ref()
 candidate="" if phase=="cleanup" else commit(
                phase,expected,obj["generation"])
 git_operand=(":"+REF if phase=="cleanup" else candidate+":"+REF)
 # Native GitHub ref CAS is the only true external atomic primitive used.
 # No assumption that an etcd read and this push are one transaction.
 r=git(("push","--porcelain","--force-with-lease="+REF+":"+expected,
       "origin",git_operand),timeout=35)
 after=remote_ref()
 if phase=="stale_denied":
  need(r.returncode!=0 and prior!=expected and prior==after and
       "stale info" in (r.stdout+" "+r.stderr).lower(),
       "STALE_NATIVE_GIT_PUSH_NOT_PROVEN_DENIED")
  outcome="PASS_REAL_NATIVE_GIT_STALE_CAS_DENIED"
 else:
  need(r.returncode==0 and prior==expected and
       after==candidate,"REAL_NATIVE_GITHUB_EFFECT_UNKNOWN_OR_FAILED")
  outcome=("PASS_INTENTIONAL_UNSAFE_EXPIRED_OWNER_GIT_ACCEPTED"
           if phase=="unsafe_expired"
           else "PASS_REAL_GITHUB_EPOCH_REF_CAS")
 rec={"schema":"vf604.epoch-cutover-real-native-git-receipt.v1",
      "phase":phase,"status":outcome,
      "ref":REF,"repo":REPO,"base":BASE,
      "real_mtls_mac_fixture":True,
      "mac_provider_generation":obj["generation"],
      "provider_condition":obj["provider_condition"],
      "provider_observed_revision":obj["provider_observed_revision"],
      "mac_request_sha256":request_sha,
      "expected_ref_sha":expected,
      "before_ref_sha":prior,"after_ref_sha":after,
      "synthetic_candidate_commit":candidate,
      "native_git_push_exit":r.returncode,
      "sole_git_writer":"WIN_EXISTING_NATIVE_GITHUB_IDENTITY",
      "fully_atomic_etcd_github_fencing":False,
      "production_authority":False}
 f=ROOT/"runtime/receipts"/(phase+".json")
 with f.open("x") as out:
  json.dump(rec,out,sort_keys=True,indent=2)
 print(json.dumps({"status":outcome,"phase":phase,
                  "mac_provider_generation":obj["generation"],
                  "provider_condition":obj["provider_condition"],
                  "before":prior,"after":after,"candidate":candidate,
                  "native_push_exit":r.returncode,
                  "lease_git_cross_store_atomicity":False},sort_keys=True))

def selftest():
 n=0
 for phase,(actor,condition,result) in CONDITIONS.items():
  obj={"schema":"vf604.epoch-github-mtls-fixture.v1",
       "repo":REPO,"ref":REF,"base_sha":BASE,"phase":phase,
       "expected_sha":"" if phase=="seed" else "2"*40,
       "generation":3,"owner_actor":actor,
       "provider_condition":condition,"provider_observed_revision":10,
       "expected_result":result,"production_authority":False}
  valid_fixture(phase,obj);n+=1
  for key,value in (("repo","evil/fork"),("ref","refs/heads/main"),
                    ("base_sha","0"*40),("phase","../../"),
                    ("generation",False),("owner_actor","evil"),
                    ("provider_condition","PRODUCTION"),
                    ("expected_sha","notsha"),
                    ("expected_result","grant"),
                    ("production_authority",True)):
   invalid=dict(obj);invalid[key]=value
   try:valid_fixture(phase,invalid)
   except Refuse:n+=1
   else:raise AssertionError("UNSAFE_GIT_CLIENT_ALLOW_"+key)
 need(n==66,"NEGATIVE_COUNT_MISMATCH")
 return {"status":"PASS_OFFLINE","cases":n,
         "git_remote_writes":0,"git_remote_reads":0,
         "network_requests":0,"private_credentials_read":0,
         "production_authority":False,
         "two_native_host_git_writers":False,
         "etcd_github_global_atomicity":False}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("mode",choices=("selftest","run"))
 p.add_argument("--phase",choices=PHASES)
 a=p.parse_args()
 if a.mode=="selftest":print(json.dumps(selftest(),sort_keys=True))
 else:
  need(a.phase in PHASES,"MANUAL_PHASE_REQUIRED")
  execute(a.phase)

if __name__=="__main__":
 try:main()
 except (Refuse,OSError,TypeError,ValueError) as e:
  print(json.dumps({"result":"FAIL_CLOSED","reason":str(e)[:160],
                    "blind_retry":False},sort_keys=True))
  sys.exit(3)
