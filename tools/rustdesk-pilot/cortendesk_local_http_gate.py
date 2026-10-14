"""Explicit read-only localhost HTTP smoke gate for an isolated CortenDesk stage.

This NEVER starts a server/container, sends credentials, follows redirects,
invokes the remote desktop web client, reads RustDesk IDs, or accesses any
remote host. Only GET /login, /devices, /webclient on plan-pinned 127.0.0.1.
It is NOT a browser, iPhone, WebSocket, or remote-control acceptance test.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import http.client
import json
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

from cortendesk_staging_gate import StagingPlanError, validate_plan

SCHEMA = "velvetos.cortendesk.local_http_gate.v1"
ROUTES = ("/login", "/devices", "/webclient")
REDIRECT_CODES = frozenset((301, 302, 303, 307, 308))
DENY_CODES = frozenset((401, 403))
MAX_RESPONSE_BYTES = 8192


class LocalGateError(ValueError):
    pass


@dataclass(frozen=True)
class Response:
    status: int
    content_type: str = ""
    location: str = ""


def _read_local(port: int, path: str) -> Response:
    """Direct loopback socket, no ambient proxy, cookie jar or redirect."""
    if path not in ROUTES:
        raise LocalGateError("unexpected_probe_route")
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.request(
            "GET", path, body=None,
            headers={"Accept": "text/html", "Cache-Control": "no-store",
                     "User-Agent": "VelvetOS-Staging-ReadOnly/1"},
        )
        response = connection.getresponse()
        # Consume a bounded number of bytes without logging their contents.
        response.read(MAX_RESPONSE_BYTES)
        return Response(
            status=response.status,
            content_type=response.getheader("Content-Type", ""),
            location=response.getheader("Location", ""),
        )
    except (OSError, http.client.HTTPException) as exc:
        raise LocalGateError("localhost_not_reachable") from exc
    finally:
        connection.close()


def _protected(response: Response, port: int) -> str:
    """Require auth rejection or redirect to the local login route."""
    if response.status in DENY_CODES:
        return "protected"
    if response.status == 200:
        return "anonymous_page_exposed"
    if response.status not in REDIRECT_CODES:
        return "unexpected_status"
    try:
        parsed = urlsplit(response.location)
        if parsed.username or parsed.password or parsed.fragment:
            return "unexpected_redirect"
        # No redirect-follow: inspect the Location, never log or navigate it.
        if parsed.scheme or parsed.netloc:
            if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
                    or parsed.port != port):
                return "unexpected_redirect"
        if parsed.path not in ("/login", "/login/2fa"):
            return "unexpected_redirect"
    except ValueError:
        # Malformed redirect ports and authorities are not proof of auth.
        return "unexpected_redirect"
    return "protected"


def inspect(
    plan: dict,
    *,
    requester: Callable[[int, str], Response] = _read_local,
) -> dict:
    design = validate_plan(plan)
    if design["may_execute"] is not False:
        raise LocalGateError("previous_execution_denial_must_be_respected")
    if plan["bind_address"] != "127.0.0.1":
        raise LocalGateError("loopback_required")
    port = plan["host_ports"]["console_tcp"]
    report = {
        "schema": SCHEMA,
        "state": "LOCAL_HTTP_NOT_VERIFIED",
        "source_release": plan["source_release"],
        "target": "pinned_localhost_only",
        "login_route": "unknown",
        "anonymous_access": {"devices": "unknown", "webclient": "unknown"},
        "may_launch_container": False,
        "performed_mutation": False,
        "access_tokens_used": False,
        "mobile_safari_verified": False,
        "websocket_verified": False,
        "browser_remote_control_verified": False,
    }
    try:
        responses = {route: requester(port, route) for route in ROUTES}
    except LocalGateError as exc:
        if str(exc) == "localhost_not_reachable":
            report["state"] = "STAGING_NOT_REACHABLE"
            return report
        raise
    login = responses["/login"]
    report["login_route"] = ("present" if login.status == 200 and
                             "text/html" in login.content_type.lower()
                             else "unverified")
    report["anonymous_access"] = {
        "devices": _protected(responses["/devices"], port),
        "webclient": _protected(responses["/webclient"], port),
    }
    if (report["login_route"] == "present" and
            all(s == "protected" for s in report["anonymous_access"].values())):
        report["state"] = "LOCAL_HTTP_AUTH_SURFACE_PASS_NOT_MOBILE"
    else:
        report["state"] = "LOCAL_HTTP_AUTH_SURFACE_REJECTED"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="One-shot unauthenticated GET-only localhost CortenDesk route gate"
    )
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument(
        "--allow-local-staging-read", action="store_true",
        help="Explicit permission to read 3 anonymous routes on pinned loopback port",
    )
    args = parser.parse_args(argv)
    if not args.allow_local_staging_read:
        print(json.dumps({
            "schema": SCHEMA, "state": "BLOCKED_EXPLICIT_OPT_IN_REQUIRED",
            "performed_mutation": False, "may_launch_container": False,
        }, sort_keys=True))
        return 2
    try:
        if args.plan.stat().st_size > 32768:
            raise LocalGateError("plan_too_large")
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        report = inspect(plan)
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0 if report["state"] == "LOCAL_HTTP_AUTH_SURFACE_PASS_NOT_MOBILE" else 2
    except (LocalGateError, StagingPlanError, OSError, ValueError) as exc:
        reason = (str(exc) if isinstance(exc, (LocalGateError, StagingPlanError))
                  else "plan_or_probe_unavailable")
        print(json.dumps({
            "schema": SCHEMA, "state": "REJECTED", "reason": reason,
            "performed_mutation": False, "may_launch_container": False,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
