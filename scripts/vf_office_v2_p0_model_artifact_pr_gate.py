#!/usr/bin/env python3
"""#612: manually curated quarantined LOCAL-model source -> protected PR QA gate.

Offline and read-only except disposable temporary test copies; never launches
models, modifies task receipts, grants Git writer admission, or uses #604 lease.
The model-authored source is byte-exact pinned, inspected before isolated
subprocess evaluation and NEVER installed into production runtime.
"""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT = ROOT / "docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10"
EVIDENCE = ROOT / "docs/implementation/office-v2/phase2/p0-quarantined-agent-code-pr-2026-10-10.json"
SCHEMA = "velvetos.office-v2.p0-quarantined-agent-code-protected-pr.v0"
EXPECTED = {
    "canonical_tag": {
        "name": "canonical_tag.py",
        "func": "canonical_tag",
        "hash": "b2ec92fed514a5e0e37aeca31155fe0d04cdfde70a3d46fafeeb9a09b0ef1ccb",
        "task_id": "p0-diverse-run-mac-tag-state-v2-20261010-c",
        "raw_receipt": "c2f81cec7419219f942ec74524864a2159ca233759ba643e193cead7ed5087d5",
        "receipt_seal": "2bdb477dc94308e8a8c8d1dff63e5a68843a4d783946d0aaaf93b13c24629e9d",
        "base": "b078080a31fca74f622ed93bd2c58a7421a51536",
        "model": "qwen3.5:4b",
    },
    "windows_merge": {
        "name": "windows_merge.py",
        "func": "merge_windows",
        "hash": "999f8ae84cbca062a41297b6fadf6703ee69fa8a61e427a8441cd1a169c3b0a0",
        "task_id": "p0-diverse-run-mac-merge-guided-20261010-a",
        "raw_receipt": "f6dac1286bb1fad2ddb525ecf51d3fd86a9149d2a5cc8464f05c5569350cedda",
        "receipt_seal": "431c9d94ac939c794da794e84175964508e77125397e1fcc36a5a7fdc8862524",
        "base": "d081112707ad55ff9e848a380227223bc75dff63",
        "model": "qwen3.5:4b",
    },
}
MODEL_DIGEST = "7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13"
FORBIDDEN = (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal,
             ast.With, ast.AsyncWith, ast.AsyncFunctionDef,
             ast.Await, ast.Yield, ast.YieldFrom, ast.ClassDef)
ALLOWED_ATTRIBUTES = {"lower","append","pop","isalnum","join"}


class Refused(Exception):
    pass


def need(ok, why):
    if not ok:
        raise Refused(why)


def source_bytes(name, path=None):
    need(name in EXPECTED, "UNKNOWN_SOURCE_NAME")
    expected = EXPECTED[name]
    file = ARTIFACT / expected["name"] if path is None else Path(path)
    need(file.is_file() and not file.is_symlink() and file.stat().st_size < 5000,
         "QUARANTINED_SOURCE_REQUIRED")
    data = file.read_bytes()
    need(hashlib.sha256(data).hexdigest() == expected["hash"],
         "ORIGINAL_LOCAL_MODEL_SOURCE_BYTES_DRIFT")
    try:
        body = ast.parse(data.decode("utf-8"), filename=expected["name"])
    except (ValueError, UnicodeError, SyntaxError) as exc:
        raise Refused("MODEL_SOURCE_SYNTAX_INVALID") from exc
    need(len(body.body) == 1 and isinstance(body.body[0], ast.FunctionDef)
         and body.body[0].name == expected["func"]
         and not body.body[0].decorator_list
         and len(body.body[0].args.args) == 1,
         "UNEXPECTED_CODE_AT_MODULE_SCOPE")
    for node in ast.walk(body):
        need(not isinstance(node, FORBIDDEN), "MODEL_SOURCE_UNSAFE_AST")
        if isinstance(node, ast.Attribute):
            need(node.attr in ALLOWED_ATTRIBUTES, "MODEL_SOURCE_ATTRIBUTE_NOT_APPROVED")
        if isinstance(node, ast.Name):
            need(not node.id.startswith("__"), "MODEL_SOURCE_DUNDER_NOT_APPROVED")
    return data


# This subprocess runs the exact hash-pinned source in a scratch directory
# with restricted Python builtins. NOT an OS sandbox or malicious-code defense.
# Original withheld QA was kept outside this PR; these are independent new
# property tests, including int subclasses omitted by the original 12 hidden.
RUNNER = r'''
import builtins
import json
import random
import re
import sys
from pathlib import Path

kind = sys.argv[1]
source = Path(sys.argv[2]).read_text(encoding="utf-8")
safe = {k:getattr(builtins,k) for k in (
    "str","int","bool","tuple","list","ord","len","range","enumerate",
    "isinstance","sorted","max","ValueError")}
scope = {"__builtins__":safe, "__name__":"__quarantined_artifact__"}
exec(compile(source, "<exact-sha-pinned-model-source>", "exec"), scope)

if kind == "canonical_tag":
    target=scope["canonical_tag"]
    fixed=["", " ", "!!!", "A", "42", "A..B", "a___b",
           "A😀B", "áÜñ", "İ", "𝙰-𝙱", "_a_", "FOO BAR",
           "a\t...\nB", "X/Y/Z", "2026/10/10"]
    alphabet="aB09z-_.+/? !\n\téøΩİ😀Ж"
    rng=random.Random(61220261010)
    values=fixed+["".join(rng.choice(alphabet) for _ in range(rng.randrange(0,32)))
                  for _ in range(512)]
    wrong=[]
    for s in values:
        expected=re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "untitled"
        try:
            got=target(s)
        except Exception as exc:
            got="EXCEPTION_"+type(exc).__name__
        if got!=expected and len(wrong)<4:
            wrong.append({"input":repr(s),"expected":expected,"actual":str(got)})
    out={"source":"canonical_tag","samples":len(values),
         "all_public_oracle_cases_pass":len(wrong)==0,
         "counterexamples":wrong}
elif kind == "windows_merge":
    target=scope["merge_windows"]
    rng=random.Random(61220261011)
    passed=0
    for _ in range(256):
        rows=[]
        for i in range(rng.randrange(0,12)):
            lo=rng.randrange(-40,40)
            rows.append((lo,lo+rng.randrange(0,12)))
        rng.shuffle(rows)
        original=rows[:]
        expected=[]
        for lo,hi in sorted(rows):
            if expected and lo<=expected[-1][1]+1:
                expected[-1]=(expected[-1][0],max(expected[-1][1],hi))
            else:
                expected.append((lo,hi))
        try:
            actual=target(rows)
        except Exception:
            actual=None
        if actual==expected and rows==original:
            passed+=1
    invalid=[[(True,2)],[(1,False)],[(1,2.5)],[[1,2]],
             [(2,1)],[(1,)], [("1",2)],[(1,2,3)], [1]]
    reject=0
    for bad in invalid:
        try:
            target(bad)
        except ValueError:
            reject+=1
    class IntSubclass(int):
        pass
    try:
        result=target([(IntSubclass(1),2)])
    except ValueError:
        subclass_rejected=True
        returned=None
    else:
        subclass_rejected=False
        returned=str(result)
    out={"source":"windows_merge","standard_samples":256,
         "standard_oracle_passed":passed,
         "invalid_cases":len(invalid),"invalid_rejected":reject,
         "int_subclass_rejected":subclass_rejected,
         "int_subclass_actual_if_accepted":returned,
         "int_subclass_contract_expected":"ValueError"}
else:
    raise SystemExit(3)
print(json.dumps(out,sort_keys=True,ensure_ascii=True))
'''


def independent_qa():
    observed = {}
    for kind in EXPECTED:
        raw = source_bytes(kind)
        with tempfile.TemporaryDirectory(prefix="vf-office-v2-quarantine-") as t:
            scratch = Path(t) / EXPECTED[kind]["name"]
            scratch.write_bytes(raw)
            need(scratch.read_bytes() == raw, "TEMP_SOURCE_COPY_CHANGED")
            env = {k:os.environ[k] for k in ("PATH","SYSTEMROOT","WINDIR","TEMP","TMP",
                                              "TMPDIR") if k in os.environ}
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            try:
                proc = subprocess.run(
                    [sys.executable,"-I","-B","-c",RUNNER,kind,str(scratch)],
                    cwd=t,env=env,capture_output=True,timeout=13,text=True,
                    encoding="utf-8",errors="replace",
                )
            except (OSError,subprocess.TimeoutExpired):
                raise Refused("ISOLATED_OFFLINE_QA_TIMEOUT_OR_UNAVAILABLE")
            need(proc.returncode==0 and len(proc.stdout)<12000,
                 "INDEPENDENT_QA_CHILD_FAILED")
            try:
                observed[kind] = json.loads(proc.stdout)
            except ValueError:
                raise Refused("INDEPENDENT_QA_OUTPUT_CORRUPT")
    return observed


def proof_validate(v, observed):
    need(isinstance(v,dict) and v.get("schema")==SCHEMA
         and v.get("status")=="QUARANTINED_ONLY_ONE_EXPANDED_QA_CONTRACT_GAP"
         and v.get("issue")=="https://github.com/nocturney/velvetos-core/issues/612",
         "PROOF_SCHEMA_OR_SUCCESS_OVERCLAIM")
    need(v.get("source_host")=="MacMiniOffice.local"
         and v.get("model_digest")==MODEL_DIGEST
         and v.get("source_code_never_rewritten") is True,
         "MODEL_SOURCE_PROVENANCE_INVALID")
    entries=v.get("artifacts")
    need(isinstance(entries,dict) and set(entries)==set(EXPECTED),"ARTIFACT_SET_DRIFT")
    for name,spec in EXPECTED.items():
        item=entries[name]
        need(isinstance(item,dict)
             and item.get("task_id")==spec["task_id"]
             and item.get("git_seed_base_sha")==spec["base"]
             and item.get("model")==spec["model"]
             and item.get("model_source_sha256")==spec["hash"]
             and item.get("original_mac_receipt_raw_sha256")==spec["raw_receipt"]
             and item.get("original_worker_receipt_selfhash")==spec["receipt_seal"]
             and item.get("original_3_visible_and_12_hidden_qa")=="PASS"
             and item.get("quarantine_only") is True
             and item.get("model_authored_git_change_auto_pushed") is False,
             "MODEL_AUTHORSHIP_OR_ORIGINAL_QA_DRIFT_"+name)
    need(v.get("expanded_oracle") == observed,
         "EXPANDED_QA_OBSERVATION_NOT_REPRODUCIBLE")
    tag=observed["canonical_tag"]
    merge=observed["windows_merge"]
    need(tag["source"]=="canonical_tag"
         and tag["samples"]==528
         and tag["all_public_oracle_cases_pass"] is True
         and tag["counterexamples"]==[],
         "CANONICAL_TAG_EXPANDED_ORACLE_REGRESSED")
    need(merge["source"]=="windows_merge"
         and merge["standard_samples"]==256
         and merge["standard_oracle_passed"]==256
         and merge["invalid_cases"]==9
         and merge["invalid_rejected"]==9
         and merge["int_subclass_rejected"] is False
         and merge["int_subclass_actual_if_accepted"]=="[(1, 2)]"
         and merge["int_subclass_contract_expected"]=="ValueError",
         "MODEL_WINDOWS_EDGE_BUG_NOT_PINNED_OR_FALSE_PASS")
    require_false=("production_code_promoted","model_pr_created_autonomously",
                   "fleet_lease_proven","stale_fenced_git_effect_proven",
                   "distributed_recovery_proven","original_qa_results_overwritten",
                   "model_reexecuted_for_this_pr","paid_model_calls_for_this_pr",
                   "both_artifacts_expanded_qa_green","runtime_sandbox_proven")
    for k in require_false:
        need((v.get("limits") or {}).get(k) is False,
             "UNAUTHORIZED_CLAIM_"+k)
    need((v.get("limits") or {}).get("manual_protected_pr_with_pinned_code_only")
         is True, "PR_SCOPED_AUTHORITY_MISSING")
    return {"status":"PASS_QUARANTINED_ORIGINAL_MODEL_BYTES_AND_EXPANDED_QA",
            "artifact_count":2,
            "canonical_tag_expanded_pass":True,
            "windows_merge_expanded_contract_gap":True,
            "production_promoted":False,"automated_pr_or_fleet_lease":False,
            "model_calls_by_verifier":0}


def load_proof():
    need(EVIDENCE.is_file() and not EVIDENCE.is_symlink()
         and EVIDENCE.stat().st_size < 50000,"PINNED_PROOF_REQUIRED")
    try:
        return json.loads(EVIDENCE.read_text(encoding="utf-8"))
    except (OSError,ValueError):
        raise Refused("EVIDENCE_PARSE_FAILED")


def selftest(v, observed):
    proof_validate(v,observed)
    tested=["original_readback_and_real_independent_qa_positive"]
    negatives=[
        ("promoted_fake",lambda d:d.update(status="PRODUCTION_READY")),
        ("wrong_host",lambda d:d.update(source_host="Chris")),
        ("model_swapped",lambda d:d.update(model_digest="0"*64)),
        ("rewrite_false",lambda d:d.update(source_code_never_rewritten=False)),
        ("missing_source",lambda d:d["artifacts"].pop("windows_merge")),
        ("wrong_receipt",lambda d:d["artifacts"]["canonical_tag"].update(original_mac_receipt_raw_sha256="0"*64)),
        ("wrong_original_qa",lambda d:d["artifacts"]["windows_merge"].update(original_3_visible_and_12_hidden_qa="FAILED")),
        ("wrong_source",lambda d:d["artifacts"]["windows_merge"].update(model_source_sha256="0"*64)),
        ("fake_expanded_green",lambda d:d["expanded_oracle"]["windows_merge"].update(int_subclass_rejected=True)),
        ("hide_contract_gap",lambda d:d["expanded_oracle"]["windows_merge"].update(int_subclass_actual_if_accepted=None)),
        ("false_tag_fail",lambda d:d["expanded_oracle"]["canonical_tag"].update(all_public_oracle_cases_pass=False)),
        ("fake_property_count",lambda d:d["expanded_oracle"]["windows_merge"].update(standard_oracle_passed=300)),
        ("false_prod",lambda d:d["limits"].update(production_code_promoted=True)),
        ("false_fence",lambda d:d["limits"].update(stale_fenced_git_effect_proven=True)),
        ("false_model_calls",lambda d:d["limits"].update(model_reexecuted_for_this_pr=True)),
        ("false_autopr",lambda d:d["limits"].update(model_pr_created_autonomously=True)),
        ("false_sandbox",lambda d:d["limits"].update(runtime_sandbox_proven=True)),
        ("hide_manual_scope",lambda d:d["limits"].update(manual_protected_pr_with_pinned_code_only=False)),
    ]
    for label,mutation in negatives:
        fake=copy.deepcopy(v)
        mutation(fake)
        try:
            proof_validate(fake,observed)
        except Refused:
            tested.append(label+"_DENIED")
        else:
            raise AssertionError("FALSE_EVIDENCE_ACCEPTED_"+label)
    for name in EXPECTED:
        with tempfile.TemporaryDirectory(prefix="vf-office-v2-tamper-") as t:
            other=Path(t)/EXPECTED[name]["name"]
            other.write_bytes(source_bytes(name)+b"\n#changed\n")
            try:
                source_bytes(name,other)
            except Refused:
                tested.append(name+"_source_tamper_DENIED")
            else:
                raise AssertionError("MODIFIED_MODEL_SOURCE_ACCEPTED_"+name)
    need(len(tested)==21,"SELFTEST_EXPECTED_CASE_COUNT_DRIFT")
    return {"status":"PASS_OFFLINE","tests":len(tested),
            "model_calls":0,"external_git_effects":0,
            "production_code_promoted":False,
            "cross_host_fencing_proven":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=("probe","verify","selftest"))
    args=parser.parse_args()
    observed=independent_qa()
    if args.mode=="probe":
        result={"status":"OBSERVED_ACTUAL_QUARANTINED_LOCAL_MODEL_CODE",
                "expanded_oracle":observed,"model_calls":0,
                "production_authority":False}
    else:
        proof=load_proof()
        result=proof_validate(proof,observed) if args.mode=="verify" else selftest(proof,observed)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    try:
        main()
    except (Refused,AssertionError,OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:180],
                          "model_calls":0,"production_writes":0},sort_keys=True))
        raise SystemExit(2)
