"""Delivery-approval schema constants (velvet.delivery_approval.v1)."""

from __future__ import annotations

SCHEMA_ID = "velvet.delivery_approval.v1"
ALGORITHM = "Ed25519"
ISSUER_NAME = "velvet-delivery-approval-issuer"
TENANT = "velvet-factory"
ACCOUNT_LABEL = "velvets_cloud"
# Canonical IG business account id for @velvets_cloud (CAPABILITIES.json).
DEFAULT_IG_USER_ID = "17841407772120429"

MAX_TTL_SECONDS = 30 * 60  # 30 minutes
CLOCK_SKEW_SECONDS = 60

# Deterministic claim field order for documentation; canonical.py sorts keys.
CLAIM_FIELDS = (
    "schema",
    "approval_id",
    "tenant",
    "ig_user_id",
    "account_label",
    "content_id",
    "package_sha256",
    "mutation_tool",
    "issued_at",
    "expires_at",
    "nonce",
    "issuer",
    "key_id",
)

SHA256_RE = r"^[0-9a-f]{64}$"
