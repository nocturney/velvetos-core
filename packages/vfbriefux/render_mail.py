#!/usr/bin/env python3
"""Fill the תצוגה 3 vfops HTML brief. No invented ₪. No send."""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = Path(__file__).resolve().parent / "MAIL.html"
LTR = re.compile(r"^(VF-[\w.-]+|[A-Z]{2,}[-/]?\d[\w.-]*|G00\d)$")

CHECK_BRIEF = {
    "date_line": "יום בדיקה · תצוגה 3 — לא 07:00",
    "bottom_line": "בוקר טוב. לוח הפרסום לא זז. אין ספירה עד מקור — לא ממציאים.",
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
            "prose": "נתונים מאינסטגרם: אין ספירה.",
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
    print("OK תצוגה 3 html")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render תצוגה 3 vfops HTML brief")
    parser.add_argument("json_path", nargs="?", help="brief JSON")
    parser.add_argument("-o", "--out", help="write HTML here")
    parser.add_argument("--check", action="store_true", help="self-check fixture")
    args = parser.parse_args()
    if args.check:
        self_check()
        return 0
    if not args.json_path:
        print("usage: render_mail.py <brief.json> [-o out.html]", file=sys.stderr)
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
