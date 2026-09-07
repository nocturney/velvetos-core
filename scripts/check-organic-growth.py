#!/usr/bin/env python3
"""Validate Organic Growth Control Plane overlay. No network. No send."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "constitution" / "ORGANIC_GROWTH.md"
PLAY = ROOT / "packages" / "vfgrowth" / "ORGANIC-GROWTH.md"
GATE = ROOT / "packages" / "vfgrowth" / "GATE.md"
CLI = ROOT / "scripts" / "vf_organic_growth.py"
AGENTS = ROOT / "AGENTS.md"
EVENTS = ROOT / "packages" / "velvetos" / "schema" / "events.catalog.json"
QUEUE = ROOT / "packages" / "vfgrowth" / "data" / "approval-queue.json"
ORDERS = ROOT / "packages" / "vfsales" / "data" / "orders.json"
LOOP = ROOT / "packages" / "vfops" / "LOOP.json"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (
        POLICY,
        PLAY,
        GATE,
        CLI,
        ROOT / "packages" / "vfgrowth" / "HASHTAGS.md",
        ROOT / "packages" / "vfgrowth" / "COMMUNITY.md",
        ROOT / "packages" / "vfprod" / "CLAIMS.md",
        ROOT / "packages" / "vfsales" / "ORDERS.md",
        ROOT / "packages" / "vfinsights" / "ATTRIBUTION.md",
        ROOT / "packages" / "vfbriefux" / "hq" / "GROWTH-BRIEF.md",
        ROOT / ".cursor" / "skills" / "vf-organic-growth" / "SKILL.md",
        QUEUE,
        ORDERS,
    ):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    policy = POLICY.read_text(encoding="utf-8")
    for needle in (
        "approved_for_manual_posting",
        "posted_manually",
        "print.done",
        "050-2517000",
        "אין ריל כל יום",
        "pending_ops",
        "vf_organic_growth.py",
        "אוטומטי",
    ):
        if needle not in policy:
            fail(f"ORGANIC_GROWTH.md missing {needle!r}")
    if "שלחו DM" in policy and "לא «שלחו DM»" not in policy and "לא «שלחו DM»" not in policy:
        # allow mention only as forbidden
        if "אסור" not in policy:
            fail("ORGANIC_GROWTH.md must forbid שלחו DM")

    play = PLAY.read_text(encoding="utf-8")
    for needle in ("CONTROL", "print.done", "GATE.md", "אין ריל כל יום", "blocked_no_media"):
        if needle not in play and needle != "CONTROL":
            fail(f"ORGANIC-GROWTH.md missing {needle!r}")
    if "לא מפרסמת" not in play and "לא מפרסם" not in play:
        fail("ORGANIC-GROWTH.md must say the plane does not publish")

    gate = GATE.read_text(encoding="utf-8")
    for needle in (
        "draft",
        "quality_checked",
        "policy_checked",
        "pending_human_approval",
        "approved_for_manual_posting",
        "posted_manually",
        "human_marked",
    ):
        if needle not in gate:
            fail(f"GATE.md missing {needle!r}")

    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    ids = {e.get("id") for e in events.get("events") or []}
    for need in (
        "content.policy_checked",
        "content.approved_for_manual_posting",
        "content.posted_manually",
        "community.work_order",
        "lead.attributed",
    ):
        if need not in ids:
            fail(f"events.catalog.json missing {need}")
    for hg in ("ig-autopost", "auto-dm", "user-tag-without-optin"):
        if hg not in (events.get("humanGates") or []):
            fail(f"events.catalog.json humanGates missing {hg}")

    posted = [e for e in events.get("events") or [] if e.get("id") == "content.posted_manually"]
    if not posted:
        fail("content.posted_manually event missing")
    if "human" not in (posted[0].get("note") or "").lower() and "אדם" not in (posted[0].get("note") or ""):
        fail("content.posted_manually note must say only a human marks it")

    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    for item in queue.get("items") or []:
        if item.get("gate") == "posted_manually" and not item.get("human_marked"):
            fail("approval-queue has posted_manually without human_marked")

    orders = json.loads(ORDERS.read_text(encoding="utf-8"))
    for row in orders.get("orders") or []:
        if row.get("estimated_value_ils") not in (None, "X ₪"):
            fail("orders.json must not invent estimated_value_ils")

    agents = AGENTS.read_text(encoding="utf-8")
    if "check-organic-growth.py" not in agents:
        fail("AGENTS.md sensor table must list check-organic-growth.py")
    if "ORGANIC_GROWTH.md" not in agents:
        fail("AGENTS.md must point at constitution/ORGANIC_GROWTH.md")

    loop = json.loads(LOOP.read_text(encoding="utf-8"))
    packs = {p["id"]: p for p in loop.get("packs") or []}
    growth = packs.get("vfgrowth") or {}
    gates = growth.get("gates") or []
    if "packages/vfgrowth/ORGANIC-GROWTH.md" not in gates:
        fail("LOOP.json vfgrowth.gates must include ORGANIC-GROWTH.md")
    guide_paths = {g.get("path") for g in loop.get("guides") or []}
    if "constitution/ORGANIC_GROWTH.md" not in guide_paths:
        fail("LOOP.json guides must include constitution/ORGANIC_GROWTH.md")

    proc = subprocess.run(
        [sys.executable, str(CLI), "policy"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        fail(f"vf_organic_growth.py policy: {proc.stderr or proc.stdout}")

    proc_b = subprocess.run(
        [sys.executable, str(CLI), "brief", "--write"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc_b.returncode != 0:
        fail(f"vf_organic_growth.py brief --write: {proc_b.stderr or proc_b.stdout}")
    out = ROOT / "packages" / "vfgrowth" / "data" / "growth-brief.json"
    if not out.is_file():
        fail("brief --write did not create growth-brief.json")
    brief = json.loads(out.read_text(encoding="utf-8"))
    if "אין ספירה" not in json.dumps(brief, ensure_ascii=False):
        fail("growth-brief.json must keep אין ספירה when metrics are missing")
    if brief.get("reel", {}).get("gate") == "posted_manually":
        fail("brief must not mark reel posted_manually")

    proc_s = subprocess.run(
        [sys.executable, str(CLI), "score"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc_s.returncode != 0 or "אין ספירה" not in (proc_s.stdout or ""):
        fail("score must print אין ספירה when unverified")

    print("OK organic growth control plane")


if __name__ == "__main__":
    main()
