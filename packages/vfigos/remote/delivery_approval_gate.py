"""Enforce signed delivery approval at the Instagram mutation boundary.

Applied from http_server.py **before** mutation/story overlays register tools
so write callables never capture a stale ``_guard`` reference.

Primary enforcement:
1. ASGI middleware captures ``delivery_approval`` + full MCP tool arguments
   (and optional ``X-Velvet-Delivery-Approval`` header) into ContextVars,
   with an explicit body-size cap before FastMCP auth.
2. ``instagram_mcp.server._guard`` is patched so every canonical write tool
   verify→atomic-claim before the Graph impl runs. Call sites must resolve
   ``_guard`` dynamically via ``instagram_mcp.server`` (never ``from … import _guard``).

This process must NEVER load the Ed25519 private key or issuer credential.
"""

from __future__ import annotations

import json
import os
import sys
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Callable

_HERE = Path(__file__).resolve().parent
for candidate in (
    _HERE.parents[2] if len(_HERE.parents) >= 3 else None,
    Path("/app/packages"),
):
    if candidate and candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

_delivery_approval_ctx: ContextVar[Any] = ContextVar("velvet_delivery_approval", default=None)
_binding_ctx: ContextVar[dict[str, Any]] = ContextVar("velvet_delivery_binding", default={})
_mutation_args_ctx: ContextVar[dict[str, Any]] = ContextVar("velvet_mutation_args", default={})


def get_request_delivery_approval() -> Any:
    return _delivery_approval_ctx.get()


def get_request_mutation_args() -> dict[str, Any]:
    return dict(_mutation_args_ctx.get() or {})


def _registry():
    from vfigos.approval.keys_registry import KeyRegistry

    path = (os.environ.get("VELVET_DELIVERY_APPROVAL_REGISTRY") or "").strip()
    if path:
        return KeyRegistry.from_path(Path(path))
    return KeyRegistry.from_path()


def _spend_store():
    from vfigos.approval.spend import default_spend_store_from_env

    return default_spend_store_from_env()


def _mutation_tools() -> frozenset[str]:
    from vfigos.approval.capabilities import mutation_tool_ids

    names = set(mutation_tool_ids())
    names.add("delete_media")
    return frozenset(names)


def authorize_or_block(mutation_tool: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Return a BLOCKED MCP dict, or None if mutation may proceed."""
    from vfigos.approval.gate import authorize_mutation
    from vfigos.approval.media_bytes import (
        MEDIA_BEARING_TOOLS,
        inject_media_sha256s,
        resolve_media_sha256s,
        strip_untrusted_media_digest_fields,
    )
    from vfigos.approval.mutation_payload import merge_tool_params, mutation_payload_sha256

    for forbidden in (
        "VELVET_DELIVERY_APPROVAL_PRIVATE_KEY_B64",
        "VELVET_DELIVERY_APPROVAL_ISSUER_TOKEN",
    ):
        if (os.environ.get(forbidden) or "").strip():
            return {
                "ok": False,
                "blocked": True,
                "error": f"isolation violation: {forbidden} must not be present on mutation service",
                "error_class": "delivery_approval",
                "mutated": False,
            }

    params = dict(params or {})
    binding = dict(_binding_ctx.get() or {})
    mcp_args = get_request_mutation_args()
    receipt = params.get("delivery_approval")
    if receipt is None:
        receipt = get_request_delivery_approval()
    if isinstance(receipt, str):
        try:
            receipt = json.loads(receipt)
        except Exception:
            pass

    content_id = params.get("content_id") or binding.get("content_id") or mcp_args.get("content_id")
    package_sha256 = (
        params.get("package_sha256")
        or binding.get("package_sha256")
        or mcp_args.get("package_sha256")
    )
    if isinstance(content_id, str):
        content_id = content_id.strip() or None
    else:
        content_id = None
    if isinstance(package_sha256, str):
        package_sha256 = package_sha256.strip() or None
    else:
        package_sha256 = None

    # Authoritative payload = actual tool args (MCP args preferred over guard summary).
    merged = strip_untrusted_media_digest_fields(merge_tool_params(params, mcp_args))
    media_digests: list[str] = []
    if mutation_tool in MEDIA_BEARING_TOOLS:
        # Hash exact bytes that will back Graph's URL fetch — BEFORE claim.
        try:
            media_digests = resolve_media_sha256s(mutation_tool, merged)
        except (KeyError, TypeError, ValueError) as exc:
            return {
                "ok": False,
                "blocked": True,
                "error": "delivery approval required",
                "error_class": "delivery_approval",
                "problems": [f"media byte digest failed: {exc}"],
                "mutated": False,
                "mutation_tool": mutation_tool,
            }
        merged = inject_media_sha256s(mutation_tool, merged, media_digests)

    try:
        payload_digest = mutation_payload_sha256(mutation_tool, merged)
    except (KeyError, TypeError, ValueError) as exc:
        return {
            "ok": False,
            "blocked": True,
            "error": "delivery approval required",
            "error_class": "delivery_approval",
            "problems": [f"mutation payload digest failed: {exc}"],
            "mutated": False,
            "mutation_tool": mutation_tool,
        }

    result = authorize_mutation(
        receipt=receipt,
        mutation_tool=mutation_tool,
        spend_store=_spend_store(),
        registry=_registry(),
        content_id=content_id,
        package_sha256=package_sha256,
        mutation_payload_sha256=payload_digest,
        media_sha256s=media_digests if mutation_tool in MEDIA_BEARING_TOOLS else [],
        ig_user_id=(os.environ.get("INSTAGRAM_MCP_IG_USER_ID") or "").strip() or None,
    )
    if result.ok:
        return None
    return {
        "ok": False,
        "blocked": True,
        "error": "delivery approval required",
        "error_class": "delivery_approval",
        "problems": result.problems,
        "gate": result.as_dict(),
        "mutated": False,
        "mutation_tool": mutation_tool,
    }


def apply_delivery_approval_gate(mcp: Any = None) -> None:
    """Patch ``instagram_mcp.server._guard`` before write tools bind callables.

    Install early in ``http_server._build_mcp`` (before ``apply_mutation_tools`` /
    story overlays). Tools must call ``instagram_mcp.server._guard`` dynamically.
    """
    import instagram_mcp.server as ig_server

    mutation_names = _mutation_tools()
    if getattr(ig_server, "_velvet_delivery_approval_guard_patched", False):
        return

    _orig_guard = ig_server._guard

    def _guard(tool_name: str, params: dict[str, Any], impl: Callable[[], Any]):
        if tool_name in mutation_names:
            blocked = authorize_or_block(tool_name, dict(params or {}))
            if blocked is not None:
                return blocked
        return _orig_guard(tool_name, params, impl)

    ig_server._guard = _guard  # type: ignore[assignment]
    ig_server._velvet_delivery_approval_guard_patched = True  # type: ignore[attr-defined]


def live_guard():
    """Resolve the current module ``_guard`` (never a stale captured reference)."""
    import instagram_mcp.server as ig_server

    return ig_server._guard


class DeliveryApprovalCaptureMiddleware:
    """Capture delivery_approval + mutation args with an explicit body-size cap."""

    def __init__(self, app, max_body_bytes: int | None = None):
        from vfigos.approval.schema import MUTATION_CAPTURE_MAX_BODY_BYTES

        self.app = app
        self.max_body_bytes = (
            MUTATION_CAPTURE_MAX_BODY_BYTES if max_body_bytes is None else int(max_body_bytes)
        )

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        header_val = b""
        content_length = None
        for k, v in scope.get("headers") or []:
            name = k.decode().lower()
            if name == "x-velvet-delivery-approval":
                header_val = v
            elif name == "content-length":
                try:
                    content_length = int(v.decode().strip())
                except Exception:
                    content_length = None

        if content_length is not None and content_length > self.max_body_bytes:
            await _send_json(send, 413, {"ok": False, "problems": ["request body too large"]})
            return

        chunks: list[bytes] = []
        total = 0
        body_messages: list[dict] = []
        more = True
        while more:
            msg = await receive()
            body_messages.append(msg)
            if msg["type"] != "http.request":
                more = False
                continue
            piece = msg.get("body") or b""
            if piece:
                total += len(piece)
                if total > self.max_body_bytes:
                    await _send_json(
                        send, 413, {"ok": False, "problems": ["request body too large"]}
                    )
                    return
                chunks.append(piece)
            more = bool(msg.get("more_body"))

        raw = b"".join(chunks)
        approval_from_body, binding, mutation_args = _extract_from_mcp_body(raw)
        approval = approval_from_body
        if approval is None and header_val:
            try:
                approval = json.loads(header_val.decode())
            except Exception:
                approval = header_val.decode()

        token_a = _delivery_approval_ctx.set(approval)
        token_b = _binding_ctx.set(binding)
        token_c = _mutation_args_ctx.set(mutation_args)
        try:
            idx = {"i": 0}

            async def replay_receive():
                i = idx["i"]
                if i < len(body_messages):
                    idx["i"] = i + 1
                    return body_messages[i]
                return await receive()

            await self.app(scope, replay_receive, send)
        finally:
            _mutation_args_ctx.reset(token_c)
            _binding_ctx.reset(token_b)
            _delivery_approval_ctx.reset(token_a)


async def _send_json(send, status: int, body: dict[str, Any]) -> None:
    payload = json.dumps(body).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(payload)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": payload})


def _extract_from_mcp_body(raw: bytes) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    if not raw:
        return None, {}, {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return None, {}, {}
    messages = data if isinstance(data, list) else [data]
    approval = None
    binding: dict[str, Any] = {}
    mutation_args: dict[str, Any] = {}
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        if not args and isinstance(params.get("args"), dict):
            args = params["args"]
        if args:
            mutation_args = dict(args)
        if "delivery_approval" in args:
            approval = args.get("delivery_approval")
        for key in ("content_id", "package_sha256"):
            if key in args and args[key]:
                binding[key] = args[key]
        req = params.get("request") if isinstance(params.get("request"), dict) else {}
        if "delivery_approval" in req:
            approval = req.get("delivery_approval")
    return approval, binding, mutation_args
