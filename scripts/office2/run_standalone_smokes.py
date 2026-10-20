#!/usr/bin/env python3
"""Report the 2026-10-19 Office 2.0 standalone smoke record. Report only.

This helper runs no smoke. It installs nothing, starts no process, opens no
socket and reads no environment secret. It prints the reported versions and the
path of the record. The results in that record are author-reported cloud-VM
output; no log is committed, and this helper does not verify them.

--execute is refused with exit 2 on every input. There is no flag or
environment variable that makes this helper run a smoke. A future run needs
its own reviewed runbook.

check-all discovers only scripts/check-*.py, so it does not run this file.
The offline checks are in scripts/office2/test_run_standalone_smokes.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "office2" / "standalone-candidate-tests-2026-10-19.md"
DOC_REL = "docs/office2/standalone-candidate-tests-2026-10-19.md"

STATUS = "REPORT_ONLY"
SMOKES_RUN_BY_HELPER = 0
RESULT_PROVENANCE = "AUTHOR_REPORTED_UNVERIFIED"
EXECUTE_REFUSAL = "EXECUTE_UNSUPPORTED"

# Author-reported 2026-10-19 versions, NOT a reproducible pin/lock manifest.
# Most direct install requests named a version; iFixAi was installed unpinned.
# No transitive dependency lock, downloadable binary hashes, or run receipt is committed.
REPORTED_VERSIONS = (
    "langgraph==1.2.16",
    "langgraph-checkpoint==4.3.0",
    "crewai==1.15.28",
    "autogen-core==0.7.5",
    "dbos==3.3.0",
    "pydantic-ai==2.57.0",
    "litellm==1.88.6",
    "agent-framework-core==1.22.0",
    "ifixai 4.2.0 (observed after unpinned install)",
    "promptfoo@0.124.1",
    "temporal CLI v1.9.1",
    "goose v1.55.0",
    "opencode v1.19.3",
)

USAGE = "usage: run_standalone_smokes.py [--json]"


def report() -> dict[str, object]:
    return {
        "status": STATUS,
        "doc": DOC_REL,
        "doc_present": DOC.is_file(),
        "smokes_run_by_helper": SMOKES_RUN_BY_HELPER,
        "result_provenance": RESULT_PROVENANCE,
        "reported_versions": list(REPORTED_VERSIONS),
        "reproducible_lock": False,
    }


def main(argv: list[str]) -> int:
    if "--execute" in argv:
        print(EXECUTE_REFUSAL + ": this helper is report only and runs no smoke.", file=sys.stderr)
        print("Nothing was installed, started or checked.", file=sys.stderr)
        return 2
    unknown = [arg for arg in argv if arg != "--json"]
    if unknown:
        print(USAGE, file=sys.stderr)
        print("unknown argument: " + unknown[0], file=sys.stderr)
        return 2
    data = report()
    if not data["doc_present"]:
        print("missing " + DOC_REL, file=sys.stderr)
        return 1
    if "--json" in argv:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    print("status: " + STATUS)
    print("record: " + DOC_REL)
    print("smokes run by this helper: 0")
    print("results: author-reported, unverified. No log is committed.")
    print("versions (NOT a reproducible lock): " + ", ".join(REPORTED_VERSIONS))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
