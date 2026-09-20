from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any

ROOT = Path(r"C:\ProgramData\VelvetOS\instagram-failover")
REQUESTS = ROOT / "requests"
RESULTS = ROOT / "results"
TRUSTED = ROOT / "trusted-instagram-failover.py"
ALLOWED_MANIFEST_ROOTS = [
    Path(r"C:\ProgramData\VelvetOS\openpost-rollout").resolve(),
    ROOT.resolve(),
]
ID_RE = re.compile(r"^[0-9a-f]{32}$")

def _safe_json(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    start = text.find("{")
    if start < 0:
        raise ValueError("trusted runner returned no JSON")
    obj, _ = decoder.raw_decode(text[start:])
    if not isinstance(obj, dict):
        raise ValueError("trusted runner JSON is not an object")
    return obj
def _allowed_manifest(path: Path) -> bool:
    resolved = path.resolve()
    for root in ALLOWED_MANIFEST_ROOTS:
        try:
            resolved.relative_to(root)
            return resolved.suffix.lower() == ".json"
        except ValueError:
            continue
    return False

def _write_result(request_id: str, payload: dict[str, Any]) -> None:
    target = RESULTS / f"{request_id}.json"
    temp = RESULTS / f".{request_id}.tmp"
    temp.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(target)

def _process(path: Path) -> None:
    request_id = path.stem
    if not ID_RE.fullmatch(request_id):
        path.unlink(missing_ok=True)
        return
    try:
        request = json.loads(path.read_text(encoding="utf-8-sig"))
        expires_at = float(request.get("expires_at") or 0)
        if expires_at <= time.time():
            raise ValueError("failover request expired")
        manifest = Path(str(request.get("manifest") or ""))
        execute = request.get("execute") is True
        if not _allowed_manifest(manifest):
            raise ValueError("manifest path is outside trusted roots")
        if not manifest.is_file():
            raise ValueError("manifest file does not exist")
        argv = [sys.executable, "-X", "utf8", str(TRUSTED), "--manifest", str(manifest.resolve())]
        if execute:
            argv.append("--execute")
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=300, check=False)
        result = _safe_json(proc.stdout)
        result["trusted_dispatch"] = True
        result["request_id"] = request_id
        if proc.returncode != 0 and result.get("ok") is True:
            result = {"ok": False, "blocked": True, "error": "trusted runner returned non-zero", "request_id": request_id, "trusted_dispatch": True}
    except Exception as exc:
        result = {
            "ok": False,
            "blocked": True,
            "error": str(exc)[:400],
            "request_id": request_id,
            "trusted_dispatch": True,
        }
    finally:
        path.unlink(missing_ok=True)
    _write_result(request_id, result)

def main() -> int:
    REQUESTS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    for request in sorted(REQUESTS.glob("*.json"), key=lambda p: p.stat().st_mtime):
        _process(request)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())