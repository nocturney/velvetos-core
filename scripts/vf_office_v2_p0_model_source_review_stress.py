#!/usr/bin/env python3
"""Office #612: review-only bridge from real pinned model bytes to candidate diff.

Historical Worker evidence is immutable. The observed source is quarantined;
this verifier neither grants Git/production authority nor edits any checkout.
It runs a NEW independent metamorphic public-spec QA in a scratch subprocess.
The restricted Python builtins are NOT an OS sandbox.
"""
from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import vf_office_v2_p0_exact_int_model_qa_gate as original
from vf_office_v2_p0_diverse_task_fixtures import INTERVAL_SOURCE

SOURCE_TARGET = "windows_merge.py"
TASK_ID = "p0-diverse-run-mac-merge-exact-int-20261010-d"
BASE_SHA = "d89317730bc9ff5fac95bd064fea710847e1c404"
SCHEMA = "velvetos.office-v2.p0-model-review-only-candidate.v0"
SEEDS = (61220261012, 61220261013, 61220261014, 61220261015)

# The source in this fixture is a known SHA-pinned model output, not arbitrary
# uploaded code. Re-evaluation is strictly limited to this exact source.
STRESS_RUNNER = r'''
import builtins
import json
import random
import sys
from pathlib import Path

raw = Path(sys.argv[1]).read_bytes()
safe = {k:getattr(builtins,k) for k in
        ("list","tuple","int","bool","str","len","type","range",
         "sorted","max","enumerate","isinstance","ValueError")}
ns = {"__builtins__":safe, "__name__":"__pinned_review_only__"}
exec(compile(raw,"<sha-pinned-review-only>","exec"),ns)
merge = ns["merge_windows"]
seeds = (61220261012,61220261013,61220261014,61220261015)
counts = {"ordinary_oracle":0,"permutation":0,"idempotence":0,
          "translation":0,"discrete_coverage":0}
for seed in seeds:
    rng = random.Random(seed)
    for i in range(128):
        rows = []
        for _ in range(rng.randrange(0,14)):
            lo = rng.randrange(-40,40)
            rows.append((lo,lo+rng.randrange(0,11)))
        snapshot = rows[:]
        expected = []
        for lo,hi in sorted(rows):
            if expected and lo<=expected[-1][1]+1:
                expected[-1] = (expected[-1][0],max(expected[-1][1],hi))
            else:
                expected.append((lo,hi))
        got = merge(rows)
        assert got == expected and rows == snapshot and got is not rows
        counts["ordinary_oracle"] += 1
        shuffled = rows[:]
        rng.shuffle(shuffled)
        assert merge(shuffled) == got
        counts["permutation"] += 1
        assert merge(got) == got
        counts["idempotence"] += 1
        offset = rng.randrange(-1000,1000)
        shifted = [(a+offset,b+offset) for a,b in rows]
        assert merge(shifted) == [(a+offset,b+offset) for a,b in got]
        counts["translation"] += 1
        original_coverage = {x for a,b in rows for x in range(a,b+1)}
        resulting_coverage = {x for a,b in got for x in range(a,b+1)}
        assert original_coverage == resulting_coverage
        counts["discrete_coverage"] += 1
big = 10**80
assert merge([(big+3,big+8),(big,big+2),(-big,-big)]) == [
    (-big,-big),(big,big+8)]
print(json.dumps({"seeds":len(seeds),"samples":512,"counts":counts,
                  "very_large_exact_ints":True,"model_calls":0},
                 sort_keys=True))
'''


class Refused(Exception):
    pass


def need(condition: bool, message: str) -> None:
    if not condition:
        raise Refused(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_and_evidence():
    raw = original.verify_source()
    need(sha(raw) == original.SOURCE_SHA, "MODEL_SOURCE_PIN_DRIFT")
    observed = original.observed_qa()
    proof = original.load_proof()
    original.validate(proof, observed)
    worker = proof["new_original_worker"]
    need(worker["task_id"] == TASK_ID and worker["base_sha"] == BASE_SHA,
         "MODEL_TASK_LINEAGE_WRONG")
    return raw, observed, proof


def run_stress(raw: bytes) -> dict:
    with tempfile.TemporaryDirectory(prefix="office-v2-review-stress-") as t:
        path = Path(t) / SOURCE_TARGET
        path.write_bytes(raw)
        need(path.read_bytes() == raw, "SCRATCH_COPY_SOURCE_DRIFT")
        env = {k:os.environ[k] for k in
               ("PATH","SYSTEMROOT","WINDIR","TMP","TEMP","TMPDIR")
               if k in os.environ}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            result = subprocess.run(
                [sys.executable,"-I","-B","-c",STRESS_RUNNER,str(path)],
                cwd=t,env=env,capture_output=True,timeout=25,
                text=True,encoding="utf-8",errors="replace")
        except (OSError,subprocess.TimeoutExpired) as exc:
            raise Refused("STRESS_SUBPROCESS_UNAVAILABLE") from exc
        need(result.returncode == 0 and len(result.stdout) < 2000,
             "MODEL_SOURCE_STRESS_FAILED")
        try:
            result_obj = json.loads(result.stdout)
        except ValueError as exc:
            raise Refused("STRESS_OUTPUT_NOT_JSON") from exc
    expected = {name:512 for name in
                ("ordinary_oracle","permutation","idempotence",
                 "translation","discrete_coverage")}
    need(result_obj == {"seeds":4,"samples":512,"counts":expected,
                        "very_large_exact_ints":True,"model_calls":0},
         "STRESS_COUNTERS_NOT_EXACT")
    return result_obj


def patch_for_review(raw: bytes) -> str:
    # Reconstructed against the public fixture, NOT asserted to be a byte-
    # exact historical agent worktree diff. Original model bytes are unchanged.
    text = raw.decode("utf-8")
    return "".join(difflib.unified_diff(
        INTERVAL_SOURCE.splitlines(keepends=True),
        text.splitlines(keepends=True),
        fromfile="a/" + SOURCE_TARGET,
        tofile="b/" + SOURCE_TARGET))


def make_bundle(raw: bytes, qa: dict, proof: dict, stress: dict) -> dict:
    patch = patch_for_review(raw)
    need(patch.startswith("--- a/windows_merge.py\n+++ b/windows_merge.py\n")
         and len(patch.encode()) < 10000, "REVIEW_PATCH_SCOPE_INVALID")
    worker = proof["new_original_worker"]
    return {
        "schema": SCHEMA,
        "status": "OFFLINE_CANDIDATE_REVIEW_ONLY_NOT_PR_AUTHORIZED",
        "issue": "https://github.com/nocturney/velvetos-core/issues/612",
        "task_id": TASK_ID,
        "historical_task_git_base": BASE_SHA,
        "review_diff_base": "PUBLIC_FIXTURE_SEED_RECONSTRUCTION_NOT_HISTORY",
        "model_source_sha256": sha(raw),
        "public_fixture_seed_sha256": sha(INTERVAL_SOURCE.encode("utf-8")),
        "unified_review_diff_sha256": sha(patch.encode("utf-8")),
        "review_target_allowlist": [SOURCE_TARGET],
        "model_source_original_receipt_sha256": worker["receipt_raw_sha256"],
        "source_authored_by": "LOCAL_QWEN_MODEL",
        "git_commit_and_pr_authored_by": "NONE_THIS_PROOF",
        "required_review": "SEPARATE_OPERATOR_REVIEW_AND_PROTECTED_CI",
        "stress": stress,
        "previous_public_qa": {
            "standard_oracle_passed": qa["new_independent_properties"]["standard_oracle_passed"],
            "invalid_rejected": qa["new_independent_properties"]["invalid_rejected"],
        },
        "limits": {
            "quarantined_source_not_edited": True,
            "source_promoted_to_production": False,
            "agent_autonomous_pr_created": False,
            "git_effects_this_run": 0,
            "model_calls_this_run": 0,
            "provider_lease_or_fence_proven": False,
            "secure_os_sandbox_proven": False,
            "authorization_to_commit_or_merge": False,
        },
    }


def verify_bundle(bundle: dict, expected: dict) -> None:
    need(type(bundle) is dict and bundle == expected,
         "REVIEW_BUNDLE_UNPINNED_OR_FALSE_AUTHORITY")
    limits = bundle["limits"]
    need(limits["authorization_to_commit_or_merge"] is False
         and limits["agent_autonomous_pr_created"] is False
         and limits["git_effects_this_run"] == 0
         and bundle["review_target_allowlist"] == [SOURCE_TARGET],
         "REVIEW_WOULD_CROSS_EFFECT_BOUNDARY")


def selftest(expected: dict, raw: bytes, qa: dict, proof: dict) -> dict:
    cases = ["verified_reconstructed_model_candidate_positive"]
    mutations = [
        ("false_status", lambda d:d.update(status="PRODUCTION_READY")),
        ("wrong_task", lambda d:d.update(task_id="previous-unknown")),
        ("wrong_base", lambda d:d.update(historical_task_git_base="0"*40)),
        ("wrong_source", lambda d:d.update(model_source_sha256="0"*64)),
        ("wrong_seed", lambda d:d.update(public_fixture_seed_sha256="0"*64)),
        ("wrong_diff", lambda d:d.update(unified_review_diff_sha256="0"*64)),
        ("path_escape", lambda d:d.update(review_target_allowlist=["../live.py"])),
        ("more_files", lambda d:d.update(review_target_allowlist=["windows_merge.py","test.py"])),
        ("fake_model_author", lambda d:d.update(source_authored_by="GITHUB_BOT")),
        ("fake_autonomous_pr", lambda d:d["limits"].update(agent_autonomous_pr_created=True)),
        ("fake_commit_actor", lambda d:d.update(git_commit_and_pr_authored_by="AGENT")),
        ("allow_commit", lambda d:d["limits"].update(authorization_to_commit_or_merge=True)),
        ("false_promotion", lambda d:d["limits"].update(source_promoted_to_production=True)),
        ("false_fence", lambda d:d["limits"].update(provider_lease_or_fence_proven=True)),
        ("false_sandbox", lambda d:d["limits"].update(secure_os_sandbox_proven=True)),
        ("fake_token_or_model", lambda d:d["limits"].update(model_calls_this_run=1)),
        ("fake_git_effect", lambda d:d["limits"].update(git_effects_this_run=1)),
        ("fewer_cases", lambda d:d["stress"]["counts"].update(translation=0)),
        ("bad_receipt", lambda d:d.update(model_source_original_receipt_sha256="0"*64)),
    ]
    for label, apply in mutations:
        candidate = copy.deepcopy(expected)
        apply(candidate)
        try:
            verify_bundle(candidate, expected)
        except Refused:
            cases.append(label + "_DENIED")
        else:
            raise AssertionError("UNSAFE_REVIEW_MANIFEST_ACCEPTED_" + label)
    with tempfile.TemporaryDirectory(prefix="office-v2-review-corrupt-") as t:
        corrupted = Path(t) / SOURCE_TARGET
        corrupted.write_bytes(raw + b"\n# changed after Worker receipt\n")
        try:
            original.verify_source(corrupted)
        except original.Refused:
            cases.append("altered_model_source_DENIED")
        else:
            raise AssertionError("UNPINNED_MODEL_SOURCE_ACCEPTED")
    fake_proof = copy.deepcopy(proof)
    fake_proof["new_original_worker"]["original_worker_verify"] = "FAIL"
    try:
        original.validate(fake_proof, qa)
    except original.Refused:
        cases.append("modified_historical_worker_receipt_DENIED")
    else:
        raise AssertionError("BAD_WORKER_EVIDENCE_ACCEPTED")
    need(len(cases) == 22, "REVIEW_NEGATIVE_COVERAGE_CHANGED")
    return {
        "status": "PASS_OFFLINE",
        "tests": len(cases),
        "model_calls": 0,
        "git_effects": 0,
        "production_promoted": False,
        "agent_pr_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("verify","selftest","patch"))
    args = parser.parse_args()
    raw, qa, proof = source_and_evidence()
    stress = run_stress(raw)
    bundle = make_bundle(raw, qa, proof, stress)
    verify_bundle(bundle, bundle)
    if args.mode == "patch":
        sys.stdout.write(patch_for_review(raw))
    elif args.mode == "verify":
        print(json.dumps(bundle, sort_keys=True))
    else:
        print(json.dumps(selftest(bundle, raw, qa, proof), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refused,original.Refused,AssertionError,OSError,ValueError,TypeError,
            KeyError,UnicodeError) as exc:
        print(json.dumps({"status":"FAIL_CLOSED",
                          "reason":str(exc)[:180],
                          "git_effects":0,"model_calls":0},sort_keys=True))
        raise SystemExit(2)
