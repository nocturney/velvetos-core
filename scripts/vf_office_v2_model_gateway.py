#!/usr/bin/env python3
"""Office v2 Phase 3C vendor-neutral MODEL GATEWAY contract checks.

Offline; does not open sockets, invoke model APIs, inspect secrets, or alter
production authority. Receipt evaluation is structural and NEVER live proof.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
P3C = ROOT / "docs" / "implementation" / "office-v2" / "phase3c"
P2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"
CONTRACT_PATH = P3C / "model-gateway-contract-v0.json"
FIXTURE_PATH = P3C / "model-gateway-fixture-v0.json"
CONTRACT_SCHEMA = "velvetos.office-v2.phase3c-model-gateway-contract.v0"
FIXTURE_SCHEMA = "velvetos.office-v2.phase3c-model-gateway-fixture.v0"
RECEIPT_SCHEMA = "velvetos.office-v2.phase3c-model-gateway-adapter-receipt.v0"
TERMINALS = {"ROUTED", "DENIED", "FAILED", "UNKNOWN"}
REQUIRED_TELEMETRY = {
    "trace_id", "policy_decision_ref", "budget_decision_ref", "latency_ms",
    "token_input_count", "token_output_count", "cost_usd",
}
FORBIDDEN_EVIDENCE_KEYS = {
    "token", "password", "secret", "private_key", "api_key", "authorization",
    "credentials", "credential", "prompt", "completion", "messages",
    "raw_request", "raw_response", "access_token", "bearer",
}


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("JSON root is not an object")
    return data


def detect_secret_keys(value: Any, path: str = "root") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in FORBIDDEN_EVIDENCE_KEYS:
                found.append(path + "." + str(key))
            found += detect_secret_keys(nested, path + "." + str(key))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            found += detect_secret_keys(nested, path + "." + str(index))
    return found


def validate_contract(contract: dict[str, Any], fixture: dict[str, Any],
                      shortlist: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("schema") != CONTRACT_SCHEMA:
        errors.append("contract_schema_mismatch")
    if contract.get("status") != "CONTRACT_PREP_NO_LAB_ADMISSION":
        errors.append("contract_must_not_claim_lab_admission")
    for flag in ("production_authority_change", "production_writer_change",
                 "production_credentials_allowed", "real_provider_invocations_allowed_by_contract_runner"):
        if contract.get(flag) is not False:
            errors.append("contract_forbidden_boolean:" + flag)
    if fixture.get("schema") != FIXTURE_SCHEMA or fixture.get("fixture_id") != "model-gateway-isolated-13-case":
        errors.append("fixture_schema_or_id_invalid")
    for flag, expected in (
        ("candidate_agnostic", True), ("lab_only", True), ("production_credentials_used", False),
        ("real_provider_calls_performed", False), ("side_effects_performed", False),
    ):
        if fixture.get(flag) is not expected:
            errors.append("fixture_guard_invalid:" + flag)
    if fixture.get("request_payloads") != "SYNTHETIC_METADATA_ONLY":
        errors.append("fixture_must_be_synthetic_only")
    if contract.get("competitor_neutrality") != "COMPETITOR_NEUTRAL_ADMISSION_V1":
        errors.append("competitor_neutrality_required")
    lanes = [row for row in (shortlist.get("lanes") or []) if row.get("lane_id") == "model-routing"]
    if len(lanes) != 1:
        errors.append("model_routing_shortlist_missing_or_duplicate")
    else:
        lane = lanes[0]
        if contract.get("incumbent") != lane.get("incumbent"):
            errors.append("contract_incumbent_not_current_shortlist")
        if set(contract.get("active_challengers") or []) != set(lane.get("challengers") or []):
            errors.append("contract_challengers_not_current_shortlist")
    if len(set(contract.get("hard_gates") or [])) < 10:
        errors.append("hard_gates_incomplete")
    if not REQUIRED_TELEMETRY.issubset(set(fixture.get("required_telemetry") or [])):
        errors.append("required_telemetry_incomplete")
    cases = fixture.get("cases")
    if not isinstance(cases, list) or len(cases) != 13:
        errors.append("fixture_must_have_13_cases")
        cases = []
    ids = [case.get("case_id") for case in cases if isinstance(case, dict)]
    if any(not x or not isinstance(x, str) for x in ids) or len(set(ids)) != len(ids):
        errors.append("case_ids_invalid_or_duplicate")
    if set(ids) != set(fixture.get("required_case_ids") or []):
        errors.append("required_case_ids_mismatch")
    for case in cases:
        cid = str(case.get("case_id"))
        req = case.get("request") or {}
        exp = case.get("expected") or {}
        if not isinstance(req, dict) or req.get("tenant_ref") != "synthetic-office-a":
            errors.append(cid + ":non_synthetic_tenant")
        if not isinstance(req, dict) or req.get("budget_cap_usd") != 0.05:
            errors.append(cid + ":invalid_synthetic_budget")
        state = exp.get("terminal_state")
        if state not in TERMINALS:
            errors.append(cid + ":invalid_terminal_state")
        attempts = exp.get("min_attempts")
        if type(attempts) is not int or attempts < 0 or attempts != exp.get("max_attempts"):
            errors.append(cid + ":invalid_attempt_bounds")
        if type(exp.get("fallback_executed")) is not bool:
            errors.append(cid + ":fallback_flag_missing")
        if state in {"DENIED", "UNKNOWN"} and exp.get("fallback_executed") is not False:
            errors.append(cid + ":forbidden_fallback")
        if state == "DENIED" and attempts != 0:
            errors.append(cid + ":denial_would_call_provider")
        if state == "ROUTED" and exp.get("chosen_provider_locality") not in {"local", "cloud"}:
            errors.append(cid + ":invalid_route_locality")
        if state != "ROUTED" and exp.get("chosen_provider_locality") is not None:
            errors.append(cid + ":non_route_selects_provider")
        if exp.get("fallback_executed") is True and (type(attempts) is not int or attempts < 2):
            errors.append(cid + ":fallback_without_second_provider")
    errors += ["sensitive_key_in_fixture:" + k for k in detect_secret_keys(fixture)]
    return sorted(set(errors))


def evaluate_receipt(fixture: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if receipt.get("schema") != RECEIPT_SCHEMA:
        errors.append("adapter_receipt_schema_invalid")
    if receipt.get("fixture_id") != fixture.get("fixture_id"):
        errors.append("adapter_fixture_id_mismatch")
    if not receipt.get("candidate_id") or not receipt.get("run_id") or not receipt.get("adapter_id"):
        errors.append("adapter_identity_missing")
    if receipt.get("lab_only") is not True:
        errors.append("adapter_not_lab_only")
    for flag in ("production_credentials_used", "production_authority_change",
                 "production_writer_change", "external_mutation_performed"):
        if receipt.get(flag) is not False:
            errors.append("adapter_authority_violation:" + flag)
    errors.extend("sensitive_field:" + k for k in detect_secret_keys(receipt))
    rows = receipt.get("case_results")
    if not isinstance(rows, list):
        rows = []
        errors.append("case_results_not_list")
    by_id = {case["case_id"]: case for case in fixture["cases"]}
    actual_ids = [case.get("case_id") for case in rows if isinstance(case, dict)]
    if len(actual_ids) != len(rows) or len(set(actual_ids)) != len(actual_ids) or set(actual_ids) != set(by_id):
        errors.append("case_coverage_duplicate_missing_or_unexpected")
    for row in rows:
        if not isinstance(row, dict):
            errors.append("case_result_not_object")
            continue
        cid = row.get("case_id")
        expected_case = by_id.get(cid)
        if expected_case is None:
            continue
        exp = expected_case["expected"]
        if row.get("terminal_state") != exp["terminal_state"]:
            errors.append(str(cid) + ":unexpected_terminal_state")
        attempts = row.get("attempted_providers")
        if not isinstance(attempts, list):
            attempts = []
            errors.append(str(cid) + ":attempts_not_list")
        if not exp["min_attempts"] <= len(attempts) <= exp["max_attempts"]:
            errors.append(str(cid) + ":attempt_count_invalid")
        if row.get("fallback_executed") is not exp["fallback_executed"]:
            errors.append(str(cid) + ":fallback_policy_invalid")
        if row.get("correlation_id") != cid:
            errors.append(str(cid) + ":correlation_not_preserved")
        providers = []
        for item in attempts:
            if not isinstance(item, dict) or not isinstance(item.get("provider_id"), str) or not item.get("provider_id"):
                errors.append(str(cid) + ":attempt_invalid")
                continue
            if item.get("locality") not in {"local", "cloud"}:
                errors.append(str(cid) + ":attempt_locality_invalid")
            providers.append(item["provider_id"])
        if len(providers) != len(set(providers)):
            errors.append(str(cid) + ":reused_provider_for_fallback")
        chosen = row.get("chosen_provider")
        if exp["terminal_state"] == "ROUTED":
            if not isinstance(chosen, dict) or chosen.get("provider_id") not in providers:
                errors.append(str(cid) + ":route_provider_not_attempted")
            elif chosen.get("locality") != exp["chosen_provider_locality"]:
                errors.append(str(cid) + ":route_locality_invalid")
            if expected_case["request"]["provider_preference"] in {"local", "cloud"}:
                if chosen and chosen.get("locality") != expected_case["request"]["provider_preference"]:
                    errors.append(str(cid) + ":preference_mismatch")
        elif chosen is not None:
            errors.append(str(cid) + ":terminal_cannot_choose_provider")
        if exp["terminal_state"] in {"DENIED", "UNKNOWN"} and row.get("fallback_executed"):
            errors.append(str(cid) + ":fail_closed_fallback_violation")
        telemetry = row.get("telemetry")
        if not isinstance(telemetry, dict):
            errors.append(str(cid) + ":telemetry_missing")
            continue
        for key in REQUIRED_TELEMETRY:
            val = telemetry.get(key)
            if key not in telemetry:
                errors.append(str(cid) + ":missing_telemetry:" + key)
            elif val is None and not (telemetry.get("unknown_metric_reasons") or {}).get(key):
                errors.append(str(cid) + ":unknown_metric_missing_reason:" + key)
            elif key in {"trace_id", "policy_decision_ref", "budget_decision_ref"} and not isinstance(val, str):
                errors.append(str(cid) + ":invalid_telemetry_ref:" + key)
            elif key in {"latency_ms", "token_input_count", "token_output_count", "cost_usd"} and val is not None and (type(val) not in (int, float) or val < 0):
                errors.append(str(cid) + ":invalid_numeric_telemetry:" + key)
        if exp["terminal_state"] == "DENIED" and telemetry.get("cost_usd") not in (0, None):
            errors.append(str(cid) + ":denied_call_billed")
    return {
        "status": "FAIL" if errors else "CONTRACT_COMPATIBLE_UNVERIFIED",
        "fixture_id": fixture["fixture_id"],
        "cases_checked": len(rows),
        "problems": sorted(set(errors)),
        "real_provider_calls_by_runner": 0,
        "lab_runtime_proven": False,
        "production_promotion_allowed": False,
    }


def selftest(contract: dict[str, Any], fixture: dict[str, Any], shortlist: dict[str, Any]) -> dict[str, Any]:
    problems = validate_contract(contract, fixture, shortlist)
    if problems:
        return {"status": "FAIL", "problems": problems}
    receipt: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA, "fixture_id": fixture["fixture_id"],
        "candidate_id": "selftest-synthetic-adapter", "adapter_id": "selftest-offline",
        "run_id": "offline-selftest", "lab_only": True,
        "production_credentials_used": False, "production_authority_change": False,
        "production_writer_change": False, "external_mutation_performed": False,
        "case_results": [],
    }
    for case in fixture["cases"]:
        exp = case["expected"]
        attempts = [
            {"provider_id": "synthetic-provider-" + str(i + 1),
             "locality": exp["chosen_provider_locality"] if i == exp["min_attempts"] - 1 and exp["chosen_provider_locality"] else "cloud"}
            for i in range(exp["min_attempts"])
        ]
        chosen = attempts[-1] if exp["terminal_state"] == "ROUTED" else None
        receipt["case_results"].append({
            "case_id": case["case_id"], "correlation_id": case["case_id"],
            "terminal_state": exp["terminal_state"], "attempted_providers": attempts,
            "fallback_executed": exp["fallback_executed"], "chosen_provider": chosen,
            "telemetry": {
                "trace_id": "synthetic-trace", "policy_decision_ref": "synthetic-policy",
                "budget_decision_ref": "synthetic-budget", "latency_ms": 1,
                "token_input_count": 0, "token_output_count": 0, "cost_usd": 0,
            },
        })
    good = evaluate_receipt(fixture, receipt)
    if good["status"] != "CONTRACT_COMPATIBLE_UNVERIFIED" or good["lab_runtime_proven"] or good["production_promotion_allowed"]:
        problems.append("good_synthetic_contract_not_accepted_with_no_runtime_claim")
    for name, edit in (
        ("policy_deny_fallback", lambda d: d["case_results"][3].update(fallback_executed=True)),
        ("unknown_outcome_retry", lambda d: d["case_results"][11].update(fallback_executed=True)),
        ("secret_exposure", lambda d: d.update(api_key="synthetic-invalid-secret-value")),
        ("missing_telemetry", lambda d: d["case_results"][0]["telemetry"].pop("trace_id")),
        ("changed_fixture", lambda d: d.update(fixture_id="wrong")),
        ("duplicate_case", lambda d: d["case_results"].append(copy.deepcopy(d["case_results"][0]))),
        ("authority_expansion", lambda d: d.update(production_writer_change=True)),
    ):
        bad = copy.deepcopy(receipt)
        edit(bad)
        if evaluate_receipt(fixture, bad)["status"] != "FAIL":
            problems.append("negative_control_not_rejected:" + name)
    return {
        "status": "FAIL" if problems else "PASS", "cases": len(fixture["cases"]),
        "negative_controls": 7, "runtime_proven": False,
        "production_promotion_allowed": False, "problems": problems,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("validate", "plan", "evaluate", "selftest"))
    ap.add_argument("--receipt", type=Path)
    opts = ap.parse_args()
    try:
        contract = load(CONTRACT_PATH)
        fixture = load(FIXTURE_PATH)
        shortlist = load(P2 / "p0-shortlists-v0.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("FAIL model-gateway input: " + str(exc), file=sys.stderr)
        return 1
    problems = validate_contract(contract, fixture, shortlist)
    if problems:
        print(json.dumps({"status": "FAIL", "problems": problems}, indent=2))
        return 1
    if opts.mode == "validate":
        value = {"status": "PASS", "cases": len(fixture["cases"]), "runtime_proven": False}
    elif opts.mode == "plan":
        value = {
            "status": "PLAN_ONLY", "fixture_id": fixture["fixture_id"],
            "candidate_ids": [contract["incumbent"]] + contract["active_challengers"],
            "case_ids": fixture["required_case_ids"],
            "real_provider_calls": 0, "production_promotion_allowed": False,
        }
    elif opts.mode == "selftest":
        value = selftest(contract, fixture, shortlist)
    else:
        if not opts.receipt:
            print("FAIL --receipt is required for evaluate", file=sys.stderr)
            return 2
        try:
            value = evaluate_receipt(fixture, load(opts.receipt))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print("FAIL receipt could not be read: " + type(exc).__name__, file=sys.stderr)
            return 1
    print(json.dumps(value, indent=2, sort_keys=True))
    return 1 if value.get("status") == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
