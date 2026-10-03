"""Read back the provider-owned temporary Fusion design."""
from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fusion_native import load_temp_state, print_success, run_trusted_script


def main() -> None:
    state = load_temp_state()
    expected_document = state["document"]
    token = state["token"]
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
parameters = []
for index in range(design.userParameters.count):
    param = design.userParameters.item(index)
    parameters.append({{
        "name": param.name,
        "expression": param.expression,
        "unit": param.unit
    }})
bodies = []
for index in range(root.bRepBodies.count):
    body_item = root.bRepBodies.item(index)
    bodies.append({{"name": body_item.name, "volume": body_item.volume}})
result = {{
    "document": app.activeDocument.name if app.activeDocument else None,
    "root_name": root.name,
    "body_count": root.bRepBodies.count,
    "sketch_count": root.sketches.count,
    "parameters": parameters,
    "bodies": bodies
}}
"""
    try:
        result = run_trusted_script(body, read_only=True, timeout=30)
        print_success("Temporary Fusion design read back.", result)
    except Exception as exc:
        print(json.dumps({"success": False, "message": "Failed to read temporary Fusion design.", "context": {"error": str(exc)}}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
