"""Shared schema constants and collection envelopes for velvetos.control.v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

SCHEMA = "velvetos.control.v1"
SERVICE_NAME = "velvetos-control-api"

# Capability status for UI (normalized from canonical registries)
CAP_STATUS = (
    "AVAILABLE",
    "DEGRADED",
    "NEEDS_AUTH",
    "UNAVAILABLE",
    "BLOCKED",
    "APPROVAL_REQUIRED",
)

# Risk from Don't Bother Christian policy
RISK = ("GREEN", "YELLOW", "ORANGE", "RED")

# Collection / domain projection states
DOMAIN_STATE = (
    "ready",           # verified projection; items may be empty
    "unavailable",     # source not projected / not reachable — items must be null
    "degraded",        # partial; see reason
    "needs_sync",      # known adapter needs refresh — not zero
    "conflict",        # dirty/conflict — refuse silent empty
    "unknown",         # cannot determine
)

FRESHNESS = ("live", "fresh", "stale", "unknown")

# Destination paths allowed in search results (relative UI routes only)
ALLOWED_DESTINATION_PREFIXES = (
    "/jobs/",
    "/attention/",
    "/capabilities/",
    "/activity/",
    "/modules/",
    "/health/",
    "/collections/",
    "/system/",
)

MAX_BODY_BYTES = 64 * 1024  # 64 KiB — actions are small
MAX_QUERY_LEN = 200
REQUEST_SOFT_TIMEOUT_S = 25


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def provenance(
    *,
    source: str,
    verified_at: str | None = None,
    freshness: str = "unknown",
    receipt: Any = None,
    authority: str = "projection",
) -> dict[str, Any]:
    """Provenance for operational objects. Derived projections are not canonical truth."""
    return {
        "source": source,
        "verifiedAt": verified_at,
        "freshness": freshness if freshness in FRESHNESS else "unknown",
        "receipt": receipt,
        "authority": authority,  # "canonical" | "projection" | "adapter-cache"
    }


def collection_ready(
    items: list[Any],
    *,
    source: str,
    verified_at: str | None = None,
    freshness: str = "fresh",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Verified collection — empty list is allowed only when source proves empty."""
    out: dict[str, Any] = {
        "state": "ready",
        "items": list(items),
        "count": len(items),
        "reason": None,
        "provenance": provenance(
            source=source,
            verified_at=verified_at,
            freshness=freshness,
            authority="adapter-cache" if "cache" in source or "ledger" in source else "projection",
        ),
    }
    if extra:
        out.update(extra)
    return out


def collection_unavailable(
    *,
    reason: str,
    source: str,
    verified_at: str | None = None,
    state: str = "unavailable",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Unavailable / not-yet-projected — items MUST be null (never [])."""
    if state not in DOMAIN_STATE:
        state = "unavailable"
    out: dict[str, Any] = {
        "state": state,
        "items": None,  # never invent []
        "count": None,  # never invent 0
        "reason": reason,
        "provenance": provenance(
            source=source,
            verified_at=verified_at,
            freshness="unknown",
            authority="projection",
        ),
    }
    if extra:
        out.update(extra)
    return out


def normalize_risk(raw: str | None, *, gate: str | None = None) -> str:
    """Map policy risk / gate to UI risk. Do not infer from tool availability alone."""
    g = (gate or "").strip().lower()
    if g == "deny":
        return "RED"
    if g == "lead":
        return "ORANGE"
    r = (raw or "").strip().lower()
    mapping = {
        "green": "GREEN",
        "yellow": "YELLOW",
        "orange": "ORANGE",
        "red": "RED",
        "g": "GREEN",
        "y": "YELLOW",
        "o": "ORANGE",
        "r": "RED",
    }
    if r in mapping:
        return mapping[r]
    if g == "none" or not g:
        return "GREEN"
    return "YELLOW"


def normalize_cap_status(
    *,
    gate: str | None = None,
    raw_status: str | None = None,
    supported: bool | None = None,
    auth: str | None = None,
) -> str:
    g = (gate or "").strip().lower()
    if g == "deny":
        return "BLOCKED"
    if g == "lead":
        return "APPROVAL_REQUIRED"
    if supported is False:
        return "UNAVAILABLE"
    s = (raw_status or "").strip().lower()
    if s in {"needsauth", "needs_auth", "auth_required"}:
        return "NEEDS_AUTH"
    if s in {"degraded", "partial"}:
        return "DEGRADED"
    if s in {"blocked", "denied", "forbidden"}:
        return "BLOCKED"
    if s in {"unsupported", "unavailable", "missing"}:
        return "UNAVAILABLE"
    a = (auth or "").strip().lower()
    if a in {"needsauth", "needs_auth"}:
        return "NEEDS_AUTH"
    if s in {"ready", "available", "ok", ""} or s is None:
        return "AVAILABLE"
    return "AVAILABLE"
