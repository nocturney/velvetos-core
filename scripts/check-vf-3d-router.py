#!/usr/bin/env python3
"""Static + behavioral regression for the VelvetOS 3D router."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "scripts" / "vf_3d.py"
CAD = ROOT / "scripts" / "vf_cad.py"
BLENDER_DOC = ROOT / "packages" / "vfprod" / "BLENDER-MCP.md"
VFPROD_SKILL = ROOT / "packages" / "vfprod" / "SKILL.md"
EXPERT = ROOT / "packages" / "vfprod" / "experts" / "3D-MODEL.md"
MODULE = ROOT / "packages" / "velvetos" / "modules" / "expert-3d-model.md"
CURSOR_SKILL = ROOT / ".cursor" / "skills" / "vf-3d-router" / "SKILL.md"

COST_PREFIXES = [
    "blender-ai-mcp-",
    "design-os-3d-blender-",
    "cc-blender-skill-",
]


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def route(request: str) -> dict:
    cp = subprocess.run(
        [sys.executable, str(ROUTER), "route", "--request", request],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8",
    )
    if cp.returncode:
        fail("router command failed: " + cp.stderr[-500:])
    return json.loads(cp.stdout)


def main() -> None:
    for path in (ROUTER, CAD, BLENDER_DOC, VFPROD_SKILL, EXPERT, MODULE, CURSOR_SKILL):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    source = ROUTER.read_text(encoding="utf-8")
    for needle in ("TEXT_TO_CAD", "BLENDER_NATIVE", "HYBRID_CAD_THEN_BLENDER",
                   "127.0.0.1", "BLENDER_RPC_PORT", "configured_rpc_port",
                   "component_version", "detect_blender", "blender_addon_state",
                   "blender_rpc_probe", "host_benchmark", "windows_benchmark",
                   "MCP_SURFACE_PROFILE", "llm-guided",
                   "HF_HUB_OFFLINE", "VISION_ENABLED", "physical_print_authorized"):
        if needle not in source:
            fail(f"router missing contract: {needle}")
    for forbidden in (
        "start_print(", "upload_print(", "requests.post(",
        "Blender 5.2\\blender.exe", "Blender 5.1\\blender.exe",
        "43253155440f78ce208f7c4264bb8be6fb784ec7",
        "61390fd535d812a1763ec0d2b3fd9304591fa3e0",
    ):
        if forbidden in source:
            fail(f"unsafe or version-pinned 3D router contract: {forbidden}")

    cad_source = CAD.read_text(encoding="utf-8")
    for needle in ("discover_orca", "ORCASLICER_BIN", "OrcaSlicer*"):
        if needle not in cad_source:
            fail(f"CAD bridge missing dynamic slicer discovery: {needle}")
    if "OrcaSlicer-2.4.2" in cad_source:
        fail("CAD bridge must not pin OrcaSlicer 2.4.2")

    blender_doc = BLENDER_DOC.read_text(encoding="utf-8")
    for needle in ("blender-ai-mcp", "design-os-3d-blender", "127.0.0.1",
                   "mcp-for-blender", "PAID_OPTIONAL", "installed version",
                   "capability"):
        if needle not in blender_doc:
            fail(f"Blender authority missing: {needle}")
    for forbidden in (
        "pinned by the local install receipt",
        "pinned to commit",
        "Blender 5.2 knowledge",
    ):
        if forbidden in blender_doc:
            fail(f"Blender authority still version-pinned: {forbidden}")

    if "vf_3d.py" not in VFPROD_SKILL.read_text(encoding="utf-8"):
        fail("vfprod skill does not route through vf_3d.py")
    if "HYBRID_CAD_THEN_BLENDER" not in EXPERT.read_text(encoding="utf-8"):
        fail("3D expert lacks hybrid route")
    if "vf_3d.py" not in MODULE.read_text(encoding="utf-8"):
        fail("expert-3d-model module lacks router binding")

    cost_dir = ROOT / "packages" / "vfharness" / "cost-preflight"
    for prefix in COST_PREFIXES:
        if not list(cost_dir.glob(prefix + "*.json")):
            fail(f"missing cost preflight family {prefix}*.json")

    cases = [
        ("precision bracket 40 mm two holes tolerance STEP", "TEXT_TO_CAD"),
        ("פסלון דקורטיבי מתמונות רפרנס", "BLENDER_NATIVE"),
        ("תושבת במידות מדויקות עם מעטפת אורגנית לפי רפרנס", "HYBRID_CAD_THEN_BLENDER"),
        ("make this STL printable", "BLENDER_NATIVE"),
        ("reconstruct this reference and preserve exact mounting holes", "HYBRID_CAD_THEN_BLENDER"),
    ]
    for request, expected in cases:
        result = route(request)
        if result.get("route") != expected:
            fail(f"route mismatch: expected {expected}, got {result.get('route')}")
        if result.get("physical_print_authorized") is not False:
            fail("router must never authorize a physical print")
        if result.get("paid_external_generation_authorized") is not False:
            fail("router must not authorize paid external generation")

    print("check-vf-3d-router: PASS")


if __name__ == "__main__":
    main()
