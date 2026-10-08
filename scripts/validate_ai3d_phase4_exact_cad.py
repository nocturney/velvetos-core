#!/usr/bin/env python3
"""Host acceptance for AI3D Phase 4 exact-CAD expansion.

This validator intentionally runs outside the canonical check-* sensor registry
because it exercises host-local heavy CAD runtimes. It is fail-closed and writes
optional machine-readable evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
REGISTRY = ROOT / "packages" / "vfprod" / "CAD-ENGINE-REGISTRY.json"
PATTERNS = ROOT / "packages" / "vfprod" / "EXACT-CAD-PATTERNS.json"
SAMPLE = (
    ROOT
    / "packages"
    / "vfharness"
    / "state"
    / "cad-engine-stack-20260927"
    / "geometry-ir-sample.json"
)
STACK = ROOT / "scripts" / "vf_cad_stack.py"
PROBE = ROOT / "scripts" / "ai3d_exact_cad_probe.py"

sys.path.insert(0, str(ROOT / "scripts"))
import vf_cad_stack  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_json(command: list[str], cwd: Path = ROOT, expect: int = 0) -> dict[str, Any]:
    proc = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=240,
    )
    if proc.returncode != expect:
        raise AssertionError(
            f"command failed rc={proc.returncode} expected={expect}: {command}\n"
            f"stdout={proc.stdout[-4000:]}\nstderr={proc.stderr[-4000:]}"
        )
    return json.loads(proc.stdout)


def close(actual: float, expected: float, tolerance: float) -> bool:
    return abs(float(actual) - float(expected)) <= tolerance


def assert_vector(
    actual: list[float], expected: list[float], tolerance: float, label: str
) -> None:
    assert len(actual) == len(expected), label
    for index, (left, right) in enumerate(zip(actual, expected)):
        assert close(left, right, tolerance), (
            f"{label}[{index}] actual={left} expected={right} tolerance={tolerance}"
        )


def probe(runtime: Path, artifact_dir: Path, *, with_bd: bool) -> dict[str, Any]:
    command = [str(runtime), str(PROBE), "--artifact-dir", str(artifact_dir)]
    if not with_bd:
        command.append("--skip-bd-warehouse")
    return run_json(command)


def build(engine: str, output: Path, formats: str | None = None) -> dict[str, Any]:
    command = [
        sys.executable,
        str(STACK),
        "build",
        "--input",
        str(SAMPLE),
        "--engine",
        engine,
        "--out-dir",
        str(output),
    ]
    if formats:
        command.extend(["--formats", formats])
    return run_json(command)


def geometry_signature(payload: dict[str, Any]) -> dict[str, Any]:
    artifacts = payload["artifacts"]
    result: dict[str, Any] = {}
    for key in ("step", "stl"):
        if key in artifacts:
            row = artifacts[key]
            result[key] = {
                "bbox_min": row["bbox_min"],
                "bbox_max": row["bbox_max"],
                "bbox_size": row["bbox_size"],
            }
    if "3mf" in artifacts:
        row = artifacts["3mf"]["shapes"][0]
        result["3mf"] = {
            "bbox_min": row["bbox_min"],
            "bbox_max": row["bbox_max"],
            "bbox_size": row["bbox_size"],
        }
    if "dxf" in artifacts:
        result["dxf"] = {"bbox_size": artifacts["dxf"]["shapes"][0]["bbox_size"]}
    if "svg" in artifacts:
        result["svg"] = {"bbox_size": artifacts["svg"]["shapes"][0]["bbox_size"]}
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-out", type=Path)
    args = parser.parse_args()

    registry = load(REGISTRY)
    patterns = load(PATTERNS)
    assert registry["exact_cad_patterns"] == "packages/vfprod/EXACT-CAD-PATTERNS.json"
    build123d_row = registry["engines"]["build123d"]
    assert build123d_row["role"] == "primary"
    assert build123d_row["default_artifact_formats"] == ["STEP", "STL"]
    assert {"STEP", "STL", "3MF", "DXF", "SVG"} <= set(
        build123d_row["artifact_formats"]
    )
    assert patterns["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
    assert patterns["coordinate_frame"]["primitive_local_origin"] == "xy_center_z_min"
    assert patterns["semantic_selection"]["numeric_face_index_fallback"] is False
    assert patterns["semantic_selection"]["ambiguous_selection"] == "BLOCKED"
    assert patterns["safety"] == {
        "printer_actions_allowed": False,
        "machine_control_allowed": False,
        "invent_hidden_dimensions": False,
        "invent_missing_datums": False,
        "silent_ambiguous_selection": False,
    }

    runtime = vf_cad_stack.runtime_paths()["build123d"]
    cadquery_runtime = vf_cad_stack.runtime_paths()["cadquery"]
    assert runtime.is_file(), runtime
    assert cadquery_runtime.is_file(), cadquery_runtime

    required_formats = "step,stl,3mf,dxf,svg"
    with tempfile.TemporaryDirectory(prefix="ai3d-phase4-") as temp_name:
        temp = Path(temp_name)
        first_dir = temp / "build123d-a"
        second_dir = temp / "build123d-b"
        cadquery_dir = temp / "cadquery"
        jscad_dir = temp / "jscad"

        first_receipt = build("build123d", first_dir, required_formats)
        second_receipt = build("build123d", second_dir, required_formats)
        cadquery_receipt = build("cadquery", cadquery_dir)
        jscad_receipt = build("jscad", jscad_dir)

        assert first_receipt["artifacts"] == [
            "model.step",
            "model.stl",
            "model.3mf",
            "model-top.dxf",
            "model-top.svg",
        ]
        assert first_receipt["printer_actions_allowed"] is False
        assert first_receipt["engine_version"] == "0.11.1"
        assert first_receipt["coordinate_frame"] == "xy_center_z_min"
        assert first_receipt["input_sha256"] == sha256(SAMPLE)
        assert len(first_receipt["normalized_ir_sha256"]) == 64
        assert first_receipt["profile_refs"] == [
            "packages/vfprod/CAD-ENGINE-REGISTRY.json",
            "packages/vfprod/EXACT-CAD-PATTERNS.json",
        ]
        assert cadquery_receipt["engine"] == "cadquery"
        assert cadquery_receipt["engine_version"] == "2.8.0"
        assert cadquery_receipt["coordinate_frame"] == "xy_center_z_min"
        assert jscad_receipt["engine"] == "jscad"
        assert "@jscad/modeling 2.13.0" in jscad_receipt["engine_version"]
        assert jscad_receipt["coordinate_frame"] == "xy_center_z_min"

        first = probe(runtime, first_dir, with_bd=True)
        second = probe(runtime, second_dir, with_bd=False)
        cadquery = probe(runtime, cadquery_dir, with_bd=False)
        jscad = probe(runtime, jscad_dir, with_bd=False)

        exact_size = [120.0, 80.0, 12.0]
        exact_min = [-60.0, -40.0, 0.0]
        exact_max = [60.0, 40.0, 12.0]
        for label, payload, tolerance in (
            ("build123d-step", first["artifacts"]["step"], 1e-6),
            ("build123d-3mf", first["artifacts"]["3mf"]["shapes"][0], 1e-4),
            ("build123d-stl", first["artifacts"]["stl"], 1e-3),
            ("cadquery-step", cadquery["artifacts"]["step"], 1e-6),
            ("cadquery-stl", cadquery["artifacts"]["stl"], 1e-3),
            ("jscad-stl", jscad["artifacts"]["stl"], 1e-3),
        ):
            assert_vector(payload["bbox_size"], exact_size, tolerance, f"{label}.size")
            assert_vector(payload["bbox_min"], exact_min, tolerance, f"{label}.min")
            assert_vector(payload["bbox_max"], exact_max, tolerance, f"{label}.max")

        expected_volume = 120.0 * 80.0 * 8.0 + math.pi * 10.0 * 10.0 * 4.0
        mesh_quality: dict[str, Any] = {}
        for label, payload in (
            ("build123d", first["artifacts"]["stl"]),
            ("cadquery", cadquery["artifacts"]["stl"]),
            ("jscad", jscad["artifacts"]["stl"]),
        ):
            assert payload["mesh_watertight"] is True, label
            assert payload["mesh_body_count"] == 1, label
            assert_vector(payload["mesh_extents"], exact_size, 1e-3, f"{label}.mesh_extents")
            assert close(payload["mesh_volume"], expected_volume, 1.0), (
                label,
                payload["mesh_volume"],
                expected_volume,
            )
            mesh_quality[label] = {
                "watertight": payload["mesh_watertight"],
                "body_count": payload["mesh_body_count"],
                "extents_mm": payload["mesh_extents"],
                "volume_mm3": payload["mesh_volume"],
            }

        assert_vector(
            first["artifacts"]["dxf"]["shapes"][0]["bbox_size"],
            [20.0, 20.0, 0.0],
            1e-6,
            "dxf.top-profile",
        )
        assert_vector(
            first["artifacts"]["svg"]["shapes"][0]["bbox_size"],
            [20.0, 20.0, 0.0],
            1e-4,
            "svg.top-profile",
        )

        selection = first["artifacts"]["semantic_selection"]
        assert selection["numeric_face_index_used"] is False
        assert selection["cylindrical_face_count"] == 1
        assert close(selection["top_planar_face"]["center_z"], 12.0, 1e-6)
        assert_vector(selection["top_planar_face"]["normal"], [0.0, 0.0, 1.0], 1e-6, "top.normal")
        assert close(
            selection["top_planar_face"]["area"], math.pi * 10.0 * 10.0, 1e-5
        )

        assert geometry_signature(first) == geometry_signature(second), (
            "reopened geometry changed between identical build123d runs"
        )

        bd = first["bd_warehouse"]
        assert bd["version"] == "0.3.0"
        assert bd["license"] == "Apache-2.0"
        assert bd["build123d_version"] == "0.11.1"
        expected_primitives = {
            "fastener.socket_head_cap_screw",
            "fastener.hex_nut",
            "fastener.plain_washer",
        }
        assert set(bd["primitives"]) == expected_primitives
        for primitive_id, primitive in bd["primitives"].items():
            assert primitive["volume"] > 0, primitive_id
            assert all(value > 0 for value in primitive["bbox_size"]), primitive_id

        invalid = run_json(
            [
                sys.executable,
                str(STACK),
                "build",
                "--input",
                str(SAMPLE),
                "--engine",
                "build123d",
                "--formats",
                "step,unknown-format",
                "--out-dir",
                str(temp / "invalid"),
            ],
            expect=2,
        )
        assert invalid["status"] == "BLOCKED"
        assert invalid["reason"].startswith("unsupported_formats:build123d:")

        ambiguous_ir = {
            "schema": "velvetos.geometry-ir.v1",
            "units": "mm",
            "parts": [
                {
                    "id": "left",
                    "kind": "box",
                    "dimensions": {"x": 10, "y": 10, "z": 10},
                    "translate_mm": [-20, 0, 0],
                },
                {
                    "id": "right",
                    "kind": "box",
                    "dimensions": {"x": 10, "y": 10, "z": 10},
                    "translate_mm": [20, 0, 0],
                },
            ],
            "constraints": [],
        }
        ambiguous_path = temp / "ambiguous-top-face.json"
        ambiguous_path.write_text(
            json.dumps(ambiguous_ir, indent=2) + "\n",
            encoding="utf-8",
        )
        ambiguous = run_json(
            [
                sys.executable,
                str(STACK),
                "build",
                "--input",
                str(ambiguous_path),
                "--engine",
                "build123d",
                "--formats",
                "dxf",
                "--out-dir",
                str(temp / "ambiguous-output"),
            ],
            expect=2,
        )
        assert ambiguous["status"] == "BLOCKED"
        assert ambiguous["reason"] == "engine_failed"
        assert "semantic top-face selection ambiguous" in ambiguous["stderr"]

        byte_determinism: dict[str, bool] = {}
        for name in first_receipt["artifacts"]:
            byte_determinism[name] = sha256(first_dir / name) == sha256(second_dir / name)

        evidence = {
            "schema": "velvetos.ai3d.phase4-exact-cad-acceptance.v1",
            "status": "PASS",
            "authority": "packages/vfprod/FABRICATION-ROUTER.md",
            "patterns": "packages/vfprod/EXACT-CAD-PATTERNS.json",
            "coordinate_frame": "xy_center_z_min",
            "required_export_reopen_formats": ["STEP", "3MF", "STL", "DXF", "SVG"],
            "build123d": {
                "runtime": str(runtime),
                "version": bd["build123d_version"],
                "geometry_signature": geometry_signature(first),
                "repeat_geometry_signature": geometry_signature(second),
                "byte_determinism": byte_determinism,
                "note": (
                    "Geometry/semantic determinism is acceptance-critical. "
                    "Serializer metadata may make some valid formats byte-nondeterministic."
                ),
            },
            "cadquery": {
                "runtime": str(cadquery_runtime),
                "geometry_signature": geometry_signature(cadquery),
            },
            "jscad": {
                "geometry_signature": geometry_signature(jscad),
            },
            "mesh_quality": mesh_quality,
            "bd_warehouse": bd,
            "semantic_selection": selection,
            "negative_controls": {
                "unknown_export_format": "BLOCKED",
                "ambiguous_top_profile": "BLOCKED",
                "numeric_face_index_fallback": False,
                "printer_actions_allowed": False,
            },
        }

        if args.evidence_out:
            args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
            with args.evidence_out.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    print(
        "validate_ai3d_phase4_exact_cad: PASS "
        "exports=STEP,3MF,STL,DXF,SVG "
        "engines=build123d,cadquery,jscad bd_warehouse=0.3.0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
