"""Server-to-server authentication for Control API.

Primary (Cloud Run): IAM --no-allow-unauthenticated (platform-enforced).
Defense in depth: shared bearer / API key in VELVETOS_CONTROL_API_TOKEN (GSM).

Designed so a later scoped operator identity can replace the shared secret
without changing endpoint contracts — callers keep Authorization: Bearer …
"""

from __future__ import annotations

import hmac
import os
from typing import Mapping

from velvetos_control_api.errors import ControlApiError, NEEDS_OPERATOR_SETUP, UNAUTHORIZED

ENV_TOKEN = "VELVETOS_CONTROL_API_TOKEN"
# Forbidden env vars — must never be mounted on this service
FORBIDDEN_ENV = (
    "INSTAGRAM_MCP_ACCESS_TOKEN",
    "VELVET_INSTAGRAM_MCP_BEARER_TOKEN",
    "INSTAGRAM_MCP_DM_ENABLED",
    "VELVET_DELIVERY_APPROVAL_ED25519_PRIVATE",
    "VELVET_DELIVERY_APPROVAL_PRIVATE_KEY",
)


def configured_token() -> str:
    return (os.environ.get(ENV_TOKEN) or "").strip()


def isolation_violations() -> list[str]:
    return [name for name in FORBIDDEN_ENV if (os.environ.get(name) or "").strip()]


def assert_isolation() -> None:
    bad = isolation_violations()
    if bad:
        raise SystemExit(
            "isolation violation: Control API must not mount "
            + ", ".join(bad)
        )


def extract_bearer(headers: Mapping[str, str]) -> str:
    """Accept Authorization: Bearer <token> or X-Api-Key / X-VelvetOS-Token."""
    # Headers may be mixed-case depending on server
    def get(name: str) -> str:
        for k, v in headers.items():
            if k.lower() == name.lower():
                return (v or "").strip()
        return ""

    auth = get("authorization")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    for alt in ("x-api-key", "x-velvetos-token"):
        val = get(alt)
        if val:
            return val
    return ""


def authorize(headers: Mapping[str, str], *, require_configured: bool = True) -> None:
    """Raise ControlApiError if the request is not authenticated.

    When the service token is unset: NEEDS_OPERATOR_SETUP (503) — fail closed,
    never serve anonymous snapshot data.
    """
    expected = configured_token()
    if not expected:
        if require_configured:
            raise ControlApiError(
                NEEDS_OPERATOR_SETUP,
                "Control API token not configured",
                status=503,
            )
        return
    provided = extract_bearer(headers)
    if not provided or not hmac.compare_digest(
        provided.encode("utf-8"), expected.encode("utf-8")
    ):
        raise ControlApiError(UNAUTHORIZED, "invalid or missing credentials", status=401)
