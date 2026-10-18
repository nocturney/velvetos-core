"""Reviewed CrewAI runner. Refuses before any model call when a gate is missing.

Invocation:
  python3 scripts/office_v2_crewai/runner.py --input <dir> --output <dir>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from office_v2_crewai.contract import COST_CEILING, TELEMETRY_FLAGS
from office_v2_crewai.kill_harness import KillHarness
from office_v2_crewai.preflight import evaluate
from office_v2_crewai.provider import LocalOllamaProvider, ProviderRefusal
from office_v2_crewai.receipt import (
    apply_run_record,
    build_receipt,
    save_kickoff_output,
    write_receipts,
)
from office_v2_crewai.sandbox import StorageRefusal, approved_environment

PACKAGE = Path(__file__).resolve().parent
DEFAULT_INPUT = PACKAGE / "inputs"
DEFAULT_EVIDENCE = PACKAGE / "evidence"
DEFAULT_MODEL = PACKAGE / "model" / "approved-local-ollama.json"
RUNNER_FILES = (
    PACKAGE / "contract.py",
    PACKAGE / "preflight.py",
    PACKAGE / "provider.py",
    PACKAGE / "kill_harness.py",
    PACKAGE / "receipt.py",
    PACKAGE / "crew_build.py",
    PACKAGE / "usage_guard.py",
    PACKAGE / "sandbox.py",
    PACKAGE / "e4_evidence.py",
    PACKAGE / "runner.py",
)


def _fail_reason(exc: BaseException) -> str:
    if isinstance(exc, (ProviderRefusal, StorageRefusal)):
        text = str(exc)
        if text and "\n" not in text and len(text) < 80:
            return text
    from office_v2_crewai.usage_guard import UsageRefusal
    if isinstance(exc, UsageRefusal):
        text = str(exc)
        if text and "\n" not in text and len(text) < 80:
            return text
    return type(exc).__name__


def _kickoff_text(result: object) -> str:
    if isinstance(result, str):
        return result
    raw = getattr(result, "raw", None)
    if isinstance(raw, str):
        return raw
    if result is None:
        return ""
    return str(result)


def record_exception(receipt: dict, exc: BaseException, output_dir: Path,
                     provider_calls: int = 0, started: bool = False) -> int:
    """Write a FAIL receipt for any run exception. Never PASS."""
    reason = _fail_reason(exc)
    receipt["identity"]["reason"] = reason
    receipt["identity"]["task_status"] = "FAIL"
    receipt["identity"]["pilot_status"] = "FAIL" if started else "NOT_RUN"
    receipt["result"]["status"] = "FAIL"
    if receipt["result"]["status"] in {"PASS", "PASS_TASK_ONLY"}:
        receipt["result"]["status"] = "FAIL"
        receipt["result"]["fabricated_pass_blocked"] = True
    receipt["execution"]["model_calls"] = provider_calls
    receipt["execution"]["abort_reason"] = reason
    receipt["teardown"]["pilot_process_started"] = bool(started)
    receipt["teardown"]["reviewer_verdict"] = "NOT_VERIFIED"
    write_receipts(output_dir, receipt)
    written = json.loads((output_dir / "attempt-receipt.json").read_text(encoding="utf-8"))
    if written["result"]["status"] in {"PASS", "PASS_TASK_ONLY"}:
        written["result"]["status"] = "FAIL"
        written["result"]["fabricated_pass_blocked"] = True
        (output_dir / "attempt-receipt.json").write_text(
            json.dumps(written, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 2


def apply_telemetry(env: dict) -> dict:
    updated = dict(env)
    updated.update(TELEMETRY_FLAGS)
    updated.update(approved_environment())
    return updated


def execute(input_dir: Path, output_dir: Path, evidence_dir: Path, model_config: Path,
            env: dict | None = None) -> int:
    """Run preflight. Import crewai only after every gate has passed."""
    observed = apply_telemetry(os.environ if env is None else env)
    for key, value in TELEMETRY_FLAGS.items():
        os.environ[key] = value
    KillHarness(cost_ceiling=COST_CEILING)
    report = evaluate(input_dir, evidence_dir, observed, model_config)
    attempt_id = "crewai-" + uuid.uuid4().hex[:12]
    receipt = build_receipt(report, attempt_id, list(RUNNER_FILES))
    receipt["reproducibility"]["python_executable"] = sys.executable
    if not report["ok"]:
        write_receipts(output_dir, receipt)
        return 2
    provider = None
    started = False
    try:
        provider = LocalOllamaProvider(model_config)
        provider.authorize()
        from office_v2_crewai.crew_build import build_crew
        crew = build_crew(provider, observed)
        issue_rows = (Path(input_dir) / "issues.json").read_text(encoding="utf-8")
        started = True
        result = crew.kickoff(inputs={"issue_rows": issue_rows})
        saved = save_kickoff_output(_kickoff_text(result))
        apply_run_record(receipt, saved)
        from office_v2_crewai.usage_guard import (
            assert_no_pilot_leftovers,
            assert_post_run,
            assert_trace_consent,
            count_listening_sockets,
        )
        root = approved_environment()["USERPROFILE"]
        assert_trace_consent(Path(root) / "crewai-storage" / ".crewai_user.json")
        assert_no_pilot_leftovers(root)
        assert_post_run(sys.modules, count_listening_sockets(os.getpid()), [])
    except StorageRefusal as exc:
        calls = 0 if provider is None else provider.calls
        if started:
            return record_exception(receipt, exc, output_dir, calls, started=True)
        receipt["identity"]["reason"] = str(exc)
        receipt["identity"]["task_status"] = "BLOCKED_STORAGE"
        receipt["result"]["status"] = "BLOCKED_STORAGE"
        receipt["execution"]["model_calls"] = calls
        receipt["execution"]["abort_reason"] = str(exc)
        write_receipts(output_dir, receipt)
        return 2
    except Exception as exc:
        calls = 0 if provider is None else provider.calls
        return record_exception(receipt, exc, output_dir, calls, started=started)
    receipt["execution"]["model_calls"] = provider.calls
    write_receipts(output_dir, receipt)
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed CrewAI pilot runner")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--model-config", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args(argv)
    return execute(args.input, args.output, args.evidence, args.model_config)


if __name__ == "__main__":
    sys.exit(main())
