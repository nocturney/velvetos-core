# ביקורת פיד קיים — @velvets_cloud · RESET OVERRIDE

עדכון סמכות: 14.9.2026 · Christian.  
מושב: צמיחה. `CONTENT-RESET-2026-09-10.md` + owner override 2026-09-14 גוברים על החלטות Archive/KEEP ישנות במסמך זה.

## מצב חי מאומת · 2026-09-14

כלי Instagram החי מדווח על **3 Reels** בלבד. Christian קבע במפורש: **לא למחוק ולא לארכב אותם**.

| Reel | media id | החלטה |
|---|---|---|
| `DdAPhozlNe2` | `17873372004572489` | `KEEP_LIVE_BASELINE`; נדרש רק תיקון ידני לקפטן הקיים שמכיל WhatsApp/טלפון |
| `DcvuJLxCJgU` | `18113247517791419` | `KEEP_LIVE_BASELINE`; ללא שינוי |
| `DcqkjOLlYVX` | `18107769701162221` | `KEEP_LIVE_BASELINE`; ללא שינוי |

אין archive/delete transition. אין דרישה לייצר פיד ריק לפני תוכן חדש. ה־3 הם baseline חי ללמידה, novelty/fatigue והשוואת ביצועים.

חמשת הפריטים האחרים מתוך snapshot ה־8 מ־10.9 כבר אינם live. הם נשמרים ב־audit כ־`HISTORICAL_NOT_LIVE`; אין לשחזר אותם בגלל reset ואין להתייחס אליהם כ־archive pending.

## Retroactive QA policy

סטנדרטים יצירתיים חדשים חלים על תוכן חדש ועל נכס שנפתח מחדש לעריכה. הם **לא** סיבה לשכתב/לעצב מחדש את שלושת הרילים החיים בדיעבד.

מתקנים retained live media רק אם קיימת חריגה פעילה מהמדיניות הנוכחית, בעיית אמת/פרטיות/בטיחות או דרישת פלטפורמה. כרגע החריגה היחידה שנמצאה היא שורת WhatsApp/טלפון בקפטן `DdAPhozlNe2`. כלי Graph המחובר אינו מציע existing-caption edit, לכן זה `human_required` ממוקד — בלי archive/delete.

## מה נשמר מהביקורת ההיסטורית

מקור הנתונים המפורט: [`data/feed-audit.json`](data/feed-audit.json). הוא snapshot היסטורי, לא רשימת פעולות.

- Reels של proof/process/reveal הראו Reach עדיף במדגם הקטן, אבל המרה לפעולה הייתה חלשה.
- Product-story קונקרטי הראה יעילות אינטראקציה טובה יותר מקרוסלות סטודיו גנריות.
- כפילות/חזרתיות היא failure של novelty/fatigue.
- WhatsApp / `050-2517000` / `wa.me` אינם CTA ציבורי לפי `PUBLIC_CTA.md`.
- G004 נשמר בזהות העובדתית: **מחזיק טבעות לזמן אימון** — לא משקולת / kettlebell workout weight. הקריאייטיב הישן שלו STALE ואינו approval לשימוש חדש.
- שום cover/caption/preflight היסטורי אינו עובר בירושה לארטיפקט חדש.

## Launch authority

שלישיית העבודה נמצאת ב־`RESET-LAUNCH-TRIO.md`:
- VF-R001 — Reel movement proof.
- VF-R002 — Dragon detail carousel.
- VF-R003 — Metallic helmet reveal Reel.

Readiness נקבע רק לפי ה־preflight העדכני של כל פריט וה־exact-final package; אין להסתמך על label ישן ב־manifest/ledger.

## Profile state · live verified 2026-09-14

הביו החי הוא:

`הדפסות תלת־ממד בעיצוב ייחודי`  
`מוצרים מוכנים • מודלים בהתאמה אישית`  
`[שורה ישנה להסרה ידנית]`  
`📍 איסוף משדרות`

אין בו WhatsApp/טלפון ולכן אין כרגע profile CTA violation. הוא אינו כולל CTA מפורש להודעות Instagram; זה הבדל מה־desired profile, **לא blocker**. Graph write לביו אינו זמין בכלי המחובר.

## כלל סיום

ה־3 live Reels הם baseline, לא template. תוכן חדש עובר: real evidence → Media Librarian → Creative Director → render/edit + audio → Visible Text/Hebrew Copy → Brand Guardian exact-final → Rubric/Contract/applicable policy → digest-bound execution receipts → publish → live verify → performance learning.