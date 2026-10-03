"""Export the provider-owned temporary design to STEP or STL under D:\\Velvet\\Tmp."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fusion_native import EXPORT_ROOT, load_temp_state, print_success, run_trusted_script

_BASE_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def main(format: str = None, basename: str = "acceptance") -> None:
    fmt = str(format or "").strip().lower()
    if fmt not in {"step", "stl"}:
        print(json.dumps({"success": False, "message": "format must be 'step' or 'stl'."}))
        raise SystemExit(1)
    basename = str(basename or "acceptance").strip()
    if not _BASE_RE.fullmatch(basename):
        print(json.dumps({"success": False, "message": "Invalid export basename."}))
        raise SystemExit(1)

    state = load_temp_state()
    expected_document = state["document"]
    token = state["token"]
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    output = EXPORT_ROOT / f"{basename}.{fmt}"
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
manager = design.exportManager
output_path = {str(output)!r}
if {fmt!r} == "step":
    options = manager.createSTEPExportOptions(output_path, root)
else:
    options = manager.createSTLExportOptions(root, output_path)
ok = manager.execute(options)
result = {{
    "format": {fmt!r},
    "path": output_path,
    "export_ok": bool(ok),
    "root_name": root.name
}}
"""
    try:
        result = run_trusted_script(body, timeout=40)
        path = Path(str(result.get("path") or ""))
        if not result.get("export_ok") or not path.is_file() or path.stat().st_size <= 0:
            raise RuntimeError("Fusion reported export completion but the artifact is missing or empty.")
        result["bytes"] = path.stat().st_size
        print_success("Temporary Fusion design exported.", result)
    except Exception as exc:
        print(json.dumps({"success": False, "message": "Failed to export temporary Fusion design.", "context": {"error": str(exc)}}))
        raise SystemExit(1)


if __name__ == "__main__":
    params = {}
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            params = json.loads(raw)
    main(**params)
