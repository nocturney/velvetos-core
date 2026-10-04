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
VELVETOS_PACK = ROOT / "packages" / "velvetos"
if str(VELVETOS_PACK) not in sys.path:
    sys.path.insert(0, str(VELVETOS_PACK))
from living_studio_rules import LivingStudioRuleResolutionError, effective_business_rules  # type: ignore  # noqa: E402

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

    if "businessRules" in cfg:
        errors.append("AUTONOMY.json must not embed instance business-rule values after Stage 8C")
    resolution = cfg.get("businessRulesResolution") or {}
    if resolution != {
        "resolver": "packages/velvetos/living_studio_rules.py",
        "instanceSurface": "profile",
        "instanceIdEnvironment": "VELVETOS_INSTANCE_ID",
        "requireExplicitInstanceIdWhenRunningFromCore": True,
        "projectionOnly": True,
        "legacyShape": "businessRules",
        "sourceOfTruth": "selected instance profile + generic safety semantics",
    }:
        errors.append("AUTONOMY businessRulesResolution contract drift")

    try:
        rules = effective_business_rules(ROOT, instance_id="velvet-factory", env={})
    except LivingStudioRuleResolutionError as exc:
        errors.append(f"cannot resolve canonical VF business rules: {exc}")
        rules = {}

    profile_path = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"canonical VF profile invalid: {exc}")
        profile = {}
    fulfillment = profile.get("fulfillment") or {}
    compliance = profile.get("compliance") or {}
    whatsapp = ((profile.get("mcpBind") or {}).get("whatsapp") or {})
    expected_pickup = profile.get("where") if fulfillment.get("mode") == "pickup" else None
    if rules.get("pickupOnly") != expected_pickup:
        errors.append("effective pickup rule must derive from canonical instance profile")
    if rules.get("nationwideShipping") != fulfillment.get("nationalShipping"):
        errors.append("effective shipping rule must derive from canonical instance profile")
    if rules.get("customerWhatsAppSend") != ("tool" if whatsapp.get("send") is True else "human"):
        errors.append("effective customer send rule must derive from canonical instance binding")
    if rules.get("inventSaleILS") != (not bool(compliance.get("noInventedPrices"))):
        errors.append("effective price invention lock must derive from canonical instance compliance")
    if rules.get("inventInsights") != (not bool(compliance.get("noInventedInsights"))):
        errors.append("effective Insights invention lock must derive from canonical instance compliance")
    if rules.get("destructiveAutonomy") is not False:
        errors.append("destructive autonomy must remain a generic false safety invariant")
    if rules.get("publicCTA") != "Instagram message":
        errors.append("effective public CTA projection must preserve legacy Instagram-message semantics")

    try:
        effective_business_rules(ROOT, env={})
    except LivingStudioRuleResolutionError:
        pass
    else:
        errors.append("Living Studio business-rule resolver must require explicit instance from Core")

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
