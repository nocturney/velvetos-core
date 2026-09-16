"""Single deterministic serializer for delivery-approval payloads.

Signer tests and verifier MUST use this module only — no second serializer.
"""

from __future__ import annotations

import json
from typing import Any, Mapping


def canonical_payload_bytes(claims: Mapping[str, Any]) -> bytes:
    """Return UTF-8 bytes of claims as sorted-key compact JSON (no whitespace).

    Only claim fields are serialized — never the signature envelope.
    """
    if not isinstance(claims, Mapping):
        raise TypeError("claims must be a mapping")
    # Reject nested structures — claims are flat strings only.
    flat: dict[str, str] = {}
    for key, value in claims.items():
        if not isinstance(key, str):
            raise TypeError("claim keys must be strings")
        if value is None:
            raise TypeError(f"claim {key!r} must not be null")
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            # Allow int only if somehow present — coerce refused; strings only.
            if not isinstance(value, str):
                raise TypeError(f"claim {key!r} must be a string")
        flat[key] = value if isinstance(value, str) else str(value)
    return json.dumps(flat, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
