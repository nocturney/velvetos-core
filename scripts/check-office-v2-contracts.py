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
        or fresh_source.get("script_git_blob") != "138cc0ec9906822fcb8fc9da1952f5ba89e37c5d"
        or fresh_source.get("script_file_sha256") != "00882aa96d6e22e785b4c3c6ba30ff1048f655284256b455f760a366c437bddc"
        or hashlib.sha256(fresh_script.read_bytes()).hexdigest() !=
            "00882aa96d6e22e785b4c3c6ba30ff1048f655284256b455f760a366c437bddc"
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

    # #612: actual byte-preserved Mac local-model source files in quarantine.
    # CI runs deterministic offline public-property QA in a temp subprocess,
    # asserts one strict int-subclass bug DENIES production promotion.
    # This is a manually reviewed evidence PR, NOT autonomous model Git writing.
    artifact_gate = ROOT / "scripts" / "vf_office_v2_p0_model_artifact_pr_gate.py"
    if hashlib.sha256(artifact_gate.read_bytes()).hexdigest() != (
            "352c192ebfa9ea6b32739c1185fa06741c68430ed5b183db1c045df94e52c096"):
        fail("P0 quarantined model-source QA gate actual script bytes drift")
    for artifact_mode in ("verify", "selftest"):
        artifact_run = subprocess.run(
            [sys.executable, str(artifact_gate), artifact_mode],
            cwd=ROOT, capture_output=True, text=True, timeout=35,
        )
        if artifact_run.returncode:
            fail("P0 quarantined real model source " + artifact_mode +
                 " failed: " + artifact_run.stdout[:220])
        try:
            artifact_status = json.loads(artifact_run.stdout)
        except ValueError:
            fail("P0 quarantined real model source emitted invalid JSON")
        if artifact_mode == "verify":
            if (artifact_status.get("status") !=
                    "PASS_QUARANTINED_ORIGINAL_MODEL_BYTES_AND_EXPANDED_QA"
                    or artifact_status.get("artifact_count") != 2
                    or artifact_status.get("canonical_tag_expanded_pass") is not True
                    or artifact_status.get("windows_merge_expanded_contract_gap")
                       is not True
                    or artifact_status.get("production_promoted") is not False
                    or artifact_status.get("automated_pr_or_fleet_lease") is not False
                    or artifact_status.get("model_calls_by_verifier") != 0):
                fail("P0 model source quarantine or expanded QA overstated green")
        elif (artifact_status.get("status") != "PASS_OFFLINE"
              or artifact_status.get("tests") != 21
              or artifact_status.get("model_calls") != 0
              or artifact_status.get("external_git_effects") != 0
              or artifact_status.get("production_code_promoted") is not False
              or artifact_status.get("cross_host_fencing_proven") is not False):
            fail("P0 model-source adversarial QA permitted promotion")

    # #612: Two real, different-code QA-green Task Envelopes on ONE Mac.
    # Offline checks only; never start Ollama, requeue UNKNOWN or grant a lease.
    two_family_script = ROOT / "scripts" / "vf_office_v2_p0_second_diverse_success_evidence.py"
    two_family_data = P2 / "p0-two-families-mac-independent-qa-success-2026-10-10.json"
    if hashlib.sha256(two_family_script.read_bytes()).hexdigest() != (
            "80172813472c72fc11d3cf50f107d8cdce6b3bc1c89b704f811d432ef067033c"):
        fail("P0 two-family historical verifier source bytes changed")
    for proof_mode in ("selftest", "verify"):
        proof_run = subprocess.run(
            [sys.executable, str(two_family_script), proof_mode,
             "--evidence", str(two_family_data)],
            cwd=ROOT, capture_output=True, text=True, timeout=25)
        if proof_run.returncode != 0:
            fail("P0 two-family metadata " + proof_mode +
                 " failed: " + proof_run.stdout[:180])
        try:
            check_family = json.loads(proof_run.stdout)
        except ValueError:
            fail("P0 two-family validator returned non-JSON")
        if proof_mode == "selftest":
            if (check_family.get("status") != "PASS_OFFLINE"
                    or check_family.get("tests") != 25
                    or check_family.get("model_invocations") != 0
                    or check_family.get("scheduler_calls") != 0
                    or check_family.get("production_actions") != 0
                    or check_family.get("authority_promoted") is not False):
                fail("P0 two-family offline negative cases overstated success")
        elif (check_family.get("status") !=
              "PASS_HISTORICAL_TWO_DIFFERENT_MAC_CODING_FAMILIES_OFFLINE_ONLY"
              or check_family.get("different_target_files") != 2
              or check_family.get("separate_original_worker_verifications") != 2
              or check_family.get("different_physical_hosts") != 1
              or check_family.get("prior_unknown_journals_intact") is not True
              or check_family.get("original_model_tasks_retried") is not False
              or check_family.get("reliable_p95") is not False
              or check_family.get("additional_model_calls") != 0
              or check_family.get("production_or_distributed_fencing_authority")
                 is not False):
            fail("P0 two-family Mac-only proof was falsified")

    # #612: TWO fresh new Mac public-spec guided Qwen coding attempts.
    # One original Worker independent QA PASS, one original journal remains
    # FAIL_CLOSED. Only historical/offline validation in CI; no model/OS run.
    guided_data = P2 / "p0-two-fresh-guided-model-qa-2026-10-10.json"
    guided_verifier = ROOT / "scripts" / "vf_office_v2_p0_guided_qa_evidence.py"
    if hashlib.sha256(guided_verifier.read_bytes()).hexdigest() != (
            "8208d1b978c0c8247f74a186dff28829b7b90a49d3d85a428e4a2fa066c35737"):
        fail("P0 guided QA evidence validator source bytes drift")
    for mode in ("selftest", "verify"):
        check_guided = subprocess.run(
            [sys.executable, str(guided_verifier), mode,
             "--evidence", str(guided_data)],
            cwd=ROOT, capture_output=True, text=True, timeout=25,
        )
        if check_guided.returncode:
            fail("P0 Mac guided QA " + mode + " rejected: " +
                 check_guided.stdout[:160])
        try:
            result_guided = json.loads(check_guided.stdout)
        except ValueError:
            fail("P0 Mac guided QA validator emitted invalid JSON")
        if mode == "selftest":
            if (result_guided.get("status") != "PASS_OFFLINE"
                    or result_guided.get("tests") != 25
                    or result_guided.get("model_calls") != 0
                    or result_guided.get("new_model_worker_tasks") != 0
                    or result_guided.get("production_writes") != 0
                    or result_guided.get("cross_host_lease") is not False):
                fail("P0 Mac guided QA negatives overstated green/authority")
        else:
            if (result_guided.get("status") != "PASS_HISTORICAL_METADATA_ONLY"
                    or result_guided.get("successful_coding_tasks") != 1
                    or result_guided.get("failed_qa_tasks") != 1
                    or result_guided.get("distinct_task_families") != 2
                    or result_guided.get("original_failed_journals_preserved")
                       is not True
                    or result_guided.get("model_invocations_by_verifier") != 0
                    or result_guided.get("two_host_success_proven") is not False
                    or result_guided.get("causal_prompt_improvement_proven")
                       is not False
                    or result_guided.get("production_authority") is not False):
                fail("P0 Mac guided outcome failed sealed historical contract")

    # #612: New separate local-model diverse Worker emitted no false
    # successes for two actual Mac model-backed code attempts. Both exact
    # original journals remain UNKNOWN, independently read-only QA-audited.
    # Windows was admitted without touching active CAD/GPU or launching model.
    diverse_worker_file = ROOT / "scripts" / "vf_office_v2_p0_diverse_local_worker.py"
    diverse_failure_path = (P2 / "p0-two-diverse-real-model-qa-failclosed-2026-10-09.json")
    executed_diverse_worker_src = "c08a8413f59a1924c013adc66f523c897f1e477fae810f2c76127699d4262087"
    expected_diverse_worker_src = "4bab56091da28e18d7ad5e28023ddaedbbdc5537c10340e02bdd330a862e6d06"
    if hashlib.sha256(diverse_worker_file.read_bytes()).hexdigest() != expected_diverse_worker_src:
        fail("P0 diverse model worker actual source byte pin changed")
    diverse_tests = subprocess.run(
        [sys.executable, str(diverse_worker_file), "selftest"],
        cwd=ROOT, capture_output=True, text=True, timeout=35,
    )
    if diverse_tests.returncode:
        fail("P0 diverse Worker offline negative suite failed: " +
             diverse_tests.stdout[:150])
    try:
        check_result = json.loads(diverse_tests.stdout)
        failure_proof = json.loads(diverse_failure_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fail("P0 diverse Worker historical failures missing/invalid")
    if (
        check_result.get("status") != "PASS_OFFLINE"
        or check_result.get("tests") != 35
        or check_result.get("model_invocations") != 0
        or check_result.get("different_tasks_model_proven") is not False
        or check_result.get("automatic_retry") is not False
        or check_result.get("production_authority") is not False
        or check_result.get("distributed_fencing_verified") is not False
        or failure_proof.get("schema") !=
           "velvetos.office-v2.p0-diverse-model-worker-failclosed-experimental-evidence.v0"
        or failure_proof.get("status") !=
           "PASS_TWO_REAL_MODEL_ATTEMPTS_FAILED_QA_AND_PRESERVED_JOURNALS_ONE_WINDOWS_ADMISSION_ONLY"
    ):
        fail("P0 diverse Qwen experiment falsely claims success or authority")
    diverse_source = failure_proof.get("executed_source") or {}
    if (
        diverse_source.get("base_main") !=
           "017178eee2fe46bd8d0833d1a91b743505437776"
        or diverse_source.get("initial_mac_worker_commit") !=
           "a90a42133526a6f4e989ac059ffc16e3a449a67b"
        or diverse_source.get("subsequent_mac_worker_commit") !=
           "46cb07f5879d25c9a19a79f4c8e7bed713d381de"
        or diverse_source.get("current_audit_source_commit") !=
           "949f948ca42ea20e1c9d8f1052b5bcf3ac5ec955"
        or diverse_source.get("current_audit_source_raw_sha256") !=
           executed_diverse_worker_src
        or diverse_source.get("model_digest") !=
           "7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13"
    ):
        fail("P0 diverse model source, host or actual executed digest drift")
    failed = failure_proof.get("mac_actual_failed_attempts") or {}
    expected_failed = {
        "merge-windows-v1": {
            "task": "p0-diverse-run-mac-merge-20261009-a",
            "raw": "187da326e9f8931d6a1c08bff575a16f2615262a920e81b9351e45afd7e9d37a",
            "self": "4607bc34a9a7ed7668f74fb290bf50786243d2727c7b1f41eaee17d1ba806427",
            "journal": "e909db6a1ab48bd5baaafece671c3a6cf825c6f804b7a273b7314e447fddd89d",
            "base": "336318a6440bbbc5efd6d56fec66007405722923",
            "target": "windows_merge.py",
            "unit": 0,
        },
        "canonical-tag-v1": {
            "task": "p0-diverse-run-mac-canonical-20261009-b",
            "raw": "12b61a9afda1148599dde31951519def6edda21072ba0e20d8f7a2792b18a3e8",
            "self": "25c4cd2f22c2790dffef6173c7aae746e1cbf5304a8b75e17bc3677cb408b547",
            "journal": "dbf9fa62bfdf6c9da85586810e30dbc0a6fba4c10e6bd5286419375ba5f8e7a3",
            "base": "c944a8b1ff44040925856517a65d47cc3e5cf834",
            "target": "canonical_tag.py",
            "unit": 1,
        },
    }
    if set(failed) != set(expected_failed):
        fail("P0 exactly two distinct real Mac negative coding outcomes needed")
    import vf_office_v2_p0_diverse_local_worker as diverse_worker
    for task_family, expect in expected_failed.items():
        info = failed[task_family]
        audit = info.get("audit") or {}
        try:
            diverse_worker.audit_record_validate(audit)
        except Exception as exc:
            fail("P0 historic failed original Aider QA was not validated: " + str(exc)[:120])
        qa = audit.get("independent_failed_qa") or {}
        historical = audit.get("historical_native_process_readback") or {}
        if (
            info.get("raw_audit_sha256") != expect["raw"]
            or audit.get("audit_sha256") != expect["self"]
            or audit.get("task_id") != expect["task"]
            or audit.get("host") != "MacMiniOffice.local"
            or audit.get("base_sha") != expect["base"]
            or audit.get("fixture_id") != task_family
            or audit.get("journal_sha256_raw") != expect["journal"]
            or qa.get("replay_changed_paths") != [expect["target"]]
            or qa.get("unit_exit") != expect["unit"]
            or qa.get("hidden_exit") != 1
            or qa.get("pass") is not False
            or historical.get("worker") != "HISTORICAL_PID_ABSENT"
            or historical.get("aider") != "HISTORICAL_PID_ABSENT"
            or audit.get("automatic_requeue_authorized") is not False
        ):
            fail("P0 original negative QA, OS birth or preserved journal pin drift")
    admitted = failure_proof.get("win_admitted_not_run") or {}
    if (
        admitted.get("task_id") != "p0-diverse-run-win-canonical-20261009-b"
        or admitted.get("host") != "Chris"
        or admitted.get("base_sha") !=
           "9463e189c29f48e7a9a8c956a38e6f9cadcf8f8d"
        or admitted.get("original_raw_envelope_sha256") !=
           "c84d36677b514595773516d4ebc990dd29c94868be0cd1ad9e823eb694df175f"
        or admitted.get("admitted_only") is not True
        or admitted.get("journal_exists") is not False
        or admitted.get("receipt_exists") is not False
        or admitted.get("model_started") is not False
    ):
        fail("P0 Windows Qwen9b was wrongly claimed to have executed")
    negative_limits = failure_proof.get("limits") or {}
    for flag in ("original_v1_worker_modified","production_authority",
                 "canonical_fleet_lease","cross_host_fencing_verified",
                 "automated_unknown_recovery_proven",
                 "two_successful_distinct_model_tasks_proven",
                 "two_host_model_concurrency_proven",
                 "operator_effort_quantified","token_counts_known",
                 "new_background_service"):
        if negative_limits.get(flag) is not False:
            fail("P0 general Worker LAB falsely asserts " + flag)
    if negative_limits.get("paid_model_or_api_calls") != 0:
        fail("P0 general Worker LAB falsely claims an external inference cost")
    # #612: Two genuinely distinct synthetic coding task families have
    # been byte-exact prepared on independent real Windows/Mac hosts. This
    # does NOT mean either model worker has been run, PR created, or lease won.
    diverse_script = ROOT / "scripts" / "vf_office_v2_p0_diverse_task_fixtures.py"
    diverse_proof_path = P2 / "p0-two-host-diverse-prepared-fixtures-2026-10-09.json"
    expected_diverse_source = "2bc85ad0b028c959ba2b958c6184ef682bc68325aca1c6a78a93e49385378af3"
    if hashlib.sha256(diverse_script.read_bytes()).hexdigest() != expected_diverse_source:
        fail("P0 diverse preparation source bytes changed")
    prep_tests = subprocess.run(
        [sys.executable, str(diverse_script), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=35,
    )
    if prep_tests.returncode:
        fail("P0 diverse fixture source/golden adversarial QA failed: " +
             prep_tests.stdout[:180])
    try:
        prep_result = json.loads(prep_tests.stdout)
        prepared_record = json.loads(diverse_proof_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fail("P0 two-host diverse preparation evidence absent or invalid")
    if (
        prep_result.get("status") != "PASS_OFFLINE"
        or prep_result.get("tests") != 11
        or prep_result.get("fixture_count") != 2
        or prep_result.get("model_calls") != 0
        or prep_result.get("external_effects") != 0
        or prep_result.get("v1_worker_ready") is not False
        or prep_result.get("different_live_coding_tasks_proven") is not False
        or prepared_record.get("schema") !=
           "velvetos.office-v2.p0-two-host-diverse-fixtures-preparation-evidence.v0"
        or prepared_record.get("status") !=
           "PASS_TWO_DIFFERENT_HOST_BOUND_PREPARATIONS_ONLY_NOT_MODEL_TASKS"
    ):
        fail("P0 diverse preparation is not limited to offline tasks")
    executed = prepared_record.get("executed_source") or {}
    if (
        executed.get("main_at_start") !=
           "4f1cc80537430b5d18bf5747f543118a7ee54887"
        or executed.get("script_commit") !=
           "5823591da1072e87c1290de9d3bfdb461b7ea565"
        or executed.get("script_source_sha256") != expected_diverse_source
        or executed.get("script_git_blob") !=
           "8bd62db1065501cec356f4e554184dbac15e10a7"
        or executed.get("offline_adversarial_selftests_each_host") != 11
        or executed.get("seed_fails_visible_or_hidden_for_each") is not True
        or executed.get("golden_passes_visible_three_and_hidden_twelve_for_each") is not True
    ):
        fail("P0 diverse fixture original source or QA proof drift")
    bounds = prepared_record.get("limits") or {}
    for k in ("cross_host_concurrent_workers_proven",
              "actual_software_product_changes_proven",
              "protected_pr_from_coding_worker_proven",
              "original_v1_worker_accepts_these_tasks",
              "autonomous_recovery_proven", "distributed_fencing_verified",
              "canonical_fleet_lease", "production_writer",
              "customer_or_printer_effects"):
        if bounds.get(k) is not False:
            fail("P0 diverse prepared-only claim inflated: " + k)
    if (
        bounds.get("actual_model_tasks_executed") != 0
        or bounds.get("paid_api_calls") != 0
        or bounds.get("model_invocations") != 0
        or (prepared_record.get("failed_preliminary_windows") or {}).get(
            "automatic_retry") is not False
    ):
        fail("P0 diverse prep falsely claims models/cost/retries")
    origins = prepared_record.get("prepared") or {}
    expected_origins = {
        "windows": ("Chris", "canonical-tag-v1",
                    "p0-diverse-win-canonical-tag-20261009-b",
                    "9463e189c29f48e7a9a8c956a38e6f9cadcf8f8d",
                    "92aa42ba0e6795e0b2a2a243d43bf7ed185684611abb40a1cae536fac6e565f6",
                    "ae04bb38ed2c3df118b658b04d413a20112899b83cf2b003d3c99191782e1582"),
        "mac": ("MacMiniOffice.local", "merge-windows-v1",
                "p0-diverse-mac-merge-windows-20261009",
                "336318a6440bbbc5efd6d56fec66007405722923",
                "ab9d7c1da5b167b275a732201c2f501ad864db0891421381c9d8e2874e1c58d8",
                "5e215da8c7fe14eee06fd81bcf07e81b989c6e1ec12edf8efc3a64dd5672782a"),
    }
    if set(origins) != set(expected_origins):
        fail("P0 two different physical host preparations required")
    for host_key, (host, family, task, base, raw, selfhash) in expected_origins.items():
        obj = origins[host_key]
        fixture = (prep_result.get("fixtures") or {}).get(family) or {}
        if (
            obj.get("host") != host or obj.get("fixture_id") != family
            or obj.get("task_id") != task or obj.get("base_sha") != base
            or obj.get("raw_candidate_sha256") != raw
            or obj.get("proof_self_hash") != selfhash
            or obj.get("source_sha256") != fixture.get("seed_sha256")
            or obj.get("visible_sha256") != fixture.get("visible_sha256")
            or obj.get("hidden_sha256") != fixture.get("hidden_sha256")
            or obj.get("prompt_sha256") != fixture.get("prompt_sha256")
            or obj.get("target_file") != fixture.get("target")
            or obj.get("candidate_status") !=
               "PREPARED_ONLY_NOT_EXECUTABLE_BY_V1_WORKER"
            or obj.get("independent_host_verify") !=
               "PASS_PREPARED_ONLY_INDEPENDENT_BYTE_GIT_QA_READBACK"
            or obj.get("model_invocations") != 0
            or obj.get("production_authority") is not False
        ):
            fail("P0 original distinct task fixture/hash/host drift")

    # #612: Native Ollama serve+runner observed beside one original real
    # Qwen/Aider Mac Worker. CI runs ONLY offline tests/receipt verification.
    ollama_observer_script = ROOT / "scripts" / "vf_office_v2_p0_ollama_runner_resource_lab.py"
    ollama_history_path = P2 / "p0-mac-real-ollama-runner-correlated-resources-2026-10-09.json"
    expected_ollama_source = "6c57e5c4bd06105134aeba6f5c960c0d08e4af605364dd7ca0699d4becefacc8"
    if hashlib.sha256(ollama_observer_script.read_bytes()).hexdigest() != expected_ollama_source:
        fail("P0 Ollama native runner observer source byte drift")
    ollama_offline = subprocess.run(
        [sys.executable, str(ollama_observer_script), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if ollama_offline.returncode:
        fail("P0 Ollama offline test failed: " + ollama_offline.stdout[:180])
    try:
        ollama_checks = json.loads(ollama_offline.stdout)
        ollama_history = json.loads(ollama_history_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fail("P0 Ollama historic observations missing or malformed")
    if (
        ollama_checks.get("status") != "PASS_OFFLINE"
        or ollama_checks.get("tests") != 26
        or ollama_checks.get("model_invocations") != 0
        or ollama_checks.get("operating_system_queries") != 0
        or ollama_checks.get("actual_gpu_vram_measured") is not False
        or ollama_checks.get("distributed_fencing_verified") is not False
        or ollama_checks.get("production_authority") is not False
        or ollama_history.get("schema") !=
           "velvetos.office-v2.p0-real-mac-ollama-runner-observed-evidence.v0"
        or ollama_history.get("status") !=
           "PASS_CORRELATED_PINNED_MAC_OLLAMA_RUNNER_AND_INDEPENDENT_WORKER_QA"
    ):
        fail("P0 Ollama observer offline authority or report failed")
    run_source = ollama_history.get("source") or {}
    original_raw = ollama_history.get("raw_file_sha256") or {}
    expected_raw = {
        "envelope_sha256": "fda549a0feb58b5e03f456720a559e890d37e130eb75d7f99780e7453f6f3fae",
        "receipt_sha256": "2522204a87f531d53faf97e3ab335066954da5cd40c6d1c751559a871e08f012",
        "kernel_pin_sha256": "d0e02c179cbf56807c3f18b9524444fbacc05ae22192bd9b3ea3b4f82d20a116",
        "observer_sha256": "488aa3bd22ae200b78f40c5e1a321fb81321bb994e4ff2c2ddcf4f962bbabff9",
    }
    if (
        run_source.get("executed_script_commit") !=
           "468f070da8d88c113210328b1be7cf8a7fbb9927"
        or run_source.get("script_raw_sha256") != expected_ollama_source
        or run_source.get("host") != "MacMiniOffice.local"
        or run_source.get("model_name") != "qwen3.5:4b"
        or run_source.get("model_digest") !=
           "7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13"
        or original_raw != expected_raw
    ):
        fail("P0 real Ollama source/model/raw byte pin drift")
    original_task = ollama_history.get("envelope") or {}
    original_worker = ollama_history.get("model_worker") or {}
    model_qa = original_worker.get("independent_qa") or {}
    expected_task = "p0-ollama-observed-mac-20261009-02"
    original_pin = ollama_history.get("kernel_process_pin") or {}
    if (
        original_task.get("task_id") != expected_task
        or original_task.get("base_sha") != "ecabd70a292bc11ae4d8009a44502cb42ca1c0c9"
        or original_worker.get("task_id") != expected_task
        or original_worker.get("state") != "SUCCEEDED"
        or original_worker.get("elapsed_seconds") != 43.341
        or original_worker.get("receipt_selfhash") !=
           "3ef20205569c88108191e59d40ee7cf3d823d28a9a0da150d118b43bf66ec02b"
        or original_worker.get("kernel_pin_sha256") != original_pin.get("pin_sha256")
        or original_worker.get("model_invocations_min") != 1
        or original_worker.get("exact_model_calls") is not None
        or original_worker.get("additional_api_spend_usd") != 0
        or original_worker.get("separate_worker_verify") != "PASS"
        or model_qa.get("pass") is not True
        or model_qa.get("unit_3_verified") is not True
        or model_qa.get("hidden_12_verified") is not True
        or model_qa.get("replay_changed_paths") != ["slug.py"]
    ):
        fail("P0 Ollama real coding Worker independent QA not proven")
    lab_limits = ollama_history.get("limits") or {}
    for flag in ("model_exclusive_clients_proven", "host_wide_memory_usage_attributed",
                 "ollama_api_reported_size_vram_is_direct_gpu_measurement",
                 "actual_gpu_vram_measured", "cross_host_distributed_fencing",
                 "canonical_fleet_lease", "autonomous_retry_or_recovery_proven",
                 "production_authority", "all_process_descendants_excluded",
                 "exact_model_invocation_count_known", "long_tail_latency_reliably_estimated"):
        if lab_limits.get(flag) is not False:
            fail("P0 Ollama observation falsely grants " + flag)
    if (
        lab_limits.get("model_server_and_runner_rss_samples_observed") is not True
        or lab_limits.get("paid_api_spend_usd") != 0
        or lab_limits.get("observer_model_calls") != 0
        or (ollama_history.get("failed_preliminary_observer") or {}).get(
            "fresh_second_task_used") is not True
    ):
        fail("P0 Ollama observation spend and new-task negative control failed")
    import vf_office_v2_p0_ollama_runner_resource_lab as ollama_lab
    observed_report = (ollama_history.get("inference_runner_observer") or {}).get("report") or {}
    try:
        ollama_lab.validate(observed_report)
    except Exception as exc:
        fail("P0 real Ollama history not validated: " + str(exc)[:120])
    if (
        observed_report.get("task_id") != expected_task
        or observed_report.get("observation_sha256") !=
           "f1d020804841632d16c21766692b1bf9fc4d64e605d1f729b6a798c9916fe263"
        or observed_report.get("sample_count") != 10
        or observed_report.get("baseline_model_preloaded") is not False
        or observed_report.get("startup_api_unavailable_count") != 1
        or observed_report.get("runner_birth", {}).get("pid") != 69666
        or observed_report.get("server_birth", {}).get("pid") != 99094
        or observed_report.get("peak_runner_rss_bytes") != 3687776256
        or observed_report.get("peak_server_rss_bytes") != 22429696
        or observed_report.get("observed_runner_cpu_delta_ms") != 2126
        or observed_report.get("samples", [{}])[0].get("api_size_vram_bytes") != 3953628688
        or observed_report.get("pin_sha256") != original_worker.get("kernel_pin_sha256")
        or observed_report.get("worker_birth") != original_pin.get("worker")
        or observed_report.get("aider_birth") != original_pin.get("aider")
        or (ollama_history.get("inference_runner_observer") or {}).get(
            "separate_observer_verify") !=
           "PASS_OFFLINE_HISTORICAL_REPORT_NOT_LIVE_ATTESTATION"
    ):
        fail("P0 original Ollama native born PID samples/source drift")

    # #612: One real Mac local Aider+Qwen coding run had its exact Worker
    # and child Aider OS PID/birth pinned BEFORE/AFTER 12 read-only CPU/RSS
    # samples. Static CI checks historical receipts only, never starts model.
    owned_sampler = ROOT / "scripts" / "vf_office_v2_p0_owned_worker_aider_sampler.py"
    owned_data = P2 / "p0-mac-real-worker-aider-resource-observation-2026-10-09.json"
    expected_owned_src = "ad52d5ce56f504ac1e6105b4e4cc32801fea6f21cb3104512a2b3a01cd2fcaf7"
    if hashlib.sha256(owned_sampler.read_bytes()).hexdigest() != expected_owned_src:
        fail("P0 real Worker/Aider OS sampler source pin drift")
    owned_contract = subprocess.run(
        [sys.executable, str(owned_sampler), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if owned_contract.returncode:
        fail("P0 real Worker/Aider sampling negatives failed: " +
             owned_contract.stdout[:220])
    try:
        owned_checks = json.loads(owned_contract.stdout)
        owned_proof = json.loads(owned_data.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fail("P0 real Worker/Aider historical evidence missing/invalid")
    if (
        owned_checks.get("status") != "PASS_OFFLINE"
        or owned_checks.get("tests") != 26
        or owned_checks.get("live_os_calls") != 0
        or owned_checks.get("model_calls_by_observer") != 0
        or owned_checks.get("automatic_retries_authorized") is not False
        or owned_checks.get("production_authority") is not False
        or owned_checks.get("gpu_vram_measured") is not False
        or owned_proof.get("schema") !=
           "velvetos.office-v2.p0-live-mac-worker-aider-cpu-rss-evidence.v0"
        or owned_proof.get("status") !=
           "PASS_REAL_LOCAL_MODEL_WORKER_AND_AIDER_OS_PINNED_METRICS_LAB"
    ):
        fail("P0 real Worker/Aider LAB false execution, authority or evidence")
    real_src = owned_proof.get("source") or {}
    expected_id = "p0-observed-worker-mac-20261009-01"
    model_digest = "7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13"
    if (
        real_src.get("host") != "MacMiniOffice.local"
        or real_src.get("executed_head") !=
           "5d8b6613c18b3973344efe193fac139ec9bc458d"
        or real_src.get("observer_source_sha256") != expected_owned_src
        or real_src.get("original_model_worker_source_sha256") !=
           "7b4cb176c9c66351f9658c08589f45ec94d50c2a8b6450fe8e5cb1d8f09d86f7"
        or real_src.get("model") != "qwen3.5:4b"
        or real_src.get("model_digest") != model_digest
    ):
        fail("P0 real Worker/Aider pin/model identity drift")
    expected_raw = {
        "envelope": "b45932d4feae257f0de11329d3f84288ac3e45745301e08ecd91cec012ef0767",
        "receipt": "0ec632d2fecd772756ddbaf5a0eff5aaf4ef49220fa3bc2ece7475e3e19fdefe",
        "pin": "8c5bc727bea0ee9a4d2c3893370693b437c82f9cc167d61f91ea5f07843ee319",
        "observer": "6d764e33f210fe207d399919daa073a8e0a4816fdc3e2919859ff50053d4ce28",
    }
    if owned_proof.get("raw_artifact_hashes") != expected_raw:
        fail("P0 real Worker/Aider original Mac raw hashes changed")
    owned_task = owned_proof.get("task") or {}
    owned_rcpt = owned_task.get("worker_model_receipt") or {}
    qa = owned_rcpt.get("independent_qa") or {}
    if (
        owned_task.get("task_id") != expected_id
        or owned_task.get("base_sha") !=
           "17e304738bd05f526b6c29174dd3f6b6cc9b8d9e"
        or owned_rcpt.get("task_id") != expected_id
        or owned_rcpt.get("state") != "SUCCEEDED"
        or owned_rcpt.get("receipt_selfhash") !=
           "9de9ff084b1bfd8e5258f7732ad8e2a449681b131143522308e9a4d3b185f1ba"
        or owned_rcpt.get("model_digest") != model_digest
        or owned_rcpt.get("elapsed_seconds") != 49.241
        or owned_rcpt.get("artifact_sha256") !=
           "456f89bec0af23e6287e88956b8b85e992d4926b89e9613238bee7f77302ab45"
        or owned_rcpt.get("model_invocations_min") != 1
        or owned_rcpt.get("exact_model_calls") is not None
        or owned_rcpt.get("additional_api_spend_usd") != 0
        or owned_task.get("separate_original_worker_verify") != "PASS"
        or qa.get("pass") is not True
        or qa.get("unit_3_verified") is not True
        or qa.get("hidden_12_verified") is not True
        or qa.get("replay_changed_paths") != ["slug.py"]
    ):
        fail("P0 real Worker receipt not independently proven")
    owned_limits = owned_proof.get("limits") or {}
    for flag in ("separate_sampling_process_spawned_model", "model_inference_server_measured",
                 "gpu_vram_measured", "entire_process_family_measured",
                 "production_authority", "canonical_fleet_lease",
                 "distributed_fencing_verified", "automated_unknown_recovery_proven",
                 "statistically_reliable_peak_or_p95_proven",
                 "complete_os_orphan_exclusion"):
        if owned_limits.get(flag) is not False:
            fail("P0 actual Mac sampler overstated " + flag)
    if (owned_limits.get("actual_worker_and_aider_pair_cpu_rss_measured") is not True
            or owned_limits.get("model_calls_by_observer") != 0
            or owned_limits.get("additional_paid_api_spend_usd") != 0):
        fail("P0 actual Mac sampler misreported effects or coverage")
    import vf_office_v2_p0_owned_worker_aider_sampler as owned_observer
    owned_pin = owned_proof.get("process_pin") or {}
    witnessed = (owned_proof.get("observer") or {}).get("report") or {}
    try:
        owned_observer.validate(witnessed)
    except Exception as exc:
        fail("P0 real Mac sampled Worker/Aider historical report failed: "+
             str(exc)[:120])
    if (
        owned_pin.get("task_id") != expected_id
        or owned_pin.get("pin_sha256") != witnessed.get("kernel_pin_sha256")
        or owned_rcpt.get("kernel_pin_sha256") != witnessed.get("kernel_pin_sha256")
        or owned_pin.get("worker") != witnessed.get("worker_birth")
        or owned_pin.get("aider") != witnessed.get("aider_birth")
        or owned_pin.get("retry_permitted") is not False
        or witnessed.get("task_id") != expected_id
        or witnessed.get("observation_sha256") !=
           "06c68d07487b120389601a503089cfd7b050d2a4aa13ec6eab59aff53a5623cb"
        or witnessed.get("sample_count") != 12
        or witnessed.get("observed_peak_worker_rss_bytes") != 34930688
        or witnessed.get("observed_peak_aider_rss_bytes") != 172425216
        or witnessed.get("observed_peak_pair_rss_bytes") != 207339520
        or witnessed.get("observed_aider_cpu_delta_ms") != 4949
        or witnessed.get("observed_worker_cpu_delta_ms") != 0
        or (owned_proof.get("observer") or {}).get("separate_offline_verify") != "PASS"
    ):
        fail("P0 real Worker+Aider paired kernel resource proof drift")

    # #612: Native OS PID/birth-pinned RSS/CPU measurement on two owned
    # synthetic Python children. Pure offline replay only in CI.
    resource_script = ROOT / "scripts" / "vf_office_v2_p0_native_resource_probe_lab.py"
    resource_receipts = P2 / "p0-two-host-owned-resource-probe-2026-10-09.json"
    expected_resource_source = "a640328463d43ed1ab1b74c9585c1edc7681534aa3ac6928da001fbcb60d6b1e"
    if hashlib.sha256(resource_script.read_bytes()).hexdigest() != expected_resource_source:
        fail("P0 native resource observer source bytes changed")
    resource_test = subprocess.run(
        [sys.executable, str(resource_script), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if resource_test.returncode:
        fail("P0 native resource pure tests failed: " + resource_test.stdout[:220])
    try:
        sample_contract = json.loads(resource_test.stdout)
        historic_resource = json.loads(resource_receipts.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        fail("P0 native resource historical evidence invalid")
    if (
        sample_contract.get("status") != "PASS_OFFLINE"
        or sample_contract.get("tests") != 22
        or sample_contract.get("native_children_spawned") != 0
        or sample_contract.get("model_invocations") != 0
        or sample_contract.get("gpu_vram_measured") is not False
        or sample_contract.get("distributed_fencing_verified") is not False
        or sample_contract.get("all_possible_descendants_excluded") is not False
        or historic_resource.get("schema") !=
           "velvetos.office-v2.p0-native-owned-process-cpu-rss-dual-host-lab.v0"
        or historic_resource.get("status") !=
           "PASS_TWO_NATIVE_OWNED_RESOURCE_PROBES_SYNTHETIC_ONLY"
        or (historic_resource.get("original_source") or {}).get("script_git_blob") !=
           "e50ebddae5ccfc7463980958340be34e3b5bef9c"
        or (historic_resource.get("original_source") or {}).get("script_raw_source_sha256") !=
           expected_resource_source
    ):
        fail("P0 native resource historical controls overstated authority")
    resource_limits = historic_resource.get("limits") or {}
    for key in ("actual_model_process_resource_usage_proven",
                "per_model_cpu_ram_peak_measured",
                "gpu_vram_observed", "process_family_exhaustive",
                "all_escaped_descendants_excluded",
                "automatic_recovery_proven", "cross_host_fencing_verified",
                "production_writer", "canonical_fleet_lease",
                "host_process_enumeration", "unrelated_process_termination"):
        if resource_limits.get(key) is not False:
            fail("P0 native resource LAB falsely claims " + key)
    if (resource_limits.get("model_invocations") != 0
            or resource_limits.get("additional_api_spend_usd") != 0):
        fail("P0 native resource LAB falsified zero spend or model activity")
    import vf_office_v2_p0_native_resource_probe_lab as resource
    expected_reports = {
        "windows": ("Chris", "WINDOWS_CIM_CREATION_DATE",
                    "a872b53f5d560db404cc13d8bdee56f56b571f4c80d11d3213b8c79c5b7703ed",
                    "71e9bbb1cd301d8978deb45cf17a8f5dcb22ba5513ece4561dd8d99ede4d6529"),
        "mac": ("MacMiniOffice.local", "PSUTIL_OS_CREATE_TIME",
                "5be67076bd3a46cb2c97d062a1fd5a7096b1dc6ed1897cf444fbf815852bb98f",
                "0a38e8af93e7e6431dca4646a5c9ff6fe9bd7a9febf33d31b7dc94f684bde5d7"),
    }
    seen_resource = historic_resource.get("hosts") or {}
    if set(seen_resource) != set(expected_reports):
        fail("P0 native resource two real host proofs required")
    for host_label, (host_id, backend, seal, raw_sha) in expected_reports.items():
        row = seen_resource[host_label]
        record = row.get("report") or {}
        try:
            resource.validate(record)
        except Exception as exc:
            fail("P0 native resource sample receipt failed: " + str(exc)[:120])
        if (record.get("host") != host_id or record.get("kernel_backend") != backend
                or record.get("receipt_sha256") != seal
                or record.get("source_sha256") != expected_resource_source
                or row.get("raw_report_sha256") != raw_sha
                or record.get("sample_count") != 6
                or record.get("gpu_vram_measured") is not False):
            fail("P0 native resource physical host, source or historic hash drift")

    # #612: Five distinct real local Qwen/Aider Mac Task Envelopes already
    # independently QA-verified on origin host. CI validates ONLY sanitized
    # historical receipt identifiers/metrics; no inference, callbacks or launch.
    repeat_evidence_script = ROOT / "scripts" / "vf_office_v2_p0_repeat_model_evidence.py"
    repeat_evidence_path = P2 / "p0-mac-five-real-model-sequential-metrics-2026-10-09.json"
    if hashlib.sha256(repeat_evidence_script.read_bytes()).hexdigest() != (
            "ff33f05214562d278dc16173386107052e82800eee599242f796b19ff056af21"):
        fail("P0 real Mac repeat validator source bytes drift")
    for mode in ("selftest", "verify"):
        attempt = subprocess.run(
            [sys.executable, str(repeat_evidence_script), mode,
             "--evidence", str(repeat_evidence_path)],
            cwd=ROOT, text=True, capture_output=True, timeout=25,
        )
        if attempt.returncode:
            fail("P0 real Mac repeat evidence " + mode +
                 " rejected: " + attempt.stdout[:220])
        try:
            parsed = json.loads(attempt.stdout)
        except json.JSONDecodeError:
            fail("P0 real Mac repeat evidence returned invalid JSON")
        if mode == "selftest":
            if (
                parsed.get("status") != "PASS_OFFLINE"
                or parsed.get("tests") != 25
                or parsed.get("model_invocations") != 0
                or parsed.get("automatic_retries") != 0
                or parsed.get("scheduler_authority") is not False
                or parsed.get("statistically_robust_p95") is not False
                or parsed.get("production_effects") != 0
            ):
                fail("P0 real Mac repeat LAB offline negatives falsely passed")
        elif (
            parsed.get("status") !=
            "PASS_OFFLINE_HISTORICAL_RECORD_VALIDATED_NOT_LIVE_REPLAY"
            or parsed.get("samples") != 5
            or parsed.get("independent_worker_verifies_reported") != 5
            or parsed.get("median_seconds") != 46.331
            or parsed.get("sample_p95_nearest_rank_seconds") != 48.576
            or parsed.get("model_calls_during_verification") != 0
            or parsed.get("production_or_scheduler_authority") is not False
            or parsed.get("statistically_robust_p95") is not False
            or parsed.get("automatic_retries_authorized") is not False
        ):
            fail("P0 Mac repeat metrics promoted unsupported model/P95 claims")

    # #612: two real physical hosts tested O_EXCL same-host singleflight and
    # post-owner-loss sticky refusal. CI does NOT spawn any live subprocesses
    # from this experiment or mint a #604 cross-host lease.
    singleflight_script = ROOT / "scripts" / "vf_office_v2_p0_local_singleflight_lab.py"
    singleflight_test = subprocess.run(
        [sys.executable, str(singleflight_script), "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=25,
    )
    if singleflight_test.returncode:
        fail("P0 same-host reservation selftest failed: " + singleflight_test.stdout[:220])
    try:
        singleflight_checks = json.loads(singleflight_test.stdout)
        singleflight_proof = json.loads((P2 / "p0-two-host-local-singleflight-loss-2026-10-09.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        fail("P0 same-host historical receipts missing or invalid JSON")
    expected_source_sha = "c02e1374ad2a6775baef8c1231f0662932c0fb72d768188ae8666911e0826b8c"
    if (
        singleflight_checks.get("status") != "PASS_OFFLINE"
        or singleflight_checks.get("tests") != 25
        or singleflight_checks.get("real_children_spawned") != 0
        or singleflight_checks.get("model_calls") != 0
        or singleflight_checks.get("canonical_fleet_lease") is not False
        or singleflight_checks.get("distributed_fencing_verified") is not False
        or singleflight_checks.get("new_job_execution_authorized") is not False
        or singleflight_checks.get("original_unknown_retry_authorized") is not False
        or hashlib.sha256(singleflight_script.read_bytes()).hexdigest() != expected_source_sha
        or singleflight_proof.get("schema") !=
           "velvetos.office-v2.p0-two-host-local-exclusive-loss-proof.v0"
        or singleflight_proof.get("status") != "PASS_TWO_INDEPENDENT_SAME_HOST_LABS_ONLY"
        or singleflight_proof.get("executed_source_git_blob") !=
           "2526682600bb2b99b7bf4792bab091658c297607"
        or singleflight_proof.get("executed_source_windows_file_sha256") != expected_source_sha
        or singleflight_proof.get("offline_source_selftests") != "25/25 each Windows and Mac"
    ):
        fail("P0 same-host LAB source/negative-safety claims drift")
    singleflight_limits = singleflight_proof.get("limits") or {}
    for flag in ("canonical_fleet_lease", "distributed_fencing_verified",
                 "all_orphan_descendants_excluded", "original_unknown_retry_authorized",
                 "new_job_execution_authorized", "autonomous_recovery_proven",
                 "production_writer"):
        if singleflight_limits.get(flag) is not False:
            fail("P0 same-host LAB falsely grants " + flag)
    if (singleflight_limits.get("model_calls") != 0 or
        singleflight_limits.get("additional_api_spend_usd") != 0 or
        singleflight_limits.get("no_cross_host_shared_resource") is not True):
        fail("P0 same-host LAB misrepresents spend or cross-host lease")
    import vf_office_v2_p0_local_singleflight_lab as singleflight
    observed = singleflight_proof.get("observations") or {}
    expected_hosts = {
        "windows": ("Chris", "WINDOWS_CIM_CREATION_DATE",
                    "e4ca551d64d8284fc1848fc37aaf995fd5368576901cdccf832a70517354d65d",
                    "840a442f8e47dc5aa12244b0c56d9fc2ef64f81c00b437e525f8fc3dda75e25c"),
        "mac": ("MacMiniOffice.local", "PSUTIL_OS_CREATE_TIME",
                "4103291fc75701fe75bf9784e1c72e1d2d07a9468223b9ee8f3a5e08d06002f8",
                "5b7112d32e4c5e4ef03a831e6a29a0822803320304ad36610319c7e10a8a5b8c"),
    }
    if set(observed) != set(expected_hosts):
        fail("P0 same-host expected distinct physical host evidence missing")
    for key, (expected_host, backend, receipt_hash, raw_hash) in expected_hosts.items():
        pair = observed[key]
        claim = pair.get("claim") or {}
        report = pair.get("report") or {}
        try:
            singleflight.verify_claim(claim)
            singleflight.verify_report(report)
        except Exception as exc:
            fail("P0 same-host historical receipt failed: " + str(exc)[:150])
        if (claim.get("host") != expected_host
                or report.get("host") != expected_host
                or claim.get("kernel_identity", {}).get("source") != backend
                or report.get("winner") != claim.get("contender")
                or report.get("receipt_sha256") != receipt_hash
                or report.get("claim_sha256_raw") != raw_hash
                or report.get("model_calls") != 0
                or report.get("canonical_fleet_lease") is not False
                or report.get("distributed_fencing_verified") is not False):
            fail("P0 same-host historical win/mac receipt pin or authority drift")

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

    # #612: an additional denial-only guard catches collisions *between* fresh
    # attempts that individually pass comparison against an older UNKNOWN.
    batch_lineage_check = subprocess.run(
        [sys.executable,
         str(ROOT / "scripts" / "vf_office_v2_p0_batch_lineage_guard.py"),
         "--selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=30,
    )
    if batch_lineage_check.returncode != 0:
        fail("P0 batch fresh-attempt collision negative controls failed: " +
             batch_lineage_check.stdout[:250])
    try:
        batch_lineage = json.loads(batch_lineage_check.stdout)
    except json.JSONDecodeError:
        fail("P0 batch lineage audit JSON invalid")
    if (batch_lineage.get("status") != "PASS_OFFLINE"
            or batch_lineage.get("tests") != 15
            or batch_lineage.get("model_invocations") != 0
            or batch_lineage.get("dispatches") != 0
            or batch_lineage.get("retries") != 0
            or batch_lineage.get("production_effects") != 0):
        fail("P0 batch lineage guard unsafe or incomplete")

    # #612 consumer-only fencing: *synthetic*, denial-only, no #604 lease
    # issuance or integration with live effect/write boundaries.
    fence_source = ROOT / "scripts" / "vf_office_v2_p0_fenced_effect_consumer_lab.py"
    if hashlib.sha256(fence_source.read_bytes()).hexdigest() != (
        "1359f5fbaf6902dbc02cf86e8174d11b0912f76f69b72df2ba48c98581d85dc5"
    ):
        fail("P0 fenced-effect consumer exact source provenance changed")
    fenced_consumer_check = subprocess.run(
        [sys.executable,
         str(ROOT / "scripts" / "vf_office_v2_p0_fenced_effect_consumer_lab.py"),
         "selftest"],
        cwd=ROOT, text=True, capture_output=True, timeout=30,
    )
    if fenced_consumer_check.returncode != 0:
        fail("P0 synthetic fenced-effect consumer tests failed: " +
             fenced_consumer_check.stdout[:250] +
             fenced_consumer_check.stderr[:150])
    try:
        fence_contract = json.loads(fenced_consumer_check.stdout)
    except json.JSONDecodeError:
        fail("P0 synthetic fenced-effect consumer JSON invalid")
    if (
        fence_contract.get("status") != "PASS_OFFLINE"
        or fence_contract.get("tests") != 47
        or fence_contract.get("synthetic_provider_only") is not True
        or fence_contract.get("real_lease_issued") is not False
        or fence_contract.get("model_invocations") != 0
        or fence_contract.get("dispatches") != 0
        or fence_contract.get("retries") != 0
        or fence_contract.get("writes_authorized") != 0
        or fence_contract.get("effects_committed") != 0
        or fence_contract.get("production_effects") != 0
    ):
        fail("P0 fenced-effect consumer false-positive authority regression")

    # #612: independent comparison of TWO already-successful distinct local
    # coding tasks on Chris Windows and Mac Mini; no new model/lease/PR run.
    two_host_witness = ROOT / "scripts" / "vf_office_v2_p0_two_host_coding_witness.py"
    if hashlib.sha256(two_host_witness.read_bytes()).hexdigest() != (
        "93f34b7aa8fd9e4d58bf0d2ea07d2122393b8eda62503b140d7ca71edbc5a3b7"
    ):
        fail("P0 two-host historical coding witness source provenance drift")
    for mode in ("selftest", "verify"):
        result = subprocess.run(
            [sys.executable, str(two_host_witness), mode],
            cwd=ROOT, text=True, capture_output=True, timeout=35,
        )
        if result.returncode != 0:
            fail("P0 two-host historical coding evidence refused " + mode + ": " +
                 result.stdout[:200] + result.stderr[:100])
        try:
            witness = json.loads(result.stdout)
        except json.JSONDecodeError:
            fail("P0 two-host historical coding witness JSON invalid")
        if mode == "selftest":
            if (witness.get("status") != "PASS_OFFLINE"
                    or witness.get("tests") != 31
                    or witness.get("model_invocations") != 0
                    or witness.get("production_effects") != 0
                    or witness.get("no_retries") is not True):
                fail("P0 two-host historic witness adversarial regression")
        else:
            if (witness.get("status") !=
                    "PASS_TWO_HOST_DISTINCT_HISTORICAL_CODING_QA_ONLY"
                    or witness.get("hosts") != ["Chris", "MacMiniOffice.local"]
                    or witness.get("code_families") != ["slug.py", "windows_merge.py"]
                    or witness.get("historic_successes_with_independent_qa") != 2
                    or witness.get("original_receipt_bytes_checked_by_CI") is not False
                    or witness.get("simultaneous_cross_host_execution_proven") is not False
                    or witness.get("distributed_lease_proven") is not False
                    or witness.get("agent_authored_pr_or_merge_proven") is not False
                    or witness.get("autonomous_recovery_proven") is not False
                    or witness.get("historical_failed_attempts_retried") is not False
                    or witness.get("current_new_model_invocations") != 0
                    or witness.get("production_effects") != 0):
                fail("P0 two-host evidence promoted beyond original historic QA scope")

    print(
        "OK office-v2-contracts authority=single writer_change=NO credentials=LAB_DENIED "
        f"candidates={len(items)} phase3_effects=LAB_LOCAL_ONLY"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
