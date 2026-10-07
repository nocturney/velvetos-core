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
SPECIALISTS_PATH = BASE / "mesh-organic-specialists-v1.json"
REVERSE_PATH = BASE / "reverse-engineering-scan-to-cad-v1.json"
ASSEMBLY_ECAD_PATH = BASE / "assembly-motion-ecad-v1.json"


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
    specialists = load(SPECIALISTS_PATH)
    reverse = load(REVERSE_PATH)
    assembly_ecad = load(ASSEMBLY_ECAD_PATH)
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

    mechanical_records = {
        row["capability_id"].removeprefix("cad.feature."): row
        for row in records
        if row["record_id"].endswith("--mechanical-pack")
    }
    assert set(mechanical_records) == {
        "fasteners",
        "threads",
        "gears",
        "bearings",
        "inserts",
        "magnets",
        "fits",
        "snap_fit",
        "living_hinge",
        "enclosure",
        "sheet_metal",
    }
    for pack_id in (
        "fasteners",
        "threads",
        "gears",
        "bearings",
        "inserts",
        "magnets",
        "fits",
        "enclosure",
    ):
        row = mechanical_records[pack_id]
        assert row["status"] == "PROVEN", pack_id
        assert row["verification"]["state"] == "PROVEN_PROVIDER", pack_id
        assert row["adapter"]["id"] == "ai3d-mechanical-features", pack_id
    for pack_id in ("snap_fit", "living_hinge", "sheet_metal"):
        row = mechanical_records[pack_id]
        assert row["status"] == "CANDIDATE", pack_id
        assert row["verification"]["state"] == "CANDIDATE", pack_id

    fits = mechanical_records["fits"]
    assert fits["precision_model"] == "not_applicable"
    assert "fit_calculation" in fits["output_types"]
    assert fits["license_lane"] == "review-required"

    assert specialists["schema"] == "velvetos.ai3d.mesh-organic-specialists.v1"
    assert specialists["non_authoritative_staging"] is True
    assert specialists["policy"]["no_second_mesh_router"] is True
    assert specialists["policy"]["reuse_existing_typed_operations"] is True
    reused_typed = set(specialists["existing_typed_capabilities_reused"])
    assert reused_typed <= typed_caps
    for capability in reused_typed:
        rows = [
            row
            for row in typed
            if row["capability_id"] == capability
        ]
        assert len(rows) == 1, capability

    phase6_provider_records = {
        ("sidecar_pymeshlab", "ai.image_to_3d.print_cleanup"),
        ("sidecar_trimesh", "automation.geometry"),
        ("sidecar_trimesh", "geometry.variant_batch"),
        ("sidecar_open3d", "scan.reconstruct"),
        ("sidecar_libigl", "simulation.analysis"),
        ("native_sculpt", "sculpt.organic"),
    }
    for engine_id, capability_id in phase6_provider_records:
        row = next(
            item
            for item in records
            if item["engine"]["id"] == engine_id
            and item["capability_id"] == capability_id
        )
        assert row["status"] == "PROVEN", (engine_id, capability_id)
        assert row["verification"]["state"] == "PROVEN_PROVIDER", (
            engine_id,
            capability_id,
        )
        assert "validate_ai3d_phase6_mesh" in row["verification"]["validators"]
        assert all(
            item["verification"]["state"] != "PROVEN_TYPED"
            for item in records
            if item["engine"]["id"] == engine_id
            and item["capability_id"] == capability_id
        )

    sdf = next(
        row
        for row in records
        if row["record_id"] == "implicit.signed_distance--trimesh_sdf"
    )
    assert sdf["status"] == "PROVEN"
    assert sdf["verification"]["state"] == "PROVEN_PROVIDER"
    assert sdf["problem_class"] == "mesh_geometry"
    assert sdf["precision_model"] == "mixed"
    assert "signed_distance_field" in sdf["output_types"]
    assert sdf["runtime"]["id"] == "geometry-core-py312"
    assert sdf["license_lane"] == "commercial-clean"
    assert "mit" in sdf["license"]["code_license"].lower()

    openvdb = next(
        row
        for row in records
        if row["record_id"] == "implicit.openvdb--candidate-openvdb"
    )
    assert openvdb["status"] == "CANDIDATE"
    assert openvdb["verification"]["state"] == "CANDIDATE"
    assert openvdb["runtime"]["id"] == "not-admitted"
    assert openvdb["headless"] is False
    assert openvdb["license_lane"] == "review-required"
    assert "vdb_volume_artifact" in openvdb["output_types"]

    assert reverse["schema"] == "velvetos.ai3d.reverse-engineering-scan-to-cad.v1"
    assert reverse["non_authoritative_staging"] is True
    assert reverse["existing_composite_provider"] == "pipeline_scan_to_cad"
    assert reverse["epistemic_policy"]["scan_is_evidence_not_manufacturing_truth"] is True
    assert reverse["epistemic_policy"]["automatic_semantic_feature_recognition_claimed"] is False

    reverse_pipeline = next(
        row
        for row in records
        if row["record_id"] == "cad.reverse_engineer--pipeline_scan_to_cad"
    )
    assert reverse_pipeline["status"] == "PROVEN"
    assert reverse_pipeline["verification"]["state"] == "PROVEN_PROVIDER"
    assert reverse_pipeline["engine"]["id"] == "pipeline_scan_to_cad"
    assert reverse_pipeline["runtime"]["id"] == "multi-sidecar"
    assert "no_automatic_semantic_feature_recognition" in reverse_pipeline["constraints_support"]
    assert reverse_pipeline["verification"]["state"] != "PROVEN_TYPED"

    primitive_fit = next(
        row
        for row in records
        if row["record_id"] == "reconstruction.primitive_fit--phase7-explicit-primitive"
    )
    assert primitive_fit["status"] == "PROVEN"
    assert primitive_fit["verification"]["state"] == "PROVEN_PROVIDER"
    assert primitive_fit["authority"]["id"] == "fabrication-router"
    assert "geometry_ir" in primitive_fit["output_types"]
    assert "explicit_segment_ref" in primitive_fit["constraints_support"]
    assert "explicit_primitive_family" in primitive_fit["constraints_support"]
    assert "no_hidden_dimension_inference" in primitive_fit["constraints_support"]

    geomdl_fit = next(
        row
        for row in records
        if row["record_id"] == "reconstruction.nurbs_fit--geomdl"
    )
    assert geomdl_fit["status"] == "PROVEN"
    assert geomdl_fit["verification"]["state"] == "PROVEN_PROVIDER"
    assert geomdl_fit["engine"]["version"] == "5.4.0"
    assert geomdl_fit["runtime"]["id"] == "geometry-core-py312"
    assert geomdl_fit["license_lane"] == "commercial-clean"
    assert geomdl_fit["license"]["code_license"] == "MIT"
    assert "nurbs_surface_evidence" in geomdl_fit["output_types"]
    assert "separate_exact_cad_contract_required" in geomdl_fit["constraints_support"]

    nurbsfit = next(
        row
        for row in records
        if row["record_id"] == "reconstruction.nurbs_fit--candidate-nurbsfit_2026"
    )
    assert nurbsfit["status"] == "CANDIDATE"
    assert nurbsfit["verification"]["state"] == "CANDIDATE"
    assert nurbsfit["runtime"]["id"] == "not-admitted"
    assert nurbsfit["license_lane"] == "commercial-clean"
    assert nurbsfit["license"]["code_license"] == "MIT"

    assert assembly_ecad["schema"] == "velvetos.ai3d.assembly-motion-ecad.v1"
    assert assembly_ecad["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
    assert assembly_ecad["safety"]["printer_actions_allowed"] is False
    assert assembly_ecad["safety"]["machine_control_allowed"] is False
    assert assembly_ecad["safety"]["continuous_motion_claim_without_sampling"] is False
    assert assembly_ecad["safety"]["component_complete_ecad_claim_when_models_missing"] is False

    phase8_proven = {
        "assembly.joint.revolute--build123d-phase8": "assembly.joint.revolute",
        "assembly.motion.sweep--build123d-phase8": "assembly.motion.sweep",
        "assembly.collision.static--build123d-phase8": "assembly.collision.static",
        "assembly.freecad.fixed_joint--sidecar_freecad": "assembly.freecad.fixed_joint",
        "electronics.pcb_step_export--sidecar_kicad_cli-phase8": "electronics.pcb_step_export",
        "electronics.enclosure_fit--pipeline_pcb_to_enclosure-phase8": "electronics.enclosure_fit",
    }
    for record_id, capability_id in phase8_proven.items():
        row = next(item for item in records if item["record_id"] == record_id)
        assert row["capability_id"] == capability_id
        assert row["status"] == "PROVEN"
        assert row["verification"]["state"] == "PROVEN_PROVIDER"
        assert "validate_ai3d_phase8_assembly_ecad" in row["verification"]["validators"]

    revolute = next(
        row
        for row in records
        if row["record_id"] == "assembly.joint.revolute--build123d-phase8"
    )
    assert revolute["authority"]["id"] == "fabrication-router"
    assert revolute["engine"]["id"] == "build123d"
    assert revolute["engine"]["version"] == runtime_distribution_version("build123d")
    assert revolute["precision_model"] == "mixed"
    assert "explicit_joint_axis" in revolute["constraints_support"]
    assert "explicit_angle_range" in revolute["constraints_support"]
    assert "no_inferred_joint_axis" in revolute["constraints_support"]
    assert revolute["license_lane"] == "commercial-clean"

    sweep = next(
        row
        for row in records
        if row["record_id"] == "assembly.motion.sweep--build123d-phase8"
    )
    assert "sampled_motion_only" in sweep["constraints_support"]
    assert "no_continuous_collision_guarantee" in sweep["constraints_support"]
    assert "sampled_motion_report" in sweep["output_types"]

    collision = next(
        row
        for row in records
        if row["record_id"] == "assembly.collision.static--build123d-phase8"
    )
    assert "exact_brep_intersection" in collision["constraints_support"]
    assert "collision_report" in collision["output_types"]

    freecad_assembly = next(
        row
        for row in records
        if row["record_id"] == "assembly.freecad.fixed_joint--sidecar_freecad"
    )
    assert freecad_assembly["engine"]["version"] == "1.1.3"
    assert freecad_assembly["runtime"]["id"] == "freecad-1.1"
    assert freecad_assembly["headless"] is True
    assert freecad_assembly["license_lane"] == "commercial-clean"
    assert "lgpl" in freecad_assembly["license"]["code_license"].lower()

    pcb_export = next(
        row
        for row in records
        if row["record_id"] == "electronics.pcb_step_export--sidecar_kicad_cli-phase8"
    )
    assert pcb_export["engine"]["version"] == "10.0.6"
    assert pcb_export["runtime"]["id"] == "kicad-10.0.6"
    assert pcb_export["headless"] is True
    assert "no_component_complete_claim_when_models_missing" in pcb_export["constraints_support"]

    enclosure_fit = next(
        row
        for row in records
        if row["record_id"] == "electronics.enclosure_fit--pipeline_pcb_to_enclosure-phase8"
    )
    assert enclosure_fit["engine"]["id"] == "pipeline_pcb_to_enclosure"
    assert enclosure_fit["runtime"]["id"] == "multi-provider"
    assert enclosure_fit["verification"]["state"] != "PROVEN_TYPED"

    component_candidate = next(
        row
        for row in records
        if row["record_id"]
        == "electronics.pcb_step_export_components--candidate-kicad-models"
    )
    assert component_candidate["status"] == "CANDIDATE"
    assert component_candidate["verification"]["state"] == "CANDIDATE"
    assert component_candidate["license_lane"] == "review-required"

    robotics_candidate = next(
        row
        for row in records
        if row["record_id"] == "robotics.urdf_pinocchio--candidate-pinocchio"
    )
    assert robotics_candidate["status"] == "CANDIDATE"
    assert robotics_candidate["verification"]["state"] == "CANDIDATE"
    assert robotics_candidate["runtime"]["id"] == "not-admitted"
    assert robotics_candidate["headless"] is False

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
