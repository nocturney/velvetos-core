"""Export the active Fusion design to STEP or STL under D:\\Velvet."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fusion_native import print_success, run_trusted_script

ROOT = os.path.normcase(os.path.abspath(r"D:\Velvet"))

def main(**kwargs) -> None:
    fmt = str(kwargs.get("format") or "").strip().lower()
    output = os.path.normcase(os.path.abspath(str(kwargs.get("output_path") or "")))
    if fmt not in {"step","stl"}:
        raise SystemExit(json.dumps({"success":False,"message":"format must be step or stl"}))
    try:
        if os.path.commonpath([ROOT, output]) != ROOT:
            raise ValueError
    except Exception:
        raise SystemExit(json.dumps({"success":False,"message":"output_path must stay under D:\\Velvet"}))
    ext = ".step" if fmt == "step" else ".stl"
    if not output.endswith(ext):
        raise SystemExit(json.dumps({"success":False,"message":f"{fmt} output must end with {ext}"}))
    body = f"""
import os
app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
if not design:
    raise RuntimeError("No active Fusion design")
output = {output!r}
os.makedirs(os.path.dirname(output), exist_ok=True)
manager = design.exportManager
if {fmt!r} == "step":
    options = manager.createSTEPExportOptions(output, design.rootComponent)
else:
    options = manager.createSTLExportOptions(design.rootComponent, output)
ok = bool(manager.execute(options))
exists = os.path.isfile(output)
size = os.path.getsize(output) if exists else 0
if not ok or not exists or size <= 0:
    raise RuntimeError("Fusion export verification failed")
result = {{"format": {fmt!r}, "path": output, "bytes": size, "verified": True}}
"""
    try:
        result = run_trusted_script(body, timeout=45)
        print_success("Fusion export verified.", result)
    except Exception as exc:
        print(json.dumps({"success":False,"message":"Failed to export Fusion design.","context":{"error":str(exc)}}))
        raise SystemExit(1)

if __name__ == "__main__":
    main()
