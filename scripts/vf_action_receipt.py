#!/usr/bin/env python3
"""Validate VelvetOS exact-action authorization receipts.

This is a receipt verifier, not a policy decision engine. The canonical policy
listed in policy-registry.json must make the decision first; this verifier only
checks that the decision is bound to the correct external effect/action and
that any required owner gate is exact, current and blocker-free.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
VECTORS = ROOT / "packages" / "velvetos" / "policy" / "action-receipt-test-vectors.json"
HEX64 = re.compile(r"^[a-f0-9]{64}$")
DECISIONS = {"ALLOW", "DENY", "REQUIRE_OWNER_APPROVAL"}


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


def _exact_binding_present(binding: Any) -> bool:
    if not isinstance(binding, dict):
        return False
    for key in ("artifact_sha256", "payload_sha256", "text_sha256", "target_sha256"):
        value = binding.get(key)
        if isinstance(value, str) and HEX64.fullmatch(value):
            return True
    media = binding.get("media_sha256")
    return isinstance(media, list) and bool(media) and all(isinstance(x, str) and HEX64.fullmatch(x) for x in media)


def _effect_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    contract = registry.get("external_effect_contract") or {}
    return {
        row.get("policy_id"): row
        for row in contract.get("effects") or []
        if isinstance(row, dict) and isinstance(row.get("policy_id"), str)
    }


def validate_receipt(receipt: Any, *, at: datetime | None = None, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry or json.loads(REGISTRY.read_text(encoding="utf-8"))
    at = at or datetime.now(timezone.utc)
    reasons: list[str] = []

    if not isinstance(receipt, dict):
        return {"gate": "BLOCKED", "action_authorized": False, "reason_codes": ["RECEIPT_OBJECT_REQUIRED"]}

    if receipt.get("schema_version") != "velvetos.action-receipt.v1":
        reasons.append("SCHEMA_VERSION_INVALID")

    policy_id = receipt.get("policy_id")
    effects = _effect_map(registry)
    effect = effects.get(policy_id)
    if effect is None:
        reasons.append("POLICY_ID_UNREGISTERED")
    elif receipt.get("effect_class") != effect.get("effect_class"):
        reasons.append("EFFECT_CLASS_MISMATCH")

    contract = registry.get("external_effect_contract") or {}
    vocabulary = set(contract.get("normalized_decision_vocabulary") or [])
    if vocabulary != DECISIONS:
        reasons.append("REGISTRY_DECISION_VOCABULARY_INVALID")

    decision = receipt.get("policy_decision")
    if not isinstance(decision, dict):
        reasons.append("POLICY_DECISION_MISSING")
        outcome = None
    else:
        outcome = decision.get("outcome")
        if outcome not in DECISIONS:
            reasons.append("POLICY_DECISION_INVALID")
        if not isinstance(decision.get("decision_ref"), str) or not decision.get("decision_ref"):
            reasons.append("POLICY_DECISION_REF_MISSING")
        if _parse_time(decision.get("decided_at")) is None:
            reasons.append("POLICY_DECIDED_AT_INVALID")

    action = receipt.get("action")
    if not isinstance(action, dict):
        reasons.append("ACTION_MISSING")
        commitment = False
    else:
        if not isinstance(action.get("action_type"), str) or not action.get("action_type"):
            reasons.append("ACTION_TYPE_MISSING")
        if not isinstance(action.get("scope"), str) or not action.get("scope"):
            reasons.append("ACTION_SCOPE_MISSING")
        if type(action.get("commitment")) is not bool:
            reasons.append("ACTION_COMMITMENT_INVALID")
        commitment = action.get("commitment") is True

    mode = effect.get("receipt_mode") if effect else None
    if mode == "POLICY_NATIVE_RECEIPT":
        reasons.append("POLICY_NATIVE_RECEIPT_REQUIRED")
    elif mode == "EXACT_ACTION_REQUIRED" and not _exact_binding_present(receipt.get("exact_binding")):
        reasons.append("EXACT_BINDING_REQUIRED")
    elif mode == "EXACT_ACTION_ON_COMMITMENT" and commitment and not _exact_binding_present(receipt.get("exact_binding")):
        reasons.append("EXACT_BINDING_REQUIRED")
    elif mode == "OWNER_RESERVED" and not _exact_binding_present(receipt.get("exact_binding")):
        reasons.append("EXACT_BINDING_REQUIRED")

    allowed_evidence = {
        row.get("id")
        for row in contract.get("evidence_input_classes") or []
        if isinstance(row, dict) and row.get("can_authorize_external_effect") is False
    }
    effect_evidence = set(effect.get("evidence_inputs") or []) if effect else set()
    evidence = receipt.get("evidence")
    if not isinstance(evidence, list):
        reasons.append("EVIDENCE_ARRAY_REQUIRED")
    else:
        for item in evidence:
            if not isinstance(item, dict):
                reasons.append("EVIDENCE_ITEM_INVALID")
                continue
            cls = item.get("class")
            if cls not in allowed_evidence or (effect and cls not in effect_evidence):
                reasons.append(f"EVIDENCE_CLASS_NOT_ALLOWED:{cls}")
            if not isinstance(item.get("ref"), str) or not item.get("ref"):
                reasons.append("EVIDENCE_REF_MISSING")
            if item.get("status") != "PASS":
                reasons.append(f"EVIDENCE_NOT_PASS:{cls}")

    gate = receipt.get("owner_gate")
    owner_required = mode == "OWNER_RESERVED" or (isinstance(gate, dict) and gate.get("required") is True)
    if not isinstance(gate, dict):
        reasons.append("OWNER_GATE_MISSING")
    else:
        blockers = gate.get("blocker_ids")
        if not isinstance(blockers, list):
            reasons.append("OWNER_BLOCKERS_INVALID")
        elif blockers:
            reasons.append("OWNER_BLOCKER_OPEN")
        if owner_required:
            if gate.get("decision") != "APPROVED":
                reasons.append("OWNER_APPROVAL_REQUIRED")
            if not isinstance(gate.get("reviewer"), str) or not gate.get("reviewer"):
                reasons.append("NAMED_REVIEWER_REQUIRED")
            if _parse_time(gate.get("reviewed_at")) is None:
                reasons.append("OWNER_REVIEWED_AT_INVALID")
            expires = _parse_time(gate.get("expires_at"))
            if expires is None:
                reasons.append("OWNER_APPROVAL_EXPIRY_REQUIRED")
            elif expires <= at:
                reasons.append("OWNER_APPROVAL_EXPIRED")
        elif gate.get("decision") not in {"NOT_REQUIRED", "APPROVED"}:
            reasons.append("OWNER_GATE_DECISION_INVALID")

    if outcome == "DENY":
        reasons.append("POLICY_DENY")
    elif outcome == "REQUIRE_OWNER_APPROVAL":
        reasons.append("OWNER_APPROVAL_REQUIRED")
    elif outcome != "ALLOW" and outcome is not None:
        reasons.append("POLICY_DECISION_INVALID")

    reasons = list(dict.fromkeys(reasons))
    return {
        "gate": "PASS" if not reasons else "BLOCKED",
        "action_authorized": not reasons and outcome == "ALLOW",
        "policy_id": policy_id,
        "effect_class": receipt.get("effect_class"),
        "reason_codes": reasons,
    }


def _patch(doc: dict[str, Any], ops: list[dict[str, Any]]) -> dict[str, Any]:
    out = copy.deepcopy(doc)
    for op in ops:
        path = op["path"].strip("/").split("/") if op.get("path") else []
        if not path:
            raise ValueError("root patch unsupported")
        parent: Any = out
        for token in path[:-1]:
            parent = parent[token]
        leaf = path[-1]
        if op["op"] == "remove":
            parent.pop(leaf, None)
        elif op["op"] == "replace":
            parent[leaf] = copy.deepcopy(op.get("value"))
        else:
            raise ValueError(f"unsupported patch op {op['op']}")
    return out


def self_test() -> int:
    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    base = data["base_receipt"]
    failed = 0
    for vector in data["vectors"]:
        receipt = _patch(base, vector.get("patch_ops") or [])
        at = _parse_time(vector["evaluation_time"])
        if at is None:
            print(f"FAIL {vector['id']}: invalid evaluation_time", file=sys.stderr)
            failed += 1
            continue
        actual = validate_receipt(receipt, at=at)
        expected = vector["expected"]
        if actual["gate"] != expected["gate"] or actual["reason_codes"] != expected["reason_codes"]:
            print(
                f"FAIL {vector['id']}: expected {expected}, got "
                f"{{'gate': {actual['gate']!r}, 'reason_codes': {actual['reason_codes']!r}}}",
                file=sys.stderr,
            )
            failed += 1
    if failed:
        return 1
    print(f"OK action-receipt vectors={len(data['vectors'])} policy_decision_is_canonical=true")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--at", help="ISO-8601 evaluation time; defaults to now")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.receipt:
        parser.error("--receipt or --self-test is required")
    at = _parse_time(args.at) if args.at else None
    if args.at and at is None:
        parser.error("--at must be an offset-aware ISO-8601 timestamp")
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    result = validate_receipt(receipt, at=at)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["gate"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
