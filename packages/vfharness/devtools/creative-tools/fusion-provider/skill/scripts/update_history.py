"""Bounded Fusion undo/redo through the Autodesk native MCP update tool."""
from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fusion_native import native_call, print_success

def main(**kwargs) -> None:
    action = str(kwargs.get("action") or "").strip().lower()
    if action not in {"undo","redo"}:
        raise SystemExit(json.dumps({"success":False,"message":"action must be undo or redo"}))
    try:
        result = native_call("fusion_mcp_update", {"featureType": action}, timeout=15)
        print_success(f"Fusion {action} request completed.", {"action": action, "native_result": result})
    except Exception as exc:
        print(json.dumps({"success":False,"message":f"Fusion {action} failed.","context":{"error":str(exc)}}))
        raise SystemExit(1)

if __name__ == "__main__":
    main()
