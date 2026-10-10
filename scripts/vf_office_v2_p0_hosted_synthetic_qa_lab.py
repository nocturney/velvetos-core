#!/usr/bin/env python3
"""#612 scoped GitHub-hosted, credential-free synthetic coding QA comparison.

selftest: PURE static source/contract checks, never executes generated code.
run: exclusively on a GitHub-hosted temporary Ubuntu Actions runner as a
diagnostic guard, with NO credentials, writes, scheduler, model or business data.
The environment guard is NOT a cryptographic runner identity or OS attestation.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

import vf_office_v2_p0_diverse_task_fixtures as fixtures

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "velvetos.office-v2.p0-hosted-quarantined-synthetic-qa.v0"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
SHA = re.compile(r"[0-9a-f]{64}\Z")
BASE = "docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10/"
SOURCES = (
    {
        "label": "mac-qwen4b-existing-tag",
        "path": BASE + "parallel-mac-tag-20261010.py",
        "sha256": "b2ec92fed514a5e0e37aeca31155fe0d04cdfde70a3d46fafeeb9a09b0ef1ccb",
        "fixture": "canonical-tag-v1",
        "target": "canonical_tag.py",
        "visible_sha256": "55ada6c9ae4bca3cba1633010795dae2e02dabed3071aca56ea1fdcede17d668",
        "hidden_sha256": "fd3b286041bfe835416ab14e89dc6b56195c807f01bcc9bbe843095c463009db",
    },
    {
        "label": "win-qwen9b-existing-merge",
        "path": BASE + "parallel-win-merge-20261010.py",
        "sha256": "e625ea816531000df82d15144f3155ebd59a868a2dd89c81c1f254115bafb2b9",
        "fixture": "merge-windows-v1",
        "target": "windows_merge.py",
        "visible_sha256": "c2f84a610eb78121b74e88c83057d79974b3cd98422d71cb554d6ec360e27747",
        "hidden_sha256": "a5b648d4877772f081e528dbf380695f0ce0da47009a586797fcf0dccd8025cc",
    },
)


class Refused(Exception):
    pass


def require(value, reason):
    if not value:
        raise Refused(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def manifest_check(entry):
    require(type(entry) is dict and entry in SOURCES
            and entry.get("path") in tuple(r["path"] for r in SOURCES)
            and entry.get("fixture") in fixtures.catalog(),
            "UNREGISTERED_OR_TAMPERED_GENERATED_SOURCE")
    fixture = fixtures.catalog()[entry["fixture"]]
    require(entry["target"] == fixture["target"] and
            entry["visible_sha256"] == sha(fixture["visible"].encode()) and
            entry["hidden_sha256"] == sha(fixture["hidden"].encode()),
            "FIXTURE_QA_BYTES_DRIFT")
    p = ROOT / entry["path"]
    require(p.is_file() and not p.is_symlink() and
            1 <= p.stat().st_size <= 16384 and
            sha(p.read_bytes()) == entry["sha256"],
            "GENERATION_OR_SOURCE_SHA_CHANGED")
    return p, fixture


def runner_context_check(env, expected_root=ROOT):
    # These are defense-in-depth CI context checks, not OS identity proof.
    require(env.get("GITHUB_ACTIONS") == "true"
            and env.get("RUNNER_ENVIRONMENT") == "github-hosted"
            and env.get("RUNNER_OS") == "Linux"
            and env.get("GITHUB_REPOSITORY") == "nocturney/velvetos-core"
            and env.get("GITHUB_EVENT_NAME") in ("pull_request", "workflow_dispatch"),
            "GH_HOSTED_LAB_CONTEXT_NOT_PRESENT")
    require(not any(env.get(name) for name in (
                "GITHUB_TOKEN", "GH_TOKEN", "GIT_ASKPASS", "SSH_ASKPASS",
                "AWS_ACCESS_KEY_ID", "GOOGLE_APPLICATION_CREDENTIALS")),
            "POSSIBLE_EXPORTED_CREDENTIAL")
    workspace = env.get("GITHUB_WORKSPACE", "")
    require(bool(workspace) and
            Path(workspace).resolve() == Path(expected_root).resolve() and
            "/home/runner/work/" in expected_root.as_posix(),
            "RUNNER_WORKSPACE_NOT_EXPECTED_EPHEMERAL_LOCATION")
    return True


def no_persisted_checkout_auth():
    cmd = ["git", "-C", str(ROOT), "config", "--local", "--get-regexp",
           r"^http[.].*[.]extraheader$"]
    proc = subprocess.run(cmd, capture_output=True, timeout=7,
                          env={"PATH":os.environ.get("PATH", "/usr/bin:/bin")})
    require(proc.returncode == 1, "CHECKOUT_HAS_AUTH_EXTRAHEADER_OR_GIT_FAILURE")
    return True


def limited_child():
    # Imported only on the admitted Linux runner; Windows static QA must not
    # need the POSIX-only resource module.
    import resource
    # The source is pinned; these are bounded process resources, not a VM.
    resource.setrlimit(resource.RLIMIT_CPU, (7, 7))
    resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))


def qa_once(code, fixture):
    """Execute only in an isolated temporary repository-free QA directory."""
    with tempfile.TemporaryDirectory(prefix="vf-office-p0-hosted-synthetic-") as temp:
        work = Path(temp)
        target = work / fixture["target"]
        test = work / fixture["test"]
        test.parent.mkdir(parents=True)
        target.write_bytes(code)
        test.write_text(fixture["visible"], encoding="utf-8")
        home = work / "home"
        home.mkdir()
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(home),
            "TMPDIR": temp,
            "LANG": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
        }
        def bounded(argv):
            return subprocess.run(argv, cwd=work, env=env,
                                  capture_output=True, timeout=19,
                                  stdin=subprocess.DEVNULL,
                                  preexec_fn=limited_child)
        unit = bounded([sys.executable, "-B", "-m", "unittest", "discover",
                        "-s", "tests", "-q"])
        hidden = bounded([sys.executable, "-B", "-c", fixture["hidden"]])
        return {
            "visible_3": (unit.returncode == 0 and
                          b"Ran 3 tests" in unit.stderr),
            "hidden_12": (hidden.returncode == 0 and
                          hidden.stdout.strip() == b"QA_HIDDEN_12_PASS"),
            "visible_exit": unit.returncode,
            "hidden_exit": hidden.returncode,
            "source_sha256": sha(code),
            "test_sha256": sha(test.read_bytes()),
        }


def run():
    runner_context_check(os.environ)
    no_persisted_checkout_auth()
    before = [(r["path"], sha((ROOT / r["path"]).read_bytes())) for r in SOURCES]
    starts = time.monotonic()
    results = []
    for entry in SOURCES:
        path, fixture = manifest_check(entry)
        observed = qa_once(path.read_bytes(), fixture)
        require(observed["visible_3"] is True and
                observed["hidden_12"] is True and
                observed["source_sha256"] == entry["sha256"] and
                observed["test_sha256"] == entry["visible_sha256"],
                "GENERATED_CODE_INDEPENDENT_QA_FAILED_" + entry["label"])
        results.append({"label": entry["label"], **observed})
    # Negative control executes ONLY the known public fixture seed; it must
    # actually FAIL QA and is never counted as another model output.
    broken = fixtures.catalog()["canonical-tag-v1"]
    negative = qa_once(broken["source"].encode("utf-8"), broken)
    require(negative["visible_3"] is False and negative["hidden_12"] is False,
            "BROKEN_PUBLIC_SEED_FALSE_POSITIVE")
    after = [(r["path"], sha((ROOT / r["path"]).read_bytes())) for r in SOURCES]
    require(before == after, "GENERATED_SOURCE_MODIFIED")
    report = {
        "schema": SCHEMA, "status": "PASS_GITHUB_HOSTED_SYNTHETIC_QA_ONLY",
        "issue": ISSUE, "utc": datetime.now(timezone.utc).isoformat(),
        "runner_os": os.environ["RUNNER_OS"],
        "runner_environment": os.environ["RUNNER_ENVIRONMENT"],
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "source_hashes_pinned": True, "git_persisted_credential_absent": True,
        "synthetic_source_qa": results,
        "negative_seed_qa_rejected": True,
        "accepted_existing_sources": len(results),
        "accepted_new_algorithms": 0,
        "elapsed_seconds": round(time.monotonic() - starts, 3),
        "model_invocations": 0, "additional_paid_api_usd": 0,
        "production_authority": False,
        "github_write_token_present": False,
        "production_secret_present": False,
        "os_isolation_cryptographically_attested": False,
        "arbitrary_untrusted_code_egress_constrained": False,
        "exclusive_git_sink_credential_custody_proven": False,
        "local_worker_execution_unblocked": False,
        "autonomous_worker_pr_proven": False,
        "new_scheduler": False,
    }
    print(json.dumps(report, sort_keys=True))
    return 0


def selftest():
    # Pure local path: no generated code imports, QA child, model, network, Git
    # effect, hosted-runner spoof or auth/runner probe.
    cases = []
    for item in SOURCES:
        manifest_check(item)
        cases.append("pinned_" + item["label"])
    negative_cases = (
        ("wrong_sha", lambda x: x.update(sha256="0" * 64)),
        ("wrong_path", lambda x: x.update(path="/tmp/candidate.py")),
        ("wrong_fixture", lambda x: x.update(fixture="other")),
        ("wrong_target", lambda x: x.update(target="customer.py")),
        ("wrong_visible", lambda x: x.update(visible_sha256="f" * 64)),
        ("wrong_hidden", lambda x: x.update(hidden_sha256="f" * 64)),
        ("false_model", lambda x: x.update(model="paid-api")),
        ("false_token", lambda x: x.update(authority="GITHUB_WRITE")),
    )
    for name, mutate in negative_cases:
        fake = copy.deepcopy(SOURCES[0])
        mutate(fake)
        try: manifest_check(fake)
        except Refused: cases.append("denied_" + name)
        else: raise AssertionError("FALSE_GENERATED_SOURCE_ALLOWED_" + name)
    valid = {"GITHUB_ACTIONS": "true", "RUNNER_ENVIRONMENT": "github-hosted",
             "RUNNER_OS": "Linux", "GITHUB_REPOSITORY": "nocturney/velvetos-core",
             "GITHUB_EVENT_NAME": "pull_request",
             "GITHUB_WORKSPACE": "/home/runner/work/velvetos-core/velvetos-core"}
    # Test the SHAPE of an approved CI context with a synthetic expected path.
    # This does not probe the actual host or confer runtime authorization.
    fake_root = Path("/home/runner/work/velvetos-core/velvetos-core")
    runner_context_check(valid, expected_root=fake_root)
    cases.append("synthetic_hosted_context_shape_only")
    wrong_workspace = dict(valid, GITHUB_WORKSPACE="/home/runner/work/other/other")
    try: runner_context_check(wrong_workspace, expected_root=fake_root)
    except Refused: cases.append("wrong_workspace_denied")
    else: raise AssertionError("FOREIGN_RUNNER_WORKSPACE_ALLOWED")
    for name, changes in (
        ("not_actions", {"GITHUB_ACTIONS": "false"}),
        ("selfhost", {"RUNNER_ENVIRONMENT": "self-hosted"}),
        ("bad_os", {"RUNNER_OS": "Windows"}),
        ("foreign_repo", {"GITHUB_REPOSITORY": "other/repo"}),
        ("pr_target", {"GITHUB_EVENT_NAME": "pull_request_target"}),
        ("token", {"GH_TOKEN": "synthetic-do-not-use"}),
        ("cloud_creds", {"AWS_ACCESS_KEY_ID": "FAKE"}),
    ):
        invalid = dict(valid, **changes)
        try: runner_context_check(invalid, expected_root=fake_root)
        except Refused: cases.append("denied_" + name)
        else: raise AssertionError("FALSE_RUNNER_CONTEXT_ALLOWED_" + name)
    require(len(cases) == 19, "HOSTED_QA_CASES_MISSING")
    return {"status": "PASS_MODEL_FREE_STATIC_ONLY",
            "tests": len(cases), "cases": cases,
            "generated_source_subprocesses": 0,
            "model_invocations": 0, "git_write_calls": 0,
            "production_authority": False,
            "runner_isolation_proven_locally": False}


def main():
    require(len(sys.argv) == 2 and sys.argv[1] in ("selftest", "run"),
            "EXPECTED_SELFTEST_OR_RUN")
    if sys.argv[1] == "selftest":
        print(json.dumps(selftest(), sort_keys=True))
        return 0
    return run()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Refused, OSError, ValueError, KeyError,
            subprocess.TimeoutExpired, AssertionError) as err:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(err)[:175],
                          "production_authority": False,
                          "git_write_calls": 0}, sort_keys=True))
        raise SystemExit(2)
