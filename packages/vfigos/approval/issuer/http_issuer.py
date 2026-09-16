"""Cloud Run HTTP entry for velvet-delivery-approval-issuer.

Auth: Cloud Run IAM (require authenticated invocation). This process must NOT
load Meta Graph tokens, Instagram MCP bearer, FastMCP, or mutation runtime.

Optional defense-in-depth app bearer (VELVET_DELIVERY_APPROVAL_ISSUER_TOKEN)
lives only in issuer GSM — never in MCP config / mutation service.

Body handling: authenticate (optional app bearer) and enforce an explicit size
cap before buffering/parsing JSON. Never unbounded ``await request.body()``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

# Resolve packages/ on sys.path whether running from repo or container layout.
_HERE = Path(__file__).resolve().parent
_APPROVAL = _HERE.parent
_VFIGOS = _APPROVAL.parent
_PACKAGES = _VFIGOS.parent
for candidate in (_PACKAGES, _APPROVAL.parent.parent):
    if (candidate / "vfigos" / "approval").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
        break


def _configured_key_id() -> str:
    return (os.environ.get("VELVET_DELIVERY_APPROVAL_KEY_ID") or "").strip()


def _optional_app_bearer() -> str:
    return (os.environ.get("VELVET_DELIVERY_APPROVAL_ISSUER_TOKEN") or "").strip()


def _max_body_bytes() -> int:
    from vfigos.approval.schema import ISSUER_MAX_BODY_BYTES

    return ISSUER_MAX_BODY_BYTES


def _check_isolation() -> None:
    for name in (
        "INSTAGRAM_MCP_ACCESS_TOKEN",
        "VELVET_INSTAGRAM_MCP_BEARER_TOKEN",
        "INSTAGRAM_MCP_DM_ENABLED",
    ):
        if (os.environ.get(name) or "").strip():
            raise SystemExit(
                f"isolation violation: {name} must not be mounted on the issuer service"
            )


async def healthz(_request: Request) -> Response:
    return JSONResponse(
        {
            "ok": True,
            "service": "velvet-delivery-approval-issuer",
            "mcp": False,
            "meta_graph": False,
            "auth": "cloud-run-iam",
            "signing": "Ed25519",
            "schema": "velvet.delivery_approval.v1",
            "key_id_configured": bool(_configured_key_id()),
            "mutation_service_has_private_key": False,
            "max_body_bytes": _max_body_bytes(),
        }
    )


def _authorize_request(request: Request) -> str | None:
    """Cloud Run IAM is primary. Optional app bearer = defense in depth only.

    When running behind Cloud Run with --no-allow-unauthenticated, Google already
    rejected anonymous callers. Optional bearer, if set, must match.
    Checked before any body buffering.
    """
    expected = _optional_app_bearer()
    if not expected:
        return None
    auth = (request.headers.get("authorization") or "").strip()
    x_api = (request.headers.get("x-api-key") or "").strip()
    token = ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    elif x_api:
        token = x_api
    if not token or not secrets_compare(token, expected):
        return "unauthorized"
    return None


def secrets_compare(a: str, b: str) -> bool:
    import hmac

    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


async def _read_body_capped(request: Request, max_bytes: int) -> tuple[bytes | None, Response | None]:
    """Read request body with hard cap. Prefer Content-Length short-circuit."""
    cl = request.headers.get("content-length")
    if cl is not None and cl.strip():
        try:
            length = int(cl.strip())
        except ValueError:
            return None, JSONResponse(
                {"ok": False, "problems": ["invalid Content-Length"]}, status_code=400
            )
        if length > max_bytes:
            return None, JSONResponse(
                {"ok": False, "problems": ["request body too large"]}, status_code=413
            )

    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        if not chunk:
            continue
        total += len(chunk)
        if total > max_bytes:
            return None, JSONResponse(
                {"ok": False, "problems": ["request body too large"]}, status_code=413
            )
        chunks.append(chunk)
    return b"".join(chunks), None


async def issue(request: Request) -> Response:
    # 1) Auth before any body buffering / JSON parse.
    denied = _authorize_request(request)
    if denied:
        return JSONResponse({"ok": False, "problems": [denied]}, status_code=401)

    # 2) Cap then buffer; never unbounded request.body()/json().
    raw, err = await _read_body_capped(request, _max_body_bytes())
    if err is not None:
        return err
    assert raw is not None
    try:
        body = json.loads(raw.decode("utf-8") if raw else "null")
    except Exception:
        return JSONResponse({"ok": False, "problems": ["invalid JSON body"]}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"ok": False, "problems": ["body must be an object"]}, status_code=400)

    # Reject attempts to supply server-owned fields as authoritative input.
    # They are ignored deterministically (not blind-signed).
    from vfigos.approval.issuer.signing import issue_approval, load_private_key_from_env

    key_id = _configured_key_id()
    if not key_id:
        return JSONResponse(
            {
                "ok": False,
                "problems": ["issuer key_id not configured (VELVET_DELIVERY_APPROVAL_KEY_ID)"],
                "status": "NEEDS_OPERATOR_SETUP",
            },
            status_code=503,
        )
    try:
        private_key = load_private_key_from_env()
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "problems": [str(exc)],
                "status": "NEEDS_OPERATOR_SETUP",
            },
            status_code=503,
        )

    # mutation_payload is hashed server-side; ignore any client mutation_payload_sha256.
    # media_sha256s are computed from media_artifacts bytes or CAS URL fetch — never trusted.
    mutation_payload = body.get("mutation_payload")
    if mutation_payload is not None and not isinstance(mutation_payload, dict):
        return JSONResponse(
            {"ok": False, "problems": ["mutation_payload must be an object"]},
            status_code=400,
        )
    media_artifacts = body.get("media_artifacts")
    if media_artifacts is not None and not isinstance(media_artifacts, list):
        return JSONResponse(
            {"ok": False, "problems": ["media_artifacts must be a list"]},
            status_code=400,
        )

    result = issue_approval(
        private_key=private_key,
        key_id=key_id,
        content_id=str(body.get("content_id") or ""),
        package_sha256=str(body.get("package_sha256") or ""),
        mutation_tool=str(body.get("mutation_tool") or ""),
        mutation_payload=mutation_payload if isinstance(mutation_payload, dict) else {},
        media_artifacts=media_artifacts if isinstance(media_artifacts, list) else None,
        ttl_seconds=body.get("ttl_seconds"),
        # Server-controlled account identity — ignore caller tenant/ig overrides.
        ig_user_id=None,
    )
    status = 200 if result.get("ok") else 400
    return JSONResponse(result, status_code=status)


def create_app() -> Starlette:
    _check_isolation()
    return Starlette(
        routes=[
            Route("/healthz", healthz, methods=["GET"]),
            Route("/health", healthz, methods=["GET"]),
            Route("/v1/delivery-approvals", issue, methods=["POST"]),
        ]
    )


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(create_app(), host=host, port=port, proxy_headers=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    main()
