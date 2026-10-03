#!/usr/bin/env python3
"""Bounded cost-envelope evaluator for policy_id cost.recurring.new.

This module performs no provider, billing or mutation calls. It validates one
owner-approved envelope and one exact usage request. The canonical decision
entrypoint remains scripts/vf_cost_preflight.py; this file is a helper plus
self-test surface.

A valid envelope removes repeated owner approval/full preflight for matching
calls only. It never removes:
- exact provider/plan/billing/usage/scope binding;
- aggregate hard-cap enforcement;
- fresh usage-meter evidence;
- expiry;
- exact-action receipt after ALLOW;
- fail-closed revalidation on plan/usage/cap/overage drift.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "packages" / "velvetos" / "policy" / "cost-envelope-test-vectors.json"
HEX64 = re.compile(r"^[a-f0-9]{64}$")
ALLOWED_CLASSIFICATIONS = {"EXISTING_PAID_CAPABILITY", "FREE_TIER_LIMITED", "PAID_REQUIRED"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _safe_repo_path(value: Any) -> Path | None:
    if not _text(value):
        return None
    raw = str(value).replace("\\", "/")
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        return None
    resolved = (ROOT / path).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return resolved


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_time(value: Any) -> datetime | None:
    """Public timestamp parser for the canonical cost preflight entrypoint."""
    return _parse_time(value)


def _decision_ref(envelope: dict[str, Any], use: dict[str, Any]) -> str:
    payload = {
        "policy_id": "cost.recurring.new",
        "envelope_id": envelope.get("envelope_id"),
        "use": use,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "cost.recurring.new:" + hashlib.sha256(encoded).hexdigest()


def _result(
    decision: str,
    reasons: list[str],
    *,
    envelope: dict[str, Any] | None = None,
    use: dict[str, Any] | None = None,
    basis: str,
    remaining_before: float | None = None,
    remaining_after: float | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": "velvetos.cost-envelope-decision.v1",
        "policy_id": "cost.recurring.new",
        "decision": decision,
        "reason_codes": list(dict.fromkeys(reasons)),
        "authorization_basis": basis,
        "owner_prompt_required": decision == "REQUIRE_OWNER_APPROVAL",
        "full_preflight_required": decision == "REQUIRE_OWNER_APPROVAL",
        "exact_action_receipt_required": decision == "ALLOW",
        "envelope_id": envelope.get("envelope_id") if isinstance(envelope, dict) else None,
    }
    if isinstance(envelope, dict) and isinstance(use, dict):
        out["decision_ref"] = _decision_ref(envelope, use)
    if remaining_before is not None:
        out["remaining_before_ils"] = round(remaining_before, 6)
    if remaining_after is not None:
        out["remaining_after_ils"] = round(remaining_after, 6)
    return out


def validate_envelope(envelope: Any, *, at: datetime) -> tuple[list[str], list[str]]:
    """Return (hard_fail_reasons, revalidation_reasons)."""
    hard: list[str] = []
    revalidate: list[str] = []
    if not isinstance(envelope, dict):
        return ["ENVELOPE_OBJECT_REQUIRED"], []

    if envelope.get("schema") != "velvetos.cost-envelope.v1":
        hard.append("ENVELOPE_SCHEMA_INVALID")
    if envelope.get("policy_id") != "cost.recurring.new":
        hard.append("POLICY_ID_MISMATCH")
    if not _text(envelope.get("envelope_id")):
        hard.append("ENVELOPE_ID_REQUIRED")
    if envelope.get("classification") not in ALLOWED_CLASSIFICATIONS:
        hard.append("ENVELOPE_CLASSIFICATION_INVALID")
    for field, reason in (
        ("provider", "PROVIDER_REQUIRED"),
        ("product_or_plan", "PLAN_REQUIRED"),
        ("billing_model", "BILLING_MODEL_REQUIRED"),
        ("usage_model", "USAGE_MODEL_REQUIRED"),
    ):
        if not _text(envelope.get(field)):
            hard.append(reason)

    scope = envelope.get("scope")
    if not isinstance(scope, dict):
        hard.append("SCOPE_REQUIRED")
    else:
        if not _text(scope.get("component")) or not _text(scope.get("environment")):
            hard.append("SCOPE_IDENTITY_REQUIRED")
        actions = scope.get("actions")
        if not isinstance(actions, list) or not actions or not all(_text(x) for x in actions):
            hard.append("SCOPE_ACTIONS_REQUIRED")
        elif len(actions) != len(set(actions)):
            hard.append("SCOPE_ACTIONS_DUPLICATE")

    cap = envelope.get("cap")
    if not isinstance(cap, dict):
        hard.append("CAP_REQUIRED")
    else:
        if not _number(cap.get("amount")) or float(cap.get("amount", 0)) <= 0:
            hard.append("CAP_AMOUNT_INVALID")
        if cap.get("currency") != "ILS":
            hard.append("CAP_CURRENCY_INVALID")
        if not _text(cap.get("period")):
            hard.append("CAP_PERIOD_REQUIRED")
        if cap.get("hard_cap_enforced") is not True:
            hard.append("HARD_CAP_REQUIRED")

    overage = envelope.get("overage")
    if not isinstance(overage, dict):
        hard.append("OVERAGE_POLICY_REQUIRED")
    else:
        if overage.get("behavior") != "BLOCK_AT_CAP":
            hard.append("OVERAGE_BEHAVIOR_UNBOUNDED")
        if type(overage.get("automatic_paid_overage_allowed")) is not bool:
            hard.append("AUTO_OVERAGE_FLAG_REQUIRED")

    max_age = envelope.get("meter_max_age_seconds")
    if not isinstance(max_age, int) or isinstance(max_age, bool) or not (60 <= max_age <= 86400):
        hard.append("METER_MAX_AGE_INVALID")

    source = envelope.get("source_preflight")
    if not isinstance(source, dict):
        hard.append("SOURCE_PREFLIGHT_REQUIRED")
    else:
        source_path = _safe_repo_path(source.get("path"))
        source_sha = source.get("sha256")
        if source_path is None:
            hard.append("SOURCE_PREFLIGHT_PATH_INVALID")
        elif not source_path.is_file():
            hard.append("SOURCE_PREFLIGHT_MISSING")
        if not isinstance(source_sha, str) or not HEX64.fullmatch(source_sha):
            hard.append("SOURCE_PREFLIGHT_SHA_INVALID")
        elif source_path is not None and source_path.is_file() and _sha256(source_path) != source_sha:
            hard.append("SOURCE_PREFLIGHT_HASH_MISMATCH")

    approval = envelope.get("approval")
    if not isinstance(approval, dict):
        hard.append("OWNER_APPROVAL_REQUIRED")
    else:
        if not _text(approval.get("approved_by")):
            hard.append("APPROVER_REQUIRED")
        if not _text(approval.get("approval_ref")):
            hard.append("APPROVAL_REF_REQUIRED")
        approved_at = _parse_time(approval.get("approved_at"))
        expires_at = _parse_time(approval.get("expires_at"))
        if approved_at is None:
            hard.append("APPROVED_AT_INVALID")
        if expires_at is None:
            hard.append("EXPIRES_AT_INVALID")
        if approved_at is not None and expires_at is not None and expires_at <= approved_at:
            hard.append("APPROVAL_WINDOW_INVALID")
        if approved_at is not None and approved_at > at:
            hard.append("APPROVAL_FROM_FUTURE")
        if expires_at is not None and expires_at <= at:
            revalidate.append("ENVELOPE_EXPIRED")

    return list(dict.fromkeys(hard)), list(dict.fromkeys(revalidate))


def evaluate_use(envelope: Any, use: Any, *, at: datetime | None = None) -> dict[str, Any]:
    at = at or datetime.now(timezone.utc)
    hard, revalidate = validate_envelope(envelope, at=at)
    if hard:
        return _result("DENY", hard, envelope=envelope if isinstance(envelope, dict) else None,
                       use=use if isinstance(use, dict) else None, basis="FAIL_CLOSED")
    assert isinstance(envelope, dict)

    if not isinstance(use, dict):
        return _result("DENY", ["USE_OBJECT_REQUIRED"], envelope=envelope, basis="FAIL_CLOSED")
    if use.get("schema") != "velvetos.cost-envelope-use.v1":
        return _result("DENY", ["USE_SCHEMA_INVALID"], envelope=envelope, use=use, basis="FAIL_CLOSED")

    comparisons = (
        ("provider", "PROVIDER_CHANGED"),
        ("product_or_plan", "PLAN_CHANGED"),
        ("billing_model", "BILLING_MODEL_CHANGED"),
        ("usage_model", "USAGE_MODEL_CHANGED"),
    )
    for field, reason in comparisons:
        if use.get(field) != envelope.get(field):
            revalidate.append(reason)

    scope = envelope["scope"]
    if use.get("component") != scope.get("component"):
        revalidate.append("COMPONENT_SCOPE_CHANGED")
    if use.get("environment") != scope.get("environment"):
        revalidate.append("ENVIRONMENT_SCOPE_CHANGED")
    if use.get("action") not in set(scope.get("actions") or []):
        revalidate.append("ACTION_SCOPE_CHANGED")

    if use.get("cap_snapshot") != envelope.get("cap"):
        revalidate.append("CAP_CHANGED")
    if use.get("overage_snapshot") != envelope.get("overage"):
        revalidate.append("AUTO_OVERAGE_OR_BEHAVIOR_CHANGED")

    if revalidate:
        return _result("REQUIRE_OWNER_APPROVAL", revalidate, envelope=envelope, use=use,
                       basis="ENVELOPE_REVALIDATION_REQUIRED")

    meter = use.get("meter")
    meter_reasons: list[str] = []
    if not isinstance(meter, dict):
        meter_reasons.append("USAGE_METER_REQUIRED")
    else:
        for field in ("spent_before_ils", "projected_incremental_cost_ils"):
            if not _number(meter.get(field)) or float(meter.get(field, -1)) < 0:
                meter_reasons.append(f"{field.upper()}_INVALID")
        if meter.get("currency") != envelope["cap"]["currency"]:
            meter_reasons.append("METER_CURRENCY_MISMATCH")
        if meter.get("period") != envelope["cap"]["period"]:
            meter_reasons.append("METER_PERIOD_MISMATCH")
        if meter.get("hard_cap_enforced") is not True:
            meter_reasons.append("METER_HARD_CAP_NOT_PROVEN")
        if not _text(meter.get("evidence_ref")):
            meter_reasons.append("METER_EVIDENCE_REQUIRED")
        checked_at = _parse_time(meter.get("checked_at"))
        if checked_at is None:
            meter_reasons.append("METER_CHECKED_AT_INVALID")
        else:
            age = (at - checked_at).total_seconds()
            if age < -60:
                meter_reasons.append("METER_FROM_FUTURE")
            elif age > envelope["meter_max_age_seconds"]:
                meter_reasons.append("METER_STALE")

    if meter_reasons:
        return _result("DENY", meter_reasons, envelope=envelope, use=use, basis="FAIL_CLOSED")

    assert isinstance(meter, dict)
    spent = float(meter["spent_before_ils"])
    projected = float(meter["projected_incremental_cost_ils"])
    cap_amount = float(envelope["cap"]["amount"])
    remaining_before = cap_amount - spent
    remaining_after = cap_amount - spent - projected
    if spent > cap_amount:
        return _result("DENY", ["METER_ALREADY_OVER_CAP"], envelope=envelope, use=use,
                       basis="FAIL_CLOSED", remaining_before=remaining_before, remaining_after=remaining_after)
    if remaining_after < -1e-9:
        return _result("DENY", ["COST_CAP_EXCEEDED"], envelope=envelope, use=use,
                       basis="CAP_BLOCK", remaining_before=remaining_before, remaining_after=remaining_after)

    return _result(
        "ALLOW",
        [],
        envelope=envelope,
        use=use,
        basis="BOUNDED_COST_ENVELOPE",
        remaining_before=remaining_before,
        remaining_after=max(0.0, remaining_after),
    )


def _patch(doc: dict[str, Any], ops: list[dict[str, Any]]) -> dict[str, Any]:
    out = copy.deepcopy(doc)
    for op in ops:
        tokens = op["path"].strip("/").split("/")
        parent: Any = out
        for token in tokens[:-1]:
            parent = parent[token]
        leaf = tokens[-1]
        if op["op"] == "replace":
            parent[leaf] = copy.deepcopy(op.get("value"))
        elif op["op"] == "remove":
            parent.pop(leaf, None)
        else:
            raise ValueError(f"unsupported patch op {op['op']}")
    return out


def self_test() -> int:
    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    base_envelope = data["base_envelope"]
    base_use = data["base_use"]
    failed = 0
    allow_count = 0
    revalidate_count = 0
    deny_count = 0
    for vector in data["vectors"]:
        envelope = _patch(base_envelope, vector.get("envelope_patch_ops") or [])
        use = _patch(base_use, vector.get("use_patch_ops") or [])
        at = _parse_time(vector["evaluation_time"])
        if at is None:
            print(f"FAIL {vector['id']}: invalid evaluation_time", file=sys.stderr)
            failed += 1
            continue
        actual = evaluate_use(envelope, use, at=at)
        expected = vector["expected"]
        projection = {
            "decision": actual["decision"],
            "reason_codes": actual["reason_codes"],
            "owner_prompt_required": actual["owner_prompt_required"],
            "full_preflight_required": actual["full_preflight_required"],
            "exact_action_receipt_required": actual["exact_action_receipt_required"],
            "authorization_basis": actual["authorization_basis"],
        }
        if projection != expected:
            print(f"FAIL {vector['id']}: expected {expected}, got {projection}", file=sys.stderr)
            failed += 1
        else:
            print(f"PASS {vector['id']} {actual['decision']} {actual['authorization_basis']}")
        if actual["decision"] == "ALLOW":
            allow_count += 1
        elif actual["decision"] == "REQUIRE_OWNER_APPROVAL":
            revalidate_count += 1
        else:
            deny_count += 1
    if failed:
        return 1
    print(
        f"OK cost-envelope vectors={len(data['vectors'])} allow={allow_count} "
        f"revalidate={revalidate_count} deny={deny_count} "
        "matching_call_owner_prompts=0 full_preflight_per_call=NO"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--envelope", type=Path)
    parser.add_argument("--use", type=Path)
    parser.add_argument("--at")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.envelope or not args.use:
        parser.error("--envelope and --use are required, or use --self-test")
    at = _parse_time(args.at) if args.at else None
    if args.at and at is None:
        parser.error("--at must be an offset-aware ISO-8601 timestamp")
    envelope = json.loads(args.envelope.read_text(encoding="utf-8"))
    use = json.loads(args.use.read_text(encoding="utf-8"))
    result = evaluate_use(envelope, use, at=at)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["decision"] == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
