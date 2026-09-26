#!/usr/bin/env python3
"""Fail-closed recurring-cost preflight. Local JSON validation only; no network or billing actions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "packages" / "vfharness" / "cost-policy.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return data


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    return load_json(path)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _approval_valid(approval: Any, policy: dict[str, Any]) -> bool:
    if not isinstance(approval, dict) or approval.get("approved") is not True:
        return False
    for key in policy["approval"]["requiredFields"]:
        value = approval.get(key)
        if key == "approved":
            continue
        if not _text(value):
            return False
    return True


def evaluate(preflight: dict[str, Any], policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or load_policy()
    required = policy["preflight"]["requiredFields"]
    missing = [key for key in required if key not in preflight]
    if missing:
        return {"status": policy["blockedStatus"], "reason": "MISSING_REQUIRED_FIELDS", "fields": missing}

    classification = preflight.get("classification")
    if classification not in policy["classifications"]:
        return {"status": policy["blockedStatus"], "reason": "INVALID_CLASSIFICATION"}
    if not _text(preflight.get("component")) or not _text(preflight.get("action")):
        return {"status": policy["blockedStatus"], "reason": "COMPONENT_OR_ACTION_MISSING"}
    if not _text(preflight.get("evidence")) or not _text(preflight.get("checked_at")):
        return {"status": policy["blockedStatus"], "reason": "EVIDENCE_OR_DATE_MISSING"}

    approval_ok = _approval_valid(preflight.get("approval"), policy)

    if classification in policy["blockedWithoutExplicitApproval"]:
        if not approval_ok:
            return {"status": policy["blockedStatus"], "reason": "EXPLICIT_OWNER_APPROVAL_REQUIRED", "classification": classification}
        return {"status": "PASS", "classification": classification, "approval_required": True}

    if classification == "EXISTING_PAID_CAPABILITY":
        if preflight.get("incremental_cost_possible") is False:
            return {"status": "PASS", "classification": classification, "approval_required": False}
        if approval_ok:
            return {"status": "PASS", "classification": classification, "approval_required": True}
        return {"status": policy["blockedStatus"], "reason": "INCREMENTAL_COST_NOT_PROVEN_FALSE", "classification": classification}

    if classification == "FREE_TIER_LIMITED":
        overage = preflight.get("automatic_paid_overage_possible")
        cap = preflight.get("hard_cap_enforced")
        if overage is False or cap is True:
            return {"status": "PASS", "classification": classification, "approval_required": False}
        if approval_ok:
            return {"status": "PASS", "classification": classification, "approval_required": True}
        return {"status": policy["blockedStatus"], "reason": "FREE_TIER_OVERAGE_NOT_HARD_CAPPED", "classification": classification}

    if classification == "PAID_OPTIONAL":
        if preflight.get("paid_features_enabled") is not False:
            return {"status": policy["blockedStatus"], "reason": "PAID_OPTIONAL_FEATURES_MUST_STAY_DISABLED", "classification": classification}
        return {"status": "PASS", "classification": classification, "approval_required": False}

    if classification in {"FREE_LOCAL", "FREE_SELF_HOSTED"}:
        if preflight.get("incremental_cost_possible") is True:
            if approval_ok:
                return {"status": "PASS", "classification": classification, "approval_required": True}
            return {"status": policy["blockedStatus"], "reason": "FREE_CLASSIFICATION_CONFLICTS_WITH_INCREMENTAL_COST", "classification": classification}
        return {"status": "PASS", "classification": classification, "approval_required": False}

    return {"status": policy["blockedStatus"], "reason": "UNHANDLED_CLASSIFICATION", "classification": classification}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preflight", type=Path, help="task-specific cost-preflight JSON")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args(argv)
    try:
        policy = load_policy(args.policy)
        preflight = load_json(args.preflight)
        result = evaluate(preflight, policy)
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED_BY_NO_NEW_RECURRING_COST", "reason": f"INVALID_PREFLIGHT: {exc}"}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
