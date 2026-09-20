"""GrokBot client for the trusted Instagram failover task.

Grok never receives SSH keys, MCP bearer tokens, signed receipts, or Meta tokens.
The privileged runner is consumed only by the always-on GrokBot Boot Supervisor and returns safe JSON only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
import uuid

ROOT = Path(r"C:\ProgramData\VelvetOS\instagram-failover")
REQUESTS = ROOT / "requests"
RESULTS = ROOT / "results"

def _emit(payload: dict) -> int:
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload.get("ok") is True else 2

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    manifest = Path(args.manifest).resolve()
    if not manifest.is_file():
        return _emit({"ok": False, "blocked": True, "error": "manifest file does not exist"})

    REQUESTS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    request_id = uuid.uuid4().hex
    request_path = REQUESTS / f"{request_id}.json"
    result_path = RESULTS / f"{request_id}.json"
    payload = {
        "request_id": request_id,
        "manifest": str(manifest),
        "execute": bool(args.execute),
        "expires_at": time.time() + 180,
    }
    temp = REQUESTS / f".{request_id}.tmp"
    temp.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(request_path)

    # The always-on GrokBot Boot Supervisor (S4U) is the sole trusted dispatcher.
    # Keeping one consumer prevents two workers from racing the same execute request.
    deadline = time.monotonic() + 330
    while time.monotonic() < deadline:
        if result_path.is_file():
            try:
                result = json.loads(result_path.read_text(encoding="utf-8-sig"))
            finally:
                result_path.unlink(missing_ok=True)
            if not isinstance(result, dict):
                return _emit({"ok": False, "blocked": True, "error": "trusted failover returned invalid result"})
            return _emit(result)
        time.sleep(0.5)

    return _emit({
        "ok": False,
        "blocked": True,
        "error": "trusted failover task timed out; inspect task state before retrying",
        "request_id": request_id,
    })

if __name__ == "__main__":
    raise SystemExit(main())