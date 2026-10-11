#!/usr/bin/env python3
"""#612/#604: protected-default-branch verifier, never a writer authority.

This code is executed by workflow_run from DEFAULT BRANCH, not by untrusted
pull_request HEAD. Two credential-free checkouts: policy at GITHUB_SHA (main)
and candidate at the preceding verified Core Sensors PR HEAD. Only candidate
request + pinned source/provenance bytes are read; its scripts/workflows are
NEVER imported or run on host. Pinned generated code executes only inside a
non-root no-network read-only Docker guest with trusted hidden tests.

SELFTEST is pure/offline on Mac/Windows and does not run generated code.
Even hosted PASS never authorizes Git, model-generated arbitrary source,
production, credential custody, stale leases or retry of UNKNOWN effects.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

# Isolation ignores arbitrary PYTHONPATH/CWD injection. Imports below resolve
# ONLY the separately checked-out protected policy source tree, never HEAD.
POLICY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(POLICY / "scripts"))
import vf_office_v2_p0_hosted_mac4b_c1_nativeblob_qa as c1  # noqa: E402
import vf_office_v2_p0_hosted_container_boundary_lab as docker  # noqa: E402

REPO = "nocturney/velvetos-core"
CORE_WORKFLOW_ID = 352155264
WORKFLOW = ".github/workflows/office-p0-protected-base-c1-qa.yml"
REQUEST = ("docs/implementation/office-v2/phase2/"
           "p0-612-protected-base-c1-qa-request-2026-10-11.json")
SCHEMA = "velvetos.office-v2.p0-612-protected-base-c1-qa.v0"
REQUEST_SCHEMA = "velvetos.office-v2.p0-612-protected-base-c1-request.v0"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
SOURCE = c1.ARCHIVE
MANIFEST = c1.MANIFEST

EXPECTED_REQUEST = {
    "schema": REQUEST_SCHEMA,
    "task_id": c1.TASK_ID,
    "source_path": SOURCE,
    "source_sha256": c1.SOURCE_SHA256,
    "source_git_blob_sha1": c1.SOURCE_GIT_BLOB,
    "source_size_bytes": 480,
    "fixture": "canonical-tag-v1",
    "source_trusted_as_executable": False,
    "git_sink_write_authorized": False,
    "production_effects": False,
}


class Refused(Exception):
    pass


def need(ok, reason):
    if not ok:
        raise Refused(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def exact(observed, expected, name):
    need(type(observed) is type(expected), "TYPE_" + name)
    if type(expected) is dict:
        need(set(observed) == set(expected), "FIELDS_" + name)
        for key in expected:
            exact(observed[key], expected[key], name + "." + key)
    elif type(expected) is list:
        need(len(observed) == len(expected), "LENGTH_" + name)
        for j, (a, b) in enumerate(zip(observed, expected)):
            exact(a, b, name + "." + str(j))
    else:
        need(observed == expected, "VALUE_" + name)


def no_writer_ticket(request):
    # Deliberately non-authoritative even for a legitimate source and green CI.
    if type(request) is not dict:
        raise Refused("WRITER_REQUEST_NOT_OBJECT")
    if request.get("effect_state") in ("UNKNOWN", "EFFECT_IN_FLIGHT"):
        return "BLOCKED_UNKNOWN_NO_BLIND_RETRY"
    return "BLOCKED_PRETRUSTED_QA_NOT_GIT_WRITE_AUTHORITY"


def validate_event(evt):
    need(type(evt) is dict and type(evt.get("repository")) is dict,
         "GITHUB_WORKFLOW_RUN_EVENT_REQUIRED")
    repo = evt["repository"]
    need(repo.get("full_name") == REPO and
         repo.get("default_branch") == "main",
         "EVENT_NOT_CANONICAL_REPOSITORY")
    info = evt.get("workflow_run")
    need(type(info) is dict and
         type(info.get("id")) is int and info["id"] > 0 and
         type(info.get("workflow_id")) is int and
         info["workflow_id"] == CORE_WORKFLOW_ID and
         info.get("event") == "pull_request" and
         info.get("status") == "completed" and
         info.get("conclusion") == "success" and
         type(info.get("head_repository")) is dict and
         info["head_repository"].get("full_name") == REPO and
         type(info.get("head_sha")) is str and
         HEX40.fullmatch(info["head_sha"]) is not None,
         "CORE_CI_ISSUER_NOT_MATCHED_OR_PR_UNVERIFIED")
    return info["head_sha"], info["id"]


def require_regular(root: Path, rel: str, limit: int) -> bytes:
    need(root.is_dir() and not root.is_symlink(), "ROOT_NOT_REGULAR")
    path = root / rel
    need(path.is_file() and not path.is_symlink() and
         path.stat().st_size <= limit and
         path.resolve().is_relative_to(root.resolve()),
         "UNTRUSTED_PATH_OR_SIZE_" + Path(rel).name)
    return path.read_bytes()


def verify_candidate(candidate: Path):
    raw_request = require_regular(candidate, REQUEST, 2048)
    try:
        data = json.loads(raw_request.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise Refused("MALFORMED_CANDIDATE_REQUEST")
    exact(data, EXPECTED_REQUEST, "request")
    source = require_regular(candidate, SOURCE, 2048)
    c1.verify_source(source)
    manifest = require_regular(candidate, MANIFEST, 4096)
    try:
        c1.verify_manifest(json.loads(manifest.decode("utf-8")))
    except (ValueError, UnicodeError):
        raise Refused("UNTRUSTED_SOURCE_ORIGINAL_PROVENANCE")
    return source, raw_request, manifest


def git(repo: Path, *args):
    result = subprocess.run(["git", "-C", str(repo), *args],
                            check=False, capture_output=True,
                            stdin=subprocess.DEVNULL, timeout=10,
                            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                                 "GIT_CONFIG_NOSYSTEM": "1"})
    need(result.returncode == 0,
         "TRUSTED_GIT_READ_ONLY_COMMAND_REFUSED")
    return result.stdout.strip().decode("ascii")


def check_checkout(repo: Path, commit_sha: str):
    need(type(commit_sha) is str and HEX40.fullmatch(commit_sha) and
         repo.is_dir() and not repo.is_symlink() and
         (repo / ".git").is_dir(),
         "CHECKOUT_NOT_EXPECTED_GIT_TREE")
    need(git(repo, "rev-parse", "HEAD") == commit_sha,
         "CHECKOUT_HEAD_NOT_EXACT_PROVIDER_SHA")
    cred = subprocess.run(
        ["git", "-C", str(repo), "config", "--local", "--get-regexp",
         r"^http[.].*[.]extraheader$"],
        capture_output=True, stdin=subprocess.DEVNULL, timeout=7,
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
             "GIT_CONFIG_NOSYSTEM": "1"},
    )
    need(cred.returncode == 1 and not cred.stdout,
         "CHECKOUT_PERSISTED_GIT_CREDENTIAL_OR_CONFIG_FAILURE")
    # Checkout is read-only; generated byte sources are NEVER git hooks.
    return True


def preflight_hosted():
    e = os.environ
    need(sys.flags.isolated == 1 and e.get("GITHUB_ACTIONS") == "true" and
         e.get("GITHUB_EVENT_NAME") == "workflow_run" and
         e.get("RUNNER_ENVIRONMENT") == "github-hosted" and
         e.get("RUNNER_OS") == "Linux" and
         e.get("GITHUB_REPOSITORY") == REPO and
         e.get("GITHUB_REF") == "refs/heads/main" and
         type(e.get("GITHUB_SHA")) is str and
         HEX40.fullmatch(e["GITHUB_SHA"]) and
         e.get("GITHUB_RUN_ID", "").isdigit(),
         "PROTECTED_DEFAULT_BRANCH_HOSTED_RUN_ONLY")
    need(not any(e.get(n) for n in (
         "GITHUB_TOKEN", "GH_TOKEN", "GIT_ASKPASS", "SSH_ASKPASS",
         "AWS_ACCESS_KEY_ID", "GOOGLE_APPLICATION_CREDENTIALS")),
         "ENV_EXPORTED_PRIVILEGED_CREDENTIAL")
    workspace = Path(e.get("GITHUB_WORKSPACE", "")).resolve()
    need("/home/runner/work/" in workspace.as_posix() and
         workspace.is_dir(), "GITHUB_HOSTED_WORKSPACE_REQUIRED")
    need(POLICY == (workspace / "policy").resolve() and
         POLICY.is_relative_to(workspace),
         "VERIFIER_NOT_LOADED_FROM_PROTECTED_POLICY_CHECKOUT")
    path = Path(e.get("GITHUB_EVENT_PATH", "")).resolve()
    need(path.is_file() and path.stat().st_size < 600_000,
         "GITHUB_SIGNED_EVENT_PAYLOAD_MISSING")
    with path.open(encoding="utf-8") as file:
        event = json.load(file)
    candidate_sha, upstream_run = validate_event(event)
    need(candidate_sha != e["GITHUB_SHA"],
         "WORKFLOW_RUN_PR_HEAD_SHOULD_NOT_BE_PROTECTED_BASE")
    candidate = workspace / "candidate"
    check_checkout(POLICY, e["GITHUB_SHA"])
    check_checkout(candidate, candidate_sha)
    # Cross-check the trust-owned Python script against the *protected*
    # checkout's canonical Git blob; never consult PR-supplied verifier.
    path_rel = "scripts/vf_office_v2_p0_protected_base_c1_qa.py"
    own = (POLICY / path_rel).read_bytes()
    need(sha(own) == sha(git(POLICY, "show",
         e["GITHUB_SHA"] + ":" + path_rel).encode("utf-8")),
         "POLICY_SOURCE_NOT_EXACT_BASE_COMMIT")
    need(require_regular(POLICY, WORKFLOW, 6000) ==
         git(POLICY, "show", e["GITHUB_SHA"] + ":" + WORKFLOW).encode("utf-8"),
         "WORKFLOW_NOT_EXACT_PROTECTED_BASE_COMMIT")
    return workspace, candidate, e["GITHUB_SHA"], candidate_sha, upstream_run


def offline_selftest():
    # Offline, including on Windows SYSTEM Session0 & macOS user: NO model
    # execution, Docker, HTTP, model calls, credential access or git write.
    source = require_regular(POLICY, SOURCE, 2048)
    c1.verify_source(source)
    rows = ["original_C1_known_480_byte_sha"]
    raw_manifest = json.loads(require_regular(POLICY, MANIFEST, 4096))
    c1.verify_manifest(raw_manifest)
    rows.append("source_provenance_verified")
    exact(copy.deepcopy(EXPECTED_REQUEST), EXPECTED_REQUEST, "baseline")
    rows.append("strict_expected_request_pass")
    for key, value in EXPECTED_REQUEST.items():
        x = copy.deepcopy(EXPECTED_REQUEST)
        x[key] = (not value if type(value) is bool
                  else value + "_forged" if type(value) is str else value + 1)
        try:
            exact(x, EXPECTED_REQUEST, "forged")
        except Refused:
            rows.append("request_" + key + "_spoof_denied")
        else:
            raise Refused("FALSE_CANDIDATE_REQUEST_ACCEPTED")
    for extra in ("approval", "api_token", "writer_authority"):
        x = dict(EXPECTED_REQUEST, **{extra: True})
        try:
            exact(x, EXPECTED_REQUEST, "extra")
        except Refused:
            rows.append("unexpected_request_field_denied")
        else:
            raise Refused("ARBITRARY_REQUEST_FIELD_ACCEPTED")
    example = {"repository": {"full_name": REPO, "default_branch": "main"},
               "workflow_run": {
                   "id": 123, "workflow_id": CORE_WORKFLOW_ID,
                   "event": "pull_request", "status": "completed",
                   "conclusion": "success",
                   "head_repository": {"full_name": REPO},
                   "head_sha": "a" * 40}}
    need(validate_event(example) == ("a" * 40, 123),
         "VALID_HISTORICAL_CI_EVENT_UNEXPECTED")
    rows.append("provider_event_scope_structurally_valid")
    wrongs = [
        ("repository", "full_name", "attacker/repo"),
        ("repository", "default_branch", "preview"),
        ("workflow_run", "id", 0),
        ("workflow_run", "id", True),
        ("workflow_run", "workflow_id", 1),
        ("workflow_run", "workflow_id", True),
        ("workflow_run", "event", "push"),
        ("workflow_run", "status", "in_progress"),
        ("workflow_run", "conclusion", "failure"),
        ("workflow_run", "head_repository", {"full_name": "fork/repo"}),
        ("workflow_run", "head_sha", "0"),
        ("workflow_run", "head_sha", "0" * 40 + "\n"),
    ]
    for section, key, value in wrongs:
        e = copy.deepcopy(example)
        e[section][key] = value
        try:
            validate_event(e)
        except Refused:
            rows.append("false_issuer_or_foreign_repo_denied")
        else:
            raise Refused("FALSE_PROVIDER_WORKFLOW_RUN_ACCEPTED")
    for bad in (source + b"\n", source[:-1], b"import os\n" + source,
                source.replace(b"return ''.join(parts)", b"return 'evil'")):
        try:
            c1.verify_source(bad)
        except (c1.Refused, c1.reviewed.Refused):
            rows.append("tampered_model_source_denied")
        else:
            raise Refused("TAMPERED_C1_SOURCE_ACCEPTED")
    for candidate in (
        {"qa_passed": True, "epoch": 7, "current_sha": "a" * 40},
        {"effect_state": "UNKNOWN", "qa_passed": True},
        {"effect_state": "EFFECT_IN_FLIGHT"},
        {"worker": "mac", "github_app_token": "fake"},
    ):
        need(no_writer_ticket(candidate).startswith("BLOCKED_"),
             "QA_FORGED_GIT_WRITE_AUTHORITY")
        rows.append("issuer_proof_never_git_token")
    need(len(rows) == 33, "OFFLINE_TEST_COUNT_CHANGED")
    return {
        "schema": SCHEMA,
        "status": "PASS_33_OFFLINE_PROTECTED_BASE_ISSUER_NEGATIVES_ONLY",
        "tests": len(rows),
        "policy_from_protected_branch_tested_live": False,
        "model_code_executed_on_user_host": False,
        "docker_calls": 0, "github_api_writes": 0, "network_calls": 0,
        "provider_leases": 0, "model_calls": 0,
        "git_sink_credential_custody_proven": False,
        "production_authority": False,
    }


def hosted_run():
    # All GH and runtime state checks before model-source payload or Docker.
    workspace, candidate, base_sha, head_sha, source_run = preflight_hosted()
    offline_selftest()
    request = candidate / REQUEST
    if not request.exists():
        return {"schema": SCHEMA, "status": "SKIP_NO_QA_REQUEST_ON_PR_HEAD",
                "policy_sha": base_sha, "candidate_sha": head_sha,
                "upstream_core_run_id": source_run,
                "docker_calls": 0, "production_authority": False,
                "git_sink_credential_custody_proven": False}
    original, req, manifest = verify_candidate(candidate)
    # Re-use pinned *protected-base* reviewers, fixture and Docker argv.
    # Override ONLY candidate source/receipt root, not Python import path.
    c1.ROOT = candidate
    c1.selftest()  # 29 static negatives, never executes untrusted Python
    entry, code, row = c1.reviewed_case()
    need(code == original and sha(code) == c1.SOURCE_SHA256,
         "CANDIDATE_MUST_MATCH_VERIFIED_BYTES")
    start = time.monotonic()
    image_ref = docker.EXPECTED_IMAGE_DIGEST
    need(image_ref.startswith("python@sha256:"),
         "IMMUTABLE_PYTHON_GUEST_REQUIRED")
    docker.docker_command(["docker", "version", "--format", "{{.Server.Version}}"],
                          timeout=12)
    docker.docker_command(["docker", "pull", "--quiet", image_ref], timeout=125)
    info = json.loads(
        docker.docker_command(["docker", "image", "inspect", image_ref],
                              timeout=12))[0]
    image_id = info["Id"]
    need(image_ref in info["RepoDigests"] and
         image_id.startswith("sha256:") and
         docker.SHA256.fullmatch(image_id[7:]),
         "GUEST_IMAGE_DIGEST_NOT_INSPECTED")
    with tempfile.TemporaryDirectory(prefix="vf-trusted-base-qa-") as tmp, \
         tempfile.TemporaryDirectory(prefix="vf-trusted-no-credential-") as secret:
        work = Path(tmp)
        canary = Path(secret) / "synthetic-cannot-see.key"
        canary.write_text("SYNTHETIC_NOT_A_GIT_SECRET", encoding="ascii")
        src = work / row["target"]
        src.write_bytes(code)
        tests = work / row["test"]
        tests.parent.mkdir(parents=True)
        tests.write_text(row["visible"], encoding="utf-8")
        (work / "hidden.py").write_text(row["hidden"], encoding="utf-8")
        (work / "qa_inner.py").write_text(docker.INNER, encoding="utf-8")
        for p in (src, tests, work / "hidden.py", work / "qa_inner.py"):
            p.chmod(0o644)
        tests.parent.chmod(0o755)
        work.chmod(0o755)
        need(sha(src.read_bytes()) == c1.SOURCE_SHA256 and
             c1.git_blob_sha(src.read_bytes()) == c1.SOURCE_GIT_BLOB,
             "BEFORE_GUEST_CANDIDATE_BYTES_NORMALIZED")
        argv = docker.docker_args(image_id, work, canary, entry)
        docker.assert_docker_plan(argv, image_id, work, canary, entry)
        cid = None
        try:
            cid = docker.docker_command(argv, timeout=18)
            need(docker.DOCKER_ID.fullmatch(cid),
                 "CONTAINER_ID_NOT_EXACT")
            security = docker.inspect_cid(cid, work, image_id)
            stdout = docker.docker_command(
                ["docker", "start", "--attach", cid], timeout=38)
            state = json.loads(
                docker.docker_command(["docker", "inspect", cid],
                                      timeout=12))[0]["State"]
            need(state["Status"] == "exited" and state["ExitCode"] == 0,
                 "TRUSTED_BASE_DOCKER_QA_ACTUALLY_FAILED")
            receipts = [json.loads(s) for s in stdout.splitlines()
                        if s.startswith("{") and s.endswith("}")]
            need(len(receipts) == 1, "ONE_TRUSTED_GUEST_RECEIPT_REQUIRED")
            observed = receipts[0]
            need(
                observed.get("status") ==
                    "PASS_CONTAINER_ISOLATION_NEGATIVES_AND_QA" and
                observed.get("source_sha256") == c1.SOURCE_SHA256 and
                observed.get("visible_3") is True and
                observed.get("hidden_12") is True and
                observed.get("network_denied") is True and
                observed.get("host_canary_invisible") is True and
                observed.get("no_exported_github_token") is True and
                observed.get("no_docker_socket") is True and
                observed.get("uid_65534") is True and
                observed.get("setuid_root_denied") is True and
                observed.get("read_only_root_and_mount") is True and
                observed.get("tmpfs_only_write") is True,
                "ORIGINAL_C1_3PLUS12_OR_DOCKER_ISOLATION_NEGATIVES_FAILED")
            # Detect changes in HEAD data even after the Docker test.
            need(verify_candidate(candidate) == (original, req, manifest),
                 "CANDIDATE_BYTES_CHANGED_DURING_HOSTED_QA")
            need((work / row["target"]).read_bytes() == original,
                 "GUEST_SOURCE_BYTES_CHANGED")
            return {
                "schema": SCHEMA,
                "status": "PASS_TRUSTED_DEFAULT_BRANCH_POLICY_C1_ORIGINAL_3PLUS12",
                "trusted_policy_main_sha": base_sha,
                "untrusted_candidate_sha": head_sha,
                "upstream_protected_core_run_id": source_run,
                "source_sha256": c1.SOURCE_SHA256,
                "source_git_blob_sha1": c1.SOURCE_GIT_BLOB,
                "source_bytes": 480,
                "visible_3": True, "hidden_12": True,
                "docker_container_security": security,
                "policy_execution_from_candidate_head": False,
                "head_workflow_or_verifier_imported": False,
                "github_credentials_in_guest": False,
                "github_git_writes": 0, "provider_lease_ops": 0,
                "model_calls": 0, "paid_api_usd": 0,
                "unknown_effect_replayed": False,
                "single_credentialed_sink_proven": False,
                "future_arbitrary_source_qa_admitted": False,
                "production_authority": False,
                "elapsed_seconds": round(time.monotonic() - start, 3),
            }
        finally:
            if cid and docker.DOCKER_ID.fullmatch(cid):
                docker.docker_command(["docker", "rm", "--force", cid],
                                      timeout=14)


def main():
    need(len(sys.argv) == 2 and sys.argv[1] in ("selftest", "run"),
         "ONLY_SAFE_OFFLINE_SELFTEST_OR_PROTECTED_HOSTED_RUN")
    return offline_selftest() if sys.argv[1] == "selftest" else hosted_run()


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True))
    except (Refused, c1.Refused, c1.reviewed.Refused,
            docker.Refused, docker.hosted.Refused, ValueError, KeyError,
            TypeError, OSError, subprocess.TimeoutExpired,
            AssertionError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED",
                          "reason": str(exc)[:180],
                          "model_source_executed_on_user_host": False,
                          "git_writes": 0,
                          "production_authority": False}, sort_keys=True))
        raise SystemExit(2)
