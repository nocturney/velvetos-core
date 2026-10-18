#!/usr/bin/env python3
"""Bounded reverse-engineering helpers for AI3D Phase 7.

This is not a router and does not infer hidden semantics. Primitive fitting
requires an explicit primitive family and explicit segment reference. NURBS
fitting produces surface evidence only; it never grants manufacturing authority.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any


REQUEST_SCHEMA = "velvetos.ai3d.reverse-engineering-request.v1"
ALLOWED_PRIMITIVES = {"box_axis_aligned", "cylinder_z"}


def emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("request must be a JSON object")
    return value


def blocked(reason: str, **extra: Any) -> tuple[dict[str, Any], bool]:
    return (
        {
            "schema": "velvetos.ai3d.reverse-engineering-result.v1",
            "status": "BLOCKED",
            "reason": reason,
            "manufacturing_authority": False,
            **extra,
        },
        False,
    )


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_common(request: dict[str, Any]) -> str | None:
    if request.get("schema") != REQUEST_SCHEMA:
        return "schema"
    if request.get("units") != "mm":
        return "units_must_be_mm"
    if request.get("measurement_basis") not in {"metric_scan", "known_dimension_anchor"}:
        return "measurement_basis"
    if request.get("measurement_basis") == "known_dimension_anchor" and not request.get("known_dimensions"):
        return "known_dimension_anchor_required"
    return None


def selected_points(request: dict[str, Any]) -> tuple[list[list[float]] | None, str | None]:
    segment_ref = request.get("segment_ref")
    if not isinstance(segment_ref, str) or not segment_ref:
        return None, "segment_ref_required"
    rows = request.get("points")
    if not isinstance(rows, list):
        return None, "points_required"
    points: list[list[float]] = []
    for row in rows:
        if not isinstance(row, dict) or row.get("segment") != segment_ref:
            continue
        xyz = row.get("xyz")
        if (
            not isinstance(xyz, list)
            or len(xyz) != 3
            or not all(_number(value) for value in xyz)
        ):
            return None, "invalid_point"
        points.append([float(value) for value in xyz])
    if len(points) < 12:
        return None, "insufficient_segment_points"
    return points, None


def dimensions_for_family(family: str, points: list[list[float]]) -> tuple[dict[str, float], list[float]]:
    xs = [row[0] for row in points]
    ys = [row[1] for row in points]
    zs = [row[2] for row in points]
    z_min = min(zs)
    z_max = max(zs)

    if family == "box_axis_aligned":
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        dimensions = {
            "x": x_max - x_min,
            "y": y_max - y_min,
            "z": z_max - z_min,
        }
        translate = [(x_min + x_max) / 2.0, (y_min + y_max) / 2.0, z_min]
        return dimensions, translate

    if family == "cylinder_z":
        cx = statistics.fmean(xs)
        cy = statistics.fmean(ys)
        radii = [math.hypot(x - cx, y - cy) for x, y in zip(xs, ys)]
        radius = statistics.median(radii)
        dimensions = {
            "diameter": 2.0 * radius,
            "height": z_max - z_min,
        }
        translate = [cx, cy, z_min]
        return dimensions, translate

    raise AssertionError(family)


def dimension_evidence(
    request: dict[str, Any],
    dimensions: dict[str, float],
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    all_within = True
    known = request.get("known_dimensions") or []
    if not isinstance(known, list):
        return [{"error": "known_dimensions_must_be_list"}], False
    for item in known:
        if not isinstance(item, dict):
            return [{"error": "invalid_known_dimension"}], False
        dimension_id = item.get("id")
        value = item.get("value_mm")
        tolerance = item.get("tolerance_mm")
        if dimension_id not in dimensions or not _number(value) or not _number(tolerance):
            return [{"error": "invalid_known_dimension"}], False
        tolerance = float(tolerance)
        if tolerance < 0:
            return [{"error": "invalid_known_dimension_tolerance"}], False
        actual = float(dimensions[dimension_id])
        error = abs(actual - float(value))
        within = error <= tolerance
        all_within = all_within and within
        rows.append(
            {
                "id": dimension_id,
                "expected_mm": float(value),
                "actual_mm": actual,
                "absolute_error_mm": error,
                "tolerance_mm": tolerance,
                "within_tolerance": within,
            }
        )
    return rows, all_within


def fit_primitive(request: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    common_error = validate_common(request)
    if common_error:
        return blocked(common_error)

    family = request.get("primitive_family")
    if family not in ALLOWED_PRIMITIVES:
        return blocked("explicit_supported_primitive_family_required")

    points, points_error = selected_points(request)
    if points_error or points is None:
        return blocked(points_error or "points")

    dimensions, translate = dimensions_for_family(str(family), points)
    evidence, within_tolerance = dimension_evidence(request, dimensions)
    if not within_tolerance:
        return blocked(
            "dimension_anchor_mismatch",
            primitive_family=family,
            fitted_dimensions_mm=dimensions,
            dimension_evidence=evidence,
        )

    if family == "box_axis_aligned":
        part = {
            "id": "reverse_engineered_body",
            "kind": "box",
            "dimensions": dimensions,
            "translate_mm": translate,
            "operation": "add",
            "parent": None,
            "source": "reverse-engineering-fit",
        }
    else:
        part = {
            "id": "reverse_engineered_body",
            "kind": "cylinder",
            "dimensions": dimensions,
            "translate_mm": translate,
            "operation": "add",
            "parent": None,
            "source": "reverse-engineering-fit",
        }

    result = {
        "schema": "velvetos.ai3d.reverse-engineering-result.v1",
        "status": "PASS",
        "fit_kind": "explicit_primitive",
        "primitive_family": family,
        "segment_ref": request["segment_ref"],
        "measurement_basis": request["measurement_basis"],
        "source_units": "mm",
        "selected_point_count": len(points),
        "fitted_dimensions_mm": dimensions,
        "translate_mm": translate,
        "dimension_evidence": evidence,
        "geometry_ir": {
            "schema": "velvetos.geometry-ir.v1",
            "units": "mm",
            "parts": [part],
            "constraints": [],
        },
        "semantic_feature_recognition": False,
        "hidden_dimension_inference": False,
        "manufacturing_authority": False,
        "next_authority": "packages/vfprod/FABRICATION-ROUTER.md",
    }
    return result, True


def fit_nurbs_surface(request: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    common_error = validate_common(request)
    if common_error:
        return blocked(common_error)

    if request.get("fit_kind") != "nurbs_surface_grid":
        return blocked("fit_kind_must_be_nurbs_surface_grid")

    try:
        from geomdl import fitting
    except ImportError:
        return blocked("geomdl_runtime_unavailable")

    points = request.get("points")
    size_u = request.get("size_u")
    size_v = request.get("size_v")
    degree_u = request.get("degree_u", 3)
    degree_v = request.get("degree_v", 3)
    ctrlpts_size_u = request.get("ctrlpts_size_u")
    ctrlpts_size_v = request.get("ctrlpts_size_v")

    if not isinstance(size_u, int) or not isinstance(size_v, int) or size_u < 4 or size_v < 4:
        return blocked("invalid_surface_grid_size")
    if not isinstance(points, list) or len(points) != size_u * size_v:
        return blocked("surface_point_count_mismatch")
    normalized: list[list[float]] = []
    for point in points:
        if (
            not isinstance(point, list)
            or len(point) != 3
            or not all(_number(value) for value in point)
        ):
            return blocked("invalid_surface_point")
        normalized.append([float(value) for value in point])

    if not isinstance(degree_u, int) or not isinstance(degree_v, int):
        return blocked("invalid_surface_degree")
    kwargs: dict[str, Any] = {}
    if ctrlpts_size_u is not None:
        if not isinstance(ctrlpts_size_u, int):
            return blocked("invalid_ctrlpts_size_u")
        kwargs["ctrlpts_size_u"] = ctrlpts_size_u
    if ctrlpts_size_v is not None:
        if not isinstance(ctrlpts_size_v, int):
            return blocked("invalid_ctrlpts_size_v")
        kwargs["ctrlpts_size_v"] = ctrlpts_size_v

    try:
        surface = fitting.approximate_surface(
            normalized,
            size_u,
            size_v,
            degree_u,
            degree_v,
            **kwargs,
        )
    except Exception as exc:
        return blocked("nurbs_fit_failed", detail=str(exc))

    surface.sample_size = int(request.get("sample_size", 35))
    evaluated = [[float(value) for value in point] for point in surface.evalpts]
    if not evaluated:
        return blocked("nurbs_evaluation_empty")

    # Nearest sampled surface-point discrepancy. This is evidence quality only,
    # not a substitute for a CAD tolerance contract.
    squared_errors = []
    for source in normalized:
        nearest = min(
            (source[0] - point[0]) ** 2
            + (source[1] - point[1]) ** 2
            + (source[2] - point[2]) ** 2
            for point in evaluated
        )
        squared_errors.append(nearest)
    rms = math.sqrt(statistics.fmean(squared_errors))
    max_error = math.sqrt(max(squared_errors))

    threshold = request.get("max_fit_error_mm")
    if not _number(threshold) or float(threshold) <= 0:
        return blocked("max_fit_error_mm_required")
    fit_within = max_error <= float(threshold)

    result = {
        "schema": "velvetos.ai3d.reverse-engineering-result.v1",
        "status": "PASS" if fit_within else "BLOCKED",
        "reason": None if fit_within else "nurbs_fit_error_exceeded",
        "fit_kind": "nurbs_surface_grid",
        "measurement_basis": request["measurement_basis"],
        "source_units": "mm",
        "source_point_count": len(normalized),
        "degree_u": int(surface.degree_u),
        "degree_v": int(surface.degree_v),
        "ctrlpts_size_u": int(surface.ctrlpts_size_u),
        "ctrlpts_size_v": int(surface.ctrlpts_size_v),
        "control_points": [[float(value) for value in point] for point in surface.ctrlpts],
        "knotvector_u": [float(value) for value in surface.knotvector_u],
        "knotvector_v": [float(value) for value in surface.knotvector_v],
        "sampled_surface_point_count": len(evaluated),
        "fit_error_mm": {
            "rms_nearest_sample": rms,
            "max_nearest_sample": max_error,
            "threshold": float(threshold),
        },
        "surface_role": "reconstruction_evidence",
        "manufacturing_authority": False,
        "cad_conversion_requires_separate_contract": True,
        "hidden_dimension_inference": False,
    }
    return result, fit_within


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    commands = root.add_subparsers(dest="cmd", required=True)

    command = commands.add_parser("fit-primitive")
    command.add_argument("--input", type=Path, required=True)
    command.add_argument("--output", type=Path)

    command = commands.add_parser("fit-nurbs-surface")
    command.add_argument("--input", type=Path, required=True)
    command.add_argument("--output", type=Path)

    return root


def main() -> int:
    args = parser().parse_args()
    request = load(args.input)
    if args.cmd == "fit-primitive":
        result, ok = fit_primitive(request)
    elif args.cmd == "fit-nurbs-surface":
        result, ok = fit_nurbs_surface(request)
    else:
        raise AssertionError(args.cmd)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(result, indent=2) + "\n")
    return emit(result, 0 if ok else 2)


if __name__ == "__main__":
    raise SystemExit(main())
