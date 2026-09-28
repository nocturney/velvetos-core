#!/usr/bin/env python3
"""Fail closed when the Reel route vocabulary drifts from its contract/templates/presets."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "packages/vfom/REEL-ROUTE-CONTRACT.json"
PRESETS = ROOT / "packages/vfom/MOTION-PRESETS.md"

def fail(msg: str) -> None:
    print("FAIL reel-route-sync: " + msg, file=sys.stderr)
    raise SystemExit(1)

c = json.loads(CONTRACT.read_text(encoding="utf-8"))
route = ROOT / c["routeDoc"]
if not route.is_file() or not PRESETS.is_file():
    fail("route doc or preset document missing")
route_text = route.read_text(encoding="utf-8")
preset_text = PRESETS.read_text(encoding="utf-8")
names = list(c.get("presets") or [])
templates = list(c.get("templates") or [])
if not names or not templates:
    fail("contract needs non-empty presets and templates")
for name in names:
    if name not in route_text:
        fail(f"route doc no longer names preset {name}")
for name in templates:
    if name not in route_text:
        fail(f"route doc no longer names template {name}")

status = c.get("implementationStatus")
root = ROOT / c["templateRoot"]
if status == "implemented":
    for name in names:
        if name not in preset_text:
            fail(f"implemented preset missing from MOTION-PRESETS.md: {name}")
    for name in templates:
        path = root / name
        if not path.is_file():
            fail(f"implemented template missing: {path.relative_to(ROOT)}")
        if name.removesuffix(".html") not in path.read_text(encoding="utf-8"):
            fail(f"template lacks stable id marker: {name}")
elif status == "pending_templates_and_editorial_presets":
    existing = ("VELVET_HARD_CUT", "VELVET_MACRO_PUNCH", "VELVET_MATERIAL_LABEL", "VELVET_FINAL_STAMP")
    for name in existing:
        if name not in preset_text:
            fail(f"existing preset disappeared during pending phase: {name}")
    if root.exists() and any(root.glob("*.html")):
        fail("template implementation started without flipping contract to implemented")
else:
    fail(f"unknown implementationStatus: {status!r}")

print(f"OK reel-route-sync status={status} presets={len(names)} templates={len(templates)}")
