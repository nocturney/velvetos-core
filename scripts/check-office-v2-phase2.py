#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"
FIXTURES = P2 / "golden-fixtures"

REQUIRED = [
    P2 / "README.md",
    P2 / "candidate-lifecycle-v0.json",
    P2 / "candidate-registry.schema.json",
    P2 / "candidate-registry-v0.json",
    P2 / "admission-policy-v0.md",
    P2 / "scorecard.schema.json",
    P2 / "golden-fixture-contract.schema.json",
    P2 / "fixture-adapter-receipt.schema.json",
    P2 / "pattern-adoption-receipt.schema.json",
    P2 / "research-freeze-record.schema.json",
    P2 / "p0-shortlists-v0.json",
    ROOT / "scripts" / "vf_office_v2_golden_fixture.py",
]

EXPECTED_FORWARD = [
    "DISCOVERED", "RESEARCHED", "CANDIDATE", "ADMITTED", "LAB",
    "SHADOW", "PILOT", "PRODUCTION", "FALLBACK", "RETIRED",
]
EXPECTED_EXIT = [
    "REJECTED_WITH_REASON", "BENCHMARKED_AND_LOST",
    "SUPERSEDED", "DEFERRED_WITH_REASON",
]
EXPECTED_FIXTURES = {
    "instagram-request-publish-live-verify",
    "customer-quote-production-ready-paid",
    "3d-asset-dcc-slice-artifact",
    "agent-approval-effect-reconciliation",
    "long-job-crash-resume",
    "morning-brief-compose-send-verify",
}


def fail(msg: str) -> None:
    print("FAIL " + msg, file=sys.stderr)
    raise SystemExit(1)


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")


def main() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.is_file()]
    if missing:
        fail("missing Phase 2 files: " + ", ".join(missing))

    lifecycle = load(P2 / "candidate-lifecycle-v0.json")
    if lifecycle.get("forward_states") != EXPECTED_FORWARD:
        fail("candidate forward lifecycle mismatch")
    if lifecycle.get("exit_verdicts") != EXPECTED_EXIT:
        fail("candidate exit verdicts mismatch")

    registry = load(P2 / "candidate-registry-v0.json")
    if registry.get("status") != "CLOSED_IMPORT":
        fail("candidate registry import is not closed")
    items = registry.get("items") or []
    if len(items) < 68:
        fail(f"candidate registry incomplete: {len(items)} < 68")
    if registry.get("source_item_count") != 68 or registry.get("imported_source_item_count") != 68:
        fail("candidate registry must preserve the complete 68-item source import")
    source_ids = [x.get("source_item_id") for x in items if x.get("source_item_id") is not None]
    if len(source_ids) != 68 or len(set(source_ids)) != 68:
        fail("candidate registry source_item_id coverage is not exactly 68 unique items")
    ids = [x.get("candidate_id") for x in items]
    if len(ids) != len(set(ids)):
        fail("candidate registry ids are not unique")
    meaningful = set(lifecycle.get("decision_verdicts") or []) | set(EXPECTED_EXIT)
    for item in items:
        if item.get("lifecycle_state") not in set(EXPECTED_FORWARD):
            fail("invalid lifecycle state for " + str(item.get("candidate_id")))
        if item.get("decision_verdict") not in meaningful:
            fail("missing meaningful verdict for " + str(item.get("candidate_id")))
        if not item.get("evidence_refs"):
            fail("candidate missing evidence refs: " + str(item.get("candidate_id")))

    shortlists = load(P2 / "p0-shortlists-v0.json")
    lanes = shortlists.get("lanes") or []
    if not lanes:
        fail("P0 shortlists are empty")
    known = set(ids)
    for lane in lanes:
        incumbent = lane.get("incumbent")
        challengers = lane.get("challengers") or []
        if not incumbent or incumbent not in known:
            fail("shortlist incumbent missing from registry: " + str(lane.get("lane_id")))
        if not 2 <= len(challengers) <= 3:
            fail("shortlist must have 2-3 challengers: " + str(lane.get("lane_id")))
        if lane.get("lane_id") == "durable-execution":
            if lane.get("winner") != "candidate-restate":
                fail("closed durable-execution lane must record Restate winner")
            if lane.get("fallback") != "candidate-temporal":
                fail("closed durable-execution lane must record Temporal fallback")
            if lane.get("freeze_state") != "FROZEN_AFTER_PHASE3A_BAKEOFF":
                fail("closed durable-execution lane freeze state mismatch")
            if lane.get("verdict_receipt") != "docs/implementation/office-v2/phase3/durable-execution-verdict-v0.json":
                fail("closed durable-execution lane verdict provenance missing")
        elif lane.get("winner") is not None:
            fail("open pre-benchmark shortlist must not declare a winner: " + str(lane.get("lane_id")))
        if any(c not in known for c in challengers):
            fail("shortlist challenger missing from registry: " + str(lane.get("lane_id")))

    fixture_files = sorted(FIXTURES.glob("*.json"))
    fixture_ids = set()
    runner = ROOT / "scripts" / "vf_office_v2_golden_fixture.py"
    selftest = subprocess.run(
        [sys.executable, str(runner), "--self-test", "--json"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    if selftest.returncode != 0 or json.loads(selftest.stdout).get("status") != "PASS":
        fail("Golden Fixture runner self-test failed")
    for path in fixture_files:
        data = load(path)
        fixture_ids.add(data.get("fixture_id"))
        p = subprocess.run(
            [sys.executable, str(runner), "--validate", str(path), "--json"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
        )
        if p.returncode != 0 or json.loads(p.stdout).get("status") != "PASS":
            fail("fixture validation failed: " + path.name)
    if fixture_ids != EXPECTED_FIXTURES:
        fail("Golden Fixture set mismatch")

    readme = (P2 / "README.md").read_text(encoding="utf-8-sig")
    for marker in (
        "Contracts come before executable fixtures",
        "incumbent plus 2–3 serious challengers",
        "No item may remain",
        "fitness, safety, operability and evidence",
    ):
        if marker not in readme:
            fail("Phase 2 README missing rule: " + marker)

    print(
        f"OK office-v2-phase2 registry={len(items)} lifecycle=PASS "
        f"shortlists={len(lanes)} fixtures={len(fixture_ids)} research-freeze=DEFINED"
    )


if __name__ == "__main__":
    main()
