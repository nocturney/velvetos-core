#!/usr/bin/env python3
"""Offline #604 desktop provider-eligibility fixture, NOT a runtime provider.

No desktop API, network, account, VM, scheduler or external effect is invoked.
A simulated eligible result means only that a fixture passes preflight checks.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

FIXTURE = Path(__file__).resolve().with_name("desktop-runtime-eligibility-fixtures-v0.json")
MAX_BINDING_AGE_MS = 5000


def overlay(original: dict, updates: dict) -> dict:
    result = copy.deepcopy(original)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = overlay(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def nonblank(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def well_formed_choices(value: object) -> bool:
    """Fixture declarations are JSON arrays, never substring-search strings."""
    return (type(value) is list and bool(value) and
            all(nonblank(item) for item in value))


def inspect(record: dict, test_clock_ms: int) -> str:
    """Pure synthetic preflight; never grants or authenticates a real Core lease.

    Reject malformed data deterministically before comparing identities.
    Avoid assertions so -O cannot remove any denial path.
    """
    required = ("schema", "route", "host", "session", "app", "binding",
                "current_identity", "task", "scope", "lease", "effect_state",
                "postcondition")
    nested = ("host", "session", "app", "binding", "current_identity", "task",
              "scope", "lease", "postcondition")
    if (type(record) is not dict or type(test_clock_ms) is not int or
            test_clock_ms <= 0 or any(k not in record for k in required) or
            any(type(record[k]) is not dict for k in nested)):
        return "MALFORMED_CAPABILITY"
    if record["schema"] != "velvet.desktop.capability-request.v0":
        return "MALFORMED_CAPABILITY"
    scope, task = record["scope"], record["task"]
    if not all(well_formed_choices(scope.get(k))
               for k in ("routes", "operations", "effects")):
        return "MALFORMED_CAPABILITY"
    if scope.get("authority") != "synthetic_only":
        return "AUTHORITY_NOT_SYNTHETIC"
    if task.get("data_class") != "synthetic":
        return "SYNTHETIC_DATA_ONLY"

    route = record["route"]
    if (not nonblank(route) or
            route not in ("native_api", "named_accessibility", "visual_replay") or
            route not in scope["routes"]):
        return "ROUTE_UNDECLARED"
    if not nonblank(task.get("operation")) or task["operation"] not in scope["operations"]:
        return "OPERATION_UNDECLARED"
    if (not nonblank(task.get("requested_effect")) or
            task["requested_effect"] not in scope["effects"]):
        return "EFFECT_OUT_OF_SCOPE"

    session = record["session"]
    kind = session.get("kind")
    if kind not in ("interactive_user", "isolated_headless", "system_session0"):
        return "SESSION_KIND_UNVERIFIED"
    if kind == "system_session0" and route == "native_api":
        return "HOST_SYSTEM_SESSION_FORBIDDEN"
    if route in ("named_accessibility", "visual_replay") and kind != "interactive_user":
        return "INTERACTIVE_USER_REQUIRED"
    if not nonblank(session.get("principal")):
        return "SESSION_PRINCIPAL_UNVERIFIED"

    host, app = record["host"], record["app"]
    if (not nonblank(host.get("id")) or
            host.get("os") not in ("windows", "macos", "linux") or
            not nonblank(session.get("session_id"))):
        return "HOST_SESSION_IDENTITY_UNVERIFIED"
    if not nonblank(app.get("id")) or not nonblank(app.get("version")):
        return "APP_IDENTITY_UNVERIFIED"
    if not nonblank(task.get("id")):
        return "TASK_ID_UNVERIFIED"

    if record["effect_state"] == "UNKNOWN":
        return "EFFECT_UNKNOWN_RECONCILE"
    if record["effect_state"] != "NOT_STARTED":
        return "EFFECT_NOT_FRESH"

    lease = record["lease"]
    if lease.get("granted") is not True:
        return "LEASE_NOT_GRANTED"
    epoch, observed_epoch = lease.get("epoch"), lease.get("observed_epoch")
    if (type(epoch) is not int or epoch <= 0 or
            type(observed_epoch) is not int or observed_epoch <= 0):
        return "LEASE_EPOCH_INVALID"
    if epoch != observed_epoch:
        return "LEASE_FENCED"
    if (lease.get("owner_task") != task["id"] or
            lease.get("host_id") != host["id"] or
            lease.get("session_id") != session["session_id"]):
        return "LEASE_OWNER_DRIFT"

    binding = record["binding"]
    if (binding.get("host_id") != host["id"] or
            binding.get("session_id") != session["session_id"]):
        return "SESSION_BINDING_DRIFT"
    if (binding.get("app_id") != app["id"] or
            binding.get("app_version") != app["version"]):
        return "APP_BINDING_MISMATCH"
    observed = binding.get("observed_at_ms")
    if (type(observed) is not int or observed < 0 or
            observed > test_clock_ms):
        return "BINDING_CLOCK_INVALID"
    if test_clock_ms - observed > MAX_BINDING_AGE_MS:
        return "BINDING_STALE"

    identity = record["current_identity"]
    for side in (binding, identity):
        if (type(side.get("pid")) is not int or side["pid"] <= 0 or
                not nonblank(side.get("start_nonce")) or
                not nonblank(side.get("window_id"))):
            return "PROCESS_WINDOW_IDENTITY_UNVERIFIED"
    if any(binding.get(field) != identity.get(field)
           for field in ("pid", "start_nonce", "window_id")):
        return "PROCESS_WINDOW_IDENTITY_DRIFT"

    post = record["postcondition"]
    if not all(nonblank(post.get(k))
               for k in ("kind", "expected", "independent_verifier")):
        return "POSTCONDITION_NOT_INDEPENDENT"
    return "ELIGIBLE_SIMULATION_ONLY"


def evaluate(data: dict, *, quiet: bool = False) -> tuple[list[tuple[str, str, str]], dict]:
    """Run every case. A repeated id fails closed and does not reduce the pass total.

    ``passed`` counts only cases whose inspect result equals ``expected``.
    A duplicate is an extra executed failure with reason ``DUPLICATE_CASE_ID``
    and is not inserted into the seen set. ``passed + failed == executed_cases``.
    """
    if (data.get("classification") != "SYNTHETIC_LAB_ONLY" or
            data.get("owner_issue") != 604):
        raise SystemExit("unsafe fixture scope")
    seen: set[str] = set()
    fails: list[tuple[str, str, str]] = []
    passed = 0
    executed = 0
    for case in data["cases"]:
        executed += 1
        cid = case["id"]
        expected = case["expected"]
        if cid in seen:
            fails.append((cid, "DUPLICATE_CASE_ID", expected))
            if not quiet:
                print(f"FAIL {cid}: DUPLICATE_CASE_ID")
            continue
        seen.add(cid)
        got = inspect(overlay(data["base_record"], case["overrides"]),
                      data["test_clock_ms"])
        if got == expected:
            passed += 1
        else:
            fails.append((cid, got, expected))
        if not quiet:
            print(f"{'PASS' if got == expected else 'FAIL'} {cid}: {got}")
    failed = len(fails)
    if passed + failed != executed:
        raise SystemExit("receipt accounting mismatch")
    receipt = {
        "schema": "velvet.desktop.eligibility-lab-receipt.v0",
        "owner_issue": 604,
        "executed_cases": executed,
        "passed": passed,
        "failed": failed,
        "model_invoked": False,
        "desktop_invoked": False,
        "external_effects": False,
        "production_authority": False,
    }
    return fails, receipt


def main() -> int:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    fails, receipt = evaluate(data)
    print(json.dumps(receipt, sort_keys=True))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
