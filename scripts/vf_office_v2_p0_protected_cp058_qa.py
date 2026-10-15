#!/usr/bin/env python3
"""#612/604 Phase-A pretrusted CP058 source QA extension, NO writer authority.

SELFTEST is STATIC only (no generated Python or guest execution).
RUN works ONLY from a previously merged protected-default-branch workflow_run
policy checkout after exact upstream Core CI; untrusted PR HEAD is DATA ONLY.
The model proposal is the one *historical* CP058 Qwen9B exact-type one-line
repair, deterministically reconstructed from an immutable quarantined source.
No general model executor, provider lease, Git credential, autonomous retry,
write effect or main promotion is admitted by a green receipt.
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

POLICY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(POLICY / "scripts"))
import vf_office_v2_p0_protected_base_c1_qa as base  # noqa: E402
import vf_office_v2_p0_hosted_container_boundary_lab as docker  # noqa: E402
import vf_office_v2_p0_hosted_new_source_review_lab as reviewer  # noqa: E402
import vf_office_v2_p0_diverse_task_fixtures as fixtures  # noqa: E402

SCHEMA = "velvetos.office-v2.p0-cp058-pretrusted-repair-qa.v1"
REQUEST_SCHEMA = "velvetos.office-v2.p0-cp058-repair-request.v1"
WORKFLOW = ".github/workflows/office-p0-protected-cp058-qa.yml"
ORIGINAL = ("docs/implementation/office-v2/phase2/"
            "quarantined-agent-sources-2026-10-10/windows_merge.py")
REQUEST = ("docs/implementation/office-v2/phase2/"
           "p0-612-protected-cp058-qa-request-2026-10-15.json")
CANDIDATE = ("docs/implementation/office-v2/phase2/"
             "quarantined-model-repairs-2026-10-15/"
             "windows-qwen9b-cp058-repaired.py.txt")
BEFORE_SHA = "999f8ae84cbca062a41297b6fadf6703ee69fa8a61e427a8441cd1a169c3b0a0"
AFTER_SHA = "544908a800b3546b9e5ee0bba57a6395b95f99a4aef6fd5d931e73e89631b5e3"
AFTER_BLOB = "e688462ca7a0e22f7977ea840f0c9a167c7f9b08"
OLD_LINE = b"        if not isinstance(start, int) or not isinstance(end, int):"
NEW_LINE = b"        if type(start) is not int or type(end) is not int:"
FIXTURE = "merge-windows-v1"
SOURCE_BYTES = 1914
VISIBLE_SHA = "c2f84a610eb78121b74e88c83057d79974b3cd98422d71cb554d6ec360e27747"
HIDDEN_SHA = "a5b648d4877772f081e528dbf380695f0ce0da47009a586797fcf0dccd8025cc"
EXPECTED_REQUEST = {
    "schema": REQUEST_SCHEMA,
    "task_id": "cp058-exact-int-subclass-repair-only",
    "source_path": CANDIDATE,
    "source_sha256": AFTER_SHA,
    "source_git_blob_sha1": AFTER_BLOB,
    "source_size_bytes": SOURCE_BYTES,
    "source_before_sha256": BEFORE_SHA,
    "model_provenance": "CP058_QWEN9B_UNATTESTED_STATIC_ONLY",
    "fixture": FIXTURE,
    "source_trusted_as_executable": False,
    "git_sink_write_authorized": False,
    "core_signed_lease_issued": False,
    "production_effects": False,
}


class Refuse(Exception):
    pass


def need(value: bool, reason: str) -> None:
    if not value:
        raise Refuse(reason)


def sha(buf: bytes) -> str:
    return hashlib.sha256(buf).hexdigest()


def blob(buf: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(buf)).encode() + b"\0" + buf).hexdigest()


def deterministic_pinned_repair() -> bytes:
    # Protected-main code + original data; never import/exec model-authored bytes.
    original = base.require_regular(POLICY, ORIGINAL, 4096)
    need(sha(original) == BEFORE_SHA and original.count(OLD_LINE) == 1,
         "IMMUTABLE_QUARANTINED_BASE_CHANGED")
    patched = original.replace(OLD_LINE, NEW_LINE, 1)
    need(len(patched) == SOURCE_BYTES and sha(patched) == AFTER_SHA
         and blob(patched) == AFTER_BLOB,
         "HISTORICAL_QWEN9B_REPAIR_BYTES_CHANGED")
    reviewer.reviewed_structure(patched, "windows_merge.py")
    return patched


def trusted_test_case() -> tuple[dict, dict]:
    row = fixtures.catalog()[FIXTURE]
    need(set(row) == {"target", "test", "source", "visible", "hidden",
                      "prompt", "golden"}
         and row["target"] == "windows_merge.py"
         and row["test"] == "tests/test_windows_merge.py"
         and sha(row["visible"].encode()) == VISIBLE_SHA
         and sha(row["hidden"].encode()) == HIDDEN_SHA,
         "PROTECTED_DEFAULT_BRANCH_HIDDEN_TESTS_DRIFT")
    entry = {"label": "cp058-pinned-qwen9b-repair",
             "fixture": FIXTURE, "sha256": AFTER_SHA,
             "test_sha256": VISIBLE_SHA, "hidden_sha256": HIDDEN_SHA,
             "expected_good": True}
    return entry, row


def request_exact(value: dict) -> None:
    base.exact(value, EXPECTED_REQUEST, "cp058_request")


def verified_candidate_data(candidate: Path) -> tuple[bytes, bytes]:
    request = base.require_regular(candidate, REQUEST, 2048)
    try:
        payload = json.loads(request.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise Refuse("NOT_EXACT_CP058_DATA_REQUEST")
    request_exact(payload)
    data = base.require_regular(candidate, CANDIDATE, 4096)
    need(data == deterministic_pinned_repair(),
         "CANDIDATE_NOT_EXACT_MODEL_REPAIR_BYTES")
    need(sha(data) == AFTER_SHA and blob(data) == AFTER_BLOB,
         "CANDIDATE_GIT_SOURCE_DIGEST_CHANGED")
    return request, data


def offline_selftest() -> dict:
    original = deterministic_pinned_repair()
    entry, _ = trusted_test_case()
    test_names = ["pinned_quarantined_original", "exact_CP058_model_patch",
                  "immutable_visible_and_hidden_fixtures"]
    request_exact(copy.deepcopy(EXPECTED_REQUEST))
    test_names.append("exact_data_only_request")
    for key, value in EXPECTED_REQUEST.items():
        claim = copy.deepcopy(EXPECTED_REQUEST)
        claim[key] = (not value if type(value) is bool
                      else value + "_forged" if type(value) is str
                      else value + 1)
        try:
            request_exact(claim)
        except base.Refused:
            test_names.append("request_field_denied_" + key)
        else:
            raise Refuse("FORGED_REQUEST_ACCEPTED_" + key)
    for name in ("write_token", "approval", "unknown_resume", "lease_epoch"):
        claim = dict(EXPECTED_REQUEST, **{name: True})
        try:
            request_exact(claim)
        except base.Refused:
            test_names.append("extra_effect_authority_denied")
        else:
            raise Refuse("ARBITRARY_REQUEST_GRANTS_AUTHORITY_" + name)
    altered = (
        original + b"\n", original[:-1], b"import os\n" + original,
        original.replace(NEW_LINE, OLD_LINE),
        original.replace(NEW_LINE, NEW_LINE.replace(b"type(start)", b"eval(start)")),
    )
    for changed in altered:
        need(changed != original and
             not (sha(changed) == AFTER_SHA and blob(changed) == AFTER_BLOB),
             "UNSAFE_SOURCE_MUTATION_NOT_REJECTED")
        test_names.append("mutated_generated_source_refused")
    image = "sha256:" + "a" * 64
    home = Path(tempfile.gettempdir()).resolve()
    scratch = home / "vf-cp058-synthetic-uncreated"
    canary = home / "vf-cp058-private-uncreated" / "canary.key"
    args = docker.docker_args(image, scratch, canary, entry)
    docker.assert_docker_plan(args, image, scratch, canary, entry)
    test_names.append("zero_write_guest_exact_args")
    for old, new in (
        ("--network=none", "--network=bridge"),
        ("--read-only", "--privileged"),
        ("--cap-drop=ALL", "--cap-add=SYS_ADMIN"),
        ("--user=65534:65534", "--user=0:0"),
        ("--ipc=none", "--ipc=host"),
        ("--pids-limit=32", "--pids-limit=4096"),
        ("--security-opt=no-new-privileges:true", "--privileged"),
        ("--memory=256m", "--memory=8g"),
    ):
        broken = list(args)
        broken[broken.index(old)] = new
        try: docker.assert_docker_plan(broken, image, scratch, canary, entry)
        except docker.Refused: test_names.append("insecure_guest_mutant_denied")
        else: raise Refuse("WEAKENED_GUEST_EXECUTOR_PASSED")
    need(len(test_names) == 35, "CP058_SELFTEST_COUNT_DRIFT")
    return {"schema": SCHEMA,
            "status": "PASS_CP058_PRETRUSTED_POLICY_OFFLINE_NO_EXECUTION",
            "tests": len(test_names), "repaired_source_sha256": AFTER_SHA,
            "repaired_source_git_blob": AFTER_BLOB,
            "hidden_test_sha256": HIDDEN_SHA,
            "candidate_model_code_executed": False,
            "docker_calls": 0, "model_calls": 0,
            "core_provider_lease": False,
            "git_writer_credential": False, "production_authority": False}


def hosted_run() -> dict:
    # Calling base's policy verifier also checks exact default-branch source
    # hashes, upstream Core CI id+successful head, both credential-free git
    # checkouts and GitHub's signed workflow_run payload.
    workspace, candidate, base_sha, head_sha, upstream = base.preflight_hosted()
    offline_selftest()
    need((POLICY / WORKFLOW).is_file()
         and base.git(POLICY, "hash-object", WORKFLOW) ==
             base.git(POLICY, "rev-parse", base_sha + ":" + WORKFLOW),
         "CP058_WORKFLOW_NOT_FROM_PROTECTED_MAIN")
    # The existing C1 preflight verifies its own trusted script/workflow.
    # Also pin EVERY newly imported CP058 policy/dependency file to the
    # protected-main Git tree, never to untrusted PR HEAD content.
    for trusted_path in (
        "scripts/vf_office_v2_p0_protected_cp058_qa.py",
        "scripts/vf_office_v2_p0_hosted_container_boundary_lab.py",
        "scripts/vf_office_v2_p0_hosted_new_source_review_lab.py",
        "scripts/vf_office_v2_p0_diverse_task_fixtures.py",
    ):
        need(base.git(POLICY, "hash-object", trusted_path) ==
             base.git(POLICY, "rev-parse", base_sha + ":" + trusted_path),
             "CP058_IMPORTED_POLICY_NOT_EXACT_PROTECTED_BASE_" +
             Path(trusted_path).name)
    request_path = candidate / REQUEST
    if not request_path.exists():
        return {"schema": SCHEMA,
                "status": "SKIP_NO_CP058_DATA_REQUEST",
                "trusted_policy_main_sha": base_sha,
                "untrusted_candidate_sha": head_sha,
                "upstream_core_run_id": upstream,
                "docker_calls": 0, "github_writes": 0,
                "production_authority": False}
    req, data = verified_candidate_data(candidate)
    entry, row = trusted_test_case()
    # Candidate code never imports on host. Run only as the Docker fixture.
    start = time.monotonic()
    image_ref = docker.EXPECTED_IMAGE_DIGEST
    need(image_ref.startswith("python@sha256:"),
         "OCI_IMAGE_DIGEST_NOT_PINNED")
    docker.docker_command(["docker", "version", "--format",
                           "{{.Server.Version}}"], timeout=12)
    docker.docker_command(["docker", "pull", "--quiet", image_ref], timeout=125)
    image = json.loads(docker.docker_command(
        ["docker", "image", "inspect", image_ref], timeout=12))[0]
    img_id = image["Id"]
    need(image_ref in image["RepoDigests"] and
         img_id.startswith("sha256:") and
         docker.SHA256.fullmatch(img_id[7:]),
         "UNTRUSTED_CONTAINER_IMAGE")
    with tempfile.TemporaryDirectory(prefix="vf-cp058-protected-qa-") as td, \
         tempfile.TemporaryDirectory(prefix="vf-cp058-host-secret-not-real-") as sec:
        work = Path(td)
        canary = Path(sec) / "synthetic-not-a-token.key"
        canary.write_text("SYNTHETIC_NOT_A_SECRET", encoding="ascii")
        source = work / row["target"]
        source.write_bytes(data)
        test = work / row["test"]
        test.parent.mkdir(parents=True)
        test.write_text(row["visible"], encoding="utf-8")
        hidden = work / "hidden.py"
        hidden.write_text(row["hidden"], encoding="utf-8")
        inner = work / "qa_inner.py"
        inner.write_text(docker.INNER, encoding="utf-8")
        for file in (source, test, hidden, inner):
            file.chmod(0o644)
        test.parent.chmod(0o755)
        work.chmod(0o755)
        need(sha(source.read_bytes()) == AFTER_SHA and
             blob(source.read_bytes()) == AFTER_BLOB,
             "GENERATED_SOURCE_WRITTEN_DIFFERENT_BYTES")
        argv = docker.docker_args(img_id, work, canary, entry)
        docker.assert_docker_plan(argv, img_id, work, canary, entry)
        cid = None
        try:
            cid = docker.docker_command(argv, timeout=18)
            need(docker.DOCKER_ID.fullmatch(cid), "DOCKER_ID_MALFORMED")
            security = docker.inspect_cid(cid, work, img_id)
            stdout = docker.docker_command(
                ["docker", "start", "--attach", cid], timeout=38)
            container = json.loads(docker.docker_command(
                ["docker", "inspect", cid], timeout=12))[0]["State"]
            need(container["Status"] == "exited" and
                 container["ExitCode"] == 0, "CP058_DOCKER_HIDDEN_QA_FAILED")
            records = [json.loads(line) for line in stdout.splitlines()
                       if line.startswith("{") and line.endswith("}")]
            need(len(records) == 1, "CP058_SINGLE_GUEST_RECEIPT")
            proof = records[0]
            for name in ("network_denied", "host_canary_invisible",
                         "no_docker_socket", "no_exported_github_token",
                         "uid_65534", "setuid_root_denied",
                         "read_only_root_and_mount", "tmpfs_only_write",
                         "visible_3", "hidden_12"):
                need(proof.get(name) is True, "CP058_SECURITY_OR_QA_" + name)
            need(proof.get("status") ==
                 "PASS_CONTAINER_ISOLATION_NEGATIVES_AND_QA"
                 and proof.get("source_sha256") == AFTER_SHA,
                 "CP058_GUEST_RECEIPT_SOURCE_DRIFT")
            need(verified_candidate_data(candidate) == (req, data)
                 and source.read_bytes() == data,
                 "CP058_DATA_CHANGED_DURING_HIDDEN_QA")
            return {"schema": SCHEMA,
                    "status": "PASS_PRETRUSTED_CP058_EXACT_REPAIR_3PLUS12",
                    "trusted_policy_main_sha": base_sha,
                    "untrusted_candidate_sha": head_sha,
                    "upstream_core_run_id": upstream,
                    "source_sha256": AFTER_SHA,
                    "source_git_blob_sha1": AFTER_BLOB,
                    "visible_3": True, "hidden_12": True,
                    "protected_hidden_test_sha256": HIDDEN_SHA,
                    "docker_container_security": security,
                    "head_policy_imported": False,
                    "user_host_model_code_executed": False,
                    "github_git_writes": 0, "provider_lease_ops": 0,
                    "git_writer_credential": False,
                    "production_authority": False,
                    "elapsed_seconds": round(time.monotonic() - start, 3)}
        finally:
            if cid and docker.DOCKER_ID.fullmatch(cid):
                docker.docker_command(["docker", "rm", "--force", cid],
                                      timeout=14)


def main() -> dict:
    need(len(sys.argv) == 2 and sys.argv[1] in ("selftest", "run"),
         "ONLY_OFFLINE_OR_PROTECTED_HOSTED_RUN")
    return offline_selftest() if sys.argv[1] == "selftest" else hosted_run()


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True))
    except (Refuse, base.Refused, reviewer.Refused, docker.Refused,
            docker.hosted.Refused, OSError, ValueError, AssertionError,
            KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:180],
                          "model_source_executed_on_user_host": False,
                          "github_git_writes": 0,
                          "production_authority": False}, sort_keys=True))
        raise SystemExit(2)
