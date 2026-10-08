#!/usr/bin/env python3
"""Phase 12 regression: CAM typed provider reuse + bounded FreeCAD GRBL post.

Synthetic G-code only. No physical CNC/laser/printer controls, no automatic
manufacturing release, and no process calibration or machine-compatibility claim.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
from typing import Any

ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/"docs"/"implementation"/"ai-3d-modeling-engineering-core"
CONTRACT=BASE/"cam-toolpath-v1.json"
FIXTURE=BASE/"fixtures"/"phase12"/"rect-outline.json"
REPORT=BASE/"evidence"/"phase12-cam-acceptance-20261008.json"
DRIVER=ROOT/"scripts"/"ai3d_phase12_freecad_post.py"
FREECAD=pathlib.Path(r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe")
EXTERNAL=pathlib.Path(r"D:\Velvet\BlenderStack\tests\cross_station_cam_toolpath.gcode")
EXTERNAL_REPORT=pathlib.Path(r"D:\Velvet\BlenderStack\tests\cross_station_cam_toolpath_report.json")
PROBE=pathlib.Path(r"D:\Velvet\Runtime\CreativeCraft\CncGcodeProbe.py")
STATION_ROUTING=pathlib.Path(r"D:\Velvet\State\CreativeCraft\blender-station-routing.json")
REGISTRY=ROOT/"docs"/"implementation"/"ai-3d-modeling-engineering-core"/"cad-capability-registry-v1.json"

sys.path.insert(0,str(ROOT/"scripts"))
from ai3d_cam_contract import errors,validate  # noqa:E402
from ai3d_cam_gcode_validator import verify_text  # noqa:E402


def load(path:pathlib.Path)->dict[str,Any]:
    obj=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj,dict):
        raise AssertionError(f"expected JSON object: {path}")
    return obj


def sha(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def receipt(path:pathlib.Path)->dict[str,Any]:
    assert path.is_file() and path.stat().st_size>100,path
    return {"name":path.name,"bytes":path.stat().st_size,"sha256":sha(path)}


def case_negative_controls(case:dict[str,Any])->dict[str,str]:
    variants={}
    def variant(name:str, section:str|None, key:str, value:Any)->None:
        candidate=copy.deepcopy(case)
        if section:
            candidate[section][key]=value
        else:
            candidate[key]=value
        variants[name]=candidate
    variant("production_scope",None,"purpose","real-production")
    variant("unsupported_units","units","length","in")
    variant("oversize_stock","geometry","width_mm",301)
    variant("missing_dimension","geometry","height_mm",None)
    variant("wrong_origin","geometry","origin_xy_mm",[20,0])
    variant("unknown_tool","tool","diameter_mm",6)
    variant("excessive_cut_depth","process","depth_mm",12)
    variant("arbitrary_feed","process","feed_mm_min",2000)
    variant("arbitrary_spindle","process","spindle_rpm",24000)
    variant("real_material_without_qualification","material","designation","Aluminium-6061")
    variant("false_material_qualification","material","machining_parameters_qualified",True)
    variant("connected_machine","machine","control",True)
    variant("unsupported_postprocessor",None,"postprocessor","linuxcnc")
    variant("upload_or_machine_execution","safety","external_execution_allowed",True)
    variant("printer_control","safety","printer_actions_allowed",True)
    for name,case2 in variants.items():
        assert errors(case2),f"invalid case passed preflight: {name}"
    assert not errors(case),"canonical explicit case failed preflight"
    return {name:"BLOCKED" for name in variants}


def gcode_negative_controls(gcode:str,case:dict[str,Any])->dict[str,str]:
    # These mutated strings are in-memory only and never become machine files.
    mutations={
        "inch_mode":gcode.replace("G21","G20",1),
        "relative_mode":gcode.replace("G17 G90","G17 G91",1),
        "outside_xy":gcode.replace("X21.500","X999.000",1),
        "plunge_too_deep":gcode.replace("Z-2.000","Z-9.000",1),
        "arbitrary_feed":gcode.replace("F10.000","F1000.000",1),
        "arbitrary_spindle_rpm":gcode.replace("S12000","S30000",1),
        "laser_spindle_reverse":gcode.replace("M3 S12000","M4 S12000",1),
        "missing_spindle_start":gcode.replace("M3 S12000","",1),
        "missing_spindle_stop":gcode.replace("\nM5\n","\n",1),
        "missing_end":gcode.replace("\nM2\n","\n",1),
        "rapid_below_stock":gcode.replace("G0 X-21.500","G0 Z-1.000\nG0 X-21.500",1),
        "trailing_unsafe_command":gcode+"\nG1 X999\n",
        "extruder_axis":gcode.replace("F10.000","F10.000 E2.0",1),
        "heater":gcode.replace("M3 S12000","M3 S12000\nM104 S210",1),
        "wrong_plane":gcode.replace("G17 G90","G18 G90",1),
        "incremental_zero_reset":gcode.replace("G21","G21\nG92 X0",1),
        "missing_units":gcode.replace("G21","",1),
        "unexpected_axis":gcode.replace("G21","G21\nG0 A20",1),
    }
    for name,changed in mutations.items():
        assert changed!=gcode, f"mutation could not be inserted: {name}"
        proof=verify_text(changed,case)
        assert proof["status"]=="BLOCKED" and proof["errors"],(name,proof)
    assert verify_text(gcode,case)["status"]=="PASS"
    return {key:"BLOCKED" for key in mutations}


def run_existing_fabex(case:dict[str,Any])->dict[str,Any]:
    sources=[EXTERNAL,EXTERNAL_REPORT,PROBE,STATION_ROUTING]
    for path in sources:
        assert path.is_file(),f"live existing provider evidence missing: {path}"
    current={str(path):sha(path) for path in sources}
    provider=load(EXTERNAL_REPORT)
    assert provider["status"]=="PASS"
    assert provider["typed_operation"]=="cam.toolpath"
    assert provider["profile"]=="rect_cutout_grbl_v1"
    artifact=provider["positive_job"]["artifact"]
    assert artifact["bytes"]==EXTERNAL.stat().st_size
    assert artifact["sha256"].casefold()==sha(EXTERNAL).casefold()
    assert provider["positive_job"]["local_validation"]["validator_independent"] is True
    assert provider["positive_job"]["remote_execution"]["runtime"]["contract"]["offline_generation_only"] is True
    assert provider["positive_job"]["remote_execution"]["runtime"]["contract"]["machine_execution_exposed"] is False
    route=load(STATION_ROUTING)["capability_routes"]["cam.toolpath"]
    assert route["provider"]=="mac_fabexcnc"
    assert route["fallback_provider"]=="fabexcnc"

    # Fresh Windows-side independent parsing of the persisted output and
    # provenance. Does not repeat the remote Mac side operation.
    proc=subprocess.run(
        [sys.executable,str(PROBE),"--input",str(EXTERNAL),
         "--width-mm",str(case["geometry"]["width_mm"]),
         "--height-mm",str(case["geometry"]["height_mm"])],
        capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=25)
    assert proc.returncode==0,proc.stdout[-2000:]+proc.stderr[-1000:]
    windows=json.loads(proc.stdout)
    assert windows["status"]=="PASS" and all(windows["checks"].values())
    parsed=verify_text(EXTERNAL.read_text(encoding="utf-8"),case)
    assert parsed["status"]=="PASS",parsed["errors"]

    after={str(path):sha(path) for path in sources}
    assert current==after,"existing CreativeCraft/Fabex evidence modified"
    return {
        "provenance":"existing-historical-cross-station-receipt-revalidated-locally",
        "historical_remote_proof_status":provider["status"],
        "existing_typed_route":"cam.toolpath",
        "route_prefers_mac":True,
        "source_artifact":receipt(EXTERNAL),
        "existing_windows_probe":"PASS",
        "fresh_strict_parser":parsed,
        "existing_source_sha256":current,
        "external_sources_unchanged":True,
    }


def run_freecad(case:dict[str,Any],root:pathlib.Path)->tuple[dict[str,Any],str]:
    assert FREECAD.is_file(),FREECAD
    launch=root/"launch-freecad.py"
    launch.write_text(
        "import runpy,sys\n"
        f"target={str(DRIVER)!r}\n"
        "sys.argv=[target]\n"
        "runpy.run_path(target,run_name='__main__')\n",
        encoding="utf-8",newline="\n")
    target=root/"freecad-post-output"
    assert not target.exists(),"refusing output overwrite"
    env=dict(__import__("os").environ)
    env["AI3D_PHASE12_CASE"]=str(FIXTURE)
    env["AI3D_PHASE12_OUT_DIR"]=str(target)
    proc=subprocess.run([str(FREECAD),str(launch)],cwd=ROOT,env=env,
       capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=90)
    output=(proc.stdout or "")+"\n"+(proc.stderr or "")
    assert "AI3D_PHASE12_FREECAD_POST" in output,output[-1800:]
    nc=target/"synthetic-grbl-post.nc"
    receipt_path=target/"synthetic-grbl-post.json"
    assert nc.is_file() and receipt_path.is_file(),"FreeCAD post missing output"
    ref=load(receipt_path)
    assert ref["status"]=="PASS_POST_ONLY"
    assert ref["fixture_sha256"]==sha(FIXTURE)
    assert ref["gcode"]["sha256"]==sha(nc)
    assert ref["gcode"]["bytes"]==nc.stat().st_size
    assert ref["freecad_version"]=="1.1.3"
    assert ref["path_command_count"]>=13
    assert all(value is False for value in ref["safety"].values())
    gcode=nc.read_text(encoding="utf-8",errors="replace")
    proof=verify_text(gcode,case)
    assert proof["status"]=="PASS",proof["errors"]
    return {"driver":ref,"strict_gcode":proof,"artifact":receipt(nc)},gcode


def acceptance(root:pathlib.Path,evidence_out:pathlib.Path)->dict[str,Any]:
    policy=load(CONTRACT)
    case=validate(FIXTURE)
    assert policy["schema"]=="velvetos.ai3d.cam-toolpath.v1"
    assert policy["non_authoritative_staging"] is True
    assert policy["authority"]=="packages/vfprod/FABRICATION-ROUTER.md"
    assert policy["existing_capability"]=="cam.toolpath"
    assert policy["toolpath_provider"]["reuse_not_duplicate"] is True
    assert policy["freecad_post"]["no_native_job_strategy_claim"] is True
    assert all(value is False for value in policy["safety"].values())

    case_negative=case_negative_controls(case)
    existing=run_existing_fabex(case)
    new,gcode=run_freecad(case,root)
    mutations=gcode_negative_controls(gcode,case)
    fabex=existing["fresh_strict_parser"]
    freecad=new["strict_gcode"]
    for axis in ("x","y","z"):
        a,b=fabex["bounds_mm"][axis],freecad["bounds_mm"][axis]
        assert len(a)==len(b)==2
        assert all(abs(x-y)<=0.15 for x,y in zip(a,b)),(axis,a,b)
    assert set(fabex["depths_mm"])==set(freecad["depths_mm"])=={-2,-1}
    assert fabex["feeds_mm_min"]==freecad["feeds_mm_min"]==[5,10]
    assert fabex["spindle_start_count"]==freecad["spindle_start_count"]==1
    assert fabex["spindle_stop_count"]==freecad["spindle_stop_count"]==1

    evidence={
        "schema":"velvetos.ai3d.phase12-cam-acceptance.v1",
        "status":"PASS_BOUNDED_OFFLINE",
        "fixture_id":case["fixture_id"],
        "fixture_sha256":sha(FIXTURE),
        "contract_sha256":sha(CONTRACT),
        "existing_provider":existing,
        "freecad_grbl_post":new,
        "cross_provider_compatibility":{
            "matched_bounds_within_mm":0.15,
            "matched_cut_depths_mm":[-2,-1],
            "matched_feedrates_mm_min":[5,10],
            "identical_spindle_start_stop_counts":True,
            "different_planners_or_contours_do_not_imply_equal_machining_quality":True,
        },
        "negative_controls":{"input_contract":case_negative,"gcode_dialect":mutations},
        "material_qualified":False,
        "physical_machine_validated":False,
        "production_gcode_authorized":False,
        "laser_machining_allowed":False,
        "spindle_hardware_control_allowed":False,
        "printer_actions_allowed":False,
        "new_cam_toolpath_router_added":False,
        "licenses":[
            "FreeCAD standalone LGPL external runtime; local postprocessor only",
            "Existing Fabex provider reused; redistribution and commercial deployment require independent license review",
        ],
        "artifact_dir":str(root),
        "limitations":[
            "Synthetic two-pass rectangular outline only, material unqualified",
            "FreeCAD path consists of explicit synthetic waypoints; not a generated stock-aware CAM machining operation",
            "Existing cross-station Fabex proof is historical but artifact hash and Windows-side validation were rechecked",
            "No tool-life, fixture/workholding, tool deflection, collisions, CNC firmware execution or real-machine motion is validated",
        ],
    }
    evidence_out.parent.mkdir(parents=True,exist_ok=True)
    with evidence_out.open("w",encoding="utf-8",newline="\n") as handle:
        handle.write(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(
        "validate_ai3d_phase12_cam: PASS "
        f"freecad_commands={new['driver']['path_command_count']} "
        f"provider=EXISTING_MAC_WIN_PROVEN "
        f"gcode_mutations_blocked={len(mutations)} "
        f"input_negative_controls={len(case_negative)} "
        "machine_control=DISABLED"
    )
    return evidence


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifacts-root",type=pathlib.Path)
    ap.add_argument("--evidence-out",type=pathlib.Path,default=REPORT)
    args=ap.parse_args()
    ctx=None
    if args.artifacts_root is None:
        ctx=tempfile.TemporaryDirectory(prefix="ai3d-phase12-")
        artifacts=pathlib.Path(ctx.name)
        # The FreeCAD driver intentionally only permits the D:/Velvet
        # isolated artifact lane, so validation requires an explicit root.
        raise ValueError("Phase12 requires --artifacts-root under D:/Velvet/Artifacts/AI3D")
    else:
        artifacts=args.artifacts_root.resolve()
        if not artifacts.is_relative_to(pathlib.Path(r"D:\Velvet\Artifacts\AI3D")):
            raise ValueError("Phase12 artifacts must stay under D:/Velvet/Artifacts/AI3D")
        if artifacts.exists():
            raise FileExistsError(f"refusing to overwrite Phase12 artifacts: {artifacts}")
        artifacts.mkdir(parents=True,exist_ok=False)
    acceptance(artifacts,args.evidence_out)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
