"""Reviewed CrewAI runner. Refuses before any model call when a gate is missing.

Invocation:
  python3 scripts/office_v2_crewai/runner.py --input <dir> --output <dir>
"""
from __future__ import annotations

import argparse
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
from office_v2_crewai.receipt import build_receipt, write_receipts

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
    PACKAGE / "runner.py",
)


def apply_telemetry(env: dict) -> dict:
    updated = dict(env)
    updated.update(TELEMETRY_FLAGS)
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
    try:
        provider = LocalOllamaProvider(model_config)
        provider.authorize()
        from office_v2_crewai.crew_build import build_crew
        crew = build_crew(provider, observed)
        issue_rows = (Path(input_dir) / "issues.json").read_text(encoding="utf-8")
        crew.kickoff(inputs={"issue_rows": issue_rows})
        from office_v2_crewai.usage_guard import assert_post_run, count_listening_sockets
        assert_post_run(sys.modules, count_listening_sockets(os.getpid()), [])
    except (ProviderRefusal, ImportError, ModuleNotFoundError, OSError, RuntimeError) as exc:
        receipt["identity"]["reason"] = type(exc).__name__
        receipt["identity"]["task_status"] = "NOT_VERIFIED"
        receipt["result"]["status"] = "NOT_VERIFIED"
        receipt["execution"]["model_calls"] = 0 if provider is None else provider.calls
        receipt["execution"]["abort_reason"] = type(exc).__name__
        write_receipts(output_dir, receipt)
        return 2
    receipt["identity"]["reason"] = "AWAITING_INDEPENDENT_REVIEW"
    receipt["identity"]["task_status"] = "NOT_VERIFIED"
    receipt["result"]["status"] = "NOT_VERIFIED"
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
