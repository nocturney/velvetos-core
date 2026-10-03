"""Create a provider-owned disposable Fusion design."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fusion_native import FusionProviderError, clear_temp_state, print_success, run_trusted_script, save_temp_state

_LABEL_RE = re.compile(r"^[A-Za-z0-9 _.-]{1,80}$")


def main(label: str = "VelvetOS Acceptance") -> None:
    label = str(label or "VelvetOS Acceptance").strip()
    if not _LABEL_RE.fullmatch(label):
        raise SystemExit(json.dumps({"success": False, "message": "label contains unsupported characters"}))
    token = uuid.uuid4().hex
    body = f"""
app = adsk.core.Application.get()
doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
design = adsk.fusion.Design.cast(app.activeProduct)
if not design:
    raise RuntimeError("Fusion did not activate a design document")
root = design.rootComponent
marker = root.attributes.add("VelvetOS", "ProviderToken", {token!r})
if not marker or marker.value != {token!r}:
    raise RuntimeError("Fusion provider ownership marker could not be written")
result = {{
    "document": doc.name,
    "root_name": root.name,
    "token": {token!r},
    "ownership_marker": marker.value,
    "body_count": root.bRepBodies.count,
    "sketch_count": root.sketches.count
}}
"""
    clear_temp_state()
    try:
        result = run_trusted_script(body, timeout=50)
        state = {
            "token": token,
            "document": result.get("document"),
            "label": label,
        }
        save_temp_state(state)
        print_success("Provider-owned temporary Fusion design created.", result)
    except Exception as exc:
        clear_temp_state()
        print(json.dumps({"success": False, "message": "Failed to create temporary Fusion design.", "context": {"error": str(exc)}}))
        raise SystemExit(1)


if __name__ == "__main__":
    params = {}
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            params = json.loads(raw)
    main(**params)
