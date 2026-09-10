#!/usr/bin/env python3
"""Sensor for VelvetOS autonomy composition."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "packages" / "velvetos" / "living-studio" / "AUTONOMY.json"
CLI = ROOT / "scripts" / "vf_autonomy.py"
CONTROL_PLANE = ROOT / "office" / "control-plane.json"
POLICY = ROOT / "office" / "control" / "POLICY.md"

EXPECTED_COMPONENTS = {
    "foundation-runtime-contract",
    "router-context-engine",
    "blocker-waiting-engine",
    "project-lifecycle-engine",
    "approval-system",
    "reliability-exception-engine",
    "work-prioritization",
    "background-executor-policy",
}
REQUIRED_IDS = {"run_id", "idempotency_key", "correlation_id"}
REQUIRED_STATES = {"queued", "running", "waiting_approval", "completed", "failed"}
FORBIDDEN_DUPLICATE_WRITES = {
    "new approval queue",
    "second approval queue",
    "new event bus",
    "second event bus",
    "new database",
    "second database",
    "new runtime",
    "second runtime",
}


def fail(errors: list[str]) -> int:
    for error in errors:
        print(f"FAIL {error}", file=sys.stderr)
    return 1


def main() -> int:
    errors: list[str] = []
    for path in (CONFIG, CLI, CONTROL_PLANE, POLICY):
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")
    if errors:
        return fail(errors)

    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception as exc:
        return fail([f"AUTONOMY.json invalid JSON: {exc}"])

    ids = {str(c.get("id")) for c in cfg.get("components") or []}
    missing = sorted(EXPECTED_COMPONENTS - ids)
    if missing:
        errors.append("missing autonomy components: " + ", ".join(missing))

    contract = cfg.get("executionContract") or {}
    required_ids = set(contract.get("requiredIds") or [])
    missing_ids = sorted(REQUIRED_IDS - required_ids)
    if missing_ids:
        errors.append("execution contract missing ids: " + ", ".join(missing_ids))
    states = set(contract.get("states") or [])
    missing_states = sorted(REQUIRED_STATES - states)
    if missing_states:
        errors.append("execution contract missing states: " + ", ".join(missing_states))

    retry = contract.get("retry") or {}
    if retry.get("beforeRetry") != "reconcile actual external/internal state":
        errors.append("retry must reconcile actual state before retry")
    if retry.get("neverRetryBlindly") is not True:
        errors.append("blind retry must remain forbidden")
    if int(retry.get("maxAutomaticRetries", 99)) > 1:
        errors.append("automatic retries exceed one")

    rules = cfg.get("businessRules") or {}
    if rules.get("pickupOnly") != "Sderot":
        errors.append("Velvet Factory pickup rule must remain Sderot")
    if rules.get("nationwideShipping") is not False:
        errors.append("nationwide shipping must remain false")
    if rules.get("customerWhatsAppSend") != "human":
        errors.append("customer WhatsApp send must remain human")
    if rules.get("inventSaleILS") is not False or rules.get("inventInsights") is not False:
        errors.append("invented price/Insights locks must remain false")
    if rules.get("destructiveAutonomy") is not False:
        errors.append("destructive autonomy must remain false")

    whole = CONFIG.read_text(encoding="utf-8").lower()
    for phrase in FORBIDDEN_DUPLICATE_WRITES:
        if phrase in whole and "not a second" not in whole and "do not" not in whole:
            errors.append(f"possible duplicate architecture introduced: {phrase}")

    projection_components = [c for c in cfg.get("components") or [] if c.get("kind") == "projection"]
    for component in projection_components:
        writes = component.get("writes") or []
        if writes not in (["none; projection only"], []):
            errors.append(f"projection {component.get('id')} must not own canonical writes")

    proc = subprocess.run(
        [sys.executable, str(CLI), "selftest"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "selftest failed").strip()
        errors.append(f"vf_autonomy selftest failed: {detail}")

    if errors:
        return fail(errors)
    print("OK vf-autonomy composition + contracts + business locks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
