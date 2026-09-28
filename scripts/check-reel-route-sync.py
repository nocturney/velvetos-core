#!/usr/bin/env python3
"""Keep the Project Reel route, legacy HyperFrames vocabulary and Adobe implementation in sync."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "packages/vfom/REEL-ROUTE-CONTRACT.json"
LATEST = ROOT / "packages/velvetos/chatgpt-project/LATEST.json"
PRESETS = ROOT / "packages/vfom/MOTION-PRESETS.md"


def fail(msg: str) -> None:
    print("FAIL reel-route-sync: " + msg, file=sys.stderr)
    raise SystemExit(1)


c = json.loads(CONTRACT.read_text(encoding="utf-8"))
latest = json.loads(LATEST.read_text(encoding="utf-8"))
route = ROOT / c["routeDoc"]
instructions = ROOT / c["projectInstructions"]
if not route.is_file() or not instructions.is_file() or not PRESETS.is_file():
    fail("route, project instructions or preset document missing")
if latest.get("revision") != c.get("projectRevision"):
    fail("LATEST revision differs from reel route contract")
if latest.get("revision") != "6.6.11":
    fail("Adobe Reel route must bind Project revision 6.6.11")
if (latest.get("baseProject") or {}).get("revision") != c.get("baseCreativeRevision"):
    fail("base Project revision drift")
if latest.get("reelRoute") != Path(c["routeDoc"]).name:
    fail("LATEST reelRoute binding drift")
if latest.get("instructions") != Path(c["projectInstructions"]).name:
    fail("LATEST instructions binding drift")

route_text = route.read_text(encoding="utf-8")
instructions_text = instructions.read_text(encoding="utf-8")
preset_text = PRESETS.read_text(encoding="utf-8")

for needle in (
    "ANIMATED_RICH_STILL", "PRINTER_TO_SHELF", "REAL_PRINT_FILE_TURNTABLE",
    "RICH_STYLE_V2", "ready_for_publish", "PREFLIGHT", "EDIT-GATE",
    "reference match", "EMPTY plate", "Photoshop", "After Effects",
    "1080x1920", "Select Subject", "CC Particle World",
    "py -3.14 scripts\\vf_ae_reel.py --job",
):
    if needle not in route_text:
        fail(f"route doc missing required contract term {needle}")
for needle in (
    "REEL-ROUTE.md", "6.6.9", "6.6.10", "Generative video models",
    "needs_review", "D:\\Velvet\\Runtime\\VelvetOS", "vf_ae_reel.py",
):
    if needle not in instructions_text:
        fail(f"Project instructions missing Reel binding {needle}")

templates = list(c.get("templates") or [])
presets = list(c.get("presets") or [])
if len(templates) != 5 or len(presets) != 8:
    fail("template/preset inventory drift")
for name in templates + presets:
    if name not in route_text:
        fail(f"route doc missing contract name {name}")

status = c.get("implementationStatus")
template_root = ROOT / c["templateRoot"]
if status != "implemented":
    fail(f"unknown implementationStatus {status!r}")
for name in presets:
    if name not in preset_text:
        fail(f"implemented preset missing: {name}")
for name in templates:
    path = template_root / name
    if not path.is_file():
        fail(f"implemented template missing: {name}")
    if name.removesuffix(".html") not in path.read_text(encoding="utf-8"):
        fail(f"template stable id marker missing: {name}")

adobe = c.get("adobe") or {}
expected = {
    "jobSchema": "packages/vfom/adobe/REEL-JOB.schema.json",
    "photoshopScript": "packages/vfom/adobe/photoshop-product-layer.jsx",
    "afterEffectsScript": "packages/vfom/adobe/build-reel.jsx",
    "orchestrator": "scripts/vf_ae_reel.py",
}
if adobe != expected:
    fail("Adobe implementation binding drift")
for rel in expected.values():
    path = ROOT / rel
    if not path.is_file():
        fail(f"Adobe implementation file missing: {rel}")
    if rel not in route_text:
        fail(f"route doc missing Adobe binding {rel}")

print(
    f"OK reel-route-sync revision={c['projectRevision']} status={status} "
    f"templates={len(templates)} presets={len(presets)} adobe=PASS"
)
