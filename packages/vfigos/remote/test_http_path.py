"""Unit tests for MCP path normalization (no HTTP 307)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from http_server import NormalizeMcpPathMiddleware


class NormalizeMcpPathTests(unittest.IsolatedAsyncioTestCase):
    async def test_rewrites_exact_mcp_path(self):
        seen = {}

        async def inner(scope, receive, send):
            seen["path"] = scope["path"]

        app = NormalizeMcpPathMiddleware(inner, mcp_path="/mcp")
        await app({"type": "http", "path": "/mcp"}, MagicMock(), MagicMock())
        self.assertEqual(seen["path"], "/mcp/")

    async def test_leaves_trailing_slash(self):
        seen = {}

        async def inner(scope, receive, send):
            seen["path"] = scope["path"]

        app = NormalizeMcpPathMiddleware(inner, mcp_path="/mcp")
        await app({"type": "http", "path": "/mcp/"}, MagicMock(), MagicMock())
        self.assertEqual(seen["path"], "/mcp/")

    async def test_leaves_other_paths(self):
        seen = {}

        async def inner(scope, receive, send):
            seen["path"] = scope["path"]

        app = NormalizeMcpPathMiddleware(inner, mcp_path="/mcp")
        await app({"type": "http", "path": "/health"}, MagicMock(), MagicMock())
        self.assertEqual(seen["path"], "/health")

    def test_create_app_does_not_pass_redirect_slashes_kwarg(self):
        import pathlib
        import re

        src = pathlib.Path(__file__).with_name("http_server.py").read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(r"Starlette\([^)]*redirect_slashes\s*=", src, re.S),
            "Do not pass redirect_slashes into Starlette() — crashes on Starlette 1.x",
        )


if __name__ == "__main__":
    unittest.main()
