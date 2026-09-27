#!/usr/bin/env python3
"""Validate NO_NEW_RECURRING_COST preflight evidence. Local-only; no network/calls."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "packages" / "vfharness" / "cost-policy.json"
PLACEHOLDERS = {"", "UNKNOWN", "REPLACE_ME", "PENDING", "TODO", None}


def fail(msg: str) -> None:
    raise ValueError(msg)


def meaningful(value) -> bool:
    if value in PLACEHOLDERS:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().upper() not in PLACEHOLDERS
    if isinstance(value, list):
        return len(value) > 0
    return True


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(path: Path) -> dict:
    policy = load(POLICY)
    doc = load(path)
    if doc.get("schema") != 1:
        fail("schema must be 1")
    classification = doc.get("classification")
    if classification not in policy["classifications"]:
        fail("unsupported cost classification")

    for field in policy["preflightRequiredFields"]:
        if field == "api_dependencies":
            if not isinstance(doc.get(field), list):
                fail("api_dependencies must be a list (empty is allowed)")
            continue
        if field == "evidence":
            if not isinstance(doc.get(field), list) or not doc[field]:
                fail("evidence must contain at least one pricing/license source or local proof")
            continue
        if not meaningful(doc.get(field)):
            fail(f"missing/unverified preflight field: {field}")

    approval = doc.get("approval")
    needs_approval = classification in policy["blockedWithoutExplicitApproval"]
    if classification == "EXISTING_PAID_CAPABILITY":
        if doc.get("incremental_cost_possible") is not False:
            needs_approval = True
    if classification == "FREE_TIER_LIMITED":
        if doc.get("automatic_paid_overage_possible") is not False and not meaningful(doc.get("hard_cap")):
            needs_approval = True
    if classification == "PAID_OPTIONAL":
        if doc.get("paid_features_enabled") is not False:
            fail("PAID_OPTIONAL must explicitly set paid_features_enabled=false")

    if needs_approval:
        if not isinstance(approval, dict):
            fail("BLOCKED_BY_NO_NEW_RECURRING_COST: explicit owner approval required")
        for field in policy["approvalRequiredFields"]:
            if not meaningful(approval.get(field)):
                fail(f"BLOCKED_BY_NO_NEW_RECURRING_COST: approval missing {field}")
    elif approval is not None and not isinstance(approval, dict):
        fail("approval must be null or an object")

    return {
        "status": "PASS",
        "component": doc["component"],
        "classification": classification,
        "explicit_approval_required": needs_approval,
        "policy": policy["sourceOfTruth"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("preflight")
    args = ap.parse_args()
    try:
        path = Path(args.preflight).resolve()
        result = validate(path)
    except Exception as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
