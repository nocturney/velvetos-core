#!/usr/bin/env python3
"""Canonical live Office v2 safety contracts, independent of phase-closure receipts."""
from __future__ import annotations

import hashlib
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

    # #612: manual fresh-attempt evidence separation after preserved UNKNOWN.
    # Pure offline only: never dispatch/requeue tasks or acquire a fleet lease.
    fresh_script = ROOT / "scripts" / "vf_office_v2_p0_fresh_attempt_lineage.py"
    fresh_check = subprocess.run(
        [sys.executable, str(fresh_script), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if fresh_check.returncode:
        fail("P0 fresh attempt fail-closed selftest failed: " + fresh_check.stdout[:220])
    try:
        fresh_proof = json.loads(fresh_check.stdout)
        fresh_evidence = json.loads((P2 / "p0-manual-fresh-attempt-lineage-2026-10-09.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        fail("P0 fresh attempt evidence invalid or missing")
    fresh_original = fresh_evidence.get("actual_host_local_readback") or {}
    fresh_limits = fresh_evidence.get("scope_limits") or {}
    fresh_source = fresh_evidence.get("source") or {}
    if (
        fresh_check.returncode != 0
        or fresh_proof.get("status") != "PASS_OFFLINE"
        or fresh_proof.get("tests") != 21
        or fresh_proof.get("model_invocations") != 0
        or fresh_proof.get("auto_retry_authorized") is not False
        or fresh_proof.get("new_task_execution_authorized") is not False
        or fresh_proof.get("all_orphan_descendants_excluded") is not False
        or fresh_proof.get("fleet_authority") is not False
        or fresh_evidence.get("schema") != "velvetos.office-v2.p0-manual-new-attempt-lineage-lab.v1"
        or fresh_evidence.get("status") != "PASS_READ_ONLY_LINEAGE_NOT_ADMISSION"
        or fresh_source.get("script_git_blob") != "783575ff1784bb7165ec4cb1a73b1c643dccfed7"
        or fresh_source.get("script_file_sha256") != "b2eb921c37ace4f979f98433f069df07484e7b0b5f1e670c112efabf6a90ea73"
        or hashlib.sha256(fresh_script.read_bytes()).hexdigest() !=
            "b2eb921c37ace4f979f98433f069df07484e7b0b5f1e670c112efabf6a90ea73"
        or fresh_original.get("original_state") != "UNKNOWN_RUNNING_JOURNAL_NO_BLIND_RETRY"
        or fresh_original.get("new_state") != "SUCCESS_CLAIM_NEEDS_INDEPENDENT_WORKER_VERIFY"
        or fresh_original.get("original_running_journal_raw_sha256") !=
            "798081231f7af3d13256de84653ca5abe283488b82b03fe67fe4477b0237cf18"
        or fresh_original.get("new_envelope_sha256") !=
            "9694d73817bea7c541dacf23c4c5eb9ce9e21b9f4e033210dc4757de259c04b1"
        or fresh_original.get("new_task_success_independently_verified_by_this_tool") is not False
        or fresh_limits.get("read_only") is not True
        or fresh_limits.get("original_unknown_retry_authorized") is not False
        or fresh_limits.get("new_task_execution_authorized") is not False
        or fresh_limits.get("autonomous_recovery_proven") is not False
        or fresh_limits.get("worker_fencing_proven") is not False
        or fresh_limits.get("fleet_lease_or_scheduler_authority") is not False
        or fresh_limits.get("production_writer_authority") is not False
        or fresh_limits.get("actual_model_calls_this_check") != 0
    ):
        fail("P0 manual new-attempt lineage overstated safety or authority")

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
        or escaped.get("receipt_sha256") != "64f1662300c035cd5be3b06b1438bab6ecb72cb308194d5234a3f124e35afc7c"
        or escaped.get("independent_offline_verify") is not True
        or escaped.get("no_auto_retry") is not True
        or escaped.get("model_invocations") != 0
    ):
        fail("P0 orphan escape evidence incorrectly admitted unsafe recovery")

    # P0 Windows native Job Object inheritance / kill-on-close: exact LAB proof.
    # CI runs ONLY pure offline assertions and historical receipt verification.
    # Never create a live Windows job or launch a process in this sensor.
    job_lab_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_windows_job_object_lab.py"), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if job_lab_check.returncode != 0:
        fail("P0 Windows Job Object offline contract failed: " + job_lab_check.stdout[:220])
    try:
        job_lab = json.loads(job_lab_check.stdout)
    except json.JSONDecodeError:
        fail("P0 Windows Job Object selftest returned invalid JSON")
    if (
        job_lab.get("status") != "PASS"
        or job_lab.get("tests") != 17
        or job_lab.get("live_processes_launched") != 0
        or job_lab.get("model_invocations") != 0
        or job_lab.get("original_task_retry_allowed") is not False
        or job_lab.get("all_possible_escaped_processes_excluded") is not False
    ):
        fail("P0 Windows Job Object LAB overstated its cleanup authority")

    job_record_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_p0_windows_job_object_lab.py"),
         "verify", "--evidence", str(P2 / "p0-windows-native-job-containment-2026-10-09.json")],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if job_record_check.returncode != 0:
        fail("P0 real Windows Job Object receipt invalid: " + job_record_check.stdout[:220])
    try:
        job_record = json.loads(job_record_check.stdout)
    except json.JSONDecodeError:
        fail("P0 Windows native Job Object receipt returned invalid JSON")
    if (
        job_record.get("status") != "PASS"
        or job_record.get("independent_offline_verification") is not True
        or job_record.get("job_child_inherited_containment") is not True
        or job_record.get("receipt_sha256") != "e44cb0fc832b57c8f194caf22646dab8b978381b83d3ca2e8bdb64486ac1b6ad"
        or job_record.get("original_task_retry_allowed") is not False
        or job_record.get("all_possible_escaped_processes_excluded") is not False
        or job_record.get("model_invocations") != 0
    ):
        fail("P0 Windows native containment LAB became unsafe or falsified")

    # #612: exact Windows detached-grandchild negative-escape test. Only read
    # historical evidence and run offline validations; NEVER launch a Job in CI.
    detached_script = ROOT / "scripts" / "vf_office_v2_p0_detached_descendant_lab.py"
    detached_proof = P2 / "p0-windows-job-detached-descendant-lab-2026-10-09.json"
    detached_test = subprocess.run(
        [sys.executable, str(detached_script), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if detached_test.returncode:
        fail("P0 detached-descendant pure selftest failed: " + detached_test.stdout[:220])
    try:
        detached_test_record = json.loads(detached_test.stdout)
    except json.JSONDecodeError:
        fail("P0 detached-descendant selftest invalid JSON")
    if (detached_test_record.get("status") != "PASS_OFFLINE"
            or detached_test_record.get("tests") != 14
            or detached_test_record.get("native_jobs_created") != 0
            or detached_test_record.get("model_calls") != 0
            or detached_test_record.get("all_possible_escaped_processes_excluded") is not False):
        fail("P0 detached-descendant selftest overstated native containment")

    detached_verify = subprocess.run(
        [sys.executable, str(detached_script), "verify", "--evidence", str(detached_proof)],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if detached_verify.returncode:
        fail("P0 historical detached-descendant receipt invalid: " + detached_verify.stdout[:220])
    try:
        detached_check = json.loads(detached_verify.stdout)
        detached_raw = json.loads(detached_proof.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        fail("P0 detached-descendant evidence readback invalid")
    if (detached_check.get("status") !=
            "PASS_SHAPE_SELF_HASH_ONLY_NOT_INDEPENDENT_OS_ATTESTATION"
            or detached_check.get("model_calls") != 0
            or detached_check.get("all_possible_escaped_processes_excluded") is not False
            or detached_raw.get("receipt_sha256") !=
            "13272458fa66476b71a4a025e197fa6888dde168adc16612bc23089b0667737f"
            or detached_raw.get("all_possible_escaped_processes_excluded") is not False):
        fail("P0 detached-descendant re-sealed receipt or authority drift")

    # #612: real historical Windows Job-supervised Aider interruption + completion.
    # Pure offline verification only. No model, scheduler, Win32 process launch or
    # external effect occurs during CI or this evidence check.
    supervised_job_check = subprocess.run(
        [sys.executable,
         str(ROOT / "scripts" / "vf_office_v2_p0_supervised_aider_evidence.py"),
         "--evidence", str(P2 / "p0-supervised-aider-windows-job-2026-10-09.json")],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if supervised_job_check.returncode != 0:
        fail("P0 supervised real Aider Job LAB evidence invalid: " +
             supervised_job_check.stdout[:230])
    try:
        supervised_job = json.loads(supervised_job_check.stdout)
    except json.JSONDecodeError:
        fail("P0 supervised real Aider Job evidence not JSON")
    if (
        supervised_job.get("status") != "PASS_SCOPED_WINDOWS_SUPERVISED_AIDER_LAB"
        or supervised_job.get("negative_controls_rejected") != 19
        or supervised_job.get("receipt_sha256") != "f4df14dc17d98e9788b3ef246ff00121341c945ce300ea72e084c74428cd7c88"
        or supervised_job.get("two_distinct_real_task_envelopes") is not True
        or supervised_job.get("historical_interrupt") != "UNKNOWN_NO_BLIND_RETRY"
        or supervised_job.get("historical_new_attempt") != "SUCCEEDED_INDEPENDENT_LAB_QA"
        or supervised_job.get("verified_real_local_model_min_invocations") != 1
        or supervised_job.get("model_calls_during_verification") != 0
        or supervised_job.get("original_task_retry_allowed") is not False
        or supervised_job.get("all_possible_escaped_processes_excluded") is not False
        or supervised_job.get("automatic_recovery_proven") is not False
        or supervised_job.get("scheduler_proven") is not False
        or supervised_job.get("production_effects") != 0
    ):
        fail("P0 supervised Aider historical Job claims exceeded scoped LAB proof")

    # #612: harden MANUAL Windows Aider supervisor origin/path trust.
    # CLI selftest only: disposable temporary Git & path assertions, no Win32
    # Job object, no local model launch, no scheduler and no external effects.
    supervised_guard_check = subprocess.run(
        [sys.executable,
         str(ROOT / "scripts" / "vf_office_v2_p0_supervised_aider_lab.py"),
         "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=35,
    )
    if supervised_guard_check.returncode != 0:
        fail("P0 supervised Aider admission source-pin selftest failed: " +
             supervised_guard_check.stdout[:220])
    try:
        supervised_guard = json.loads(supervised_guard_check.stdout)
    except json.JSONDecodeError:
        fail("P0 supervised Aider admission selftest JSON invalid")
    if (
        supervised_guard.get("status") != "PASS_OFFLINE"
        or supervised_guard.get("tests", 0) < 15
        or supervised_guard.get("model_invocations") != 0
        or supervised_guard.get("native_job_objects_created") != 0
        or supervised_guard.get("production_effects") != 0
        or supervised_guard.get("retries_authorized") != 0
    ):
        fail("P0 supervised Aider admission source integrity safety regression")

    print(
        "OK office-v2-contracts authority=single writer_change=NO credentials=LAB_DENIED "
        f"candidates={len(items)} phase3_effects=LAB_LOCAL_ONLY"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
