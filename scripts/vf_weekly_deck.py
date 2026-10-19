#!/usr/bin/env python3
"""Build a bento/slides JSON doc for a weekly recap deck.

Reads only real data already present in the repo (LEARNINGS.md, LAST30.md,
DAILY-RETRO.md, WEEKLY-LOAD.md). Never fabricates numbers. Writes
packages/vfbriefux/hq/weekly-deck.bento-doc.json — paste into a downloaded
Bento_Slides.bento.html to view (see hq/BENTO.md). Not part of the daily
email pipeline.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "vfbriefux" / "hq" / "weekly-deck.bento-doc.json"

LEARNINGS = ROOT / "packages" / "vfinsights" / "data" / "LEARNINGS.md"
LAST30 = ROOT / "packages" / "vfops" / "hq" / "LAST30.md"
RETRO = ROOT / "packages" / "vfops" / "hq" / "DAILY-RETRO.md"
LOAD = ROOT / "packages" / "vfops" / "hq" / "WEEKLY-LOAD.md"


def first_lines(path: Path, n: int = 6) -> list[str]:
    if not path.is_file():
        return []
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return lines[:n]


def esc(html: str) -> str:
    return html.replace("<", "\\u003c")


def text_block(lines: list[str], fallback: str) -> str:
    if not lines:
        return fallback
    return "<br>".join(l.lstrip("#- ").strip() for l in lines)


def build() -> dict:
    today = date.today().isoformat()
    learnings = text_block(first_lines(LEARNINGS), "אין ספירה")
    last30 = text_block(first_lines(LAST30), "אין ספירה")
    retro = text_block(first_lines(RETRO), "אין רישום יומי עדיין")
    load = text_block(first_lines(LOAD), "אין רישום שבועי עדיין")

    doc = {
        "format": "bento/slides",
        "version": 1,
        "title": f"Velvet Factory — דק שבועי {today}",
        "size": {"width": 1280, "height": 720},
        "theme": {
            "background": "#11110f",
            "color": "#f4efe6",
            "accent": "#c9a227",
            "fontFamily": "'Helvetica Neue', Arial, sans-serif",
        },
        "meta": {"author": "Velvet Factory", "company": "Velvet Factory", "subject": "דק שבועי"},
        "slides": [
            {
                "id": "cover", "background": "#11110f", "transition": "none",
                "notes": "כיסוי — לא לפרסום, לצפייה פנימית בדפדפן בלבד.",
                "elements": [
                    {"id": "title", "type": "text", "x": 96, "y": 280, "w": 1088, "h": 160,
                     "rotation": 0, "opacity": 1, "role": "title",
                     "html": f"Velvet Factory<br>דק שבועי · {today}",
                     "fontSize": 64, "fontWeight": 800, "color": "#f4efe6",
                     "align": "right", "valign": "top", "lineHeight": 1.15,
                     "fx": {"enter": "fade-up"}},
                    {"id": "bar", "type": "shape", "shape": "rect", "x": 96, "y": 460,
                     "w": 220, "h": 10, "fill": "#c9a227", "stroke": "none",
                     "strokeWidth": 0, "radius": 0, "rotation": 0, "opacity": 1},
                ],
            },
            {
                "id": "learnings", "background": "#1b1a17", "transition": "none",
                "notes": "מקור: packages/vfinsights/data/LEARNINGS.md — אין המצאה.",
                "elements": [
                    {"id": "h2", "type": "text", "x": 96, "y": 72, "w": 1088, "h": 84,
                     "rotation": 0, "opacity": 1, "role": "kicker",
                     "html": "מה למדנו", "fontSize": 32, "fontWeight": 800,
                     "color": "#c9a227", "align": "right", "valign": "top", "lineHeight": 1.1},
                    {"id": "body2", "type": "text", "x": 96, "y": 208, "w": 1088, "h": 416,
                     "rotation": 0, "opacity": 1, "role": "body",
                     "html": esc(learnings), "fontSize": 28, "fontWeight": 400,
                     "color": "#f4efe6", "align": "right", "valign": "top", "lineHeight": 1.4,
                     "fx": {"enter": "fade-up"}},
                ],
            },
            {
                "id": "numbers", "background": "#1b1a17", "transition": "none",
                "notes": "מקור: vfops/hq/LAST30.md — טקסט בלבד, לא צ'ארט, כי אין נתון מדיד מאומת עדיין.",
                "elements": [
                    {"id": "h3", "type": "text", "x": 96, "y": 72, "w": 1088, "h": 84,
                     "rotation": 0, "opacity": 1, "role": "kicker",
                     "html": "מספרים (30 יום)", "fontSize": 32, "fontWeight": 800,
                     "color": "#c9a227", "align": "right", "valign": "top", "lineHeight": 1.1},
                    {"id": "body3", "type": "text", "x": 96, "y": 208, "w": 1088, "h": 416,
                     "rotation": 0, "opacity": 1, "role": "body",
                     "html": esc(last30), "fontSize": 28, "fontWeight": 400,
                     "color": "#f4efe6", "align": "right", "valign": "top", "lineHeight": 1.4,
                     "fx": {"enter": "fade-up"}},
                ],
            },
            {
                "id": "retro", "background": "#1b1a17", "transition": "none",
                "notes": "מקור: DAILY-RETRO.md + WEEKLY-LOAD.md.",
                "elements": [
                    {"id": "h4", "type": "text", "x": 96, "y": 72, "w": 528, "h": 84,
                     "rotation": 0, "opacity": 1, "role": "kicker",
                     "html": "רטרו יומי", "fontSize": 28, "fontWeight": 800,
                     "color": "#c9a227", "align": "right", "valign": "top", "lineHeight": 1.1},
                    {"id": "h5", "type": "text", "x": 656, "y": 72, "w": 528, "h": 84,
                     "rotation": 0, "opacity": 1, "role": "kicker",
                     "html": "עומס שבועי", "fontSize": 28, "fontWeight": 800,
                     "color": "#c9a227", "align": "right", "valign": "top", "lineHeight": 1.1},
                    {"id": "body4", "type": "text", "x": 96, "y": 208, "w": 528, "h": 416,
                     "rotation": 0, "opacity": 1, "role": "body",
                     "html": esc(retro), "fontSize": 24, "fontWeight": 400,
                     "color": "#f4efe6", "align": "right", "valign": "top", "lineHeight": 1.4},
                    {"id": "body5", "type": "text", "x": 656, "y": 208, "w": 528, "h": 416,
                     "rotation": 0, "opacity": 1, "role": "body",
                     "html": esc(load), "fontSize": 24, "fontWeight": 400,
                     "color": "#f4efe6", "align": "right", "valign": "top", "lineHeight": 1.4},
                ],
            },
        ],
    }
    return doc


DOCS_DIR = ROOT / "docs" / "weekly-deck"
NETWORK_FAIL = "FAIL BENTO_SHELL_NETWORK"
OPENSSL_FAIL = "FAIL BENTO_SHELL_OPENSSL"


def main() -> None:
    doc = build()
    today = date.today().isoformat()
    dated_html = DOCS_DIR / f"{today}.html"
    latest_html = DOCS_DIR / "index.html"
    rc = ship(doc, OUT, dated_html)
    if rc:
        raise SystemExit(rc)
    if dated_html.is_file():
        latest_html.write_text(dated_html.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"OK latest pointer written: {latest_html}")


def ship(doc: dict, out_json: Path, out_html: Path) -> int:
    """Write the JSON deck, then try the shell HTML. JSON is already on disk."""
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK weekly bento deck written: {out_json}")
    return build_html(doc, out_html)


def inject_shell(doc: dict, shell: str, out_html: Path) -> int:
    """Inject the deck into a shell that already passed the pin."""
    import re

    payload = json.dumps(doc, ensure_ascii=False)
    payload_safe = payload.replace("</script", "<\\/script")
    pattern = re.compile(
        r'(<script type="application/bento\+json" id="bento-doc">)(.*?)(</script>)',
        re.DOTALL,
    )
    new_shell, count = pattern.subn(
        lambda m: m.group(1) + payload_safe + m.group(3), shell, count=1
    )
    if count != 1:
        print("WARN could not locate #bento-doc block in shell; skipping HTML build")
        return 0
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(new_shell, encoding="utf-8")
    print(f"OK weekly bento HTML written: {out_html}")
    return 0


def build_html(doc: dict, out_html: Path) -> int:
    """Fetch the pinned shell. A network error or a mismatch fails the job."""
    import urllib.error

    from verify_bento_shell import ShellPinError, load_shell

    try:
        shell = load_shell().decode("utf-8")
    except ShellPinError as exc:
        print(f"FAIL bento shell: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"{OPENSSL_FAIL} HTML build skipped: {exc}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"{NETWORK_FAIL} HTML build skipped: {exc}", file=sys.stderr)
        return 1
    return inject_shell(doc, shell, out_html)


def self_test() -> int:
    import contextlib
    import io
    import tempfile
    import urllib.error

    import verify_bento_shell as shellmod
    from verify_bento_shell import FIXTURE, ShellPinError, pin_problems

    doc = {"format": "bento/slides", "version": 1, "title": "self-test", "slides": []}
    real = shellmod.load_shell
    try:
        def offline() -> bytes:
            raise urllib.error.URLError("offline")

        shellmod.load_shell = offline
        with tempfile.TemporaryDirectory() as tmp:
            out_json = Path(tmp) / "deck.json"
            out_html = Path(tmp) / "deck.html"
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = ship(doc, out_json, out_html)
            if rc == 0 or out_html.exists():
                print("FAIL weekly deck: offline network did not fail the job", file=sys.stderr)
                return 1
            if NETWORK_FAIL not in err.getvalue():
                print("FAIL weekly deck: offline network failure was not named", file=sys.stderr)
                return 1

        def tampered() -> bytes:
            problems = pin_problems(FIXTURE.read_bytes(), b"tampered-shell")
            if problems:
                raise ShellPinError("; ".join(problems))
            return b"tampered-shell"

        shellmod.load_shell = tampered
        with tempfile.TemporaryDirectory() as tmp:
            out_json = Path(tmp) / "deck.json"
            out_html = Path(tmp) / "deck.html"
            rc = ship(doc, out_json, out_html)
            if rc == 0 or out_html.exists():
                print("FAIL weekly deck: tampered bytes did not fail the job", file=sys.stderr)
                return 1
            if not out_json.is_file():
                print("FAIL weekly deck: tampered run dropped the JSON deck", file=sys.stderr)
                return 1

        def missing_openssl() -> bytes:
            raise FileNotFoundError("openssl")

        shellmod.load_shell = missing_openssl
        with tempfile.TemporaryDirectory() as tmp:
            out_json = Path(tmp) / "deck.json"
            out_html = Path(tmp) / "deck.html"
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = ship(doc, out_json, out_html)
            text = err.getvalue()
            if rc == 0 or out_html.exists():
                print("FAIL weekly deck: missing openssl did not fail the job", file=sys.stderr)
                return 1
            if OPENSSL_FAIL not in text or NETWORK_FAIL in text:
                print(f"FAIL weekly deck: missing openssl was mislabeled: {text}", file=sys.stderr)
                return 1
    finally:
        shellmod.load_shell = real
    print("OK weekly deck self-test")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        raise SystemExit(self_test())
    main()
