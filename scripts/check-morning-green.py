#!/usr/bin/env python3
"""Offline contract sensor for the Morning Green owner brief."""
from __future__ import annotations
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
        ASSETS / "morning-top.jpg",
        ASSETS / "morning-story.jpg",
        ASSETS / "morning-radar.jpg",
        ASSETS / "morning-footer.jpg",
        ROOT / "packages" / "vfigos" / "openpost_morning_snapshot.py",
    ]
    for path in required:
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    template = (PACK / "MORNING-GREEN.html").read_text(encoding="utf-8")
    for token in (
        "#15352b", "#f8f3e9", "MORNING EDITION", "בקרוב באינסטגרם",
        "{{scheduled_posts_html}}", "{{attention_html}}", "{{progress_html}}",
        "{{stats_html}}", "max-width:920px", "@media only screen and (max-width:680px)",
    ):
        if token not in template:
            fail(f"MORNING-GREEN.html missing {token!r}")
    for forbidden in ("<button", "<form", "...", "ellipsis"):
        if forbidden in template.lower():
            fail(f"fake-interactive token in Morning Green: {forbidden}")

    contract = (PACK / "MORNING-GREEN.md").read_text(encoding="utf-8")
    for token in (
        "scheduled != approved != published_verified",
        "מתוזמן", "טרם שובץ", "OpenPost", "CID",
        "list_media/get_media", "owner-visible-text",
    ):
        if token not in contract:
            fail(f"Morning Green contract missing {token!r}")

    openpost = (ROOT / "packages" / "vfigos" / "openpost_morning_snapshot.py").read_text(encoding="utf-8")
    for token in ("activity_bucket':'scheduled'", "scheduled_at", "public_url_ready", "OPENPOST_TOKEN"):
        if token not in openpost:
            fail(f"OpenPost Morning adapter missing {token!r}")
    for forbidden in ("method='POST'", 'method="POST"', "method='PUT'", 'method="PUT"', "method='DELETE'", 'method="DELETE"'):
        if forbidden in openpost:
            fail(f"OpenPost Morning adapter contains write HTTP method: {forbidden}")

    sender = (ROOT / "packages" / "vfops" / "gmail_brief_send.py").read_text(encoding="utf-8")
    for token in ("multipart/related", "Content-ID", "embed_remote_images"):
        if token not in sender:
            fail(f"Gmail sender missing CID capability {token!r}")

    proc = subprocess.run([sys.executable, str(PACK / "render_morning_green.py"), "--check"], cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        fail(proc.stderr or proc.stdout or "Morning Green renderer self-check failed")
    print("OK Morning Green v3.1 editorial email + truth semantics + CID transport contract")

if __name__ == "__main__":
    main()