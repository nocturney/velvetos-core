#!/usr/bin/env python3
"""Keep the Project reel route, motion vocabulary and HyperFrames templates in sync."""
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
if (latest.get("baseProject") or {}).get("revision") != c.get("baseCreativeRevision"):
    fail("base Project revision drift")
if latest.get("reelRoute") != Path(c["routeDoc"]).name:
    fail("LATEST reelRoute binding drift")

route_text = route.read_text(encoding="utf-8")
instructions_text = instructions.read_text(encoding="utf-8")
preset_text = PRESETS.read_text(encoding="utf-8")
for needle in ("ANIMATED_RICH_STILL", "PRINTER_TO_SHELF", "REAL_PRINT_FILE_TURNTABLE", "RICH_STYLE_V2",
               "ready_for_publish", "PREFLIGHT", "EDIT-GATE", "reference match"):
    if needle not in route_text:
        fail(f"route doc missing required contract term {needle}")
for needle in ("REEL-ROUTE.md", "6.6.9", "Generative video models", "ready_for_publish"):
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
existing_presets = {"VELVET_HARD_CUT", "VELVET_MACRO_PUNCH", "VELVET_MATERIAL_LABEL", "VELVET_FINAL_STAMP"}
if status == "pending_pr2":
    for name in existing_presets:
        if name not in preset_text:
            fail(f"existing preset missing while PR2 pending: {name}")
    if template_root.exists() and any(template_root.glob("*.html")):
        fail("templates exist but contract is still pending_pr2")
elif status == "implemented":
    for name in presets:
        if name not in preset_text:
            fail(f"implemented preset missing: {name}")
    for name in templates:
        p = template_root / name
        if not p.is_file():
            fail(f"implemented template missing: {name}")
        body = p.read_text(encoding="utf-8")
        if name.removesuffix(".html") not in body:
            fail(f"template stable id marker missing: {name}")
else:
    fail(f"unknown implementationStatus {status!r}")

print(f"OK reel-route-sync revision={c['projectRevision']} status={status} templates={len(templates)} presets={len(presets)}")
