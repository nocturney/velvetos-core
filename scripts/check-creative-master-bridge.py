#!/usr/bin/env python3
"""Fail-closed sensor for the creative-master materialization bridge."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "scripts/vf_creative_master_bridge.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(BRIDGE), *args], cwd=cwd, text=True, capture_output=True)


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    src = root / "provider-output.png"
    Image.new("RGB", (64, 64), (220, 210, 190)).save(src)

    proc = run("register", "--root", str(root), "--input", "provider-output.png",
               "--workspace", "job", "--origin-kind", "PROVIDER_FETCHED_FILE",
               "--provider", "test-provider", "--origin-id", "task-123", cwd=root)
    if proc.returncode:
        fail(f"register failed: {proc.stderr}")
    result = json.loads(proc.stdout)
    master = root / result["creative_master"]["path"]
    receipt = root / result["creative_master_materialization"]["path"]
    if not master.is_file() or not receipt.is_file():
        fail("register did not create master + receipt")
    if sha(master) != sha(src):
        fail("registered creative master is not exact bytes")

    proc = run("verify", "--root", str(root), "--receipt",
               result["creative_master_materialization"]["path"], cwd=root)
    if proc.returncode:
        fail(f"verify failed: {proc.stderr}")

    forbidden = sha(src)
    proc = run("register", "--root", str(root), "--input", "provider-output.png",
               "--workspace", "forbidden-job", "--origin-kind", "LOCAL_RENDER",
               "--forbid-sha", forbidden, cwd=root)
    if proc.returncode == 0:
        fail("forbidden raw/reference SHA was accepted as creative master")

    master.write_bytes(master.read_bytes() + b"tamper")
    proc = run("verify", "--root", str(root), "--receipt",
               result["creative_master_materialization"]["path"], cwd=root)
    if proc.returncode == 0:
        fail("tampered materialized master passed verification")

print("OK creative-master bridge exact-byte materialization + tamper detection")
