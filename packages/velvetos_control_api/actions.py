"""Fail-closed action router — contract only; no parallel workflows.

Resolves only existing approved capabilities. Unknown / unavailable / denied /
missing approval / missing confirmation → reject.
No shell execution, no caller-selected paths, no provider bypass.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from velvetos_control_api.contributions.capabilities import normalize_all_capabilities
from velvetos_control_api.errors import (
    APPROVAL_REQUIRED,
    BAD_REQUEST,
    CAPABILITY_DENIED,
    CAPABILITY_UNAVAILABLE,
    CONFIRMATION_REQUIRED,
    ControlApiError,
    UNKNOWN_ACTION,
)
from velvetos_control_api.registry import repo_root
from velvetos_control_api.schema import now_iso

_ACTION_ID_RE = re.compile(r"^[a-z][a-z0-9_.\-]{1,80}$", re.IGNORECASE)
_OBJECT_ID_RE = re.compile(r"^[A-Za-z0-9_.:\-]{1,120}$")
_IDEM_RE = re.compile(r"^[A-Za-z0-9_.:\-]{8,128}$")

# Actions that are explicitly never executable via Control API (even if listed elsewhere)
HARD_DENY_ACTIONS = frozenset(
    {
        "auto.dm",
        "print.job",
        "public.site",
        "shell.exec",
        "shell",
        "exec",
        "system",
        "run_command",
        "run-command",
        "filesystem",
        "fs.read",
        "fs.write",
        "arbitrary",
    }
)

# Path / command injection markers in any string field
_INJECTION = re.compile(
    r"(?i)(\.\./|\.\.\\|/etc/passwd|/bin/sh|cmd\.exe|powershell|"
    r"\$\(|`|;|\||&&|\brm\s+-rf\b|\bcurl\b|\bwget\b)"
)


def _receipt_id(idempotency_key: str, action_id: str, outcome: str) -> str:
    digest = hashlib.sha256(f"{idempotency_key}|{action_id}|{outcome}".encode()).hexdigest()[:24]
    return f"rcv_{digest}"


def validate_action_request(body: dict[str, Any]) -> dict[str, str]:
    if not isinstance(body, dict):
        raise ControlApiError(BAD_REQUEST, "body must be an object", status=400)

    # Reject caller-supplied executable / path fields outright
    for forbidden in (
        "command",
        "cmd",
        "shell",
        "executable",
        "path",
        "cwd",
        "script",
        "argv",
        "env",
        "url",
        "fetch",
    ):
        if forbidden in body:
            raise ControlApiError(
                CAPABILITY_DENIED,
                f"field '{forbidden}' is not allowed — no arbitrary execution or fetch",
                status=403,
            )

    action_id = str(body.get("actionId") or "").strip()
    object_id = str(body.get("objectId") or "").strip()
    confirmation = str(body.get("confirmation") or "").strip()
    idem = str(body.get("idempotencyKey") or "").strip()

    if not action_id or not _ACTION_ID_RE.match(action_id):
        raise ControlApiError(BAD_REQUEST, "invalid actionId", status=400)
    if object_id and not _OBJECT_ID_RE.match(object_id):
        raise ControlApiError(BAD_REQUEST, "invalid objectId", status=400)
    if not idem or not _IDEM_RE.match(idem):
        raise ControlApiError(
            BAD_REQUEST,
            "idempotencyKey required (8–128 chars, safe alphabet)",
            status=400,
        )

    for field_name, value in (
        ("actionId", action_id),
        ("objectId", object_id),
        ("confirmation", confirmation),
        ("idempotencyKey", idem),
    ):
        if value and _INJECTION.search(value):
            raise ControlApiError(
                CAPABILITY_DENIED,
                f"injection pattern rejected in {field_name}",
                status=403,
            )

    return {
        "actionId": action_id,
        "objectId": object_id,
        "confirmation": confirmation,
        "idempotencyKey": idem,
    }


def resolve_capability(action_id: str, *, root=None) -> dict[str, Any] | None:
    root = root or repo_root()
    for cap in normalize_all_capabilities(root):
        if cap.get("id") == action_id:
            return cap
    return None


def execute_action(body: dict[str, Any], *, root=None) -> dict[str, Any]:
    """Route an action request. v1: fail-closed — no write execution wired.

    Successful future actions must return a receipt. Accepted ≠ completed.
    """
    root = root or repo_root()
    try:
        req = validate_action_request(body)
    except ControlApiError as exc:
        # Still emit a rejection-shaped body when idempotencyKey is present
        idem = ""
        action_id = ""
        if isinstance(body, dict):
            idem = str(body.get("idempotencyKey") or "")[:128]
            action_id = str(body.get("actionId") or "invalid")[:80]
        rid = _receipt_id(idem or "missing-idem", action_id or "invalid", exc.code)
        return {
            "ok": False,
            "accepted": False,
            "completed": False,
            "error": {"code": exc.code, "message": exc.message, "details": exc.details or None},
            "receipt": {
                "receiptId": rid,
                "actionId": action_id or None,
                "objectId": (body.get("objectId") if isinstance(body, dict) else None),
                "idempotencyKey": idem or None,
                "outcome": exc.code,
                "at": now_iso(),
                "note": "rejection receipt — validation failed; no side effects",
            },
            "_httpStatus": exc.status,
        }
    action_id = req["actionId"]
    idem = req["idempotencyKey"]

    # Deterministic idempotent rejection envelope helper
    def reject(code: str, message: str, *, status: int = 403, extra: dict | None = None) -> dict[str, Any]:
        rid = _receipt_id(idem, action_id, code)
        out = {
            "ok": False,
            "accepted": False,
            "completed": False,
            "error": {"code": code, "message": message},
            "receipt": {
                "receiptId": rid,
                "actionId": action_id,
                "objectId": req["objectId"] or None,
                "idempotencyKey": idem,
                "outcome": code,
                "at": now_iso(),
                "note": "rejection receipt — accepted≠completed; no side effects",
            },
        }
        if extra:
            out["error"]["details"] = extra
        out["_httpStatus"] = status
        return out

    if action_id.lower() in HARD_DENY_ACTIONS or action_id.lower().split(".")[0] in {
        "shell",
        "exec",
        "system",
        "fs",
    }:
        return reject(CAPABILITY_DENIED, "action is hard-denied by Control API policy", status=403)

    cap = resolve_capability(action_id, root=root)
    if cap is None:
        return reject(UNKNOWN_ACTION, f"unknown actionId '{action_id}'", status=404)

    status = cap.get("status")
    risk = cap.get("risk")
    gate = cap.get("gate")

    if status == "BLOCKED":
        return reject(CAPABILITY_DENIED, "capability is blocked", status=403, extra={"risk": risk})
    if status == "UNAVAILABLE" or status == "NEEDS_AUTH":
        return reject(
            CAPABILITY_UNAVAILABLE,
            f"capability status={status}",
            status=409,
            extra={"status": status},
        )
    if status == "APPROVAL_REQUIRED" or risk in {"ORANGE", "RED"} or gate in {"lead", "deny"}:
        if gate == "deny" or status == "BLOCKED":
            return reject(CAPABILITY_DENIED, "capability denied by gate", status=403)
        if not req["confirmation"]:
            return reject(
                CONFIRMATION_REQUIRED,
                "confirmation required for approval-gated action",
                status=400,
                extra={"risk": risk, "gate": gate},
            )
        # Confirmation present still does not execute — no safe write route wired in v1
        return reject(
            APPROVAL_REQUIRED,
            "owner/lead approval required; Control API v1 does not execute this action",
            status=403,
            extra={"risk": risk},
        )

    # AVAILABLE + GREEN/YELLOW but no safe executable route wired yet
    return reject(
        CAPABILITY_UNAVAILABLE,
        "no safe canonical executable route wired for this action in Control API v1",
        status=409,
        extra={"capabilityStatus": status, "risk": risk},
    )


def idempotent_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Same idempotency key + action must yield same receipt id for same outcome."""
    ra = (a.get("receipt") or {}).get("receiptId")
    rb = (b.get("receipt") or {}).get("receiptId")
    return bool(ra) and ra == rb
