#!/usr/bin/env python3
"""Phase 14 offline-only printer profile proof and portable receipt checks.

This is not a machine-command audit or permission to print. The only executable
toolchain is the existing vf_cad.py -> installed OrcaSlicer CLI. This script
never connects to printers, alters native profiles, widens coordinates,
launches hardware or approves production jobs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import re
import sys
from typing import Any

ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/"docs"/"implementation"/"ai-3d-modeling-engineering-core"
CONFIG=BASE/"printer-profile-audit-v1.json"
DEFAULT_REPORT=BASE/"evidence"/"phase14-printer-profiles-acceptance-20261008.json"
P11_REPORT=BASE/"evidence"/"phase11-dfam-slicer-acceptance-20261008.json"
sys.path.insert(0,str(ROOT/"scripts"))
import validate_ai3d_phase11_dfam_slicer as p11  # noqa: E402


def sha(path:pathlib.Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt(path:pathlib.Path)->dict[str,Any]:
    assert path.is_file() and path.stat().st_size>100,(path, "missing or empty")
    return {"name":path.name,"bytes":path.stat().st_size,"sha256":sha(path)}


def config()->dict[str,Any]:
    c=p11.load_json(CONFIG)
    assert c["schema"]=="velvetos.ai3d.printer-profile-audit.v1"
    assert c["non_authoritative_staging"] is True
    assert c["authority"]=="packages/vfprod/FABRICATION-ROUTER.md"
    assert c["existing_slicer_authority"]=="scripts/vf_cad.py"
    assert c["scope"]["printers"]==["u1","ecc2","c5pro"]
    assert c["scope"]["inputs"]==["stl","3mf"]
    assert all(v is False for v in c["qualification"].values())
    assert all(v is False for v in c["prohibitions"].values())
    assert all(v is True for v in c["output_policy"].values())
    return c


def parent_source_profiles(paths:dict[str,pathlib.Path])->dict[str,str]:
    source={}
    # Matrix is read, never written. Generated wrappers are deterministically
    # recreated by the existing bridge; hash equality is checked afterward.
    root=pathlib.Path(paths["u1"]).parents[1]
    matrix_path=root/"printer_matrix.json"
    assert matrix_path.is_file(),matrix_path
    config=p11.load_json(matrix_path)
    assert all(config["safety"].get(k) is False for k in
               ("printer_network_control","upload","start_print","heating","motion"))
    source["printer_matrix.json"]=sha(matrix_path)
    for name in ("u1","ecc2","c5pro","h2d"):
        for f in p11.immutable_profile_sources(paths[name]):
            source[name+"/"+("wrapper.json" if f==paths[name] else f.name)]=sha(f)
    assert len(source)==1+4*4,source
    return source


def check_negative_motion(gcode:pathlib.Path,wrapper:pathlib.Path,scratch:pathlib.Path)->str:
    return p11.injected_out_of_bounds(gcode,wrapper,scratch)


def new_offline_capture(out_dir:pathlib.Path, evidence_out:pathlib.Path)->dict[str,Any]:
    c=config()
    # Do not allow accidental outside-artifact output, overwrite or mutation
    # of the source configuration / printer profile tree.
    if sys.platform!="win32":
        raise RuntimeError("real Orca provider capture requires the existing Windows host")
    root_base=pathlib.Path(r"D:\Velvet\Artifacts\AI3D").resolve()
    out_dir=out_dir.resolve()
    if not out_dir.is_relative_to(root_base):
        raise ValueError("artifacts must remain under D:/Velvet/Artifacts/AI3D")
    if out_dir.exists():
        raise FileExistsError("refusing Phase14 artifact overwrite")
    if evidence_out.resolve()==CONFIG.resolve():
        raise ValueError("cannot overwrite contract with evidence")

    profiles=p11.profiles()
    sources_before=parent_source_profiles(profiles)
    assert p11.load_json(P11_REPORT)["quarantined_profiles"]["h2d"]["status"]=="BLOCKED_MOTION_BOUNDS"
    ecc2_native=p11.load_json(pathlib.Path(p11.load_json(profiles["ecc2"])["native_config"]))
    h2d_native=p11.load_json(pathlib.Path(p11.load_json(profiles["h2d"])["native_config"]))
    assert "Y-1.2" in str(ecc2_native.get("machine_start_gcode") or ""),"ECC2 negative Y source drift"
    assert "G1 X270 Y-0.5 F60000" in str(h2d_native.get("machine_start_gcode") or ""),"H2D service source drift"

    out_dir.mkdir(parents=True,exist_ok=False)
    cad_dir=out_dir/"cad"
    build=p11.invoke([
        sys.executable,str(p11.CAD),"build","--input",str(p11.SOURCE),
        "--engine","build123d","--formats","step,stl,3mf",
        "--out-dir",str(cad_dir),
    ],timeout=90)
    built=json.loads(build.stdout)
    assert built["status"]=="PASS" and built["printer_actions_allowed"] is False
    assert set(built["artifacts"])=={"model.step","model.stl","model.3mf"}
    files={ext:cad_dir/("model."+ext) for ext in ("step","stl","3mf")}
    for path in files.values():
        assert path.is_file()
    sizes=list(c["expected"]["model_bounds_mm"])
    assert all(p11.fits_bed(sizes,p11.machine_limits(profiles[name]))
               for name in c["scope"]["printers"])
    for name in c["scope"]["printers"]:
        limits=p11.machine_limits(profiles[name])
        assert not p11.fits_bed([999,80,12],limits),name

    results={}
    for name in ("u1","ecc2","c5pro"):
        samples={}
        for fmt in ("stl","3mf"):
            target=out_dir/(name+"-"+fmt+".gcode")
            item=p11.slicer_call(files[fmt],name,target)
            header=p11.gcode_evidence(
                target,sizes[2],float(c["expected"]["max_height_delta_mm"])
            )
            assert header["reported_version"]=="2.4.2"
            assert header["reported_layer_count"]==c["expected"]["expected_layer_count"]
            assert item["slicer_returncode"]==0
            assert item["command_backend"]=="orcaslicer"
            assert item["stats"]["extrusion_moves"]>100
            assert item["stats"]["temperature_commands"]>0
            assert item["artifact"]["sha256"]==receipt(target)["sha256"]
            samples[fmt]={
                "slicer_returncode":item["slicer_returncode"],
                "canonical_bridge_returncode":item["bridge_returncode"],
                "bounds_validation_ok":item["validation_ok"],
                "bounds_errors":item["validation_errors"],
                "warnings":item["validation_warnings"],
                "stats":item["stats"],
                "header":header,
            }
        assert samples["stl"]["header"]["reported_layer_count"]==samples["3mf"]["header"]["reported_layer_count"]
        assert abs(samples["stl"]["header"]["reported_max_z_mm"] -
                   samples["3mf"]["header"]["reported_max_z_mm"])<=0.1

        warnings=[w for fmt in ("stl","3mf") for w in samples[fmt]["warnings"]]
        assert any("Unknown or unsupported commands" in w for w in warnings),(
            name,"expected vendor-specific dialect warning changed"
        )
        if name in ("u1","c5pro"):
            assert all(samples[fmt]["bounds_validation_ok"] is True
                       and not samples[fmt]["bounds_errors"]
                       and samples[fmt]["canonical_bridge_returncode"]==0
                       for fmt in ("stl","3mf")),name
            state="OFFLINE_GCODE_VERIFIED_DIALECT_REVIEW"
        else:
            assert all(samples[fmt]["bounds_validation_ok"] is False
                       and samples[fmt]["canonical_bridge_returncode"]!=0
                       and any("Y=-1.2" in e and "outside Y motion range" in e
                               for e in samples[fmt]["bounds_errors"])
                       for fmt in ("stl","3mf")),"ECC2 negative service move not blocked"
            state="BLOCKED_MOTION_BOUNDS"
        results[name]={
            "state":state,
            "firmware_command_set_audited":False,
            "manufacturing_qualified":False,
            "offline_slices":samples,
            "profile_limits":{k:v for k,v in p11.machine_limits(profiles[name]).items() if k!="native_config"},
        }
        print(f"PHASE14_PROFILE {name}={state} stl_layers={samples['stl']['header']['reported_layer_count']} 3mf_layers={samples['3mf']['header']['reported_layer_count']}",flush=True)

    negative={
        "direct_step_input":p11.unmeshable_step_blocked(
            files["step"],"u1",out_dir/"should-not-slice-step.gcode"
        ),
        "out_of_bed_geometry_all_three":"BLOCKED" if all(
            not p11.fits_bed([999,80,12],p11.machine_limits(profiles[name]))
            for name in ("u1","ecc2","c5pro")
        ) else "FAIL",
        "injected_out_of_bounds_u1":check_negative_motion(
            out_dir/"u1-stl.gcode",profiles["u1"],out_dir/"bad-u1.tmp.gcode"
        ),
        "injected_out_of_bounds_c5pro":check_negative_motion(
            out_dir/"c5pro-stl.gcode",profiles["c5pro"],out_dir/"bad-c5pro.tmp.gcode"
        ),
        "ecc2_y_negative_guard":"BLOCKED" if results["ecc2"]["state"]=="BLOCKED_MOTION_BOUNDS" else "FAIL",
        "h2d_remains_blocked":"BLOCKED",
    }
    for f in ("bad-u1.tmp.gcode","bad-c5pro.tmp.gcode"):
        (out_dir/f).unlink(missing_ok=True)
    sources_after=parent_source_profiles(profiles)
    assert sources_before==sources_after,"native profiles or wrappers modified"
    negative["native_profile_hash_unchanged"]="PASS_UNCHANGED"
    assert all(x=="BLOCKED" for k,x in negative.items() if k!="native_profile_hash_unchanged")

    proof={
        "schema":"velvetos.ai3d.phase14-printer-profiles-acceptance.v1",
        "status":"PASS_OFFLINE_AUDIT_WITH_EXPLICIT_BLOCKERS",
        "authority":c["authority"],
        "provider":"installed OrcaSlicer 2.4.2 via existing vf_cad.py",
        "non_authoritative_staging":True,
        "fixture_source_sha256":sha(p11.SOURCE),
        "input_geometry_mm":sizes,
        "input_artifacts":{ext:receipt(path) for ext,path in files.items()},
        "native_profile_hashes":sources_before,
        "native_profiles_unchanged":True,
        "profiles":results,
        "negative_controls":negative,
        "h2d_motion":"BLOCKED_MOTION_BOUNDS",
        "printer_actions_executed":False,
        "production_release_authorized":False,
        "machine_firmware_commands_verified":False,
        "licenses_review_required":True,
        "limitations":[
            "Orca CLI success and generic bounds acceptance do not certify vendor command execution",
            "U1 and C5 Pro emitted executable commands unrecognized by generic G-code validator",
            "ECC2 native G180 service move at Y=-1.2 is outside declared 0..256 mm Y envelope",
            "H2D native service Y=-0.5 still requires independent printer-specific envelope",
            "No network, firmware, live material or first-print verification",
        ],
    }
    verify_record(proof,c)
    evidence_out.parent.mkdir(parents=True,exist_ok=True)
    with evidence_out.open("w",encoding="utf-8",newline="\n") as f:
        f.write(json.dumps(proof,ensure_ascii=False,indent=2)+"\n")
    print("validate_ai3d_phase14_printer_profiles: PASS offline u1=candidate c5pro=candidate ecc2=BLOCKED h2d=BLOCKED profiles_unchanged=TRUE",flush=True)
    return proof


def verify_record(proof:dict[str,Any],contract:dict[str,Any])->None:
    assert proof["schema"]=="velvetos.ai3d.phase14-printer-profiles-acceptance.v1"
    assert proof["status"]=="PASS_OFFLINE_AUDIT_WITH_EXPLICIT_BLOCKERS"
    assert proof["authority"]==contract["authority"]
    assert proof["non_authoritative_staging"] is True
    assert proof["input_geometry_mm"]==contract["expected"]["model_bounds_mm"]
    assert proof["native_profiles_unchanged"] is True
    assert proof["printer_actions_executed"] is False
    assert proof["production_release_authorized"] is False
    assert proof["machine_firmware_commands_verified"] is False
    assert proof["licenses_review_required"] is True
    assert re.fullmatch(r"[0-9a-f]{64}",proof["fixture_source_sha256"])
    assert len(proof["native_profile_hashes"])==17
    assert all(re.fullmatch(r"[0-9a-f]{64}",h) for h in proof["native_profile_hashes"].values())
    assert set(proof["profiles"])==set(contract["scope"]["printers"])
    assert set(proof["input_artifacts"])=={"step","stl","3mf"}
    for cap in proof["input_artifacts"].values():
        assert cap["bytes"]>100 and re.fullmatch(r"[0-9a-f]{64}",cap["sha256"])
    for name,state in (
        ("u1","OFFLINE_GCODE_VERIFIED_DIALECT_REVIEW"),
        ("c5pro","OFFLINE_GCODE_VERIFIED_DIALECT_REVIEW"),
        ("ecc2","BLOCKED_MOTION_BOUNDS"),
    ):
        row=proof["profiles"][name]
        assert row["state"]==state
        assert row["manufacturing_qualified"] is False
        assert row["firmware_command_set_audited"] is False
        assert "native_config" not in row["profile_limits"]
        assert set(row["offline_slices"])=={"stl","3mf"}
        a=row["offline_slices"]["stl"]
        b=row["offline_slices"]["3mf"]
        assert a["slicer_returncode"]==b["slicer_returncode"]==0
        assert a["header"]["reported_layer_count"]==b["header"]["reported_layer_count"]==60
        assert a["header"]["reported_version"]==b["header"]["reported_version"]=="2.4.2"
        assert abs(a["header"]["reported_max_z_mm"]-b["header"]["reported_max_z_mm"])<=0.1
        for item in (a,b):
            assert item["stats"]["extrusion_moves"]>100
            assert item["stats"]["temperature_commands"]>0
            assert item["header"]["artifact"]["bytes"]>100
            assert re.fullmatch(r"[0-9a-f]{64}",item["header"]["artifact"]["sha256"])
            assert any("Unknown or unsupported commands" in w for w in item["warnings"])
            if name=="ecc2":
                assert item["bounds_validation_ok"] is False
                assert item["canonical_bridge_returncode"]!=0
                assert any("Y=-1.2" in e and "outside Y motion range" in e
                           for e in item["bounds_errors"])
            else:
                assert item["bounds_validation_ok"] is True
                assert item["canonical_bridge_returncode"]==0
                assert not item["bounds_errors"]
    assert proof["h2d_motion"]=="BLOCKED_MOTION_BOUNDS"
    required=set(contract["required_negative_controls"])
    assert required<=set(proof["negative_controls"])
    assert all(proof["negative_controls"][k]=="BLOCKED" for k in required if k!="native_profile_hash_unchanged")
    assert proof["negative_controls"]["native_profile_hash_unchanged"]=="PASS_UNCHANGED"


def main()->int:
    arg=argparse.ArgumentParser()
    group=arg.add_mutually_exclusive_group(required=True)
    group.add_argument("--capture-root",type=pathlib.Path)
    group.add_argument("--verify-recorded",action="store_true")
    arg.add_argument("--evidence-out",type=pathlib.Path,default=DEFAULT_REPORT)
    args=arg.parse_args()
    if args.verify_recorded:
        verify_record(p11.load_json(DEFAULT_REPORT),config())
        print("validate_ai3d_phase14_printer_profiles: RECORDED_PASS profiles=3 u1/c5pro=OFFLINE_DIALECT_REVIEW ecc2=BLOCKED",flush=True)
    else:
        new_offline_capture(args.capture_root,args.evidence_out)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
