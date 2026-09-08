#!/usr/bin/env python3
"""Sensor: Instagram remote MCP autonomy honesty. No network. No secrets.

Guarantees:
  - remote_access cannot be ready without endpoint + successful remote-health.json
  - local stdio / ready-codespace is not mistaken for remote autonomy
  - no secret literals in tracked remote config
  - DM stays disabled
  - jlbadano is not canonical
  - publish still requires live verification states
  - remote wrapper / REMOTE.md / health script exist
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / ".cursor" / "vf-desk.json"
CAPS = ROOT / "packages" / "vfigos" / "CAPABILITIES.json"
REMOTE_MD = ROOT / "packages" / "vfigos" / "REMOTE.md"
REMOTE_HEALTH = ROOT / "packages" / "vfigos" / "live" / "remote-health.json"
SERVE = ROOT / "packages" / "vfigos" / "remote" / "serve.py"
FLY = ROOT / "packages" / "vfigos" / "remote" / "fly.toml"
DOCKER = ROOT / "packages" / "vfigos" / "remote" / "Dockerfile"
HEALTH_SCRIPT = ROOT / "scripts" / "vf_instagram_mcp_remote_health.py"
CLOUD_EX = ROOT / "packages" / "vfmcp" / "mcp.cloud.example.json"
CORE_MCP = ROOT / "packages" / "vfmcp" / "core-mcp.json"
PUB_STATES = ROOT / "packages" / "vfigos" / "PUBLICATION-STATES.json"
CONNECT = ROOT / "packages" / "vfigos" / "CONNECT-IG.md"

SECRET_LITERAL = re.compile(r"(EAA[A-Za-z0-9]{10,}|IGQV[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{20,})")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (DESK, CAPS, REMOTE_MD, REMOTE_HEALTH, SERVE, FLY, DOCKER, HEALTH_SCRIPT, CLOUD_EX, CORE_MCP, PUB_STATES, CONNECT):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    desk = json.loads(DESK.read_text(encoding="utf-8"))
    ig = (desk.get("tools") or {}).get("instagram") or {}
    caps = json.loads(CAPS.read_text(encoding="utf-8"))
    health = json.loads(REMOTE_HEALTH.read_text(encoding="utf-8"))
    core = json.loads(CORE_MCP.read_text(encoding="utf-8"))
    states = json.loads(PUB_STATES.read_text(encoding="utf-8"))

    remote = ig.get("remote_access")
    status = ig.get("status")
    if remote not in ("pending", "ready", "degraded"):
        fail("desk instagram.remote_access must be pending|ready|degraded")

    # remote_access ready requires health ok + endpoint
    if remote == "ready":
        if health.get("ok") is not True:
            fail("remote_access=ready requires remote-health.json ok=true")
        if health.get("remote_access") != "ready":
            fail("remote_access=ready requires remote-health.json remote_access=ready")
        endpoint = health.get("endpoint") or ""
        if not str(endpoint).startswith("https://"):
            fail("remote_access=ready requires https endpoint in remote-health.json")
        if status not in ("ready",):
            fail("when remote_access=ready, desk status must be ready (not codespace-only)")

    # Codespace / pending honesty
    if status == "ready-codespace" and remote == "ready":
        fail("ready-codespace must not claim remote_access=ready")
    if remote == "pending" and health.get("ok") is True and health.get("remote_access") == "ready":
        # Allow desk lag only if operator forgot — prefer fail so flip is explicit
        fail("remote-health.json is ready but desk remote_access still pending — flip desk after verified deploy")

    # Current truthful default: pending + not ok
    if remote == "pending":
        if health.get("ok") is True:
            fail("remote_access pending but remote-health ok=true — inconsistent")
        if health.get("remote_access") not in ("pending", "degraded"):
            fail("pending desk must have remote-health remote_access pending|degraded")

    # CAPABILITIES align
    if caps.get("remote_access") != remote and not (
        remote == "degraded" and caps.get("remote_access") in ("pending", "degraded")
    ):
        # Allow caps to stay pending while desk degraded mid-incident only if both not ready
        if remote == "ready" or caps.get("remote_access") == "ready":
            fail("CAPABILITIES.remote_access must match desk when either is ready")

    if caps.get("providerPreference", "").startswith("jlbadano"):
        fail("jlbadano must not be providerPreference")
    if "adelaidasofia" not in (caps.get("canonicalMcp") or "") and "adelaidasofia" not in (
        caps.get("providerPreference") or ""
    ):
        fail("canonical must remain adelaidasofia")

    if ig.get("dmEnabled") is True:
        fail("instagram.dmEnabled must stay false")
    forbidden = " ".join(ig.get("forbidden") or []).lower()
    if "send_message" not in forbidden and "auto-dm" not in forbidden and "send_dm" not in forbidden:
        fail("desk must forbid DM tools")

    # Publication live verification retained
    by_id = {s.get("id"): s for s in (states.get("states") or [])}
    if "publish_pending_verification" not in by_id:
        fail("PUBLICATION-STATES must keep publish_pending_verification")
    if by_id["publish_pending_verification"].get("live") is True:
        fail("publish_pending_verification must not be live=true")
    if "liveVerified" not in by_id:
        fail("PUBLICATION-STATES must keep liveVerified")

    # Wrapper / docs content
    serve = SERVE.read_text(encoding="utf-8")
    for needle in (
        "VELVET_INSTAGRAM_MCP_BEARER_TOKEN",
        "streamable-http",
        "StaticTokenVerifier",
        "INSTAGRAM_MCP_DM_ENABLED",
        "adelaidasofia",
    ):
        if needle not in serve:
            fail(f"serve.py must mention {needle}")

    remote_md = REMOTE_MD.read_text(encoding="utf-8")
    for needle in (
        "Fly.io",
        "streamable-http",
        "VELVET_INSTAGRAM_MCP_BEARER_TOKEN",
        "vf_instagram_mcp_remote_health.py",
        "remote_access",
        "Codespace",
    ):
        if needle not in remote_md:
            fail(f"REMOTE.md must mention {needle}")

    health_src = HEALTH_SCRIPT.read_text(encoding="utf-8")
    for needle in ("accounts_configured", "live_check", "velvets_cloud", "17841407772120429", "REDACTED"):
        if needle not in health_src:
            fail(f"remote health script must mention {needle}")

    cloud_ex = CLOUD_EX.read_text(encoding="utf-8")
    if "INSTAGRAM_MCP_REMOTE_URL" not in cloud_ex or "VELVET_INSTAGRAM_MCP_BEARER_TOKEN" not in cloud_ex:
        fail("mcp.cloud.example.json must use remote URL + bearer env placeholders")
    if SECRET_LITERAL.search(cloud_ex):
        fail("mcp.cloud.example.json must not contain secret literals")

    # No secret literals in tracked IG remote paths
    for path in (
        REMOTE_MD,
        SERVE,
        FLY,
        REMOTE_HEALTH,
        CONNECT,
        DESK,
        CORE_MCP,
        CLOUD_EX,
        ROOT / "packages" / "vfmcp" / "mcp.desktop.example.json",
    ):
        blob = path.read_text(encoding="utf-8")
        if SECRET_LITERAL.search(blob):
            fail(f"{path.name} must not contain secret literals")
        if "BEGIN PRIVATE" in blob:
            fail(f"{path.name} must not contain private key material")

    core_ig = next((s for s in (core.get("servers") or []) if s.get("id") == "instagram"), None)
    if not core_ig:
        fail("core-mcp.json missing instagram")
    if core_ig.get("remote_access") == "ready" and not remote_ok_from(health):
        fail("core-mcp remote_access ready without health ok")
    if "REMOTE.md" not in (core_ig.get("deploy") or ""):
        fail("core-mcp.json instagram.deploy should point at REMOTE.md for autonomy path")

    # Local stdio is not remote autonomy — document in desk
    if status == "ready-codespace" and ig.get("transport") == "streamable-http" and remote != "ready":
        fail("do not claim streamable-http transport on desk before remote ready")

    print("OK instagram-remote")


def remote_ok_from(health: dict) -> bool:
    return health.get("ok") is True and health.get("remote_access") == "ready"


if __name__ == "__main__":
    main()
