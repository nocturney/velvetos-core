#!/usr/bin/env python3
"""Canonical live Office v2 safety contracts, independent of phase-closure receipts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT / "docs" / "implementation" / "office-v2" / "phase0"
P1 = ROOT / "docs" / "implementation" / "office-v2" / "phase1"
P2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"
P3 = ROOT / "docs" / "implementation" / "office-v2" / "phase3"

FORWARD = {
    "DISCOVERED", "RESEARCHED", "CANDIDATE", "ADMITTED", "LAB",
    "SHADOW", "PILOT", "PRODUCTION", "FALLBACK", "RETIRED",
}
PRODUCTION_VERDICTS = {"KEEP_INCUMBENT", "REPAIR_REQUIRED"}


def fail(message: str) -> None:
    print("FAIL office-v2-contracts: " + message, file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must be an object")
    return value


def main() -> int:
    authority = load(P0 / "authority-map-v0.1.json")
    if authority.get("single_external_effect_authority") is not True:
        fail("Phase 0 must preserve single external-effect authority")
    if authority.get("new_production_writer_added") is not False:
        fail("Phase 0 must not add a production writer")

    credentials = load(P0 / "credential-trust-classes-v0.json")
    if credentials.get("secrets_in_git_allowed") is not False:
        fail("secrets must remain forbidden in Git")
    if credentials.get("lab_receives_production_credentials_by_default") is not False:
        fail("LAB must not receive production credentials by default")

    lab = load(P1 / "lab-boundary-v0.json")
    if lab.get("production_authority") != "NONE":
        fail("Phase 1 LAB gained production authority")
    if lab.get("production_credentials_allowed") is not False:
        fail("Phase 1 LAB gained production credentials")
    if lab.get("stateful_candidate_rule") != "RESTORE_DRILL_REQUIRED_BEFORE_PRODUCTION_CAPABLE":
        fail("stateful candidate restore-drill gate drifted")
    lane = lab.get("artifact_lane") or {}
    if lane.get("full_c_drive_mounted") is not False or lane.get("full_d_drive_mounted") is not False:
        fail("Phase 1 LAB must not mount full Windows drives")

    lifecycle = load(P2 / "candidate-lifecycle-v0.json")
    if set(lifecycle.get("forward_states") or []) != FORWARD:
        fail("candidate lifecycle vocabulary drifted")
    registry = load(P2 / "candidate-registry-v0.json")
    if registry.get("status") != "CLOSED_IMPORT":
        fail("candidate registry must remain a closed import")
    items = registry.get("items") or []
    if not items:
        fail("candidate registry is empty")
    for item in items:
        cid = item.get("candidate_id")
        state = item.get("lifecycle_state")
        verdict = item.get("decision_verdict")
        if state not in FORWARD:
            fail(f"{cid}: unknown lifecycle state {state}")
        if state == "PRODUCTION" and verdict not in PRODUCTION_VERDICTS:
            fail(f"{cid}: production entry lacks incumbent/repair verdict")
        if state in {"CANDIDATE", "ADMITTED", "LAB", "SHADOW", "PILOT"} and not item.get("evidence_refs"):
            fail(f"{cid}: non-incumbent lifecycle entry lacks evidence")

    contract = load(P3 / "durable-execution-contract-v0.json")
    if contract.get("authority_change") is not False:
        fail("Phase 3 durable execution changed authority")
    if contract.get("production_writer_change") is not False:
        fail("Phase 3 durable execution changed production writer")
    if contract.get("production_credentials_allowed") is not False:
        fail("Phase 3 durable execution allows production credentials")
    if contract.get("external_effect_surface") != "LAB_LOCAL_SIMULATED_EFFECT_ADAPTER_ONLY":
        fail("Phase 3 external effects must remain LAB-local simulated")

    plan = load(P3 / "durable-execution-lab-plan-v0.json")
    if plan.get("production_authority") != "NONE":
        fail("Phase 3 LAB plan gained production authority")
    if plan.get("production_credentials_allowed") is not False:
        fail("Phase 3 LAB plan gained production credentials")
    if plan.get("full_windows_drive_mounts_allowed") is not False:
        fail("Phase 3 LAB plan permits full Windows drive mounts")

    verdict = load(P3 / "durable-execution-verdict-v0.json")
    if verdict.get("production_authority_change") is not False:
        fail("Phase 3 verdict changed production authority")
    if verdict.get("production_writer_change") is not False:
        fail("Phase 3 verdict changed production writer")
    if verdict.get("production_credentials_used") is not False:
        fail("Phase 3 verdict used production credentials")

    print(
        "OK office-v2-contracts authority=single writer_change=NO credentials=LAB_DENIED "
        f"candidates={len(items)} phase3_effects=LAB_LOCAL_ONLY"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
