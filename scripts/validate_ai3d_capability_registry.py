#!/usr/bin/env python3
"""Validate AI3D CAD Capability Registry v1 staging contract."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import vf_cad_stack

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
SCHEMA_PATH = BASE / "cad-capability-registry-v1.schema.json"
REGISTRY_PATH = BASE / "cad-capability-registry-v1.json"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def validate_schema(instance: dict, schema: dict) -> None:
    try:
        import jsonschema
    except ImportError:
        return
    jsonschema.Draft202012Validator(schema).validate(instance)


def runtime_distribution_version(
    distribution: str, runtime_engine: str | None = None
) -> str:
    runtime = vf_cad_stack.runtime_paths()[runtime_engine or distribution]
    proc = subprocess.run(
        [
            str(runtime),
            "-c",
            (
                "import importlib.metadata as m;"
                f"print(m.version({distribution!r}))"
            ),
        ],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip().splitlines()[-1]


def main() -> int:
    schema = load(SCHEMA_PATH)
    registry = load(REGISTRY_PATH)
    validate_schema(registry, schema)

    assert registry["schema"] == "velvetos.ai3d.cad-capability-registry.v1"
    assert registry["non_authoritative_staging"] is True
    assert "grants no authority" in registry["authority_invariant"].lower()

    records = registry["records"]
    assert records, "registry must not be empty"
    record_ids = [row["record_id"] for row in records]
    assert len(record_ids) == len(set(record_ids)), "duplicate record_id"

    allowed_authorities = {"fabrication-router", "blender-capability-host"}
    for row in records:
        assert row["authority"]["id"] in allowed_authorities
        assert row["input_types"], row["record_id"]
        assert row["output_types"], row["record_id"]
        assert row["constraints_support"], row["record_id"]
        assert row["verification"]["validators"], row["record_id"]
        assert row["verification"]["evidence_refs"], row["record_id"]
        license_record = row["license"]
        for field in (
            "license_source",
            "code_license",
            "data_license",
            "allowed_use",
            "attribution",
            "redistribution",
            "bundle_policy",
            "provenance",
        ):
            assert field in license_record, f"{row['record_id']}: license field {field}"

        if row["status"] == "CANDIDATE":
            assert row["verification"]["state"] == "CANDIDATE"
            assert row["license_lane"] != "commercial-clean" or row["license"]["code_license"], (
                f"{row['record_id']}: candidate cannot be assumed commercial-clean"
            )

    typed = [
        row
        for row in records
        if row["authority"]["id"] == "blender-capability-host"
        and row["verification"]["state"] == "PROVEN_TYPED"
    ]
    assert len(typed) == 20, f"expected 20 cross-station typed records, got {len(typed)}"

    typed_caps = {row["capability_id"] for row in typed}
    assert len(typed_caps) == 20
    assert "cam.toolpath" in typed_caps
    assert "cad.export_step" in typed_caps
    assert "mesh.boolean_hardsurface" in typed_caps
    assert "scan.register" in typed_caps

    cam = next(row for row in typed if row["capability_id"] == "cam.toolpath")
    assert "offline_grbl_artifact" in cam["output_types"]
    assert "offline_output_only" in cam["constraints_support"]
    assert "no_machine_control" in cam["constraints_support"]

    build123d = next(
        row for row in records if row["record_id"] == "cad.solid.parametric--build123d"
    )
    assert build123d["authority"]["id"] == "fabrication-router"
    assert build123d["status"] == "ACTIVE_AUTHORITY"
    assert build123d["precision_model"] == "exact_brep"
    assert build123d["engine"]["version"] == runtime_distribution_version("build123d")
    assert build123d["runtime"]["id"] == "vf-cad-stack:build123d-venv"
    assert build123d["license_lane"] == "commercial-clean"
    assert "apache" in build123d["license"]["code_license"].lower()

    cadquery = next(
        row for row in records if row["record_id"] == "cad.solid.parametric--cadquery"
    )
    assert cadquery["status"] == "PROVEN"
    assert cadquery["engine"]["version"] == runtime_distribution_version("cadquery")
    assert cadquery["runtime"]["id"] == "vf-cad-stack:cadquery-venv"
    assert cadquery["license_lane"] == "commercial-clean"

    jscad = next(
        row for row in records if row["record_id"] == "cad.solid.parametric--jscad"
    )
    assert jscad["status"] == "PROVEN"
    assert jscad["verification"]["state"] == "PROVEN_PROVIDER"
    assert jscad["runtime"]["id"] == "vf-cad-stack:jscad-node"
    assert jscad["license_lane"] == "commercial-clean"

    bd_warehouse = next(
        row
        for row in records
        if row["record_id"] == "cad.primitives.mechanical--bd_warehouse"
    )
    assert bd_warehouse["status"] == "PROVEN"
    assert bd_warehouse["verification"]["state"] == "PROVEN_PROVIDER"
    assert bd_warehouse["engine"]["version"] == runtime_distribution_version(
        "bd_warehouse", "build123d"
    )
    assert bd_warehouse["runtime"]["id"] == "vf-cad-stack:build123d-venv"
    assert bd_warehouse["license_lane"] == "commercial-clean"
    assert bd_warehouse["license"]["code_license"] == "Apache-2.0"

    forgent = next(
        row for row in records if row["record_id"] == "cad.solid.parametric--forgent3d"
    )
    assert forgent["status"] == "CANDIDATE"
    assert forgent["headless"] is False

    research_candidate_engines = {
        "hunyuan3d-2.1-shape",
        "triposg",
        "spar3d",
        "vggt-commercial-checkpoint",
        "moge",
        "pixal3d",
    }
    candidate_rows = [row for row in records if row["engine"]["id"] in research_candidate_engines]
    assert len(candidate_rows) == len(research_candidate_engines)
    assert all(row["status"] == "CANDIDATE" for row in candidate_rows)
    assert all(row["license_lane"] == "review-required" for row in candidate_rows)

    print(
        "validate_ai3d_capability_registry: PASS "
        f"records={len(records)} typed={len(typed)} candidates="
        f"{sum(1 for row in records if row['status'] == 'CANDIDATE')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
