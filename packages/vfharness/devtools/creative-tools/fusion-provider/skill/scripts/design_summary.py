"""Read a bounded summary of the active Fusion design."""
from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fusion_native import print_success, run_trusted_script

def main(**_kwargs) -> None:
    body = """
app = adsk.core.Application.get()
doc = app.activeDocument
design = adsk.fusion.Design.cast(app.activeProduct)
if not doc or not design:
    raise RuntimeError("No active Fusion design")
root = design.rootComponent
params = design.userParameters
result = {
    "document": doc.name,
    "root_component": root.name,
    "bodies": root.bRepBodies.count,
    "occurrences": root.occurrences.count,
    "sketches": root.sketches.count,
    "user_parameters": params.count,
    "parameter_names": [params.item(i).name for i in range(params.count)]
}
"""
    try:
        result = run_trusted_script(body, read_only=True, timeout=25)
        print_success("Fusion design summary read.", result)
    except Exception as exc:
        print(json.dumps({"success":False,"message":"Failed to read Fusion design summary.","context":{"error":str(exc)}}))
        raise SystemExit(1)

if __name__ == "__main__":
    main()
