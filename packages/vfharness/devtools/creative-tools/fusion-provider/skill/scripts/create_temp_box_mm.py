"""Create a rectangular box in the provider-owned temporary design."""
from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fusion_native import load_temp_state, print_success, run_trusted_script


def _number(kwargs, name: str) -> float:
    try:
        value = float(kwargs.get(name))
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be numeric")
    if not (0.01 <= value <= 100000.0):
        raise ValueError(f"{name} is outside the accepted range")
    return value


def main(width_mm: float = None, depth_mm: float = None, height_mm: float = None) -> None:
    values = {"width_mm": width_mm, "depth_mm": depth_mm, "height_mm": height_mm}
    try:
        width = _number(values, "width_mm")
        depth = _number(values, "depth_mm")
        height = _number(values, "height_mm")
    except ValueError as exc:
        print(json.dumps({"success": False, "message": str(exc)}))
        raise SystemExit(1)

    state = load_temp_state()
    expected_document = state["document"]
    token = state["token"]
    width_cm = width / 10.0
    depth_cm = depth / 10.0
    height_expr = f"{height:.9g} mm"
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
sketch = root.sketches.add(root.xYConstructionPlane)
sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create({width_cm!r}, {depth_cm!r}, 0)
)
profile = sketch.profiles.item(0)
feature = root.features.extrudeFeatures.addSimple(
    profile,
    adsk.core.ValueInput.createByString({height_expr!r}),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
result = {{
    "feature": feature.name,
    "width_mm": {width!r},
    "depth_mm": {depth!r},
    "height_mm": {height!r},
    "body_count": root.bRepBodies.count,
    "sketch_count": root.sketches.count,
    "root_name": root.name
}}
"""
    try:
        result = run_trusted_script(body, timeout=35)
        print_success("Temporary Fusion box created.", result)
    except Exception as exc:
        print(json.dumps({"success": False, "message": "Failed to create temporary Fusion box.", "context": {"error": str(exc)}}))
        raise SystemExit(1)


if __name__ == "__main__":
    params = {}
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            params = json.loads(raw)
    main(**params)
