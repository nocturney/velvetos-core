#!/usr/bin/env python3
"""Validate local non-authoritative OTel/OpenInference observability evidence."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "packages" / "vfharness" / "observability" / "trace-policy.json"
RECEIPT = ROOT / "packages" / "vfharness" / "state" / "observability-phase2-2026-09-27.json"
REQS = ROOT / "tools" / "observability" / "requirements.txt"
VENDOR = ROOT / "tools" / "observability" / "python"
EXPECTED = {
    "opentelemetry-sdk": "1.45.0",
    "openinference-instrumentation": "0.1.66",
    "openinference-semantic-conventions": "0.1.39",
}

def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)

def parse_requirements() -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in REQS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        name, version = line.split("==", 1)
        rows[name] = version
    return rows

def validate_receipt() -> tuple[int, int]:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if policy.get("authority") is not False or policy.get("remote_exporters") != []:
        fail("telemetry policy must be local and non-authoritative")
    if receipt.get("authority") is not False or receipt.get("remote_exporters") != []:
        fail("trace receipt claims authority or remote export")
    if receipt.get("role") != "LOCAL_NON_AUTHORITATIVE_TELEMETRY":
        fail("trace role mismatch")
    if receipt.get("flow_status") != "PASS":
        fail("acceptance flow did not pass")
    if receipt.get("required_flow") != policy.get("required_flow"):
        fail("flow contract mismatch")
    spans = receipt.get("spans") or []
    if len(spans) != len(policy["required_flow"]) or receipt.get("span_count") != len(spans):
        fail("span count mismatch")
    by_name = {row.get("name"): row for row in spans}
    if set(by_name) != set(policy["required_flow"]):
        fail("required span set mismatch")
    trace_ids = {row.get("trace_id") for row in spans}
    if len(trace_ids) != 1 or None in trace_ids:
        fail("acceptance spans must share one trace")
    root = by_name["request"]
    if root.get("parent_span_id") is not None:
        fail("request span must be root")
    root_id = root.get("span_id")
    for name, row in by_name.items():
        if name != "request" and row.get("parent_span_id") != root_id:
            fail(f"{name}: span is not parented by request")
        attrs = row.get("attributes") or {}
        if attrs.get("velvetos.stage") != name:
            fail(f"{name}: stage attribute mismatch")
        if attrs.get("velvetos.status") != "PASS":
            fail(f"{name}: non-PASS stage")
    allowed = set(policy["allowed_attributes"])
    forbidden = tuple(x.casefold() for x in policy["forbidden_attribute_fragments"])
    for row in spans:
        for key, value in (row.get("attributes") or {}).items():
            if key not in allowed:
                fail(f"attribute not allowlisted: {key}")
            folded = key.casefold()
            if any(fragment in folded for fragment in forbidden):
                fail(f"sensitive attribute key: {key}")
            if isinstance(value, str) and len(value) > 160:
                fail(f"oversized attribute value: {key}")
    if by_name["approval"]["attributes"].get("velvetos.approval_required") is not False:
        fail("cost approval gate was not cleared by zero-cost preflight")
    if by_name["readback"]["attributes"].get("velvetos.readback_verified") is not True:
        fail("read-back verification missing")
    if by_name["result"]["attributes"].get("velvetos.incremental_cost_ils") != 0:
        fail("acceptance trace must report zero incremental recurring cost")
    return len(spans), len(trace_ids)

def validate_strict_install() -> None:
    if not VENDOR.is_dir():
        fail("local observability install missing")
    dist = {p.name.casefold() for p in VENDOR.glob("*.dist-info")}
    for package, version in EXPECTED.items():
        normalized = package.replace("-", "_").casefold()
        prefix = f"{normalized}-{version}.dist-info"
        if prefix not in dist:
            fail(f"installed distribution missing: {package}=={version}")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    for path in (POLICY, RECEIPT, REQS):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
    if parse_requirements() != EXPECTED:
        fail("observability dependency pins mismatch")
    spans, traces = validate_receipt()
    if args.strict:
        validate_strict_install()
    print(
        f"OK observability spans={spans} traces={traces} "
        f"strict_install={'PASS' if args.strict else 'NOT_REQUIRED'} local_only=YES authority=NO"
    )

if __name__ == "__main__":
    main()
