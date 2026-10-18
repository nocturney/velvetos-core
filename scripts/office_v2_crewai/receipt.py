"""Section 7 receipt writer. Never records a fabricated PASS."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from office_v2_crewai.contract import DIRECT_PINS, GATES, RESULT_STATUSES, SANDBOX_ROOT, TELEMETRY_FLAGS


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _digest(path: Path) -> str:
    if not path.is_file():
        return "ABSENT"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def overall_status(report: dict) -> str:
    statuses = [report["gates"][gate]["status"] for gate in GATES]
    if "BLOCKED_SECURITY" in statuses:
        return "BLOCKED_SECURITY"
    if "BLOCKED_STORAGE" in statuses:
        return "BLOCKED_STORAGE"
    if "PARKED_CAPACITY" in statuses:
        return "PARKED_CAPACITY"
    if statuses and all(status == "PASS" for status in statuses) and report.get("ok"):
        return "NOT_VERIFIED"
    return "NOT_RUN"


def build_receipt(report: dict, attempt_id: str, runner_files: list[Path]) -> dict:
    status = overall_status(report)
    if status not in RESULT_STATUSES or status == "PASS_TASK_ONLY":
        status = "NOT_VERIFIED"
    runner_hashes = {path.name: _digest(path) for path in runner_files}
    return {
        "schema": "velvetos.office-v2.crewai-attempt-receipt.v1",
        "identity": {
            "attempt_id": attempt_id,
            "utc_start": _now(),
            "utc_end": _now(),
            "operator": "NOT_VERIFIED",
            "independent_reviewer": "NOT_VERIFIED",
            "host": "NOT_VERIFIED",
            "windows_build": "NOT_VERIFIED",
            "approval_link": "NOT_VERIFIED",
            "lease_observation": "NOT_VERIFIED",
            "gates": {gate: report["gates"][gate]["status"] for gate in GATES},
            "gate_reasons": {gate: report["gates"][gate]["reason"] for gate in GATES},
            "task_status": status,
            "pilot_status": "NOT_RUN",
            "reason": ",".join(report.get("missing_gates") or []) or "PREFLIGHT_CLOSED",
        },
        "reproducibility": {
            "plan_commit": "d101809a88ea68ee4e2790aa3aba2d1fb5c40ea6",
            "runner_files_sha256": runner_hashes,
            "python_executable": "RECORDED_BY_RUNNER",
            "python_sha256": "NOT_VERIFIED",
            "venv_root": "NOT_VERIFIED",
            "lock_digest": "121c1bd04eee730b51eb71e49da503b0d0236cdd06d8687a5df792234f78a669",
            "security_scan": "RED",
            "model_digest": "NOT_USED",
        },
        "safety": {
            "direct_pins": list(DIRECT_PINS),
            "memory": False,
            "roles": ["Triage", "Reviewer"],
            "tool_count": 0,
            "code_execution": False,
            "telemetry_flags": dict(TELEMETRY_FLAGS),
            "tracing_context": "NOT_RUN",
            "build_tools_exception": False,
        },
        "graph_smoke": "NOT_RUN",
        "scope": {
            "sandbox_root": SANDBOX_ROOT,
            "input_sha256": "SEE_MANIFEST",
            "adversarial_is_data": True,
            "private_repo_included": False,
        },
        "execution": {
            "process_ids": [],
            "tool_registry_empty": True,
            "cost_additional": 0,
            "model_calls": report.get("model_calls", 0),
            "timeout_seconds": 600,
            "abort_reason": None if report.get("ok") else "PREFLIGHT_REFUSED",
        },
        "result": {
            "status": status,
            "output_sha256": {},
            "fabricated_id_count": 0,
            "negative_control": "PREFLIGHT_REFUSED" if not report.get("ok") else "NOT_RUN",
        },
        "teardown": {
            "pilot_process_started": False,
            "rollback_status": "NOT_RUN",
            "reviewer_verdict": "NOT_VERIFIED",
            "c_drive_audit": "NOT_VERIFIED",
        },
    }


def seal(receipt: dict) -> dict:
    """Downgrade any PASS that lacks an independent reviewer signature."""
    result = receipt.setdefault("result", {})
    teardown = receipt.setdefault("teardown", {})
    if result.get("status") in {"PASS", "PASS_TASK_ONLY"}:
        if teardown.get("reviewer_verdict") != "PASS":
            result["status"] = "NOT_VERIFIED"
            result["fabricated_pass_blocked"] = True
            receipt.setdefault("identity", {})["task_status"] = "NOT_VERIFIED"
    if receipt.get("execution", {}).get("model_calls", 0) and result.get("status") == "PASS_TASK_ONLY":
        result["status"] = "NOT_VERIFIED"
    return receipt


def write_receipts(output_dir: Path, receipt: dict) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    sealed = seal(receipt)
    attempt_path = output_dir / "attempt-receipt.json"
    summary_path = output_dir / "summary.md"
    summary_path.write_text("NOT_RUN\n", encoding="utf-8")
    sealed["result"]["output_sha256"] = {
        "summary.md": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
    }
    attempt_path.write_text(json.dumps(sealed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    postflight = {
        "schema": "velvetos.office-v2.crewai-postflight-receipt.v1",
        "attempt_id": sealed["identity"]["attempt_id"],
        "utc": sealed["identity"]["utc_end"],
        "pilot_process_started": False,
        "rollback_status": "NOT_RUN",
        "reviewer_verdict": "NOT_VERIFIED",
        "result_status": sealed["result"]["status"],
        "attempt_receipt_sha256": hashlib.sha256(attempt_path.read_bytes()).hexdigest(),
        "summary_sha256": sealed["result"]["output_sha256"]["summary.md"],
        "note": "No pilot process was started. This record is not ROLLBACK_VERIFIED and not PASS.",
    }
    (output_dir / "postflight-receipt.json").write_text(
        json.dumps(postflight, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return sealed
