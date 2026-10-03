"""Create, export, and close one provider-owned Fusion box atomically."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fusion_native import EXPORT_ROOT, print_success, run_trusted_script

_BASE_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _number(value, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not 0.01 <= number <= 100000.0:
        raise ValueError(f"{name} is outside the accepted range")
    return number


def main(width_mm=None, depth_mm=None, height_mm=None, format=None, basename=None) -> None:
    try:
        width = _number(width_mm, "width_mm")
        depth = _number(depth_mm, "depth_mm")
        height = _number(height_mm, "height_mm")
    except ValueError as exc:
        print(json.dumps({"success": False, "message": str(exc)}))
        raise SystemExit(1)
    fmt = str(format or "").strip().lower()
    if fmt not in {"step", "stl"}:
        print(json.dumps({"success": False, "message": "format must be step or stl"}))
        raise SystemExit(1)
    basename = str(basename or "").strip()
    if not _BASE_RE.fullmatch(basename):
        print(json.dumps({"success": False, "message": "invalid export basename"}))
        raise SystemExit(1)

    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    output = EXPORT_ROOT / f"{basename}.{fmt}"
    if output.exists():
        print(json.dumps({"success": False, "message": "refusing to overwrite temporary export"}))
        raise SystemExit(1)

    token = uuid.uuid4().hex
    width_cm = width / 10.0
    depth_cm = depth / 10.0
    height_expr = f"{height:.9g} mm"
    body = f"""
app = adsk.core.Application.get()
doc = None
try:
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError("Fusion did not activate a design document")
    root = design.rootComponent
    marker = root.attributes.add("VelvetOS", "CreativeCraftToken", {token!r})
    if not marker or marker.value != {token!r}:
        raise RuntimeError("provider ownership marker could not be written")
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
    manager = design.exportManager
    output_path = {str(output)!r}
    if {fmt!r} == "step":
        options = manager.createSTEPExportOptions(output_path, root)
    else:
        options = manager.createSTLExportOptions(root, output_path)
    export_ok = bool(manager.execute(options))
    if not export_ok:
        raise RuntimeError("Fusion exportManager returned false")
    result = {{
        "document": doc.name,
        "feature": feature.name,
        "width_mm": {width!r},
        "depth_mm": {depth!r},
        "height_mm": {height!r},
        "body_count": root.bRepBodies.count,
        "sketch_count": root.sketches.count,
        "format": {fmt!r},
        "path": output_path,
        "export_ok": export_ok,
        "ownership_marker": marker.value
    }}
finally:
    if doc is not None:
        doc.close(False)
"""
    try:
        result = run_trusted_script(body, timeout=90)
        artifact = Path(str(result.get("path") or ""))
        if not result.get("export_ok") or not artifact.is_file() or artifact.stat().st_size <= 0:
            raise RuntimeError("atomic Fusion export artifact is missing or empty")
        result["bytes"] = artifact.stat().st_size
        result["closed"] = True
        print_success("Provider-owned Fusion box exported and closed.", result)
    except Exception as exc:
        try:
            output.unlink(missing_ok=True)
        except Exception:
            pass
        print(json.dumps({"success": False, "message": "Atomic Fusion box operation failed.", "context": {"error": str(exc)}}))
        raise SystemExit(1)

if __name__ == "__main__":
    params = {}
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            params = json.loads(raw)
    main(**params)
