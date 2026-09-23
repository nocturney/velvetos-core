#!/usr/bin/env python3
"""Offline contract sensor for the Morning Green owner brief."""
from __future__ import annotations
import json
import subprocess
import sys
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
        ROOT / "packages" / "vfigos" / "openpost_morning_snapshot.py",
        ROOT / "packages" / "vfigos" / "run_openpost_morning_snapshot.ps1",
        ROOT / "packages" / "vfigos" / "materialize_openpost_morning_thumbnails.ps1",
        ROOT / "automation" / "grok" / "CONTRACT.md",
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
        "vf-feed-thumb", "vf-insta-value", "vf-stat-value", "vf-item-cell", "vf-hero-img", "vf-story-img", "vf-radar-img", "ימים טובים עושים יותר", "{{radar_title}}", "max-width:420px", "max-width:460px", "{{footer_image_url}}",
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
        "מתוזמן", "טרם שובץ", "OpenPost", "CID", "TARGET-CONCEPT", "QA חזותי", "VF-YYYYMMDD-NNN",
        "list_media/get_media", "owner-visible-text",
    ):
        if token not in contract:
            fail(f"Morning Green contract missing {token!r}")

    openpost = (ROOT / "packages" / "vfigos" / "openpost_morning_snapshot.py").read_text(encoding="utf-8")
    for token in ("activity_bucket':'scheduled'", "scheduled_at", "public_url_ready", "thumbnail_media_id", "thumbnail_cid", "OPENPOST_TOKEN"):
        if token not in openpost:
            fail(f"OpenPost Morning adapter missing {token!r}")
    if "value.startswith('/media/')" in openpost or "origin+value" in openpost:
        fail("OpenPost Morning adapter must not treat authenticated relative /media paths as public")
    for forbidden in ("method='POST'", 'method="POST"', "method='PUT'", 'method="PUT"', "method='DELETE'", 'method="DELETE"'):
        if forbidden in openpost:
            fail(f"OpenPost Morning adapter contains write HTTP method: {forbidden}")
    snapshot_runner=(ROOT / "packages" / "vfigos" / "run_openpost_morning_snapshot.ps1").read_text(encoding="utf-8")
    materializer=(ROOT / "packages" / "vfigos" / "materialize_openpost_morning_thumbnails.ps1").read_text(encoding="utf-8")
    for token in ("openpost-morning-brief.token.dpapi", "OPENPOST_TOKEN", "ZeroFreeBSTR"):
        if token not in snapshot_runner:
            fail(f"OpenPost DPAPI runner missing {token!r}")
    for token in ("sm_$media.jpg", "--tunnel-through-iap", "thumbnail_cid", "sudo rm -f"):
        if token not in materializer:
            fail(f"OpenPost thumbnail materializer missing {token!r}")

    sender = (ROOT / "packages" / "vfops" / "gmail_brief_send.py").read_text(encoding="utf-8")
    for token in ("multipart/related", "Content-ID", "embed_remote_images"):
        if token not in sender:
            fail(f"Gmail sender missing CID capability {token!r}")

    grok_contract = (ROOT / "automation" / "grok" / "CONTRACT.md").read_text(encoding="utf-8")
    for token in ("09:00 owner brief must use Morning Green v3.1", "V10.3 remains available only for legacy/recovery", "Apps Script bridge v5 health"):
        if token not in grok_contract:
            fail(f"Grok owner-email authority missing Morning Green cutover token {token!r}")
    grok_manifest = json.loads((ROOT / "automation" / "grok" / "manifest.json").read_text(encoding="utf-8"))
    if int(grok_manifest.get("version", 0)) < 2 or grok_manifest.get("morningGreenCutoverDate") != "2026-09-23":
        fail("Grok manifest missing Morning Green production cutover version/date")
    authority = grok_manifest.get("ownerEmailAuthority") or {}
    if not str(authority.get("design") or "").startswith("Morning Green v3.1"):
        fail("Grok ownerEmailAuthority is not Morning Green v3.1")
    morning = next((x for x in grok_manifest.get("routines", []) if x.get("id") == "velvet-morning-brief"), None)
    if not morning or "Morning Green v3.1" not in str(morning.get("responsibility") or ""):
        fail("protected 09:00 routine is not bound to Morning Green v3.1")
    routine = (ROOT / "packages" / "vfops" / "ROUTINE.md").read_text(encoding="utf-8")
    for token in ("09:00** | Velvet Morning Brief | Owner-facing Morning Green v3.1", "10:00** | Morning Delivery Guard | Verify TODAY'S 09:00 Morning Green delivery", "must not silently downgrade to V10.3"):
        if token not in routine:
            fail(f"vfops ROUTINE missing Morning Green production rule {token!r}")

    builder = (PACK / "build_morning_green.py").read_text(encoding="utf-8")
    preparer = (PACK / "prepare_morning_green.py").read_text(encoding="utf-8")
    for token in ("'enabled':bool(args.enable)", "--enable", "embedRemoteImages", "PACK/'assets'/'morning-green'", "--thumbnail-dir", "morning-green-assets-"):
        if token not in preparer:
            fail(f"Morning Green preparer missing fail-closed send contract {token!r}")
    for token in ("reader_friendly", "compact_overview", "compact_attention", "compact_progress", "compact_receivables", "ready_for_brief", "waiting_for_print_done", "lastMod", "thumbnail_cid", "no materialized/public thumbnail", "range(7)", "HE_DAY_SHORT", "extra_count", "instagram_snapshot", "מעורבות בפוסט האחרון", "Insights", "Instagram has its own dedicated analytics section", "דברים שכדאי לשים לב אליהם", "תודה שאתה חלק מהדרך"):
        if token not in builder:
            fail(f"Morning Green builder missing reader-friendly/week-strip/Instagram mapping {token!r}")
    renderer=(PACK / "render_morning_green.py").read_text(encoding="utf-8")
    if "WEEK_DAYS = 7" not in renderer:
        fail("Morning Green renderer must enforce an exact seven-day feed strip")
    if "mixed_text" not in renderer or "unicode-bidi:isolate" not in renderer or "<nobr" not in renderer or "&#8209;" not in renderer:
        fail("Morning Green renderer must isolate VF IDs for RTL mobile clients")
    if "rows.reverse()" not in renderer:
        fail("Morning Green KPI order must match the approved mockup visual order")

    proc = subprocess.run([sys.executable, str(PACK / "render_morning_green.py"), "--check"], cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        fail(proc.stderr or proc.stdout or "Morning Green renderer self-check failed")
    print("OK Morning Green v3.1 editorial email + truth semantics + CID transport contract")

if __name__ == "__main__":
    main()