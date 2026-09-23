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
    "top": ("cid:morning-top.jpg", "אווירת בוקר ירוקה"),
    "story": ("cid:morning-story.jpg", "סצנת בוקר רגועה"),
    "radar": ("cid:morning-radar.jpg", "פרט ירוק"),
    "footer": ("cid:morning-footer.jpg", "סצנת סיום ירוקה"),
}

def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)

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
            thumb = f'<img src="{img}" alt="{alt}" width="82" style="width:100%;max-width:82px;height:74px;object-fit:cover;border-radius:11px;margin:0 auto">'
            meta = kind + (f' +{extra}' if extra else '')
            time_html = f'<div dir="ltr" style="font-size:13px;line-height:17px;font-weight:700;color:#17372d;margin-top:6px">{time}</div>'
            meta_html = f'<div style="font-size:9px;line-height:13px;color:#6f766f;margin-top:1px;white-space:nowrap">{meta}</div>'
        else:
            thumb = '<table role="presentation" width="100%" bgcolor="#eef0e8" style="background:#eef0e8;border-radius:11px"><tr><td align="center" height="74" style="height:74px;color:#a3aaa4;font-size:16px">–</td></tr></table>'
            time_html = '<div style="font-size:13px;line-height:17px;color:#a3aaa4;margin-top:6px">&nbsp;</div>'
            meta_html = '<div style="font-size:9px;line-height:13px;color:#a3aaa4;margin-top:1px">&nbsp;</div>'
        cells.append(f'''<td class="vf-week-day" width="14.285%" valign="top" align="center" style="padding:0 4px 2px;color:#17372d">
<div style="font-size:11px;line-height:15px;font-weight:700;color:#80683f">{day}</div>
<div style="font-size:10px;line-height:14px;color:#7f847f;margin:1px 0 7px">{date}</div>
{thumb}{time_html}{meta_html}
</td>''')
    return "".join(cells)
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
        cells.append(f'<td class="{cls}" width="33.333%" align="center" valign="middle" style="padding:16px 12px;color:#17372d;{border}"><div style="font-size:{size};line-height:29px;font-weight:700">{value}</div><div style="font-size:11px;line-height:17px;color:#6f766f;margin-top:3px">{label}</div></td>')

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

def item_list(items: object, accent: str) -> str:
    rows: list[str] = []
    for item in list(items or [])[:MAX_LIST_ITEMS]:
        title = esc(item.get("title") if isinstance(item, dict) else item)
        detail = esc(item.get("detail") if isinstance(item, dict) else "")
        detail_html = f'<div style="font-size:12px;line-height:18px;color:#7f847f;margin-top:3px">{detail}</div>' if detail else ""
        rows.append(f'<div style="border-top:1px solid #e1d9cb;margin-top:14px;padding-top:14px"><div style="font-size:15px;line-height:22px;font-weight:700;color:#17372d"><span style="color:{accent}">&#9679;</span>&nbsp;&nbsp;{title}</div>{detail_html}</div>')
    return "".join(rows) if rows else '<div style="border-top:1px solid #e1d9cb;margin-top:14px;padding-top:14px;font-size:14px;line-height:21px;color:#7f847f">אין פריטים להצגה.</div>'

def stat_cells(stats: object) -> str:
    rows = list(stats or [])[:3]
    while len(rows) < 3:
        rows.append({"value":"אין נתון","label":""})
    cells: list[str] = []
    for idx, stat in enumerate(rows):
        cls = "vf-stat vf-stat-last" if idx == 2 else "vf-stat"
        border = "" if idx == 2 else "border-left:1px solid #ddd5c7;"
        cells.append(f'<td class="{cls}" width="33.333%" align="center" style="padding:23px 10px;color:#17372d;{border}"><div style="font-size:34px;line-height:39px;font-weight:700">{esc(stat.get("value",""))}</div><div style="font-size:13px;line-height:20px;color:#6f766f;margin-top:4px">{esc(stat.get("label",""))}</div></td>')
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
    footer_alt = esc((data.get("footer") or {}).get("image", {}).get("alt") or DECOR["footer"][1])
    instagram_html, instagram_note = instagram_metrics(data.get('instagram'))
    values = {
        "email_title": esc(data.get("email_title") or "Velvet Factory - Morning Brief"),
        "preheader": esc(data.get("preheader") or ""),
        "date_label": esc(data["date_label"]),
        "greeting": esc(data["greeting"]),
        "daily_summary": esc(data["daily_summary"]),
        "top_image_url": top_url, "top_image_alt": top_alt,
        "scheduled_posts_html": post_cards(data.get("scheduled_posts"), allow_local),
        "instagram_metrics_html": instagram_html,
        "instagram_note": instagram_note,
        "story_title": esc(data["story"]["title"]), "story_body": esc(data["story"]["body"]),
        "story_image_url": story_url, "story_image_alt": story_alt,
        "morning_line": esc(data["morning_line"]["text"]),
        "morning_line_note": esc(data["morning_line"].get("note") or ""),
        "attention_html": item_list(data.get("attention"), "#a85c44"),
        "progress_html": item_list(data.get("progress"), "#4b8a64"),
        "radar_image_url": radar_url, "radar_image_alt": radar_alt,
        "radar_title": esc(data["radar"]["title"]), "radar_text": esc(data["radar"]["text"]),
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
        "attention":[{"title":"החלטה אחת","detail":"פירוט"}],
        "progress":[{"title":"משהו התקדם","detail":"פירוט"}],
        "radar":{"title":"על הרדאר","text":"משהו מתקרב","image":{}},
        "stats":[{"value":"1","label":"מתוזמן"},{"value":"2","label":"פעיל"},{"value":"3","label":"פתוח"}],
        "footer":{"quote":"Same, brighter tomorrow.","note":"Velvet Factory","image":{}},
    }
    out = render(fixture)
    for token in ("MORNING EDITION","בקרוב בפיד","Instagram","81","מעורבות בפוסט האחרון","Reach / חשיפות: אין נתון Insights מאומת",'src="cid:morning-top.jpg"','class="vf-week-day"',"09:00","12:00","#15352b"):
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
    print("OK Morning Green v3.1 · RTL · responsive · Outlook-safe · cid/https")

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
