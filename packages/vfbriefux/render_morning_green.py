#!/usr/bin/env python3
"""Render the Velvet Factory Morning Green owner brief.

Morning-only editorial route. V10.3 remains available for other owner surfaces.
Production accepts cid: package assets and public HTTPS live-media thumbnails.
"""
from __future__ import annotations
import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

PACK = Path(__file__).resolve().parent
TEMPLATE = PACK / "MORNING-GREEN.html"
WEEK_DAYS = 7
MAX_LIST_ITEMS = 6
DECOR = {
    "top": ("cid:morning-top.jpg", "כוס בוקר וענף זית מהקונספט המאושר"),
    "story": ("cid:morning-story.jpg", "ענפי זית באור בוקר"),
    "radar": ("cid:morning-radar.jpg", "מחברת וקפה באור בוקר"),
    "footer": ("cid:morning-footer.jpg", "נוף חם וחתימת Velvet Factory"),
}

def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)

def mixed_text(value: object) -> str:
    """Escape text, then isolate machine IDs so Gmail RTL keeps each ID intact."""
    out=esc(value)
    def repl(match: re.Match[str]) -> str:
        safe_id=match.group(1).replace('-', '&#8209;')
        return f'<span class="vf-id" dir="ltr" style="display:inline-block;direction:ltr;unicode-bidi:isolate;white-space:nowrap;overflow-wrap:normal;word-break:normal;font-size:8px;line-height:12px;letter-spacing:-.35px">{safe_id}</span>'
    return re.sub(r'(VF-\d{8}-\d{3})', repl, out)

def mixed_radar_text(value: object) -> str:
    """Keep Latin product/version fragments readable inside an RTL radar sentence."""
    out=esc(value)

    def phrase_repl(match: re.Match[str]) -> str:
        return f'<span dir="ltr" style="direction:ltr;unicode-bidi:isolate">{match.group(1)}</span>'

    # Long Latin product names may wrap, but must keep their LTR ordering.
    out = re.sub(r'([A-Za-z][A-Za-z0-9. ]*[A-Za-z0-9])', phrase_repl, out)

    # Keep dotted version tokens together so Gmail cannot reverse or split them.
    def version_repl(match: re.Match[str]) -> str:
        return f'<span class="vf-version" dir="ltr" style="display:inline-block;direction:ltr;unicode-bidi:isolate;white-space:nowrap">{match.group(1)}</span>'

    return re.sub(r'(?<![A-Za-z0-9.])(\d+(?:\.\d+)+(?:\.x)?)(?![A-Za-z0-9])', version_repl, out)

def safe_image(value: object, allow_local: bool = False) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("missing image URL")
    if raw.startswith("cid:"):
        if not re.fullmatch(r"cid:[A-Za-z0-9._-]+", raw):
            raise ValueError("invalid cid image reference")
        return esc(raw)
    if allow_local and "://" not in raw:
        return esc(raw)
    parsed = urlparse(raw)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"production image must be cid: or public HTTPS: {raw}")
    return esc(raw)
def replace_tokens(template: str, values: dict[str, str]) -> str:
    missing: list[str] = []
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            missing.append(key)
            return match.group(0)
        return values[key]
    out = re.sub(r"\{\{([a-zA-Z0-9_]+)\}\}", repl, template)
    if missing:
        raise ValueError("missing template values: " + ", ".join(sorted(set(missing))))
    leftovers = sorted(set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", out)))
    if leftovers:
        raise ValueError("unresolved template tokens: " + ", ".join(leftovers))
    return out

def post_cards(posts: object, allow_local: bool) -> str:
    rows = list(posts or [])
    if len(rows) != WEEK_DAYS:
        raise ValueError(f"7-day feed strip requires exactly {WEEK_DAYS} calendar cells, got {len(rows)}")
    cells: list[str] = []
    for post in rows:
        day = esc(post.get("day_label") or "")
        date = esc(post.get("date_label") or "")
        has_post = bool(post.get("has_post"))
        time_raw = str(post.get("time_label") or "").strip()
        time = esc(time_raw)
        kind = esc(post.get("type_label") or "")
        extra = int(post.get("extra_count") or 0)
        if has_post:
            img = safe_image(post.get("image_url"), allow_local)
            alt = esc(post.get("image_alt") or "תצוגה מקדימה של פוסט מתוזמן")
            thumb = f'<img class="vf-feed-thumb" src="{img}" alt="{alt}" width="62" style="width:100%;max-width:62px;height:58px;object-fit:cover;border-radius:10px;margin:0 auto">'
            meta = kind + (f' +{extra}' if extra else '')
            time_html = f'<div dir="ltr" style="font-size:13px;line-height:17px;font-weight:700;color:#17372d;margin-top:6px">{time}</div>'
            meta_html = f'<div style="font-size:9px;line-height:13px;color:#6f766f;margin-top:1px;white-space:nowrap">{meta}</div>'
        else:
            thumb = '<table role="presentation" class="vf-feed-thumb" width="62" align="center" bgcolor="#eef0e8" style="width:100%;max-width:62px;background:#eef0e8;border-radius:10px"><tr><td align="center" height="58" style="height:58px;color:#a3aaa4;font-size:16px">–</td></tr></table>'
            time_html = '<div style="font-size:13px;line-height:17px;color:#a3aaa4;margin-top:6px">&nbsp;</div>'
            meta_html = '<div style="font-size:9px;line-height:13px;color:#a3aaa4;margin-top:1px">&nbsp;</div>'
        cells.append(f'''<td class="vf-week-day" width="14.285%" valign="top" align="center" dir="rtl" style="padding:0 3px 2px;color:#17372d">
<div style="font-size:10px;line-height:14px;font-weight:700;color:#80683f">{day}</div>
<div style="font-size:10px;line-height:14px;color:#7f847f;margin:1px 0 7px">{date}</div>
{thumb}{time_html}{meta_html}
</td>''')
    return "".join(cells)
def feed_status_html(status: object) -> str:
    """Paused/unavailable note under the feed heading; empty for a live schedule."""
    row = status if isinstance(status, dict) else {}
    state = str(row.get('state') or 'live').strip().lower()
    label = str(row.get('label') or '').strip()
    if state == 'live' or not label:
        return ''
    color = '#80683f' if state == 'paused' else '#a85c44'
    return (f'<tr><td class="vf-card-pad vf-feed-status" data-state="{esc(state)}" dir="rtl" align="right" '
            f'style="padding:0 20px 10px;color:{color};font-size:12px;line-height:18px;font-weight:700;text-align:right">{esc(label)}</td></tr>\n')

def instagram_metrics(data: object) -> tuple[str,str]:
    row = data if isinstance(data, dict) else {}
    followers = row.get('followers')
    followers_value = esc(followers if followers is not None else 'אין נתון')

    latest = row.get('latest') if isinstance(row.get('latest'), dict) else {}
    likes = latest.get('likes')
    comments = latest.get('comments')
    if likes is None and comments is None:
        engagement_value = 'אין נתון'
    else:
        parts=[]
        if likes is not None: parts.append(f"{likes} לייק" if int(likes)==1 else f"{likes} לייקים")
        if comments is not None: parts.append(f"{comments} תגובות" if int(comments)!=1 else 'תגובה 1')
        engagement_value = ' · '.join(parts)

    change_raw = str(row.get('change_text') or 'אין נתון שינוי מאומת')
    change_value = 'ללא שינוי' if 'ללא שינוי' in change_raw else change_raw

    metrics = [
        (followers_value, 'עוקבים'),
        (esc(engagement_value), 'מעורבות בפוסט האחרון'),
        (esc(change_value), 'מאז הבריף הקודם'),
    ]
    cells=[]
    for idx,(value,label) in enumerate(metrics):
        cls='vf-insta-metric vf-insta-last' if idx==2 else 'vf-insta-metric'
        border='' if idx==2 else 'border-left:1px solid #ddd5c7;'
        size='24px' if idx!=1 else '18px'
        cells.append(f'<td class="{cls}" width="33.333%" align="center" valign="middle" dir="rtl" style="padding:15px 8px;color:#17372d;{border}"><div class="vf-insta-value" style="font-size:{size};line-height:28px;font-weight:700;overflow-wrap:anywhere">{value}</div><div class="vf-insta-label" style="font-size:10px;line-height:15px;color:#6f766f;margin-top:3px">{label}</div></td>')

    note_parts=[]
    if row.get('following') is not None: note_parts.append(f"עוקב אחרי {int(row['following'])}")
    if row.get('media_count') is not None: note_parts.append(f"{int(row['media_count'])} פריטי מדיה")
    previous = row.get('previous') if isinstance(row.get('previous'), dict) else {}
    if previous.get('likes') is not None or previous.get('comments') is not None:
        prev=[]
        if previous.get('likes') is not None: prev.append(f"{int(previous['likes'])} לייקים")
        if previous.get('comments') is not None: prev.append(f"{int(previous['comments'])} תגובות")
        note_parts.append('פוסט קודם: ' + ' · '.join(prev))
    if not row.get('insights_available'):
        note_parts.append('Reach / חשיפות: אין נתון Insights מאומת')
    elif row.get('insights_note'):
        note_parts.append('Insights: '+str(row['insights_note']))
    return ''.join(cells), esc(' · '.join(note_parts))

def item_grid(items: object, accent: str, widths: list[float] | None = None) -> str:
    rows = list(items or [])[:4]
    if not rows:
        return '<td class="vf-item-cell" width="100%" dir="rtl" align="right" style="padding:12px 4px 2px;color:#7f847f;font-size:13px;line-height:19px;text-align:right">אין פריטים להצגה.</td>'
    if widths is None or len(widths) != len(rows):
        widths = [100/len(rows)] * len(rows)
    cells: list[str] = []
    for idx, item in enumerate(rows):
        title = mixed_text(item.get("title") if isinstance(item, dict) else item)
        detail = mixed_text(item.get("detail") if isinstance(item, dict) else "")
        border = "" if idx == len(rows)-1 else "border-left:1px solid #e1d9cb;"
        detail_html = f'<div class="vf-item-detail" dir="rtl" style="font-size:10px;line-height:15px;color:#7f847f;margin-top:4px;text-align:right;overflow-wrap:anywhere">{detail}</div>' if detail else ""
        width = f"{widths[idx]:.3f}%"
        cells.append(f'<td class="vf-item-cell" width="{width}" valign="top" dir="rtl" align="right" style="padding:11px 7px 3px;color:#17372d;text-align:right;overflow-wrap:anywhere;{border}"><div class="vf-item-title" style="font-size:11px;line-height:16px;font-weight:700"><span style="color:{accent}">&#9679;</span>&nbsp;{title}</div>{detail_html}</td>')
    return "".join(cells)

def stat_cells(stats: object) -> str:
    rows = list(stats or [])[:3]
    while len(rows) < 3:
        rows.append({"value":"אין נתון","label":""})
    rows.reverse()
    cells: list[str] = []
    for idx, stat in enumerate(rows):
        cls = "vf-stat vf-stat-last" if idx == 2 else "vf-stat"
        border = "" if idx == 2 else "border-left:1px solid #718a7d;"
        cells.append(f'<td class="{cls}" width="33.333%" align="center" dir="rtl" style="padding:20px 8px;color:#fff8ec;{border}"><div class="vf-stat-value" style="font-size:30px;line-height:36px;font-weight:700">{esc(stat.get("value",""))}</div><div class="vf-stat-label" style="font-size:11px;line-height:17px;color:#d8d0bf;margin-top:3px">{esc(stat.get("label",""))}</div></td>')
    return "".join(cells)

def decor_image(data: dict, key: str, allow_local: bool) -> tuple[str, str]:
    item = data.get(key) or {}
    default_url, default_alt = DECOR[key.replace("_image","")]
    return safe_image(item.get("url") or default_url, allow_local), esc(item.get("alt") or default_alt)
def render(data: dict, *, allow_local: bool = False, template: str | None = None) -> str:
    shell = template if template is not None else TEMPLATE.read_text(encoding="utf-8")
    top_url, top_alt = decor_image(data, "top_image", allow_local)
    story_url = safe_image((data.get("story") or {}).get("image", {}).get("url") or DECOR["story"][0], allow_local)
    story_alt = esc((data.get("story") or {}).get("image", {}).get("alt") or DECOR["story"][1])
    radar_url = safe_image((data.get("radar") or {}).get("image", {}).get("url") or DECOR["radar"][0], allow_local)
    radar_alt = esc((data.get("radar") or {}).get("image", {}).get("alt") or DECOR["radar"][1])
    footer_url = safe_image((data.get("footer") or {}).get("image", {}).get("url") or DECOR["footer"][0], allow_local)
    footer_alt = esc((data.get("footer") or {}).get("image", {}).get("alt") or (data.get("footer") or {}).get("quote") or DECOR["footer"][1])
    instagram_html, instagram_note = instagram_metrics(data.get('instagram'))
    values = {
        "email_title": esc(data.get("email_title") or "Velvet Factory - Morning Brief"),
        "preheader": esc(data.get("preheader") or ""),
        "date_label": esc(data["date_label"]),
        "greeting": esc(data["greeting"]),
        "daily_summary": esc(data["daily_summary"]),
        "top_image_url": top_url, "top_image_alt": top_alt,
        "scheduled_posts_html": post_cards(data.get("scheduled_posts"), allow_local),
        "feed_status_html": feed_status_html(data.get("feed_status")),
        "instagram_metrics_html": instagram_html,
        "instagram_note": instagram_note,
        "story_title": esc(data["story"]["title"]), "story_body": esc(data["story"]["body"]),
        "story_image_url": story_url, "story_image_alt": story_alt,
        "morning_line": esc(data["morning_line"]["text"]),
        "morning_line_note": esc(data["morning_line"].get("note") or ""),
        "attention_html": item_grid(data.get("attention"), "#a85c44", [18.0, 27.333, 27.333, 27.334]),
        "progress_html": item_grid(data.get("progress"), "#4b8a64"),
        "radar_image_url": radar_url, "radar_image_alt": radar_alt,
        "radar_title": esc(data["radar"]["title"]), "radar_text": mixed_radar_text(data["radar"]["text"]),
        "stats_html": stat_cells(data.get("stats")),
        "footer_image_url": footer_url, "footer_image_alt": footer_alt,
        "closing_quote": esc(data["footer"]["quote"]),
        "closing_note": esc(data["footer"].get("note") or ""),
    }
    return replace_tokens(shell, values)
def self_check() -> None:
    fixture = {
        "date_label":"יום בדיקה · Asia/Jerusalem",
        "greeting":"בוקר טוב, כריסטיאן",
        "daily_summary":"המידע החשוב קודם.",
        "scheduled_posts":[
            {"day_label":"ד׳","date_label":"23.9","has_post":False,"time_label":"","type_label":"","extra_count":0},
            {"day_label":"ה׳","date_label":"24.9","has_post":True,"image_url":"https://example.com/post.jpg","image_alt":"פוסט מתוזמן","time_label":"09:00","type_label":"פוסט","extra_count":0},
            {"day_label":"ו׳","date_label":"25.9","has_post":False,"time_label":"","type_label":"","extra_count":0},
            {"day_label":"שבת","date_label":"26.9","has_post":False,"time_label":"","type_label":"","extra_count":0},
            {"day_label":"א׳","date_label":"27.9","has_post":True,"image_url":"https://example.com/post2.jpg","image_alt":"קרוסלה מתוזמנת","time_label":"12:00","type_label":"קרוסלה","extra_count":1},
            {"day_label":"ב׳","date_label":"28.9","has_post":False,"time_label":"","type_label":"","extra_count":0},
            {"day_label":"ג׳","date_label":"29.9","has_post":False,"time_label":"","type_label":"","extra_count":0}
        ],
        "instagram":{"followers":81,"following":125,"media_count":5,"latest":{"likes":1,"comments":0,"date_label":"20.9.2026"},"previous":{"likes":2,"comments":1,"date_label":"19.9.2026"},"change_text":"אין שינוי מאומת","insights_available":False,"insights_note":"אין ספירה"},
        "story":{"title":"הסיפור של היום","body":"פרטים נוחים לקריאה","image":{}},
        "morning_line":{"text":"פחות ז׳רגון, יותר הקשר.","note":"בדיקה"},
        "attention":[{"title":"סינקופה VF-20260908-001","detail":"4350"}],
        "progress":[{"title":"משהו התקדם","detail":"פירוט"}],
        "radar":{"title":"על הרדאר","text":"Bambu Studio 2.8.4 Public Beta - למעקב בלבד; ייצור נשאר 2.8.2.x.","image":{}},
        "stats":[{"value":"1","label":"מתוזמן"},{"value":"2","label":"פעיל"},{"value":"3","label":"פתוח"}],
        "footer":{"quote":"Same, brighter tomorrow.","note":"Velvet Factory","image":{}},
    }
    out = render(fixture)
    for token in ("MORNING EDITION","בקרוב בפיד","Instagram","81","מעורבות בפוסט האחרון","Reach / חשיפות: אין נתון Insights מאומת",'src="cid:morning-top.jpg"','class="vf-week-day"',"09:00","12:00","#15352b",'class="vf-id"','class="vf-version"','dir="ltr"'):
        if token not in out:
            raise SystemExit(f"FAIL Morning Green missing {token!r}")
    if out.count('class="vf-week-day"') != 7:
        raise SystemExit("FAIL Morning Green feed strip is not exactly seven days")
    if "{{" in out:
        raise SystemExit("FAIL Morning Green unresolved template token")
    try:
        safe_image("http://example.com/bad.jpg")
    except ValueError:
        pass
    else:
        raise SystemExit("FAIL Morning Green accepted non-HTTPS production image")
    print("OK Morning Green v3.1 · RTL · Gmail-mobile-safe · Outlook-safe · cid/https")

def main() -> int:
    ap = argparse.ArgumentParser(description="Render Velvet Factory Morning Green email")
    ap.add_argument("json_path", nargs="?")
    ap.add_argument("-o","--out")
    ap.add_argument("--allow-local-images", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        self_check(); return 0
    if not args.json_path:
        print("usage: render_morning_green.py <brief.json> [-o out.html]", file=sys.stderr); return 2
    data = json.loads(Path(args.json_path).read_text(encoding="utf-8"))
    output = render(data, allow_local=args.allow_local_images)
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
