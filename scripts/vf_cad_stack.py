#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"packages"/"vfprod"/"CAD-ENGINE-REGISTRY.json"
MAX_REPAIRS=2

def emit(x,code=0):
    print(json.dumps(x,ensure_ascii=False,indent=2)); return code

def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def contract(_):
    r=load_json(REGISTRY)
    return emit({"status":"PASS","schema":r["schema"],"max_repair_iterations":r["max_repair_iterations"],"engines":r["engines"]})

def validate_ir(data):
    if data.get("schema")!="velvetos.geometry-ir.v1" or data.get("units")!="mm": return "schema_or_units"
    parts=data.get("parts")
    cons=data.get("constraints")
    if not isinstance(parts,list) or not parts or not isinstance(cons,list): return "parts_or_constraints"
    ids=[]
    allowed={"box","cylinder","extrusion","imported_step","assembly"}
    for p in parts:
        if not isinstance(p,dict) or not isinstance(p.get("id"),str) or not p["id"] or p.get("kind") not in allowed: return "invalid_part"
        if not isinstance(p.get("dimensions"),dict) or not p["dimensions"]: return "dimensions_required"
        for v in p["dimensions"].values():
            if not isinstance(v,(int,float)) or isinstance(v,bool) or v<=0: return "positive_numeric_dimensions_required"
        ids.append(p["id"])
    if len(ids)!=len(set(ids)): return "duplicate_part_id"
    known=set(ids)
    for c in cons:
        if not isinstance(c,dict) or c.get("a") not in known or c.get("b") not in known: return "constraint_ref_unknown"
        if c.get("type") not in {"align","offset","mate","clearance","contains"}: return "constraint_type"
        if c.get("value_mm") is not None and not isinstance(c.get("value_mm"),(int,float)): return "constraint_value"
    return None

def ir_validate(a):
    data=load_json(a.input); err=validate_ir(data)
    return emit({"status":"BLOCKED" if err else "PASS","reason":err,"parts":len(data.get("parts",[]))},2 if err else 0)

def repair_next(a):
    p=Path(a.state)
    state={"schema":"velvetos.cad-repair-state.v1","attempts":0,"failures":[]} if not p.exists() else load_json(p)
    state["failures"].append(a.failure)
    if state["attempts"]<MAX_REPAIRS:
        state["attempts"]+=1; decision="REPAIR_ALLOWED"
    else:
        decision="FALLBACK_REQUIRED"
    state["decision"]=decision
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return emit({"status":"PASS","decision":decision,"attempts":state["attempts"],"max":MAX_REPAIRS})

def stack_root():
    base=Path(os.environ.get("VELVET_PRINTLAB_ROOT",Path.home()/"Documents"/"VelvetPrintLab"))
    return (base/"tools"/"cad-stack").resolve()

def doctor(_):
    r=load_json(REGISTRY); sr=stack_root()
    text2cad=Path(os.environ.get("TEXT_TO_CAD_ROOT",Path.home()/"Documents"/"VelvetPrintLab"/"tools"/"text-to-cad"))
    b3d_py=text2cad/".venv"/("Scripts/python.exe" if os.name=="nt" else "bin/python")
    cq_py=sr/"cadquery"/".venv"/("Scripts/python.exe" if os.name=="nt" else "bin/python")
    js_runner=sr/"jscad"/"probe.mjs"
    checks={}
    checks["build123d"]=b3d_py.is_file()
    checks["cadquery"]=cq_py.is_file()
    checks["jscad"]=shutil.which("node") is not None and js_runner.is_file()
    checks["cad-cae-copilot"]=(sr/"pilots"/"cad-cae-copilot"/".git").exists()
    checks["forgent3d"]=(sr/"pilots"/"forgent3d-desktop"/".git").exists()
    status="PASS" if all(checks[k] for k in ("build123d","cadquery","jscad")) else "BLOCKED"
    return emit({"status":status,"stack_root":str(sr),"engines":checks,"pilots_required_for_pass":False},0 if status=="PASS" else 2)

def parser():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest="cmd",required=True)
    s.add_parser("contract"); s.add_parser("doctor")
    q=s.add_parser("ir-validate"); q.add_argument("--input",required=True)
    q=s.add_parser("repair-next"); q.add_argument("--state",required=True); q.add_argument("--failure",required=True)
    return p

def main():
    a=parser().parse_args()
    if a.cmd=="contract": return contract(a)
    if a.cmd=="doctor": return doctor(a)
    if a.cmd=="ir-validate": return ir_validate(a)
    if a.cmd=="repair-next": return repair_next(a)
    return 2

if __name__=="__main__": raise SystemExit(main())
