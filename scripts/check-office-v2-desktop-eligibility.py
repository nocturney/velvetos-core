#!/usr/bin/env python3
"""Offline #604 desktop provider-eligibility fixture, NOT a runtime provider.

No desktop API, network, account, VM, scheduler or external effect is invoked.
A simulated eligible result means only that a fixture passes preflight checks.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "docs/implementation/office-v2/phase2/desktop-runtime-eligibility-fixtures-v0.json"
MAX_BINDING_AGE_MS = 5000


def overlay(original: dict, updates: dict) -> dict:
    result = copy.deepcopy(original)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = overlay(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def inspect(record: dict, test_clock_ms: int) -> str:
    # Never use assert for security negatives; Python -O must not bypass gates.
    required = ("schema", "route", "host", "session", "app", "binding",
                "current_identity", "task", "scope", "lease", "effect_state", "postcondition")
    if any(k not in record for k in required):
        return "MALFORMED_CAPABILITY"
    if record["schema"] != "velvet.desktop.capability-request.v0":
        return "MALFORMED_CAPABILITY"
    scope, task = record["scope"], record["task"]
    if scope.get("authority") != "synthetic_only":
        return "AUTHORITY_NOT_SYNTHETIC"
    if task.get("data_class") != "synthetic":
        return "SYNTHETIC_DATA_ONLY"
    if record["route"] not in {"native_api", "named_accessibility", "visual_replay"} or (
        record["route"] not in scope.get("routes", [])
    ):
        return "ROUTE_UNDECLARED"
    if task.get("operation") not in scope.get("operations", []):
        return "OPERATION_UNDECLARED"
    if task.get("requested_effect") not in scope.get("effects", []):
        return "EFFECT_OUT_OF_SCOPE"
    if (record["session"].get("kind") == "system_session0" and
            record["route"] == "native_api"):
        return "HOST_SYSTEM_SESSION_FORBIDDEN"
    if (record["route"] in ("named_accessibility", "visual_replay") and
            record["session"].get("kind") != "interactive_user"):
        return "INTERACTIVE_USER_REQUIRED"
    if not record["session"].get("principal"):
        return "SESSION_PRINCIPAL_UNVERIFIED"
    if record["effect_state"] == "UNKNOWN":
        return "EFFECT_UNKNOWN_RECONCILE"
    if record["effect_state"] != "NOT_STARTED":
        return "EFFECT_NOT_FRESH"
    lease = record["lease"]
    if lease.get("granted") is not True:
        return "LEASE_NOT_GRANTED"
    if lease.get("epoch") != lease.get("observed_epoch"):
        return "LEASE_FENCED"
    if (lease.get("owner_task") != task.get("id") or
            lease.get("host_id") != record["host"].get("id") or
            lease.get("session_id") != record["session"].get("session_id")):
        return "LEASE_OWNER_DRIFT"
    binding, app, session = record["binding"], record["app"], record["session"]
    if (binding.get("host_id") != record["host"].get("id") or
            binding.get("session_id") != session.get("session_id")):
        return "SESSION_BINDING_DRIFT"
    if (binding.get("app_id") != app.get("id") or
            binding.get("app_version") != app.get("version")):
        return "APP_BINDING_MISMATCH"
    observed = binding.get("observed_at_ms")
    if not isinstance(observed, int) or observed > test_clock_ms:
        return "BINDING_CLOCK_INVALID"
    if test_clock_ms - observed > MAX_BINDING_AGE_MS:
        return "BINDING_STALE"
    if any(binding.get(field) != record["current_identity"].get(field)
           for field in ("pid", "start_nonce", "window_id")):
        return "PROCESS_WINDOW_IDENTITY_DRIFT"
    post = record["postcondition"]
    if (not post.get("kind") or not post.get("expected") or
            not post.get("independent_verifier")):
        return "POSTCONDITION_NOT_INDEPENDENT"
    return "ELIGIBLE_SIMULATION_ONLY"


def main() -> int:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if (data.get("classification") != "SYNTHETIC_LAB_ONLY" or
            data.get("owner_issue") != 604):
        raise SystemExit("unsafe fixture scope")
    seen: set[str] = set()
    fails = []
    for case in data["cases"]:
        cid = case["id"]
        if cid in seen:
            fails.append((cid, "duplicate id", case["expected"]))
            continue
        seen.add(cid)
        got = inspect(overlay(data["base_record"], case["overrides"]),
                      data["test_clock_ms"])
        if got != case["expected"]:
            fails.append((cid, got, case["expected"]))
        print(f"{'PASS' if got == case['expected'] else 'FAIL'} {cid}: {got}")
    print(json.dumps({
        "schema": "velvet.desktop.eligibility-lab-receipt.v0",
        "owner_issue": 604, "executed_cases": len(seen),
        "passed": len(seen)-len(fails), "failed": len(fails),
        "model_invoked": False, "desktop_invoked": False,
        "external_effects": False, "production_authority": False,
    }, sort_keys=True))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
