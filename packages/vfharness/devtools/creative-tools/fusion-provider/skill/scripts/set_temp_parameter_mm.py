"""Set one millimetre parameter on the provider-owned temporary design."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fusion_native import load_temp_state, print_success, run_trusted_script

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")


def main(name: str = None, value_mm: float = None) -> None:
    name = str(name or "").strip()
    if not _NAME_RE.fullmatch(name):
        print(json.dumps({"success": False, "message": "Invalid parameter name."}))
        raise SystemExit(1)
    try:
        value_mm = float(value_mm)
    except (TypeError, ValueError):
        print(json.dumps({"success": False, "message": "value_mm must be numeric."}))
        raise SystemExit(1)
    if not (0.001 <= value_mm <= 100000.0):
        print(json.dumps({"success": False, "message": "value_mm is outside the accepted range."}))
        raise SystemExit(1)

    state = load_temp_state()
    expected_document = state["document"]
    token = state["token"]
    expression = f"{value_mm:.9g} mm"
    body = f"""
app = adsk.core.Application.get()
doc = app.activeDocument
design = adsk.fusion.Design.cast(app.activeProduct)
if not doc or not design:
    raise RuntimeError("No active Fusion design")
root = design.rootComponent
marker = root.attributes.itemByName("VelvetOS", "ProviderToken")
if doc.name != {expected_document!r} or not marker or marker.value != {token!r}:
    raise RuntimeError("Active document is not the provider-owned temporary design")
params = design.userParameters
param = params.itemByName({name!r})
existed = param is not None
if param:
    param.expression = {expression!r}
else:
    param = params.add(
        {name!r},
        adsk.core.ValueInput.createByString({expression!r}),
        "mm",
        "VelvetOS temporary acceptance parameter"
    )
result = {{
    "name": param.name,
    "expression": param.expression,
    "existed": existed,
    "root_name": root.name
}}
"""
    try:
        result = run_trusted_script(body, timeout=30)
        print_success("Temporary Fusion parameter set.", result)
    except Exception as exc:
        print(json.dumps({"success": False, "message": "Failed to set temporary Fusion parameter.", "context": {"error": str(exc)}}))
        raise SystemExit(1)


if __name__ == "__main__":
    params = {}
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            params = json.loads(raw)
    main(**params)
