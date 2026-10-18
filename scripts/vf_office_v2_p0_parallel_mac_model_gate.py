#!/usr/bin/env python3
"""#612 independent bounded QA for quarantined MODEL_OUTPUT on another host.

Read-only to the core repo. Python model-generated source is pinned by SHA
and reviewed; execute only in a disposable independent tempfile using the
already canonical 3-visible + 12-hidden benchmark QA. No model invocation,
scheduler, lease, GitHub effect, production privilege or auto-recovery.
"""
import hashlib
import json
from pathlib import Path
import sys
import vf_office_v2_p0_diverse_task_fixtures as fixture

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10" / "parallel-mac-tag-20261010.py"
SHA256 = "b2ec92fed514a5e0e37aeca31155fe0d04cdfde70a3d46fafeeb9a09b0ef1ccb"
TASK_ID = "p0-diverse-run-mac-speed-tag-20261010-c"
HOST = "MacMiniOffice.local"
MODEL = "qwen3.5:4b"
FIXTURE = "canonical-tag-v1"

def run():
    if not TARGET.is_file() or TARGET.is_symlink():
        raise RuntimeError("MODEL_OUTPUT_MISSING_OR_SYMLINK")
    data = TARGET.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise RuntimeError("REFUSE_UNPINNED_MODEL_SOURCE")
    if data.decode("utf-8").encode("utf-8") != data:
        raise RuntimeError("MODEL_SOURCE_NONUTF8")
    spec = fixture.catalog()[FIXTURE]
    fixture.check_fixture(FIXTURE, spec)
    qa = fixture.replay(spec, data.decode("utf-8"), expected_pass=True)
    baseline = fixture.replay(spec, spec["source"], expected_pass=False)
    if (qa["pass"] is not True
            or qa["unit_exit"] != 0 or qa["hidden_exit"] != 0
            or qa["source_sha256"] != SHA256
            or baseline["pass"] is not False):
        raise RuntimeError("INDEPENDENT_REPLAY_NOT_PROVEN")
    return {
        "schema": "vf.office-v2.p0-quarantined-model-artifact-qa.v1",
        "status": "PASS_QUARANTINED_3_VISIBLE_12_HIDDEN",
        "producer_task_id": TASK_ID,
        "producer_host": HOST,
        "producer_model": MODEL,
        "fixture": FIXTURE,
        "source_sha256": SHA256,
        "independent_qa_visible_tests": 3,
        "independent_qa_hidden_cases": 12,
        "seed_negative_control_fails_as_expected": True,
        "model_executed_by_this_gate": False,
        "real_github_writer_fenced": False,
        "autonomous_pr_authority": False,
        "production_authority": False,
        "github_writes": 0,
        "paid_model_calls": 0,
        "scheduler_created": False,
    }

if __name__ == "__main__":
    try:
        if sys.argv[1:] not in (["verify"], ["selftest"]):
            raise ValueError("EXPLICIT_VERIFY_OR_SELFTEST_ONLY")
        print(json.dumps(run(), sort_keys=True))
    except Exception as error:
        print(json.dumps({"status": "FAIL_CLOSED",
                          "reason": type(error).__name__,
                          "production_authority": False}, sort_keys=True))
        raise SystemExit(1)
