#!/usr/bin/env python3
"""Validate AI 3D Modeling & Engineering Core Phase 0/1 evidence.

This checker is intentionally read-only. It validates the isolated inventory
artifacts and preserves existing authority boundaries.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
PHASE0 = BASE / "phase0-readiness-baseline-20261007.json"
INVENTORY = BASE / "phase1-capability-inventory-v0.json"
GAPS = BASE / "phase1-overlap-gap-map-v0.json"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def unique_ids(items: list[dict], label: str) -> None:
    ids = [item.get("id") for item in items]
    assert all(ids), f"{label}: missing id"
    assert len(ids) == len(set(ids)), f"{label}: duplicate ids"


def main() -> int:
    phase0 = load(PHASE0)
    inventory = load(INVENTORY)
    gaps = load(GAPS)

    assert phase0["schema"] == "velvetos.ai3d.phase0-readiness-baseline.v1"
    assert inventory["schema"] == "velvetos.ai3d.phase1-capability-inventory.v0"
    assert gaps["schema"] == "velvetos.ai3d.phase1-overlap-gap-map.v0"

    for gate in ("G1", "G2", "G3", "G4"):
        assert phase0["gates"][gate]["status"] == "GREEN", f"{gate} not green"

    assert phase0["gates"]["G2"]["promoted_capability_count"] == 20
    assert phase0["gates"]["G4"]["blender_provider_count"] == 271

    summary = inventory["summary"]
    assert summary["fabrication_intents"] == 25
    assert summary["cad_engines"] == 5
    assert summary["creative_craft_tools"] == 38
    assert summary["blender_providers"] == 271
    assert summary["cross_station_proven_capabilities"] == 20

    unique_ids(inventory["fabrication"]["intents"], "fabrication intents")
    unique_ids(inventory["cad_engines"]["engines"], "CAD engines")
    unique_ids(inventory["creative_craft"]["tools"], "CreativeCraft tools")
    unique_ids(inventory["blender_host"]["providers"], "Blender providers")

    boundaries = inventory["fabrication"]["hard_boundaries"]
    prohibited = (
        "printer_network_control",
        "upload_to_printer",
        "start_print",
        "heating",
        "motion",
        "sendcutsend_order_submission",
        "hidden_dimensions_may_be_invented",
    )
    for key in prohibited:
        assert boundaries.get(key) is False, f"unsafe fabrication boundary: {key}"

    station = inventory["creative_craft"]["blender_station_transport"]
    proven = station["proven_capabilities"]
    allowlist = station["execute_typed_allowlist"]
    assert len(proven) == 20
    assert len(proven) == len(set(proven))
    assert set(proven) == set(allowlist)
    assert "cam.toolpath" in proven

    closed = {item["id"]: item for item in gaps["closed_baselines"]}
    assert closed["fabrication-router"]["status"] == "ACTIVE_CANONICAL"
    assert closed["vf-3d-router"]["status"] == "ACTIVE_CANONICAL"

    gap_ids = {item["id"] for item in gaps["gaps"]}
    required_gaps = {
        "control-plane.task-spec-evidence-graph",
        "control-plane.license-manifest",
        "benchmark.golden-ai3d",
        "reconstruction.geometry-evidence",
        "reconstruction.render-back-scorer",
        "generation.local-ensemble",
        "organic.typed-refinement",
        "reverse-engineering.typed-contract",
        "cad.engine-contract-metadata",
    }
    assert required_gaps <= gap_ids, "required Phase 1 gaps missing"

    assert "No duplicate Fabrication Router" in phase0["authority_invariant"]

    print(
        "validate_ai3d_phase1: PASS "
        f"gates=4 intents={summary['fabrication_intents']} "
        f"engines={summary['cad_engines']} tools={summary['creative_craft_tools']} "
        f"providers={summary['blender_providers']} proven={summary['cross_station_proven_capabilities']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
