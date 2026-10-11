#!/usr/bin/env python3
"""#612: bounded credential-free hosted QA of ONE new Mac Qwen4B candidate.

The original guided-attempt A remains a static REJECT; the new guided B1
is exact SHA-pinned, AST reviewed, and may execute ONLY in a temporary
GitHub-hosted low-permission Docker guest. No local model-generated code.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import vf_office_v2_p0_hosted_container_boundary_lab as sandbox
import vf_office_v2_p0_hosted_new_source_review_lab as reviewed
import vf_office_v2_p0_diverse_task_fixtures as fixtures

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "velvetos.office-v2.p0-mac4b-explicit-state-machine-hosted-qa.v0"
ARCHIVE = "docs/implementation/office-v2/phase2/quarantined-new-model-sources-2026-10-11/"
GOOD_NAME = "mac-qwen4b-tag-guided-b1.py.txt"
BAD_NAME = "mac-qwen4b-tag-feedback-a1.py.txt"
GOOD_SHA = "47c4a82129f7ca5ad034144c2301b029e6beb4e5578a4f6a7f4a0492de3c439c"
BAD_SHA = "27ee28702c88e1d84a2409c63337228693186e8802a1115faeace86a543f6b23"
MANIFEST = ROOT / "docs/implementation/office-v2/phase2/p0-612-mac-qwen4b-prompt-revision-2026-10-11.json"
MANIFEST_SHA = "baefc46135372a572cc047b0f9dbd1f546da621d2e830df63020cc2483bf2aad"
SOURCE_TASK = "canonical-tag-v1"

class Refused(Exception):
    pass

def require(ok, reason):
    if not ok:
        raise Refused(reason)

def sha(v):
    return hashlib.sha256(v).hexdigest()

def candidate(name, expected_sha):
    require(name in (GOOD_NAME, BAD_NAME), "UNKNOWN_SOURCE_ARCHIVE")
    source = ROOT / ARCHIVE / name
    require(source.is_file() and not source.is_symlink(), "SOURCE_FILE_MISSING")
    data = source.read_bytes()
    require(len(data) < 16384 and sha(data) == expected_sha,
            "UNREVIEWED_GENERATED_SOURCE_HASH_DRIFT")
    return data

def reviewed_case():
    require(SOURCE_TASK in fixtures.catalog(), "UNAPPROVED_FIXTURE")
    row = fixtures.catalog()[SOURCE_TASK]
    require(row["target"] == "canonical_tag.py" and
            row["test"] == "tests/test_canonical_tag.py", "TARGET_DRIFT")
    good = candidate(GOOD_NAME, GOOD_SHA)
    require(reviewed.reviewed_structure(good, row["target"]),
            "GUIDED_SOURCE_NOT_STATICALLY_ADMITTED")
    # A1 was visibly erroneous and included disallowed pop(). It MUST remain
    # rejected by the exact original AST policy, not silently become runnable.
    bad = candidate(BAD_NAME, BAD_SHA)
    try:
        reviewed.reviewed_structure(bad, row["target"])
    except reviewed.Refused as exc:
        require(str(exc) == "DYNAMIC_CALL_TARGET_REFUSED",
                "HISTORICAL_BAD_SOURCE_REJECTION_REASON_CHANGED")
    else:
        raise Refused("FAILED_SOURCE_FALSE_ADMITTED")
    require(MANIFEST.is_file() and not MANIFEST.is_symlink() and
            sha(MANIFEST.read_bytes()) == MANIFEST_SHA,
            "ONE_SHOT_MODEL_MANIFEST_SHA_DRIFT")
    receipt = json.loads(MANIFEST.read_text(encoding="utf-8"))
    runs = receipt.get("new_attempts")
    require(receipt.get("schema") ==
            "velvetos.office-v2.p0-mac-qwen4b-feedback-two-new-attempts-20261011.v0"
            and receipt.get("new_model_calls") == 2
            and receipt.get("one_call_per_new_task") is True
            and receipt.get("automatic_retry") is False
            and receipt.get("generated_python_executed_on_host") is False
            and receipt.get("local_model_code_qa_executed") is False
            and receipt.get("hosted_qa_status") == "NOT_YET_OBSERVED"
            and receipt.get("paid_api_usd") == 0
            and receipt.get("production_effects") is False
            and len(runs or []) == 2, "MODEL_HISTORY_OR_SCOPE_DRIFT")
    for run, name, digest, expected_status in zip(
        runs, (BAD_NAME, GOOD_NAME), (BAD_SHA, GOOD_SHA),
        ("REJECTED", "PASS_AST_ONLY_NOT_QA")
    ):
        require(run.get("candidate", "").endswith(name)
                and run.get("candidate_sha256") == digest
                and run.get("model_calls") == 1
                and run.get("static_policy_status") == expected_status
                and run.get("hosted_qa_submitted") is False
                and len(run.get("prompt_sha256", "")) == 64
                and len(run.get("response_sha256", "")) == 64,
                "ONE_SHOT_CANDIDATE_PROVENANCE_DRIFT")
    require(runs[0]["task_id"] != runs[1]["task_id"]
            and runs[0]["task_id"].endswith("-a1")
            and runs[1]["task_id"].endswith("-b1"),
            "DUPLICATE_OR_RETRIED_TASK_ID")
    entry = {"label": "mac-qwen4b-guided-b1-20261011",
             "fixture": SOURCE_TASK, "sha256": GOOD_SHA,
             "test_sha256": sha(row["visible"].encode()),
             "hidden_sha256": sha(row["hidden"].encode()),
             "expected_good": True}
    return entry, good, row

def selftest():
    entry, good, row = reviewed_case()
    checks = ["new_source_exact_sha", "new_source_ast_reviewed",
              "old_source_exact_sha", "old_source_ast_rejected",
              "one_shot_receipts_both_pinned", "no_model_run_in_selftest",
              "task_ids_unique_and_unretried"]
    require(sha(good) == GOOD_SHA and row["target"] == "canonical_tag.py",
            "SOURCE_LOCK_DRIFT")
    checks.append("public_fixture_pinned")
    fake = "sha256:" + "a"*64
    base = Path(tempfile.gettempdir()).resolve()
    directory = base / "vf-mac4b-guided-static-no-create"
    canary = base / "vf-mac4b-host-canary-not-created" / "fake.key"
    args = sandbox.docker_args(fake, directory, canary, entry)
    sandbox.assert_docker_plan(args, fake, directory, canary, entry)
    checks.append("docker_exact_plan")
    for original, mutated in (
        ("--network=none", "--network=host"),
        ("--read-only", "--privileged"),
        ("--cap-drop=ALL", "--cap-add=SYS_ADMIN"),
        ("--security-opt=no-new-privileges:true", "--security-opt=seccomp=unconfined"),
        ("--user=65534:65534", "--user=0:0"),
        ("--ipc=none", "--ipc=host"),
    ):
        changed = args.copy()
        changed[changed.index(original)] = mutated
        try:
            sandbox.assert_docker_plan(changed, fake, directory, canary, entry)
        except sandbox.Refused:
            checks.append("privileged_guest_plan_denied")
        else:
            raise Refused("UNSAFE_GUEST_PARAMETER_ACCEPTED")
    require(len(checks) == 15, "STATIC_TEST_COUNT_DRIFT")
    return {"schema": SCHEMA,
            "status": "PASS_MAC4B_B1_STATIC_AND_A1_REJECTION_ONLY",
            "tests": len(checks), "new_static_good_source_sha256": GOOD_SHA,
            "rejected_source_sha256": BAD_SHA,
            "known_original_win9b_success_only_in_separate_pr695": True,
            "candidate_executed_locally": False, "model_calls": 0,
            "docker_calls": 0, "git_writes": 0,
            "production_authority": False,
            "mac_algorithm_qa_pass_proven": False}

def run():
    selftest()
    # Never execute outside a new read-only uncredentialed hosted PR runner.
    sandbox.hosted.runner_context_check(os.environ)
    sandbox.hosted.no_persisted_checkout_auth()
    require(os.environ.get("RUNNER_OS") == "Linux"
            and os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
            and os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
            and os.environ.get("GITHUB_RUN_ID", "").isdigit(),
            "PR_ONLY_CREDENTIAL_FREE_HOSTED_LAB")
    start = time.monotonic()
    image = sandbox.EXPECTED_IMAGE_DIGEST
    require(image.startswith("python@sha256:"),
            "PINNED_OCI_IMAGE_REQUIRED")
    sandbox.docker_command(["docker", "version",
                            "--format", "{{.Server.Version}}"], timeout=12)
    sandbox.docker_command(["docker", "pull", "--quiet", image], timeout=125)
    observed = json.loads(sandbox.docker_command(
        ["docker", "image", "inspect", image], timeout=12))[0]
    image_id = observed["Id"]
    require(image_id.startswith("sha256:")
            and sandbox.SHA256.fullmatch(image_id[7:])
            and image in observed["RepoDigests"],
            "APPROVED_OCI_IMAGE_DIGEST_DRIFT")
    entry, source, row = reviewed_case()
    with tempfile.TemporaryDirectory(prefix="vf-p0-qwen4b-new-source-") as tmp, \
         tempfile.TemporaryDirectory(prefix="vf-p0-qwen4b-excluded-canary-") as secret:
        wd = Path(tmp)
        host_canary = Path(secret) / "synthetic-only-not-secret.key"
        host_canary.write_text("SYNTHETIC_CANARY_NO_CREDENTIAL",
                               encoding="ascii")
        target = wd / row["target"]
        target.write_bytes(source)
        visible = wd / row["test"]
        visible.parent.mkdir(parents=True)
        visible.write_text(row["visible"], encoding="utf-8")
        (wd / "hidden.py").write_text(row["hidden"], encoding="utf-8")
        (wd / "qa_inner.py").write_text(sandbox.INNER, encoding="utf-8")
        for file in (target, visible, wd / "hidden.py", wd / "qa_inner.py"):
            file.chmod(0o644)
        (wd / "tests").chmod(0o755)
        wd.chmod(0o755)
        args = sandbox.docker_args(image_id, wd, host_canary, entry)
        sandbox.assert_docker_plan(args, image_id, wd, host_canary, entry)
        cid = None
        try:
            cid = sandbox.docker_command(args, timeout=18)
            require(sandbox.DOCKER_ID.fullmatch(cid),
                    "UNOWNED_GUEST_CONTAINER_DENIED")
            details = sandbox.inspect_cid(cid, wd, image_id)
            raw = sandbox.docker_command(["docker", "start", "--attach", cid],
                                         timeout=38)
            state = json.loads(sandbox.docker_command(
                ["docker", "inspect", cid], timeout=12))[0]["State"]
            require(state["Status"] == "exited" and state["ExitCode"] == 0,
                    "GUEST_QA_EXIT_NONZERO")
            receipts = [json.loads(line) for line in raw.splitlines()
                        if line.startswith("{") and line.endswith("}")]
            require(len(receipts) == 1, "SINGLE_INDEPENDENT_QA_REQUIRED")
            q = receipts[0]
            require(q.get("status") == "PASS_CONTAINER_ISOLATION_NEGATIVES_AND_QA"
                    and q.get("source_sha256") == GOOD_SHA
                    and q.get("visible_3") is True
                    and q.get("hidden_12") is True
                    and q.get("network_denied") is True
                    and q.get("host_canary_invisible") is True
                    and q.get("no_exported_github_token") is True
                    and q.get("no_docker_socket") is True
                    and q.get("uid_65534") is True
                    and q.get("setuid_root_denied") is True
                    and q.get("read_only_root_and_mount") is True,
                    "NEW_MAC_QWEN4B_ALGORITHM_QA_NOT_PROVEN")
            return {"schema": SCHEMA,
                    "status": "PASS_NEW_MAC4B_ALGORITHM_IN_CREDENTIAL_FREE_HOSTED_DOCKER",
                    "github_run_id": os.environ["GITHUB_RUN_ID"],
                    "new_model_calls_in_hosted_runner": 0,
                    "source_sha256": GOOD_SHA,
                    "prior_bad_source_executed": False,
                    "visible_3": q["visible_3"],
                    "hidden_12": q["hidden_12"],
                    "guest_inspection": details,
                    "registered_generated_code_only": True,
                    "arbitrary_future_generated_code_admitted": False,
                    "local_chris_or_mac_generated_code_executed": False,
                    "os_kernel_escape_resistance_proven": False,
                    "git_sink_exclusive_authority_proven": False,
                    "autonomous_coding_worker_proven": False,
                    "no_production_authority": True,
                    "paid_api_usd": 0,
                    "elapsed_seconds": round(time.monotonic()-start,3)}
        finally:
            if cid is not None and sandbox.DOCKER_ID.fullmatch(cid):
                sandbox.docker_command(["docker","rm","--force",cid],timeout=14)

def main():
    require(len(sys.argv)==2 and sys.argv[1] in ("selftest", "run"),
            "ONLY_SELFTEST_OR_HOSTED_RUN")
    print(json.dumps(selftest() if sys.argv[1]=="selftest" else run(),
                     sort_keys=True))

if __name__ == "__main__":
    try:
        main()
    except (Refused, reviewed.Refused, sandbox.Refused, sandbox.hosted.Refused,
            OSError, ValueError, KeyError, AssertionError, TypeError,
            subprocess.TimeoutExpired) as error:
        print(json.dumps({"status":"FAIL_CLOSED", "reason":str(error)[:200],
                          "no_production_authority":True,
                          "generated_source_executed_on_local_host":False},
                         sort_keys=True))
        raise SystemExit(2)
