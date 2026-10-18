#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT / "docs" / "implementation" / "office-v2" / "phase3"
P2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"

REQUIRED = [
    P3 / "README.md",
    P3 / "durable-execution-contract-v0.json",
    P3 / "durable-execution-destructive-v0.json",
    P3 / "durable-execution-admission-v0.json",
    P3 / "durable-execution-lab-plan-v0.json",
    P3 / "runtime-pins-v0.json",
    P3 / "durable-execution-shortlist-reopen-v0.json",
    P3 / "durable-execution-shortlist-correction-v0.json",
    P3 / "scorecard-incumbent-current-v0.json",
    P3 / "scorecard-restate-v0.json",
    P3 / "scorecard-hatchet-v0.json",
    P3 / "scorecard-temporal-v0.json",
    P3 / "durable-execution-verdict-v0.json",
]

MANDATORY_STEP_IDS = {
    "kill-worker",
    "recover-worker",
    "kill-engine",
    "restart-engine",
    "duplicate-webhook",
    "dedupe",
    "approval-wait",
    "approval-resume",
    "cancel-child",
    "transient-failure",
    "retry",
    "move",
    "unknown-effect",
    "reconcile-inspect",
    "replay-finalize",
}

EXPECTED_CHALLENGERS = {
    "candidate-restate",
    "candidate-hatchet",
    "candidate-temporal",
}


def fail(message: str) -> None:
    print("FAIL " + message, file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(data, dict):
        fail(f"JSON root must be object: {path.relative_to(ROOT)}")
    return data


def main() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.is_file()]
    if missing:
        fail("missing Phase 3A files: " + ", ".join(missing))

    contract = load(P3 / "durable-execution-contract-v0.json")
    if contract.get("status") != "CONTRACT_V0_FROZEN_FOR_LAB":
        fail("durable contract is not frozen for LAB")
    if contract.get("authority_change") is not False:
        fail("Phase 3A must not change production authority")
    if contract.get("production_writer_change") is not False:
        fail("Phase 3A must not add production writer")
    if contract.get("production_credentials_allowed") is not False:
        fail("Phase 3A LAB must deny production credentials")
    if contract.get("external_effect_surface") != "LAB_LOCAL_SIMULATED_EFFECT_ADAPTER_ONLY":
        fail("Phase 3A external-effect surface is not LAB-local simulated")
    gate = contract.get("gate") or {}
    if not gate or not all(gate.values()):
        fail("Phase 3A durable gate is incomplete")

    fixture = load(P3 / "durable-execution-destructive-v0.json")
    if fixture.get("fixture_id") != "durable-execution-destructive-20-step":
        fail("destructive fixture id mismatch")
    if fixture.get("production_effects_forbidden") is not True:
        fail("destructive fixture must forbid production effects")
    if fixture.get("effect_adapter") != "LAB_LOCAL_SIMULATED_EFFECT_ADAPTER":
        fail("destructive fixture must use local simulated effect adapter")
    if fixture.get("vendor_specific_fields_forbidden") is not True:
        fail("destructive fixture must be vendor-neutral")
    steps = fixture.get("steps") or []
    if len(steps) != 20:
        fail(f"destructive fixture must contain exactly 20 steps, got {len(steps)}")
    nums = [step.get("n") for step in steps]
    if nums != list(range(1, 21)):
        fail("destructive fixture step numbering must be 1..20")
    ids = [step.get("id") for step in steps]
    if len(ids) != len(set(ids)):
        fail("destructive fixture step ids must be unique")
    if not MANDATORY_STEP_IDS.issubset(set(ids)):
        fail("destructive fixture missing required failure/recovery semantics")
    required_evidence = set(fixture.get("required_evidence") or [])
    for step in steps:
        expected = set(step.get("expected") or [])
        if not expected:
            fail("fixture step missing expected evidence: " + str(step.get("id")))
        if not expected.issubset(required_evidence):
            fail("fixture required_evidence incomplete for: " + str(step.get("id")))

    admission = load(P3 / "durable-execution-admission-v0.json")
    if admission.get("winner") is not None:
        fail("Phase 3A admission must not declare a winner")
    if admission.get("production_authority_granted") is not False:
        fail("Phase 3A admission granted production authority")
    candidates = admission.get("candidates") or []
    by_id = {c.get("candidate_id"): c for c in candidates}
    if len(by_id) != len(candidates):
        fail("duplicate candidate ids in admission")
    admitted = {
        cid for cid, item in by_id.items()
        if item.get("role") == "CHALLENGER"
        and item.get("disposition") == "ADMITTED"
    }
    if admitted != EXPECTED_CHALLENGERS:
        fail("Phase 3A admitted challenger set drifted")
    dbos = by_id.get("candidate-dbos") or {}
    if dbos.get("role") != "CREDIBLE_RESERVE" or dbos.get("disposition") != "RESERVE_DEFERRED_WITH_REASON":
        fail("DBOS must remain the credible reserve after corrected Hatchet admission")
    if dbos.get("authority_role") != "NONE":
        fail("DBOS reserve must have no authority")
    for cid in EXPECTED_CHALLENGERS | {"candidate-dbos"}:
        item = by_id.get(cid)
        if not item:
            fail("missing candidate admission: " + cid)
        if item.get("authority_role") != "NONE":
            fail("challenger/reserve authority must remain NONE: " + cid)
        if not item.get("target_version"):
            fail("candidate target version missing: " + cid)
        if not item.get("evidence_refs"):
            fail("candidate evidence missing: " + cid)

    p0 = load(P2 / "p0-shortlists-v0.json")
    lane = next((x for x in p0.get("lanes", []) if x.get("lane_id") == "durable-execution"), None)
    if not lane:
        fail("Phase 2 durable-execution shortlist missing")
    if set(lane.get("challengers") or []) != EXPECTED_CHALLENGERS:
        fail("Phase 3A admission must remain aligned to Phase 2 durable shortlist")
    if lane.get("winner") != "candidate-restate":
        fail("durable-execution shortlist winner must be candidate-restate after completed bake-off")
    if lane.get("fallback") != "candidate-temporal":
        fail("durable-execution shortlist fallback must be candidate-temporal")
    if lane.get("freeze_state") != "FROZEN_AFTER_PHASE3A_BAKEOFF":
        fail("durable-execution shortlist must be frozen after Phase 3A bake-off")
    if lane.get("verdict_receipt") != "docs/implementation/office-v2/phase3/durable-execution-verdict-v0.json":
        fail("durable-execution shortlist verdict provenance missing")
    if lane.get("correction_receipt") != "docs/implementation/office-v2/phase3/durable-execution-shortlist-correction-v0.json":
        fail("durable-execution shortlist correction provenance missing")

    pins = load(P3 / "runtime-pins-v0.json")
    if pins.get("production_credentials_used") is not False or pins.get("production_authority_change") is not False:
        fail("runtime pin resolution must not use production credentials or change authority")
    pin_candidates = pins.get("candidates") or {}
    for cid in EXPECTED_CHALLENGERS:
        if cid not in pin_candidates:
            fail("runtime pins missing active candidate: " + cid)
        if pin_candidates[cid].get("status") != "PINNED":
            fail("active candidate runtime pin is not PINNED: " + cid)
    if pin_candidates.get("candidate-dbos", {}).get("status") != "PINNED_RESERVE":
        fail("DBOS reserve pin status missing")

    reopen = load(P3 / "durable-execution-shortlist-reopen-v0.json")
    if reopen.get("trigger") != "SHORTLISTED_CANDIDATE_ADMISSION_FAILURE":
        fail("historical shortlist reopen receipt trigger mismatch")
    if reopen.get("status") != "SUPERSEDED_AFTER_CORRECTED_HATCHET_OCI_ADMISSION":
        fail("historical shortlist reopen must be marked superseded")
    if reopen.get("failed_candidate") != "candidate-hatchet" or reopen.get("temporary_replacement_candidate") != "candidate-dbos":
        fail("historical shortlist reopen mapping mismatch")
    if set(reopen.get("active_challengers") or []) != EXPECTED_CHALLENGERS:
        fail("historical reopen receipt must point to corrected active challengers")
    if reopen.get("winner") is not None or reopen.get("production_authority_change") is not False:
        fail("shortlist history must not select winner or change authority")

    correction = load(P3 / "durable-execution-shortlist-correction-v0.json")
    if correction.get("status") != "APPLIED":
        fail("shortlist correction is not applied")
    if correction.get("restored_candidate") != "candidate-hatchet" or correction.get("returned_to_reserve") != "candidate-dbos":
        fail("shortlist correction candidate mapping mismatch")
    if set(correction.get("active_challengers") or []) != EXPECTED_CHALLENGERS:
        fail("shortlist correction active challengers mismatch")
    if correction.get("winner") is not None or correction.get("production_authority_change") is not False:
        fail("shortlist correction must not select winner or change authority")

    lab = load(P3 / "durable-execution-lab-plan-v0.json")
    if lab.get("status") != "DESTRUCTIVE_BAKEOFF_COMPLETE_WINNER_SELECTED_NO_AUTHORITY_CHANGE":
        fail("LAB plan must record completed destructive bake-off and selected winner")
    if lab.get("winner_candidate") != "candidate-restate" or lab.get("fallback_candidate") != "candidate-temporal":
        fail("LAB plan winner/fallback mismatch")
    if lab.get("verdict_ref") != "docs/implementation/office-v2/phase3/durable-execution-verdict-v0.json":
        fail("LAB plan verdict reference missing")
    if lab.get("production_authority") != "NONE":
        fail("LAB plan production authority must be NONE")
    if lab.get("production_credentials_allowed") is not False:
        fail("LAB plan must deny production credentials")
    if lab.get("full_windows_drive_mounts_allowed") is not False:
        fail("LAB plan must not allow full Windows drive mounts")
    forbidden = set(lab.get("forbidden_host_ports") or [])
    if not {18080, 18100}.issubset(forbidden):
        fail("known occupied/forbidden ports are not reserved")
    lab_candidates = lab.get("candidates") or []
    if {item.get("candidate_id") for item in lab_candidates} != EXPECTED_CHALLENGERS:
        fail("LAB plan active candidate set does not match corrected shortlist")
    for item in lab_candidates:
        if item.get("runtime_pin_status") != "RESOLVED":
            fail("candidate immutable runtime pin is not resolved")
        if not item.get("immutable_pin"):
            fail("candidate immutable runtime pin value is missing")
        if forbidden.intersection(set(item.get("host_ports") or [])):
            fail("candidate LAB plan uses forbidden host port")
        if not str(item.get("admission_smoke", "")).startswith("PASS"):
            fail("active candidate admission smoke is not PASS: " + str(item.get("candidate_id")))
        if not item.get("evidence_ref"):
            fail("active candidate admission smoke evidence is missing: " + str(item.get("candidate_id")))
        if item.get("destructive_benchmark") != "PASS":
            fail("active candidate destructive benchmark must PASS: " + str(item.get("candidate_id")))
        if not item.get("benchmark_evidence_ref") or not item.get("scorecard_ref"):
            fail("active candidate benchmark/scorecard provenance missing: " + str(item.get("candidate_id")))
    incumbent = lab.get("incumbent_baseline") or {}
    if incumbent.get("destructive_benchmark") != "FAIL":
        fail("incumbent baseline must record frozen-fixture FAIL")
    if not incumbent.get("evidence_ref") or not incumbent.get("scorecard_ref"):
        fail("incumbent baseline evidence/scorecard provenance missing")
    reserves = lab.get("reserve_candidates") or []
    if {item.get("candidate_id") for item in reserves} != {"candidate-dbos"}:
        fail("LAB plan reserve set must contain only DBOS")

    verdict = load(P3 / "durable-execution-verdict-v0.json")
    if verdict.get("status") != "SELECTED_FOR_INTEGRATION_NO_PRODUCTION_AUTHORITY":
        fail("Phase 3A verdict status mismatch")
    if verdict.get("winner") != "candidate-restate" or verdict.get("fallback") != "candidate-temporal":
        fail("Phase 3A verdict winner/fallback mismatch")
    if verdict.get("production_authority_change") is not False or verdict.get("production_writer_change") is not False:
        fail("Phase 3A verdict must not change production authority/writer")
    if verdict.get("production_credentials_used") is not False:
        fail("Phase 3A verdict must not use production credentials")
    dispositions = verdict.get("dispositions") or {}
    expected_verdicts = {
        "incumbent-current-durable-execution": "REJECTED_WITH_REASON",
        "candidate-restate": "ADVANCE",
        "candidate-hatchet": "BENCHMARKED_AND_LOST",
        "candidate-temporal": "DEFERRED_WITH_REASON",
        "candidate-dbos": "DEFERRED_WITH_REASON",
    }
    for cid, expected in expected_verdicts.items():
        if (dispositions.get(cid) or {}).get("verdict") != expected:
            fail("Phase 3A disposition mismatch: " + cid)

    expected_scorecards = {
        "scorecard-incumbent-current-v0.json": ("incumbent-current-durable-execution", "REJECTED_WITH_REASON"),
        "scorecard-restate-v0.json": ("candidate-restate", "ADVANCE"),
        "scorecard-hatchet-v0.json": ("candidate-hatchet", "BENCHMARKED_AND_LOST"),
        "scorecard-temporal-v0.json": ("candidate-temporal", "DEFERRED_WITH_REASON"),
    }
    required_resource_fields = {
        "wall_seconds", "cpu_peak_pct", "ram_peak_mb", "gpu_peak_pct", "vram_peak_mb",
        "storage_delta_mb", "network_mb", "external_cost", "recurring_cost", "operator_minutes",
    }
    for name, (cid, expected_verdict) in expected_scorecards.items():
        card = load(P3 / name)
        if card.get("schema") != "velvetos.office-v2.phase2-scorecard.v0":
            fail("scorecard schema mismatch: " + name)
        if card.get("candidate_id") != cid or card.get("verdict") != expected_verdict:
            fail("scorecard candidate/verdict mismatch: " + name)
        if set((card.get("resources") or {}).keys()) != required_resource_fields:
            fail("scorecard resource shape mismatch: " + name)
        if (card.get("rollback") or {}).get("status") != "PASS":
            fail("scorecard rollback must PASS: " + name)

    readme = (P3 / "README.md").read_text(encoding="utf-8-sig")
    for marker in (
        "WINNER: candidate-restate",
        "FALLBACK: candidate-temporal",
        "no production credentials",
        "exactly 20 semantic steps",
        "candidate-hatchet",
        "production authority remains unchanged",
    ):
        if marker not in readme:
            fail("Phase 3A README missing closure marker: " + marker)

    print(
        "OK office-v2-phase3a contract=FROZEN fixture=20-STEP "
        "challengers=3 reserve=DBOS winner=RESTATE fallback=TEMPORAL benchmark=COMPLETE authority=NONE"
    )


if __name__ == "__main__":
    main()
