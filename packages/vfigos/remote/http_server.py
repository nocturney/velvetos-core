"""Cloud Run HTTP entry for VelvetOS Instagram MCP (streamable-http).

Wraps adelaidasofia/instagram-mcp with a connector Bearer gate that is
independent of the Meta Graph access token.

Env:
  VELVET_INSTAGRAM_MCP_BEARER_TOKEN  — required for /mcp (ChatGPT API key / Cursor)
  INSTAGRAM_MCP_ACCESS_TOKEN        — Meta Graph (upstream package)
  INSTAGRAM_MCP_IG_USER_ID          — Meta IG user id
  INSTAGRAM_MCP_APP_SECRET          — optional
  PORT / MCP_PATH                   — Cloud Run bind (default 8080 / /mcp)

No secrets in source. Do not enable INSTAGRAM_MCP_DM_ENABLED for VelvetOS HQ.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

# Allow `python3 http_server.py` in Docker (/app) and repo checkouts.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_REPO = _HERE.parents[2] if len(_HERE.parents) >= 3 else None
if _REPO and str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _require_bearer() -> str:
    token = (os.environ.get("VELVET_INSTAGRAM_MCP_BEARER_TOKEN") or "").strip()
    if not token:
        raise SystemExit(
            "VELVET_INSTAGRAM_MCP_BEARER_TOKEN is required for the remote MCP HTTP entry. "
            "Store it in Secret Manager — never commit it."
        )
    if not (os.environ.get("INSTAGRAM_MCP_ACCESS_TOKEN") or "").strip():
        raise SystemExit(
            "INSTAGRAM_MCP_ACCESS_TOKEN is required (Meta Graph). "
            "It must stay in Secret Manager / runtime env — never use it as the ChatGPT connector key."
        )
    if not (os.environ.get("INSTAGRAM_MCP_IG_USER_ID") or "").strip():
        raise SystemExit("INSTAGRAM_MCP_IG_USER_ID is required.")
    return token


def _build_mcp():
    """Import the canonical Instagram FastMCP instance and attach connector auth."""
    from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

    # Import after env checks so missing Meta token fails closed before binding tools.
    from instagram_mcp.server import mcp as ig_mcp

    # Graph v21 Insights hardening (does not rebuild the MCP — patches insights tools only).
    from insights_v21 import apply_insights_patch

    apply_insights_patch(ig_mcp)

    # Official Graph mutation matrix tools (honest unsupported + gated delete).
    from mutations import apply_mutation_tools

    apply_mutation_tools(ig_mcp)

    # Read-only live CTA constitution audit (no caption/bio mutation).
    from cta_tools import apply_cta_audit_tools

    apply_cta_audit_tools(ig_mcp)

    bearer = _require_bearer()
    ig_mcp.auth = StaticTokenVerifier(
        tokens={
            bearer: {
                "client_id": "velvetos-instagram-connector",
                "scopes": ["instagram:mcp"],
            }
        },
        required_scopes=["instagram:mcp"],
    )
    # Prefer a stable server name for ChatGPT / Cursor namespaces.
    if getattr(ig_mcp, "name", None) != "instagram":
        try:
            ig_mcp.name = "instagram"
        except Exception:
            pass
    return ig_mcp


async def healthz(_request: Request) -> Response:
    return JSONResponse(
        {
            "ok": True,
            "service": "velvet-instagram-mcp",
            "transport": "streamable-http",
            "auth": "bearer",
            "chatgpt_auth": "API key",
            "mcp_path": os.environ.get("MCP_PATH", "/mcp"),
            "insights_compat": "graph_v21",
        }
    )


class ApiKeyHeaderMiddleware:
    """Map ChatGPT-style X-Api-Key / raw Authorization into Bearer for StaticTokenVerifier."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = list(scope.get("headers") or [])
            lower = {k.decode().lower(): v for k, v in headers}
            auth = lower.get("authorization", b"").decode()
            x_api = lower.get("x-api-key", b"").decode().strip()
            if x_api and not auth.lower().startswith("bearer "):
                headers.append((b"authorization", f"Bearer {x_api}".encode()))
                scope = dict(scope)
                scope["headers"] = headers
            elif auth and not auth.lower().startswith("bearer ") and " " not in auth.strip():
                # Raw token in Authorization (some API-key UIs).
                headers = [(k, v) for k, v in headers if k.decode().lower() != "authorization"]
                headers.append((b"authorization", f"Bearer {auth.strip()}".encode()))
                scope = dict(scope)
                scope["headers"] = headers
        await self.app(scope, receive, send)


class NormalizeMcpPathMiddleware:
    """Rewrite POST /mcp → /mcp/ in-process (no HTTP 307).

    Starlette Mount redirects /mcp → /mcp/ by default; some clients drop
    Authorization on that hop. Starlette 1.x no longer accepts a
    redirect-slashes kwarg on Starlette(), so we normalize the path here.
    """

    def __init__(self, app, mcp_path: str = "/mcp"):
        self.app = app
        self.mcp_path = (mcp_path or "/mcp").rstrip("/") or "/mcp"

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path") or ""
            if path == self.mcp_path:
                scope = dict(scope)
                scope["path"] = self.mcp_path + "/"
        await self.app(scope, receive, send)


def create_app() -> Starlette:
    mcp = _build_mcp()
    path = (os.environ.get("MCP_PATH") or "/mcp").rstrip("/") or "/mcp"
    mcp_app = mcp.http_app(
        path="/",
        transport="streamable-http",
        allowed_origins=[
            "https://chatgpt.com",
            "https://chat.openai.com",
            "https://platform.openai.com",
        ],
    )

    # CORS so browser-side ChatGPT connector probes can read responses.
    cors = Middleware(
        CORSMiddleware,
        allow_origins=[
            "https://chatgpt.com",
            "https://chat.openai.com",
            "https://platform.openai.com",
        ],
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Mcp-Session-Id",
            "X-Api-Key",
        ],
        expose_headers=["Mcp-Session-Id"],
        allow_credentials=False,
    )

    app = Starlette(
        routes=[
            Route("/healthz", healthz, methods=["GET"]),
            Route("/health", healthz, methods=["GET"]),
            Mount(path, app=mcp_app),
        ],
        middleware=[
            cors,
            Middleware(NormalizeMcpPathMiddleware, mcp_path=path),
            Middleware(ApiKeyHeaderMiddleware),
        ],
        lifespan=mcp_app.lifespan,
    )
    return app


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    host = os.environ.get("HOST", "0.0.0.0")
    app = create_app()
    uvicorn.run(app, host=host, port=port, proxy_headers=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    main()
