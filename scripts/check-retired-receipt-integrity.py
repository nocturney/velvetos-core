#!/usr/bin/env python3
"""Fast integrity guard for retired historical sensor receipts."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "velvetos" / "policy" / "retired-receipt-manifest.json"
GENERATOR = ROOT / "scripts" / "generate-retired-receipt-manifest.py"


def fail(message: str) -> None:
    print("FAIL retired-receipt-integrity: " + message, file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if not MANIFEST.is_file() or not GENERATOR.is_file():
        fail("manifest or generator missing")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema") != "velvetos.retired-receipts.v1":
        fail("schema mismatch")
    entries = data.get("entries") or []
    if len(entries) != 7:
        fail(f"expected 7 retired entries, got {len(entries)}")
    paths = [row.get("path") for row in entries]
    if len(paths) != len(set(paths)):
        fail("duplicate retired receipt paths")
    for row in entries:
        rel = row.get("path")
        path = ROOT / str(rel or "")
        if not path.is_file():
            fail(f"missing {rel}")
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if observed != row.get("sha256"):
            fail(f"hash drift: {rel}")
    proc = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )
    if proc.returncode != 0:
        fail(proc.stderr.strip() or proc.stdout.strip() or "generator check failed")
    print("OK retired-receipt-integrity entries=7 immutable=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
