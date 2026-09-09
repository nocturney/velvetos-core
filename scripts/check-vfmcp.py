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
CONNECT_IG = ROOT / "packages" / "vfigos" / "CONNECT-IG.md"
CONNECT_ICLOUD = ROOT / "packages" / "vfmcp" / "CONNECT-ICLOUD.md"
SUBSCRIPTIONS = ROOT / "packages" / "vfmcp" / "SUBSCRIPTIONS.md"
HOST = ROOT / "packages" / "vfmcp" / "HOST.md"
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
        CONNECT_IG,
        CONNECT_ICLOUD,
        SUBSCRIPTIONS,
        HOST,
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
    for key in ("mcp-gsheets", "whatsapp", "instagram", "icloud"):
        row = tools.get(key) or {}
        if not row:
            fail(f"vf-desk.json tools missing {key}")
        if not (row.get("failover") or ""):
            fail(f"vf-desk.json tools.{key} must declare failover")
    ig = tools.get("instagram") or {}
    ig_ok_status = ("needsAuth", "ready", "ready-codespace", "ready-local")
    if ig.get("status") not in ig_ok_status:
        fail("vf-desk.json instagram.status must be needsAuth|ready|ready-codespace|ready-local")
    if "CONNECT-IG.md" not in (ig.get("connect") or "") and "CONNECT-IG.md" not in (ig.get("useWhen") or ""):
        fail("vf-desk.json instagram must point at CONNECT-IG.md")
    forbidden_blob = " ".join(ig.get("forbidden") or []).lower()
    if "send_dm" not in forbidden_blob and "auto-dm" not in forbidden_blob and "send_message" not in forbidden_blob:
        fail("vf-desk.json instagram must forbid send_dm / auto-dm / DM send_message")
    mcp_blob = f"{ig.get('mcp') or ''} {ig.get('source') or ''} {ig.get('package') or ''}"
    if "adelaidasofia" not in mcp_blob.lower() and "adelaidasofia" not in (ig.get("rule") or "").lower():
        fail("vf-desk.json instagram must point at adelaidasofia/instagram-mcp as canonical")
    if "jlbadano" in (ig.get("mcp") or "").lower() and "legacy" not in (ig.get("legacyMcp") or "").lower():
        # primary mcp field must not still be jlbadano
        if "adelaidasofia" not in (ig.get("mcp") or "").lower():
            fail("vf-desk.json instagram.mcp must not list jlbadano as primary")
    if ig.get("status") in ("ready-codespace", "ready-local", "ready"):
        if ig.get("status") == "ready-codespace" and ig.get("remote_access") not in ("pending", "ready"):
            fail("ready-codespace must declare remote_access pending|ready")
        if ig.get("auth") not in (None, "ready", "ok"):
            fail("instagram.auth when set must be ready")
        if ig.get("dmEnabled") is True:
            fail("instagram.dmEnabled must stay false")
        if "publish_story" not in " ".join(ig.get("allowed") or []) and ig.get("stories") not in (
            "enabled-same-mcp",
            True,
            "enabled",
        ):
            fail("instagram must allow publish_story / stories on same MCP")
    icloud = tools.get("icloud") or {}
    if "CONNECT-ICLOUD.md" not in (icloud.get("useWhen") or "") and "CONNECT-ICLOUD.md" not in (icloud.get("rule") or ""):
        fail("vf-desk.json icloud must point at CONNECT-ICLOUD.md")

    core_mcp = json.loads(CORE_MCP.read_text())
    ids = {s.get("id") for s in (core_mcp.get("servers") or [])}
    for need in ("studiomcphub", "mcp-gsheets", "whatsapp", "gemini-api", "chatgpt-api", "instagram"):
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
        (CONNECT_IG, (
            "adelaidasofia/instagram-mcp",
            "publish_image",
            "publish_story",
            "אוטו־DM",
            "SEND.md",
            "אין ספירה",
            "liveVerified",
            "INSTAGRAM_MCP_ACCESS_TOKEN",
            "remote_access",
            "CHATGPT-MCP.md",
            "VELVET_INSTAGRAM_MCP_BEARER_TOKEN",
            "API key",
        )),
        (CONNECT_ICLOUD, ("iCloud", "Cloud Agent", "ICLOUD-DRIVE-SYNC.md", "Drive")),
        (SUBSCRIPTIONS, ("חסר מפתח Gemini", "חסר מפתח ChatGPT", "עוגיות", "chatgpt.com", "gemini.google.com", "vf_chatgpt.py", "perplexity-user-mcp", "patchright", "HOST.md")),
        (HOST, ("המק בשדרות", "codex login", "Gemini CLI", "perplexity.ai", "Cloud Agent", "לא ממציאים", "agent worker", "computer-use")),
        (CORE_MCP_MD, ("mcpBind", "studiomcphub", "mcp-gsheets", "WhatsApp", "Gemini API", "ChatGPT API", "adelaidasofia")),
    ):
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                fail(f"{path.name} must mention {needle}")
    connect_ig_text = CONNECT_IG.read_text(encoding="utf-8")
    chatgpt_mcp = ROOT / "packages" / "vfigos" / "CHATGPT-MCP.md"
    if not chatgpt_mcp.is_file():
        fail("missing packages/vfigos/CHATGPT-MCP.md")
    chatgpt_text = chatgpt_mcp.read_text(encoding="utf-8")
    for needle in (
        "API key",
        "VELVET_INSTAGRAM_MCP_BEARER_TOKEN",
        "No Auth",
        "does not implement OAuth",
        "401",
        "INSTAGRAM_MCP_ACCESS_TOKEN",
        "CONNECTED + VERIFIED",
    ):
        if needle not in chatgpt_text:
            fail(f"CHATGPT-MCP.md must mention {needle}")
    remote_dir = ROOT / "packages" / "vfigos" / "remote"
    for rel in (
        "http_server.py",
        "Dockerfile",
        "deploy.sh",
        "smoke_public.py",
        "README.md",
        "insights_v21.py",
        "mutations.py",
        "cta_tools.py",
        "cta_audit.py",
        "test_insights_v21.py",
    ):
        if not (remote_dir / rel).is_file():
            fail(f"missing packages/vfigos/remote/{rel}")
    remote_http = (remote_dir / "http_server.py").read_text(encoding="utf-8")
    for needle in (
        "StaticTokenVerifier",
        "VELVET_INSTAGRAM_MCP_BEARER_TOKEN",
        "INSTAGRAM_MCP_ACCESS_TOKEN",
        "streamable-http",
        "chatgpt.com",
        "insights_v21",
        "apply_insights_patch",
        "apply_mutation_tools",
        "apply_cta_audit_tools",
    ):
        if needle not in remote_http:
            fail(f"remote/http_server.py must mention {needle}")
    insights_src = (remote_dir / "insights_v21.py").read_text(encoding="utf-8")
    for needle in (
        "metric_type",
        "total_value",
        "impressions",
        "profile_views",
        "total_interactions",
        "DEFAULT_ACCOUNT_METRICS_V21",
        "partition_account_metrics",
        "partition_account_metrics_by_period",
        "period_incompatible",
        "MEDIA_METRIC_ALIASES",
        "DEFAULT_MEDIA_METRICS_REELS",
        "saved",
    ):
        if needle not in insights_src:
            fail(f"remote/insights_v21.py must mention {needle}")
    if "reach,impressions,profile_views,follower_count" in insights_src:
        fail("insights_v21 must not keep the broken upstream default string as active default")
    # Media must not apply account saved→saves remap (live Reel #100 metric[4]).
    if "ACCOUNT_METRIC_ALIASES.get(p.lower(), p)" in insights_src:
        fail("get_media_insights must not remap via ACCOUNT_METRIC_ALIASES (saves≠saved)")
    if '"saved": "saves"' in insights_src and "MEDIA_METRIC_ALIASES" not in insights_src:
        fail("media insights must keep a separate MEDIA_METRIC_ALIASES map")
    mutations_md = ROOT / "packages" / "vfigos" / "GRAPH-MUTATIONS.md"
    if not mutations_md.is_file():
        fail("missing packages/vfigos/GRAPH-MUTATIONS.md")
    mut_text = mutations_md.read_text(encoding="utf-8")
    for needle in (
        "unsupported_by_official_graph",
        "update_biography",
        "update_media_caption",
        "delete_media",
        "instagram_manage_contents",
        "graph_mutation_matrix",
        "Not exposed",
    ):
        if needle not in mut_text:
            fail(f"GRAPH-MUTATIONS.md must mention {needle}")
    mutations_py = (remote_dir / "mutations.py").read_text(encoding="utf-8")
    if "NEVER_EXPOSE_AS_WRITE_TOOLS" not in mutations_py:
        fail("mutations.py must define NEVER_EXPOSE_AS_WRITE_TOOLS")
    # Misleading write tools must not be registered as @mcp.tool functions.
    if "def update_profile(" in mutations_py or "def update_media_caption(" in mutations_py:
        fail("mutations.py must not register update_profile/update_media_caption as MCP tools")
    if "def graph_mutation_matrix(" not in mutations_py:
        fail("mutations.py must expose graph_mutation_matrix as capability SoT")
    caps = json.loads((ROOT / "packages" / "vfigos" / "CAPABILITIES.json").read_text(encoding="utf-8"))
    for cap_id in ("instagram.profile.update", "instagram.media.caption.update"):
        row = next((c for c in (caps.get("capabilities") or []) if c.get("id") == cap_id), None)
        if not row:
            fail(f"CAPABILITIES missing {cap_id}")
        if row.get("supported") is not False:
            fail(f"{cap_id} must set supported=false")
        cap_tools = row.get("tools") or []
        if "update_profile" in cap_tools or "update_media_caption" in cap_tools:
            fail(f"{cap_id} must not list misleading write tool names")
        if "graph_mutation_matrix" not in cap_tools:
            fail(f"{cap_id} must point agents at graph_mutation_matrix SoT")
    rv = caps.get("remoteVerify") or {}
    if rv.get("chatgptConnected") is not True:
        fail("CAPABILITIES remoteVerify.chatgptConnected must be true after 2026-09-09 verify")
    if (rv.get("insightsGraphCompat") or {}).get("deployed") is True and not (
        remote_dir / "insights_v21.py"
    ).is_file():
        fail("insights marked deployed but insights_v21.py missing")
    # Insights must not be marked fixed until public smoke post-deploy.
    if (rv.get("insightsGraphCompat") or {}).get("deployed") is True and (
        rv.get("chatgptSmoke") or {}
    ).get("get_account_insights_default") == "FAIL_pre_patch_impressions":
        fail("CAPABILITIES cannot claim insights deployed while chatgptSmoke still FAIL_pre_patch")
    cta_audit = ROOT / "packages" / "vfigos" / "cta_audit.py"
    if not cta_audit.is_file():
        fail("missing packages/vfigos/cta_audit.py")
    if "050-2517000" not in cta_audit.read_text(encoding="utf-8"):
        fail("cta_audit.py must know BUSINESS_CONTACT_RECORD phone for detection")
    if "TOKEN-WATCH.md" not in connect_ig_text and "token-watch" not in connect_ig_text.lower():
        fail("CONNECT-IG.md must mention TOKEN-WATCH / token-watch")
    token_watch = ROOT / "packages" / "vfigos" / "data" / "token-watch.json"
    if not token_watch.is_file():
        fail("missing packages/vfigos/data/token-watch.json")
    tw = json.loads(token_watch.read_text(encoding="utf-8"))
    if any(k in tw for k in ("access_token", "accessToken", "token")):
        fail("token-watch.json must not store token values")
    if "never-store-access-token" not in (tw.get("locks") or []):
        fail("token-watch.json must lock never-store-access-token")
    if tw.get("expiresAt") not in (None, "") and not (
        tw.get("expiresAtSource") or (tw.get("expiryEvidence") or {}).get("source")
    ):
        fail("token-watch expiresAt requires expiresAtSource or expiryEvidence.source when set")
    mode = (tw.get("expiryMode") or "unknown").strip()
    if mode not in {"unknown", "limited", "none"}:
        fail("token-watch expiryMode must be unknown|limited|none")
    if mode == "none":
        src = ((tw.get("expiryEvidence") or {}).get("source") or "").lower()
        if src not in {"owner-reported-meta", "owner_reported_meta"}:
            fail("expiryMode=none requires expiryEvidence.source=owner-reported-meta")
    if mode == "limited" and not tw.get("expiresAt"):
        fail("expiryMode=limited requires expiresAt")
    plane_src = (ROOT / "scripts" / "vf_control_plane.py").read_text(encoding="utf-8")
    if "classify_token_expiry" not in plane_src or "run_token_watch_behavior_tests" not in plane_src:
        fail("vf_control_plane.py must define classify_token_expiry + run_token_watch_behavior_tests")
    token_watch_md = ROOT / "packages" / "vfigos" / "TOKEN-WATCH.md"
    if not token_watch_md.is_file():
        fail("missing packages/vfigos/TOKEN-WATCH.md")
    tw_md = token_watch_md.read_text(encoding="utf-8")
    for needle in ("expiryMode", "owner-reported-meta", "unknown", "limited", "none"):
        if needle not in tw_md:
            fail(f"TOKEN-WATCH.md must mention {needle}")

    # Canonical must not still present jlbadano as the primary install path
    if "git clone https://github.com/jlbadano/ig-mcp" in connect_ig_text:
        fail("CONNECT-IG.md must not clone jlbadano as primary install")
    if "jlbadano/ig-mcp" in connect_ig_text and "לגאסי" not in connect_ig_text and "LEGACY" not in connect_ig_text and "legacy" not in connect_ig_text.lower():
        fail("CONNECT-IG.md may mention jlbadano only as legacy")
    if "Stories" in connect_ig_text and "לא Story" in connect_ig_text:
        fail("CONNECT-IG.md must not claim Stories unsupported")
    if connect_ig_text.count("https://github.com/adelaidasofia/instagram-mcp") < 1:
        fail("CONNECT-IG.md must declare adelaidasofia canonical repo")
    # Secrets must not appear in tracked Instagram docs/config
    for secret_path in (CONNECT_IG, CORE_MCP, DESK, ROOT / "packages" / "vfmcp" / "mcp.desktop.example.json"):
        blob = secret_path.read_text(encoding="utf-8")
        if "EAA" in blob or "IGQV" in blob:
            fail(f"{secret_path.name} must not contain Meta token-looking strings")
        if "BEGIN PRIVATE" in blob or "sk-" in blob:
            fail(f"{secret_path.name} must not contain private key material")

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
    if "HOST.md" not in orchestra:
        fail("ORCHESTRA.md must point 06:15 subscription desks at HOST.md")

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
    if "HOST.md" not in ORIGIN.read_text():
        fail("vfmcp/ORIGIN.md must mention HOST.md")
    origin_text = ORIGIN.read_text()
    if "CONNECT-IG.md" not in origin_text and "instagram-mcp" not in origin_text:
        fail("vfmcp/ORIGIN.md must mention CONNECT-IG.md / instagram-mcp")

    desktop = (ROOT / "packages" / "vfmcp" / "mcp.desktop.example.json").read_text(encoding="utf-8")
    if "instagram" not in desktop or "instagram-mcp" not in desktop:
        fail("mcp.desktop.example.json must include adelaidasofia instagram-mcp server")
    if "INSTAGRAM_MCP_ACCESS_TOKEN" not in desktop:
        fail("mcp.desktop.example.json must use INSTAGRAM_MCP_ACCESS_TOKEN env passthrough")
    ig_block = desktop
    if '"instagram"' in desktop:
        ig_block = desktop.split('"instagram"', 1)[1]
        if '"icloud"' in ig_block:
            ig_block = ig_block.split('"icloud"', 1)[0]
    if "jlbadano" in ig_block or "/ABS/PATH/ig-mcp" in ig_block or "instagram_mcp_server.py" in ig_block:
        fail("mcp.desktop.example.json must not use jlbadano/ig-mcp as primary")
    if "icloud" not in desktop:
        fail("mcp.desktop.example.json must include icloud desktop server")

    core_ig = next((s for s in (core_mcp.get("servers") or []) if s.get("id") == "instagram"), None)
    if not core_ig:
        fail("core-mcp.json missing instagram server")
    if "adelaidasofia" not in (core_ig.get("source") or ""):
        fail("core-mcp.json instagram.source must be adelaidasofia/instagram-mcp")
    if core_ig.get("canonical") is False:
        fail("core-mcp.json must keep a single canonical Instagram MCP")
    # Only one Instagram server id
    ig_servers = [s for s in (core_mcp.get("servers") or []) if s.get("id") == "instagram"]
    if len(ig_servers) != 1:
        fail("core-mcp.json must declare exactly one canonical Instagram MCP id")

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

    preflight = ROOT / "scripts" / "vf_send_preflight.py"
    if not preflight.is_file():
        fail("missing scripts/vf_send_preflight.py")
    send_law = (ROOT / "constitution" / "SEND.md").read_text(encoding="utf-8")
    if "vf_send_preflight.py" not in send_law:
        fail("constitution/SEND.md must mention vf_send_preflight.py")
    vfigos_send = (ROOT / "packages" / "vfigos" / "SEND.md").read_text(encoding="utf-8")
    if "vf_send_preflight.py" not in vfigos_send:
        fail("vfigos/SEND.md must mention vf_send_preflight.py")
    proc3 = subprocess.run(
        [sys.executable, str(preflight)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    if proc3.returncode != 0:
        fail(f"vf_send_preflight.py must exit 0: {proc3.stderr or proc3.stdout}")
    try:
        report = json.loads(proc3.stdout)
    except json.JSONDecodeError as exc:
        fail(f"vf_send_preflight.py must print JSON: {exc}")
    if not report.get("ok") or "channels" not in report:
        fail("vf_send_preflight.py report missing ok/channels")
    for need in ("gmail", "instagram", "canva", "gemini", "chatgpt"):
        if need not in report["channels"]:
            fail(f"vf_send_preflight.py missing channel {need}")
    proc4 = subprocess.run(
        [sys.executable, str(preflight), "--gate", "instagram"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    # Desk IG is needsAuth → expect failover exit 2 (actionable, not idle)
    if proc4.returncode not in (0, 2):
        fail(f"vf_send_preflight --gate instagram must exit 0 or 2, got {proc4.returncode}")

    print("OK vfmcp gap+sheets+desk web/image+canva-ready+3daistudio+office-mcp+gemini-api+chatgpt-api+instagram-mcp+icloud+send-preflight")


if __name__ == "__main__":
    main()
