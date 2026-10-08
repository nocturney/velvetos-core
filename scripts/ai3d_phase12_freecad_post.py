#!/usr/bin/env python3
"""Offline synthetic FreeCAD CAM/Path GRBL postprocessor proof.

Input: bounded synthetic fixture. Output: local .nc and receipt. No CNC machine
control, no laser, and no claim that synthetic contour is a qualified CAM job.
"""
from __future__ import annotations
import hashlib
import json
import os
import pathlib
import re
import sys
from typing import Any

import FreeCAD as App
import Path as FreeCADPath
from Path.Post.scripts import grbl_post

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from ai3d_cam_contract import validate  # noqa:E402


def sha256(path:pathlib.Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(case_path:pathlib.Path, out_dir:pathlib.Path)->dict[str,Any]:
    case=validate(case_path)
    repo_worktree = ROOT.resolve()
    if not (repo_worktree/"packages"/"vfprod"/"FABRICATION-ROUTER.json").is_file():
        raise RuntimeError("expected VelvetOS fabrication worktree")
    out_dir=out_dir.resolve()
    if not out_dir.is_relative_to(pathlib.Path(r"D:\Velvet\Artifacts\AI3D")):
        raise ValueError("refusing CAM output outside isolated D:/Velvet/Artifacts/AI3D")
    out_dir.mkdir(parents=True,exist_ok=False)
    output=out_dir/"synthetic-grbl-post.nc"
    report=out_dir/"synthetic-grbl-post.json"
    if output.exists() or report.exists():
        raise FileExistsError("refusing CAM artifact overwrite")

    geom=case["geometry"]
    process=case["process"]
    half_x=float(geom["width_mm"])/2+float(case["tool"]["diameter_mm"])/2
    half_y=float(geom["height_mm"])/2+float(case["tool"]["diameter_mm"])/2
    safe=float(process["rapid_clearance_mm"])
    step=float(process["stepdown_mm"])
    depth=float(process["depth_mm"])
    feed=float(process["feed_mm_min"])/60.0
    plunge=float(process["plunge_mm_min"])/60.0
    rpm=float(process["spindle_rpm"])

    # Exporter accepts feed in mm/s, unlike source contract (mm/min).
    # Fixed outline, two explicit passes. Path commands are waypoint evidence,
    # not FreeCAD stock-aware machining operations.
    commands=[
        FreeCADPath.Command("M3", {"S":rpm}),
        FreeCADPath.Command("G0", {"X":-half_x,"Y":-half_y,"Z":safe}),
    ]
    depths=[-step,-depth]
    for cut_z in depths:
        commands.append(FreeCADPath.Command("G1",{"X":-half_x,"Y":-half_y,"Z":cut_z,"F":plunge}))
        for x,y in ((half_x,-half_y),(half_x,half_y),(-half_x,half_y),(-half_x,-half_y)):
            commands.append(FreeCADPath.Command("G1",{"X":x,"Y":y,"Z":cut_z,"F":feed}))
        commands.append(FreeCADPath.Command("G0",{"Z":safe}))
    # grbl_post itself emits the safety M5 footer and final M2.
    # Do not insert a duplicate M5 into the user-level Path commands.

    doc=App.newDocument("AI3DPhase12CAMOffline")
    obj=doc.addObject("Path::Feature","SyntheticToolpath")
    obj.Label="Synthetic outline / not production qualified"
    obj.Path=FreeCADPath.Path(commands)
    grbl_post.export([obj],str(output),"--no-show-editor --no-comments")
    if not output.is_file() or output.stat().st_size<100:
        raise RuntimeError("real FreeCAD GRBL post yielded empty result")
    gcode=output.read_text(encoding="utf-8",errors="replace")
    if "G21" not in gcode or "G1" not in gcode:
        raise RuntimeError("missing metric or feed move in GRBL post output")

    evidence={
        "schema":"velvetos.ai3d.phase12-freecad-post-receipt.v1",
        "status":"PASS_POST_ONLY",
        "fixture_id":case["fixture_id"],
        "fixture_sha256":sha256(case_path),
        "path_command_count":len(commands),
        "depths_mm":depths,
        "reference_outline_xy_mm":[-half_x,half_x,-half_y,half_y],
        "source_feed_mm_min":float(process["feed_mm_min"]),
        "path_internal_feed_mm_sec":feed,
        "source_plunge_mm_min":float(process["plunge_mm_min"]),
        "path_internal_plunge_mm_sec":plunge,
        "spindle_reference_rpm":rpm,
        "postprocessor":"Path.Post.scripts.grbl_post",
        "freecad_version":".".join(App.Version()[:3]),
        "gcode":{"name":output.name,"bytes":output.stat().st_size,"sha256":sha256(output)},
        "safety":{
            "machine_control":False,"spindle_control":False,"laser_activation":False,
            "printer_actions":False,"production_approval":False
        },
        "warning":"Post-processing only: no stock-aware cutting, collision, machine compatibility or material feed verification.",
    }
    report.write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    print("AI3D_PHASE12_FREECAD_POST",json.dumps({
        "status":evidence["status"],"commands":len(commands),
        "bytes":output.stat().st_size,"sha256":evidence["gcode"]["sha256"]
    }),flush=True)
    return evidence


def main()->int:
    case=os.environ.get("AI3D_PHASE12_CASE")
    out_dir=os.environ.get("AI3D_PHASE12_OUT_DIR")
    if not case or not out_dir:
        raise RuntimeError("FreeCADCmd requires explicit Phase12 fixture/output environment")
    run(pathlib.Path(case).resolve(),pathlib.Path(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
