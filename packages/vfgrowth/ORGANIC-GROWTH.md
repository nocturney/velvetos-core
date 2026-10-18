# מפעל תוכן אורגני — Control Plane על vfgrowth

מושב: **צמיחה**. לא פק חדש. חוקה: `constitution/ORGANIC_GROWTH.md`.  
שער: `GATE.md` · האשטגים: `HASHTAGS.md` · קהילה: `COMMUNITY.md`.  
רצפה: `vfprod/PRINT-DONE.md`. בריף: `vfbriefux/hq/GROWTH-BRIEF.md`.

## מה זה

מערכת **ייצור טיוטות + readiness event-driven + handoff ל־publication policy**.
לא מפרסמת ישירות ל־`@velvets_cloud`: live publish הוא action נפרד של `vfigos` ורק אחרי `policy_id: instagram.publish`, exact-final gates, receipt ו־live verification. לא שולחת DM. לא סוגרת וואטסאפ.

עדיפות ספרינט תוכן (Control Plane — לא תור מקביל):
1. `ready_for_finished_content` · 2. `print.done` עם מדיה · 3. מאושר שמחכה למשבצת · 4. מדיה חדשה מקליטה · 5. רק אז רעיונות חדשים.  
CLI: `python3 scripts/vf_control_plane.py followups` · מפה: `office/control-plane.json`.

```
print.done (Edge / מפעיל)
        → Media Capture (איכות / חסר=חסר)
        → Content Factory (Reel/Story לפי content grid)
        → exact-final PREFLIGHT + EDIT-GATE
        → policy_checked
        → ALLOW + standingAuthorization → authorized_for_tool_publish → vfigos → published_verified
           OR REQUIRE_OWNER_APPROVAL → pending_human_approval → approved_for_manual_posting (legacy/manual branch)
        → readiness pack לפי צורך/אירוע; Morning Brief צורך אותו רק אם מופעל ורלוונטי
        → Insights מאומתים + orders.json
        → learning/recommendation
```

## מסלולי Reel (למשבצת לוח, לא כל יום חול)

| סוג | מקור | מטרה |
|---|---|---|
| Proof of Build | `print.done` / עבודה אמיתית | אמון |
| Material Lab | מבחן חומר מאושר | סמכות |
| Problem → Solution | צורך מתועד | לידים |
| Design Process | CAD/סלייס אמיתי | סטודיו לא «מדפסת ביתית» |
| Community Result | סקר מאתמול + מבחן רצפה | «אתם בחרתם—בדקנו» |

לוח קבוע: `CALENDAR.md` — ריל א׳/ג׳ 16:00 בלבד. **אין ריל כל יום עבודה.**

סדר ההחלטה של שער הריל (`vf_organic_growth.py brief`):

1. `print.done` / כרטיס עם נתיב מדיה → `quality_checked` (כמו קודם; עדיין PREFLIGHT לפני שיבוץ).
2. אחרת, וידאו שמיש ב־`packages/vfmedia/catalog.json` → `candidates_ready`: 2–3 מועמדים (וידאו בלבד, `status=source`, לא מפורסם, בלי נגזרות, בלי כפילויות; חדש לפני ישן; סדרה שכבר פורסמה בסוף; משך רק אם הקטלוג מחזיק אותו). לכל מועמד: מזהה קטלוג + שם קובץ, למה נבחר, ומתכון עריכה בכלי פעיל קיים — `scripts/vf_video_edit.py` → `scripts/vf_hyperframes.py`. מועמד הוא **הצעה, לא ריל**: בחירת/עריכת routine יכולה להיות office-owned, אבל completion דורש exact-final PREFLIGHT + EDIT-GATE ואז `policy_id: instagram.publish`. הסקריפט הזה לא מפרסם ולא יוצר authorization; אין רינדור/פרסום עוקף-policy ואין טענת מוצר בלי `productLink`.
3. חסר גלם איכותי וגם אין וידאו שמיש בקטלוג → `blocked_no_media` — לא ממציאים Reel. שורת בריף:  
«אין Reel איכותי אוטומטי להיום. נדרשים 15 שניות צילום ידני: קלוז־אפ של המוצר ביד + בדיקת התאמה.»

רגרסיה: `scripts/check-reel-candidates.py` (קטלוג fixture: 0 וידאו → `blocked_no_media`; 2 וידאו → `candidates_ready` עם מתכון שמצביע על כלי פעיל).

## Story 20:30 (א׳–ה׳)

2–3 שקופיות: ויזואל מחר במעבדה · סקר · CTA רך להודעת Instagram (`PUBLIC_CURRENT_CTA`).  
שלושה ניסוחים מדורגים לפי ביצועים **מאומתים** בלבד. מצב ההכנה אינו authorization: exact package עובר `policy_id: instagram.publish`; `pending_human_approval` קיים רק אם policy דורש אדם.

## תעודת מוצר

תבנית: `templates/engineering-card.md`.  
חום / חוזק / נשיאה — רק מ־`vfprod/CLAIMS.md` או מבחן מתועד. אחרת משמיטים.

## נתונים

| קובץ | תפקיד |
|---|---|
| `data/approval-queue.json` | תור אישור |
| `data/content_events.jsonl` | אירועי תוכן על דיסק |
| `data/hashtag-library.json` | אשכולות + `hashtag_set_id` |
| `data/poll-library.json` | סקרים לפי יכולת רצפה |
| `data/growth-brief.json` | Decision Pack אחרי `vf_organic_growth.py brief --write` |

## CLI

`python3 scripts/vf_organic_growth.py brief --write`

## נעול

אין direct/bypass Publish מכאן; publication עובר רק דרך `vfigos` + policy/receipt/live verification. אין אוטו־DM. אין בוסט. אין ₪ / Insights מומצאים.
תיוג משתתפים: משפט «אתם בחרתם—הנה התוצאה» — לא תיוג בלי opt-in.
