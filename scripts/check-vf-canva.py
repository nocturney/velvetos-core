#!/usr/bin/env python3
"""Validate the vfcanva Instagram desk against the HQ catalog."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packages" / "vfcanva"
FORMATS = PACK / "FORMATS.json"
ORIGIN = PACK / "ORIGIN.md"
README = PACK / "README.md"
WORKFLOW = PACK / "WORKFLOW.md"
TEMPLATE = PACK / "jobs" / "TEMPLATE.md"
CONNECT = PACK / "CONNECT.md"
OPEN = PACK / "OPEN.md"
SKILL = ROOT / ".cursor" / "skills" / "vf-canva-instagram" / "SKILL.md"
RULE = ROOT / ".cursor" / "rules" / "vf-canva-instagram.mdc"
MAP = ROOT / ".cursor" / "vf-canva.json"
MCP = ROOT / ".cursor" / "mcp.json"
DOCS = ROOT / "docs" / "CANVA.md"
MANIFEST = ROOT / "packages" / "manifest.json"

REQUIRED_FORMAT_IDS = {
    "ig_feed_square",
    "ig_feed_portrait",
    "ig_story",
    "ig_reel_cover",
    "ig_carousel_square",
}

PIXELS = {
    "ig_feed_square": (1080, 1080),
    "ig_feed_portrait": (1080, 1350),
    "ig_story": (1080, 1920),
    "ig_reel_cover": (1080, 1920),
    "ig_carousel_square": (1080, 1080),
}


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (
        FORMATS,
        ORIGIN,
        README,
        WORKFLOW,
        TEMPLATE,
        CONNECT,
        OPEN,
        SKILL,
        RULE,
        MAP,
        MCP,
        DOCS,
        MANIFEST,
    ):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    formats = json.loads(FORMATS.read_text())
    desk = json.loads(MAP.read_text())
    mcp = json.loads(MCP.read_text())
    manifest = json.loads(MANIFEST.read_text())

    packs = {p["name"] for p in manifest.get("packs", [])}
    if "vfcanva" not in packs:
        fail("vfcanva missing from packages/manifest.json")

    row = next(p for p in manifest["packs"] if p["name"] == "vfcanva")
    if row.get("vendorStatus") != "hq-native":
        fail("vfcanva vendorStatus must be hq-native")
    if "2020e135" not in (row.get("bcId") or ""):
        fail("vfcanva bcId must be this HQ agent")

    if formats.get("account") != "@velvets_cloud":
        fail("FORMATS.json account must be @velvets_cloud")

    ids = {item["id"] for item in formats.get("formats", [])}
    if ids != REQUIRED_FORMAT_IDS:
        fail(f"format ids {sorted(ids)} != {sorted(REQUIRED_FORMAT_IDS)}")

    for item in formats["formats"]:
        fid = item["id"]
        w, h = PIXELS[fid]
        if item.get("width") != w or item.get("height") != h:
            fail(f"{fid} pixels {item.get('width')}x{item.get('height')} != {w}x{h}")
        dt = item.get("design_type") or {}
        if dt.get("type") != "custom" or dt.get("width") != w or dt.get("height") != h:
            fail(f"{fid} design_type must be custom {w}x{h}")

    if desk.get("pack") != "vfcanva":
        fail("vf-canva.json pack must be vfcanva")
    if desk.get("account") != "@velvets_cloud":
        fail("vf-canva.json account must be @velvets_cloud")
    for rel in (desk.get("skill"), desk.get("alwaysOnRule"), desk.get("formatsFile")):
        if not rel or not (ROOT / rel).is_file():
            fail(f"desk map missing file {rel}")

    servers = mcp.get("mcpServers") or {}
    canva = servers.get("canva") or {}
    url = str(canva.get("url") or "")
    args = " ".join(canva.get("args") or [])
    if "mcp-remote" in args or canva.get("command") == "npx":
        fail(".cursor/mcp.json must use url https://mcp.canva.com/mcp, not mcp-remote")
    if "mcp.canva.com/mcp" not in url:
        fail(".cursor/mcp.json must register url https://mcp.canva.com/mcp")

    rule = RULE.read_text()
    if "alwaysApply: true" not in rule:
        fail("vf-canva-instagram.mdc must be alwaysApply: true")
    for needle in ("does not send", "050-2517000", "Canva לא מחובר"):
        if needle not in rule:
            fail(f"rule missing {needle!r}")

    skill = SKILL.read_text()
    for needle in ("does **not** send", "FORMATS.json", "needsAuth"):
        if needle not in skill:
            fail(f"skill missing {needle!r}")

    print(f"OK vfcanva formats={len(ids)} skill+rule+mcp")


if __name__ == "__main__":
    main()
