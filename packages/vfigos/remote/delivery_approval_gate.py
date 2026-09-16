"""Enforce signed delivery approval at the Instagram mutation boundary.

Applied from http_server.py after other overlays.

Primary enforcement:
1. ASGI middleware captures ``delivery_approval`` from MCP ``tools/call`` args
   (and optional ``X-Velvet-Delivery-Approval`` header) into a ContextVar.
2. ``instagram_mcp.server._guard`` is patched so every canonical write tool
   verify→atomic-claim before the Graph impl runs.

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


def get_request_delivery_approval() -> Any:
    return _delivery_approval_ctx.get()


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
    receipt = params.get("delivery_approval")
    if receipt is None:
        receipt = get_request_delivery_approval()
    if isinstance(receipt, str):
        try:
            receipt = json.loads(receipt)
        except Exception:
            pass

    content_id = params.get("content_id") or binding.get("content_id")
    package_sha256 = params.get("package_sha256") or binding.get("package_sha256")
    if isinstance(content_id, str):
        content_id = content_id.strip() or None
    else:
        content_id = None
    if isinstance(package_sha256, str):
        package_sha256 = package_sha256.strip() or None
    else:
        package_sha256 = None

    result = authorize_mutation(
        receipt=receipt,
        mutation_tool=mutation_tool,
        spend_store=_spend_store(),
        registry=_registry(),
        content_id=content_id,
        package_sha256=package_sha256,
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


def apply_delivery_approval_gate(mcp: Any) -> None:
    """Patch ``_guard`` so write tools cannot bypass delivery approval."""
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


class DeliveryApprovalCaptureMiddleware:
    """Capture delivery_approval from header or MCP tools/call arguments."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        header_val = b""
        for k, v in scope.get("headers") or []:
            if k.decode().lower() == "x-velvet-delivery-approval":
                header_val = v
                break

        chunks: list[bytes] = []
        approval_from_body: Any = None
        binding: dict[str, Any] = {}

        async def new_receive():
            nonlocal approval_from_body, binding
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body") or b""
                if body:
                    chunks.append(body)
                if not message.get("more_body", False):
                    raw = b"".join(chunks)
                    approval_from_body, binding = _extract_from_mcp_body(raw)
            return message

        token_a = None
        token_b = None
        try:
            # Pre-set from header; body may refine after first chunk — we set after
            # full body in new_receive, but tool may run after body consumed.
            # So we need to parse body before app runs. Buffer full body first.
            body_messages: list[dict] = []
            more = True
            while more:
                msg = await receive()
                body_messages.append(msg)
                if msg["type"] != "http.request":
                    more = False
                else:
                    if msg.get("body"):
                        chunks.append(msg["body"])
                    more = bool(msg.get("more_body"))

            raw = b"".join(chunks)
            approval_from_body, binding = _extract_from_mcp_body(raw)
            approval = approval_from_body
            if approval is None and header_val:
                try:
                    approval = json.loads(header_val.decode())
                except Exception:
                    approval = header_val.decode()

            token_a = _delivery_approval_ctx.set(approval)
            token_b = _binding_ctx.set(binding)

            # Replay buffered messages to the app.
            idx = {"i": 0}

            async def replay_receive():
                i = idx["i"]
                if i < len(body_messages):
                    idx["i"] = i + 1
                    return body_messages[i]
                return await receive()

            await self.app(scope, replay_receive, send)
        finally:
            if token_b is not None:
                _binding_ctx.reset(token_b)
            if token_a is not None:
                _delivery_approval_ctx.reset(token_a)


def _extract_from_mcp_body(raw: bytes) -> tuple[Any, dict[str, Any]]:
    if not raw:
        return None, {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return None, {}
    # JSON-RPC single or batch
    messages = data if isinstance(data, list) else [data]
    approval = None
    binding: dict[str, Any] = {}
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        # MCP tools/call: params.name + params.arguments
        args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        if not args and isinstance(params.get("args"), dict):
            args = params["args"]
        if "delivery_approval" in args:
            approval = args.get("delivery_approval")
        for key in ("content_id", "package_sha256"):
            if key in args and args[key]:
                binding[key] = args[key]
        # Some clients nest under "request"
        req = params.get("request") if isinstance(params.get("request"), dict) else {}
        if "delivery_approval" in req:
            approval = req.get("delivery_approval")
    return approval, binding
