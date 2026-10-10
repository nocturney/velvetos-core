#!/usr/bin/env python3
"""#604 real Mac-origin request -> Windows native GitHub scratch ref CAS.

Manually invoked, *no background daemon*. The isolated Windows git clone's
existing authenticated Git identity is the ONLY ref writer. Source Mac is a
read-only mTLS fixture server, NOT a native Mac Git writer or lease authority.
CI may run only selftest: zero network, Git, credentials or filesystem effects.
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

SLUG = "p0-github604-onewriter-macorigin-20261010"
BASE = "cc2cccb2770a79424741719795d552fa85d69a81"
REF = "refs/heads/office-v2-lab-604-mac-origin-cas-20261010"
REPO = "nocturney/velvetos-core"
REMOTE = "https://github.com/nocturney/velvetos-core.git"
SRC = "https://192.168.0.217:32683"
SCHEMA = "vf604.mac-origin-native-git-cas-request.v1"
PHASES = ("seed","effect_a","stale_b","fresh_b","stale_a","cleanup")
PHASE_CANDIDATE = dict(seed="seed", effect_a="a", stale_b="b",
                       fresh_b="b", stale_a="a", cleanup="none")
DENY_PHASES = ("stale_b", "stale_a")
ROOT = next((p for p in Path(__file__).resolve().parents
             if p.name == SLUG), None)


class FailClosed(Exception):
    pass


def need(ok, reason):
    if not ok:
        raise FailClosed(reason)


def valid_request(phase, obj):
    need(phase in PHASES and type(obj) is dict and
         set(obj)=={"schema","repo","ref","phase","expected_sha",
                    "candidate","expected_result","base_commit"},
         "UNEXPECTED_MAC_FIXTURE_KEYS")
    need(obj["schema"]==SCHEMA and obj["repo"]==REPO and
         obj["ref"]==REF and obj["phase"]==phase and
         obj["base_commit"]==BASE, "UNAUTHORIZED_REF_OR_REPO_OR_BASE")
    need(obj["candidate"]==PHASE_CANDIDATE[phase] and
         obj["expected_result"]==
         ("denied_stale" if phase in DENY_PHASES else "accepted"),
         "UNAUTHORIZED_NATIVE_GIT_OPERATION")
    old=obj["expected_sha"]
    need(type(old) is str and
         (old=="" if phase=="seed" else bool(re.fullmatch("[0-9a-f]{40}",old))),
         "REF_EXPECTED_SHA_NOT_EXACT")
    return obj


def git_call(words, *, commit_env=False, timeout=35):
    need(ROOT is not None and ROOT.name==SLUG, "REFUSE_WRONG_LAB")
    repo=ROOT/"repo"
    need((repo/".git").exists(), "MISSING_ISOLATED_WINDOWS_GIT_REPO")
    env=os.environ.copy()
    env["GIT_TERMINAL_PROMPT"]="0"
    if commit_env:
        env.update({"GIT_AUTHOR_NAME":"VF604 Synthetic Git CAS LAB",
                    "GIT_AUTHOR_EMAIL":"vf604-git-cas-lab@example.invalid",
                    "GIT_COMMITTER_NAME":"VF604 Synthetic Git CAS LAB",
                    "GIT_COMMITTER_EMAIL":"vf604-git-cas-lab@example.invalid",
                    "GIT_AUTHOR_DATE":"2026-10-10T13:50:00+0000",
                    "GIT_COMMITTER_DATE":"2026-10-10T13:50:00+0000"})
    try:
        return subprocess.run(["git","-C",str(repo)]+list(words),env=env,
                              capture_output=True,text=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired):
        raise FailClosed("NATIVE_GIT_OPERATION_UNKNOWN")


def git_ok(*words):
    result=git_call(words)
    need(result.returncode==0,"NATIVE_GIT_PRECHECK_FAILED")
    return result.stdout.strip()


def verify_local_git_clone():
    need(ROOT is not None and ROOT.name==SLUG and
         (ROOT/"runtime").is_dir(), "ONLY_NEW_WINDOWS_LAB_ALLOWED")
    need(git_ok("remote","get-url","origin")==REMOTE,
         "REFUSE_DIFFERENT_REMOTE_REPOSITORY")
    need(git_ok("rev-parse","HEAD")==BASE,
         "REFUSE_CLONE_ADVANCED_FROM_APPROVED_BASE")
    need(git_ok("status","--porcelain")=="", "REFUSE_DIRTY_GIT_CHECKOUT")


def native_remote_ref():
    result=git_call(("ls-remote","--heads","origin",REF), timeout=20)
    need(result.returncode==0,"GITHUB_REF_READBACK_UNKNOWN")
    items=result.stdout.strip().splitlines()
    need(len(items)<=1,"REMOTE_REF_NOT_UNIQUE")
    if not items:return ""
    fields=items[0].split()
    need(len(fields)==2 and fields[1]==REF and
         bool(re.fullmatch("[0-9a-f]{40}",fields[0])),
         "GITHUB_RETURNED_UNEXPECTED_REF")
    return fields[0]


def candidate_shas():
    tree=git_ok("rev-parse",BASE+"^{tree}")
    need(bool(re.fullmatch("[0-9a-f]{40}",tree)),"INVALID_PINNED_TREE")
    commits={}
    parent=BASE
    for ident,label in (
        ("seed","VF604_MAC_ORIGIN_CAS_SEED_20261010"),
        ("a","VF604_MAC_ORIGIN_REAL_NATIVE_GIT_EFFECT_A_20261010"),
        ("b","VF604_MAC_ORIGIN_REAL_NATIVE_GIT_EFFECT_B_20261010")):
        result=git_call(("commit-tree",tree,"-p",parent,"-m",label),
                        commit_env=True)
        need(result.returncode==0 and bool(re.fullmatch(
             "[0-9a-f]{40}",result.stdout.strip())),
             "LAB_COMMIT_OBJECT_COULD_NOT_BE_CREATED")
        commits[ident]=result.stdout.strip()
        parent=commits[ident]
    need(len(set(commits.values()))==3,
         "LAB_EFFECT_CANDIDATE_COMMITS_NOT_DISTINCT")
    return commits


def request_from_mac(phase):
    need(ROOT is not None and phase in PHASES,"INVALID_MAC_REQUEST_PHASE")
    root=ROOT/"runtime"/"tls"
    need(root.is_dir() and all((root/name).is_file() and
         500<=(root/name).stat().st_size<8000 for name in
         ("ca.crt","win.crt","win.key")), "ONLY_EPHEMERAL_MTLS_FILES")
    tls=ssl.create_default_context(cafile=str(root/"ca.crt"))
    tls.minimum_version=ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(str(root/"win.crt"),str(root/"win.key"))
    req=urllib.request.Request(SRC+"/v1/fixture/"+phase,
                               method="GET")
    op=urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=tls),
        urllib.request.ProxyHandler({}))
    try:
        with op.open(req, timeout=8) as response:
            raw=response.read(1500)
            need(response.status==200 and 80<len(raw)<1500,
                 "MAC_MTLS_REQUEST_NOT_AUTHORITATIVE")
            request=json.loads(raw)
    except (urllib.error.HTTPError,urllib.error.URLError,
            TimeoutError,ssl.SSLError,ValueError,OSError):
        raise FailClosed("MAC_MTLS_FIXTURE_UNAVAILABLE_OR_UNAUTHORIZED")
    return valid_request(phase,request),hashlib.sha256(raw).hexdigest()


def execute(phase):
    need(phase in PHASES, "ONLY_SIX_ALLOWLISTED_CAS_STAGES")
    verify_local_git_clone()
    fixture,digest=request_from_mac(phase)
    commits=candidate_shas()
    expected=fixture["expected_sha"]
    before=native_remote_ref()
    # Remote CAS is the authority. The readback above is evidence, NOT the
    # admission check and cannot replace GitHub's native expected-ref CAS.
    candidate=commits.get(fixture["candidate"])
    need((candidate is None)==(phase=="cleanup"), "UNEXPECTED_COMMIT_KIND")
    operand=(":"+REF if phase=="cleanup" else candidate+":"+REF)
    args=("push","--porcelain","--force-with-lease="+REF+":"+expected,
          "origin",operand)
    result=git_call(args,timeout=35)
    after=native_remote_ref()
    if phase in DENY_PHASES:
        need(result.returncode!=0 and
             "stale info" in (result.stdout+" "+result.stderr).lower() and
             after==before and before!=expected,
             "FAIL_CLOSED_STALE_CAS_PUSH_NOT_PROVEN_DENIED")
        status="PASS_REAL_GITHUB_REF_STALE_CAS_REJECTED"
    else:
        desired="" if phase=="cleanup" else candidate
        need(result.returncode==0 and after==desired,
             "FAIL_CLOSED_REAL_GITHUB_REF_EFFECT_NOT_READBACK")
        need(before==expected,"REF_CAS_ORIGINAL_BASE_DID_NOT_MATCH")
        status="PASS_REAL_GITHUB_REF_CAS_ACCEPTED"
    receipt={"schema":"vf604.mac-origin-win-native-git-cas-effect.v1",
             "phase":phase,"status":status,"repo":REPO,"ref":REF,
             "request_sha256":digest,"client_mtls":True,
             "sole_git_writer":"CHRIS_WINDOWS_NATIVE_AUTHENTICATED_GIT",
             "git_base":BASE,"provider_lease_integrated":False,
             "external_git_ref_cas_at_sink":True,
             "expected_sha":expected,"before":before,"after":after,
             "candidate_sha":candidate or "",
             "git_push_exit_code":result.returncode,
             "no_production_or_protected_main_writes":True,
             "no_codex_or_paid_model":True}
    receipts=ROOT/"runtime"/"receipts"
    receipts.mkdir(parents=True,exist_ok=True)
    f=receipts/(phase+".json")
    need(not f.exists(),"REFUSE_REPEATED_LIVE_GIT_STAGE")
    with f.open("x",encoding="utf-8") as fp:
        json.dump(receipt,fp,indent=2,sort_keys=True)
        fp.write("\n")
    # Safe stdout: no GitHub credentials, caller secrets or complete HTTPS
    # command/stderr that could contain helper diagnostics.
    print(json.dumps({"status":status,"phase":phase,
                      "expected_sha":expected,"before":before,"after":after,
                      "candidate_sha":candidate or "",
                      "git_push_exit_code":result.returncode,
                      "mac_mtls_request_read":True,
                      "sole_writer":"Windows Native Git",
                      "protected_main_untouched":True},
                     sort_keys=True),flush=True)
    return 0


def selftest():
    count=0
    for phase in PHASES:
        f={"schema":SCHEMA,"repo":REPO,"ref":REF,"phase":phase,
           "expected_sha":"" if phase=="seed" else "a"*40,
           "candidate":PHASE_CANDIDATE[phase],
           "expected_result":"denied_stale" if phase in DENY_PHASES
                            else "accepted",
           "base_commit":BASE}
        valid_request(phase,f)
        count+=1
        for key,bad in (
            ("repo","attacker/fork"),("ref","refs/heads/main"),
            ("phase","../seed"),("base_commit","0"*40),
            ("expected_sha","g"*40),("candidate","malicious"),
            ("expected_result","unchecked"),("new_field","unsafe")):
            v=dict(f);v[key]=bad
            try:valid_request(phase,v)
            except FailClosed:count+=1
            else:raise AssertionError("FALSE_ALLOW_"+phase+"_"+key)
    need(count==54,"WRONG_LOCAL_NEGATIVE_COUNT")
    return {"status":"PASS_OFFLINE","cases":count,
            "github_network_operations":0,"external_pushes":0,
            "model_calls":0,"client_secret_uses":0,
            "production_authority":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("selftest","run"))
    p.add_argument("--phase",choices=PHASES)
    args=p.parse_args()
    if args.mode=="selftest":
        print(json.dumps(selftest(),sort_keys=True))
    else:
        need(args.phase in PHASES, "MANUAL_PHASE_REQUIRED")
        execute(args.phase)


if __name__=="__main__":
    try:main()
    except (FailClosed,ValueError,TypeError,KeyError,OSError) as err:
        print(json.dumps({"result":"FAIL_CLOSED","reason":str(err)[:170],
                          "blind_retry":False}),flush=True)
        sys.exit(3)
