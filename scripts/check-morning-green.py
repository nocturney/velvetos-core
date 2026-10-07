#!/usr/bin/env python3
"""Offline contract sensor for the Morning Green owner brief."""
from __future__ import annotations
import json
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packages" / "vfbriefux"
ASSETS = PACK / "assets" / "morning-green"

def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)

def main() -> None:
    required = [
        PACK / "MORNING-GREEN.html",
        PACK / "MORNING-GREEN.md",
        PACK / "render_morning_green.py",
        PACK / "build_morning_green.py",
        PACK / "prepare_morning_green.py",
        ASSETS / "morning-top.jpg",
        ASSETS / "morning-story.jpg",
        ASSETS / "morning-radar.jpg",
        ASSETS / "morning-footer.jpg",
        ROOT / "packages" / "vfigos" / "officev2_secure_publisher_snapshot.py",
        ROOT / "automation" / "chatgpt" / "CONTRACT.md",
        ROOT / "automation" / "chatgpt" / "manifest.json",
        ROOT / "automation" / "grok" / "manifest.json",
        ROOT / "packages" / "vfops" / "ROUTINE.md",
    ]
    for path in required:
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    template = (PACK / "MORNING-GREEN.html").read_text(encoding="utf-8")
    for token in (
        "#15352b", "#f8f3e9", "#eee8dc", "MORNING EDITION", "בקרוב בפיד", "7 הימים הקרובים", "Instagram", "מצב החשבון",
        "{{scheduled_posts_html}}", "{{instagram_metrics_html}}", "{{instagram_note}}", "{{attention_html}}", "{{progress_html}}",
        "{{stats_html}}", "max-width:680px", "@media only screen and (max-width:680px)", "vf-hero-copy", "vf-hero-photo",
        "vf-feed-thumb", "vf-insta-value", "vf-stat-value", "vf-item-cell", "vf-hero-img", "vf-story-img", "vf-radar-img", "vf-brand", "vf-edition", "vf-date", "vf-hero-tag", "64%!important", "36%!important", "ימים טובים עושים יותר", "{{radar_title}}", "max-width:420px", "max-width:460px", "{{footer_image_url}}",
    ):
        if token not in template:
            fail(f"MORNING-GREEN.html missing {token!r}")
    for forbidden in ("<button", "<form", "...", "ellipsis"):
        if forbidden in template.lower():
            fail(f"fake-interactive token in Morning Green: {forbidden}")
    for forbidden in ('width="920"', "max-width:920px", "display:block!important;width:100%!important"):
        if forbidden in template:
            fail(f"legacy/mobile-layout regression risk in Morning Green: {forbidden}")
    if "vf-footer-quote" in template or "{{closing_quote}}" in template:
        fail("Morning Green must not duplicate the handwritten footer quote as a large HTML quote")
    for name,min_bytes in (("morning-top.jpg",5000),("morning-story.jpg",10000),("morning-radar.jpg",8000),("morning-footer.jpg",2500)):
        if (ASSETS / name).stat().st_size < min_bytes:
            fail(f"Morning Green editorial asset {name} is unexpectedly small")

    contract = (PACK / "MORNING-GREEN.md").read_text(encoding="utf-8")
    for token in (
        "scheduled != approved != published_verified",
        "מתוזמן", "טרם שובץ", "Cloudflare", "CID", "TARGET-CONCEPT", "QA חזותי", "VF-YYYYMMDD-NNN",
        "list_media/get_media", "owner-visible-text",
    ):
        if token not in contract:
            fail(f"Morning Green contract missing {token!r}")

    schedule_adapter = (ROOT / "packages" / "vfigos" / "officev2_secure_publisher_snapshot.py").read_text(encoding="utf-8")
    for token in ("Resolve-Phase3B-ProductionSnapshot.ps1", "VELVET_OFFICEV2_PUBLISHER_SNAPSHOT_RESOLVER", "-Mode", "Production", "vf.instagram.schedule-snapshot.v1", "cloudflare-instagram-publisher"):
        if token not in schedule_adapter:
            fail(f"Cloudflare publisher snapshot adapter missing {token!r}")
    for forbidden in ("VELVET_INSTAGRAM_PUBLISHER_CONTROL_TOKEN", "cloudflare-publisher-control.dpapi", "resolve_token", "Authorization: Bearer"):
        if forbidden in schedule_adapter:
            fail(f"active Office v2 snapshot adapter contains forbidden incumbent credential path {forbidden!r}")
    for forbidden in ("POST", "PUT", "DELETE"):
        if f'method="{forbidden}"' in schedule_adapter or f"method='{forbidden}'" in schedule_adapter:
            fail(f"Cloudflare publisher snapshot adapter contains write method {forbidden}")

    sender = (ROOT / "packages" / "vfops" / "gmail_brief_send.py").read_text(encoding="utf-8")
    for token in ("multipart/related", "Content-ID", "embed_remote_images"):
        if token not in sender:
            fail(f"Gmail sender missing CID capability {token!r}")

    chatgpt_contract = (ROOT / "automation" / "chatgpt" / "CONTRACT.md").read_text(encoding="utf-8")
    if "Current owner-facing scheduling authority is ChatGPT automations" not in chatgpt_contract:
        fail("ChatGPT scheduler contract missing current authority")
    chatgpt_manifest = json.loads((ROOT / "automation" / "chatgpt" / "manifest.json").read_text(encoding="utf-8"))
    if chatgpt_manifest.get("provider") != "chatgpt-automations" or chatgpt_manifest.get("status") != "ACTIVE":
        fail("ChatGPT scheduler manifest is not active")
    authority = chatgpt_manifest.get("ownerEmailAuthority") or {}
    if not str(authority.get("design") or "").startswith("Morning Green v3.1"):
        fail("ChatGPT ownerEmailAuthority is not Morning Green v3.1")
    if authority.get("deliveryEvidenceRequired") is not True:
        fail("Morning Green delivery must remain evidence-gated")
    morning = chatgpt_manifest.get("morningBrief") or {}
    if morning.get("scheduled") is not False or morning.get("mode") != "manual-or-event-driven":
        fail("Morning Brief must remain manual/event-driven")
    if morning.get("design") != "Morning Green v3.1":
        fail("event-driven Morning Brief is not bound to Morning Green v3.1")
    grok_manifest = json.loads((ROOT / "automation" / "grok" / "manifest.json").read_text(encoding="utf-8"))
    if grok_manifest.get("productionScheduler") != "chatgpt-automations" or (grok_manifest.get("protectedSet") or {}).get("count") != 0:
        fail("Grok retirement mirror disagrees with ChatGPT scheduler authority")
    routine = (ROOT / "packages" / "vfops" / "ROUTINE.md").read_text(encoding="utf-8")
    for token in ("Velvet Morning Brief", "manual/event-driven", "Morning Green", "delivery requires real Gmail/provider evidence"):
        if token not in routine:
            fail(f"vfops ROUTINE missing event-driven Morning Green rule {token!r}")

    builder = (PACK / "build_morning_green.py").read_text(encoding="utf-8")
    preparer = (PACK / "prepare_morning_green.py").read_text(encoding="utf-8")
    for token in ('\"enabled\": bool(args.enable)', "--enable", "embedRemoteImages", "PACK / \"assets\" / \"morning-green\"", "--thumbnail-dir", "morning-green-assets-current", "morning-green-current.html", "rolling-current-transport"):
        if token not in preparer:
            fail(f"Morning Green preparer missing fail-closed send/retention contract {token!r}")
    if 'f"morning-green-assets-{iso}"' in preparer or 'f"morning-green-{iso}.html"' in preparer:
        fail("Morning Green preparer must not accumulate dated rendered transport bundles after Stage 7D")
    if "--openpost" in preparer:
        fail("Morning Green active preparer must not expose an OpenPost input")
    for token in ("reader_friendly", "compact_overview", "compact_attention", "compact_progress", "compact_receivables", "ready_for_brief", "waiting_for_print_done", "lastMod", "thumbnail_cid", "no materialized/public thumbnail", "range(7)", "HE_DAY_SHORT", "extra_count", "instagram_snapshot", "מעורבות בפוסט האחרון", "Insights", "Instagram has its own dedicated analytics section", "דברים שכדאי לשים לב אליהם", "תודה שאתה חלק מהדרך"):
        if token not in builder:
            fail(f"Morning Green builder missing reader-friendly/week-strip/Instagram mapping {token!r}")
    renderer=(PACK / "render_morning_green.py").read_text(encoding="utf-8")
    if "WEEK_DAYS = 7" not in renderer:
        fail("Morning Green renderer must enforce an exact seven-day feed strip")
    if "mixed_text" not in renderer or "vf-id" not in renderer or "display:inline-block" not in renderer or "unicode-bidi:isolate" not in renderer or "&#8209;" not in renderer:
        fail("Morning Green renderer must isolate VF IDs for RTL mobile clients")
    if "mixed_radar_text" not in renderer or "vf-version" not in renderer:
        fail("Morning Green radar must isolate Latin product/version fragments inside RTL copy")
    if "rows.reverse()" not in renderer:
        fail("Morning Green KPI order must match the approved mockup visual order")
    if "[18.0, 27.333, 27.333, 27.334]" not in renderer:
        fail("Morning Green attention widths must protect VF IDs while matching the approved mockup")

    proc = subprocess.run([sys.executable, str(PACK / "render_morning_green.py"), "--check"], cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        fail(proc.stderr or proc.stdout or "Morning Green renderer self-check failed")
    check_feed_status()
    print("OK Morning Green v3.1 editorial email + truth semantics + CID transport contract")

def check_feed_status() -> None:
    """Missing Cloudflare schedule evidence must never read as an empty/failed schedule."""
    cfg_path = PACK / "FEED-SOURCE.json"
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"FEED-SOURCE.json unreadable: {exc}")
    if cfg.get("schema") != "vf.morning-green.feed-source.v2":
        fail("FEED-SOURCE.json schema drifted")
    template = (PACK / "MORNING-GREEN.html").read_text(encoding="utf-8")
    if template.count("{{feed_status_html}}") != 1:
        fail("MORNING-GREEN.html must carry exactly one {{feed_status_html}} slot")
    spec = importlib.util.spec_from_file_location("vf_mg_build", PACK / "build_morning_green.py")
    build = importlib.util.module_from_spec(spec); spec.loader.exec_module(build)  # type: ignore[union-attr]
    rspec = importlib.util.spec_from_file_location("vf_mg_render", PACK / "render_morning_green.py")
    render = importlib.util.module_from_spec(rspec); rspec.loader.exec_module(render)  # type: ignore[union-attr]
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        paused = t / "paused.json"; paused.write_text(json.dumps({"cloudflare_publisher": {"state": "paused", "label": "P", "visibleText": "V"}}), encoding="utf-8")
        active = t / "active.json"; active.write_text(json.dumps({"cloudflare_publisher": {"state": "active"}}), encoding="utf-8")
        broken = t / "broken.json"; broken.write_text("{not json", encoding="utf-8")
        cases = [
            (build.feed_status({"scheduled": []}, paused), "live", ""),
            (build.feed_status(None, paused), "paused", "P"),
            (build.feed_status(None, active), "unavailable", None),
            (build.feed_status(None, broken), "unavailable", None),
            (build.feed_status(None, t / "missing.json"), "unavailable", None),
        ]
        for got, state, label in cases:
            if got.get("state") != state or (label is not None and got.get("label") != label):
                fail(f"feed_status contract drifted: {got!r} expected {state}/{label}")
            if state != "live" and not (got.get("label") and got.get("visible_text")):
                fail(f"feed_status {state} must carry both an email label and a visible-text line")
    if build.feed_status(None).get("state") not in {"paused", "unavailable"}:
        fail("feed_status without a snapshot must be paused or unavailable")
    if render.feed_status_html({"state": "live", "label": "x"}) != "" or render.feed_status_html(None) != "":
        fail("feed_status_html must be empty for live/missing status (backward compatible)")
    html = render.feed_status_html({"state": "paused", "label": "Cloudflare <paused>"})
    if 'data-state="paused"' not in html or "&lt;paused&gt;" not in html or not html.startswith("<tr>"):
        fail("feed_status_html must render an escaped full-row paused note")

if __name__ == "__main__":
    main()