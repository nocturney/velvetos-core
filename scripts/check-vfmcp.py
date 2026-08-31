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
MCP = ROOT / ".cursor" / "mcp.json"
ORCHESTRA = ROOT / "constitution" / "ORCHESTRA.md"
ORIGIN = ROOT / "packages" / "vfmcp" / "ORIGIN.md"
CONNECT_3DAI = ROOT / "packages" / "vfprod" / "CONNECT-3DAI.md"
PLAYBOOK_3DAI = ROOT / "packages" / "vfprod" / "3DAISTUDIO.md"

REQUIRED_MCP = {
    "canva": "https://mcp.canva.com/mcp",
    "threedaistudio": "https://mcp.3daistudio.com/mcp",
    "studiomcphub": "https://studiomcphub.com/mcp",
}

CORE_MCP = ROOT / "packages" / "vfmcp" / "core-mcp.json"
CONNECT_SHEETS = ROOT / "packages" / "vfmcp" / "CONNECT-SHEETS.md"
CONNECT_WA = ROOT / "packages" / "vfmcp" / "CONNECT-WHATSAPP.md"
CONNECT_HUB = ROOT / "packages" / "vfmcp" / "CONNECT-STUDIOHUB.md"
CORE_MCP_MD = ROOT / "packages" / "vfmcp" / "CORE-MCP.md"

NEEDLES_GAP = (
    "WebSearch",
    "GenerateImage",
    "Canva",
    "skip",
    "אין בכוונה",
    "SHEETS.md",
    "Treg",
    "3D AI Studio",
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
    for path in (
        GAP,
        FIT,
        SHEETS,
        DESK,
        MCP,
        ORCHESTRA,
        ORIGIN,
        CONNECT_3DAI,
        PLAYBOOK_3DAI,
        CORE_MCP,
        CONNECT_SHEETS,
        CONNECT_WA,
        CONNECT_HUB,
        CORE_MCP_MD,
    ):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    mcp = json.loads(MCP.read_text())
    servers = mcp.get("mcpServers") or {}
    for name, expected_url in REQUIRED_MCP.items():
        row = servers.get(name) or {}
        url = str(row.get("url") or "")
        if expected_url not in url:
            fail(f".cursor/mcp.json must register {name} url {expected_url}")
        args = " ".join(row.get("args") or [])
        if "mcp-remote" in args or row.get("command") == "npx":
            fail(f".cursor/mcp.json {name} must use HTTP url, not mcp-remote")

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
    if "3D AI Studio" not in fit:
        fail("MCP-FIT.md must map the owner 3D AI Studio account")

    studio = PLAYBOOK_3DAI.read_text()
    for needle in ("אין מפתח בגיט", "vlicense", "STL", "OAuth", "CONNECT-3DAI.md", "לא על Cloud Agent"):
        if needle not in studio:
            fail(f"3DAISTUDIO.md must mention {needle}")
    if "₪" in studio and "X ₪" not in studio:
        fail("3DAISTUDIO.md must not invent a sale ₪")

    connect = CONNECT_3DAI.read_text()
    for needle in ("threedaistudio", "mcp.3daistudio.com", "AI Assistants (MCP)"):
        if needle not in connect:
            fail(f"CONNECT-3DAI.md must mention {needle}")

    desk = json.loads(DESK.read_text())
    tools = desk.get("tools") or {}
    for key in ("web", "image", "canva"):
        if key not in tools:
            fail(f"vf-desk.json tools missing {key}")
        if not (tools[key].get("failover") or ""):
            fail(f"vf-desk.json tools.{key} must declare failover")
    if (tools.get("canva") or {}).get("status") != "ready":
        fail("vf-desk.json canva.status must be ready after Cloud Agent verify")

    threed = tools.get("threedaistudio") or {}
    if not threed:
        fail("vf-desk.json tools missing threedaistudio")
    if threed.get("mcp") != REQUIRED_MCP["threedaistudio"]:
        fail("vf-desk.json threedaistudio.mcp must match .cursor/mcp.json")
    if not (threed.get("failover") or ""):
        fail("vf-desk.json threedaistudio must declare failover")
    if "3DAISTUDIO.md" not in (threed.get("useWhen") or "") and "3DAISTUDIO.md" not in (threed.get("rule") or ""):
        fail("vf-desk.json threedaistudio must point at 3DAISTUDIO.md")

    hub = tools.get("studiomcphub") or {}
    if hub.get("mcp") != REQUIRED_MCP["studiomcphub"]:
        fail("vf-desk.json studiomcphub.mcp must match .cursor/mcp.json")
    if not (hub.get("failover") or ""):
        fail("vf-desk.json studiomcphub must declare failover")
    for key in ("mcp-gsheets", "whatsapp"):
        row = tools.get(key) or {}
        if not row:
            fail(f"vf-desk.json tools missing {key}")
        if not (row.get("failover") or ""):
            fail(f"vf-desk.json tools.{key} must declare failover")

    core_mcp = json.loads(CORE_MCP.read_text())
    ids = {s.get("id") for s in (core_mcp.get("servers") or [])}
    for need in ("studiomcphub", "mcp-gsheets", "whatsapp"):
        if need not in ids:
            fail(f"core-mcp.json must list {need}")
    if CORE_MCP.read_text().count("sk-") or "BEGIN PRIVATE" in CORE_MCP.read_text():
        fail("core-mcp.json must not contain secrets")

    for path, needles in (
        (CONNECT_HUB, ("studiomcphub.com/mcp", "Team MCP", "print_ready", "x402")),
        (CONNECT_SHEETS, ("mcp-gsheets", "~/.cursor/mcp.json", "חסר גיליון", "לא ממציאים")),
        (CONNECT_WA, ("lharries/whatsapp-mcp", "050-2517000", "send=false", "Infobip")),
        (CORE_MCP_MD, ("mcpBind", "studiomcphub", "mcp-gsheets", "WhatsApp")),
    ):
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                fail(f"{path.name} must mention {needle}")

    orchestra = ORCHESTRA.read_text()
    if "WebSearch" not in orchestra and "tools.web" not in orchestra:
        fail("ORCHESTRA.md must mention WebSearch / tools.web failover")
    if "GenerateImage" not in orchestra and "tools.image" not in orchestra:
        fail("ORCHESTRA.md must mention GenerateImage / tools.image failover")
    if "3D AI Studio" not in orchestra:
        fail("ORCHESTRA.md must failover 3D AI Studio to the site")

    if "GAP.md" not in ORIGIN.read_text():
        fail("vfmcp/ORIGIN.md must mention GAP.md")
    if "CORE-MCP.md" not in ORIGIN.read_text():
        fail("vfmcp/ORIGIN.md must mention CORE-MCP.md")

    print("OK vfmcp gap+sheets+desk web/image+canva-ready+3daistudio+office-mcp")


if __name__ == "__main__":
    main()
