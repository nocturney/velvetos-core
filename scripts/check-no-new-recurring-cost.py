#!/usr/bin/env python3
"""Verify canonical recurring-cost law, bindings, risk gates, and validator semantics."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vf_cost_preflight import evaluate, load_policy  # noqa: E402


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    law = read("constitution/NO_NEW_RECURRING_COST.md")
    for needle in (
        "Status: CANONICAL COST AUTHORITY",
        "FREE_LOCAL",
        "FREE_SELF_HOSTED",
        "EXISTING_PAID_CAPABILITY",
        "FREE_TIER_LIMITED",
        "PAID_OPTIONAL",
        "PAID_REQUIRED",
        "COST_UNKNOWN",
        "Fail closed",
        "monthly cost-drift review",
        "No silent cost escalation",
    ):
        if needle not in law:
            fail(f"canonical law missing {needle!r}")

    policy = load_policy()
    expected = {
        "FREE_LOCAL",
        "FREE_SELF_HOSTED",
        "EXISTING_PAID_CAPABILITY",
        "FREE_TIER_LIMITED",
        "PAID_OPTIONAL",
        "PAID_REQUIRED",
        "COST_UNKNOWN",
    }
    if policy.get("sourceOfTruth") != "constitution/NO_NEW_RECURRING_COST.md":
        fail("cost-policy sourceOfTruth mismatch")
    if policy.get("failClosed") is not True or set(policy.get("classifications", [])) != expected:
        fail("cost-policy classifications/failClosed mismatch")
    if set(policy.get("blockedWithoutExplicitApproval", [])) != {"PAID_REQUIRED", "COST_UNKNOWN"}:
        fail("blocked classification set mismatch")

    bindings = {
        "AGENTS.md": ("NO_NEW_RECURRING_COST", "scripts/check-no-new-recurring-cost.py"),
        "constitution/CONSTITUTION.md": ("NO_NEW_RECURRING_COST",),
        "constitution/ORCHESTRA.md": ("Cost failover law", "cost preflight"),
        "office/control/POLICY.md": ("עלות חוזרת חדשה", "COST_UNKNOWN"),
    }
    for path, needles in bindings.items():
        body = read(path)
        for needle in needles:
            if needle not in body:
                fail(f"{path} missing binding {needle!r}")

    risk = json.loads(read("packages/vfops/risk-policy.json"))
    red = set(risk["levels"]["RED"]["onlyWhen"])
    for item in ("new-recurring-cost", "paid-api-call", "billing-capable-resource"):
        if item not in red:
            fail(f"risk-policy missing RED condition {item}")

    layers = json.loads(read("packages/vfharness/layers.json"))
    if not any(row.get("script") == "scripts/check-no-new-recurring-cost.py" and row.get("type") == "computational" for row in layers.get("sensors", [])):
        fail("cost sensor not registered in harness layers")

    base = {
        "component": "fixture",
        "action": "fixture-check",
        "evidence": "fixture evidence for deterministic validator semantics",
        "checked_at": "2026-09-26",
        "incremental_cost_possible": False,
        "automatic_paid_overage_possible": False,
        "hard_cap_enforced": False,
        "paid_features_enabled": False,
        "approval": None,
    }
    approval = {
        "approved": True,
        "approved_by": "owner",
        "provider": "fixture-provider",
        "product_or_plan": "fixture-plan",
        "billing_model": "fixture billing model",
        "expected_recurring_cost": "owner-approved bounded exposure",
        "cost_period_or_usage_basis": "fixture period",
        "scope": "fixture validator test only",
        "hard_cap_or_limit": "fixture hard limit",
        "note": "explicit fixture approval for semantic test",
    }

    def status(classification: str, **updates: object) -> str:
        row = dict(base, classification=classification)
        row.update(updates)
        return evaluate(row, policy)["status"]

    if status("FREE_LOCAL") != "PASS" or status("FREE_SELF_HOSTED") != "PASS":
        fail("free local/self-hosted routes must pass")
    if status("PAID_REQUIRED") != policy["blockedStatus"] or status("COST_UNKNOWN") != policy["blockedStatus"]:
        fail("paid/unknown routes must fail closed without approval")
    if status("PAID_REQUIRED", approval=approval) != "PASS" or status("COST_UNKNOWN", approval=approval) != "PASS":
        fail("explicit complete approval must unlock paid/unknown fixture")
    if status("EXISTING_PAID_CAPABILITY", incremental_cost_possible=None) != policy["blockedStatus"]:
        fail("existing paid capability must prove no incremental cost")
    if status("FREE_TIER_LIMITED", automatic_paid_overage_possible=True, hard_cap_enforced=False) != policy["blockedStatus"]:
        fail("uncapped paid overage must block")
    if status("FREE_TIER_LIMITED", automatic_paid_overage_possible=True, hard_cap_enforced=True) != "PASS":
        fail("hard-capped free tier fixture should pass")
    if status("PAID_OPTIONAL", paid_features_enabled=True) != policy["blockedStatus"]:
        fail("paid optional features must remain disabled")

    print("OK NO_NEW_RECURRING_COST canonical + fail-closed cost preflight")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
