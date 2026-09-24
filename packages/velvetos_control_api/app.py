"""stdlib HTTP server for VelvetOS Control API.

No wildcard CORS (Site proxies server-side).
Body caps, method checks, safe JSON, normalized errors, no stack traces.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from velvetos_control_api import SCHEMA, SERVICE_NAME, __version__
from velvetos_control_api.actions import execute_action
from velvetos_control_api.auth import assert_isolation, authorize, configured_token
from velvetos_control_api.contributions.capabilities import normalize_all_capabilities
from velvetos_control_api.errors import (
    BODY_TOO_LARGE,
    ControlApiError,
    INTERNAL,
    INVALID_JSON,
    METHOD_NOT_ALLOWED,
    NOT_FOUND,
    error_body,
    sanitize_public,
)
from velvetos_control_api.registry import repo_root
from velvetos_control_api.schema import MAX_BODY_BYTES, now_iso
from velvetos_control_api.search import decode_query_param, search
from velvetos_control_api.snapshot import build_snapshot

# Routes: method -> path -> needs_auth
ROUTES = {
    ("GET", "/health"): False,
    ("GET", "/v1/snapshot"): True,
    ("GET", "/v1/search"): True,
    ("GET", "/v1/capabilities"): True,
    ("POST", "/v1/actions"): True,
}


class ControlApiHandler(BaseHTTPRequestHandler):
    server_version = f"{SERVICE_NAME}/{__version__}"
    root = None  # set on server

    def log_message(self, fmt: str, *args: Any) -> None:
        # Never log Authorization headers or tokens
        msg = fmt % args
        sys.stderr.write("%s - %s\n" % (self.address_string(), sanitize_public(msg)))

    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        # Explicitly no Access-Control-Allow-Origin wildcard
        self.end_headers()
        self.wfile.write(raw)

    def _error(self, status: int, code: str, message: str, details: dict | None = None) -> None:
        self._send_json(status, error_body(code, message, details=details))

    def _read_body(self) -> bytes:
        cl = self.headers.get("Content-Length")
        if cl is None or not str(cl).strip():
            return b""
        try:
            length = int(str(cl).strip())
        except ValueError:
            raise ControlApiError(INVALID_JSON, "invalid Content-Length", status=400)
        if length < 0:
            raise ControlApiError(INVALID_JSON, "invalid Content-Length", status=400)
        if length > MAX_BODY_BYTES:
            raise ControlApiError(BODY_TOO_LARGE, "request body too large", status=413)
        return self.rfile.read(length)

    def _dispatch(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        # Normalize /health/ → /health
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        method = self.command.upper()
        key = (method, path)

        # Method validation for known paths with wrong method
        known_paths = {p for _, p in ROUTES}
        if path in known_paths and key not in ROUTES:
            allow = sorted({m for m, p in ROUTES if p == path})
            self.send_header_allow = allow  # type: ignore[attr-defined]
            raise ControlApiError(
                METHOD_NOT_ALLOWED,
                f"method {method} not allowed",
                status=405,
                details={"allow": allow},
            )
        if key not in ROUTES:
            raise ControlApiError(NOT_FOUND, "not found", status=404)

        needs_auth = ROUTES[key]
        if needs_auth:
            authorize(self.headers)

        root = self.root or repo_root()

        if key == ("GET", "/health"):
            self._handle_health(root)
            return
        if key == ("GET", "/v1/snapshot"):
            snap = build_snapshot(root=root)
            self._send_json(200, snap)
            return
        if key == ("GET", "/v1/capabilities"):
            caps = normalize_all_capabilities(root)
            self._send_json(
                200,
                {
                    "schema": SCHEMA,
                    "generatedAt": now_iso(),
                    "capabilities": caps,
                },
            )
            return
        if key == ("GET", "/v1/search"):
            qs = parse_qs(parsed.query, keep_blank_values=True)
            q = decode_query_param((qs.get("q") or [""])[0])
            result = search(q, root=root)
            self._send_json(200, result)
            return
        if key == ("POST", "/v1/actions"):
            raw = self._read_body()
            if not raw:
                raise ControlApiError(INVALID_JSON, "JSON body required", status=400)
            try:
                body = json.loads(raw.decode("utf-8"))
            except Exception:
                raise ControlApiError(INVALID_JSON, "invalid JSON body", status=400)
            result = execute_action(body, root=root)
            status = int(result.pop("_httpStatus", 200))
            self._send_json(status, result)
            return

        raise ControlApiError(NOT_FOUND, "not found", status=404)

    def _handle_health(self, root) -> None:
        """Service liveness — does NOT claim all VelvetOS integrations healthy."""
        token_ok = bool(configured_token())
        try:
            snap = None
            velvetos = "unknown"
            # Cheap signal without full auth path: control-plane file presence
            plane = root / "office" / "control-plane.json"
            if not plane.is_file():
                velvetos = "degraded"
            else:
                # Use jobs status only (cheap) for degraded signal
                from velvetos_control_api.contributions.jobs import JobsContribution
                from velvetos_control_api.registry import ProjectContext

                jobs = JobsContribution().project(ProjectContext(root=root)).get("jobs") or {}
                if jobs.get("state") == "ready":
                    velvetos = "ok"
                elif jobs.get("state") in {"needs_sync", "conflict", "unavailable"}:
                    velvetos = "degraded"
                else:
                    velvetos = "unknown"
        except Exception:
            velvetos = "unknown"

        self._send_json(
            200,
            {
                "service": "ready",
                "velvetos": velvetos,
                "name": SERVICE_NAME,
                "version": __version__,
                "schema": SCHEMA,
                "authConfigured": token_ok,
                "note": "service=ready means the HTTP process is up — not that all integrations are healthy",
            },
        )

    def do_GET(self) -> None:  # noqa: N802
        self._safe_dispatch()

    def do_POST(self) -> None:  # noqa: N802
        self._safe_dispatch()

    def do_PUT(self) -> None:  # noqa: N802
        self._safe_dispatch()

    def do_DELETE(self) -> None:  # noqa: N802
        self._safe_dispatch()

    def do_PATCH(self) -> None:  # noqa: N802
        self._safe_dispatch()

    def do_OPTIONS(self) -> None:  # noqa: N802
        # No CORS — refuse preflight expansion
        self._error(404, NOT_FOUND, "not found")

    def _safe_dispatch(self) -> None:
        try:
            self._dispatch()
        except ControlApiError as exc:
            if exc.status == 405:
                allow = (exc.details or {}).get("allow") or []
                self.send_response(405)
                if allow:
                    self.send_header("Allow", ", ".join(allow))
                raw = json.dumps(
                    error_body(exc.code, exc.message, details=exc.details),
                    ensure_ascii=False,
                ).encode("utf-8")
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            self._error(exc.status, exc.code, exc.message, exc.details)
        except Exception:
            # Never send stack traces to clients
            traceback.print_exc(file=sys.stderr)
            self._error(500, INTERNAL, "internal error")


def create_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    *,
    root=None,
    check_isolation: bool = True,
) -> ThreadingHTTPServer:
    if check_isolation:
        assert_isolation()
    handler = ControlApiHandler
    handler.root = root or repo_root()
    return ThreadingHTTPServer((host, port), handler)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    if "--port" in argv:
        i = argv.index("--port")
        port = int(argv[i + 1])
    server = create_server(host, port, check_isolation=("--skip-isolation" not in argv))
    print(
        f"{SERVICE_NAME} listening on {host}:{port} schema={SCHEMA} "
        f"authConfigured={bool(configured_token())}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutting down", flush=True)
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
