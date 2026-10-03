"""Close only the provider-owned temporary Fusion design without saving."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fusion_native import (
    FusionProviderError,
    clear_temp_state,
    load_temp_state,
    native_call,
    print_success,
    run_trusted_script,
)


def _text_payload(value):
    if not isinstance(value, dict):
        return value
    content = value.get("content")
    if not isinstance(content, list):
        return value
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
            try:
                return json.loads(block["text"])
            except json.JSONDecodeError:
                return block["text"]
    return value


def main() -> None:
    try:
        state = load_temp_state()
        expected_document = str(state["document"])
        token = str(state["token"])

        validation_body = f"""
app = adsk.core.Application.get()
doc = app.activeDocument
design = adsk.fusion.Design.cast(app.activeProduct)
if not doc or not design:
    raise RuntimeError("No active Fusion design")
root = design.rootComponent
marker = root.attributes.itemByName("VelvetOS", "ProviderToken")
if doc.name != {expected_document!r} or not marker or marker.value != {token!r}:
    raise RuntimeError("Active design is not the provider-owned temporary design")
result = {{"document": doc.name, "root_name": root.name, "ownership_marker": marker.value}}
"""
        verified = run_trusted_script(validation_body, read_only=True, timeout=20)

        close_args = {
            "featureType": "document",
            "object": {
                "operation": "close",
                "userConfirmedCloseWithoutSave": True,
            },
        }
        close_response = None
        try:
            close_response = native_call("fusion_mcp_execute", close_args, timeout=8)
        except FusionProviderError as exc:
            if "timed out" not in str(exc).lower():
                raise

        deadline = time.monotonic() + 12
        last_documents = None
        closed = False
        while time.monotonic() < deadline:
            try:
                raw = native_call(
                    "fusion_mcp_read",
                    {"queryType": "document", "operation": "open"},
                    timeout=6,
                )
                last_documents = _text_payload(raw)
                results = last_documents.get("results", []) if isinstance(last_documents, dict) else []
                if not any(
                    isinstance(item, dict)
                    and item.get("name") == expected_document
                    and item.get("isActive") is True
                    for item in results
                ):
                    closed = True
                    break
            except FusionProviderError:
                pass
            time.sleep(0.25)

        if not closed:
            raise FusionProviderError(
                f"Fusion did not verify closure of provider-owned document {expected_document!r}"
            )

        clear_temp_state()
        print_success(
            "Provider-owned temporary Fusion design closed without saving.",
            {
                "closed": True,
                "document": expected_document,
                "saved": False,
                "root_name": verified.get("root_name"),
                "close_response_received": close_response is not None,
                "open_documents_after": last_documents,
            },
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "success": False,
                    "message": "Failed to close provider-owned temporary Fusion design.",
                    "context": {"error": str(exc)},
                }
            )
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
