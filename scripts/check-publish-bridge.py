#!/usr/bin/env python3
"""Static contract sensor for the VelvetOS publish bridge. No network."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "packages" / "vfigos" / "PUBLISH-BRIDGE.json"
DOC = ROOT / "packages" / "vfigos" / "PUBLISH-BRIDGE.md"
STAGE = ROOT / "scripts" / "vf_publish_bridge.py"
CLEAN = ROOT / "scripts" / "vf_publish_bridge_cleanup.py"
WORKFLOW = ROOT / ".github" / "workflows" / "publish-bridge-cleanup.yml"
SEND = ROOT / "packages" / "vfigos" / "SEND.md"
INSTANCE = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    for path in (CFG, DOC, STAGE, CLEAN, WORKFLOW, SEND, INSTANCE):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    if cfg.get("status") != "active":
        fail("bridge status must be active")
    if cfg.get("branch") != "publish-bridge":
        fail("bridge must use dedicated publish-bridge branch")
    if cfg.get("branch") == "main":
        fail("bridge assets must never target main")
    base = str(cfg.get("publicBaseUrl") or "")
    if not base.startswith("https://raw.githubusercontent.com/"):
        fail("publicBaseUrl must be HTTPS raw GitHub URL")
    if cfg.get("retention", {}).get("historyErasure") is not False:
        fail("contract must explicitly state Git cleanup is not history erasure")
    if cfg.get("publicReleaseGate") != "approved_for_public_release":
        fail("public release gate missing")

    send = SEND.read_text(encoding="utf-8")
    if "PUBLISH-BRIDGE.md" not in send or "publish-bridge" not in send:
        fail("SEND.md must route private-source derivatives through publish bridge")

    instance = json.loads(INSTANCE.read_text(encoding="utf-8"))
    ig = ((instance.get("mcpBind") or {}).get("instagram") or {})
    creative_publish = (((instance.get("creativeAutonomy") or {}).get("publish")) or {})
    expected = "packages/vfigos/PUBLISH-BRIDGE.json"
    if ig.get("publishBridge") != expected:
        fail("instance Instagram binding missing canonical publishBridge")
    if creative_publish.get("transportBridge") != expected:
        fail("creativeAutonomy.publish missing canonical transportBridge")
    if creative_publish.get("transportBridgeRequiredForPrivateAssets") is not True:
        fail("private publish assets must require the transport bridge")

    print("OK publish bridge active · instance-bound · dedicated branch · public-release gate · cleanup sensor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
