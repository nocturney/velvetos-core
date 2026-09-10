#!/usr/bin/env python3
"""Render Velvet Factory Brief V10. No invented ₪. No send.

Gmail-safe table HTML, RTL-first, Hebrew-first. Backward-compatible with the
legacy 01–07 JSON while supporting V10 status badges, KPI cards, delta-first
changes, semantic card colors, and clickable CID/remote thumbnails.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
TEMPLATE = PACK / "MAIL.html"
DIAGRAM_SHELL = PACK / "hq" / "diagram-svg-template.html"
LTR = re.compile(r"^(VF-[\w.-]+|[A-Z]{2,}[-/]?\d[\w.-]*|G00\d)$")

PIPELINE_NODES = (
    ("lead", "פנייה", "input"),
    ("talk", "שיחה", "process"),
    ("offer", "הצעה", "process"),
    ("print", "הדפסה", "storage"),
    ("pickup", "איסוף", "external"),
)

SLOT_NODES = (
    ("s01", "01 החלטה", "risk"),
    ("s02", "02 כסף", "storage"),
    ("s03", "03 הדפסה", "process"),
    ("s04", "04 פרנסה", "external"),
    ("s05", "05 משרד", "neutral"),
    ("s06", "06 עמוד", "input"),
    ("s07", "07 פיד", "process"),
)

THEMES = {
    "decision": ("#ff5fa2", "#fff0f6", "#a91f50", "#27152c"),
    "money": ("#a3e635", "#f4fce7", "#4d7c0f", "#182315"),
    "production": ("#ff8a65", "#fff3ed", "#b94727", "#2b1914"),
    "revenue": ("#f5c451", "#fff8df", "#8b6100", "#2a2110"),
    "office": ("#7c5cff", "#f2efff", "#5a3fd2", "#1c1736"),
    "insights": ("#20d9ff", "#eafcff", "#087b94", "#10272d"),
    "content": ("#8b7cff", "#f2f0ff", "#5948cf", "#1d1938"),
    "neutral": ("#8a93a5", "#f6f7fa", "#50596b", "#202532"),
}

STATES = {
    "green": ("#e9fbe9", "#256b33", "#55d66b"),
    "yellow": ("#fff5d8", "#8b6100", "#f5c451"),
    "red": ("#ffe8ef", "#a91f50", "#ff5f8f"),
    "blue": ("#e8f9ff", "#087b94", "#20d9ff"),
    "purple": ("#f0edff", "#5a3fd2", "#7c5cff"),
    "neutral": ("#eef0f4", "#50596b", "#8a93a5"),
}

CHECK_BRIEF = {
    "date_line": "יום בדיקה · V10 — לא 07:00",
    "bottom_line": "אין ספירה עד מקור. לא ממציאים.",
    "footer": "Velvet Factory · איסוף משדרות · V10",
    "attention": {"state": "yellow", "label": "מצב העסק", "text": "דורש מעקב"},
    "system_health": {"state": "green", "label": "בריאות מערכת", "text": "תקינה"},
    "kpis": [
        {"value": "3", "label": "עבודות פעילות", "state": "purple"},
        {"value": "1", "label": "צריך ממך", "state": "red"},
    ],
    "changes": [
        {"text": "נכנס מצב דלתא", "state": "blue"},
        {"text": "תמונה חיה נתמכת", "state": "green"},
    ],
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
        {"kicker": "04", "title": "איך הסטודיו מרוויח", "prose": "איסוף שדרות."},
        {"kicker": "05 · משרד", "title": "מה נבנה / יועל", "prose": "אין חדש במשרד"},
        {"kicker": "06", "title": "מה קורה בעמוד", "prose": "Insights: אין ספירה."},
        {
            "kicker": "07 · פיד בסוף",
            "title": "מה עולה בפיד",
            "prose": "כריכות בגוף המייל — לא כקישור.",
            "covers": [{"cid": "G005.jpg", "caption": "G005"}],
        },
    ],
}


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def prose_html(text: str) -> str:
    return "<br>".join(esc(line) for line in text.split("\n"))


def cell_html(text: str) -> str:
    raw = text.strip()
    first = raw.split()[0] if raw else ""
    if LTR.match(first):
        rest = raw[len(first):].lstrip()
        body = f'<span dir="ltr" style="direction:ltr;display:inline-block">{esc(first)}</span>'
        if rest:
            body += f" {esc(rest)}"
        return body
    return esc(raw)


def slot_kind(slot: dict) -> str:
    explicit = str(slot.get("kind") or "").strip().lower()
    if explicit in THEMES:
        return explicit
    hay = f'{slot.get("kicker", "")} {slot.get("title", "")}'
    if "01" in hay or "החלט" in hay or "צריך ממך" in hay:
        return "decision"
    if "02" in hay or "כסף" in hay or "גבייה" in hay:
        return "money"
    if "03" in hay or "הדפס" in hay or "ייצור" in hay:
        return "production"
    if "04" in hay or "פרנסה" in hay or "הכנסה" in hay:
        return "revenue"
    if "05" in hay or "משרד" in hay or "VelvetOS" in hay:
        return "office"
    if "06" in hay or "עמוד" in hay or "Insight" in hay:
        return "insights"
    if "07" in hay or "פיד" in hay or "תוכן" in hay:
        return "content"
    return "neutral"


def table_html(headers: list[str], rows: list[list[str]], theme: tuple[str, str, str, str]) -> str:
    accent, soft, _label, dark = theme
    head = "".join(
        f'<td dir="rtl" bgcolor="{dark}" align="right" style="color:#ffffff;font-weight:800;border-bottom:3px solid {accent}">{esc(h)}</td>'
        for h in headers
    )
    body = []
    for i, row in enumerate(rows):
        bg = "#ffffff" if i % 2 == 0 else soft
        cells = "".join(
            f'<td dir="rtl" bgcolor="{bg}" align="right" style="border-bottom:1px solid #e4e6ee">{cell_html(c)}</td>'
            for c in row
        )
        body.append(f"<tr>{cells}</tr>")
    return (
        '<table width="100%" cellpadding="9" cellspacing="0" border="0" dir="rtl" '
        'style="border-collapse:separate;border-spacing:0;font-family:Arial,sans-serif;font-size:13px;border-radius:12px;overflow:hidden">'
        f"<tbody><tr>{head}</tr>{''.join(body)}</tbody></table>"
    )


def covers_html(covers: list[dict], theme: tuple[str, str, str, str]) -> str:
    _accent, _soft, label, _dark = theme
    parts: list[str] = []
    for cover in covers:
        cid = str(cover.get("cid") or "").strip()
        remote = str(cover.get("url") or cover.get("src") or "").strip()
        href = str(cover.get("href") or "").strip()
        caption = cover.get("caption") or cover.get("alt") or cid or "תמונה"
        alt = cover.get("alt") or caption
        src = f"cid:{cid}" if cid else remote
        if not src:
            continue
        image = (
            f'<img class="vf-img" src="{esc(src)}" alt="{esc(alt)}" width="560" '
            'style="display:block;width:100%;max-width:560px;height:auto;border:0;border-radius:14px;margin:0">'
        )
        if href:
            image = f'<a href="{esc(href)}" style="text-decoration:none">{image}</a>'
        parts.append(
            f'<div dir="rtl" style="margin:12px 0 5px;font-size:11px;color:{label};font-weight:900">{esc(caption)}</div>{image}'
        )
    return "".join(parts)


def actions_html(actions: list[dict], theme: tuple[str, str, str, str]) -> str:
    accent, _soft, label_color, _dark = theme
    parts = [
        f'<div dir="rtl" style="margin:12px 0 6px;font-size:11px;color:{label_color};font-weight:900">אישור בלחיצה · לא הודעת לקוח · לא Print</div>'
    ]
    for item in actions:
        label = esc(item.get("label") or item.get("id") or "שער")
        links = []
        if item.get("yes"):
            links.append(f'<a class="vf-touch" href="{esc(item["yes"])}" style="color:#fff;text-decoration:none;background:{accent};border-radius:9px;padding:8px 12px;margin-left:7px;display:inline-block;font-weight:900">כן</a>')
        if item.get("no"):
            links.append(f'<a class="vf-touch" href="{esc(item["no"])}" style="color:#9d274e;text-decoration:none;background:#ffe8ef;border-radius:9px;padding:8px 12px;margin-left:7px;display:inline-block;font-weight:900">דחה</a>')
        if item.get("defer"):
            links.append(f'<a class="vf-touch" href="{esc(item["defer"])}" style="color:#50596b;text-decoration:none;background:#eef0f4;border-radius:9px;padding:8px 12px;display:inline-block;font-weight:900">דחה למועד</a>')
        parts.append(f'<p dir="rtl" style="font-size:13px;color:#23273a;margin:9px 0">{label} {" ".join(links)}</p>')
    return "".join(parts)


def slot_delta_html(slot: dict) -> str:
    delta = slot.get("delta")
    if not delta:
        return ""
    if isinstance(delta, str):
        text, state = delta, "blue"
    else:
        text = delta.get("text") or delta.get("label") or ""
        state = str(delta.get("state") or "blue").lower()
    if not text:
        return ""
    bg, fg, dot = STATES.get(state, STATES["blue"])
    return f'<div dir="rtl" style="margin:0 0 10px;padding:9px 11px;background:{bg};color:{fg};border-radius:10px;font-size:11px;font-weight:900"><span style="color:{dot}">●</span> {esc(text)}</div>'


def slot_html(slot: dict) -> str:
    theme = THEMES[slot_kind(slot)]
    accent, soft, label, _dark = theme
    density = str(slot.get("density") or "normal").lower()
    pad = "13px 18px" if density == "compact" else "17px 20px"
    bits = [
        '<tr><td dir="rtl" bgcolor="#f6f5fb" class="vf-slot" style="padding:6px 14px">',
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" dir="rtl"><tr><td bgcolor="{soft}" style="padding:{pad};border-radius:16px;border:1px solid #e3e1eb;border-right:4px solid {accent}">',
        f'<div style="color:{label};font-size:10px;font-weight:900;letter-spacing:.3px">{esc(slot.get("kicker") or "")}</div>',
        f'<h2 style="margin:4px 0 8px;color:#161a2d;font-size:21px;line-height:26px">{esc(slot.get("title") or "")}</h2>',
        slot_delta_html(slot),
    ]
    prose = slot.get("prose") or ""
    if prose:
        bits.append(f'<p dir="rtl" style="font-size:14px;line-height:1.65;color:#30364d;margin:0 0 10px">{prose_html(prose)}</p>')
    headers = slot.get("headers") or []
    rows = slot.get("rows") or []
    if headers and rows:
        bits.append(table_html(headers, rows, theme))
    covers = slot.get("covers") or []
    if covers:
        bits.append(covers_html(covers, theme))
    actions = slot.get("actions") or []
    if actions:
        bits.append(actions_html(actions, theme))
    bits.append("</td></tr></table></td></tr>")
    return "".join(bits)


def status_badges_html(brief: dict) -> str:
    cells = []
    for key, default_label in (("attention", "מצב העסק"), ("system_health", "בריאות מערכת")):
        item = brief.get(key) or {}
        if not item:
            continue
        bg, fg, dot = STATES.get(str(item.get("state") or "neutral").lower(), STATES["neutral"])
        label = item.get("label") or default_label
        text = item.get("text") or item.get("state") or ""
        cells.append(
            f'<td valign="top" style="padding:0 0 0 6px"><div style="display:inline-block;background:{bg};color:{fg};border-radius:999px;padding:7px 10px;font-size:10px;font-weight:900;white-space:nowrap"><span style="color:{dot}">●</span> {esc(label)} · {esc(text)}</div></td>'
        )
    if not cells:
        return ""
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" dir="rtl" style="margin-top:14px"><tr>' + "".join(cells) + '<td>&nbsp;</td></tr></table>'


def kpi_strip_html(kpis: list[dict]) -> str:
    cells = []
    for item in kpis[:4]:
        bg, fg, dot = STATES.get(str(item.get("state") or "purple").lower(), STATES["purple"])
        value = esc(item.get("value") or "—")
        label = esc(item.get("label") or "")
        note = esc(item.get("note") or "")
        cells.append(
            f'<td class="vf-kpi-cell" width="25%" valign="top" style="padding:0 3px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td bgcolor="{bg}" style="padding:11px 8px;border-radius:12px;text-align:center;border:1px solid {dot}"><div style="font-size:20px;line-height:23px;color:{fg};font-weight:900">{value}</div><div style="font-size:9px;color:{fg};font-weight:900;margin-top:2px">{label}</div>'
            + (f'<div style="font-size:8px;color:{fg};opacity:.78;margin-top:3px">{note}</div>' if note else "")
            + '</td></tr></table></td>'
        )
    if not cells:
        return ""
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" dir="rtl" style="margin-top:13px"><tr>' + "".join(cells) + '</tr></table>'


def delta_strip_html(changes: list[object]) -> str:
    rows = []
    for change in changes[:4]:
        if isinstance(change, str):
            text, state = change, "blue"
        else:
            text = change.get("text") or change.get("label") or ""
            state = str(change.get("state") or "blue").lower()
        if not text:
            continue
        _bg, _fg, dot = STATES.get(state, STATES["blue"])
        rows.append(f'<div style="padding:5px 0;color:#dfe5f4;font-size:11px;line-height:17px"><span style="color:{dot};font-weight:900">●</span> {esc(text)}</div>')
    if not rows:
        return ""
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" dir="rtl" style="margin-top:12px"><tr><td bgcolor="#0d1b2f" style="padding:11px 13px;border-radius:13px;border:1px solid #203959"><div style="font-size:9px;color:#8ee8ff;font-weight:900;letter-spacing:.4px">מה השתנה מאז הבריף הקודם</div>' + "".join(rows) + '</td></tr></table>'


def render(brief: dict, template: str | None = None) -> str:
    shell = template if template is not None else TEMPLATE.read_text()
    out = shell
    out = out.replace("{{DATE_LINE}}", prose_html(brief.get("date_line") or ""))
    out = out.replace("{{BOTTOM_LINE}}", prose_html(brief.get("bottom_line") or ""))
    out = out.replace("{{FOOTER}}", esc(brief.get("footer") or "Velvet Factory · איסוף משדרות"))
    out = out.replace("{{STATUS_BADGES}}", status_badges_html(brief))
    out = out.replace("{{KPI_STRIP}}", kpi_strip_html(brief.get("kpis") or []))
    out = out.replace("{{DELTA_STRIP}}", delta_strip_html(brief.get("changes") or []))
    out = out.replace("{{SLOTS}}", "".join(slot_html(s) for s in brief.get("slots") or []))
    return out


def _flow_svg(nodes: tuple[tuple[str, str, str], ...], title: str, *, box_w: int = 100, gap: int = 18, y: int = 48) -> str:
    n = len(nodes)
    start_x = 16
    height = 120
    width = start_x * 2 + n * box_w + (n - 1) * gap
    marker = '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker></defs>'
    edges, boxes = [], []
    for i, (nid, label, kind) in enumerate(nodes):
        x = start_x + i * (box_w + gap)
        cy = y + 28
        if i < n - 1:
            edges.append(f'<path class="edge" marker-end="url(#arrow)" d="M {x + box_w} {cy} L {x + box_w + gap} {cy}"/>')
        boxes.append(f'<rect class="node {kind}" id="{esc(nid)}" x="{x}" y="{y}" width="{box_w}" height="56" rx="8"/><text class="label" text-anchor="middle" x="{x + box_w / 2}" y="{cy + 5}">{esc(label)}</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">{marker}<text class="title" x="{width - 12}" y="22" text-anchor="end">{esc(title)}</text>{"".join(edges)}{"".join(boxes)}</svg>'


def render_diagram(kind: str, template: str | None = None) -> str:
    shell = template if template is not None else DIAGRAM_SHELL.read_text()
    if kind == "pipeline":
        title, svg, heading, sub, doc_title = "צינור הסטודיו", _flow_svg(PIPELINE_NODES, "צינור הסטודיו", box_w=108, gap=20), "צינור · פנייה עד איסוף", "clean-svg · לוויין לבריף · איסוף שדרות בלבד", "Velvet Factory · צינור הסטודיו"
    elif kind == "slots":
        title, svg, heading, sub, doc_title = "חריצי בריף 01–07", _flow_svg(SLOT_NODES, "חריצי בריף 01–07", box_w=86, gap=12), "מבנה בריף · חריצים", "clean-svg · לא מחליף MAIL.html", "Velvet Factory · חריצי בריף"
    else:
        raise SystemExit(f"unknown diagram kind: {kind}")
    out = shell.replace("<title>Velvet Factory · דיאגרמת בריף</title>", f"<title>{esc(doc_title)}</title>", 1)
    out = out.replace("<h1>דיאגרמת בריף</h1>", f"<h1>{esc(heading)}</h1>", 1)
    out = out.replace("לוויין ל־vfbriefux · לא תצוגה 3 במייל", sub, 1)
    if "<!-- SVG -->" not in out:
        raise SystemExit("FAIL diagram shell missing <!-- SVG --> marker")
    return out.replace("<!-- SVG -->", svg, 1)


def self_check() -> None:
    html_out = render(CHECK_BRIEF)
    need = (
        'bgcolor="#080a14"', 'dir="rtl"', "V10 · חי", "מה השתנה מאז הבריף הקודם",
        "מצב העסק", "בריאות מערכת", "01 · קודם החלטה", "07 · פיד בסוף",
        'src="cid:G005.jpg"', "אין ספירה", "#ff5fa2", "#20d9ff",
    )
    missing = [token for token in need if token not in html_out]
    if missing:
        raise SystemExit(f"FAIL render missing {missing}")
    if "{{" in html_out:
        raise SystemExit("FAIL placeholders left in output")
    remote = render({
        "date_line": "x", "bottom_line": "x",
        "slots": [{"kicker": "06", "title": "עמוד", "covers": [{"url": "https://example.com/a.jpg", "href": "https://example.com/post", "caption": "חי"}]}],
    })
    if 'src="https://example.com/a.jpg"' not in remote or 'href="https://example.com/post"' not in remote:
        raise SystemExit("FAIL remote clickable thumbnail")
    if not DIAGRAM_SHELL.is_file():
        raise SystemExit("FAIL missing hq/diagram-svg-template.html")
    for kind, must in (("pipeline", ("פנייה", "שיחה", "הצעה", "הדפסה", "איסוף", 'class="edge"')), ("slots", ("01 החלטה", "07 פיד", "חריצי בריף", 'marker-end="url(#arrow)"'))):
        diagram = render_diagram(kind)
        miss = [token for token in must if token not in diagram]
        if miss:
            raise SystemExit(f"FAIL diagram {kind} missing {miss}")
    print("OK Brief V10 · עברית תחילה · living visual")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Velvet Factory Brief V10 HTML")
    parser.add_argument("json_path", nargs="?", help="brief JSON")
    parser.add_argument("-o", "--out", help="write HTML here")
    parser.add_argument("--check", action="store_true", help="self-check fixture")
    parser.add_argument("--diagram", choices=("pipeline", "slots"), help="render companion SVG diagram")
    args = parser.parse_args()
    if args.check:
        self_check()
        return 0
    if args.diagram:
        html_out = render_diagram(args.diagram)
    else:
        if not args.json_path:
            print("usage: render_mail.py <brief.json> [-o out.html] | --check | --diagram pipeline|slots", file=sys.stderr)
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
