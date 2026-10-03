"""Create or update one bounded Fusion user parameter."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fusion_native import print_success, run_trusted_script

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_UNITS = {"mm","cm","m","in","deg","rad"}

def main(**kwargs) -> None:
    name = str(kwargs.get("name") or "").strip()
    expression = str(kwargs.get("expression") or "").strip()
    units = str(kwargs.get("units") or "mm").strip()
    comment = str(kwargs.get("comment") or "VelvetOS")[:128]
    if not _NAME_RE.fullmatch(name):
        raise SystemExit(json.dumps({"success":False,"message":"Invalid parameter name."}))
    if not expression or len(expression) > 128:
        raise SystemExit(json.dumps({"success":False,"message":"Expression must be 1-128 characters."}))
    if units not in _UNITS:
        raise SystemExit(json.dumps({"success":False,"message":"Unsupported parameter units."}))
    body = f"""
app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
if not design:
    raise RuntimeError("No active Fusion design")
params = design.userParameters
param = params.itemByName({name!r})
created = param is None
if param:
    param.expression = {expression!r}
else:
    param = params.add({name!r}, adsk.core.ValueInput.createByString({expression!r}), {units!r}, {comment!r})
result = {{"name": param.name, "expression": param.expression, "unit": param.unit, "created": created}}
"""
    try:
        result = run_trusted_script(body, timeout=30)
        print_success("Fusion user parameter updated.", result)
    except Exception as exc:
        print(json.dumps({"success":False,"message":"Failed to update Fusion user parameter.","context":{"error":str(exc)}}))
        raise SystemExit(1)

if __name__ == "__main__":
    main()
