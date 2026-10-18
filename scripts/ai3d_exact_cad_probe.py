#!/usr/bin/env python3
"""Probe exact-CAD artifacts inside the canonical build123d runtime.

Run this script with the build123d venv Python. It is read-only with respect to
the artifacts under test and emits machine-readable geometry evidence.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
from pathlib import Path
from typing import Any

import build123d as b


def vector(value: Any) -> list[float]:
    return [float(value.X), float(value.Y), float(value.Z)]


def metrics(shape: Any) -> dict[str, Any]:
    box = shape.bounding_box()
    return {
        "type": type(shape).__name__,
        "bbox_min": vector(box.min),
        "bbox_max": vector(box.max),
        "bbox_size": vector(box.size),
        "volume": float(getattr(shape, "volume", 0.0)),
        "area": float(getattr(shape, "area", 0.0)),
    }


def geom_name(face: Any) -> str:
    value = getattr(face, "geom_type", None)
    return getattr(value, "name", str(value).split(".")[-1])


def select_unique_extreme_planar_face(shape: Any, *, positive_z: bool) -> Any:
    matches = []
    for face in shape.faces():
        if geom_name(face) != "PLANE":
            continue
        normal = face.normal_at()
        if positive_z and normal.Z < 0.999999:
            continue
        if not positive_z and normal.Z > -0.999999:
            continue
        matches.append(face)
    if not matches:
        raise RuntimeError("no matching planar face")
    extreme = (
        max(face.center().Z for face in matches)
        if positive_z
        else min(face.center().Z for face in matches)
    )
    selected = [face for face in matches if abs(face.center().Z - extreme) <= 1e-6]
    if len(selected) != 1:
        raise RuntimeError(f"ambiguous semantic planar selection: {len(selected)}")
    return selected[0]


def probe_artifacts(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    step_path = root / "model.step"
    if step_path.is_file():
        step = b.import_step(step_path)
        result["step"] = metrics(step)
        top = select_unique_extreme_planar_face(step, positive_z=True)
        bottom = select_unique_extreme_planar_face(step, positive_z=False)
        cylinders = [face for face in step.faces() if geom_name(face) == "CYLINDER"]
        result["semantic_selection"] = {
            "top_planar_face": {
                **metrics(top),
                "center_z": float(top.center().Z),
                "normal": vector(top.normal_at()),
            },
            "bottom_planar_face": {
                **metrics(bottom),
                "center_z": float(bottom.center().Z),
                "normal": vector(bottom.normal_at()),
            },
            "cylindrical_face_count": len(cylinders),
            "numeric_face_index_used": False,
        }

    three_mf = root / "model.3mf"
    if three_mf.is_file():
        mesher = b.Mesher()
        shapes = mesher.read(three_mf)
        result["3mf"] = {
            "shape_count": len(shapes),
            "shapes": [metrics(shape) for shape in shapes],
        }

    stl_path = root / "model.stl"
    if stl_path.is_file():
        stl_metrics = metrics(b.import_stl(stl_path))
        if importlib.util.find_spec("trimesh") is not None:
            import trimesh

            mesh = trimesh.load_mesh(stl_path, process=True)
            stl_metrics["mesh_extents"] = [float(value) for value in mesh.extents]
            stl_metrics["mesh_volume"] = float(mesh.volume)
            stl_metrics["mesh_watertight"] = bool(mesh.is_watertight)
            stl_metrics["mesh_body_count"] = int(mesh.body_count)
        result["stl"] = stl_metrics

    dxf_path = root / "model-top.dxf"
    if dxf_path.is_file():
        shapes = b.import_dxf(dxf_path)
        result["dxf"] = {
            "shape_count": len(shapes),
            "shapes": [metrics(shape) for shape in shapes],
        }

    svg_path = root / "model-top.svg"
    if svg_path.is_file():
        shapes = b.import_svg(svg_path, align=None)
        result["svg"] = {
            "shape_count": len(shapes),
            "shapes": [metrics(shape) for shape in shapes],
        }

    return result


def bd_warehouse_probe() -> dict[str, Any]:
    from bd_warehouse.fastener import HexNut, PlainWasher, SocketHeadCapScrew

    rows = {
        "fastener.socket_head_cap_screw": SocketHeadCapScrew(
            "M4-0.7", 16, "iso4762", simple=True
        ),
        "fastener.hex_nut": HexNut("M4-0.7", "iso4032", simple=True),
        "fastener.plain_washer": PlainWasher("M4", "iso7089"),
    }
    metadata = importlib.metadata.metadata("bd_warehouse")
    return {
        "version": importlib.metadata.version("bd_warehouse"),
        "license": metadata.get("License-Expression") or metadata.get("License"),
        "build123d_version": importlib.metadata.version("build123d"),
        "primitives": {name: metrics(shape) for name, shape in rows.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--skip-bd-warehouse", action="store_true")
    args = parser.parse_args()

    payload = {
        "schema": "velvetos.ai3d.exact-cad-probe.v1",
        "artifact_dir": str(args.artifact_dir.resolve()),
        "artifacts": probe_artifacts(args.artifact_dir.resolve()),
    }
    if not args.skip_bd_warehouse:
        payload["bd_warehouse"] = bd_warehouse_probe()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
