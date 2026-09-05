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
CONNECT_GEMINI = ROOT / "packages" / "vfmcp" / "CONNECT-GEMINI.md"
CONNECT_CHATGPT = ROOT / "packages" / "vfmcp" / "CONNECT-CHATGPT.md"
SUBSCRIPTIONS = ROOT / "packages" / "vfmcp" / "SUBSCRIPTIONS.md"
CORE_MCP_MD = ROOT / "packages" / "vfmcp" / "CORE-MCP.md"
VF_GEMINI = ROOT / "scripts" / "vf_gemini.py"
VF_CHATGPT = ROOT / "scripts" / "vf_chatgpt.py"

NEEDLES_GAP = (
    "WebSearch",
    "GenerateImage",
    "Canva",
    "skip",
    "אין בכוונה",
    "SHEETS.md",
    "Treg",
    "3D AI Studio",
    "חסר מפתח Gemini",
    "חסר מפתח ChatGPT",
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
        CONNECT_GEMINI,
        CONNECT_CHATGPT,
        SUBSCRIPTIONS,
        CORE_MCP_MD,
        VF_GEMINI,
        VF_CHATGPT,
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
    for needle in ("אין מפתח בגיט", "vlicense", "STL", "OAuth", "CONNECT-3DAI.md", "3DAIStudio"):
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
    for need in ("studiomcphub", "mcp-gsheets", "whatsapp", "gemini-api", "chatgpt-api"):
        if need not in ids:
            fail(f"core-mcp.json must list {need}")
    if CORE_MCP.read_text().count("sk-") or "BEGIN PRIVATE" in CORE_MCP.read_text():
        fail("core-mcp.json must not contain secrets")

    for path, needles in (
        (CONNECT_HUB, ("studiomcphub.com/mcp", "Team MCP", "print_ready", "x402")),
        (CONNECT_SHEETS, ("mcp-gsheets", "~/.cursor/mcp.json", "חסר גיליון", "לא ממציאים")),
        (CONNECT_WA, ("lharries/whatsapp-mcp", "050-2517000", "send=false", "Infobip")),
        (CONNECT_GEMINI, ("חסר מפתח Gemini", "vf_gemini.py", "aliargun", "gemini.google.com", "לא ממציאים", "RLabs")),
        (CONNECT_CHATGPT, ("חסר מפתח ChatGPT", "vf_chatgpt.py", "chatgpt.com", "OPENAI_API_KEY", "לא ממציאים")),
        (SUBSCRIPTIONS, ("חסר מפתח Gemini", "חסר מפתח ChatGPT", "עוגיות", "chatgpt.com", "gemini.google.com", "vf_chatgpt.py", "perplexity-user-mcp", "patchright")),
        (CORE_MCP_MD, ("mcpBind", "studiomcphub", "mcp-gsheets", "WhatsApp", "Gemini API", "ChatGPT API")),
    ):
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                fail(f"{path.name} must mention {needle}")

    gemini = tools.get("gemini") or {}
    if not gemini:
        fail("vf-desk.json tools missing gemini")
    if "vf_gemini.py" not in (gemini.get("command") or "") and "vf_gemini.py" not in (gemini.get("failover") or ""):
        fail("vf-desk.json gemini must call vf_gemini.py")
    if not (gemini.get("failover") or ""):
        fail("vf-desk.json gemini must declare failover")
    if "חסר מפתח Gemini" not in (gemini.get("rule") or ""):
        fail("vf-desk.json gemini.rule must mention חסר מפתח Gemini")

    chatgpt = tools.get("chatgpt") or {}
    if not chatgpt:
        fail("vf-desk.json tools missing chatgpt")
    if "vf_chatgpt.py" not in (chatgpt.get("command") or "") and "vf_chatgpt.py" not in (chatgpt.get("failover") or ""):
        fail("vf-desk.json chatgpt must call vf_chatgpt.py")
    if not (chatgpt.get("failover") or ""):
        fail("vf-desk.json chatgpt must declare failover")
    if "חסר מפתח ChatGPT" not in (chatgpt.get("rule") or ""):
        fail("vf-desk.json chatgpt.rule must mention חסר מפתח ChatGPT")

    orchestra = ORCHESTRA.read_text()
    if "WebSearch" not in orchestra and "tools.web" not in orchestra:
        fail("ORCHESTRA.md must mention WebSearch / tools.web failover")
    if "GenerateImage" not in orchestra and "tools.image" not in orchestra:
        fail("ORCHESTRA.md must mention GenerateImage / tools.image failover")
    if "3D AI Studio" not in orchestra:
        fail("ORCHESTRA.md must failover 3D AI Studio to the site")
    if "vf_gemini.py" not in orchestra:
        fail("ORCHESTRA.md must failover Gemini browser wall to vf_gemini.py")
    if "חסר מפתח Gemini" not in orchestra:
        fail("ORCHESTRA.md must mention חסר מפתח Gemini")
    if "vf_chatgpt.py" not in orchestra:
        fail("ORCHESTRA.md must failover ChatGPT to vf_chatgpt.py")
    if "חסר מפתח ChatGPT" not in orchestra:
        fail("ORCHESTRA.md must mention חסר מפתח ChatGPT")
    if "SUBSCRIPTIONS.md" not in orchestra and "לא פותחים" not in orchestra:
        fail("ORCHESTRA.md must forbid Cloud browser login to subscription sites")
    if "perplexity-user-mcp" not in orchestra and "vscode-perplexity" not in orchestra:
        fail("ORCHESTRA.md must skip vscode-perplexity-mcp / perplexity-user-mcp on Cloud")

    if "GAP.md" not in ORIGIN.read_text():
        fail("vfmcp/ORIGIN.md must mention GAP.md")
    if "CORE-MCP.md" not in ORIGIN.read_text():
        fail("vfmcp/ORIGIN.md must mention CORE-MCP.md")
    if "CONNECT-GEMINI.md" not in ORIGIN.read_text() and "vf_gemini.py" not in ORIGIN.read_text():
        fail("vfmcp/ORIGIN.md must mention the Gemini API bridge")
    if "CONNECT-CHATGPT.md" not in ORIGIN.read_text() and "vf_chatgpt.py" not in ORIGIN.read_text():
        fail("vfmcp/ORIGIN.md must mention the ChatGPT API bridge")
    if "SUBSCRIPTIONS.md" not in ORIGIN.read_text():
        fail("vfmcp/ORIGIN.md must mention SUBSCRIPTIONS.md")

    sys.path.insert(0, str(ROOT / "scripts"))
    import vf_gemini  # noqa: E402

    if vf_gemini.MISSING_KEY != "חסר מפתח Gemini":
        fail("vf_gemini.MISSING_KEY must be חסר מפתח Gemini")
    mock = [
        {"name": "models/gemini-2.5-pro", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-3.5-flash", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-3.1-pro-preview", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-embedding-001", "supportedGenerationMethods": ["embedContent"]},
        {"name": "models/veo-3.0-generate", "supportedGenerationMethods": ["predict"]},
        {"name": "models/gemini-2.5-flash-image", "supportedGenerationMethods": ["generateContent"]},
    ]
    flash = vf_gemini.pick_generate_model(mock)
    if flash != "gemini-3.5-flash":
        fail(f"live picker should prefer 3.5 flash, got {flash}")
    pro = vf_gemini.pick_generate_model(mock, prefer_pro=True)
    if pro != "gemini-3.1-pro-preview":
        fail(f"live picker --pro should prefer 3.1 pro, got {pro}")
    forced = vf_gemini.pick_generate_model(mock, requested="gemini-2.5-pro")
    if forced != "gemini-2.5-pro":
        fail("requested model must win when on the live list")

    import os
    import subprocess

    env = {k: v for k, v in os.environ.items() if k not in {"GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY", "CHATGPT_API_KEY"}}
    proc = subprocess.run(
        [sys.executable, str(VF_GEMINI), "status"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    if proc.returncode != 2:
        fail(f"vf_gemini.py status without key must exit 2, got {proc.returncode}")
    out = (proc.stdout or "") + (proc.stderr or "")
    if "חסר מפתח Gemini" not in out:
        fail("vf_gemini.py status without key must print חסר מפתח Gemini")
    if "AIza" in out or "sk-" in out:
        fail("vf_gemini.py must not print secrets")

    import vf_chatgpt  # noqa: E402

    if vf_chatgpt.MISSING_KEY != "חסר מפתח ChatGPT":
        fail("vf_chatgpt.MISSING_KEY must be חסר מפתח ChatGPT")
    gpt_mock = [
        {"id": "gpt-4o-mini"},
        {"id": "gpt-4.1"},
        {"id": "text-embedding-3-large"},
        {"id": "dall-e-3"},
        {"id": "gpt-5"},
    ]
    gpt_pick = vf_chatgpt.pick_chat_model(gpt_mock)
    if gpt_pick != "gpt-5":
        fail(f"chatgpt picker should prefer gpt-5, got {gpt_pick}")
    proc2 = subprocess.run(
        [sys.executable, str(VF_CHATGPT), "status"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    if proc2.returncode != 2:
        fail(f"vf_chatgpt.py status without key must exit 2, got {proc2.returncode}")
    out2 = (proc2.stdout or "") + (proc2.stderr or "")
    if "חסר מפתח ChatGPT" not in out2:
        fail("vf_chatgpt.py status without key must print חסר מפתח ChatGPT")
    if "sk-" in out2:
        fail("vf_chatgpt.py must not print secrets")

    print("OK vfmcp gap+sheets+desk web/image+canva-ready+3daistudio+office-mcp+gemini-api+chatgpt-api")


if __name__ == "__main__":
    main()
