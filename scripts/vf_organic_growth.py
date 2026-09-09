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


def g004_ready_for_slot() -> bool:
    """True only when G004 preflight gate section is עבור (not נכשל-סגור)."""
    path = GROWTH / "preflight" / "G004.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if "## שער" in text:
        gate = text.split("## שער", 1)[1][:600]
        if "נכשל-סגור" in gate:
            return False
        if "**עבור**" in gate or "\nעבור\n" in f"\n{gate}\n":
            return True
        return False
    # No gate section → not ready
    return False


def next_stories_slot_after(now: datetime) -> dict:
    """Next A–Th 20:30 Asia/Jerusalem stories slot at or after now (no schedule)."""
    t = now
    for _ in range(8):
        candidate = t.replace(hour=20, minute=30, second=0, microsecond=0)
        if candidate.weekday() < 5 and candidate >= now:
            he = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"][candidate.weekday()]
            return {
                "when": candidate.isoformat(timespec="minutes"),
                "whenHe": f"{he} {candidate.date().isoformat()} 20:30 Asia/Jerusalem",
            }
        t = (t + __import__("datetime").timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return {"when": "חסר", "whenHe": "חסר משבצת"}


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
    g004_ready = g004_ready_for_slot()
    contested = g004_stories_draft_contests_slot(today_d) and not g004_ready
    slot_meta = next_stories_slot_after(now)
    # Single recommendation: prefer G004 when edit/preflight ready; else poll if still before slot
    if g004_ready:
        slot_rec = {
            "choice": "G004",
            "when": slot_meta["when"],
            "whenHe": slot_meta["whenHe"],
            "reasonShort": "מוצר מוכן לעריכה+פריפלייט · פרנסה מסיפור-מוצר",
            "reason": (
                "G004 מחזיק-טבעות עבר EDIT-GATE/Canva + preflight עבור; "
                "משרת הצעת מוצר/פנייה. סקר PETG/Nylon נדחה למשבצת סטוריז פנויה אחרת — "
                "לא שני שיבוצים על 20:30. בלי Calendar create · G003 הנעול לא זז."
            ),
            "deferred": {"id": f"poll-{poll.get('poll_id') or 'petg_vs_nylon'}", "to": "משבצת סטוריז פנויה אחרת"},
        }
        story_gate = "recommended_g004_pending_human_post"
        slot_status = f"המלצה יחידה · G004 · {slot_meta['whenHe']}"
        story_note = "בחירה אחת: G004. סקר לא משובץ במקביל. אישור ≠ פרסום · בלי תזמון מ־HQ."
        studio_story_task = f"לאשר ידנית G004 ל־{slot_meta['whenHe']} (לא מפרסם מ־HQ)."
    elif now.weekday() < 5 and (
        now.hour < 20 or (now.hour == 20 and now.minute < 30)
    ):
        slot_rec = {
            "choice": "poll",
            "when": slot_meta["when"],
            "whenHe": slot_meta["whenHe"],
            "reasonShort": "G004 עדיין חסום עריכה/preflight · סקר קל יותר הערב",
            "reason": (
                "G004 עדיין לא עבור בשערי עריכה — לא ממליצים לשבץ מוצר לא מוכן. "
                f"סקר organic `{poll.get('poll_id') or 'petg_vs_nylon'}` למשבצת {slot_meta['whenHe']}. "
                "בלי Calendar create."
            ),
            "deferred": {"id": "G004-stories", "to": "אחרי EDIT-GATE+PREFLIGHT עבור"},
        }
        story_gate = "recommended_poll_pending_human_post"
        slot_status = f"המלצה יחידה · סקר · {slot_meta['whenHe']}"
        story_note = "בחירה אחת: סקר. G004 נדחה עד שער עבור. אישור ≠ פרסום."
        studio_story_task = f"לאשר או לדחות סקר ל־{slot_meta['whenHe']} (לא מפרסם)."
    else:
        slot_rec = {
            "choice": "poll" if not g004_ready else "G004",
            "when": slot_meta["when"],
            "whenHe": slot_meta["whenHe"],
            "reasonShort": "20:30 היום חלף · משבצת הבאה",
            "reason": f"20:30 היום חלף. משבצת סטוריז הבאה: {slot_meta['whenHe']}. בלי תזמון מ־HQ.",
        }
        story_gate = "next_slot_recommendation"
        slot_status = f"המלצה · {slot_meta['whenHe']}"
        story_note = "המשבצת להיום חלפה — הצעה למשבצת הבאה בלבד."
        studio_story_task = f"לתכנן ידנית למשבצת {slot_meta['whenHe']} — לא Calendar מ־HQ."

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
        "slotRecommendation": slot_rec,
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
            "slotStatus": slot_status,
            "recommendation": slot_rec,
            "poll_id": poll.get("poll_id"),
            "question": poll.get("question") or "חסר סקר בספרייה",
            "options": poll.get("options") or [],
            "cta": "לפרטים — שלחו הודעה כאן באינסטגרם",
            "actions": ["אישור", "עריכה", "דחייה"],
            "note": story_note,
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
            studio_story_task,
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
            "resolution": "אם G004 לא מוכן — המלצה יחידה לסקר; אחרת המלצה יחידה ל-G004",
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
        f"2. STORY · {pack['story']['slotStatus']} · gate={pack['story']['gate']}\n"
        f"המלצה יחידה: {slot_rec['choice']} · {slot_rec['whenHe']}\n"
        f"נימוק: {slot_rec['reason']}\n"
        f"סקר (לא שיבוץ מקביל): {pack['story']['question']} · {' / '.join(pack['story']['options'])}\n"
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
