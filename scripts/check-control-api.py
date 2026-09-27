#!/usr/bin/env python3
"""Sensor: VelvetOS Control API — projection gateway, no second SoT/runtime."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "packages" / "velvetos_control_api"
CLI = ROOT / "scripts" / "vf_control_api.py"
PLANE = ROOT / "office" / "control-plane.json"
TESTS = PKG / "tests" / "test_control_api.py"
DEPLOY = PKG / "DEPLOY.md"
README = PKG / "README.md"
CONTRIB = PKG / "CONTRIBUTIONS.json"
DOCKERFILE = PKG / "Dockerfile"
AGENTS = ROOT / "AGENTS.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (PKG, CLI, TESTS, DEPLOY, README, CONTRIB, DOCKERFILE):
        if not path.exists():
            fail(f"missing {path.relative_to(ROOT)}")

    # Must not claim to be a new Control Plane / SoT
    readme = README.read_text(encoding="utf-8")
    for needle in (
        "projection gateway",
        "not a Control Plane",
        "not a source of truth",
    ):
        if needle.lower() not in readme.lower():
            fail(f"README must state Control API is {needle}")

    plane = json.loads(PLANE.read_text(encoding="utf-8"))
    api = plane.get("controlApi") or {}
    if not api:
        fail("office/control-plane.json must reference controlApi projection")
    if api.get("rule") and "not" not in (api.get("rule") or "").lower():
        fail("controlApi.rule must clarify it is not a SoT")
    sots = plane.get("sourcesOfTruth") or {}
    # Control API must not appear as a source of truth
    for k, v in sots.items():
        if "control_api" in k.lower() or "control-api" in str(v).lower():
            if "projection" not in str(v).lower():
                fail(f"Control API must not be registered as SoT key={k}")

    # Dockerfile isolation: no Instagram mutation secrets
    df = DOCKERFILE.read_text(encoding="utf-8")
    for banned in (
        "INSTAGRAM_MCP_ACCESS_TOKEN",
        "VELVET_INSTAGRAM_MCP_BEARER",
        "delivery_approval_ed25519",
    ):
        if banned in df:
            fail(f"Dockerfile must not reference {banned}")

    # CONTRIBUTIONS registry present
    reg = json.loads(CONTRIB.read_text(encoding="utf-8"))
    ids = {c.get("id") for c in reg.get("contributions") or []}
    for need in (
        "jobs",
        "capabilities",
        "integrations",
        "attention",
        "control_plane",
        "unavailable_domains",
        "operational_domains",
    ):
        if need not in ids:
            fail(f"CONTRIBUTIONS.json missing {need}")

    # CLI selftest
    proc = subprocess.run(
        [sys.executable, str(CLI), "selftest"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "packages")},
    )
    if proc.returncode != 0:
        fail(f"vf_control_api.py selftest: {proc.stderr or proc.stdout}")

    # Unit + HTTP tests
    tproc = subprocess.run(
        [sys.executable, str(TESTS)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "packages")},
    )
    if tproc.returncode != 0:
        fail(f"control-api tests:\n{tproc.stderr or tproc.stdout}")

    # Snapshot must be authenticable shape
    snap_proc = subprocess.run(
        [sys.executable, str(CLI), "snapshot"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "packages")},
    )
    if snap_proc.returncode != 0:
        fail(f"snapshot: {snap_proc.stderr or snap_proc.stdout}")
    snap = json.loads(snap_proc.stdout)
    if snap.get("schema") != "velvetos.control.v1":
        fail("snapshot schema mismatch")
    jobs = (snap.get("collections") or {}).get("jobs") or {}
    if jobs.get("state") != "ready" and jobs.get("items") == []:
        fail("non-ready jobs must not report []")
    for name in ("production", "content", "files", "agents", "models"):
        col = (snap.get("collections") or {}).get(name) or {}
        state = col.get("state")
        if state == "ready":
            items = col.get("items")
            count = col.get("count")
            if not isinstance(items, list):
                fail(f"{name} ready projection must expose items=list")
            if not isinstance(count, int) or count < 0:
                fail(f"{name} ready projection must expose non-negative count")
            if col.get("truncated"):
                if col.get("projectedCount") != len(items) or count < len(items):
                    fail(f"{name} truncated projection count contract invalid")
            elif count != len(items):
                fail(f"{name} ready projection count must equal len(items)")
            prov = col.get("provenance") or {}
            if not prov.get("source"):
                fail(f"{name} ready projection must carry provenance source")
        else:
            if col.get("items") is not None or col.get("count") is not None:
                fail(f"{name} non-ready projection must keep items/count null")

    # No secrets in package source
    for path in PKG.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "BEGIN PRIVATE KEY" in text or "INSTAGRAM_MCP_ACCESS_TOKEN=" in text:
            fail(f"secret material in {path.relative_to(ROOT)}")

    agents = AGENTS.read_text(encoding="utf-8")
    if "control-api" not in agents.lower() and "Control API" not in agents:
        # soft: prefer mention but control-plane reference is enough if AGENTS points to control plane
        if "Office Control Plane" not in agents and "control-plane" not in agents:
            fail("AGENTS.md should mention Control Plane / Control API")

    print("OK control-api schema+auth+actions+operational-honesty+tests")


if __name__ == "__main__":
    main()
