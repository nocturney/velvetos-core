#!/usr/bin/env python3
"""Fail-closed NO_NEW_RECURRING_COST preflight validator.

Supports the detailed schema=1 evidence used by the zero-cost program and the
compact action-oriented evidence used by Fabrication Router. Local JSON only;
no network, billing, provider, or mutation calls are performed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "packages" / "vfharness" / "cost-policy.json"
PLACEHOLDERS = {"", "UNKNOWN", "REPLACE_ME", "PENDING", "TODO", None}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return data


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    return load_json(path)
def meaningful(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().upper() not in PLACEHOLDERS
    if value is None:
        return False
    if isinstance(value, list):
        return len(value) > 0
    return True


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _compact_approval_valid(approval: Any, policy: dict[str, Any]) -> bool:
    if not isinstance(approval, dict) or approval.get("approved") is not True:
        return False
    for key in policy.get("approval", {}).get("requiredFields", []):
        if key == "approved":
            continue
        if not _text(approval.get(key)):
            return False
    return True


def _detailed_approval_valid(approval: Any, policy: dict[str, Any]) -> bool:
    if not isinstance(approval, dict):
        return False
    return all(meaningful(approval.get(key)) for key in policy["approvalRequiredFields"])
def evaluate(preflight: dict[str, Any], policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate compact evidence without raising; useful to callers and sensors."""
    policy = policy or load_policy()
    required = policy.get("preflight", {}).get("requiredFields", [])
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

    approval_ok = _compact_approval_valid(preflight.get("approval"), policy)
    blocked = policy["blockedStatus"]

    if classification in policy["blockedWithoutExplicitApproval"]:
        if not approval_ok:
            return {"status": blocked, "reason": "EXPLICIT_OWNER_APPROVAL_REQUIRED", "classification": classification}
        return {"status": "PASS", "classification": classification, "approval_required": True, "explicit_approval_required": True}

    if classification == "EXISTING_PAID_CAPABILITY":
        if preflight.get("incremental_cost_possible") is False:
            return {"status": "PASS", "classification": classification, "approval_required": False, "explicit_approval_required": False}
        if approval_ok:
            return {"status": "PASS", "classification": classification, "approval_required": True, "explicit_approval_required": True}
        return {"status": blocked, "reason": "INCREMENTAL_COST_NOT_PROVEN_FALSE", "classification": classification}
    if classification == "FREE_TIER_LIMITED":
        overage = preflight.get("automatic_paid_overage_possible")
        cap = preflight.get("hard_cap_enforced")
        if overage is False or cap is True:
            return {"status": "PASS", "classification": classification, "approval_required": False, "explicit_approval_required": False}
        if approval_ok:
            return {"status": "PASS", "classification": classification, "approval_required": True, "explicit_approval_required": True}
        return {"status": blocked, "reason": "FREE_TIER_OVERAGE_NOT_HARD_CAPPED", "classification": classification}

    if classification == "PAID_OPTIONAL":
        if preflight.get("paid_features_enabled") is not False:
            return {"status": blocked, "reason": "PAID_OPTIONAL_FEATURES_MUST_STAY_DISABLED", "classification": classification}
        return {"status": "PASS", "classification": classification, "approval_required": False, "explicit_approval_required": False}

    if classification in {"FREE_LOCAL", "FREE_SELF_HOSTED"}:
        if preflight.get("incremental_cost_possible") is True:
            if approval_ok:
                return {"status": "PASS", "classification": classification, "approval_required": True, "explicit_approval_required": True}
            return {"status": blocked, "reason": "FREE_CLASSIFICATION_CONFLICTS_WITH_INCREMENTAL_COST", "classification": classification}
        return {"status": "PASS", "classification": classification, "approval_required": False, "explicit_approval_required": False}

    return {"status": blocked, "reason": "UNHANDLED_CLASSIFICATION", "classification": classification}


def validate_detailed(doc: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if doc.get("schema") != 1:
        raise ValueError("schema must be 1")
    classification = doc.get("classification")
    if classification not in policy["classifications"]:
        raise ValueError("unsupported cost classification")
    for field in policy["preflightRequiredFields"]:
        if field == "api_dependencies":
            if not isinstance(doc.get(field), list):
                raise ValueError("api_dependencies must be a list (empty is allowed)")
            continue
        if field == "evidence":
            if not isinstance(doc.get(field), list) or not doc[field]:
                raise ValueError("evidence must contain at least one pricing/license source or local proof")
            continue
        if not meaningful(doc.get(field)):
            raise ValueError(f"missing/unverified preflight field: {field}")

    needs_approval = classification in policy["blockedWithoutExplicitApproval"]
    if classification == "EXISTING_PAID_CAPABILITY":
        needs_approval = doc.get("incremental_cost_possible") is not False
    elif classification in {"FREE_LOCAL", "FREE_SELF_HOSTED"}:
        needs_approval = doc.get("incremental_cost_possible") is True
    elif classification == "FREE_TIER_LIMITED":
        overage = doc.get("automatic_paid_overage_possible")
        capped = doc.get("hard_cap_enforced") is True
        needs_approval = overage is not False and not capped
    elif classification == "PAID_OPTIONAL":
        if doc.get("paid_features_enabled") is not False:
            raise ValueError("PAID_OPTIONAL must explicitly set paid_features_enabled=false")

    approval = doc.get("approval")
    if needs_approval and not _detailed_approval_valid(approval, policy):
        raise ValueError("BLOCKED_BY_NO_NEW_RECURRING_COST: explicit owner approval required")
    if not needs_approval and approval is not None and not isinstance(approval, dict):
        raise ValueError("approval must be null or an object")

    return {
        "status": "PASS",
        "component": doc["component"],
        "classification": classification,
        "approval_required": needs_approval,
        "explicit_approval_required": needs_approval,
        "policy": policy["sourceOfTruth"],
    }
def validate_document(doc: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if doc.get("schema") == 1:
        return validate_detailed(doc, policy)
    result = evaluate(doc, policy)
    if result.get("status") != "PASS":
        reason = result.get("reason", "BLOCKED")
        raise ValueError(f"{policy['blockedStatus']}: {reason}")
    result.setdefault("component", doc.get("component"))
    result.setdefault("policy", policy["sourceOfTruth"])
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("arguments", nargs="+", help="PRECHECK.json or validate PRECHECK.json")
    args = parser.parse_args(argv)

    if len(args.arguments) == 1:
        preflight_path = Path(args.arguments[0])
    elif len(args.arguments) == 2 and args.arguments[0] == "validate":
        preflight_path = Path(args.arguments[1])
    else:
        parser.error("use: vf_cost_preflight.py [--policy POLICY] PRECHECK.json OR vf_cost_preflight.py validate PRECHECK.json")

    try:
        policy = load_policy(args.policy)
        doc = load_json(preflight_path)
        result = validate_document(doc, policy)
    except Exception as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
