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


def main() -> None:
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK weekly bento deck written: {OUT}")


if __name__ == "__main__":
    main()
