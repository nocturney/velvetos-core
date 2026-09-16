"""Verify velvet.delivery_approval.v1 receipts (shared by preflight + mutation)."""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature

from .canonical import canonical_payload_bytes
from .capabilities import mutation_tool_ids
from .keys_registry import KeyRegistry
from .schema import (
    ACCOUNT_LABEL,
    ALGORITHM,
    CLOCK_SKEW_SECONDS,
    CLAIM_FIELDS,
    DEFAULT_IG_USER_ID,
    ISSUER_NAME,
    SCHEMA_ID,
    SHA256_RE,
    TENANT,
)


def _parse_rfc3339(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return dt.astimezone(timezone.utc)


def _b64decode_sig(value: str) -> bytes:
    text = value.strip()
    pad = "=" * (-len(text) % 4)
    try:
        return base64.urlsafe_b64decode(text + pad)
    except Exception:
        return base64.b64decode(text + pad)


@dataclass
class VerifyResult:
    ok: bool
    problems: list[str] = field(default_factory=list)
    claims: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "problems": list(self.problems), "claims": dict(self.claims)}


def parse_receipt_envelope(receipt: str | Mapping[str, Any]) -> tuple[dict[str, str], str]:
    """Split envelope into claims dict + signature string."""
    if isinstance(receipt, str):
        receipt = json.loads(receipt)
    if not isinstance(receipt, Mapping):
        raise ValueError("receipt must be an object")
    sig = receipt.get("signature")
    if not isinstance(sig, str) or not sig.strip():
        raise ValueError("receipt.signature missing")
    claims: dict[str, str] = {}
    for key in CLAIM_FIELDS:
        val = receipt.get(key)
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"receipt.{key} missing or not a string")
        claims[key] = val.strip()
    allowed = set(CLAIM_FIELDS) | {"signature"}
    extra = [k for k in receipt.keys() if k not in allowed]
    if extra:
        raise ValueError(f"receipt has unknown fields: {sorted(extra)}")
    return claims, sig.strip()


def verify_receipt_pre_media(
    receipt: str | Mapping[str, Any],
    *,
    registry: KeyRegistry,
    expected_mutation_tool: str | None = None,
    expected_content_id: str | None = None,
    expected_package_sha256: str | None = None,
    expected_ig_user_id: str | None = None,
    expected_tenant: str = TENANT,
    expected_account_label: str = ACCOUNT_LABEL,
    now: datetime | None = None,
    clock_skew_seconds: int = CLOCK_SKEW_SECONDS,
    allowed_mutation_tools: frozenset[str] | None = None,
) -> VerifyResult:
    """Phase A: authenticate receipt + non-media bindings without media I/O.

    Verifies envelope, signature, schema/issuer/key_id, tenant, account,
    mutation_tool, time bounds, content_id, and package_sha256.

    Does NOT compare ``media_sha256s`` or ``mutation_payload_sha256`` against
    runtime digests — those require resolved media bytes (Phase B).
    """
    return verify_receipt(
        receipt,
        registry=registry,
        expected_mutation_tool=expected_mutation_tool,
        expected_content_id=expected_content_id,
        expected_package_sha256=expected_package_sha256,
        expected_mutation_payload_sha256=None,
        expected_media_sha256s=None,
        expected_ig_user_id=expected_ig_user_id,
        expected_tenant=expected_tenant,
        expected_account_label=expected_account_label,
        now=now,
        clock_skew_seconds=clock_skew_seconds,
        allowed_mutation_tools=allowed_mutation_tools,
    )


def verify_receipt(
    receipt: str | Mapping[str, Any],
    *,
    registry: KeyRegistry,
    expected_mutation_tool: str | None = None,
    expected_content_id: str | None = None,
    expected_package_sha256: str | None = None,
    expected_mutation_payload_sha256: str | None = None,
    expected_media_sha256s: list[str] | None = None,
    expected_ig_user_id: str | None = None,
    expected_tenant: str = TENANT,
    expected_account_label: str = ACCOUNT_LABEL,
    now: datetime | None = None,
    clock_skew_seconds: int = CLOCK_SKEW_SECONDS,
    allowed_mutation_tools: frozenset[str] | None = None,
) -> VerifyResult:
    """Cryptographic + binding verification. Does NOT spend/claim the approval."""
    try:
        claims, signature_b64 = parse_receipt_envelope(receipt)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return VerifyResult(ok=False, problems=[f"malformed receipt: {exc}"])

    problems: list[str] = []

    if claims["schema"] != SCHEMA_ID:
        problems.append(f"unknown schema: {claims['schema']}")
    if claims["issuer"] != ISSUER_NAME:
        problems.append(f"unknown issuer: {claims['issuer']}")
    if claims["tenant"] != expected_tenant:
        problems.append("wrong tenant")
    if claims["account_label"] != expected_account_label:
        problems.append("wrong account_label")

    ig_expected = expected_ig_user_id or DEFAULT_IG_USER_ID
    if claims["ig_user_id"] != ig_expected:
        problems.append("wrong ig_user_id")

    if not claims["content_id"]:
        problems.append("missing content_id")
    if not re.fullmatch(SHA256_RE, claims["package_sha256"]):
        problems.append("invalid package_sha256")
    if not re.fullmatch(SHA256_RE, claims["mutation_payload_sha256"]):
        problems.append("invalid mutation_payload_sha256")

    from .media_bytes import MEDIA_BEARING_TOOLS, decode_media_sha256s_claim

    try:
        claimed_media = decode_media_sha256s_claim(claims.get("media_sha256s", "[]"))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        problems.append(f"invalid media_sha256s: {exc}")
        claimed_media = []

    tools = allowed_mutation_tools if allowed_mutation_tools is not None else mutation_tool_ids()
    if claims["mutation_tool"] not in tools:
        problems.append("unsupported mutation_tool")
    if claims["mutation_tool"] in MEDIA_BEARING_TOOLS and not claimed_media:
        problems.append("media-bearing approval missing media_sha256s")
    if claims["mutation_tool"] not in MEDIA_BEARING_TOOLS and claimed_media:
        problems.append("non-media approval must not bind media_sha256s")

    if expected_mutation_tool is not None and claims["mutation_tool"] != expected_mutation_tool:
        problems.append("wrong mutation_tool")
    if expected_content_id is not None and claims["content_id"] != expected_content_id:
        problems.append("wrong content_id")
    if expected_package_sha256 is not None and claims["package_sha256"] != expected_package_sha256:
        problems.append("wrong package_sha256")
    if (
        expected_mutation_payload_sha256 is not None
        and claims["mutation_payload_sha256"] != expected_mutation_payload_sha256
    ):
        problems.append("wrong mutation_payload_sha256")
    if expected_media_sha256s is not None:
        if list(expected_media_sha256s) != claimed_media:
            problems.append("wrong media_sha256s")

    key_id = claims["key_id"]
    record = registry.get(key_id)
    if record is None:
        problems.append("unknown key_id")
    elif record.algorithm != ALGORITHM:
        problems.append("unsupported key algorithm")

    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    try:
        issued_at = _parse_rfc3339(claims["issued_at"])
        expires_at = _parse_rfc3339(claims["expires_at"])
    except ValueError as exc:
        problems.append(f"malformed timestamps: {exc}")

    if issued_at is not None and expires_at is not None:
        if expires_at <= issued_at:
            problems.append("expires_at must be after issued_at")
        if issued_at > now_utc + timedelta(seconds=clock_skew_seconds):
            problems.append("future-issued receipt outside allowed clock skew")
        if now_utc > expires_at + timedelta(seconds=clock_skew_seconds):
            problems.append("expired approval")

    if record is not None:
        try:
            payload = canonical_payload_bytes(claims)
            sig = _b64decode_sig(signature_b64)
            record.public_key().verify(sig, payload)
        except InvalidSignature:
            problems.append("invalid signature")
        except Exception as exc:
            problems.append(f"signature verify error: {exc}")

    return VerifyResult(ok=not problems, problems=problems, claims=claims)
