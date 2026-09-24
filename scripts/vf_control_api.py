#!/usr/bin/env python3
"""VelvetOS Control API CLI — local projection dumps (no send, no network).

  python3 scripts/vf_control_api.py snapshot|capabilities|search|health|selftest
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"
if str(PACKAGES) not in sys.path:
    sys.path.insert(0, str(PACKAGES))


def cmd_snapshot(_args: argparse.Namespace) -> int:
    from velvetos_control_api.snapshot import build_snapshot

    print(json.dumps(build_snapshot(root=ROOT), ensure_ascii=False, indent=2))
    return 0


def cmd_capabilities(_args: argparse.Namespace) -> int:
    from velvetos_control_api.contributions.capabilities import normalize_all_capabilities

    caps = normalize_all_capabilities(ROOT)
    print(json.dumps({"count": len(caps), "capabilities": caps}, ensure_ascii=False, indent=2))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    from velvetos_control_api.search import search

    print(json.dumps(search(args.q, root=ROOT), ensure_ascii=False, indent=2))
    return 0


def cmd_health(_args: argparse.Namespace) -> int:
    from velvetos_control_api import SCHEMA, SERVICE_NAME, __version__
    from velvetos_control_api.auth import configured_token
    from velvetos_control_api.contributions.jobs import JobsContribution
    from velvetos_control_api.registry import ProjectContext

    jobs = JobsContribution().project(ProjectContext(root=ROOT)).get("jobs") or {}
    velvetos = "ok" if jobs.get("state") == "ready" else "degraded"
    print(
        json.dumps(
            {
                "service": "ready",
                "velvetos": velvetos,
                "name": SERVICE_NAME,
                "version": __version__,
                "schema": SCHEMA,
                "authConfigured": bool(configured_token()),
            },
            indent=2,
        )
    )
    return 0


def cmd_selftest(_args: argparse.Namespace) -> int:
    """Non-mutating behavioral checks — used by sensor too."""
    from velvetos_control_api.actions import execute_action, idempotent_equal
    from velvetos_control_api.auth import authorize
    from velvetos_control_api.errors import ControlApiError
    from velvetos_control_api.schema import SCHEMA
    from velvetos_control_api.search import validate_destination
    from velvetos_control_api.snapshot import build_snapshot

    errors: list[str] = []
    snap = build_snapshot(root=ROOT)
    if snap.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    jobs = (snap.get("collections") or {}).get("jobs") or {}
    # Unavailable domains must have items=null
    for name in ("production", "content", "files", "agents", "models"):
        col = (snap.get("collections") or {}).get(name) or {}
        if col.get("state") == "unavailable" and col.get("items") is not None:
            errors.append(f"{name} unavailable but items is not null")
        if col.get("state") == "unavailable" and col.get("count") is not None:
            errors.append(f"{name} unavailable but count is not null")
    # Jobs: if not ready, must not look like verified empty
    if jobs.get("state") not in {"ready", "needs_sync", "conflict", "unavailable", "unknown"}:
        errors.append(f"unexpected jobs state {jobs.get('state')}")
    if jobs.get("state") != "ready" and jobs.get("items") == []:
        errors.append("non-ready jobs must not use [] items")

    # Auth: anonymous denied when token set
    os.environ["VELVETOS_CONTROL_API_TOKEN"] = "test-token-selftest-only"
    try:
        authorize({})
        errors.append("anonymous authorize should fail")
    except ControlApiError as e:
        if e.status != 401:
            errors.append(f"expected 401 got {e.status}")
    try:
        authorize({"Authorization": "Bearer wrong"})
        errors.append("bad token should fail")
    except ControlApiError:
        pass
    authorize({"Authorization": "Bearer test-token-selftest-only"})

    # Actions fail-closed
    a1 = execute_action(
        {
            "actionId": "shell.exec",
            "objectId": "x",
            "confirmation": "yes",
            "idempotencyKey": "idem-selftest-0001",
        },
        root=ROOT,
    )
    if a1.get("error", {}).get("code") not in {"CAPABILITY_DENIED", "UNKNOWN_ACTION"}:
        errors.append(f"shell.exec should deny, got {a1}")
    a2 = execute_action(
        {
            "actionId": "shell.exec",
            "objectId": "x",
            "confirmation": "yes",
            "idempotencyKey": "idem-selftest-0001",
        },
        root=ROOT,
    )
    if not idempotent_equal(a1, a2):
        errors.append("idempotency receipt mismatch")

    unknown = execute_action(
        {
            "actionId": "totally.unknown.action",
            "idempotencyKey": "idem-selftest-0002",
        },
        root=ROOT,
    )
    if unknown.get("error", {}).get("code") != "UNKNOWN_ACTION":
        errors.append("unknown action must be UNKNOWN_ACTION")

    path_attack = execute_action(
        {
            "actionId": "gmail.read",
            "objectId": "../../../etc/passwd",
            "idempotencyKey": "idem-selftest-0003",
        },
        root=ROOT,
    )
    if path_attack.get("ok") is not False:
        errors.append("path injection must fail")

    if validate_destination("https://evil.example/x"):
        errors.append("url destination must be invalid")
    if validate_destination("/jobs/../etc"):
        errors.append("dotdot destination must be invalid")
    if not validate_destination("/jobs/VF-20260901-001"):
        errors.append("valid job destination rejected")

    # Secret leakage: snapshot must not contain the test token
    blob = json.dumps(snap)
    if "test-token-selftest-only" in blob:
        errors.append("token leaked into snapshot")

    if errors:
        print("FAIL selftest: " + "; ".join(errors))
        return 1
    print("OK control-api selftest non-mutating")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="VelvetOS Control API CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("snapshot")
    sub.add_parser("capabilities")
    sub.add_parser("health")
    sp = sub.add_parser("search")
    sp.add_argument("--q", required=True)
    sub.add_parser("selftest")
    args = p.parse_args()
    return {
        "snapshot": cmd_snapshot,
        "capabilities": cmd_capabilities,
        "search": cmd_search,
        "health": cmd_health,
        "selftest": cmd_selftest,
    }[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
