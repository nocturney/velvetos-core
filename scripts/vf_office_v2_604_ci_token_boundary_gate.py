#!/usr/bin/env python3
"""Office #604: offline check of CI token boundary; no network or effects."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/check-all.yml"
TOKEN_REF = "$" + "{{ github.token }}"
DISPATCH_IF = "    if: " + "$" + "{{ github.event_name == 'workflow_dispatch' && inputs.execution != 'main_full' }}"
PR_IF = "    if: " + "$" + "{{ github.event_name == 'pull_request' }}"


class Refused(Exception):
    pass


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise Refused(reason)


def verify(source: str) -> None:
    need(source.count("\njobs:\n") == 1, "JOBS_BOUNDARY_DRIFT")
    head, jobs_text = source.split("\njobs:\n", 1)
    perms = re.findall(r"(?m)^permissions:\n((?:  [^\n]*\n)+)", head)
    need(len(perms) == 1 and perms[0].strip() == "contents: read",
         "GLOBAL_TOKEN_NOT_READ_ONLY")
    anchors = list(re.finditer(r"(?m)^  ([a-z][a-z0-9-]*):\s*$", jobs_text))
    jobs = {match.group(1): jobs_text[match.end():anchors[i+1].start()
                                    if i+1 < len(anchors) else len(jobs_text)]
            for i, match in enumerate(anchors)}
    need(len(jobs) == len(anchors), "DUPLICATE_JOB")
    need({"check-all", "publish-machine-precheck-status"} <= set(jobs),
         "REQUIRED_JOB_MISSING")
    test = jobs["check-all"]
    writer = jobs["publish-machine-precheck-status"]
    need("Run selected VelvetOS sensors" in test
         and "Run full VelvetOS sensor suite on main" in test,
         "TEST_JOB_SCOPE_CHANGED")
    need(test.count("uses: actions/checkout@v7") == 1
         and test.count("persist-credentials: false") == 1
         and "persist-credentials: true" not in test,
         "CHECKOUT_CREDENTIAL_PERSISTENCE")
    need(not re.search(r"(?m)^    permissions:\s*$", test),
         "TEST_JOB_PERMISSION_OVERRIDE")
    need(not re.search(r"(?i)statuses:\s*write|GH_TOKEN|github\.token|gh api", test),
         "TEST_JOB_STATUS_CREDENTIAL_EXPOSURE")
    for key, value in jobs.items():
        if key != "publish-machine-precheck-status":
            need(not re.search(r"(?i)statuses:\s*write", value),
                 "OTHER_JOB_WRITE_PERMISSION")
    need(re.search(r"(?m)^    needs: check-all\s*$", writer) is not None,
         "PUBLISH_NOT_GATED_BY_CHECK_ALL")
    need(DISPATCH_IF in writer, "PUBLISH_NOT_DISPATCH_ONLY")
    rights = re.findall(r"(?m)^    permissions:\n((?:      [^\n]*\n)+)", writer)
    need(len(rights) == 1 and rights[0].strip() == "statuses: write",
         "PUBLISH_NOT_STATUS_ONLY")
    need("runs-on: ubuntu-latest" in writer
         and ("GH_TOKEN: " + TOKEN_REF) in writer,
         "PUBLISH_IDENTITY_SCOPE")
    need("- uses:" not in writer and "python3 " not in writer,
         "PUBLISH_RUNS_UNTRUSTED_CODE")
    need("gh api --method POST" in writer
         and '"repos/$GITHUB_REPOSITORY/statuses/$GITHUB_SHA"' in writer
         and "-f state=success" in writer
         and "-f context=check-all" in writer,
         "STATUS_TARGET_OR_CONTEXT_DRIFT")


def selftest(source: str) -> dict:
    verify(source)
    cases = [
        ("checkout-persistence", source.replace(
            "persist-credentials: false", "persist-credentials: true", 1)),
        ("global-write", source.replace("permissions:\n  contents: read",
            "permissions:\n  contents: read\n  statuses: write", 1)),
        ("test-job-write", source.replace("  check-all:\n",
            "  check-all:\n    permissions:\n      statuses: write\n", 1)),
        ("test-job-token", source.replace("  check-all:\n",
            "  check-all:\n    env:\n      GH_TOKEN: " + TOKEN_REF + "\n", 1)),
        ("test-job-api", source.replace("  check-all:\n",
            "  check-all:\n    run: gh api repos/$GITHUB_REPOSITORY\n", 1)),
        ("missing-needs", source.replace("    needs: check-all\n", "", 1)),
        ("wrong-needs", source.replace(
            "    needs: check-all\n", "    needs: other\n", 1)),
        ("pr-publisher", source.replace(DISPATCH_IF, PR_IF, 1)),
        ("missing-status-write", source.replace(
            "      statuses: write\n", "      contents: read\n", 1)),
        ("publisher-checkout", source.replace(
            "  publish-machine-precheck-status:\n",
            "  publish-machine-precheck-status:\n    steps:\n"
            "      - uses: actions/checkout@v7\n", 1)),
        ("publisher-runs-code", source.replace(
            "  publish-machine-precheck-status:\n",
            "  publish-machine-precheck-status:\n"
            "    run: python3 scripts/worker.py\n", 1)),
        ("publisher-wrong-sha", source.replace(
            "statuses/$GITHUB_SHA", "statuses/$GITHUB_REF", 1)),
        ("publisher-false-green", source.replace(
            "-f state=success", "-f state=pending", 1)),
        ("publisher-wrong-context", source.replace(
            "-f context=check-all", "-f context=untrusted", 1)),
        ("missing-test", source.replace(
            "Run selected VelvetOS sensors", "Run altered sensors", 1)),
        ("extra-status-job", source.replace(
            "\njobs:\n", "\njobs:\n  other:\n"
            "    permissions:\n      statuses: write\n", 1)),
        ("duplicate-jobs", source + "\njobs:\n"),
    ]
    count = 0
    for name, modified in cases:
        need(modified != source, "MUTATION_NOT_APPLIED_" + name)
        try:
            verify(modified)
        except Refused:
            count += 1
        else:
            raise Refused("MUTATION_ACCEPTED_" + name)
    return {"status": "PASS_CI_TOKEN_BOUNDARY_OFFLINE",
            "negative_cases": len(cases), "negative_denials": count,
            "workflow_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "candidate_source_executed": False,
            "token_accessed": False,
            "core_lease_issued": False, "production_authority": False}


def main() -> None:
    need(len(sys.argv) == 2 and sys.argv[1] in ("verify", "selftest"),
         "ONLY_OFFLINE_VERIFY_OR_SELFTEST")
    source = WORKFLOW.read_text(encoding="utf-8")
    if sys.argv[1] == "selftest":
        result = selftest(source)
    else:
        verify(source)
        result = {"status": "PASS_CI_TOKEN_BOUNDARY_OFFLINE",
                  "workflow_sha256": hashlib.sha256(source.encode()).hexdigest(),
                  "token_accessed": False, "production_authority": False}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refused, OSError, ValueError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:150],
                          "token_accessed": False, "production_authority": False}))
        raise SystemExit(2)
