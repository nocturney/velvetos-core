#!/usr/bin/env python3
"""Canonical live Office v2 safety contracts, independent of phase-closure receipts."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT / "docs" / "implementation" / "office-v2" / "phase0"
P1 = ROOT / "docs" / "implementation" / "office-v2" / "phase1"
P2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"
P3 = ROOT / "docs" / "implementation" / "office-v2" / "phase3"
P3C = ROOT / "docs" / "implementation" / "office-v2" / "phase3c"

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

    model_contract = load(P3C / "model-gateway-contract-v0.json")
    if model_contract.get("production_authority_change") is not False:
        fail("Phase 3C expanded authority")
    if model_contract.get("production_writer_change") is not False:
        fail("Phase 3C expanded production writer")
    if model_contract.get("production_credentials_allowed") is not False:
        fail("Phase 3C admitted production credentials")
    model_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_model_gateway.py"), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if model_check.returncode != 0:
        fail("Phase 3C synthetic model-gateway contract selftest failed")
    try:
        model_summary = json.loads(model_check.stdout)
    except json.JSONDecodeError:
        fail("Phase 3C synthetic contract selftest did not return valid JSON")
    if model_summary.get("status") != "PASS" or model_summary.get("runtime_proven") is not False:
        fail("Phase 3C selftest is incomplete or incorrectly claims live proof")
    if model_summary.get("production_promotion_allowed") is not False:
        fail("Phase 3C contract must not enable production promotion")

    # P0 execution proof is intentionally OFFLINE: it validates real bounded
    # process execution, hashed outputs, replay prevention and context recovery.
    # It must never be misreported as live LLM-based autonomous coding.
    worker_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_worker.py"), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=45,
    )
    if worker_check.returncode != 0:
        fail("P0 worker offline selftest failed: " + worker_check.stdout[:220])
    try:
        worker_summary = json.loads(worker_check.stdout)
    except json.JSONDecodeError:
        fail("P0 worker selftest did not return JSON")
    if (
        worker_summary.get("status") != "PASS"
        or worker_summary.get("tests", 0) < 11
        or worker_summary.get("autonomous_coding_agent_proven") is not False
        or worker_summary.get("model_invocations") != 0
        or worker_summary.get("additional_spend_usd") != 0
    ):
        fail("P0 worker gate failed or exaggerated its runtime proof")

    # Exact #612 evidence bundle: independently sealed real model runs and
    # forced-worker-loss negative control. Pure offline verification; no agent launch.
    evidence_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_two_host_benchmark_verify.py"),
         "--evidence", str(P2 / "p0-two-host-coding-bench-2026-10-08.json")],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if evidence_check.returncode != 0:
        fail("P0 two-host evidence verifier failed: " + evidence_check.stdout[:220])
    try:
        evidence_summary = json.loads(evidence_check.stdout)
    except json.JSONDecodeError:
        fail("P0 two-host evidence verifier output is not JSON")
    if (evidence_summary.get("status") != "PASS_SCOPED_LAB"
        or evidence_summary.get("verified_model_runs") != 4
        or evidence_summary.get("negative_cases") != 5
        or evidence_summary.get("forced_loss_no_false_success") is not True
        or evidence_summary.get("operator_reissue_verified") is not True):
        fail("P0 concurrency evidence incomplete or exaggerated")
    
    # Distinct #612 v1 model-aware Task Envelope. Only its OFFLINE contract
    # selftest runs in CI; it MUST NOT invoke Ollama, Aider or production effects.
    local_worker_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_local_model_worker.py"), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=45,
    )
    if local_worker_check.returncode != 0:
        fail("P0 local model LAB contract test failed: " + local_worker_check.stdout[:240])
    try:
        local_worker = json.loads(local_worker_check.stdout)
    except json.JSONDecodeError:
        fail("P0 local model LAB selftest returned invalid JSON")
    if (
        local_worker.get("status") != "PASS"
        or local_worker.get("tests", 0) < 19
        or local_worker.get("actual_model_invocations") != 0
        or local_worker.get("live_model_agent_proven_by_selftest") is not False
        or local_worker.get("paid_api_calls") != 0
    ):
        fail("P0 local model LAB selftest failed or misclaimed actual inference")

    # Past REAL two-host model invocations are attested by hashed receipts.
    # This separate pure verifier only reads static evidence, never runs a model.
    local_proof_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_local_model_evidence.py"),
         "--evidence", str(P2 / "p0-local-agent-envelope-lab-2026-10-08.json")],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if local_proof_check.returncode != 0:
        fail("P0 local model execution receipts invalid: " + local_proof_check.stdout[:240])
    try:
        local_proof = json.loads(local_proof_check.stdout)
    except json.JSONDecodeError:
        fail("P0 local model evidence returned invalid JSON")
    if (
        local_proof.get("status") != "PASS_SCOPED_LAB"
        or local_proof.get("successful_real_model_receipts") != 4
        or local_proof.get("historical_non_success_receipts") != 3
        or local_proof.get("negative_controls_rejected") != 5
        or local_proof.get("forced_live_model_worker_kill") is not True
        or local_proof.get("explicit_new_local_model_attempt_after_loss") is not True
        or local_proof.get("actual_model_calls_during_verification") != 0
        or local_proof.get("automatic_failover_proven") is not False
        or local_proof.get("production_promotion_allowed") is not False
    ):
        fail("P0 live model receipts/limits failed independent acceptance")

    # #612 P0 read-only UNKNOWN evidence: never execute local models or infer
    # worker liveness/success from a still-present RUNNING journal.
    unknown_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_unknown_reconcile.py"), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if unknown_check.returncode != 0:
        fail("P0 UNKNOWN journal read-only classifier failed: " + unknown_check.stdout[:220])
    try:
        unknown_proof = json.loads(unknown_check.stdout)
    except json.JSONDecodeError:
        fail("P0 UNKNOWN read-only classifier returned invalid JSON")
    if (
        unknown_proof.get("status") != "PASS"
        or unknown_proof.get("tests", 0) < 41
        or unknown_proof.get("model_invocations") != 0
        or unknown_proof.get("automatic_retries") != 0
        or unknown_proof.get("production_effects") != 0
        or unknown_proof.get("external_processes_inspected") != 0
        or unknown_proof.get("success_promotion_allowed") is not False
    ):
        fail("P0 UNKNOWN state did not preserve fail-closed LAB safety")

    # P0 historical PID inspection CI tests use MOCK processes only;
    # no live process enumeration or implicit recovery is run by CI.
    pid_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_owner_snapshot.py"), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if pid_check.returncode != 0:
        fail("P0 historical PID selftest failed: " + pid_check.stdout[:220])
    try:
        pid_result = json.loads(pid_check.stdout)
    except json.JSONDecodeError:
        fail("P0 historical PID selftest returned invalid JSON")
    if (
        pid_result.get("status") != "PASS"
        or pid_result.get("tests", 0) < 16
        or pid_result.get("model_invocations") != 0
        or pid_result.get("processes_killed") != 0
        or pid_result.get("new_task_authorized") is not False
        or pid_result.get("orphan_exclusion_proven") is not False
    ):
        fail("P0 historical PID check falsely claimed ownership or recovery")

    # P0 OS birth identity: pure offline negative controls, no process enumeration
    # in CI. Historic killed Aider has no birth pin and stays UNKNOWN.
    kernel_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_kernel_identity.py"), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if kernel_check.returncode != 0:
        fail("P0 native process birth selftest failed: " + kernel_check.stdout[:240])
    try:
        kernel_state = json.loads(kernel_check.stdout)
    except json.JSONDecodeError:
        fail("P0 native process birth selftest returned invalid JSON")
    if (
        kernel_state.get("status") != "PASS"
        or kernel_state.get("tests", 0) < 24
        or kernel_state.get("model_invocations") != 0
        or kernel_state.get("processes_killed") != 0
        or kernel_state.get("new_tasks_started") != 0
        or kernel_state.get("no_auto_retries") is not True
        or kernel_state.get("all_orphans_excluded") is not False
    ):
        fail("P0 kernel birth fixture claimed unsupported ownership or effects")

    # Separately check hash-pinned real Mac/Windows readbacks plus false-evidence
    # negatives. This subprocess does not query the live OS process table.
    kernel_proof = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_kernel_evidence.py"),
         "--evidence", str(P2 / "p0-kernel-process-identity-lab-2026-10-09.json"),
         "--source", str(ROOT / "scripts" / "vf_office_v2_p0_kernel_identity.py")],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if kernel_proof.returncode != 0:
        fail("P0 OS birth dual-host evidence invalid: " + kernel_proof.stdout[:240])
    try:
        kernel_attested = json.loads(kernel_proof.stdout)
    except json.JSONDecodeError:
        fail("P0 OS birth dual-host verifier output invalid JSON")
    if (
        kernel_attested.get("status") != "PASS_SCOPED_LAB"
        or kernel_attested.get("native_dual_host_observations") != 2
        or kernel_attested.get("negative_controls_rejected") != 8
        or kernel_attested.get("processes_killed") != 0
        or kernel_attested.get("model_invocations") != 0
        or kernel_attested.get("automatic_retry_permitted") is not False
        or kernel_attested.get("all_orphans_excluded") is not False
    ):
        fail("P0 OS birth evidence overstated orphan exclusion/recovery")

    # Offline only: previously verified local Aider source-fix and OS-birth evidence.
    # Do not run a model or enumerate running processes inside CI.
    pinned_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_live_birth_evidence.py"),
         "--evidence", str(P2 / "p0-real-aider-kernel-birth-2026-10-09.json"),
         "--worker-source", str(ROOT / "scripts" / "vf_office_v2_p0_local_model_worker.py")],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if pinned_check.returncode != 0:
        fail("P0 real local model birth-pin LAB receipts invalid: " + pinned_check.stdout[:220])
    try:
        pinned = json.loads(pinned_check.stdout)
    except json.JSONDecodeError:
        fail("P0 real local model birth-pin evidence returned invalid JSON")
    if (
        pinned.get("status") != "PASS_SCOPED_LAB"
        or pinned.get("actual_local_model_success_receipt_refs") != 3
        or pinned.get("negative_controls_rejected") != 11
        or pinned.get("pinned_live_model_killed_and_unknown_preserved") is not True
        or pinned.get("explicit_new_local_attempt_verified") is not True
        or pinned.get("original_retry_permitted") is not False
        or pinned.get("reissued_old_task") is not False
        or pinned.get("model_invocations_during_verification") != 0
        or pinned.get("auto_cross_host_failover_proven") is not False
        or pinned.get("production_promotion_allowed") is not False
    ):
        fail("P0 live Aider OS-birth proof overstated its recovery scope")

    # Exact P0 negative: an empty original POSIX group does NOT prove all
    # descendants have exited. CI verifies a real historical LAB receipt only;
    # it NEVER launches the live detached-child fixture or any worker/model.
    detached_test = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_orphan_escape_negative.py"), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if detached_test.returncode != 0:
        fail("P0 detached descendant offline selftest failed: " + detached_test.stdout[:240])
    try:
        detached = json.loads(detached_test.stdout)
    except json.JSONDecodeError:
        fail("P0 detached descendant selftest output invalid JSON")
    if (
        detached.get("status") != "PASS"
        or detached.get("tests") != 16
        or detached.get("live_processes_launched") != 0
        or detached.get("model_invocations") != 0
        or detached.get("original_attempt_retry_permitted") is not False
        or detached.get("all_orphans_excluded") is not False
    ):
        fail("P0 detached descendant false-negative safety regression")

    escaped_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_orphan_escape_negative.py"),
         "verify", "--evidence", str(P2 / "p0-orphan-escape-negative-2026-10-09.json")],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if escaped_check.returncode != 0:
        fail("P0 real detached descendant LAB receipt failed: " + escaped_check.stdout[:240])
    try:
        escaped = json.loads(escaped_check.stdout)
    except json.JSONDecodeError:
        fail("P0 detached descendant receipt verification did not return JSON")
    if (
        escaped.get("status") != "PASS"
        or escaped.get("result") != "GROUP_EMPTY_ESCAPED_CHILD_STILL_LIVE"
        or escaped.get("receipt_sha256") != "6b69eadd2b20bc25e5f73d257f8a8f671fee1a2b9219d2a92cfca7de690f5ff8"
        or escaped.get("independent_offline_verify") is not True
        or escaped.get("no_auto_retry") is not True
        or escaped.get("model_invocations") != 0
    ):
        fail("P0 orphan escape evidence incorrectly admitted unsafe recovery")

    print(
        "OK office-v2-contracts authority=single writer_change=NO credentials=LAB_DENIED "
        f"candidates={len(items)} phase3_effects=LAB_LOCAL_ONLY"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
