#!/usr/bin/env python3
"""Bounded mechanical feature-pack wrapper for the canonical build123d runtime.

Run with the build123d venv Python. Mature upstream bd_warehouse primitives are
wrapped, not copied. Process-sensitive features stay absent until promoted.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any, Callable

from build123d import Align, Box, Cylinder, Location, export_step, export_stl
from bd_warehouse.bearing import SingleRowDeepGrooveBallBearing
from bd_warehouse.fastener import (
    HeatSetNut,
    HexNut,
    PlainWasher,
    SocketHeadCapScrew,
)
from bd_warehouse.gear import SpurGear
from bd_warehouse.thread import IsoThread


def emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


def positive(params: dict[str, Any], name: str) -> float:
    value = params.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{name} must be a positive number")
    return float(value)


def nonnegative(params: dict[str, Any], name: str) -> float:
    value = params.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"{name} must be a non-negative number")
    return float(value)


def integer_at_least(params: dict[str, Any], name: str, minimum: int) -> int:
    value = params.get(name)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def required_string(params: dict[str, Any], name: str) -> str:
    value = params.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def ensure_member(value: str, values: set[str] | list[str], label: str) -> str:
    if value not in values:
        raise ValueError(f"unsupported {label}: {value}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def vec(value: Any) -> list[float]:
    return [float(value.X), float(value.Y), float(value.Z)]


def shape_metrics(shape: Any) -> dict[str, Any]:
    box = shape.bounding_box()
    return {
        "type": type(shape).__name__,
        "bbox_min": vec(box.min),
        "bbox_max": vec(box.max),
        "bbox_size": vec(box.size),
        "volume": float(shape.volume),
        "area": float(shape.area),
    }


def socket_head_cap_screw(params: dict[str, Any]) -> Any:
    standard = params.get("standard", "iso4762")
    ensure_member(standard, {"iso4762", "asme_b18.3"}, "fastener standard")
    size = required_string(params, "size")
    if size not in SocketHeadCapScrew.sizes(standard):
        raise ValueError(f"unsupported socket-head size for {standard}: {size}")
    length = positive(params, "length_mm")
    simple = bool(params.get("simple", True))
    return SocketHeadCapScrew(size, length, standard, simple=simple)


def hex_nut(params: dict[str, Any]) -> Any:
    standard = params.get("standard", "iso4032")
    ensure_member(standard, {"iso4032", "iso4033", "iso4035"}, "nut standard")
    size = required_string(params, "size")
    if size not in HexNut.sizes(standard):
        raise ValueError(f"unsupported hex-nut size for {standard}: {size}")
    return HexNut(size, standard, simple=bool(params.get("simple", True)))


def plain_washer(params: dict[str, Any]) -> Any:
    standard = params.get("standard", "iso7089")
    ensure_member(
        standard,
        {"iso7089", "iso7091", "iso7093", "iso7094"},
        "washer standard",
    )
    size = required_string(params, "size")
    if size not in PlainWasher.sizes(standard):
        raise ValueError(f"unsupported washer size for {standard}: {size}")
    return PlainWasher(size, standard)


def iso_thread(params: dict[str, Any]) -> Any:
    major = positive(params, "major_diameter_mm")
    pitch = positive(params, "pitch_mm")
    length = positive(params, "length_mm")
    interference = nonnegative(params, "interference_mm")
    simple = bool(params.get("simple", False))
    if simple:
        raise ValueError(
            "simple=true is metadata/simplified upstream output and is not accepted as solid thread geometry"
        )
    return IsoThread(
        major,
        pitch,
        length,
        external=bool(params.get("external", True)),
        hand=ensure_member(params.get("hand", "right"), {"right", "left"}, "thread hand"),
        interference=interference,
        simple=False,
    )


def spur_gear(params: dict[str, Any]) -> Any:
    module = positive(params, "module_mm")
    teeth = integer_at_least(params, "tooth_count", 6)
    pressure = positive(params, "pressure_angle_deg")
    if pressure >= 45:
        raise ValueError("pressure_angle_deg must be < 45")
    thickness = positive(params, "thickness_mm")
    return SpurGear(module, teeth, pressure, thickness)


def deep_groove_bearing(params: dict[str, Any]) -> Any:
    bearing_type = params.get("bearing_type", "SKT")
    ensure_member(bearing_type, SingleRowDeepGrooveBallBearing.types(), "bearing type")
    size = required_string(params, "size")
    if size not in SingleRowDeepGrooveBallBearing.sizes(bearing_type):
        raise ValueError(f"unsupported bearing size for {bearing_type}: {size}")
    return SingleRowDeepGrooveBallBearing(size, bearing_type)


def heat_set_insert(params: dict[str, Any]) -> Any:
    fastener_type = params.get("fastener_type", "McMaster-Carr")
    ensure_member(fastener_type, HeatSetNut.types(), "heat-set provider")
    size = required_string(params, "size")
    if size not in HeatSetNut.sizes(fastener_type):
        raise ValueError(f"unsupported heat-set size for {fastener_type}: {size}")
    return HeatSetNut(size, fastener_type, simple=bool(params.get("simple", True)))


def magnet_cylindrical_pocket(params: dict[str, Any]) -> Any:
    diameter = positive(params, "magnet_diameter_mm")
    height = positive(params, "magnet_height_mm")
    radial = nonnegative(params, "radial_clearance_mm")
    axial = nonnegative(params, "axial_clearance_mm")
    pocket_diameter = diameter + 2.0 * radial
    pocket_height = height + axial
    return Cylinder(
        pocket_diameter / 2.0,
        pocket_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )


def fit_clearance_cylindrical(params: dict[str, Any]) -> dict[str, Any]:
    shaft = positive(params, "shaft_diameter_mm")
    radial = nonnegative(params, "radial_clearance_mm")
    return {
        "shaft_diameter_mm": shaft,
        "radial_clearance_mm": radial,
        "hole_diameter_mm": shaft + 2.0 * radial,
        "diametral_clearance_mm": 2.0 * radial,
    }


def fit_interference_cylindrical(params: dict[str, Any]) -> dict[str, Any]:
    hole = positive(params, "hole_diameter_mm")
    radial = nonnegative(params, "radial_interference_mm")
    return {
        "hole_diameter_mm": hole,
        "radial_interference_mm": radial,
        "shaft_diameter_mm": hole + 2.0 * radial,
        "diametral_interference_mm": 2.0 * radial,
    }


def enclosure_rect_open_top(params: dict[str, Any]) -> Any:
    x = positive(params, "outer_x_mm")
    y = positive(params, "outer_y_mm")
    z = positive(params, "outer_z_mm")
    wall = positive(params, "wall_mm")
    floor = positive(params, "floor_mm")
    if 2.0 * wall >= min(x, y):
        raise ValueError("wall_mm leaves no interior cavity")
    if floor >= z:
        raise ValueError("floor_mm must be less than outer_z_mm")

    outer = Box(x, y, z, align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner_x = x - 2.0 * wall
    inner_y = y - 2.0 * wall
    inner_height = z - floor + 1.0
    inner = Box(
        inner_x,
        inner_y,
        inner_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).move(Location((0, 0, floor)))
    return outer - inner


SHAPE_FEATURES: dict[str, Callable[[dict[str, Any]], Any]] = {
    "fastener.socket_head_cap_screw": socket_head_cap_screw,
    "fastener.hex_nut": hex_nut,
    "fastener.plain_washer": plain_washer,
    "thread.iso": iso_thread,
    "gear.spur": spur_gear,
    "bearing.deep_groove": deep_groove_bearing,
    "insert.heat_set": heat_set_insert,
    "magnet.cylindrical_pocket": magnet_cylindrical_pocket,
    "enclosure.rect_open_top": enclosure_rect_open_top,
}
CALC_FEATURES: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "fit.clearance_cylindrical": fit_clearance_cylindrical,
    "fit.interference_cylindrical": fit_interference_cylindrical,
}


def build_feature(feature_id: str, params: dict[str, Any], out_dir: Path | None) -> dict[str, Any]:
    common = {
        "schema": "velvetos.ai3d.mechanical-feature-result.v1",
        "status": "PASS",
        "feature_id": feature_id,
        "runtime": {
            "build123d": importlib.metadata.version("build123d"),
            "bd_warehouse": importlib.metadata.version("bd_warehouse"),
        },
        "printer_actions_allowed": False,
    }

    if feature_id in CALC_FEATURES:
        return {
            **common,
            "kind": "calculation",
            "params": params,
            "result": CALC_FEATURES[feature_id](params),
        }

    builder = SHAPE_FEATURES.get(feature_id)
    if builder is None:
        raise ValueError(f"feature is not promoted/executable: {feature_id}")
    if out_dir is None:
        raise ValueError("out-dir is required for geometry features")

    shape = builder(params)
    if not getattr(shape, "_wrapped", None):
        raise ValueError(f"feature produced no solid geometry: {feature_id}")
    out_dir.mkdir(parents=True, exist_ok=True)
    step = out_dir / "feature.step"
    stl = out_dir / "feature.stl"
    export_step(shape, step)
    export_stl(shape, stl)
    return {
        **common,
        "kind": "geometry",
        "params": params,
        "metrics": shape_metrics(shape),
        "artifacts": [
            {
                "format": "STEP",
                "path": str(step),
                "bytes": step.stat().st_size,
                "sha256": sha256(step),
            },
            {
                "format": "STL",
                "path": str(stl),
                "bytes": stl.stat().st_size,
                "sha256": sha256(stl),
            },
        ],
    }


def parse_params(args: argparse.Namespace) -> dict[str, Any]:
    if args.params_json:
        value = json.loads(args.params_json)
    elif args.params_file:
        value = json.loads(Path(args.params_file).read_text(encoding="utf-8-sig"))
    else:
        value = {}
    if not isinstance(value, dict):
        raise ValueError("params must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd", required=True)

    subs.add_parser("list")

    command = subs.add_parser("build")
    command.add_argument("--feature", required=True)
    source = command.add_mutually_exclusive_group()
    source.add_argument("--params-json")
    source.add_argument("--params-file")
    command.add_argument("--out-dir", type=Path)

    args = parser.parse_args()
    if args.cmd == "list":
        return emit(
            {
                "schema": "velvetos.ai3d.mechanical-feature-list.v1",
                "geometry_features": sorted(SHAPE_FEATURES),
                "calculation_features": sorted(CALC_FEATURES),
                "candidate_only": ["snap_fit", "living_hinge", "sheet_metal"],
                "printer_actions_allowed": False,
            }
        )

    try:
        params = parse_params(args)
        payload = build_feature(args.feature, params, args.out_dir)
        return emit(payload)
    except Exception as exc:
        return emit(
            {
                "schema": "velvetos.ai3d.mechanical-feature-result.v1",
                "status": "BLOCKED",
                "feature_id": args.feature,
                "reason": f"{type(exc).__name__}:{exc}",
                "printer_actions_allowed": False,
            },
            2,
        )


if __name__ == "__main__":
    raise SystemExit(main())
