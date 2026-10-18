#!/usr/bin/env python3
"""#612: exact-byte already-generated Mac C1 candidate, hosted Docker QA ONLY.

SELFTEST reads exact public source, provenance and AST, but does not import or
execute model-generated Python. RUN refuses non-PR/non-hosted contexts BEFORE
starting Docker. No GitHub credentials, production data, new local model calls,
client workstation source execution or autonomous agent admission.
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
SCHEMA = "velvetos.office-v2.p0-612-mac4b-c1-nativeblob-hosted-qa.v0"
ARCHIVE = ("docs/implementation/office-v2/phase2/"
           "quarantined-new-model-sources-2026-10-11/"
           "mac-qwen4b-tag-byteexact-c1.py.txt")
MANIFEST = ("docs/implementation/office-v2/phase2/"
            "p0-612-mac-qwen4b-c1-nativeblob-hostedqa-2026-10-11.json")
SOURCE_SHA256 = "084d446873fb871ad444f7704b7868b72e599829b9da6e0a2fca0f972d4dae6a"
SOURCE_GIT_BLOB = "7ec37475b86cabe728b95be37e38e984a74e6264"
SOURCE_SIZE = 480
TASK_ID = "p0-mac-qwen4b-tag-byteexact-20261011-c1"
FIXTURE = "canonical-tag-v1"


class Refused(Exception):
    pass


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise Refused(msg)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def verify_source(data: bytes) -> None:
    require(type(data) is bytes and len(data) == SOURCE_SIZE,
            "MAC_C1_ORIGINAL_BYTE_COUNT_DRIFT")
    require(sha(data) == SOURCE_SHA256,
            "MAC_C1_ORIGINAL_SHA256_DRIFT")
    require(git_blob_sha(data) == SOURCE_GIT_BLOB,
            "MAC_C1_NATIVE_GIT_BLOB_MISMATCH")
    require(data.endswith(b"return ''.join(parts)") and
            not data.endswith(b"\n") and data[-1] == 41,
            "MAC_C1_LAST_BYTE_WAS_NORMALIZED")
    require(reviewed.reviewed_structure(data, "canonical_tag.py"),
            "MAC_C1_UNAPPROVED_STATIC_AST")


def verify_manifest(m: dict) -> None:
    require(type(m) is dict and
            m.get("schema") ==
            "velvetos.office-v2.p0-612-mac-qwen4b-c1-nativeblob-hostedqa-provenance.v0"
            and m.get("task_id") == TASK_ID
            and m.get("source_host") == "MacMiniOffice.local"
            and m.get("model") == "qwen3.5:4b"
            and m.get("model_calls_original_task") == 1
            and m.get("model_calls_for_this_git_transport") == 0
            and m.get("original_public_source_size_bytes") == SOURCE_SIZE
            and m.get("original_public_source_final_byte_dec") == 41
            and m.get("original_source_terminal_newline") is False
            and m.get("original_public_source_sha256") == SOURCE_SHA256
            and m.get("original_public_source_git_blob_sha1") == SOURCE_GIT_BLOB
            and m.get("archived_path") == ARCHIVE
            and m.get("transport_same_git_blob_sha_as_mac") is True
            and m.get("transport_remote_blob_size_bytes") == SOURCE_SIZE
            and m.get("host_generated_python_executed") is False
            and m.get("mac_behavioral_qa_executed") is False
            and m.get("hosted_qa_at_manifest_creation") == "NOT_YET_OBSERVED"
            and m.get("existing_mac_b1_source_or_branch_modified") is False
            and m.get("git_credentials_given_to_model") is False
            and m.get("paid_api_usd") == 0
            and m.get("production_effects") is False
            and m.get("autonomous_agent_pr_proven") is False
            and m.get("exclusive_git_sink_proven") is False,
            "LOCAL_ONE_SHOT_PROVENANCE_OR_AUTHORITY_DRIFT")


def reviewed_case() -> tuple[dict, bytes, dict]:
    path, manifest_path = ROOT / ARCHIVE, ROOT / MANIFEST
    require(path.is_file() and not path.is_symlink() and
            manifest_path.is_file() and not manifest_path.is_symlink(),
            "C1_QUARANTINE_OR_MANIFEST_MISSING")
    data = path.read_bytes()
    verify_source(data)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verify_manifest(manifest)
    require(FIXTURE in fixtures.catalog(), "FIXTURE_NOT_REGISTERED")
    row = fixtures.catalog()[FIXTURE]
    require(row["target"] == "canonical_tag.py" and
            row["test"] == "tests/test_canonical_tag.py",
            "FIXTURE_TARGET_OR_TEST_PATH_DRIFT")
    entry = {
        "label": "mac4b-c1-byteexact-20261011",
        "fixture": FIXTURE,
        "sha256": SOURCE_SHA256,
        "expected_good": True,
        "test_sha256": sha(row["visible"].encode("utf-8")),
        "hidden_sha256": sha(row["hidden"].encode("utf-8")),
    }
    return entry, data, row


def selftest() -> dict:
    entry, source, row = reviewed_case()
    manifest = json.loads((ROOT / MANIFEST).read_text(encoding="utf-8"))
    checks = [
        "mac_source_exact_480_bytes",
        "source_git_blob_sha1_equals_physical_mac",
        "original_model_response_sha256_pinned",
        "no_terminal_lf",
        "static_ast_allowlist_passes",
        "one_shot_model_provenance_static",
        "fixture_3_visible_12_hidden_pinned",
        "no_local_generated_python_exec",
    ]
    require(source[-1] == 41 and entry["fixture"] == FIXTURE and
            row["target"] == "canonical_tag.py", "ORIGINAL_CODE_SCOPE_DRIFT")
    for mutated in (
        source + b"\n",
        source[:-1],
        b"",
        b"import os\n" + source,
        source.replace(b"pending_separator", b"pending_separator_v2"),
        source.replace(b"return ''.join(parts)", b"return 'bad'"),
    ):
        try:
            verify_source(mutated)
        except (Refused, reviewed.Refused):
            checks.append("source_tampering_refused")
        else:
            raise Refused("TAMPERED_MAC_SOURCE_FALSE_ADMITTED")
    for key, changed in (
        ("model_calls_original_task", 2),
        ("original_source_terminal_newline", True),
        ("original_public_source_sha256", "0" * 64),
        ("original_public_source_git_blob_sha1", "0" * 40),
        ("host_generated_python_executed", True),
        ("existing_mac_b1_source_or_branch_modified", True),
    ):
        wrong = dict(manifest, **{key: changed})
        try:
            verify_manifest(wrong)
        except Refused:
            checks.append("provenance_tampering_refused")
        else:
            raise Refused("FALSE_PROVENANCE_OR_PREVIOUS_SOURCE_OVERRIDE")
    image = "sha256:" + "a" * 64
    tmp = Path(tempfile.gettempdir()).resolve()
    fixture_dir = tmp / "vf-mac4b-c1-synthetic-no-create"
    synthetic_canary = tmp / "vf-mac4b-c1-no-credential" / "test-canary.key"
    args = sandbox.docker_args(image, fixture_dir, synthetic_canary, entry)
    sandbox.assert_docker_plan(args, image, fixture_dir, synthetic_canary, entry)
    checks.append("read_only_credential_free_container_plan")
    for old, replacement in (
        ("--network=none", "--network=host"),
        ("--read-only", "--privileged"),
        ("--cap-drop=ALL", "--cap-add=SYS_ADMIN"),
        ("--security-opt=no-new-privileges:true", "--security-opt=seccomp=unconfined"),
        ("--user=65534:65534", "--user=0:0"),
        ("--ipc=none", "--ipc=host"),
        ("--pids-limit=32", "--pids-limit=2048"),
        ("--memory=256m", "--memory=8g"),
    ):
        modified = list(args)
        modified[modified.index(old)] = replacement
        try:
            sandbox.assert_docker_plan(
                modified, image, fixture_dir, synthetic_canary, entry
            )
        except sandbox.Refused:
            checks.append("unsafe_container_flag_denied")
        else:
            raise Refused("UNSAFE_CONTAINER_ADMITTED")
    require(len(checks) == 29, "OFFLINE_NEGATIVES_COUNT_DRIFT")
    return {
        "schema": SCHEMA,
        "status": "PASS_29_STATIC_C1_NATIVEBLOB_AND_CONTAINER_NEGATIVES_NOT_QA",
        "tests": len(checks),
        "mac_original_source_sha256": SOURCE_SHA256,
        "git_blob_sha1": SOURCE_GIT_BLOB,
        "source_bytes": len(source),
        "local_model_generated_source_executed": False,
        "hosted_source_qa_proven": False,
        "docker_calls": 0, "model_calls": 0,
        "production_authority": False, "git_sink_credential_custody_proven": False,
    }


def run() -> dict:
    selftest()
    # Only a *hosted public PR run* may execute pinned generated Python, and
    # ONLY inside the inspected credential-free, no-network Docker guest.
    sandbox.hosted.runner_context_check(os.environ)
    sandbox.hosted.no_persisted_checkout_auth()
    require(
        os.environ.get("RUNNER_OS") == "Linux" and
        os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted" and
        os.environ.get("GITHUB_EVENT_NAME") == "pull_request" and
        os.environ.get("GITHUB_REPOSITORY") == "nocturney/velvetos-core" and
        os.environ.get("GITHUB_RUN_ID", "").isdigit(),
        "GITHUB_HOSTED_PR_WITH_NO_WRITE_CREDENTIALS_ONLY"
    )
    start = time.monotonic()
    image_ref = sandbox.EXPECTED_IMAGE_DIGEST
    require(image_ref.startswith("python@sha256:"),
            "IMMUTABLE_DOCKER_IMAGE_REQUIRED")
    sandbox.docker_command(["docker", "version", "--format", "{{.Server.Version}}"],
                           timeout=12)
    sandbox.docker_command(["docker", "pull", "--quiet", image_ref], timeout=125)
    obj = json.loads(
        sandbox.docker_command(["docker", "image", "inspect", image_ref], timeout=12)
    )[0]
    image_id = obj["Id"]
    require(
        image_ref in obj["RepoDigests"] and
        image_id.startswith("sha256:") and
        sandbox.SHA256.fullmatch(image_id[7:]) is not None,
        "PINNED_IMAGE_INSPECTION_FAILED"
    )
    entry, source, row = reviewed_case()
    with tempfile.TemporaryDirectory(prefix="vf-mac-c1-hosted-qa-") as tmp, \
         tempfile.TemporaryDirectory(prefix="vf-c1-excluded-host-canary-") as excluded:
        work = Path(tmp)
        canary = Path(excluded) / "synthetic-only-not-credential.key"
        canary.write_text("SYNTHETIC_ZERO_AUTHORITY", encoding="ascii")
        target = work / row["target"]
        target.write_bytes(source)  # byte-preserving copy, NO newline insertion
        visible = work / row["test"]
        visible.parent.mkdir(parents=True)
        visible.write_text(row["visible"], encoding="utf-8")
        (work / "hidden.py").write_text(row["hidden"], encoding="utf-8")
        (work / "qa_inner.py").write_text(sandbox.INNER, encoding="utf-8")
        for item in (target, visible, work / "hidden.py", work / "qa_inner.py"):
            item.chmod(0o644)
        visible.parent.chmod(0o755)
        work.chmod(0o755)
        require(sha(target.read_bytes()) == SOURCE_SHA256 and
                git_blob_sha(target.read_bytes()) == SOURCE_GIT_BLOB,
                "PRE_GUEST_MAC_ORIGINAL_BYTES_CHANGED")
        argv = sandbox.docker_args(image_id, work, canary, entry)
        sandbox.assert_docker_plan(argv, image_id, work, canary, entry)
        cid = None
        try:
            cid = sandbox.docker_command(argv, timeout=18)
            require(sandbox.DOCKER_ID.fullmatch(cid) is not None,
                    "UNVERIFIED_DOCKER_GUEST_ID")
            observed = sandbox.inspect_cid(cid, work, image_id)
            stdout = sandbox.docker_command(
                ["docker", "start", "--attach", cid], timeout=38
            )
            state = json.loads(
                sandbox.docker_command(["docker", "inspect", cid], timeout=12)
            )[0]["State"]
            require(state["Status"] == "exited" and state["ExitCode"] == 0,
                    "INDEPENDENT_GUEST_QA_FAILED")
            receipts = [json.loads(line) for line in stdout.splitlines()
                        if line.startswith("{") and line.endswith("}")]
            require(len(receipts) == 1, "EXACTLY_ONE_QA_RECEIPT_REQUIRED")
            q = receipts[0]
            require(
                q.get("status") == "PASS_CONTAINER_ISOLATION_NEGATIVES_AND_QA" and
                q.get("source_sha256") == SOURCE_SHA256 and
                q.get("visible_3") is True and
                q.get("hidden_12") is True and
                q.get("network_denied") is True and
                q.get("host_canary_invisible") is True and
                q.get("no_exported_github_token") is True and
                q.get("no_docker_socket") is True and
                q.get("uid_65534") is True and
                q.get("setuid_root_denied") is True and
                q.get("read_only_root_and_mount") is True and
                q.get("tmpfs_only_write") is True,
                "C1_MODEL_ALGORITHM_OR_CONTAINER_NEGATIVES_FAILED"
            )
            return {
                "schema": SCHEMA,
                "status": "PASS_MAC_C1_ORIGINAL_480_BYTES_IN_HOSTED_DOCKER_QA",
                "github_run_id": os.environ["GITHUB_RUN_ID"],
                "original_mac_source_sha256": SOURCE_SHA256,
                "original_mac_git_blob_sha": SOURCE_GIT_BLOB,
                "original_mac_source_bytes": SOURCE_SIZE,
                "three_visible_pass": q["visible_3"],
                "twelve_hidden_pass": q["hidden_12"],
                "container_security_observed": observed,
                "model_calls_during_hosted_qa": 0,
                "source_executed_on_mac_or_chris": False,
                "separate_git_sink_credential_custody_proven": False,
                "future_unreviewed_generated_code_admitted": False,
                "autonomous_agent_proven": False,
                "production_authority": False,
                "elapsed_seconds": round(time.monotonic() - start, 3),
            }
        finally:
            if cid is not None and sandbox.DOCKER_ID.fullmatch(cid):
                sandbox.docker_command(["docker", "rm", "--force", cid], timeout=14)


def main() -> None:
    require(len(sys.argv) == 2 and sys.argv[1] in ("selftest", "run"),
            "ONLY_STATIC_SELFTEST_OR_HOSTED_RUN")
    record = selftest() if sys.argv[1] == "selftest" else run()
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refused, reviewed.Refused, sandbox.Refused,
            sandbox.hosted.Refused, OSError, ValueError, KeyError, TypeError,
            AssertionError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "reason": str(exc)[:180],
            "local_model_source_executed": False,
            "production_authority": False,
        }, sort_keys=True))
        raise SystemExit(2)
