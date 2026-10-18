#!/usr/bin/env python3
"""Vendor-neutral Office v2 Phase 2 Golden Fixture validator/evaluator.

This runner never performs an external mutation. Effectful benchmark execution belongs
to a separately admitted adapter. The runner validates contracts, emits plans, and
evaluates generic adapter receipts against the fixture evidence/resource contract.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA = "velvetos.office-v2.golden-fixture.v0"
ADAPTER_SCHEMA = "velvetos.office-v2.fixture-adapter-receipt.v0"
POLICY = "PROVIDER_ADAPTER_REQUIRED_NO_DIRECT_RUNNER_MUTATION"
SIDE_EFFECTS = {"NONE", "READ", "REVERSIBLE_WRITE", "IRREVERSIBLE_WRITE"}
RESOURCE_FIELDS = {
    "wall_seconds", "cpu_peak_pct", "ram_peak_mb", "gpu_peak_pct", "vram_peak_mb",
    "storage_delta_mb", "network_mb", "external_cost", "recurring_cost", "operator_minutes",
}
REQUIRED = {
    "schema", "fixture_id", "status", "title", "capability_scope", "input_contract",
    "semantic_steps", "success_contract", "evidence_contract", "rollback_contract",
    "resource_capture", "external_effect_policy",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("document must be an object")
    return value


def validate(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    missing = sorted(REQUIRED - set(data))
    problems.extend("missing:" + key for key in missing)
    if data.get("schema") != SCHEMA:
        problems.append("schema_invalid")
    if data.get("status") != "CONTRACT_V0":
        problems.append("status_invalid")
    if data.get("external_effect_policy") != POLICY:
        problems.append("external_effect_policy_invalid")
    if not data.get("fixture_id"):
        problems.append("fixture_id_empty")
    if not data.get("capability_scope"):
        problems.append("capability_scope_empty")
    inputs = data.get("input_contract") or {}
    if not inputs.get("required"):
        problems.append("input_contract_required_empty")
    if inputs.get("vendor_specific_fields_forbidden") is not True:
        problems.append("vendor_specific_fields_not_forbidden")
    steps = data.get("semantic_steps") or []
    step_ids: set[str] = set()
    expected_evidence: set[str] = set()
    for step in steps:
        sid = step.get("step_id")
        if not sid or sid in step_ids:
            problems.append("step_id_invalid_or_duplicate")
        if sid:
            step_ids.add(sid)
        if not step.get("capability"):
            problems.append("step_capability_empty")
        if step.get("side_effect_class") not in SIDE_EFFECTS:
            problems.append("step_side_effect_invalid")
        ev = step.get("expected_evidence") or []
        if not ev:
            problems.append("step_evidence_empty")
        expected_evidence.update(str(x) for x in ev)
    if not steps:
        problems.append("semantic_steps_empty")
    declared = set((data.get("evidence_contract") or {}).get("required") or [])
    if not expected_evidence.issubset(declared):
        problems.append("evidence_contract_incomplete")
    resources = set(data.get("resource_capture") or [])
    if resources != RESOURCE_FIELDS:
        problems.append("resource_capture_mismatch")
    if not data.get("success_contract"):
        problems.append("success_contract_empty")
    if not data.get("rollback_contract"):
        problems.append("rollback_contract_empty")
    return sorted(set(problems))


def plan(data: dict[str, Any]) -> dict[str, Any]:
    problems = validate(data)
    if problems:
        return {"status": "FAIL", "problems": problems, "writes_performed": 0}
    steps = []
    for step in data["semantic_steps"]:
        steps.append({
            "step_id": step["step_id"],
            "capability": step["capability"],
            "side_effect_class": step["side_effect_class"],
            "adapter_required": step["side_effect_class"] in {"REVERSIBLE_WRITE", "IRREVERSIBLE_WRITE"},
            "expected_evidence": step["expected_evidence"],
        })
    return {
        "status": "PASS",
        "fixture_id": data["fixture_id"],
        "execution_boundary": POLICY,
        "steps": steps,
        "required_evidence": data["evidence_contract"]["required"],
        "required_resources": data["resource_capture"],
        "writes_performed": 0,
    }


def evaluate(data: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    problems = validate(data)
    if problems:
        return {"status": "FAIL", "problems": problems, "writes_performed": 0}
    rp: list[str] = []
    if receipt.get("schema") != ADAPTER_SCHEMA:
        rp.append("adapter_schema_invalid")
    if receipt.get("fixture_id") != data["fixture_id"]:
        rp.append("fixture_id_mismatch")
    if receipt.get("status") != "PASS":
        rp.append("adapter_status_not_pass")
    raw_evidence = receipt.get("evidence")
    if raw_evidence is not None and not isinstance(raw_evidence, dict):
        rp.append("evidence_must_be_object")
    evidence = raw_evidence if isinstance(raw_evidence, dict) else {}
    required_evidence = set(data["evidence_contract"]["required"])
    missing_ev = sorted(required_evidence - set(evidence))
    rp.extend("missing_evidence:" + key for key in missing_ev)
    # Model-identified false-success: a present key is not proof if its value is empty.
    for key in sorted(required_evidence & set(evidence)):
        value = evidence[key]
        if value is None or value is False or value == {} or value == [] or value == "":
            rp.append(f"invalid_evidence_value:{key}")
    resources = receipt.get("resources") or {}
    missing_res = sorted(set(data["resource_capture"]) - set(resources))
    rp.extend("missing_resource:" + key for key in missing_res)
    if receipt.get("direct_runner_mutation") is not False:
        rp.append("direct_runner_mutation_must_be_false")
    return {
        "status": "PASS" if not rp else "FAIL",
        "fixture_id": data["fixture_id"],
        "problems": rp,
        "adapter_id": receipt.get("adapter_id"),
        "run_id": receipt.get("run_id"),
        "writes_performed": 0,
    }


def self_test() -> dict[str, Any]:
    fixture = {
        "schema": SCHEMA,
        "fixture_id": "fixture-selftest",
        "status": "CONTRACT_V0",
        "title": "selftest",
        "capability_scope": ["fixture"],
        "input_contract": {"required": ["input"], "vendor_specific_fields_forbidden": True},
        "semantic_steps": [
            {"step_id": "read", "capability": "fixture.read", "side_effect_class": "READ", "expected_evidence": ["readback"]}
        ],
        "success_contract": ["readback exists"],
        "evidence_contract": {"required": ["readback"]},
        "rollback_contract": ["none required"],
        "resource_capture": sorted(RESOURCE_FIELDS),
        "external_effect_policy": POLICY,
    }
    good = validate(fixture)
    bad = validate({**fixture, "external_effect_policy": "DIRECT"})
    receipt = {
        "schema": ADAPTER_SCHEMA,
        "fixture_id": "fixture-selftest",
        "adapter_id": "fixture-adapter",
        "run_id": "run-selftest",
        "status": "PASS",
        "evidence": {"readback": {"ok": True}},
        "resources": {key: 0 for key in RESOURCE_FIELDS},
        "direct_runner_mutation": False,
    }
    evaluated = evaluate(fixture, receipt)
    # Required receipt evidence must contain a real value, not just a key.
    negative_none = evaluate(fixture, {**receipt, "evidence": {"readback": None}})
    negative_empty = evaluate(fixture, {**receipt, "evidence": {"readback": {}}})
    ok = (
        not good
        and "external_effect_policy_invalid" in bad
        and evaluated["status"] == "PASS"
        and negative_none["status"] == "FAIL"
        and negative_empty["status"] == "FAIL"
    )
    return {
        "status": "PASS" if ok else "FAIL",
        "good_problems": good,
        "negative_problems": bad,
        "evaluation": evaluated["status"],
        "writes_performed": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--validate")
    mode.add_argument("--plan")
    mode.add_argument("--execute")
    ap.add_argument("--adapter-receipt")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        if args.self_test:
            result = self_test()
        elif args.validate:
            data = load(Path(args.validate))
            problems = validate(data)
            result = {"status": "PASS" if not problems else "FAIL", "problems": problems, "fixture_id": data.get("fixture_id"), "writes_performed": 0}
        elif args.plan:
            result = plan(load(Path(args.plan)))
        else:
            if not args.adapter_receipt:
                result = {"status": "FAIL", "problems": ["adapter_receipt_required"], "writes_performed": 0}
            else:
                result = evaluate(load(Path(args.execute)), load(Path(args.adapter_receipt)))
    except Exception as exc:
        result = {"status": "FAIL", "problems": [str(exc)], "writes_performed": 0}

    print(json.dumps(result, ensure_ascii=False) if args.json else json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
