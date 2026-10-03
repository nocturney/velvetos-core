"""Create one bounded rectangular box body in the active Fusion design."""
from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fusion_native import print_success, run_trusted_script

def _dim(value, default):
    try:
        v = float(default if value is None else value)
    except Exception:
        raise ValueError("Box dimensions must be numeric")
    if v <= 0 or v > 100000:
        raise ValueError("Box dimensions must be > 0 and <= 100000 mm")
    return v

def main(**kwargs) -> None:
    try:
        width = _dim(kwargs.get("width_mm"), 20.0)
        height = _dim(kwargs.get("height_mm"), 20.0)
        depth = _dim(kwargs.get("depth_mm"), 10.0)
    except Exception as exc:
        raise SystemExit(json.dumps({"success":False,"message":str(exc)}))
    body = f"""
app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
if not design:
    raise RuntimeError("No active Fusion design")
root = design.rootComponent
sketch = root.sketches.add(root.xYConstructionPlane)
lines = sketch.sketchCurves.sketchLines
lines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create({width / 10.0!r}, {height / 10.0!r}, 0)
)
if sketch.profiles.count < 1:
    raise RuntimeError("Box sketch produced no profile")
feature = root.features.extrudeFeatures.addSimple(
    sketch.profiles.item(0),
    adsk.core.ValueInput.createByString({(str(depth) + " mm")!r}),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
result = {{
    "created": True,
    "feature": feature.name,
    "body_count": root.bRepBodies.count,
    "width_mm": {width!r},
    "height_mm": {height!r},
    "depth_mm": {depth!r}
}}
"""
    try:
        result = run_trusted_script(body, timeout=35)
        print_success("Fusion box created.", result)
    except Exception as exc:
        print(json.dumps({"success":False,"message":"Failed to create Fusion box.","context":{"error":str(exc)}}))
        raise SystemExit(1)

if __name__ == "__main__":
    main()
