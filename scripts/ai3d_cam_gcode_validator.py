#!/usr/bin/env python3
"""Strict offline verification of bounded 2-pass synthetic GRBL toolpaths.

This parser interprets only a deliberately tiny GRBL subset; unrecognized
operations are blocked, never silently ignored. It never talks to a machine.
"""
from __future__ import annotations
import argparse
import json
import math
import pathlib
import re
from typing import Any

TOKEN = re.compile(r"([A-Z])([-+]?(?:\d+(?:\.\d*)?|\.\d+))")
COMMENT = re.compile(r"\([^()\r\n]*\)")


def verify_text(gcode: str, fixture: dict[str,Any]) -> dict[str,Any]:
    geometry=fixture["geometry"]
    process=fixture["process"]
    expected_x=float(geometry["width_mm"])/2+float(fixture["tool"]["diameter_mm"])/2
    expected_y=float(geometry["height_mm"])/2+float(fixture["tool"]["diameter_mm"])/2
    max_safe=float(process["rapid_clearance_mm"])
    minimum_depth=-float(process["depth_mm"])
    expected_depths={-1.0,-2.0}
    errors=[]
    if len(gcode.encode("utf-8"))<100 or "\0" in gcode:
        errors.append("nonempty plain text G-code required")
    state={
        "absolute":False,"metric":False,"xy_plane":False,"spindle":False,
        "ended":False,"mode":None,"x":None,"y":None,"z":None,
        "feed":None,"rpm":None,
    }
    found_codes={"G":set(),"M":set()}
    xyz={"x":[],"y":[],"z":[]}
    feeds=[]
    plunges=set()
    motion=0
    cut_move=0
    rapid=0
    spindle_start=0
    spindle_stop=0
    program_end=0
    after_end_commands=0
    unsafe_rapids=0
    program_line_count=0

    for line_no,raw in enumerate(gcode.splitlines(),1):
        code=COMMENT.sub("",raw).split(";",1)[0].upper().strip()
        if not code:
            continue
        program_line_count+=1
        parsed=list(TOKEN.finditer(code))
        residue=TOKEN.sub("",code).strip()
        if residue or not parsed:
            errors.append(f"line {line_no}: unknown token/executable text {residue[:45]}")
            continue
        if state["ended"]:
            after_end_commands+=1
            errors.append(f"line {line_no}: command after program end")
            continue
        tokens={}
        for m in parsed:
            name=m.group(1)
            value=float(m.group(2))
            if name not in {"G","M","X","Y","Z","F","S"} or not math.isfinite(value):
                errors.append(f"line {line_no}: forbidden address {name}")
                continue
            tokens.setdefault(name,[]).append(value)

        for value in tokens.get("G",[]):
            if int(value)!=value or int(value) not in {0,1,17,21,90}:
                errors.append(f"line {line_no}: forbidden G{value:g}")
                continue
            g=int(value)
            found_codes["G"].add(g)
            if g==17:
                state["xy_plane"]=True
            elif g==21:
                state["metric"]=True
            elif g==90:
                state["absolute"]=True
            else:
                state["mode"]=g

        for value in tokens.get("M",[]):
            if int(value)!=value or int(value) not in {2,3,5,30}:
                errors.append(f"line {line_no}: forbidden M{value:g}")
                continue
            m=int(value)
            found_codes["M"].add(m)
            if m==3:
                spindle_start+=1
                if not state["metric"] or not state["absolute"]:
                    errors.append(f"line {line_no}: spindle before declared mode")
                state["spindle"]=True
            elif m==5:
                spindle_stop+=1
                state["spindle"]=False
            elif m in (2,30):
                program_end+=1
                if state["spindle"]:
                    errors.append(f"line {line_no}: program ended without M5")
                state["ended"]=True

        for name, values in tokens.items():
            if name in {"X","Y","Z","F","S"} and len(values)!=1:
                errors.append(f"line {line_no}: repeated {name} address")

        if "S" in tokens:
            s=tokens["S"][-1]
            state["rpm"]=s
            if s!=float(process["spindle_rpm"]):
                errors.append(f"line {line_no}: forbidden spindle reference rpm")
        if "F" in tokens:
            f=tokens["F"][-1]
            state["feed"]=f
            feeds.append(f)
            if not any(abs(f-v)<=0.02 for v in (float(process["feed_mm_min"]),float(process["plunge_mm_min"]))):
                errors.append(f"line {line_no}: feed beyond approved synthetic profile")

        coords={k:tokens[k][-1] for k in ("X","Y","Z") if k in tokens}
        if not coords and state["mode"] not in (0,1):
            continue
        if not coords:
            continue
        if state["mode"] not in (0,1):
            errors.append(f"line {line_no}: coordinates without modal motion")
            continue
        if not all(state[k] for k in ("metric","absolute","xy_plane")):
            errors.append(f"line {line_no}: G17 G21 G90 required before motion")
        if not state["spindle"]:
            errors.append(f"line {line_no}: motion while spindle disabled in fixture")
        for key,val in coords.items():
            state[key.lower()]=val
        for key in xyz:
            value=state[key]
            if value is not None:
                xyz[key].append(value)
        motion+=1
        x=state["x"]; y=state["y"]; z=state["z"]
        if x is not None and abs(x)>expected_x+0.15:
            errors.append(f"line {line_no}: X out of reference contour")
        if y is not None and abs(y)>expected_y+0.15:
            errors.append(f"line {line_no}: Y out of reference contour")
        if z is not None and (z>max_safe+0.02 or z<minimum_depth-0.02):
            errors.append(f"line {line_no}: Z beyond safe/negative depth")
        if state["mode"]==0:
            rapid+=1
            if z is not None and z<0:
                unsafe_rapids+=1
                errors.append(f"line {line_no}: rapid motion below stock top Z0")
        else:
            if z is not None and z<0:
                plunges.add(round(z,3))
            if (x is not None or y is not None) and z is not None and z<0:
                cut_move+=1
            if state["feed"] is None:
                errors.append(f"line {line_no}: feed not defined")
    bounds={key:[min(values),max(values)] if values else None for key,values in xyz.items()}
    if not state["ended"] or program_end!=1:
        errors.append("must have exactly one program terminator M2/M30")
    if spindle_start!=1 or spindle_stop!=1:
        errors.append("exactly one M3 and one safety M5 required")
    if not found_codes["G"].issuperset({0,1,17,21,90}):
        errors.append("missing required metric absolute XY contour modes")
    if not bounds["x"] or not bounds["y"] or not bounds["z"]:
        errors.append("missing XYZ envelope")
    else:
        for index,limit in ((0,-expected_x),(1,expected_x)):
            if abs(bounds["x"][index]-limit)>0.15:
                errors.append("XY outer X envelope not reached")
        for index,limit in ((0,-expected_y),(1,expected_y)):
            if abs(bounds["y"][index]-limit)>0.15:
                errors.append("XY outer Y envelope not reached")
        if abs(bounds["z"][0]-minimum_depth)>0.02 or abs(bounds["z"][1]-max_safe)>0.02:
            errors.append("unexpected plunge or clearance depth")
    if not expected_depths.issubset(plunges):
        errors.append("both -1mm and -2mm depth passes required")
    if motion<12 or cut_move<9 or rapid<2:
        errors.append("insufficient contour, cutting or safe rapid moves")
    if not any(abs(f-5)<0.02 for f in feeds) or not any(abs(f-10)<0.02 for f in feeds):
        errors.append("required fixture feed/plunge speeds not observed")
    if unsafe_rapids or after_end_commands:
        errors.append("unsafe rapid or trailing command")
    return {
        "schema":"velvetos.ai3d.phase12-grbl-validation.v1",
        "status":"PASS" if not errors else "BLOCKED",
        "errors":errors,
        "metric_absolute_xy":all(state[k] for k in ("metric","absolute","xy_plane")),
        "g_codes":sorted(found_codes["G"]),
        "m_codes":sorted(found_codes["M"]),
        "bounds_mm":bounds,
        "motion_count":motion,
        "contour_motion_count":cut_move,
        "safe_rapids":rapid,
        "depths_mm":sorted(plunges),
        "feeds_mm_min":sorted(set(feeds)),
        "spindle_start_count":spindle_start,
        "spindle_stop_count":spindle_stop,
        "program_end_count":program_end,
        "no_machine_control":True,
    }


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=pathlib.Path)
    p.add_argument("--fixture",required=True,type=pathlib.Path)
    args=p.parse_args()
    fixture=json.loads(args.fixture.read_text(encoding="utf-8-sig"))
    result=verify_text(args.input.read_text(encoding="utf-8",errors="replace"),fixture)
    print(json.dumps(result,indent=2))
    return 0 if result["status"]=="PASS" else 2


if __name__=="__main__":
    raise SystemExit(main())
