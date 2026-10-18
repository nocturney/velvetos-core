#!/usr/bin/env python3
"""Validate AI3D Phase 7 reverse engineering and scan-to-CAD.

The validator reuses the existing pipeline_scan_to_cad provider, existing scan
providers and the existing Fabrication Router. It proves bounded primitive and
NURBS fitting without claiming automatic semantic feature recognition.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
CONFIG = BASE / "reverse-engineering-scan-to-cad-v1.json"
PROVIDERS = Path(r"D:\Velvet\State\CreativeCraft\blender-provider-registry.json")
CREATIVE = Path(r"D:\Velvet\Runtime\CreativeCraft\creative-craft-registry.json")
ADAPTER = ROOT / "scripts" / "ai3d_reverse_engineering.py"
CAD_STACK = ROOT / "scripts" / "vf_cad_stack.py"
GEOMETRY_PYTHON = Path(
    r"D:\Velvet\Runtime\BlenderMonster\venvs\geometry-core\Scripts\python.exe"
)
SCAN_PYTHON = Path(
    r"D:\Velvet\Runtime\BlenderMonster\venvs\scan-reconstruction\Scripts\python.exe"
)
SCAN_PROBE = Path(r"D:\Velvet\BlenderStack\probe_scan_sidecar.py")
BUILD123D_PYTHON = Path(
    r"C:\Users\Chris\Documents\VelvetPrintLab\tools\text-to-cad\.venv\Scripts\python.exe"
)


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    assert isinstance(value, dict), path
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2) + "\n")


def run(
    command: list[str],
    *,
    expect: int = 0,
    timeout: int = 240,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    if proc.returncode != expect:
        raise AssertionError(
            f"command failed rc={proc.returncode} expected={expect}: {command}\n"
            f"stdout={proc.stdout[-5000:]}\nstderr={proc.stderr[-5000:]}"
        )
    return proc


def run_json(command: list[str], *, expect: int = 0, timeout: int = 240) -> dict[str, Any]:
    proc = run(command, expect=expect, timeout=timeout)
    return json.loads(proc.stdout)


def provider(registry: dict[str, Any], provider_id: str) -> dict[str, Any]:
    matches = [row for row in registry["providers"] if row.get("id") == provider_id]
    assert len(matches) == 1, provider_id
    return matches[0]


def functional_pass(row: dict[str, Any]) -> bool:
    value = str(row.get("functional_probe_verdict") or row.get("functional_probe") or "").lower()
    return (
        value == "native"
        or value == "passed"
        or value.startswith("passed_")
        or value.endswith("_passed")
    )


def prefixed_json(stdout: str, prefix: str) -> dict[str, Any]:
    rows = [line for line in stdout.splitlines() if line.startswith(prefix)]
    assert len(rows) == 1, (prefix, stdout[-3000:])
    return json.loads(rows[0][len(prefix) :])


def package_metadata(python: Path, distribution: str) -> dict[str, Any]:
    code = (
        "import importlib.metadata as m,json;"
        f"d=m.metadata({distribution!r});"
        f"print(json.dumps(dict(version=m.version({distribution!r}),"
        "license=d.get('License-Expression') or d.get('License'))))"
    )
    return run_json([str(python), "-c", code])


def cylinder_request() -> dict[str, Any]:
    points: list[dict[str, Any]] = []
    cx, cy, radius = 5.0, -3.0, 10.0
    for z in (2.0, 17.0, 32.0):
        for index in range(32):
            angle = 2.0 * math.pi * index / 32.0
            points.append(
                {
                    "xyz": [
                        cx + radius * math.cos(angle),
                        cy + radius * math.sin(angle),
                        z,
                    ],
                    "segment": "target",
                }
            )
    for index in range(12):
        points.append(
            {
                "xyz": [100.0 + index, 100.0, 0.0],
                "segment": "distractor",
            }
        )
    return {
        "schema": "velvetos.ai3d.reverse-engineering-request.v1",
        "units": "mm",
        "source_kind": "point_cloud",
        "measurement_basis": "known_dimension_anchor",
        "segment_ref": "target",
        "primitive_family": "cylinder_z",
        "known_dimensions": [
            {"id": "diameter", "value_mm": 20.0, "tolerance_mm": 0.01},
            {"id": "height", "value_mm": 30.0, "tolerance_mm": 0.01},
        ],
        "points": points,
    }


def nurbs_request() -> dict[str, Any]:
    size_u = 7
    size_v = 7
    points = []
    for u in range(size_u):
        x = -15.0 + 5.0 * u
        for v in range(size_v):
            y = -15.0 + 5.0 * v
            z = 0.02 * x * x + 0.01 * y * y
            points.append([x, y, z])
    return {
        "schema": "velvetos.ai3d.reverse-engineering-request.v1",
        "units": "mm",
        "source_kind": "point_grid",
        "measurement_basis": "metric_scan",
        "fit_kind": "nurbs_surface_grid",
        "size_u": size_u,
        "size_v": size_v,
        "degree_u": 3,
        "degree_v": 3,
        "ctrlpts_size_u": 5,
        "ctrlpts_size_v": 5,
        "sample_size": 45,
        "max_fit_error_mm": 1.5,
        "points": points,
    }


def step_metrics(step_path: Path) -> dict[str, Any]:
    code = (
        "import build123d as b,json;"
        f"s=b.import_step(r{str(step_path)!r});"
        "q=s.bounding_box();"
        "print(json.dumps({'min':[q.min.X,q.min.Y,q.min.Z],"
        "'max':[q.max.X,q.max.Y,q.max.Z],"
        "'size':[q.size.X,q.size.Y,q.size.Z],"
        "'volume':float(s.volume)}))"
    )
    return run_json([str(BUILD123D_PYTHON), "-c", code])


def close_vector(actual: list[float], expected: list[float], tolerance: float) -> None:
    assert len(actual) == len(expected)
    for got, want in zip(actual, expected):
        assert abs(float(got) - float(want)) <= tolerance, (actual, expected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-out", type=Path)
    args = parser.parse_args()

    config = load(CONFIG)
    registry = load(PROVIDERS)
    creative = load(CREATIVE)

    assert config["schema"] == "velvetos.ai3d.reverse-engineering-scan-to-cad.v1"
    assert config["non_authoritative_staging"] is True
    assert config["existing_composite_provider"] == "pipeline_scan_to_cad"
    assert config["authorities"]["scan_mesh"] == "blender-capability-host"
    assert config["authorities"]["exact_cad"] == "packages/vfprod/FABRICATION-ROUTER.md"
    assert config["epistemic_policy"]["scan_is_evidence_not_manufacturing_truth"] is True
    assert config["epistemic_policy"]["automatic_semantic_feature_recognition_claimed"] is False
    assert config["epistemic_policy"]["hidden_dimensions_may_be_invented"] is False

    pipeline = provider(registry, "pipeline_scan_to_cad")
    assert pipeline["installed"] is True
    assert pipeline["enabled"] is True
    assert pipeline["state"] == "available"
    assert pipeline["startup_probe"] == "passed"
    assert pipeline["background_startup"] == "passed"
    assert pipeline["headless_operation"] == "available"
    assert functional_pass(pipeline)
    assert "cad.reverse_engineer" in pipeline["capabilities"]
    assert "does not claim automatic semantic feature recognition" in pipeline["notes"]

    stage_caps = {stage["capability"] for stage in pipeline["stages"]}
    assert {"scan.pointcloud", "scan.clean", "mesh.remesh_repair", "cad.solid.parametric"} <= stage_caps

    component_expectations = {
        "sidecar_colmap": ("4.2.1", "colmap-4.2.1-cuda"),
        "sidecar_meshroom": ("2025.1.0", "meshroom-2025.1.0-windows-cuda12"),
        "sidecar_open3d": ("0.20.0", "scan-reconstruction-py312"),
        "sidecar_freecad": ("1.1.3", "freecad-1.1"),
    }
    components: dict[str, Any] = {}
    for provider_id, (version, runtime) in component_expectations.items():
        row = provider(registry, provider_id)
        assert row["installed"] is True
        assert row["enabled"] is True
        assert functional_pass(row)
        assert row["version"] == version
        assert row["runtime"] == runtime
        components[provider_id] = {
            "version": row["version"],
            "runtime": row["runtime"],
            "functional_probe": row.get("functional_probe_verdict") or row.get("functional_probe"),
            "capabilities": row["capabilities"],
        }

    transport = creative["tools"]["blender"]["station_transport"]
    proven_typed = set(transport["proven_capabilities"])
    assert {"scan.pointcloud", "scan.clean", "scan.register"} <= proven_typed
    assert "cad.reverse_engineer" not in proven_typed

    assert GEOMETRY_PYTHON.is_file()
    assert SCAN_PYTHON.is_file()
    assert SCAN_PROBE.is_file()
    assert BUILD123D_PYTHON.is_file()

    geomdl = package_metadata(GEOMETRY_PYTHON, "geomdl")
    assert geomdl["version"] == "5.4.0"
    assert str(geomdl["license"]).upper() == "MIT"

    scan_proc = run([str(SCAN_PYTHON), str(SCAN_PROBE)])
    scan_fixture = prefixed_json(scan_proc.stdout, "VF_SCAN_FIXTURE ")
    assert all(row["success"] for row in scan_fixture.values())
    assert scan_fixture["open3d_icp"]["fitness"] > 0.99
    assert scan_fixture["open3d_icp"]["rmse"] < 1e-9

    with tempfile.TemporaryDirectory(prefix="ai3d-phase7-") as temp_name:
        temp = Path(temp_name)

        primitive_input = temp / "primitive-request.json"
        primitive_output = temp / "primitive-result.json"
        write(primitive_input, cylinder_request())
        primitive = run_json(
            [
                sys.executable,
                str(ADAPTER),
                "fit-primitive",
                "--input",
                str(primitive_input),
                "--output",
                str(primitive_output),
            ]
        )
        assert primitive["status"] == "PASS"
        assert primitive["primitive_family"] == "cylinder_z"
        assert primitive["segment_ref"] == "target"
        assert primitive["selected_point_count"] == 96
        assert primitive["fitted_dimensions_mm"] == {"diameter": 20.0, "height": 30.0}
        close_vector(primitive["translate_mm"], [5.0, -3.0, 2.0], 1e-9)
        assert all(row["within_tolerance"] for row in primitive["dimension_evidence"])
        assert primitive["semantic_feature_recognition"] is False
        assert primitive["hidden_dimension_inference"] is False
        assert primitive["manufacturing_authority"] is False
        assert primitive["next_authority"] == "packages/vfprod/FABRICATION-ROUTER.md"

        geometry_ir = temp / "fitted-geometry-ir.json"
        write(geometry_ir, primitive["geometry_ir"])
        cad_dir = temp / "cad-build"
        cad_build = run_json(
            [
                sys.executable,
                str(CAD_STACK),
                "build",
                "--input",
                str(geometry_ir),
                "--engine",
                "build123d",
                "--formats",
                "step,stl",
                "--out-dir",
                str(cad_dir),
            ]
        )
        assert cad_build["status"] == "PASS"
        assert cad_build["engine"] == "build123d"
        assert cad_build["engine_version"] == "0.11.1"
        assert cad_build["printer_actions_allowed"] is False
        step = step_metrics(cad_dir / "model.step")
        close_vector(step["min"], [-5.0, -13.0, 2.0], 1e-6)
        close_vector(step["max"], [15.0, 7.0, 32.0], 1e-6)
        close_vector(step["size"], [20.0, 20.0, 30.0], 1e-6)
        expected_volume = math.pi * 10.0 * 10.0 * 30.0
        assert abs(step["volume"] - expected_volume) <= 1e-6

        missing_family = cylinder_request()
        missing_family.pop("primitive_family")
        path = temp / "missing-family.json"
        write(path, missing_family)
        blocked_family = run_json(
            [sys.executable, str(ADAPTER), "fit-primitive", "--input", str(path)],
            expect=2,
        )
        assert blocked_family["reason"] == "explicit_supported_primitive_family_required"

        missing_segment = cylinder_request()
        missing_segment.pop("segment_ref")
        path = temp / "missing-segment.json"
        write(path, missing_segment)
        blocked_segment = run_json(
            [sys.executable, str(ADAPTER), "fit-primitive", "--input", str(path)],
            expect=2,
        )
        assert blocked_segment["reason"] == "segment_ref_required"

        wrong_anchor = cylinder_request()
        wrong_anchor["known_dimensions"][0]["value_mm"] = 25.0
        wrong_anchor["known_dimensions"][0]["tolerance_mm"] = 0.1
        path = temp / "wrong-anchor.json"
        write(path, wrong_anchor)
        blocked_anchor = run_json(
            [sys.executable, str(ADAPTER), "fit-primitive", "--input", str(path)],
            expect=2,
        )
        assert blocked_anchor["reason"] == "dimension_anchor_mismatch"

        nurbs_input = temp / "nurbs-request.json"
        write(nurbs_input, nurbs_request())
        nurbs = run_json(
            [
                str(GEOMETRY_PYTHON),
                str(ADAPTER),
                "fit-nurbs-surface",
                "--input",
                str(nurbs_input),
            ]
        )
        assert nurbs["status"] == "PASS"
        assert nurbs["fit_kind"] == "nurbs_surface_grid"
        assert nurbs["degree_u"] == 3 and nurbs["degree_v"] == 3
        assert nurbs["ctrlpts_size_u"] == 5 and nurbs["ctrlpts_size_v"] == 5
        assert nurbs["fit_error_mm"]["max_nearest_sample"] < 0.5
        assert nurbs["fit_error_mm"]["threshold"] == 1.5
        assert nurbs["manufacturing_authority"] is False
        assert nurbs["cad_conversion_requires_separate_contract"] is True
        assert nurbs["hidden_dimension_inference"] is False

        no_threshold = nurbs_request()
        no_threshold.pop("max_fit_error_mm")
        path = temp / "nurbs-no-threshold.json"
        write(path, no_threshold)
        blocked_nurbs = run_json(
            [
                str(GEOMETRY_PYTHON),
                str(ADAPTER),
                "fit-nurbs-surface",
                "--input",
                str(path),
            ],
            expect=2,
        )
        assert blocked_nurbs["reason"] == "max_fit_error_mm_required"

    nurbsfit = config["research_candidates"]["nurbsfit_2026"]
    assert nurbsfit["status"] == "CANDIDATE_RESEARCH"
    assert nurbsfit["license"] == "MIT"
    assert len(nurbsfit["blockers"]) >= 4

    safety = config["safety"]
    assert safety["printer_actions_allowed"] is False
    assert safety["machine_control_allowed"] is False
    assert safety["duplicate_scan_router"] is False
    assert safety["duplicate_cad_router"] is False
    assert safety["automatic_semantic_feature_inference"] is False

    evidence = {
        "schema": "velvetos.ai3d.phase7-reverse-engineering-acceptance.v1",
        "status": "PASS",
        "existing_composite_provider": "pipeline_scan_to_cad",
        "authorities": config["authorities"],
        "components": components,
        "reused_typed_capabilities": ["scan.pointcloud", "scan.clean", "scan.register"],
        "scan_fixture": scan_fixture,
        "geomdl": geomdl,
        "primitive_fit": {
            "family": primitive["primitive_family"],
            "selected_point_count": primitive["selected_point_count"],
            "fitted_dimensions_mm": primitive["fitted_dimensions_mm"],
            "translate_mm": primitive["translate_mm"],
            "dimension_evidence": primitive["dimension_evidence"],
            "semantic_feature_recognition": False,
        },
        "cad_reconstruction": {
            "engine": cad_build["engine"],
            "engine_version": cad_build["engine_version"],
            "formats": cad_build["formats"],
            "step_roundtrip": step,
            "authority": "packages/vfprod/FABRICATION-ROUTER.md",
        },
        "nurbs_fit": {
            "provider": "geomdl",
            "version": geomdl["version"],
            "fit_error_mm": nurbs["fit_error_mm"],
            "degree_u": nurbs["degree_u"],
            "degree_v": nurbs["degree_v"],
            "ctrlpts_size_u": nurbs["ctrlpts_size_u"],
            "ctrlpts_size_v": nurbs["ctrlpts_size_v"],
            "surface_role": nurbs["surface_role"],
            "manufacturing_authority": False,
        },
        "negative_controls": {
            "missing_primitive_family": "BLOCKED",
            "missing_segment_ref": "BLOCKED",
            "dimension_anchor_mismatch": "BLOCKED",
            "nurbs_without_fit_threshold": "BLOCKED",
            "automatic_semantic_feature_recognition": False,
        },
        "nurbsfit_2026": nurbsfit,
        "safety": safety,
    }

    if args.evidence_out:
        args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
        write(args.evidence_out, evidence)

    print(
        "validate_ai3d_phase7_reverse_engineering: PASS "
        "pipeline=pipeline_scan_to_cad primitive=cylinder_z "
        "cad=build123d+STEP nurbs=geomdl-5.4.0 "
        "nurbsfit=CANDIDATE"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
