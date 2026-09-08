#!/usr/bin/env python3
"""VelvetOS remote Instagram MCP — Streamable HTTP wrapper around upstream.

Upstream package (canonical tools): adelaidasofia-instagram-mcp
  https://github.com/adelaidasofia/instagram-mcp

This file does NOT rewrite Graph API tools. It:
  1. mounts the upstream FastMCP server
  2. requires a VelvetOS bearer token (VELVET_INSTAGRAM_MCP_BEARER_TOKEN)
  3. serves Streamable HTTP at /mcp for Cursor Cloud / Team MCP

Env (values never logged):
  Required for HTTP mode:
    VELVET_INSTAGRAM_MCP_BEARER_TOKEN
  Required for live Meta Graph (same as upstream):
    INSTAGRAM_MCP_ACCESS_TOKEN
    INSTAGRAM_MCP_IG_USER_ID
  Optional:
    INSTAGRAM_MCP_APP_SECRET
  MUST stay unset/false:
    INSTAGRAM_MCP_DM_ENABLED

Bind (Cloud Run sets PORT):
  INSTAGRAM_MCP_HOST (default 0.0.0.0)
  PORT or INSTAGRAM_MCP_PORT (default 8080) — Cloud Run injects PORT
  INSTAGRAM_MCP_PATH (default /mcp)
"""
from __future__ import annotations

import hmac
import os
import sys


def _listen_port() -> int:
    """Cloud Run requires listening on $PORT; INSTAGRAM_MCP_PORT is local override."""
    raw = (os.environ.get("PORT") or os.environ.get("INSTAGRAM_MCP_PORT") or "8080").strip()
    try:
        return int(raw)
    except ValueError:
        print(f"REFUSE: invalid PORT/INSTAGRAM_MCP_PORT={raw!r}", file=sys.stderr)
        raise SystemExit(2) from None


def _require_bearer() -> str:
    token = (os.environ.get("VELVET_INSTAGRAM_MCP_BEARER_TOKEN") or "").strip()
    if not token or len(token) < 24:
        print(
            "REFUSE: VELVET_INSTAGRAM_MCP_BEARER_TOKEN missing or too short "
            "(need a dedicated MCP gate token, not the Meta Graph token).",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if token.startswith("EAA") or token.startswith("IGQV"):
        print(
            "REFUSE: VELVET_INSTAGRAM_MCP_BEARER_TOKEN looks like a Meta Graph token. "
            "Use a separate random bearer for the MCP gate.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return token


def _dm_guard() -> None:
    enabled = (os.environ.get("INSTAGRAM_MCP_DM_ENABLED") or "").strip().lower()
    if enabled in {"1", "true", "yes"}:
        print(
            "REFUSE: INSTAGRAM_MCP_DM_ENABLED must stay off for VelvetOS.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def build_server():
    from fastmcp import FastMCP
    from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
    from instagram_mcp.server import mcp as upstream

    bearer = _require_bearer()
    _dm_guard()

    auth = StaticTokenVerifier(
        tokens={
            bearer: {
                "client_id": "velvetos-cloud",
                "scopes": ["instagram"],
            }
        }
    )
    # Constant-time compare is handled by StaticTokenVerifier lookup; keep hmac
    # helper available for future custom validators.
    _ = hmac

    remote = FastMCP("instagram", auth=auth)
    # Mount without namespace so tool names stay healthcheck / publish_image / …
    remote.mount(upstream)
    return remote


def main() -> None:
    transport = (os.environ.get("INSTAGRAM_MCP_TRANSPORT") or "streamable-http").strip()
    if transport in {"stdio", "local"}:
        # Dev fallback: run upstream stdio directly (no remote auth gate).
        from instagram_mcp.server import run as upstream_run

        upstream_run()
        return

    host = (os.environ.get("INSTAGRAM_MCP_HOST") or "0.0.0.0").strip()
    port = _listen_port()
    path = (os.environ.get("INSTAGRAM_MCP_PATH") or "/mcp").strip() or "/mcp"
    if not path.startswith("/"):
        path = "/" + path

    remote = build_server()
    # Prefer streamable-http (MCP remote standard). "http" alias also accepted by FastMCP.
    if transport in {"http", "streamable-http", "streamable_http"}:
        remote.run(
            transport="streamable-http",
            host=host,
            port=port,
            path=path,
            show_banner=False,
        )
    elif transport == "sse":
        remote.run(transport="sse", host=host, port=port, path=path, show_banner=False)
    else:
        print(f"REFUSE: unknown INSTAGRAM_MCP_TRANSPORT={transport!r}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
