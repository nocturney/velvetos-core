"""Normalized error responses — never leak stack traces or secrets."""

from __future__ import annotations

import re
from typing import Any

# Patterns that must never appear in client-facing bodies
_SECRET_HINTS = re.compile(
    r"(?i)(bearer\s+[a-z0-9._\-]+|api[_-]?key\s*[:=]\s*\S+|VELVETOS_CONTROL_API_TOKEN|"
    r"INSTAGRAM_MCP_ACCESS_TOKEN|VELVET_INSTAGRAM_MCP_BEARER|private[_-]?key|"
    r"BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY)"
)


class ControlApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


def sanitize_public(text: str) -> str:
    if not text:
        return text
    if _SECRET_HINTS.search(text):
        return "[redacted]"
    return text


def error_body(code: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "ok": False,
        "error": {
            "code": code,
            "message": sanitize_public(message),
        },
    }
    if details:
        # Drop any value that looks like a secret
        clean: dict[str, Any] = {}
        for k, v in details.items():
            if isinstance(v, str):
                clean[k] = sanitize_public(v)
            else:
                clean[k] = v
        body["error"]["details"] = clean
    return body


# Standard codes
UNAUTHORIZED = "UNAUTHORIZED"
FORBIDDEN = "FORBIDDEN"
NOT_FOUND = "NOT_FOUND"
METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
BAD_REQUEST = "BAD_REQUEST"
BODY_TOO_LARGE = "BODY_TOO_LARGE"
INVALID_JSON = "INVALID_JSON"
NEEDS_OPERATOR_SETUP = "NEEDS_OPERATOR_SETUP"
CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
CAPABILITY_DENIED = "CAPABILITY_DENIED"
UNKNOWN_ACTION = "UNKNOWN_ACTION"
APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
INTERNAL = "INTERNAL"
