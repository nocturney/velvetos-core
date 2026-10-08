#!/usr/bin/env python3
"""Strict, synthetic-only Phase12 CAM fixture admission.

No machine, spindle, laser, printer or G-code execution is provided here.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from typing import Any


def _number(v: Any, lower: float, upper: float) -> bool:
    return type(v) in (float, int) and math.isfinite(float(v)) and lower <= float(v) <= upper


def errors(case: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    def need(value: bool, reason: str) -> None:
        if not value:
            failures.append(reason)

    need(case.get("schema") == "velvetos.ai3d.cam.fixture.v1", "unrecognized_schema")
    need(case.get("purpose") == "synthetic-offline-reference-only", "production_input_not_authorized")
    need(bool(case.get("fixture_id")), "fixture_id_missing")
    need(case.get("units") == {"length": "mm", "feed": "mm/min", "spindle": "rpm"}, "units_not_mm_mm_min_rpm")
    geom = case.get("geometry") or {}
    need(geom.get("type") == "rectangle", "unsupported_geometry")
    need(_number(geom.get("width_mm"), 10, 300), "invalid_width")
    need(_number(geom.get("height_mm"), 10, 300), "invalid_height")
    need(geom.get("source") == "explicit-synthetic-test-dimensions", "geometry_source_unqualified")
    need(geom.get("origin_xy_mm") == [0, 0], "coordinate_origin_mismatch")
    need(geom.get("stock_top_z_mm") == 0, "stock_top_not_zero")
    tool = case.get("tool") or {}
    need(tool.get("kind") == "flat_end_mill", "unsupported_tool")
    need(tool.get("diameter_mm") == 3, "tool_diameter_mismatch")
    need(tool.get("source") == "explicit-synthetic-tool-reference", "tool_source_missing")
    process = case.get("process") or {}
    need(process.get("kind") == "external_contour", "unsupported_process")
    for field, fixed in (
        ("depth_mm", 2), ("stepdown_mm", 1), ("feed_mm_min", 10),
        ("plunge_mm_min", 5), ("rapid_clearance_mm", 5), ("spindle_rpm", 12000)
    ):
        need(type(process.get(field)) in (float, int) and process.get(field) == fixed,
             f"unsupported_{field}")
    need(process.get("source") == "synthetic-fixture-only-not-calibrated", "unsupported_process_source")
    material = case.get("material") or {}
    need(material.get("designation") == "SYNTHETIC_UNQUALIFIED", "real_material_requires_engineering_review")
    need(material.get("source") == "explicit-synthetic-reference", "material_source_missing")
    need(material.get("machining_parameters_qualified") is False, "material_qualified_without_evidence")
    machine = case.get("machine") or {}
    need(machine.get("name") == "NON_CONNECTED_SYNTHETIC_GRBL", "physical_machine_forbidden")
    need(machine.get("control") is False, "machine_control_forbidden")
    need(machine.get("verified_motion_envelope") is False, "machine_envelope_not_qualified_here")
    need(case.get("postprocessor") == "FreeCAD.CAM.GRBL", "postprocessor_not_grbl")
    need(case.get("profile") == "rect_cutout_grbl_v1", "profile_unknown")
    safety = case.get("safety") or {}
    need(safety.get("write_gcode_file_only") is True, "offline_output_only")
    need(safety.get("source_toolpath_not_certified") is True, "uncertified_path_must_remain_uncertified")
    for key in (
        "external_execution_allowed", "printer_actions_allowed",
        "machine_control_allowed", "laser_activation_allowed"
    ):
        need(safety.get(key) is False, f"safety_{key}_must_be_false")
    return failures


def validate(path: Path) -> dict[str, Any]:
    case=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(case, dict):
        raise ValueError("input must be object")
    failures=errors(case)
    if failures:
        raise ValueError("CAM request BLOCKED: "+",".join(failures))
    return case


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--case",type=Path,required=True)
    args=p.parse_args()
    try:
        case=validate(args.case)
    except (ValueError,FileNotFoundError) as exc:
        print(json.dumps({"status":"BLOCKED","error":str(exc)}))
        return 2
    print(json.dumps({"status":"PASS","fixture_id":case["fixture_id"],
                      "purpose":case["purpose"],"machine_control":False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
