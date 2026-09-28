#!/usr/bin/env python3
"""Validate Organic Growth Control Plane overlay. No network. No send."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
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
LEDGER = ROOT / "packages" / "vfgrowth" / "LEDGER.md"
REEL_GATES_ALLOWED = {"quality_checked", "candidates_ready", "blocked_no_media"}
AUTOPOST_MARKERS = ("publish_reel", "publish_video", "auto-publish", "autopost_enabled", "scheduled_publish")


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
        LEDGER,
    ):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    policy = POLICY.read_text(encoding="utf-8")
    for needle in (
        "approved_for_manual_posting",
        "posted_manually",
        "print.done",
        "050-2517000",  # BUSINESS_CONTACT_RECORD / forbidden-public mention OK
        "אין ריל כל יום",
        "pending_ops",
        "vf_organic_growth.py",
        "אוטומטי",
    ):
        if needle not in policy:
            fail(f"ORGANIC_GROWTH.md missing {needle!r}")
    # PUBLIC_CURRENT_CTA = Instagram message (not WhatsApp phone)
    cta_section = policy.split("## CTA", 1)[-1][:800] if "## CTA" in policy else ""
    if not any(n in cta_section for n in ("PUBLIC_CURRENT_CTA", "הודעה", "אינסטגרם", "Instagram")):
        fail("ORGANIC_GROWTH.md CTA section must prefer Instagram-message / PUBLIC_CURRENT_CTA")
    if "אוטו־DM" not in policy and "auto-dm" not in policy.lower() and "send_dm" not in policy.lower():
        fail("ORGANIC_GROWTH.md must forbid auto-dm / send_dm tooling")
    # Bare English «שלחו DM» as public CTA instruction stays forbidden; Hebrew IG message is OK
    if "שלחו DM" in policy and "לא «שלחו DM»" not in policy and "בלי «שלחו DM»" not in policy:
        if "אסור" not in policy and "auto-dm" not in policy.lower():
            fail("ORGANIC_GROWTH.md must forbid bare שלחו DM / auto-dm tooling")

    play = PLAY.read_text(encoding="utf-8")
    for needle in ("CONTROL", "print.done", "GATE.md", "אין ריל כל יום", "blocked_no_media", "candidates_ready"):
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
        "candidates_ready",
        "blocked_no_media",
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

    cli_text = CLI.read_text(encoding="utf-8")
    for stale in ("G004 עדיין חסום עריכה/preflight", "G003 הנעול לא זז"):
        if stale in cli_text:
            fail(f"vf_organic_growth.py still contains stale pre-reset execution text {stale!r}")
    sys.path.insert(0, str(ROOT / "scripts"))
    import vf_organic_growth as organic
    if organic.g004_currently_qualified() or organic.g004_ready_for_slot():
        fail("current LEDGER marks G004 stale; organic growth must fail closed on automatic reuse")

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
    brief_blob = json.dumps(brief, ensure_ascii=False)
    if "אין ספירה" not in brief_blob:
        fail("growth-brief.json must keep אין ספירה when metrics are missing")
    reel = brief.get("reel") or {}
    if reel.get("gate") == "posted_manually":
        fail("brief must not mark reel posted_manually")
    if reel.get("gate") not in REEL_GATES_ALLOWED:
        fail(f"brief reel gate {reel.get('gate')!r} not in {sorted(REEL_GATES_ALLOWED)}")
    if "no-autopost" not in (brief.get("locks") or []):
        fail("growth brief must keep the no-autopost lock")
    check_reel_candidates(reel.get("candidates") or [], organic)
    if reel.get("gate") == "candidates_ready" and not reel.get("candidates"):
        fail("candidates_ready without candidates")
    if brief.get("slotRecommendation", {}).get("choice") == "G004":
        fail("current stale G004 must not be recommended by growth brief")
    if brief.get("story", {}).get("recommendation", {}).get("choice") == "G004":
        fail("current stale G004 must not be recommended in story decision")
    for stale in ("G004 עדיין חסום עריכה/preflight", "G003 הנעול לא זז"):
        if stale in brief_blob:
            fail(f"growth brief still emits stale pre-reset execution text {stale!r}")

    proc_s = subprocess.run(
        [sys.executable, str(CLI), "score"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc_s.returncode != 0 or "אין ספירה" not in (proc_s.stdout or ""):
        fail("score must print אין ספירה when unverified")

    reel_gate_regression(organic)

    print("OK organic growth control plane")


def check_reel_candidates(candidates: list[dict], organic) -> None:
    """Candidates are suggestions: active tool, human gates, no product claim, no autopost."""
    active = {v["tool"] for v in organic.reel_candidates.active_edit_tools().values()}
    for cand in candidates:
        cid = cand.get("id")
        blob = json.dumps(cand, ensure_ascii=False)
        if cand.get("gate") in {"posted_manually", "published_verified", "approved_for_manual_posting"}:
            fail(f"reel candidate {cid} must not claim {cand.get('gate')}")
        for bad in AUTOPOST_MARKERS:
            if bad in blob:
                fail(f"reel candidate {cid} carries autopost marker {bad!r}")
        recipe = cand.get("recipe") or {}
        tools = [s.get("tool") for s in recipe.get("steps") or []]
        if not tools or not set(tools) <= active:
            fail(f"reel candidate {cid} recipe must name existing active edit tools (got {tools}, active {sorted(active)})")
        gates = " ".join(recipe.get("gates") or [])
        if "PREFLIGHT" not in gates or "EDIT-GATE" not in gates or "אישור אדם" not in gates:
            fail(f"reel candidate {cid} must require human approval + PREFLIGHT + EDIT-GATE")
        if not cand.get("productLink") and not str(cand.get("productClaim") or "").startswith("אין"):
            fail(f"reel candidate {cid} claims a product without catalog productLink")
        if "לפרטים והזמנות — שלחו לנו הודעה כאן באינסטגרם" not in blob:
            fail(f"reel candidate {cid} recipe missing Instagram-message CTA")


def _fixture_item(n: int, name: str, status: str = "source", uploaded: str = "2026-09-01") -> dict:
    return {
        "id": f"media-fixture-{n}",
        "sourceFile": {"id": f"fixture-{n}", "url": f"https://example.invalid/fixture-{n}"},
        "viewDescription": f"fixture · שם קובץ: {name} · טרם נפתח לצפייה מלאה במשרד · אין קישור מוצר",
        "uploadedAt": uploaded,
        "productLink": None,
        "status": status,
        "derivativeIds": [],
        "intake": {"phase": "verified", "lastError": None, "contentFingerprint": f"sha256:fixture{n}"},
        "visualReview": {"state": "none"},
    }


def reel_gate_regression(organic) -> None:
    """Fixture catalogs: 0 videos → blocked_no_media; 2 videos → candidates_ready + active-tool recipe."""
    with tempfile.TemporaryDirectory() as tmp:
        no_video = Path(tmp) / "catalog-0-videos.json"
        no_video.write_text(json.dumps({"items": [
            _fixture_item(1, "IMG_0001.HEIC"),
            _fixture_item(2, "IMG_0002.JPG"),
            _fixture_item(3, "published_PLA_1h2m_20260101.mp4", status="published"),
        ]}, ensure_ascii=False), encoding="utf-8")
        two_videos = Path(tmp) / "catalog-2-videos.json"
        two_videos.write_text(json.dumps({"items": [
            _fixture_item(1, "IMG_0001.HEIC"),
            _fixture_item(2, "IMG_0100.MOV", uploaded="2026-09-10"),
            _fixture_item(3, "clip_PLA_2h5m_20260905.mp4", uploaded="2026-09-05"),
        ]}, ensure_ascii=False), encoding="utf-8")

        zero = organic.reel_section([], catalog=no_video)
        if zero["gate"] != "blocked_no_media" or zero["candidates"]:
            fail(f"fixture 0 videos must be blocked_no_media (got {zero['gate']}, {len(zero['candidates'])} candidates)")
        if zero["line"] != organic.NO_MEDIA_LINE:
            fail("fixture 0 videos must keep the no-media brief line")

        two = organic.reel_section([], catalog=two_videos)
        if two["gate"] != "candidates_ready" or len(two["candidates"]) != 2:
            fail(f"fixture 2 videos must be candidates_ready with 2 candidates (got {two['gate']}, {len(two['candidates'])})")
        if two["candidates"][0]["fileName"] != "IMG_0100.MOV":
            fail("fixture candidates must be newest first")
        check_reel_candidates(two["candidates"], organic)

        media = organic.reel_section([{"mediaPath": "timelapse/fixture.mp4"}], catalog=two_videos)
        if media["gate"] != "quality_checked":
            fail("print.done/card media must still win as quality_checked")


# Sensors only read: undo writes made by the office CLIs this sensor smoke-tests
# (see scripts/sensor_isolation.py).
SIDE_EFFECT_PATHS = (
    "packages/vfgrowth/data",
)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from sensor_isolation import preserve_repo_files  # noqa: E402

    with preserve_repo_files(ROOT, SIDE_EFFECT_PATHS):
        main()
