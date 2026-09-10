# ביקורת פיד קיים — @velvets_cloud · RESET OVERRIDE

עדכון סמכות: 10.9.2026 · Christian.  
מושב: צמיחה. `CONTENT-RESET-2026-09-10.md` גובר על החלטות KEEP/EDIT ישנות במסמך זה.

## החלטת reset

כל **8/8** פריטי ה־Feed/Reels שהיו חיים בזמן ה־reset הם מעכשיו:

**`historical_learning_only` + `ARCHIVE_PENDING_MANUAL`**

הפעולה המועדפת היא **Archive, לא Delete**, ורק אחרי ש־VF-R001 / VF-R002 / VF-R003 הגיעו ל־`ready_for_publish` עם exact-final QA ו־execution receipts תקפים.

אין לבצע archive/delete אוטומטי דרך מסלול לא נתמך. כלי Instagram המחובר אינו חושף כרגע Archive/Delete למדיה, ולכן פעולת הארכוב עצמה מתבצעת באפליקציית Instagram ולאחריה live verification.

## מה נשמר מהביקורת הישנה

הסיווגים הישנים נשמרים **כלמידה בלבד**, לא כהחלטה להשאיר פריט בפיד:

| פריטים היסטוריים | סיווג למידה |
|---|---|
| G001 / G002 | `QUALITY_REFERENCE` למכניקת discovery/reveal בלבד; לא template ולא KEEP-live |
| G003 והלאה | `REVIEW_REQUIRED` היסטורי |

מקור הנתונים המפורט: [`data/feed-audit.json`](data/feed-audit.json).

## לקחים מחייבים לפיד החדש

- Reels של proof/process/reveal הראו Reach עדיף במדגם הקיים, אבל כמעט לא המירו לפעולה.
- Product-story קונקרטי הראה יעילות אינטראקציה טובה יותר מקרוסלות סטודיו גנריות.
- כפילות/חזרתיות כמו שני פוסטי סטודיו דומים היא failure של novelty/fatigue.
- WhatsApp / `050-2517000` / `wa.me` אינם CTA ציבורי. CTA נוכחי = הודעת Instagram בלבד.
- G004 נשמר בזהות העובדתית: **מחזיק טבעות לזמן אימון** — לא משקולת / kettlebell workout weight. הקריאייטיב הישן שלו STALE ואינו approval לשימוש חדש.
- שום cover/caption/preflight היסטורי אינו עובר בירושה לארטיפקט חדש.

## Launch authority

שלישיית הפתיחה החדשה נמצאת ב־`RESET-LAUNCH-TRIO.md`:
- VF-R001 — Reel movement proof.
- VF-R002 — Dragon detail carousel.
- VF-R003 — Metallic helmet reveal Reel.

כולם כרגע `evidence_selected`, **לא publish-authorized**.

## Profile reset

הביו החי עדיין מכיל WhatsApp/טלפון וסותר את `PUBLIC_CURRENT_CTA`. מצב רצוי: `packages/vfigos/PROFILE-DESIRED.json`. Graph write לביו אינו זמין בכלי המחובר, ולכן השינוי נעשה ידנית באפליקציה ואז נבדק מחדש בכלי live.

## כלל סיום

הפיד הישן אינו בסיס יצירתי להמשך. הוא Dataset.  
הפיד החדש מתחיל רק מ־real evidence → Media Librarian → Creative Director → render/edit → Hebrew Copy/Voice → Brand Guardian exact-final → Rubric/Contract/rights/policy → digest-bound receipts → publish → live verify → performance learning.
