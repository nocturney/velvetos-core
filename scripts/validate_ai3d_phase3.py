#!/usr/bin/env python3
"""Regression checks for AI3D Phase 3 Engineering Contract protocol."""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ai3d_protocol as protocol  # noqa: E402

BASE = ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
FIXTURES = BASE / "fixtures" / "phase3"
CONTRACT = FIXTURES / "engineering-contract.synthetic-box.json"
REPORT = FIXTURES / "artifact-report.synthetic-intent.json"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    valid_contract, contract_ok = protocol.validate_contract(CONTRACT)
    assert contract_ok, valid_contract
    assert valid_contract["status"] == "PASS"
    assert valid_contract["readiness"]["manufacturing_release"] is True

    valid_report, report_ok = protocol.validate_report(REPORT, True)
    assert report_ok, valid_report
    assert valid_report["status"] == "PASS"

    with tempfile.TemporaryDirectory(prefix="ai3d-phase3-") as tmp:
        temp = Path(tmp)

        bad_contract = copy.deepcopy(load(CONTRACT))
        bad_contract["dimensions"][0]["source_type"] = "assumed"
        bad_contract["dimensions"][0]["evidence_refs"] = []
        bad_contract_path = temp / "bad-contract.json"
        write(bad_contract_path, bad_contract)
        blocked_contract, blocked_ok = protocol.validate_contract(bad_contract_path)
        assert not blocked_ok
        assert blocked_contract["status"] == "BLOCKED"
        assert any("critical" in item.lower() or "evidence" in item.lower() for item in blocked_contract["errors"])

        blocked_unknown = copy.deepcopy(load(CONTRACT))
        blocked_unknown["unknowns"] = [
            {
                "unknown_id": "U_CRITICAL_INTERFACE",
                "description": "Synthetic unresolved critical interface",
                "blocking": True,
                "resolution_required_before": "manufacturing_release",
            }
        ]
        blocked_unknown_path = temp / "blocked-unknown.json"
        write(blocked_unknown_path, blocked_unknown)
        readiness_payload, readiness_ok = protocol.validate_contract(blocked_unknown_path)
        assert readiness_ok, readiness_payload
        assert readiness_payload["readiness"]["geometry_build"] is True
        assert readiness_payload["readiness"]["manufacturing_release"] is False
        assert readiness_payload["readiness"]["slice"] is False

        bad_report = copy.deepcopy(load(REPORT))
        bad_report["outputs"][0]["sha256"] = "0" * 64
        bad_report_path = FIXTURES / "artifact-report.synthetic-tampered.tmp.json"
        try:
            write(bad_report_path, bad_report)
            tampered_payload, tampered_ok = protocol.validate_report(bad_report_path, True)
            assert not tampered_ok
            assert tampered_payload["status"] == "BLOCKED"
            assert any("sha256 mismatch" in item for item in tampered_payload["errors"])
        finally:
            bad_report_path.unlink(missing_ok=True)

    print(
        "validate_ai3d_phase3: PASS "
        "valid_contract=1 valid_report=1 critical_assumption_blocked=1 "
        "blocking_unknown_enforced=1 tampered_hash_blocked=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
