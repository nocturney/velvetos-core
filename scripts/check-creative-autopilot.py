#!/usr/bin/env python3
"""Validate Velvet Factory Creative Autopilot contracts. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTOPILOT = ROOT / "packages" / "vfom" / "CREATIVE-AUTOPILOT.md"
VISUAL = ROOT / "packages" / "vfom" / "VISUAL-OS.md"
EDIT = ROOT / "packages" / "vfom" / "EDIT-DIRECTOR.md"
MEDIA_DIRECTOR = ROOT / "packages" / "vfom" / "experts" / "MEDIA-DIRECTOR.md"
MODULE = ROOT / "packages" / "velvetos" / "modules" / "expert-media-director.md"
CREW = ROOT / "packages" / "vfe2b" / "crews" / "content.md"
SCENARIO = ROOT / "packages" / "vfe2b" / "scenarios" / "content-live.md"
GATE = ROOT / "packages" / "vfgrowth" / "GATE.md"
POLICY = ROOT / "constitution" / "ORGANIC_GROWTH.md"
INSTANCE = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
SKILL = ROOT / ".cursor" / "skills" / "vf-creative-autopilot" / "SKILL.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def must_contain(path: Path, needles: tuple[str, ...]) -> str:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            fail(f"{path.relative_to(ROOT)} missing {needle!r}")
    return text


def main() -> None:
    must_contain(AUTOPILOT, (
        "no second orchestrator",
        "AUTO_WITH_GUARDRAILS",
        "HUMAN_REQUIRED",
        "standingAuthorization",
        "waiting_for_media",
        "published_verified",
    ))
    must_contain(VISUAL, ("brandScore", ">=80", "First-frame law", "Originality guard"))
    must_contain(EDIT, ("Edit Decision List", "shotRequest", "hard cut"))
    must_contain(MEDIA_DIRECTOR, ("Creative Director", "Edit Director", "Publishing Director", "standingAuthorization"))
    must_contain(MODULE, ("CREATIVE-AUTOPILOT.md", "VISUAL-OS.md", "EDIT-DIRECTOR.md"))
    must_contain(CREW, ("waiting_for_media", "published_verified", "Routine creative", "vfigos"))
    must_contain(SCENARIO, ("standing authorization", "auto-fix", "receipt + live evidence"))
    must_contain(GATE, ("authorized_for_tool_publish", "pending_human_approval", "published_verified"))
    must_contain(POLICY, ("Creative Autopilot", "standingAuthorization", "אין ריל כל יום", "posted_manually"))
    must_contain(SKILL, ("exception-only", "shotRequest", "published_verified"))

    if not INSTANCE.is_file():
        fail("missing Velvet Factory instance profile")
    instance = json.loads(INSTANCE.read_text(encoding="utf-8"))
    autonomy = instance.get("creativeAutonomy") or {}
    publish = autonomy.get("publish") or {}
    if autonomy.get("enabled") is not True:
        fail("creativeAutonomy.enabled must be true for Velvet Factory")
    if autonomy.get("mode") != "exception-only":
        fail("creativeAutonomy.mode must be exception-only")
    if autonomy.get("ownerSurface") != "human_required_only":
        fail("creativeAutonomy.ownerSurface must be human_required_only")
    if autonomy.get("autoRepairQuality") is not True:
        fail("creativeAutonomy.autoRepairQuality must be true")
    if publish.get("standingAuthorization") is not True:
        fail("routine organic Instagram standingAuthorization must be true")
    for key in ("requirePreflight", "requireKnownRights", "requireToolReceipt", "requireLiveVerification"):
        if publish.get(key) is not True:
            fail(f"creativeAutonomy.publish.{key} must be true")
    if "organic-instagram-routine" not in (publish.get("scope") or []):
        fail("standing authorization scope must be organic-instagram-routine")

    human_required = set(autonomy.get("humanRequired") or [])
    required_human = {
        "physical-footage-or-staging",
        "rights-or-privacy-unclear",
        "sale-ils-or-price-change",
        "purchase-or-spend",
        "boost-or-ads",
        "customer-whatsapp-send",
        "print-from-hq",
        "irreversible-destructive-action",
        "hard-blocker-after-failover",
    }
    missing = required_human - human_required
    if missing:
        fail(f"creativeAutonomy humanRequired missing {sorted(missing)}")

    mcp = instance.get("mcpBind") or {}
    ig = mcp.get("instagram") or {}
    wa = mcp.get("whatsapp") or {}
    if ig.get("publish") is not True or ig.get("dm") is not False:
        fail("Instagram must allow publish and keep DM disabled")
    if wa.get("send") is not False:
        fail("customer WhatsApp send must remain disabled")

    compliance = instance.get("compliance") or {}
    for key in ("noInventedPrices", "noInventedInsights", "noAutoDm", "noBoostWithoutLead"):
        if compliance.get(key) is not True:
            fail(f"compliance lock {key} must remain true")

    print("OK creative autopilot exception-only standing authorization")


if __name__ == "__main__":
    main()
