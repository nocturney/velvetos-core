#!/usr/bin/env python3
"""Evaluate policy_id gmail.send without sending mail.

The evaluator separates routine communication from commitment-bearing sends.
It never performs a Gmail mutation. Transport/facts/text checks are evidence;
only this policy decision authorizes the Gmail external effect.

Stage 4E invariants:
- owner_brief / known_thread_reply / routine_forward can ALLOW with facts + exact
  reader-appropriate text readiness and no restricted trigger;
- new_outbound, commercial commitment, price/spend, or rights/privacy ambiguity
  require exact owner approval before they may ALLOW;
- blast, unverified facts, unverified target, bad body identity, or unavailable
  transport DENY;
- approved_static_copy may reuse prior copy only when exact text identity and
  fact freshness remain proven.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "packages" / "velvetos" / "policy" / "gmail.send.json"
VECTORS = ROOT / "packages" / "velvetos" / "policy" / "gmail-send-test-vectors.json"
HEX64 = re.compile(r"^[a-f0-9]{64}$")


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


def _decision_ref(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "gmail.send:" + hashlib.sha256(encoded).hexdigest()


def _owner_approval_valid(
    approval: Any,
    *,
    body_sha256: str | None,
    at: datetime,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not isinstance(approval, dict):
        return False, ["OWNER_APPROVAL_REQUIRED"]
    if approval.get("decision") != "APPROVED":
        reasons.append("OWNER_APPROVAL_REQUIRED")
    if not isinstance(approval.get("reviewer"), str) or not approval.get("reviewer"):
        reasons.append("NAMED_REVIEWER_REQUIRED")
    if approval.get("body_sha256") != body_sha256:
        reasons.append("OWNER_APPROVAL_BODY_MISMATCH")
    reviewed = _parse_time(approval.get("reviewed_at"))
    expires = _parse_time(approval.get("expires_at"))
    if reviewed is None:
        reasons.append("OWNER_REVIEWED_AT_INVALID")
    if expires is None:
        reasons.append("OWNER_APPROVAL_EXPIRY_REQUIRED")
    elif expires <= at:
        reasons.append("OWNER_APPROVAL_EXPIRED")
    blockers = approval.get("blocker_ids")
    if not isinstance(blockers, list):
        reasons.append("OWNER_BLOCKERS_INVALID")
    elif blockers:
        reasons.append("OWNER_BLOCKER_OPEN")
    return not reasons, reasons


def evaluate(
    payload: Any,
    *,
    at: datetime | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = policy or json.loads(POLICY.read_text(encoding="utf-8"))
    at = at or datetime.now(timezone.utc)
    reasons: list[str] = []
    owner_reasons: list[str] = []

    if not isinstance(payload, dict):
        return {
            "schema": "velvetos.gmail-send-decision.v1",
            "policy_id": "gmail.send",
            "decision": "DENY",
            "reason_codes": ["REQUEST_OBJECT_REQUIRED"],
            "owner_approval_required": False,
            "requires_exact_action_receipt": False,
        }

    action_type = payload.get("action_type")
    send_scope = payload.get("send_scope")
    body_sha256 = payload.get("body_sha256")
    target_verified = payload.get("target_verified")
    transport_ready = payload.get("transport_ready")
    facts_verified = payload.get("facts_verified")
    blast = payload.get("blast") is True
    new_commitment = payload.get("new_commercial_commitment") is True
    price_or_spend = payload.get("price_or_spend") is True
    rights_status = payload.get("rights_privacy_status")
    text = payload.get("text_readiness")

    if action_type not in set(policy.get("allowed_actions") or []):
        reasons.append("ACTION_TYPE_NOT_ALLOWED")
    known_scopes = set(policy.get("routine_scopes") or []) | set(policy.get("owner_gated_scopes") or [])
    if send_scope not in known_scopes:
        reasons.append("SEND_SCOPE_UNKNOWN")
    if not isinstance(body_sha256, str) or not HEX64.fullmatch(body_sha256):
        reasons.append("BODY_SHA256_INVALID")
    if target_verified is not True:
        reasons.append("TARGET_NOT_VERIFIED")
    if transport_ready is not True:
        reasons.append("TRANSPORT_NOT_READY")
    if facts_verified is not True:
        reasons.append("UNVERIFIED_FACT")
    if blast:
        reasons.append("BLAST_FORBIDDEN")

    if not isinstance(text, dict):
        reasons.append("TEXT_READINESS_REQUIRED")
    else:
        mode = text.get("mode")
        modes = policy.get("text_readiness_modes") or {}
        if mode not in modes:
            reasons.append("TEXT_READINESS_MODE_INVALID")
        if text.get("status") != "PASS":
            reasons.append("TEXT_READINESS_NOT_PASS")
        if text.get("body_sha256") != body_sha256:
            reasons.append("TEXT_BODY_MISMATCH")
        if not isinstance(text.get("evidence_ref"), str) or not text.get("evidence_ref"):
            reasons.append("TEXT_EVIDENCE_REF_REQUIRED")
        if mode == "approved_static_copy":
            if text.get("text_unchanged") is not True:
                reasons.append("STATIC_COPY_CHANGED")
            if text.get("facts_current") is not True:
                reasons.append("STATIC_COPY_FACTS_STALE")

    hard_deny = {
        "ACTION_TYPE_NOT_ALLOWED",
        "SEND_SCOPE_UNKNOWN",
        "BODY_SHA256_INVALID",
        "TARGET_NOT_VERIFIED",
        "TRANSPORT_NOT_READY",
        "UNVERIFIED_FACT",
        "BLAST_FORBIDDEN",
        "TEXT_READINESS_REQUIRED",
        "TEXT_READINESS_MODE_INVALID",
        "TEXT_READINESS_NOT_PASS",
        "TEXT_BODY_MISMATCH",
        "TEXT_EVIDENCE_REF_REQUIRED",
        "STATIC_COPY_CHANGED",
        "STATIC_COPY_FACTS_STALE",
    }
    if any(reason in hard_deny for reason in reasons):
        decision = "DENY"
        owner_required = False
        exact_receipt = False
        basis = "FAIL_CLOSED"
    else:
        restricted: list[str] = []
        if send_scope in set(policy.get("owner_gated_scopes") or []):
            restricted.append("NEW_OUTBOUND_REQUIRES_OWNER_APPROVAL")
        if new_commitment:
            restricted.append("NEW_COMMERCIAL_COMMITMENT")
        if price_or_spend:
            restricted.append("PRICE_OR_SPEND")
        if rights_status != "PASS":
            restricted.append("RIGHTS_PRIVACY_AMBIGUITY")

        if restricted:
            approval_ok, owner_reasons = _owner_approval_valid(
                payload.get("owner_approval"),
                body_sha256=body_sha256 if isinstance(body_sha256, str) else None,
                at=at,
            )
            if approval_ok:
                decision = "ALLOW"
                owner_required = True
                exact_receipt = True
                basis = "EXACT_OWNER_APPROVAL"
                reasons.extend(restricted)
            else:
                decision = "REQUIRE_OWNER_APPROVAL"
                owner_required = True
                exact_receipt = True
                basis = "OWNER_GATE"
                reasons.extend(restricted)
                reasons.extend(owner_reasons)
        else:
            decision = "ALLOW"
            owner_required = False
            exact_receipt = False
            basis = "ROUTINE_STANDING_AUTHORIZATION"
            if rights_status != "PASS":
                reasons.append("RIGHTS_PRIVACY_AMBIGUITY")

    reasons = list(dict.fromkeys(reasons))
    return {
        "schema": "velvetos.gmail-send-decision.v1",
        "policy_id": "gmail.send",
        "policy_version": policy.get("version"),
        "decision_ref": _decision_ref(payload),
        "decision": decision,
        "reason_codes": reasons,
        "authorization_basis": basis,
        "owner_approval_required": owner_required,
        "requires_exact_action_receipt": exact_receipt,
        "receipt_mode": policy.get("commitment_receipt_mode"),
        "action_type": action_type,
        "send_scope": send_scope,
        "body_sha256": body_sha256,
        "text_readiness_mode": text.get("mode") if isinstance(text, dict) else None,
    }


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
    base = data["base_request"]
    failed = 0
    for vector in data["vectors"]:
        request = _patch(base, vector.get("patch_ops") or [])
        at = _parse_time(vector["evaluation_time"])
        if at is None:
            print(f"FAIL {vector['id']}: invalid evaluation_time", file=sys.stderr)
            failed += 1
            continue
        actual = evaluate(request, at=at)
        expected = vector["expected"]
        actual_projection = {
            "decision": actual["decision"],
            "reason_codes": actual["reason_codes"],
            "owner_approval_required": actual["owner_approval_required"],
            "requires_exact_action_receipt": actual["requires_exact_action_receipt"],
            "authorization_basis": actual["authorization_basis"],
        }
        if actual_projection != expected:
            print(f"FAIL {vector['id']}: expected {expected}, got {actual_projection}", file=sys.stderr)
            failed += 1
        else:
            print(f"PASS {vector['id']} {actual['decision']} {actual['authorization_basis']}")
    if failed:
        return 1
    print(f"OK gmail.send vectors={len(data['vectors'])} routine_owner_prompt=0 commitment_exact_binding=YES")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, help="JSON request envelope; evaluator never sends")
    parser.add_argument("--at", help="offset-aware ISO-8601 evaluation time")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.request:
        parser.error("--request or --self-test is required")
    at = _parse_time(args.at) if args.at else None
    if args.at and at is None:
        parser.error("--at must be an offset-aware ISO-8601 timestamp")
    payload = json.loads(args.request.read_text(encoding="utf-8"))
    result = evaluate(payload, at=at)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["decision"] == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
