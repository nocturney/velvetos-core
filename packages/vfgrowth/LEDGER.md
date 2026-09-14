# לדג׳ר צמיחה · GROWTH_LEDGER · RESET ACTIVE

מושב: **צמיחה**. מקור אמת למועמדי Feed/Reel/Story החדשים.  
סמכות: `CONTENT-RESET-2026-09-10.md` · לוח: `CALENDAR.md` · שלישיית פתיחה: `RESET-LAUNCH-TRIO.md`.

## מצב הפיד החי · owner lock 2026-09-14

Live Instagram verification: **3 Reels**. Christian קבע שהם נשארים בעמוד.

| permalink / media | פורמט | מצב פעיל | טיפול |
|---|---|---|---|
| `instagram.com/reel/DdAPhozlNe2/` · `17873372004572489` | Reel | `KEEP_LIVE_BASELINE` | להשאיר live. הקפטן החי עדיין מכיל WhatsApp/טלפון ולכן `CAPTION_POLICY_DEBT_MANUAL`; אין archive/delete |
| `instagram.com/reel/DcvuJLxCJgU/` · `18113247517791419` | Reel | `KEEP_LIVE_BASELINE` | להשאיר ללא שינוי |
| `instagram.com/reel/DcqkjOLlYVX/` · `18107769701162221` | Reel | `KEEP_LIVE_BASELINE` | להשאיר ללא שינוי |

**אין הוראת Archive/Delete לשלושת הרילים.** כלי Instagram המחובר אינו תומך בעריכת caption קיים; לכן תיקון ה־WhatsApp בריל `DdAPhozlNe2` הוא פעולה ידנית ממוקדת באפליקציה בלבד. הוא אינו תנאי למחיקת/ארכוב הריל.

חמשת הפריטים הנוספים שהיו live בזמן audit ב־10.9 אינם חיים כיום. הם נשמרים כ־`HISTORICAL_NOT_LIVE` בלבד:

| permalink | פורמט | מצב |
|---|---|---|
| `instagram.com/p/DdHidHYG4-p/` | Carousel | HISTORICAL_NOT_LIVE |
| `instagram.com/p/Dc1g1sJGzgq/` | Carousel | HISTORICAL_NOT_LIVE |
| `instagram.com/p/Dc0cKegEbxd/` | Carousel | HISTORICAL_NOT_LIVE |
| `instagram.com/p/Dci5EyuoWVJ/` | Image | HISTORICAL_NOT_LIVE |
| `instagram.com/p/Dci0aRzIO1F/` | Image | HISTORICAL_NOT_LIVE |

אין לשחזר או לפרסם אותם מחדש בגלל ה־reset.

## Historical identity map — audit only

הטבלה נשמרת עבור lineage/sensors/Insights. היא **לא** תור פרסום פעיל.

| מזהה היסטורי | ראיה/shortcode | מצב היסטורי | מצב נוכחי |
|---|---|---|---|
| **G001** | `DcqkjOLlYVX` | Reel #1 | `KEEP_LIVE_BASELINE` |
| **G002** | `DcvuJLxCJgU` | Reel #2 | `KEEP_LIVE_BASELINE` |
| **G005** | `Dc0cKegEbxd` | Carousel | `HISTORICAL_NOT_LIVE` |
| **G003** | `DdAPhozlNe2` · **SoccerBall** | היה `משובץ` היסטורית | `KEEP_LIVE_BASELINE` · reuse חדש עדיין **חסום** ללא qualification חדש |
| **G004** | **מחזיק** טבעות לזמן אימון | מועמד/פרסום היסטורי | stale · **חסום** מכל reuse אוטומטי |

## תור חדש · preflight הוא הסמכות ל־readiness

| מזהה | פורמט | Creative direction | מצב אמיתי |
|---|---|---|---|
| **VF-R001** | Reel | cover owner lock: `פה התנועה היא כל העניין` | **BLOCKED** — old final near-silent; stale showcase caption/cover; exact-final QA + execution receipts rerun required |
| **VF-R002** | Carousel | owner lock: `NO_TEXT` | **BLOCKED / REBUILD REQUIRED** — later Publish Gate v3 invalidated crop/resize-only derivative; needs real art direction from RAW while preserving exact dragon/Product Truth, then new hashes/receipts/QA |
| **VF-R003** | Reel | cover owner lock: `פה הזווית משנה הכול` | **BLOCKED** — old final has no audio stream; stale showcase caption/cover; exact-final QA + execution receipts rerun required |

ה־preflights המחייבים: `preflight/VF-R001.md`, `preflight/VF-R002.md`, `preflight/VF-R003.md`. אם manifest ישן סותר preflight מאוחר יותר — ה־preflight המאוחר וה־exact-final evidence גוברים עד reconciliation.

Blanket model-license/right-to-publish metadata **אינם blocker** ל־owner-captured showcase. Rights/privacy gate נשאר פעיל רק למדיה צד ג׳/UGC/פרטיות/מגבלה ידועה או מסלול commercial רלוונטי.

## ישן = STALE

הכרטיסים/טיוטות/כריכות/Preflight של G004/G006/G007/G008/G009/G010 וכל מועמד עתידי שנוצר לפני ה־reset אינם תור פעיל. אין להחזיר אותם ל־Calendar או Publish רק מפני שהם קיימים בריפו או ב־Canva.

## חוקי עבודה

- real evidence → Media Librarian → Creative Director → render/edit + audio strategy → Visible Text/Hebrew Copy → Brand Guardian exact-final → Content Rubric/Contract/applicable policy → package-bound execution receipts/preflight → publish → live verify → performance learning.
- Public CTA לפי `PUBLIC_CTA.md`; אין WhatsApp/טלפון/wa.me בקופי ציבורי חדש.
- אין ₪, claims, customer story, material property, deadline או Insights מומצאים.
- שינוי copy/media/render/audio מבטל receipts קודמים.
- Brand Guardian בודק novelty/fatigue מול ההיסטוריה וה־3 live baseline, אבל ההיסטוריה אינה template להעתקה.
- אין slot-filling. תוכן חלש או חסום = מדלגים.