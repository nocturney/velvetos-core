# כריכה לחבילה קיימת

## VF_PUBLICATION_ROUTE_V1 - current publication scope

Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

קלט: מזהה פוסט (VF-G00x) + hook מ־`#vfcopy` / `#vfgrowth`.  
פלט: קובץ כריכה לבריף (גוף המייל ב־07:00 על Grok) ולסקירת `#vfigos`.

לא ממציאים תמונת מוצר. בלי קובץ מהרצפה — כריכה טיפוגרפית בלבד.


## restraint (מ taste-skill brandkit — בריף בלבד)


| עקרון | בכריכה |
|---|---|
| grid + gutters | מרווח ברור בין hook / proof / CTA |
| negative space | hook קצר; לא לדחוס את כל החבילה לפריים אחד |
| sparse typography | טקסט על המסגרת מינימלי — caption ב־`vfcopy` |
| restrained density | proof אחד ברור; לא college של badges |
| coherent set | square + story מאותה שפה — `FORMATS.json` |

**אסור:** hex/fonts/לוגו מומצאים; סצנת רצפה שלא נמסרה; Insights על הגרפיקה; «שלחו DM».

**מותר על המסגרת:** hook, שם job/SKU שהמשתמש נתן, WhatsApp / איסוף שדרות.

## ספריית פרומפטים חיצונית (YouMind) — השראה בלבד

מקור: [youmind.com/prompts](https://youmind.com/ru-RU/prompts) (ספריית פרומפטי תמונה/וידאו/אתר; מתעדכן יומית).  
דוח: `packages/vfresearch/sources/2026-09-05-youmind-prompts.md`.

| דפוס | אצלנו |
|---|---|
| העתקת פרומפט + התאמת נושא | מחליפים נושא ל־**רצפה / דגם / איסוף שדרות** — לא סצנות אקשן/זומבי/דמויות זרות |
| Image → Prompt | רשות על **תמונת רצפה שנמסרה** בלבד — להרחבת תיאור לכריכה; לא המצאת מוצר |
| חבילות «travel edit / poster art» | רק אם יש צילום לקוח או הוכחת רצפה; אחרת כריכה טיפוגרפית |


דוח שתילה: `docs/TASTE-SKILL-EMBED-he.md`.

## הכנת הוכחת רצפה בדפדפן (footrue ToolBox)

מקור: [footrue.com](https://footrue.com/) — כלי חינמיים **בדפדפן** (לפי האתר: בלי הרשמה / בלי העלאה לשרת).  
דוח: `packages/vfresearch/sources/2026-09-05-footrue.md`.  

| צורך | כלי | מתי |
|---|---|---|
| רקע מפריע על דגם שנמסר | [Background Remover](https://footrue.com/tools/background-remover) | רק על קובץ רצפה אמיתי — לא להמציא מוצר |
| PDF הצעה / מסמך | [pdf-merge](https://footrue.com/tools/pdf-merge) וכו׳ | אדם במשרד; לא שליחה אוטומטית |


## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

## VF_VISUAL_STANDARD_GATE

Before public creative execution, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Bind SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897` and require `visualStandard.gate=PASS`. Missing/mismatched authority is `visual_standard_unavailable`; generic visual fallback is forbidden.
