#!/usr/bin/env python3
"""Read-only cross-platform byte-integrity gate for Git-index source/receipts.

No network, code generation, Git writes, models, business or OS configuration.
The 11 original-byte historical blobs (7 non-LF, 4 LF) remain exact.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = (".py", ".json", ".md")
HISTORICAL_RAW = {
    "docs/implementation/office-v2/phase0/authority-map-v0.1.json": "i/crlf",
    "docs/implementation/office-v2/phase0/credential-trust-classes-v0.json": "i/crlf",
    "docs/implementation/office-v2/phase3b/production-promotion-v0.json": "i/crlf",
    "packages/vfharness/devtools/creative-craft/evals/fixtures/manifest.json": "i/crlf",
    "packages/vfharness/devtools/creative-craft/skill/evals/fixtures/manifest.json": "i/crlf",
    "packages/velvetos/policy/sensor-registry.json": "i/mixed",
    "docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10/canonical_tag.py": "i/lf",
    "docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10/parallel-mac-tag-20261010.py": "i/lf",
    "docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10/parallel-win-merge-20261010.py": "i/crlf",
    "docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10/windows_merge.py": "i/lf",
    "docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10/windows_merge_exact_int_v3.py": "i/lf",
}


class Refused(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise Refused(reason)


def check_row(row):
    """Analyze one NUL-delimited git ls-files --eol -z record."""
    parts = row.split("\t", 1)
    require(len(parts) == 2, "BAD_GIT_EOL_RECORD")
    metadata, name = parts
    require(name and "\n" not in name and "\r" not in name, "BAD_GIT_PATH")
    if not name.endswith(EXTENSIONS):
        return None
    atoms = metadata.split()
    require(len(atoms) >= 3 and atoms[2].startswith("attr/"),
            "BAD_GIT_EOL_METADATA")
    indexed, working = atoms[0], atoms[1]
    attrs = [atoms[2][5:]] + atoms[3:]
    if name in HISTORICAL_RAW:
        require(indexed == HISTORICAL_RAW[name],
                "HISTORICAL_ORIGINAL_INDEX_EOL_CHANGED:" + name)
        require(working == "w/" + indexed[2:],
                "HISTORICAL_ORIGINAL_WORKTREE_BYTES_CHANGED:" + name)
        require("-text" in attrs and "eol=lf" not in attrs and "eol=crlf" not in attrs,
                "HISTORICAL_ORIGINAL_GIT_EOL_POLICY_CHANGED:" + name)
        return "historical_bytes_preserved"
    require(indexed in ("i/lf", "i/none"),
            "UNREVIEWED_NON_LF_INDEX_BLOB:" + name)
    require(working == ("w/lf" if indexed == "i/lf" else "w/none"),
            "WORKTREE_BYTES_DIFFER_FROM_INDEX:" + name)
    require("text" in attrs and "eol=lf" in attrs,
            "LF_POLICY_NOT_EXPLICIT:" + name)
    return "empty_source" if indexed == "i/none" else "lf_exact"


def selftest():
    cases = [
        ("i/lf    w/lf    attr/text eol=lf\ttrusted.py", True),
        ("i/none  w/none  attr/text eol=lf\tempty.py", True),
        ("i/lf    w/crlf  attr/text eol=lf\ttrusted.json", False),
        ("i/lf    w/lf    attr/\ttrusted.md", False),
        ("i/crlf  w/crlf  attr/-text\tnew-unreviewed.json", False),
        ("i/lf    w/lf    attr/-text\ttrusted.py", False),
        ("i/crlf  w/crlf  attr/-text\tdocs/implementation/office-v2/phase0/authority-map-v0.1.json", True),
        ("i/crlf  w/lf    attr/-text\tdocs/implementation/office-v2/phase0/authority-map-v0.1.json", False),
        ("i/crlf  w/crlf  attr/text eol=lf\tdocs/implementation/office-v2/phase0/authority-map-v0.1.json", False),
        ("i/lf    w/lf    attr/-text\tdocs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10/canonical_tag.py", True),
        ("i/mixed w/mixed attr/-text\tpackages/velvetos/policy/sensor-registry.json", True),
        ("i/lf    w/lf    attr/-text\tpackages/velvetos/policy/sensor-registry.json", False),
        ("i/lf    w/lf    attr/text eol=lf\tother.xml", True),
    ]
    for item, accept in cases:
        try:
            check_row(item)
        except Refused:
            require(not accept, "VALID_SOURCE_POLICY_REJECTED")
        else:
            require(accept, "UNSAFE_SOURCE_POLICY_ACCEPTED")
    return {"status": "PASS_CORE_EOL_STATIC_NEGATIVE_TESTS",
            "tests": len(cases), "git_calls": 0,
            "code_executions": 0, "git_writes": 0,
            "production_authority": False}


def verify():
    selftest()
    result = subprocess.run(["git", "ls-files", "--eol", "-z"],
                            cwd=str(ROOT), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=20)
    require(result.returncode == 0, "GIT_INDEX_READ_ONLY_QUERY_FAILED")
    require(result.stdout.endswith(b"\0"), "INCOMPLETE_GIT_EOL_STREAM")
    stats = {"lf_exact": 0, "empty_source": 0,
             "historical_bytes_preserved": 0}
    found = set()
    for part in result.stdout[:-1].split(b"\0"):
        line = part.decode("utf-8", errors="strict")
        state = check_row(line)
        if state is not None:
            stats[state] += 1
            path = line.split("\t", 1)[1]
            if path in HISTORICAL_RAW:
                found.add(path)
    require(found == set(HISTORICAL_RAW), "MISSING_HISTORICAL_NON_LF_BLOB")
    require(stats["lf_exact"] > 1000 and
            stats["historical_bytes_preserved"] == len(HISTORICAL_RAW),
            "CORE_EOL_SCOPE_INCOMPLETE")
    return {"status": "PASS_CORE_INDEX_WORKTREE_EOL_BYTE_INTEGRITY",
            "indexed_text_files": sum(stats.values()),
            **stats, "static_negative_tests": 13,
            "git_writes": 0, "models": 0,
            "production_authority": False}


def main():
    require(len(sys.argv) == 2 and sys.argv[1] in ("selftest", "verify"),
            "EXPECTED_SELFTEST_OR_VERIFY")
    print(json.dumps(selftest() if sys.argv[1] == "selftest" else verify(),
                     sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refused, OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:220],
                          "production_authority": False}, sort_keys=True))
        raise SystemExit(2)
