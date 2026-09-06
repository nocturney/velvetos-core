#!/usr/bin/env python3
"""Fill the תצוגה 3 vfops HTML brief. No invented ₪. No send.

Also renders companion SVG diagrams (diagram-maker embed) via --diagram.
Live mail stays table HTML; diagrams are standalone HTML satellites.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK = Path(__file__).resolve().parent
TEMPLATE = PACK / "MAIL.html"
DIAGRAM_SHELL = PACK / "hq" / "diagram-svg-template.html"
LTR = re.compile(r"^(VF-[\w.-]+|[A-Z]{2,}[-/]?\d[\w.-]*|G00\d)$")

# Canonical studio pipeline — Hebrew labels only; no ₪.
PIPELINE_NODES = (
    ("lead", "פנייה", "input"),
    ("talk", "שיחה", "process"),
    ("offer", "הצעה", "process"),
    ("print", "הדפסה", "storage"),
    ("pickup", "איסוף", "external"),
)

# Brief slots 01–07 — labels match BRIEF-SLOTS / תצוגה 3 kickers.
SLOT_NODES = (
    ("s01", "01 החלטה", "risk"),
    ("s02", "02 כסף", "storage"),
    ("s03", "03 הדפסה", "process"),
    ("s04", "04 פרנסה", "external"),
    ("s05", "05 משרד", "neutral"),
    ("s06", "06 עמוד", "input"),
    ("s07", "07 פיד", "process"),
)

CHECK_BRIEF = {
    "date_line": "יום בדיקה · תצוגה 3 — לא 07:00",
    "bottom_line": "אין ספירה עד מקור. לא ממציאים.",
    "footer": "Velvet Factory · איסוף משדרות · תצוגה 3",
    "slots": [
        {
            "kicker": "01 · קודם החלטה",
            "title": "החלטות",
            "prose": "טבלה לסריקה.",
            "headers": ["החלטה", "כן/לא/דחה", "מועד"],
            "rows": [["מחיר מכירה", "דחה", "אין סכום"]],
        },
        {
            "kicker": "02 · כסף בעבודה",
            "title": "הזמנות ומעקב",
            "prose": "אין ספירה בלי מקור.",
            "headers": ["קוד", "שלב", "חסם"],
            "rows": [["אין", "אין ספירה", "אין ספירה"]],
        },
        {
            "kicker": "03 · מה להדפיס ולפרסם",
            "title": "הצעות הדפסה ופרסום",
            "prose": "שעות תור: אין ספירה.",
            "headers": ["פריט", "למה עכשיו", "קישור"],
            "rows": [["G005", "קרוסלה משובצת", "אין קישור — לא ממציאים"]],
        },
        {
            "kicker": "04",
            "title": "איך הסטודיו מרוויח",
            "prose": "וואטסאפ 050-2517000 · איסוף שדרות.",
        },
        {
            "kicker": "05 · משרד",
            "title": "מה נבנה / יועל",
            "prose": "אין חדש במשרד",
        },
        {
            "kicker": "06",
            "title": "מה קורה בעמוד",
            "prose": "Insights: אין ספירה.",
        },
        {
            "kicker": "07 · פיד בסוף",
            "title": "מה עולה בפיד",
            "prose": "כריכות בגוף המייל — לא כקישור.",
            "covers": [{"cid": "G005.jpg", "caption": "G005"}],
        },
    ],
}


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def prose_html(text: str) -> str:
    return "<br>".join(esc(line) for line in text.split("\n"))


def cell_html(text: str) -> str:
    raw = text.strip()
    first = raw.split()[0] if raw else ""
    if LTR.match(first):
        rest = raw[len(first) :].lstrip()
        body = (
            f'<span dir="ltr" style="direction:ltr;display:inline-block">{esc(first)}</span>'
        )
        if rest:
            body += f" {esc(rest)}"
        return body
    return esc(raw)


def table_html(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(
        f'<td dir="rtl" bgcolor="#101a35" align="right" style="color:rgb(202,169,107)">{esc(h)}</td>'
        for h in headers
    )
    body = []
    for i, row in enumerate(rows):
        bg = "#fffdf8" if i % 2 == 0 else "#f7f3eb"
        border = ' style="border-bottom:1px solid rgb(230,220,200)"' if i < len(rows) - 1 else ""
        cells = "".join(
            f'<td dir="rtl" bgcolor="{bg}" align="right"{border}>{cell_html(c)}</td>'
            for c in row
        )
        body.append(f"<tr>{cells}</tr>")
    return (
        '<table width="100%" cellpadding="8" cellspacing="0" border="0" dir="rtl" '
        'style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:13px">'
        f"<tbody><tr>{head}</tr>{''.join(body)}</tbody></table>"
    )


def covers_html(covers: list[dict]) -> str:
    parts = []
    for cover in covers:
        cid = cover.get("cid") or ""
        caption = cover.get("caption") or cid
        if not cid:
            continue
        parts.append(
            f'<div dir="rtl" style="margin:10px 0 4px;font-family:Georgia,serif;font-size:12px;color:rgb(202,169,107)">{esc(caption)}</div>'
            f'<img src="cid:{esc(cid)}" alt="{esc(caption)}" width="280" '
            'style="display:block;border:0;margin:0 0 12px">'
        )
    return "".join(parts)


def slot_html(slot: dict) -> str:
    kicker = esc(slot.get("kicker") or "")
    title = esc(slot.get("title") or "")
    prose = slot.get("prose") or ""
    headers = slot.get("headers") or []
    rows = slot.get("rows") or []
    covers = slot.get("covers") or []
    bits = [
        '<tr><td dir="rtl" bgcolor="#f7f3eb" style="padding:18px 28px 6px">',
        f'<div style="color:rgb(202,169,107);font-family:Georgia,serif;font-size:12px">{kicker}</div>',
        f'<h2 style="margin:4px 0px 8px;color:rgb(16,26,53);font-family:Arial,sans-serif;font-size:22px">{title}</h2>',
    ]
    if prose:
        bits.append(
            f'<p dir="rtl" style="font-family:Arial,sans-serif;font-size:14px;line-height:1.65;color:rgb(27,36,56);margin:0px 0px 10px">{prose_html(prose)}</p>'
        )
    if headers and rows:
        bits.append(table_html(headers, rows))
    if covers:
        bits.append(covers_html(covers))
    bits.append("</td></tr>")
    return "".join(bits)


def render(brief: dict, template: str | None = None) -> str:
    shell = template if template is not None else TEMPLATE.read_text()
    slots = "".join(slot_html(s) for s in brief.get("slots") or [])
    out = shell
    out = out.replace("{{DATE_LINE}}", prose_html(brief.get("date_line") or ""))
    out = out.replace("{{BOTTOM_LINE}}", prose_html(brief.get("bottom_line") or ""))
    out = out.replace("{{FOOTER}}", esc(brief.get("footer") or "Velvet Factory · איסוף משדרות"))
    out = out.replace("{{SLOTS}}", slots)
    return out


def _flow_svg(
    nodes: tuple[tuple[str, str, str], ...],
    title: str,
    *,
    box_w: int = 100,
    gap: int = 18,
    y: int = 48,
) -> str:
    """Left-to-right boxes with VF semantic fills. Connectors before nodes."""
    n = len(nodes)
    start_x = 16
    height = 120
    width = start_x * 2 + n * box_w + (n - 1) * gap
    marker = (
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker></defs>'
    )
    edges: list[str] = []
    boxes: list[str] = []
    for i, (nid, label, kind) in enumerate(nodes):
        x = start_x + i * (box_w + gap)
        cy = y + 28
        if i < n - 1:
            x1 = x + box_w
            x2 = x + box_w + gap
            edges.append(
                f'<path class="edge" marker-end="url(#arrow)" '
                f'd="M {x1} {cy} L {x2} {cy}"/>'
            )
        boxes.append(
            f'<rect class="node {kind}" id="{esc(nid)}" x="{x}" y="{y}" '
            f'width="{box_w}" height="56" rx="8"/>'
            f'<text class="label" text-anchor="middle" x="{x + box_w / 2}" '
            f'y="{cy + 5}">{esc(label)}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{esc(title)}">'
        f"{marker}"
        f'<text class="title" x="{width - 12}" y="22" text-anchor="end">{esc(title)}</text>'
        f'{"".join(edges)}{"".join(boxes)}</svg>'
    )


def render_diagram(kind: str, template: str | None = None) -> str:
    """Standalone HTML diagram (diagram-maker clean-svg path). Not for Gmail body."""
    shell = template if template is not None else DIAGRAM_SHELL.read_text()
    if kind == "pipeline":
        title = "צינור הסטודיו"
        svg = _flow_svg(PIPELINE_NODES, title, box_w=108, gap=20)
        heading = "צינור · פנייה עד איסוף"
        sub = "clean-svg · לוויין לבריף · איסוף שדרות בלבד"
        doc_title = "Velvet Factory · צינור הסטודיו"
    elif kind == "slots":
        title = "חריצי בריף 01–07"
        svg = _flow_svg(SLOT_NODES, title, box_w=86, gap=12)
        heading = "מבנה תצוגה 3 · חריצים"
        sub = "clean-svg · לא מחליף MAIL.html"
        doc_title = "Velvet Factory · חריצי בריף"
    else:
        raise SystemExit(f"unknown diagram kind: {kind}")
    out = shell
    out = out.replace(
        "<title>Velvet Factory · דיאגרמת בריף</title>",
        f"<title>{esc(doc_title)}</title>",
        1,
    )
    out = out.replace("<h1>דיאגרמת בריף</h1>", f"<h1>{esc(heading)}</h1>", 1)
    out = out.replace(
        "לוויין ל־vfbriefux · לא תצוגה 3 במייל",
        sub,
        1,
    )
    if "<!-- SVG -->" not in out:
        raise SystemExit("FAIL diagram shell missing <!-- SVG --> marker")
    return out.replace("<!-- SVG -->", svg, 1)


def self_check() -> None:
    html_out = render(CHECK_BRIEF)
    need = (
        'bgcolor="#0b1224"',
        'dir="rtl"',
        "01 · קודם החלטה",
        "07 · פיד בסוף",
        'src="cid:G005.jpg"',
        "אין ספירה",
    )
    missing = [t for t in need if t not in html_out]
    if missing:
        raise SystemExit(f"FAIL render missing {missing}")
    if "{{SLOTS}}" in html_out or "{{DATE_LINE}}" in html_out:
        raise SystemExit("FAIL placeholders left in output")

    if not DIAGRAM_SHELL.is_file():
        raise SystemExit("FAIL missing hq/diagram-svg-template.html")
    for kind, must in (
        ("pipeline", ("פנייה", "שיחה", "הצעה", "הדפסה", "איסוף", 'class="edge"')),
        ("slots", ("01 החלטה", "07 פיד", "חריצי בריף", 'marker-end="url(#arrow)"')),
    ):
        diag = render_diagram(kind)
        miss = [t for t in must if t not in diag]
        if miss:
            raise SystemExit(f"FAIL diagram {kind} missing {miss}")
        if "<!-- SVG -->" in diag:
            raise SystemExit(f"FAIL diagram {kind} left SVG placeholder")
        if "#caa96b" not in diag and "stroke: #caa96b" not in DIAGRAM_SHELL.read_text():
            raise SystemExit("FAIL diagram shell missing gold token")
    print("OK תצוגה 3 html + diagram-maker satellites")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render תצוגה 3 vfops HTML brief")
    parser.add_argument("json_path", nargs="?", help="brief JSON")
    parser.add_argument("-o", "--out", help="write HTML here")
    parser.add_argument("--check", action="store_true", help="self-check fixture")
    parser.add_argument(
        "--diagram",
        choices=("pipeline", "slots"),
        help="render companion SVG diagram (not Gmail body)",
    )
    args = parser.parse_args()
    if args.check:
        self_check()
        return 0
    if args.diagram:
        html_out = render_diagram(args.diagram)
        if args.out:
            Path(args.out).write_text(html_out)
        else:
            sys.stdout.write(html_out)
        return 0
    if not args.json_path:
        print(
            "usage: render_mail.py <brief.json> [-o out.html]\n"
            "       render_mail.py --diagram pipeline|slots [-o out.html]\n"
            "       render_mail.py --check",
            file=sys.stderr,
        )
        return 2
    brief = json.loads(Path(args.json_path).read_text())
    html_out = render(brief)
    if args.out:
        Path(args.out).write_text(html_out)
    else:
        sys.stdout.write(html_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
