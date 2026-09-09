# ביקורת פיד קיים — @velvets_cloud

נעילה 8.9.2026 — Christian.  
מושב: צמיחה. לא מוחקים אוטומטית. לא משנים URL/live בלי כלי אמיתי.

## נקודת ייחוס איכות

| פריטים | סטטוס |
|---|---|
| פוסטים #1–#2 | **quality reference** (G001 / G002) — קצב, פשטות, צילום אמיתי, מיתוג |
| פוסט #3 ואילך | **REVIEW_REQUIRED** |

לא להעתיק את #1–#2 אחד לאחד. לא corporate cards. לא להעמיס טקסט.

## סיווג לכל פריט מהשלישי ואילך

| קוד | משמעות |
|---|---|
| A KEEP | נשאר |
| B EDIT_CAPTION | להכין תיקון כיתוב |
| C REPLACE_COVER_IF_PLATFORM_ALLOWS | כיסוי בלבד אם הפלטפורמה מאפשרת |
| D PREPARE_REVISED_VERSION | נגזרת חדשה במשרד |
| E ARCHIVE_CANDIDATE | מועמד לארכיון — **ORANGE/RED** לפי RISK |
| F REPUBLISH_CANDIDATE | מועמד לפרסום מחדש אחרי ארכיון |

## כללי WhatsApp leakage

- WhatsApp רק בכיתוב → `EDIT_CAPTION` (הכן תיקון).
- WhatsApp מוטמע במדיה → לא להעמיד פנים שהמדיה הוחלפה. הכן derivative בלי WhatsApp וסמן `revised-media-ready` / `archive-or-republish-decision`.
- אין מחיקה/ארכיון live בלי אישור לפי RISK (בדרך כלל RED/ORANGE).
- אין לטעון שנערך עד confirmation מהפלטפורמה.

## מצב גישה

אם אין כלי IG חי: `awaiting-live-audit` — מכינים מתוך ראיות ריפו/מדיה.

## כלים

אחרי חיבור MCP: `audit_public_cta` / `audit_profile_cta` (read-only).  
עריכת כיתוב/ביו דרך Graph = `unsupported_by_official_graph` — ראו `packages/vfigos/GRAPH-MUTATIONS.md`.  
אין מחיקה/ארכיון אוטומטי להיסטוריה בגלל CTA ישן.

## אחסון

[`data/feed-audit.json`](data/feed-audit.json)

## G004

זהות עובדתית: **מחזיק טבעות לזמן אימון** — לא משקולת/kettlebell workout weight.  
כל claim לוח על G004 = `scheduled` / `scheduledCandidate` — **לא** live.
