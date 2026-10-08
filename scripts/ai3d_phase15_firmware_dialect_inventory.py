#!/usr/bin/env python3
"""Read-only audit of unrecognized firmware G-code in Phase14 offline files.

Identifies commands and source-profile occurrences without executing any code
from G-code, without connecting to printers and without qualifying a firmware
dialect or expanding machine motion bounds.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pathlib
import re
from collections import Counter
from typing import Any

ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/"docs"/"implementation"/"ai-3d-modeling-engineering-core"
CONTRACT=BASE/"firmware-dialect-audit-v1.json"
P14_PROOF=BASE/"evidence"/"phase14-printer-profiles-acceptance-20261008.json"
DEFAULT_OUT=BASE/"evidence"/"phase15-firmware-dialect-inventory-20261008.json"
PRINTERS=("u1","ecc2","c5pro")
FORMATS=("stl","3mf")
ALL_PROFILES=("u1","ecc2","c5pro","h2d")
COMMAND_TOKEN=re.compile(r"^[A-Z_][A-Z0-9_]*$")
TOOL_TOKEN=re.compile(r"^T[0-9]+$")


def load(path:pathlib.Path)->dict[str,Any]:
    obj=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj,dict):
        raise ValueError(f"expected JSON object at {path.name}")
    return obj


def sha(path:pathlib.Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_commands(source:pathlib.Path)->set[str]:
    """Read (do not import/execute) the canonical generic parser command set."""
    tree=ast.parse(source.read_text(encoding="utf-8"),filename=source.name)
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(
            isinstance(t,ast.Name) and t.id=="SUPPORTED_GCODE_COMMANDS"
            for t in node.targets
        ):
            values=ast.literal_eval(node.value)
            if not isinstance(values,set) or not values:
                raise ValueError("canonical parser allowlist not a literal set")
            names={str(v).upper() for v in values}
            if not {"G0","G1","G90","G91","M104","M109","M190"}<=names:
                raise ValueError("canonical parser missing baseline instructions")
            return names
    raise ValueError("could not identify canonical generic parser allowlist")


def scan(text:str,known:set[str])->dict[str,Any]:
    unknown:dict[str,dict[str,Any]]={}
    known_count=Counter()
    unparsed:list[dict[str,Any]]=[]
    executable_count=0
    for no,line in enumerate(text.splitlines(),1):
        code=line.split(";",1)[0].strip()
        if not code:
            continue
        executable_count+=1
        token=code.split(None,1)[0].upper()
        if not COMMAND_TOKEN.fullmatch(token):
            unparsed.append({"line":no,"token":token[:70]})
            continue
        if token in known or TOOL_TOKEN.fullmatch(token):
            known_count[token]+=1
            continue
        entry=unknown.setdefault(token,{"count":0,"first_line":no,"sample_lines":[]})
        entry["count"]+=1
        if len(entry["sample_lines"])<5:
            entry["sample_lines"].append(no)
    return {
        "total_lines":len(text.splitlines()),
        "executable_lines":executable_count,
        "recognized_command_instances":sum(known_count.values()),
        "unknown_command_instances":sum(x["count"] for x in unknown.values()),
        "unknown_commands":{k:unknown[k] for k in sorted(unknown)},
        "unparsed_lines":unparsed[:25],
        "unparsed_line_count":len(unparsed),
        "relative_positioning_present":"G91" in known_count,
        "machine_control_commands_not_executed":True,
    }


def native_sources(router:pathlib.Path,expected:dict[str,str])->tuple[dict[str,str],dict[str,dict[str,Any]]]:
    matrix=router/"printer_matrix.json"
    source={"printer_matrix.json":sha(matrix)}
    matrix_data=load(matrix)
    assert set(ALL_PROFILES)<=set(matrix_data["printers"])
    assert all(matrix_data["safety"].get(k) is False for k in
               ("printer_network_control","upload","start_print","heating","motion"))
    profiles:dict[str,dict[str,Any]]={}
    for name in ALL_PROFILES:
        row=matrix_data["printers"][name]
        files={
            "machine.json":router/"native-full"/name/"machine.json",
            "process.json":router/"native-full"/name/"process.json",
            "filament.json":router/"native-full"/name/"filament.json",
            "wrapper.json":router/"text-to-cad-profiles"/(name+".json"),
        }
        for filename,path in files.items():
            source[f"{name}/{filename}"]=sha(path)
        # Native source of literal machine script lines is admission evidence
        # only, never proof the currently installed device firmware supports
        # or safely executes a given command.
        machine=load(files["machine.json"])
        process=load(files["process.json"])
        script_fields={}
        for origin,obj in (("machine",machine),("process",process)):
            for key,value in obj.items():
                if "gcode" not in key.lower():
                    continue
                if isinstance(value,str):
                    script_fields[f"{origin}.{key}"]=value
        profiles[name]={"scripts":script_fields}
    if source!=expected:
        differences=sorted(k for k in set(source)|set(expected) if source.get(k)!=expected.get(k))
        raise ValueError("native source/provenance fingerprint mismatch: "+",".join(differences))
    return source,profiles


def macro_sources(command:str,source:dict[str,Any])->list[str]:
    # A source-file textual mention does NOT qualify firmware execution.
    pattern=re.compile(r"(?<![A-Za-z0-9_])"+re.escape(command)+r"(?![A-Za-z0-9_])")
    return sorted(field for field,body in source["scripts"].items()
                  if pattern.search(body.upper()))


def check_record(rec:dict[str,Any],cfg:dict[str,Any])->None:
    assert rec["schema"]=="velvetos.ai3d.phase15-firmware-dialect-inventory.v1"
    assert rec["status"]=="PASS_STATIC_INVENTORY_ONLY_NO_MACHINE_RELEASE"
    assert rec["slicer_authority"]==cfg["source_of_truth"]
    assert rec["production_release"] is False
    assert rec["machine_commands_executed"] is False
    assert rec["native_profiles_unchanged"] is True
    assert rec["device_firmware_version_verified"] is False
    assert rec["motion_envelopes_widened"] is False
    assert rec["profiles"]["ecc2"]["qualification"]=="BLOCKED_MOTION_BOUNDS"
    assert rec["profiles"]["u1"]["qualification"]=="CANDIDATE"
    assert rec["profiles"]["c5pro"]["qualification"]=="CANDIDATE"
    assert rec["h2d_qualification"]=="BLOCKED_MOTION_BOUNDS"
    assert len(rec["native_hashes"])==17
    assert re.fullmatch(r"[0-9a-f]{64}",rec["canonical_parser_sha256"])
    assert re.fullmatch(r"[0-9a-f]{64}",rec["phase14_receipt_sha256"])
    for name in PRINTERS:
        formats=rec["profiles"][name]["files"]
        assert set(formats)==set(FORMATS)
        assert rec["profiles"][name]["unknown_command_names"]
        critical={"u1":{"FINELY_CLEAN_NOZZLE_STAGE_1","SM_PRINT_AUTO_FEED","DEFECT_DETECTION_DETECT_BED"},
                  "ecc2":{"G180","M6211","BED_MESH_CALIBRATE"},
                  "c5pro":{"M191","SET_PRESSURE_ADVANCE","SET_VELOCITY_LIMIT"}}[name]
        assert critical<=set(rec["profiles"][name]["unknown_command_names"])
        for fmt in FORMATS:
            entry=formats[fmt]
            assert entry["gcode_sha256"]==entry["phase14_provenance_sha256"]
            assert entry["bytes"]>100 and re.fullmatch(r"[0-9a-f]{64}",entry["gcode_sha256"])
            assert entry["scan"]["total_lines"]>100
            assert entry["scan"]["unknown_command_instances"]>0
            assert entry["scan"]["machine_control_commands_not_executed"] is True
    assert rec["negative_controls"]=={
        "unrecognized_command_exposed":"PASS",
        "malformed_line_exposed":"PASS",
        "source_receipt_hash_checked":"PASS",
        "native_profile_hashes_unchanged":"PASS",
    }


def capture(fixtures:pathlib.Path,router:pathlib.Path,parser_source:pathlib.Path,
            output:pathlib.Path)->dict[str,Any]:
    cfg=load(CONTRACT)
    proof=load(P14_PROOF)
    assert cfg["schema"]=="velvetos.ai3d.phase15-dialect-audit-contract.v1"
    assert cfg["non_authoritative_staging"] is True
    assert cfg["purpose"]=="read-only-unknown-command-inventory"
    assert cfg["source_of_truth"]=="scripts/vf_cad.py"
    assert all(v is False for v in cfg["prohibitions"].values())
    assert all(v is True for k,v in cfg["admission"].items() if k in
               ("unknown_commands_require_review","vendor_macro_source_not_hardware_attestation"))
    assert proof["status"]=="PASS_OFFLINE_AUDIT_WITH_EXPLICIT_BLOCKERS"
    assert proof["native_profiles_unchanged"] is True
    assert proof["machine_firmware_commands_verified"] is False
    assert proof["printer_actions_executed"] is False
    assert fixtures.resolve().is_relative_to(pathlib.Path(r"D:\Velvet\Artifacts\AI3D").resolve())
    if not fixtures.is_dir():
        raise FileNotFoundError("phase14 offline G-code fixture not present")
    expected=proof["native_profile_hashes"]
    baseline,source=native_sources(router,expected)
    known=canonical_commands(parser_source)
    records={}
    for name in PRINTERS:
        row={"qualification":cfg["status_expectation"][name],
             "source_ref":cfg["provenance"][name],
             "files":{},
             "unknown_command_names":[]}
        all_unknown=set()
        for fmt in FORMATS:
            path=fixtures/f"{name}-{fmt}.gcode"
            if not path.is_file():
                raise FileNotFoundError("missing offline fixture "+path.name)
            expected_sha=proof["profiles"][name]["offline_slices"][fmt]["header"]["artifact"]["sha256"]
            digest=sha(path)
            if expected_sha!=digest:
                raise ValueError(f"Phase14 hash mismatch for {name}/{fmt}")
            scan_result=scan(path.read_text(encoding="utf-8",errors="replace"),known)
            all_unknown.update(scan_result["unknown_commands"])
            if scan_result["unknown_command_instances"]==0:
                raise AssertionError("expected nonstandard machine commands to remain visible")
            row["files"][fmt]={
                "artifact_name":path.name,
                "bytes":path.stat().st_size,
                "gcode_sha256":digest,
                "phase14_provenance_sha256":expected_sha,
                "scan":scan_result,
            }
        row["unknown_command_names"]=sorted(all_unknown)
        row["possible_native_script_mentions"]={
            name2:macro_sources(name2,source[name]) for name2 in sorted(all_unknown)
        }
        row["firmware_execution_compatibility_certified"]=False
        records[name]=row

    unknown_mutation=scan("M999999 S1\n",known)
    malformed_mutation=scan("@UNPARSEABLE_COMMAND X1\n",known)
    assert "M999999" in unknown_mutation["unknown_commands"]
    assert malformed_mutation["unparsed_line_count"]==1
    after,_=native_sources(router,expected)
    if baseline!=after:
        raise AssertionError("read-only command inventory unexpectedly changed native files")
    result={
        "schema":"velvetos.ai3d.phase15-firmware-dialect-inventory.v1",
        "status":"PASS_STATIC_INVENTORY_ONLY_NO_MACHINE_RELEASE",
        "slicer_authority":cfg["source_of_truth"],
        "canonical_parser_sha256":sha(parser_source),
        "phase14_receipt_sha256":sha(P14_PROOF),
        "native_hashes":baseline,
        "native_profiles_unchanged":True,
        "device_firmware_version_verified":False,
        "production_release":False,
        "machine_commands_executed":False,
        "motion_envelopes_widened":False,
        "h2d_qualification":"BLOCKED_MOTION_BOUNDS",
        "profiles":records,
        "negative_controls":{
            "unrecognized_command_exposed":"PASS",
            "malformed_line_exposed":"PASS",
            "source_receipt_hash_checked":"PASS",
            "native_profile_hashes_unchanged":"PASS",
        },
        "limitations":[
            "Command inventory is lexical: native script mentions are not proof of installed firmware support",
            "Generic parser can warn on unknown executable macros and skips relative-motion XY/Z checks",
            "ECC2 -1.2 Y is in the upstream OrcaSlicer profile but the physical service travel has no independent certification",
            "Snapmaker firmware repositories require version identity and macro mapping before qualification",
            "Creator 5 Pro vendor macros remain firmware-specific and unqualified",
            "No device network, heating, motion, print upload/start, or firmware changes performed",
        ],
    }
    check_record(result,cfg)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",encoding="utf-8",newline="\n") as f:
        f.write(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("Phase15 static inventory PASS",flush=True)
    for name,row in records.items():
        print(name,"unknown=",",".join(row["unknown_command_names"]),
              "total=",sum(entry["scan"]["unknown_command_instances"]
                           for entry in row["files"].values()),flush=True)
    return result


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--verify-recorded",action="store_true")
    parser.add_argument("--fixture-root",type=pathlib.Path)
    parser.add_argument("--router-root",type=pathlib.Path)
    parser.add_argument("--canonical-parser",type=pathlib.Path)
    parser.add_argument("--evidence-out",type=pathlib.Path,default=DEFAULT_OUT)
    args=parser.parse_args()
    if args.verify_recorded:
        check_record(load(DEFAULT_OUT),load(CONTRACT))
        print("Phase15 recorded static inventory PASS; machine approval=FALSE")
        return 0
    if not (args.fixture_root and args.router_root and args.canonical_parser):
        parser.error("capture requires --fixture-root, --router-root and --canonical-parser")
    capture(args.fixture_root,args.router_root,args.canonical_parser,args.evidence_out)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
