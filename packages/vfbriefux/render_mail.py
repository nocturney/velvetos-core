#!/usr/bin/env python3
"""Render Velvet Factory Brief V10.2 Ink & Candy.

Gmail-safe table HTML, RTL-first, Hebrew-first. Backward-compatible with the
legacy 01–07 JSON. Adds image-first hero, split media cards, visual mini-cards,
KPI/status/delta blocks, and fallback enrichment from the canonical Studio Pulse.
No invented ₪. No send.
"""
from __future__ import annotations

import argparse
import copy
import html
import json
import re
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
TEMPLATE = PACK / "MAIL.html"
DIAGRAM_SHELL = PACK / "hq" / "diagram-svg-template.html"
PULSE_LATEST = PACK.parent / "velvetos" / "living-studio" / "data" / "pulse-latest.json"
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

# Ink & Candy: deep ink + hot pink + periwinkle + acid lime.
THEMES = {
    "decision": ("#FF4F91", "#FFF0F6", "#A51E57", "#321627"),
    "money": ("#B8F34A", "#F3FFD9", "#4B7200", "#1B2812"),
    "production": ("#FF8C66", "#FFF2ED", "#A94528", "#311A14"),
    "revenue": ("#FFD45A", "#FFF8DE", "#8A6500", "#302610"),
    "office": ("#6C7CFF", "#F0F1FF", "#4655CC", "#1D2340"),
    "insights": ("#45D7FF", "#EAFBFF", "#087D99", "#102A34"),
    "content": ("#FF4F91", "#FFF0F6", "#A51E57", "#321627"),
    "neutral": ("#8C96AB", "#F4F6FB", "#596277", "#242B3A"),
}
STATES = {
    "green": ("#EAFBD8", "#3F6900", "#8DD826"),
    "yellow": ("#FFF5D1", "#805E00", "#FFD45A"),
    "red": ("#FFE6F0", "#9E174D", "#FF4F91"),
    "blue": ("#E8F9FF", "#087D99", "#45D7FF"),
    "purple": ("#EEF0FF", "#4655CC", "#6C7CFF"),
    "neutral": ("#EEF1F6", "#596277", "#8C96AB"),
}

CHECK_BRIEF = {
    "date_line": "יום בדיקה · V10.2 — לא 07:00",
    "bottom_line": "המידע החשוב קודם. לא ממציאים.",
    "footer": "Velvet Factory · איסוף משדרות · V10.2",
    "attention": {"state": "yellow", "label": "מצב העסק", "text": "דורש מעקב"},
    "system_health": {"state": "green", "label": "בריאות מערכת", "text": "תקינה"},
    "hero_visual": {
        "url": "https://example.com/hero.jpg",
        "href": "https://example.com/item",
        "eyebrow": "תמונת היום",
        "title": "האות הוויזואלי המרכזי",
        "caption": "asset אמיתי בלבד",
    },
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
            "kind": "decision",
            "kicker": "צריך ממך · 1",
            "title": "החלטה",
            "prose": "כרטיס החלטה ברור.",
        },
        {
            "kind": "production",
            "layout": "split",
            "kicker": "עבודה חיה",
            "title": "ייצור",
            "prose": "שלב הבא אמיתי בלבד.",
            "covers": [{"cid": "job.jpg", "caption": "תמונת עבודה"}],
        },
        {
            "kind": "content",
            "kicker": "רדאר תוכן",
            "title": "מה קורה בתוכן",
            "cards": [
                {"cid": "c1.jpg", "kicker": "מאומת חי", "title": "Reel", "text": "thumbnail + קישור"},
                {"url": "https://example.com/c2.jpg", "href": "https://example.com/post", "kicker": "מועמד", "title": "Carousel", "text": "asset אמיתי"},
            ],
        },
        {
            "kind": "office",
            "density": "compact",
            "kicker": "פעילות VelvetOS",
            "title": "מה המערכת עשתה בפועל",
            "prose": "receipt אמיתי בלבד.",
        },
    ],
}


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def prose_html(text: str) -> str:
    return "<br>".join(esc(line) for line in str(text).split("\n"))


def cell_html(text: str) -> str:
    raw = str(text).strip()
    first = raw.split()[0] if raw else ""
    if LTR.match(first):
        rest = raw[len(first):].lstrip()
        body = f'<span dir="ltr" style="direction:ltr;display:inline-block">{esc(first)}</span>'
        return body + (f" {esc(rest)}" if rest else "")
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


def _load_pulse() -> dict:
    if not PULSE_LATEST.is_file():
        return {}
    try:
        data = json.loads(PULSE_LATEST.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _he_change(raw: object) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    if text == "first pulse this session":
        return "נוצר Studio Pulse ראשון בסשן"
    if text.startswith("media "):
        return "מדיה: " + text[6:]
    if text.startswith("followups "):
        return "מעקבים: " + text[10:]
    if text.startswith("insights_deployed→"):
        val = text.split("→", 1)[1]
        return "Insights: " + ("הוטמע" if val.lower() == "true" else "לא מוטמע")
    return text


def _visual_src(item: dict) -> str:
    cid = str(item.get("cid") or "").strip()
    remote = str(item.get("url") or item.get("src") or "").strip()
    return f"cid:{cid}" if cid else remote


def _promote_hero(brief: dict) -> None:
    """Promote an existing real visual to hero when no explicit hero was supplied."""
    if brief.get("hero_visual"):
        return
    preferred = {"production": 0, "content": 1, "insights": 2, "revenue": 3, "neutral": 9}
    candidates: list[tuple[int, dict, dict]] = []
    for slot in brief.get("slots") or []:
        priority = preferred.get(slot_kind(slot), 8)
        for cover in slot.get("covers") or []:
            if _visual_src(cover):
                candidates.append((priority, slot, cover))
    if not candidates:
        return
    _priority, slot, cover = sorted(candidates, key=lambda x: x[0])[0]
    hero = dict(cover)
    hero.setdefault("eyebrow", "תמונת היום")
    hero.setdefault("title", slot.get("title") or "מה קורה עכשיו")
    hero.setdefault("caption", cover.get("caption") or "נכס אמיתי מהעבודה")
    brief["hero_visual"] = hero
    cover["_promoted_to_hero"] = True


def enrich_v10(brief: dict) -> dict:
    pulse = _load_pulse()
    if pulse:
        now = pulse.get("what_happening_now") or {}
        moved = pulse.get("what_moved_since_last") or []
        stuck = pulse.get("what_stuck") or []
        needs = pulse.get("what_requires_christian") or []
        if not brief.get("attention"):
            if needs:
                brief["attention"] = {"state": "red", "label": "מצב העסק", "text": f"{len(needs)} דורשים אותך"}
            elif stuck:
                brief["attention"] = {"state": "yellow", "label": "מצב העסק", "text": f"{len(stuck)} במעקב"}
            else:
                brief["attention"] = {"state": "green", "label": "מצב העסק", "text": "ללא חסם בעלים"}
        if not brief.get("system_health"):
            health = str(pulse.get("system_health") or "").strip()
            paused = bool(now.get("office_paused"))
            lower = health.lower()
            if paused:
                state, text = "yellow", "המשרד מושהה לפי בעלים"
            elif any(word in lower for word in ("green", "healthy", "ok", "תקין")):
                state, text = "green", "תקינה"
            elif health:
                state, text = "yellow", health[:56]
            else:
                state, text = "neutral", "אין סטטוס"
            brief["system_health"] = {"state": state, "label": "בריאות מערכת", "text": text}
        if not brief.get("changes"):
            changes = [{"text": _he_change(x), "state": "blue"} for x in moved[:4] if _he_change(x)]
            if changes:
                brief["changes"] = changes
        if not brief.get("kpis"):
            kpis = []
            jobs = now.get("jobs")
            if isinstance(jobs, int):
                kpis.append({"value": str(jobs), "label": "עבודות במקור האמת", "state": "purple"})
            kpis.append({"value": str(len(needs)), "label": "צריך ממך", "state": "red" if needs else "green"})
            followups = now.get("followups")
            if isinstance(followups, dict):
                total = sum(v for v in followups.values() if isinstance(v, int))
                kpis.append({"value": str(total), "label": "מעקבים פתוחים", "state": "yellow" if total else "green"})
            media_inbox = now.get("media_inbox")
            if isinstance(media_inbox, int):
                kpis.append({"value": str(media_inbox), "label": "מדיה בקליטה", "state": "blue"})
            brief["kpis"] = kpis[:4]
        translated = [_he_change(x) for x in moved if _he_change(x)]
        for slot in brief.get("slots") or []:
            kind = slot_kind(slot)
            slot.setdefault("kind", kind)
            if kind == "office":
                if translated and not slot.get("delta"):
                    slot["delta"] = {"text": f"{len(translated)} שינויים נקלטו ב־Studio Pulse", "state": "purple"}
                elif not translated:
                    slot.setdefault("density", "compact")
            if kind == "decision" and not needs:
                slot.setdefault("density", "compact")
    _promote_hero(brief)
    return brief


def _image_html(item: dict, *, width: int = 560, radius: int = 14, promoted_ok: bool = False) -> str:
    if item.get("_promoted_to_hero") and not promoted_ok:
        return ""
    src = _visual_src(item)
    if not src:
        return ""
    href = str(item.get("href") or "").strip()
    alt = item.get("alt") or item.get("caption") or item.get("title") or "תמונה"
    image = (
        f'<img class="vf-img" src="{esc(src)}" alt="{esc(alt)}" width="{width}" '
        f'style="display:block;width:100%;max-width:{width}px;height:auto;border:0;border-radius:{radius}px;margin:0">'
    )
    return f'<a href="{esc(href)}" style="text-decoration:none">{image}</a>' if href else image


def hero_visual_html(item: dict | None) -> str:
    if not item or not _visual_src(item):
        return ""
    image = _image_html(item, width=636, radius=17, promoted_ok=True)
    eyebrow = esc(item.get("eyebrow") or "תמונת היום")
    title = esc(item.get("title") or "")
    caption = esc(item.get("caption") or "")
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" dir="rtl" style="margin-top:14px">'
        '<tr><td bgcolor="#0F1724" style="padding:8px;border-radius:19px;border:1px solid #303B58">'
        + image
        + '<div style="padding:10px 8px 7px">'
        + f'<div style="font-size:9px;color:#B8F34A;font-weight:900">{eyebrow}</div>'
        + (f'<div style="font-size:18px;line-height:23px;color:#FFFFFF;font-weight:900;margin-top:3px">{title}</div>' if title else "")
        + (f'<div style="font-size:10px;line-height:16px;color:#AAB4CA;margin-top:4px">{caption}</div>' if caption else "")
        + '</div></td></tr></table>'
    )


def table_html(headers: list[str], rows: list[list[str]], theme: tuple[str, str, str, str]) -> str:
    accent, soft, _label, dark = theme
    head = "".join(f'<td dir="rtl" bgcolor="{dark}" align="right" style="color:#fff;font-weight:800;border-bottom:3px solid {accent}">{esc(h)}</td>' for h in headers)
    body = []
    for i, row in enumerate(rows):
        bg = "#FFFFFF" if i % 2 == 0 else soft
        cells = "".join(f'<td dir="rtl" bgcolor="{bg}" align="right" style="border-bottom:1px solid #E5E8EF">{cell_html(c)}</td>' for c in row)
        body.append(f"<tr>{cells}</tr>")
    return '<table width="100%" cellpadding="9" cellspacing="0" border="0" dir="rtl" style="border-collapse:separate;border-spacing:0;font-size:13px;border-radius:12px;overflow:hidden"><tbody><tr>' + head + '</tr>' + ''.join(body) + '</tbody></table>'


def covers_html(covers: list[dict], theme: tuple[str, str, str, str]) -> str:
    _accent, _soft, label, _dark = theme
    parts = []
    for cover in covers:
        image = _image_html(cover)
        if not image:
            continue
        caption = cover.get("caption") or cover.get("alt") or "תמונה"
        parts.append(f'<div dir="rtl" style="margin:12px 0 5px;font-size:11px;color:{label};font-weight:900">{esc(caption)}</div>{image}')
    return ''.join(parts)


def media_cards_html(cards: list[dict], theme: tuple[str, str, str, str]) -> str:
    accent, _soft, label, _dark = theme
    usable = [c for c in cards[:3] if c.get("title") or c.get("text") or _visual_src(c)]
    if not usable:
        return ""
    width = max(1, 100 // len(usable))
    cells = []
    for card in usable:
        image = _image_html(card, width=180, radius=10)
        kicker = esc(card.get("kicker") or "")
        title = esc(card.get("title") or "")
        text = esc(card.get("text") or "")
        action = esc(card.get("action") or "")
        cells.append(
            f'<td class="vf-mini-cell" width="{width}%" valign="top" style="padding:0 3px">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td bgcolor="#FFFFFF" style="padding:9px;border-radius:13px;border:1px solid #E1E5EE">'
            + image
            + (f'<div style="font-size:9px;color:{label};font-weight:900;margin-top:8px">{kicker}</div>' if kicker else "")
            + (f'<div style="font-size:13px;line-height:17px;color:#171D2C;font-weight:900;margin-top:3px">{title}</div>' if title else "")
            + (f'<div style="font-size:10px;line-height:16px;color:#697287;margin-top:4px">{text}</div>' if text else "")
            + (f'<div style="font-size:9px;line-height:15px;color:{label};font-weight:900;margin-top:7px;border-top:1px solid #EEF0F5;padding-top:6px">{action}</div>' if action else "")
            + '</td></tr></table></td>'
        )
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" dir="rtl" style="margin-top:11px"><tr>' + ''.join(cells) + '</tr></table>'


def actions_html(actions: list[dict], theme: tuple[str, str, str, str]) -> str:
    accent, _soft, label_color, _dark = theme
    parts = [f'<div dir="rtl" style="margin:12px 0 6px;font-size:11px;color:{label_color};font-weight:900">אישור בלחיצה · לא הודעת לקוח · לא Print</div>']
    for item in actions:
        label = esc(item.get("label") or item.get("id") or "שער")
        links = []
        if item.get("yes"):
            links.append(f'<a class="vf-touch" href="{esc(item["yes"])}" style="color:#fff;text-decoration:none;background:{accent};border-radius:9px;padding:8px 12px;margin-left:7px;display:inline-block;font-weight:900">כן</a>')
        if item.get("no"):
            links.append(f'<a class="vf-touch" href="{esc(item["no"])}" style="color:#9E174D;text-decoration:none;background:#FFE6F0;border-radius:9px;padding:8px 12px;margin-left:7px;display:inline-block;font-weight:900">דחה</a>')
        if item.get("defer"):
            links.append(f'<a class="vf-touch" href="{esc(item["defer"])}" style="color:#596277;text-decoration:none;background:#EEF1F6;border-radius:9px;padding:8px 12px;display:inline-block;font-weight:900">דחה למועד</a>')
        parts.append(f'<p dir="rtl" style="font-size:13px;color:#23293A;margin:9px 0">{label} {" ".join(links)}</p>')
    return ''.join(parts)


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


def _slot_text_body(slot: dict, theme: tuple[str, str, str, str], *, include_covers: bool = True) -> str:
    bits = []
    prose = slot.get("prose") or ""
    if prose:
        bits.append(f'<p dir="rtl" style="font-size:14px;line-height:1.65;color:#30364D;margin:0 0 10px">{prose_html(prose)}</p>')
    headers, rows = slot.get("headers") or [], slot.get("rows") or []
    if headers and rows:
        bits.append(table_html(headers, rows, theme))
    cards = slot.get("cards") or []
    if cards:
        bits.append(media_cards_html(cards, theme))
    if include_covers and slot.get("covers"):
        bits.append(covers_html(slot.get("covers") or [], theme))
    if slot.get("actions"):
        bits.append(actions_html(slot.get("actions") or [], theme))
    return ''.join(bits)


def slot_html(slot: dict) -> str:
    theme = THEMES[slot_kind(slot)]
    accent, soft, label, _dark = theme
    density = str(slot.get("density") or "normal").lower()
    pad = "13px 18px" if density == "compact" else "17px 20px"
    header = (
        f'<div style="color:{label};font-size:10px;font-weight:900;letter-spacing:.2px">{esc(slot.get("kicker") or "")}</div>'
        f'<h2 style="margin:4px 0 8px;color:#171D2C;font-size:21px;line-height:26px">{esc(slot.get("title") or "")}</h2>'
        + slot_delta_html(slot)
    )
    layout = str(slot.get("layout") or "").lower()
    covers = [c for c in (slot.get("covers") or []) if not c.get("_promoted_to_hero") and _visual_src(c)]
    if layout == "split" and covers:
        first = covers[0]
        image = _image_html(first, width=210, radius=12)
        caption = esc(first.get("caption") or first.get("alt") or "תמונה")
        body = (
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" dir="rtl"><tr>'
            f'<td class="vf-split-cell" width="38%" valign="top" style="padding-left:12px">{image}<div style="font-size:9px;color:{label};font-weight:900;margin-top:6px">{caption}</div></td>'
            f'<td class="vf-split-cell" width="62%" valign="top">{_slot_text_body(slot, theme, include_covers=False)}</td>'
            '</tr></table>'
        )
        if len(covers) > 1:
            body += covers_html(covers[1:], theme)
    else:
        body = _slot_text_body(slot, theme, include_covers=True)
    return (
        '<tr><td dir="rtl" bgcolor="#F4F6FB" class="vf-slot" style="padding:6px 12px">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" dir="rtl"><tr><td bgcolor="{soft}" style="padding:{pad};border-radius:16px;border:1px solid #E1E5EE;border-right:4px solid {accent}">'
        + header + body + '</td></tr></table></td></tr>'
    )


def status_badges_html(brief: dict) -> str:
    cells = []
    for key, default_label in (("attention", "מצב העסק"), ("system_health", "בריאות מערכת")):
        item = brief.get(key) or {}
        if not item:
            continue
        bg, fg, dot = STATES.get(str(item.get("state") or "neutral").lower(), STATES["neutral"])
        label = item.get("label") or default_label
        text = item.get("text") or item.get("state") or ""
        cells.append(f'<td valign="top" style="padding:0 0 0 6px"><div style="display:inline-block;background:{bg};color:{fg};border-radius:999px;padding:7px 10px;font-size:10px;font-weight:900;white-space:nowrap"><span style="color:{dot}">●</span> {esc(label)} · {esc(text)}</div></td>')
    return '' if not cells else '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" dir="rtl" style="margin-top:14px"><tr>' + ''.join(cells) + '<td>&nbsp;</td></tr></table>'


def kpi_strip_html(kpis: list[dict]) -> str:
    cells = []
    for item in kpis[:4]:
        bg, fg, dot = STATES.get(str(item.get("state") or "purple").lower(), STATES["purple"])
        value, label, note = esc(item.get("value") or "—"), esc(item.get("label") or ""), esc(item.get("note") or "")
        cells.append(f'<td class="vf-kpi-cell" width="25%" valign="top" style="padding:0 3px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td bgcolor="{bg}" style="padding:11px 8px;border-radius:12px;text-align:center;border:1px solid {dot}"><div style="font-size:20px;line-height:23px;color:{fg};font-weight:900">{value}</div><div style="font-size:9px;color:{fg};font-weight:900;margin-top:2px">{label}</div>' + (f'<div style="font-size:8px;color:{fg};margin-top:3px">{note}</div>' if note else '') + '</td></tr></table></td>')
    return '' if not cells else '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" dir="rtl" style="margin-top:13px"><tr>' + ''.join(cells) + '</tr></table>'


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
        rows.append(f'<div style="padding:5px 0;color:#E5E9F3;font-size:11px;line-height:17px"><span style="color:{dot};font-weight:900">●</span> {esc(text)}</div>')
    return '' if not rows else '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" dir="rtl" style="margin-top:12px"><tr><td bgcolor="#1A2438" style="padding:11px 13px;border-radius:13px;border:1px solid #303B58"><div style="font-size:9px;color:#AEB7FF;font-weight:900">מה השתנה מאז הבריף הקודם</div>' + ''.join(rows) + '</td></tr></table>'


def render(brief: dict, template: str | None = None) -> str:
    brief = enrich_v10(copy.deepcopy(brief))
    shell = template if template is not None else TEMPLATE.read_text()
    out = shell.replace("{{DATE_LINE}}", prose_html(brief.get("date_line") or ""))
    out = out.replace("{{BOTTOM_LINE}}", prose_html(brief.get("bottom_line") or ""))
    out = out.replace("{{FOOTER}}", esc(brief.get("footer") or "Velvet Factory · איסוף משדרות"))
    out = out.replace("{{STATUS_BADGES}}", status_badges_html(brief))
    out = out.replace("{{HERO_VISUAL}}", hero_visual_html(brief.get("hero_visual")))
    out = out.replace("{{KPI_STRIP}}", kpi_strip_html(brief.get("kpis") or []))
    out = out.replace("{{DELTA_STRIP}}", delta_strip_html(brief.get("changes") or []))
    out = out.replace("{{SLOTS}}", ''.join(slot_html(s) for s in brief.get("slots") or []))
    return out


def _flow_svg(nodes: tuple[tuple[str, str, str], ...], title: str, *, box_w: int = 100, gap: int = 18, y: int = 48) -> str:
    n, start_x, height = len(nodes), 16, 120
    width = start_x * 2 + n * box_w + (n - 1) * gap
    marker = '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker></defs>'
    edges, boxes = [], []
    for i, (nid, label, kind) in enumerate(nodes):
        x, cy = start_x + i * (box_w + gap), y + 28
        if i < n - 1:
            edges.append(f'<path class="edge" marker-end="url(#arrow)" d="M {x + box_w} {cy} L {x + box_w + gap} {cy}"/>')
        boxes.append(f'<rect class="node {kind}" id="{esc(nid)}" x="{x}" y="{y}" width="{box_w}" height="56" rx="8"/><text class="label" text-anchor="middle" x="{x + box_w / 2}" y="{cy + 5}">{esc(label)}</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">{marker}<text class="title" x="{width - 12}" y="22" text-anchor="end">{esc(title)}</text>{"".join(edges)}{"".join(boxes)}</svg>'


def render_diagram(kind: str, template: str | None = None) -> str:
    shell = template if template is not None else DIAGRAM_SHELL.read_text()
    if kind == "pipeline":
        svg, heading, sub, doc_title = _flow_svg(PIPELINE_NODES, "צינור הסטודיו", box_w=108, gap=20), "צינור · פנייה עד איסוף", "clean-svg · לוויין לבריף · איסוף שדרות בלבד", "Velvet Factory · צינור הסטודיו"
    elif kind == "slots":
        svg, heading, sub, doc_title = _flow_svg(SLOT_NODES, "חריצי בריף 01–07", box_w=86, gap=12), "מבנה בריף · חריצים", "clean-svg · לא מחליף MAIL.html", "Velvet Factory · חריצי בריף"
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
        'bgcolor="#101828"', 'dir="rtl"', "V10.2 · חי", "מה השתנה מאז הבריף הקודם",
        "מצב העסק", "בריאות מערכת", "תמונת היום", 'src="https://example.com/hero.jpg"',
        'src="cid:job.jpg"', 'src="cid:c1.jpg"', "#FF4F91", "#6C7CFF", "#B8F34A",
    )
    missing = [token for token in need if token not in html_out]
    if missing:
        raise SystemExit(f"FAIL render missing {missing}")
    if "{{" in html_out:
        raise SystemExit("FAIL placeholders left in output")
    if not DIAGRAM_SHELL.is_file():
        raise SystemExit("FAIL missing hq/diagram-svg-template.html")
    for kind, must in (("pipeline", ("פנייה", "שיחה", "הצעה", "הדפסה", "איסוף", 'class="edge"')), ("slots", ("01 החלטה", "07 פיד", "חריצי בריף", 'marker-end="url(#arrow)"'))):
        diagram = render_diagram(kind)
        miss = [token for token in must if token not in diagram]
        if miss:
            raise SystemExit(f"FAIL diagram {kind} missing {miss}")
    print("OK Brief V10.2 · Ink & Candy · image-first · Hebrew-first")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Velvet Factory Brief V10.2 HTML")
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
            print("usage: render_mail.py <brief.json> [-o out.html]", file=sys.stderr)
            return 2
        brief = json.loads(Path(args.json_path).read_text(encoding="utf-8"))
        html_out = render(brief)
    if args.out:
        Path(args.out).write_text(html_out, encoding="utf-8")
    else:
        sys.stdout.write(html_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
