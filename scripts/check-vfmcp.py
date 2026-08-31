#!/usr/bin/env python3
"""Validate the Grok/GPT/Gemini/Perplexity tool-gap map on vfmcp. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAP = ROOT / "packages" / "vfmcp" / "GAP.md"
FIT = ROOT / "docs" / "MCP-FIT.md"
SHEETS = ROOT / "packages" / "vfbooks" / "SHEETS.md"
DESK = ROOT / ".cursor" / "vf-desk.json"
ORCHESTRA = ROOT / "constitution" / "ORCHESTRA.md"
ORIGIN = ROOT / "packages" / "vfmcp" / "ORIGIN.md"

NEEDLES_GAP = (
    "WebSearch",
    "GenerateImage",
    "Canva",
    "skip",
    "אין בכוונה",
    "SHEETS.md",
    "Treg",
)
NEEDLES_SHEETS = (
    "חסר גיליון",
    "exportMimeType",
    "לא ממציאים",
)


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (GAP, FIT, SHEETS, DESK, ORCHESTRA, ORIGIN):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    gap = GAP.read_text()
    for needle in NEEDLES_GAP:
        if needle not in gap:
            fail(f"GAP.md must mention {needle}")
    if "send_message" not in gap:
        fail("GAP.md must enable Gmail send_message")
    if "SEND.md" not in gap:
        fail("GAP.md must point at constitution/SEND.md")
    if "לא רלוונטי" not in gap and "not relevant" not in gap.lower():
        fail("GAP.md must mark Treg as not relevant")

    sheets = SHEETS.read_text()
    for needle in NEEDLES_SHEETS:
        if needle not in sheets:
            fail(f"SHEETS.md must mention {needle}")
    if "₪" in sheets and "X ₪" not in sheets and "לא ממציאים ₪" not in sheets:
        fail("SHEETS.md must not invent a sale ₪")

    fit = FIT.read_text()
    if "GAP.md" not in fit:
        fail("MCP-FIT.md must point at vfmcp/GAP.md")
    if "WebSearch" not in fit:
        fail("MCP-FIT.md must list WebSearch as already wired")

    desk = json.loads(DESK.read_text())
    tools = desk.get("tools") or {}
    for key in ("web", "image", "canva"):
        if key not in tools:
            fail(f"vf-desk.json tools missing {key}")
        if not (tools[key].get("failover") or ""):
            fail(f"vf-desk.json tools.{key} must declare failover")
    if (tools.get("canva") or {}).get("status") != "ready":
        fail("vf-desk.json canva.status must be ready after Cloud Agent verify")

    orchestra = ORCHESTRA.read_text()
    if "WebSearch" not in orchestra and "tools.web" not in orchestra:
        fail("ORCHESTRA.md must mention WebSearch / tools.web failover")
    if "GenerateImage" not in orchestra and "tools.image" not in orchestra:
        fail("ORCHESTRA.md must mention GenerateImage / tools.image failover")

    if "GAP.md" not in ORIGIN.read_text():
        fail("vfmcp/ORIGIN.md must mention GAP.md")

    print("OK vfmcp gap+sheets+desk web/image+canva-ready")


if __name__ == "__main__":
    main()
