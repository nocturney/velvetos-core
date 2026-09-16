"""Canonical mutation-payload digest for delivery-approval binding.

One serializer for issuer + mutation boundary. Digests only the public
mutation-relevant fields each write tool actually sends — never invent fields.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .schema import SHA256_RE

# Exact public mutation-relevant fields per write tool (ordered for docs only;
# JSON serialization always sorts keys). List order inside list values is significant.
MUTATION_PAYLOAD_FIELDS: dict[str, tuple[str, ...]] = {
    "publish_image": ("image_url", "caption", "account"),
    "publish_video": ("video_url", "caption", "account"),
    "publish_reel": ("video_url", "caption", "account", "share_to_feed", "cover_url"),
    "publish_carousel": ("image_urls", "caption", "account"),
    "publish_story": ("image_url", "video_url", "account"),
    "delete_media": ("media_id", "account"),
    "reply_to_comment": ("comment_id", "message", "account"),
    "hide_comment": ("comment_id", "hide", "account"),
    "delete_comment": ("comment_id", "account"),
}

# Args that are never part of the Graph mutation payload binding.
_EXCLUDED_ARG_KEYS = frozenset(
    {
        "delivery_approval",
        "content_id",
        "package_sha256",
        "mutation_payload_sha256",
        "confirm_irreversible",
    }
)


def _normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        raise TypeError("mutation payload must not contain floats")
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return [_normalize_value(v) for v in value]
    if isinstance(value, Mapping):
        raise TypeError("mutation payload must not contain nested objects")
    raise TypeError(f"unsupported mutation payload type: {type(value).__name__}")


def extract_mutation_payload(
    mutation_tool: str,
    params: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return the canonical subset of params for ``mutation_tool``.

    Missing/None fields are omitted (not invented). Unknown tools raise KeyError.
    """
    tool = (mutation_tool or "").strip()
    if tool not in MUTATION_PAYLOAD_FIELDS:
        raise KeyError(f"unsupported mutation_tool for payload binding: {tool}")
    src = dict(params or {})
    out: dict[str, Any] = {"mutation_tool": tool}
    for field in MUTATION_PAYLOAD_FIELDS[tool]:
        if field not in src:
            continue
        value = src[field]
        if value is None:
            continue
        out[field] = _normalize_value(value)
    return out


def canonical_mutation_payload_bytes(
    mutation_tool: str,
    params: Mapping[str, Any] | None,
) -> bytes:
    payload = extract_mutation_payload(mutation_tool, params)
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )


def mutation_payload_sha256(
    mutation_tool: str,
    params: Mapping[str, Any] | None,
) -> str:
    """SHA-256 hex of the canonical mutation payload JSON."""
    digest = hashlib.sha256(canonical_mutation_payload_bytes(mutation_tool, params)).hexdigest()
    if not __import__("re").fullmatch(SHA256_RE, digest):
        raise RuntimeError("internal digest error")
    return digest


def merge_tool_params(
    guard_params: Mapping[str, Any] | None,
    mcp_args: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Merge guard params with MCP tool arguments (MCP args win for payload fields)."""
    merged = {k: v for k, v in dict(guard_params or {}).items() if k not in _EXCLUDED_ARG_KEYS}
    for key, value in dict(mcp_args or {}).items():
        if key in _EXCLUDED_ARG_KEYS:
            continue
        merged[key] = value
    return merged
