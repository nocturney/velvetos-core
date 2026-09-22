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
MAX_POSTS = 4
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
    rows = list(posts or [])[:MAX_POSTS]
    if not rows:
        return '<td style="padding:16px 10px;color:#6d746e;font-size:14px">אין כרגע פרסום מתוזמן או מדיה מאושרת להצגה.</td>'
    width = {1:"100%",2:"50%",3:"33.333%",4:"25%"}[len(rows)]
    image_width = {1:820,2:410,3:274,4:205}[len(rows)]
    cells: list[str] = []
    for post in rows:
        img = safe_image(post.get("image_url"), allow_local)
        alt = esc(post.get("image_alt") or "תצוגה מקדימה של פוסט")
        date = esc(post.get("date_label") or "")
        time_raw = str(post.get("time_label") or "").strip()
        time = esc(time_raw)
        kind = esc(post.get("type_label") or "")
        status = esc(post.get("status_label") or "")
        is_clock = bool(re.fullmatch(r"[0-2]?\d:[0-5]\d", time_raw))
        direction, align = ("ltr","left") if is_clock else ("rtl","right")
        badge = (f'<span style="display:inline-block;background:#e8dfcb;color:#725b35;border-radius:999px;padding:4px 8px;font-size:10px;line-height:14px;font-weight:700">{status}</span>') if status else ""
        cells.append(f'''<td class="vf-post" width="{width}" valign="top" style="padding:0 6px 8px">
<table role="presentation" width="100%" bgcolor="#fffdf8" style="background:#fffdf8;border-radius:17px;overflow:hidden">
<tr><td><img src="{img}" alt="{alt}" width="{image_width}" style="width:100%;height:auto"></td></tr>
<tr><td style="padding:11px 12px 4px;color:#9b7840;font-size:12px;line-height:17px;font-weight:700">{date}</td></tr>
<tr><td dir="{direction}" align="{align}" style="padding:0 12px;color:#17372d;font-size:21px;line-height:26px;font-weight:700">{time}</td></tr>
<tr><td style="padding:4px 12px 12px;color:#6f766f;font-size:12px;line-height:18px">{kind}{('&nbsp;&nbsp;'+badge) if badge else ''}</td></tr>
</table></td>''')
    return "".join(cells)
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
    values = {
        "email_title": esc(data.get("email_title") or "Velvet Factory - Morning Brief"),
        "preheader": esc(data.get("preheader") or ""),
        "date_label": esc(data["date_label"]),
        "greeting": esc(data["greeting"]),
        "daily_summary": esc(data["daily_summary"]),
        "top_image_url": top_url, "top_image_alt": top_alt,
        "scheduled_posts_html": post_cards(data.get("scheduled_posts"), allow_local),
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
        "scheduled_posts":[{"image_url":"https://example.com/post.jpg","date_label":"היום","time_label":"19:30","type_label":"פוסט","status_label":"מתוזמן"}],
        "story":{"title":"הסיפור של היום","body":"פרטים נוחים לקריאה","image":{}},
        "morning_line":{"text":"פחות ז׳רגון, יותר הקשר.","note":"בדיקה"},
        "attention":[{"title":"החלטה אחת","detail":"פירוט"}],
        "progress":[{"title":"משהו התקדם","detail":"פירוט"}],
        "radar":{"title":"על הרדאר","text":"משהו מתקרב","image":{}},
        "stats":[{"value":"1","label":"מתוזמן"},{"value":"2","label":"פעיל"},{"value":"3","label":"פתוח"}],
        "footer":{"quote":"Same, brighter tomorrow.","note":"Velvet Factory","image":{}},
    }
    out = render(fixture)
    for token in ("MORNING EDITION","בקרוב באינסטגרם",'src="cid:morning-top.jpg"','dir="ltr"',"19:30","#15352b"):
        if token not in out:
            raise SystemExit(f"FAIL Morning Green missing {token!r}")
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
