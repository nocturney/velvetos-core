"""Ed25519 signing for the delivery-approval issuer only.

Private key material must never enter the Instagram mutation service.
"""

from __future__ import annotations

import base64
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ..canonical import canonical_payload_bytes
from ..capabilities import mutation_tool_ids
from ..schema import (
    ACCOUNT_LABEL,
    ALGORITHM,
    DEFAULT_IG_USER_ID,
    ISSUER_NAME,
    MAX_TTL_SECONDS,
    SCHEMA_ID,
    SHA256_RE,
    TENANT,
)


def load_private_key_from_env(env: Mapping[str, str] | None = None) -> Ed25519PrivateKey:
    """Load raw 32-byte Ed25519 seed from env (base64). Issuer-only."""
    e = env or os.environ
    raw_b64 = (e.get("VELVET_DELIVERY_APPROVAL_PRIVATE_KEY_B64") or "").strip()
    if not raw_b64:
        raise RuntimeError(
            "VELVET_DELIVERY_APPROVAL_PRIVATE_KEY_B64 missing — issuer cannot sign"
        )
    # Refuse if mutation-service secrets are present in this process (isolation guard).
    forbidden = (
        "INSTAGRAM_MCP_ACCESS_TOKEN",
        "VELVET_INSTAGRAM_MCP_BEARER_TOKEN",
    )
    for name in forbidden:
        if (e.get(name) or "").strip():
            raise RuntimeError(
                f"isolation violation: {name} must not be present in the issuer process"
            )
    pad = "=" * (-len(raw_b64) % 4)
    try:
        raw = base64.urlsafe_b64decode(raw_b64 + pad)
    except Exception:
        raw = base64.b64decode(raw_b64 + pad)
    if len(raw) == 64:
        # Some exporters store seed||pub; Ed25519PrivateKey wants 32-byte seed.
        raw = raw[:32]
    if len(raw) != 32:
        raise RuntimeError("private key must decode to 32-byte Ed25519 seed")
    return Ed25519PrivateKey.from_private_bytes(raw)


def _rfc3339(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def issue_approval(
    *,
    private_key: Ed25519PrivateKey,
    key_id: str,
    content_id: str,
    package_sha256: str,
    mutation_tool: str,
    ttl_seconds: int | None = None,
    ig_user_id: str | None = None,
    now: datetime | None = None,
    allowed_mutation_tools: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Validate caller fields, mint server-controlled claims, sign.

    Caller-supplied tenant/account/schema/issuer/key_id/approval_id/nonce/times
    are ignored — server controls those fields.
    """
    problems: list[str] = []
    cid = (content_id or "").strip()
    if not cid:
        problems.append("content_id required")
    digest = (package_sha256 or "").strip()
    if not re.fullmatch(SHA256_RE, digest):
        problems.append("package_sha256 must be 64 lowercase hex")
    tool = (mutation_tool or "").strip()
    tools = allowed_mutation_tools if allowed_mutation_tools is not None else mutation_tool_ids()
    if tool not in tools:
        problems.append(f"unsupported mutation_tool: {tool}")

    ttl = MAX_TTL_SECONDS if ttl_seconds is None else int(ttl_seconds)
    if ttl <= 0 or ttl > MAX_TTL_SECONDS:
        problems.append(f"ttl_seconds must be 1..{MAX_TTL_SECONDS}")

    kid = (key_id or "").strip()
    if not kid:
        problems.append("key_id required (server-configured)")

    if problems:
        return {"ok": False, "problems": problems, "receipt": None}

    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    expires = now_utc + timedelta(seconds=ttl)
    claims = {
        "schema": SCHEMA_ID,
        "approval_id": str(uuid.uuid4()),
        "tenant": TENANT,
        "ig_user_id": (ig_user_id or DEFAULT_IG_USER_ID).strip() or DEFAULT_IG_USER_ID,
        "account_label": ACCOUNT_LABEL,
        "content_id": cid,
        "package_sha256": digest,
        "mutation_tool": tool,
        "issued_at": _rfc3339(now_utc),
        "expires_at": _rfc3339(expires),
        "nonce": secrets.token_hex(16),
        "issuer": ISSUER_NAME,
        "key_id": kid,
    }
    payload = canonical_payload_bytes(claims)
    signature = private_key.sign(payload)
    receipt = dict(claims)
    receipt["signature"] = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return {
        "ok": True,
        "problems": [],
        "algorithm": ALGORITHM,
        "receipt": receipt,
    }
