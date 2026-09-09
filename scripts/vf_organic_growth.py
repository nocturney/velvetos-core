#!/usr/bin/env python3
"""Organic Growth Control Plane — drafts + 07:00 decision pack. No publish. No DM."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Jerusalem")
GROWTH = ROOT / "packages" / "vfgrowth"
QUEUE = GROWTH / "data" / "approval-queue.json"
EVENTS = GROWTH / "data" / "content_events.jsonl"
HASHTAGS = GROWTH / "data" / "hashtag-library.json"
POLLS = GROWTH / "data" / "poll-library.json"
BRIEF_OUT = GROWTH / "data" / "growth-brief.json"
PRINT_EVENTS = ROOT / "packages" / "vfprod" / "data" / "print-events.jsonl"
CARDS = ROOT / "packages" / "vfprod" / "hq" / "cards"
ORDERS = ROOT / "packages" / "vfsales" / "data" / "orders.json"
ATTR = ROOT / "packages" / "vfinsights" / "data" / "attribution.json"
INSIGHTS_CSV = ROOT / "packages" / "vfinsights" / "data" / "posts.csv"
POLICY = ROOT / "constitution" / "ORGANIC_GROWTH.md"

GATES_FORWARD = {
    "draft": {"quality_checked", "blocked_no_media"},
    "quality_checked": {"policy_checked", "blocked_policy"},
    "policy_checked": {"pending_human_approval"},
    "pending_human_approval": {"approved_for_manual_posting", "edit", "rejected"},
    "approved_for_manual_posting": {"posted_manually"},
    "posted_manually": {"performance_imported"},
    "performance_imported": {"attributed"},
    "attributed": {"learned"},
    "edit": {"draft"},
    "blocked_no_media": {"draft"},
    "blocked_policy": {"draft"},
    "rejected": set(),
    "learned": set(),
}

FORBIDDEN_COPY = (
    "send_dm",
    "boost now",
    "follow-back",
    "wa.me",
    "050-2517000",
    "הזמנות בוואטסאפ",
    "דברו איתנו בוואטסאפ",
)
CTA_OK = "הודעה"
CTA_OK_ALT = ("אינסטגרם", "שלחו לנו הודעה", "לפרטים — שלחו", "בהודעות")


def fail(msg: str) -> int:
    print(f"FAIL {msg}", file=sys.stderr)
    return 1


def load_json(path: Path, default):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        rows.append(json.loads(raw))
    return rows


def has_media(payload: dict) -> bool:
    media = payload.get("media") or {}
    path = (payload.get("mediaPath") or media.get("timelapse_path") or media.get("hero_frame_path") or "").strip()
    return bool(path)


def print_payloads() -> list[dict]:
    rows = []
    for ev in load_jsonl(PRINT_EVENTS):
        payload = dict(ev.get("payload") or {})
        payload["_source"] = "print-events.jsonl"
        rows.append(payload)
    if CARDS.is_dir():
        for path in sorted(CARDS.glob("*.md")):
            if path.name in {"README.md", "PRINT-CARD-TEMPLATE.md"}:
                continue
            text = path.read_text(encoding="utf-8")
            rows.append(
                {
                    "_source": str(path.relative_to(ROOT)),
                    "mediaPath": "yes" if "timelapse" in text.lower() and "חסר" not in text else "",
                    "note": path.stem,
                }
            )
    return rows


def media_quality_line(payloads: list[dict]) -> tuple[str, str]:
    if any(has_media(p) for p in payloads):
        return "quality_checked", "יש נתיב מדיה בכרטיס/אירוע — עדיין דורש PREFLIGHT לפני שיבוץ"
    return (
        "blocked_no_media",
        "אין Reel איכותי אוטומטי להיום. נדרשים 15 שניות צילום ידני: קלוז־אפ של המוצר ביד + בדיקת התאמה.",
    )


def next_reel_slot(today: datetime) -> str:
    # CALENDAR.md: Sun=0 in this office notes; Python weekday Mon=0.
    # Standing feed reels: Sunday 16:00 and Tuesday 16:00.
    wd = today.weekday()  # Mon=0 … Sun=6
    if wd == 6:
        return "היום 16:00 · ריל ראשון בשבוע"
    if wd == 1:
        return "היום 16:00 · ריל שני בשבוע"
    if wd in (0, 2, 3, 4):
        return "אין משבצת ריל היום (לוח: א׳/ג׳ 16:00 בלבד)"
    return "אין פיד בשישי–שבת"


def story_slot(today: datetime) -> str:
    wd = today.weekday()
    if wd >= 5:
        return "אין סטוריז בשישי–שבת"
    return "היום 20:30 · סטוריז א׳–ה׳"


def g004_stories_draft_contests_slot(today: date) -> bool:
    """True when a same-day G004 stories draft targets the 20:30 slot (no schedule)."""
    drafts = GROWTH / "drafts"
    if not drafts.is_dir():
        return False
    needle = f"NEXT-{today.isoformat()}-G004"
    for path in drafts.glob(f"{needle}*.md"):
        text = path.read_text(encoding="utf-8")
        if "20:30" in text and "G004" in text:
            return True
    return False


def cmd_brief(args: argparse.Namespace) -> int:
    now = datetime.now(TZ)
    today = now.date().isoformat()
    today_d = now.date()
    payloads = print_payloads()
    gate, media_line = media_quality_line(payloads)
    queue = load_json(QUEUE, {"items": []})
    items = queue.get("items") or []
    polls = load_json(POLLS, {"polls": []})
    poll = (polls.get("polls") or [{}])[0]
    tags = load_json(HASHTAGS, {"sets": []})
    tag_set = (tags.get("sets") or [{}])[0]
    orders = load_json(ORDERS, {"orders": []})
    n_orders = len(orders.get("orders") or [])
    story_items = [i for i in items if i.get("format") == "story"]
    contested = g004_stories_draft_contests_slot(today_d)
    story_gate = (
        "slot_contested_pending_human_choice"
        if contested
        else (story_items[0].get("gate") if story_items else "pending_human_approval")
    )
    weekday_he = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"][now.weekday()]
    pack = {
        "date": today,
        "generatedAt": now.isoformat(timespec="seconds"),
        "component_state": "Idle" if gate != "blocked_no_media" else "Blocked",
        "goal": "פניות B2B בדרום עבור אב-טיפוס / חלקים מותאמים.",
        "locks": [
            "no-autopost",
            "no-auto-dm",
            "no-boost",
            "no-invented-insights",
            "no-invented-ils",
            "no-schedule-from-hq",
        ],
        "weekdayNote": f"{today} = {weekday_he} (Asia/Jerusalem)",
        "reel": {
            "slot": next_reel_slot(now),
            "gate": gate,
            "topic": "חסר — אין print.done עם מדיה",
            "asset": "חסר",
            "hook": "חסר",
            "cta": "לפרטים והזמנות — שלחו לנו הודעה כאן באינסטגרם",
            "geotag": "שדרות" if gate != "blocked_no_media" else "חסר",
            "hashtag_set_id": tag_set.get("hashtag_set_id") or "local_b2b_v1",
            "actions": ["אישור", "עריכה", "דחייה"],
            "no_media_line": media_line,
        },
        "story": {
            "slot": story_slot(now),
            "gate": story_gate,
            "slotStatus": "תפוסה להצעות · לא פנויה" if contested else "ממתין לאישור",
            "poll_id": poll.get("poll_id"),
            "question": poll.get("question") or "חסר סקר בספרייה",
            "options": poll.get("options") or [],
            "cta": "לפרטים — שלחו הודעה כאן באינסטגרם",
            "actions": ["אישור", "עריכה", "דחייה"],
            "note": (
                "אל תציגו את 20:30 כפנויה. שתי הצעות: סקר organic ↔ טיוטת G004. בלי Calendar create."
                if contested
                else "אישור ≠ פרסום · בלי תזמון מ־HQ"
            ),
        },
        "yesterday": {
            "insights": "אין ספירה",
            "whatsapp_leads": "אין ספירה" if not n_orders else "אין ספירה",
            "leading_format": "אין ספירה",
            "recommendation": (
                "פער סנכרון · orders.json ריק ≠ הוכחה שאין הזמנות"
                if n_orders == 0
                else "אין ספירה עד סנאפשוט + שורת orders.json"
            ),
        },
        "studio_tasks": [
            "למלא כרטיס print.done עם נתיב טיימלאפס אמיתי — בלי זה אין Reel.",
            (
                "לבחור בין סקר 20:30 לבין טיוטת G004 (משבצת לא פנויה) — לא מפרסם ולא משבץ מ־HQ."
                if contested
                else "לאשר או לדחות את סקר הערב בבריף (לא מפרסם)."
            ),
            "לא להציג חום/חוזק בלי vfprod/CLAIMS.md.",
        ],
        "print_events": len(payloads),
        "queue_count": len(items),
    }
    if contested:
        pack["story"]["conflict"] = {
            "proposals": [
                {"id": f"poll-{poll.get('poll_id') or 'unknown'}", "kind": "organic-growth-poll"},
                {
                    "id": "G004-stories",
                    "kind": "product-story-draft",
                    "source": f"packages/vfgrowth/drafts/NEXT-{today}-G004-stories.md",
                },
            ],
            "resolution": "בחירת אדם בבריף — בלי Calendar create · בלי הזזת שיבוץ נעול",
        }
    text = (
        f"VELVET ORGANIC GROWTH BRIEF — 07:00\n"
        f"יום: {pack['weekdayNote']}\n"
        f"יעד היום: {pack['goal']}\n"
        f"1. REEL · {pack['reel']['slot']} · gate={pack['reel']['gate']}\n"
        f"{pack['reel']['no_media_line']}\n"
        f"CTA: {pack['reel']['cta']}\n"
        f"סט האשטגים: {pack['reel']['hashtag_set_id']}\n"
        f"פעולה: [אישור] [עריכה] [דחייה] — אישור ≠ פרסום\n"
        f"2. STORY · {pack['story']['slot']} · {pack['story'].get('slotStatus')} · gate={pack['story']['gate']}\n"
        f"שאלה: {pack['story']['question']}\n"
        f"אפשרויות: {' / '.join(pack['story']['options'])}\n"
        f"{pack['story'].get('note')}\n"
        f"פעולה: [אישור] [עריכה] [דחייה]\n"
        f"3. אתמול: Insights {pack['yesterday']['insights']} · הזמנות {pack['yesterday']['recommendation']}\n"
        f"4. סטודיו: {'; '.join(pack['studio_tasks'])}\n"
        "אין Publish / אין אוטו-DM / אין ₪ מומצא."
    )
    print(text)
    if args.write:
        BRIEF_OUT.parent.mkdir(parents=True, exist_ok=True)
        BRIEF_OUT.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {BRIEF_OUT.relative_to(ROOT)}")
    return 0


def cmd_policy(_args: argparse.Namespace) -> int:
    if not POLICY.is_file():
        return fail("missing constitution/ORGANIC_GROWTH.md")
    policy = POLICY.read_text(encoding="utf-8")
    for needle in (
        "approved_for_manual_posting",
        "posted_manually",
        "אוטומטי",
        "050-2517000",
        "print.done",
    ):
        if needle not in policy:
            return fail(f"ORGANIC_GROWTH.md missing {needle!r}")
    queue = load_json(QUEUE, {"items": []})
    for item in queue.get("items") or []:
        gate = item.get("gate") or "draft"
        if gate == "posted_manually" and not item.get("human_marked"):
            return fail(f"{item.get('content_id')}: posted_manually without human_marked")
        cta = str(item.get("cta") or "")
        if item.get("format") in {"reel", "story"}:
            ok = CTA_OK in cta or any(a in cta for a in CTA_OK_ALT)
            if not ok:
                return fail(f"{item.get('content_id')}: story/reel missing Instagram-message CTA")
            for bad in ("050-2517000", "wa.me", "וואטסאפ", "WhatsApp"):
                if bad in cta:
                    return fail(f"{item.get('content_id')}: public CTA must not include {bad!r}")
        blob = json.dumps(item, ensure_ascii=False)
        for bad in FORBIDDEN_COPY:
            if bad in blob and "לא" not in blob and "disabled" not in blob.lower():
                return fail(f"{item.get('content_id')}: forbidden copy {bad!r}")
        tags = item.get("tags") or []
        if tags and not (8 <= len(tags) <= 15):
            return fail(f"{item.get('content_id')}: hashtag count {len(tags)} not in 8-15")
    lib = load_json(HASHTAGS, {})
    for s in lib.get("sets") or []:
        n = len(s.get("tags") or [])
        if not (8 <= n <= 15):
            return fail(f"{s.get('hashtag_set_id')}: tag count {n} not in 8-15")
    orders = load_json(ORDERS, {"orders": []})
    for row in orders.get("orders") or []:
        for key in ("estimated_value_ils", "closed_value_ils"):
            val = row.get(key)
            if val not in (None, "X ₪"):
                return fail(f"{row.get('order_id')}: {key} must be null until verified (got {val!r})")
    print("OK policy · no autopost · queue gates hold · no invented ILS")
    return 0


def cmd_queue(_args: argparse.Namespace) -> int:
    queue = load_json(QUEUE, {"items": []})
    items = queue.get("items") or []
    if not items:
        print("תור אישור: ריק")
        return 0
    print("content_id | format | gate | human_marked")
    for item in items:
        print(
            f"{item.get('content_id')} | {item.get('format')} | "
            f"{item.get('gate')} | {item.get('human_marked')}"
        )
    return 0


def cmd_score(_args: argparse.Namespace) -> int:
    measured = False
    if INSIGHTS_CSV.is_file():
        text = INSIGHTS_CSV.read_text(encoding="utf-8")
        # Header + at least one numeric reach
        for line in text.splitlines()[1:]:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) > 3 and parts[3].replace(".", "", 1).isdigit():
                measured = True
                break
    attr = load_json(ATTR, {"attributions": []})
    orders = load_json(ORDERS, {"orders": []})
    if not measured and not attr.get("attributions") and not orders.get("orders"):
        print("Content Score: אין ספירה")
        return 0
    print("Content Score: אין ספירה — חסרים מדדים מיובאים מלאים (לא מזינים 0 מזויף)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="VelvetOS organic growth control plane")
    sub = parser.add_subparsers(dest="cmd", required=True)
    brief = sub.add_parser("brief", help="07:00 decision pack")
    brief.add_argument("--write", action="store_true")
    brief.set_defaults(func=cmd_brief)
    sub.add_parser("policy", help="policy gate over queue + orders").set_defaults(func=cmd_policy)
    sub.add_parser("queue", help="list approval queue").set_defaults(func=cmd_queue)
    sub.add_parser("score", help="content score or אין ספירה").set_defaults(func=cmd_score)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
