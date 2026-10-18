#!/usr/bin/env python3
"""#612 P0 exact-two-new-Qwen-output hosted QA, not arbitrary-code admission.

selftest = read-only source SHA and AST policy checks; never executes outputs.
run = only on credential-free GitHub-hosted PR, inside pinned nonroot/no-network
Docker guests, using existing #685 inspect, negative probes and independent QA.
No local Windows SYSTEM/Mac user executes candidate model Python.
"""
from __future__ import annotations
import ast
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
import vf_office_v2_p0_diverse_task_fixtures as fixtures

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "velvetos.office-v2.p0-two-host-new-source-docker-qa.v0"
SOURCE_CASES = (
    {"label":"chris-win9b-new-merge-20261011",
     "fixture":"merge-windows-v1",
     "source":"docs/implementation/office-v2/phase2/quarantined-new-model-sources-2026-10-11/windows-qwen9b-merge-20261011.py.txt",
     "sha256":"65bf260ac6f29c74337e0bea3c1079f7b0203cd9b1a0eade1b96569e19557bc1",
     "expected_good":True,"host":"Chris","model":"qwen3.5:9b"},
    {"label":"mac4b-new-tag-20261011",
     "fixture":"canonical-tag-v1",
     "source":"docs/implementation/office-v2/phase2/quarantined-new-model-sources-2026-10-11/mac-qwen4b-tag-20261011.py.txt",
     "sha256":"337c6c159f5de53d3628a213a815b835a830ed72ee1b97e915f29ed609540677",
     "expected_good":False,"host":"MacMiniOffice.local","model":"qwen3.5:4b"},
)
ALLOWED_CALLS = frozenset(("type","len","isinstance","range","sorted","max",
                           "enumerate","ValueError"))
ALLOWED_METHODS = frozenset(("append","join","strip","lower",
                             "isascii","isalnum","isdigit"))
class Refused(Exception):
    pass
def require(ok,reason):
    if not ok: raise Refused(reason)
def sha(data):
    return hashlib.sha256(data).hexdigest()

def reviewed_structure(source, target):
    require(type(source) is bytes and len(source)<16384,
            "CODE_SOURCE_SIZE_REFUSED")
    try: tree=ast.parse(source.decode("utf-8"),filename="quarantined-source")
    except (SyntaxError,UnicodeDecodeError,ValueError) as exc:
        raise Refused("GENERATED_PYTHON_UNPARSEABLE") from exc
    expected="merge_windows" if target=="windows_merge.py" else "canonical_tag"
    require(len(tree.body)==1 and isinstance(tree.body[0],ast.FunctionDef)
            and tree.body[0].name==expected,"UNAPPROVED_TOP_LEVEL_SOURCE")
    for node in ast.walk(tree):
        require(not isinstance(node,(ast.ClassDef,ast.AsyncFunctionDef,
                  ast.ImportFrom,ast.Global,ast.Nonlocal,
                  ast.Await,ast.Yield,ast.YieldFrom,ast.With,ast.AsyncWith,
                  ast.Try,ast.TryStar)), "DISALLOWED_DYNAMIC_SOURCE_NODE")
        if isinstance(node,ast.Import):
            require(len(node.names)==1 and node.names[0].name=="re"
                    and node.names[0].asname is None,"UNAPPROVED_MODULE_IMPORT")
        if isinstance(node,ast.FunctionDef):
            require(node is tree.body[0], "NESTED_FUNCTION_NOT_REVIEWED")
        if isinstance(node,ast.Name):
            require(not node.id.startswith("__"),"DUNDER_NAME_DENIED")
        if isinstance(node,ast.Attribute):
            require(node.attr in ALLOWED_METHODS,"UNAPPROVED_ATTRIBUTE_CALL")
        if isinstance(node,ast.Call):
            callee=node.func
            if isinstance(callee,ast.Name):
                require(callee.id in ALLOWED_CALLS,"UNAPPROVED_DYNAMIC_CALL")
            else:
                require(isinstance(callee,ast.Attribute)
                        and callee.attr in ALLOWED_METHODS,
                        "DYNAMIC_CALL_TARGET_REFUSED")
    return True

def source_case(item):
    require(item in SOURCE_CASES and type(item) is dict,"UNREGISTERED_SOURCE")
    row=fixtures.catalog()[item["fixture"]]
    path=ROOT/item["source"]
    require(path.is_file() and not path.is_symlink(),"SOURCE_FILE_MISSING_OR_ALIAS")
    data=path.read_bytes()
    require(sha(data)==item["sha256"],"GENERATED_SOURCE_HASH_CHANGED")
    reviewed_structure(data,row["target"])
    entry={"label":item["label"],"fixture":item["fixture"],
           "sha256":item["sha256"],"expected_good":item["expected_good"],
           "test_sha256":sha(row["visible"].encode()),
           "hidden_sha256":sha(row["hidden"].encode())}
    return entry,data,row

def selftest():
    checks=[]
    for item in SOURCE_CASES:
        _,data,row=source_case(item)
        checks.append("exact_pinned_"+item["label"])
        require(reviewed_structure(data,row["target"]),"STATIC_AST_NOT_ADMITTED")
        checks.append("bounded_ast_"+item["label"])
    source=SOURCE_CASES[0]
    for mutation in ({"sha256":"0"*64},{"expected_good":False},
                     {"source":SOURCE_CASES[1]["source"]},
                     {"fixture":"canonical-tag-v1"},
                     {"label":"forged"},{"host":"other"}):
        wrong=dict(source,**mutation)
        try: source_case(wrong)
        except (Refused,KeyError): checks.append("registration_spoof_denied")
        else: raise Refused("MUTATED_SOURCE_FALSE_ADMITTED")
    for malicious in (
        b"import os\ndef merge_windows(windows):\n return []\n",
        b"def merge_windows(windows):\n eval('1+1')\n",
        b"def merge_windows(windows):\n open('/tmp/secret')\n",
        b"def merge_windows(windows):\n __import__('os')\n",
        b"def merge_windows(windows):\n return windows.__class__\n",
        b"class merge_windows:\n pass\n",
        b"def merge_windows(windows):\n from os import system\n",
        b"def merge_windows(windows):\n return os.system('id')\n",
    ):
        try: reviewed_structure(malicious,"windows_merge.py")
        except Refused: checks.append("untrusted_ast_denied")
        else: raise Refused("UNREVIEWED_DYNAMIC_AST_ACCEPTED")
    entry,_,_=source_case(SOURCE_CASES[0])
    img="sha256:"+"a"*64
    base=Path(tempfile.gettempdir()).resolve()
    root=base/"vf-new-p0-fixture-not-created"
    canary=base/"vf-new-p0-canary-not-created"/"secret.txt"
    args=prior.docker_args(img,root,canary,entry)
    prior.assert_docker_plan(args,img,root,canary,entry)
    checks.append("exact_docker_plan")
    for old,new in (("--network=none","--network=host"),
                    ("--read-only","--privileged"),
                    ("--cap-drop=ALL","--cap-add=SYS_ADMIN"),
                    ("--user=65534:65534","--user=0:0"),
                    ("--ipc=none","--ipc=host")):
        broken=list(args)
        broken[broken.index(old)]=new
        try: prior.assert_docker_plan(broken,img,root,canary,entry)
        except prior.Refused: checks.append("unsafe_guest_flag_denied")
        else: raise Refused("UNSAFE_CONTAINER_CONFIG_ADMITTED")
    return {"schema":SCHEMA,"status":"PASS_STATIC_NEW_MODEL_OUTPUT_NO_HOST_EXECUTION",
            "tests":len(checks),"two_sources_pinned":True,
            "source_sha256":[s["sha256"] for s in SOURCE_CASES],
            "generated_candidate_executed":False,
            "model_calls":0,"docker_calls":0,"git_writes":0,
            "production_authority":False,
            "arbitrary_generated_code_isolation_proven":False}

def run():
    # The only runner allowed to execute these two SHA-locked inspected sources
    # is a new public GitHub-hosted PR Linux job with no checkout credentials.
    prior.hosted.runner_context_check(os.environ)
    prior.hosted.no_persisted_checkout_auth()
    require(os.environ.get("RUNNER_OS")=="Linux"
            and os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted"
            and os.environ.get("GITHUB_EVENT_NAME")=="pull_request"
            and os.environ.get("GITHUB_RUN_ID","").isdigit(),
            "HOSTED_NO_WRITE_PR_ONLY")
    started=time.monotonic()
    prior.docker_command(["docker","version","--format","{{.Server.Version}}"],
                         timeout=12)
    image_ref=prior.EXPECTED_IMAGE_DIGEST
    require(image_ref.startswith("python@sha256:"),"OCI_DIGEST_NOT_PINNED")
    prior.docker_command(["docker","pull","--quiet",image_ref],timeout=125)
    img=json.loads(prior.docker_command(
        ["docker","image","inspect",image_ref],timeout=12))[0]
    image_id=img["Id"]
    require(image_ref in img["RepoDigests"] and
            image_id.startswith("sha256:") and
            prior.SHA256.fullmatch(image_id[7:]),
            "IMMUTABLE_OCI_IMAGE_CHANGED")
    results=[]
    for item in SOURCE_CASES:
        entry,source,row=source_case(item)
        with tempfile.TemporaryDirectory(prefix="vf-p0-fresh-model-") as tmp, \
             tempfile.TemporaryDirectory(prefix="vf-p0-separate-canary-") as excluded:
            wd=Path(tmp)
            secret=Path(excluded)/"host-only-synthetic-canary.key"
            secret.write_text("NOT_A_REAL_SECRET",encoding="ascii")
            target=wd/row["target"]
            target.write_bytes(source)
            visible=wd/row["test"]
            visible.parent.mkdir(parents=True)
            visible.write_text(row["visible"],encoding="utf-8")
            (wd/"hidden.py").write_text(row["hidden"],encoding="utf-8")
            (wd/"qa_inner.py").write_text(prior.INNER,encoding="utf-8")
            for p in (target,visible,wd/"hidden.py",wd/"qa_inner.py"):
                p.chmod(0o644)
            (wd/"tests").chmod(0o755)
            wd.chmod(0o755)
            argv=prior.docker_args(image_id,wd,secret,entry)
            prior.assert_docker_plan(argv,image_id,wd,secret,entry)
            cid=None
            try:
                cid=prior.docker_command(argv,timeout=18)
                require(prior.DOCKER_ID.fullmatch(cid),"UNOWNED_CONTAINER_ID")
                cfg=prior.inspect_cid(cid,wd,image_id)
                reply=prior.docker_command(["docker","start","--attach",cid],
                                          timeout=38)
                state=json.loads(prior.docker_command(
                    ["docker","inspect",cid],timeout=12))[0]["State"]
                require(state["Status"]=="exited" and state["ExitCode"]==0,
                        "CONTAINER_NOT_DONE")
                records=[json.loads(t) for t in reply.splitlines()
                         if t.startswith("{") and t.endswith("}")]
                require(len(records)==1
                        and records[0].get("status")=="PASS_CONTAINER_ISOLATION_NEGATIVES_AND_QA"
                        and records[0].get("source_sha256")==entry["sha256"]
                        and records[0].get("visible_3") is item["expected_good"]
                        and records[0].get("hidden_12") is item["expected_good"]
                        and records[0].get("network_denied") is True
                        and records[0].get("host_canary_invisible") is True
                        and records[0].get("no_exported_github_token") is True
                        and records[0].get("setuid_root_denied") is True,
                        "INDEPENDENT_QA_OR_CONTAINER_NEGATIVES_MISMATCH")
                results.append({"label":item["label"],"host":item["host"],
                        "model":item["model"],"sha256":item["sha256"],
                        "visible_3":records[0]["visible_3"],
                        "hidden_12":records[0]["hidden_12"],
                        "negative":not item["expected_good"],
                        "docker_inspection":cfg,"credential_scope":"NONE"})
            finally:
                if cid is not None and prior.DOCKER_ID.fullmatch(cid):
                    prior.docker_command(["docker","rm","--force",cid],timeout=14)
    return {"schema":SCHEMA,
            "status":"PASS_ONE_NEW_SOURCE_QA_AND_ONE_NEW_SOURCE_REJECTED",
            "github_run_id":os.environ["GITHUB_RUN_ID"],
            "exact_new_source_samples":2,
            "reviewed_generated_sources":2,
            "new_model_calls_during_hosted_qa":0,
            "new_model_source_executed_locally":False,
            "hosted_OCI_image":image_ref,
            "results":results,
            "one_new_algorithm_QA_pass":True,
            "one_new_algorithm_QA_fail":True,
            "no_production_or_writer_authority":True,
            "no_local_worker_unblock":True,
            "kernel_escape_resistance_proven":False,
            "general_unknown_generated_code_admission":False,
            "exclusive_git_sink_proven":False,
            "automated_agent_pr_proven":False,
            "paid_api_usd":0,
            "elapsed_seconds":round(time.monotonic()-started,3)}
def main():
    require(len(sys.argv)==2 and sys.argv[1] in ("selftest","run"),
            "EXPECTED_SELFTEST_OR_RUN")
    result=selftest() if sys.argv[1]=="selftest" else run()
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    try: main()
    except (Refused,prior.Refused,prior.hosted.Refused,ValueError,
            TypeError,KeyError,AssertionError,OSError,
            subprocess.TimeoutExpired) as err:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(err)[:185],
                          "local_generated_code_executed":False,
                          "production_authority":False},sort_keys=True))
        raise SystemExit(2)
