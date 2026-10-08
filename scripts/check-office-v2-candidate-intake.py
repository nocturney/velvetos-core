#!/usr/bin/env python3
"""Deterministic negative controls for the ONE canonical Office v2 repo intake."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path

MODULE = Path(__file__).with_name("vf_office_v2_candidate_intake.py")
spec = importlib.util.spec_from_file_location("vf_office_v2_candidate_intake", MODULE)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def equal(a, b):
    assert a == b, (a, b)


def denied(fn, expected=None):
    try:
        fn()
    except p.IntakeRejected as exc:
        if expected is not None:
            equal(str(exc), expected)
        return
    raise AssertionError("accepted invalid input")


def main():
    tests = 0
    def run(fn):
        nonlocal tests
        fn()
        tests += 1

    source = {"schema": "velvetos.office-v2.repo-link-intake.v0", "items": [
        {"url": "https://GitHub.com/SomeOrg/Repo.git/", "origin_ref": "source-001"},
        {"url": "https://www.github.com/someorg/repo", "origin_ref": "source-002"},
        {"url": "https://github.com/Else/Tool", "origin_ref": "source-003"}
    ]}
    registry = {"schema": p.REGISTRY_SCHEMA, "candidate_count": 1, "items": [
        {"candidate_id": "existing-tool", "evidence_refs": ["https://github.com/else/tool/releases"]}
    ]}
    receipt = p.build(source, registry, "a" * 64, "b" * 64)
    run(lambda: equal(receipt["source_rows"], 3))
    run(lambda: equal(receipt["unique_repositories"], 2))
    run(lambda: equal(receipt["alias_rows"], 1))
    run(lambda: equal(receipt["queue"][0]["review_state"], "EXISTING_CANONICAL_CANDIDATE"))
    run(lambda: equal(receipt["queue"][1]["review_state"], "TRIAGE_PENDING_NO_ADMISSION"))
    run(lambda: equal(receipt["queue"][1]["aliases"][0]["origin_ref"], "source-001"))
    run(lambda: equal(p.verify(source, registry, receipt, "a" * 64, "b" * 64)["status"], "PASS"))

    for bad in [
        "http://github.com/org/repo", "https://notgithub.com/org/repo",
        "https://github.com:443/org/repo", "https://user@github.com/org/repo",
        "https://github.com/org/repo?token=x", "https://github.com/org/repo#x",
        "https://github.com/org/repo/tree/main", "https://github.com/org",
        "https://github.com/org/%2e%2e", "https://github.com/org/.",
        "https://github.com/org/repo%2fother", "https://github.com/org/repo\n",
        "ftp://github.com/org/repo", "https://github.com/org/repo//extra",
        "https://github.com/org/repo/subdir",
    ]:
        run(lambda bad=bad: denied(lambda: p.normalize_repo_url(bad)))

    bad = copy.deepcopy(source)
    bad["items"][1]["origin_ref"] = "source-001"
    run(lambda: denied(lambda: p.build(bad, registry, "a"*64, "b"*64),
                       "INVALID_OR_DUPLICATE_PROVENANCE"))
    bad = copy.deepcopy(source)
    bad["items"][1]["url"] = "https://evil.com/foo/bar"
    run(lambda: denied(lambda: p.build(bad, registry, "a"*64, "b"*64)))
    bad = copy.deepcopy(source)
    bad["items"][1]["extra"] = "something"
    run(lambda: denied(lambda: p.build(bad, registry, "a"*64, "b"*64),
                       "INVALID_SOURCE_ROW"))
    bad = copy.deepcopy(registry)
    bad["items"].append({"candidate_id": "existing-tool", "evidence_refs": ["https://github.com/dup/x"]})
    bad["candidate_count"] += 1
    run(lambda: denied(lambda: p.build(source, bad, "a"*64, "b"*64),
                       "DUPLICATE_CANONICAL_CANDIDATE_ID"))
    bad = copy.deepcopy(receipt)
    bad["queue"][1]["aliases"].pop()
    run(lambda: denied(lambda: p.verify(source, registry, bad, "a"*64, "b"*64),
                       "RECEIPT_TAMPERED"))
    bad = copy.deepcopy(receipt)
    run(lambda: denied(lambda: p.verify(source, registry, bad, "a"*64, "c"*64),
                       "RECEIPT_STALE_OR_MISMATCHED"))
    bad = copy.deepcopy(receipt)
    bad["runtime_authority"] = True
    bad["receipt_sha256"] = p.digest({k:v for k,v in bad.items() if k != "receipt_sha256"})
    run(lambda: denied(lambda: p.verify(source, registry, bad, "a"*64, "b"*64),
                       "RECEIPT_STALE_OR_MISMATCHED"))
    bad = copy.deepcopy(registry)
    bad["items"].append({"candidate_id": "another", "evidence_refs": ["https://github.com/else/tool/blob/main/LICENSE"]})
    bad["candidate_count"] += 1
    run(lambda: equal(p.build(source, bad, "a"*64, "b"*64)["queue"][0]["review_state"],
                      "BLOCKED_AMBIGUOUS_EXISTING_CANDIDATES"))
    bad = copy.deepcopy(registry)
    bad["candidate_count"] += 1
    run(lambda: denied(lambda: p.build(source, bad, "a"*64, "b"*64),
                       "CANONICAL_REGISTRY_COUNT_DRIFT"))
    run(lambda: equal(p.normalize_repo_url("https://github.com/X/Y/releases/v1", evidence_link=True),
                      "https://github.com/x/y"))
    run(lambda: denied(lambda: p.normalize_repo_url("https://github.com/X/Y/user-security", evidence_link=True)))
    print(json.dumps({"status": "PASS", "cases": tests, "network_calls": 0,
                      "new_runtime_authority": False, "paid_model_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
