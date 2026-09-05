# כריכה לחבילה קיימת

קלט: מזהה פוסט (VF-G00x) + hook מ־`#vfcopy` / `#vfgrowth`.  
פלט: קובץ כריכה לבריף (גוף המייל ב־07:00 על Grok) ולסקירת `#vfigos`.

לא ממציאים תמונת מוצר. בלי קובץ מהרצפה — כריכה טיפוגרפית בלבד.

## restraint (מ taste-skill brandkit — בריף בלבד)

לוגיקת פרזנטציה, **לא** generator לזהות חדשה. Canva + `canva-brand-check` נשארים המקור.

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
| חיפוש לפי מדיה (תמונה / וידאו / אתר) ומודל | כשצריך רפרנס סגנון — קודם **Canva**; `GenerateImage` רק failover |
| העתקת פרומפט + התאמת נושא | מחליפים נושא ל־**רצפה / דגם / איסוף שדרות** — לא סצנות אקשן/זומבי/דמויות זרות |
| Image → Prompt | רשות על **תמונת רצפה שנמסרה** בלבד — להרחבת תיאור לכריכה; לא המצאת מוצר |
| חבילות «travel edit / poster art» | רק אם יש צילום לקוח או הוכחת רצפה; אחרת כריכה טיפוגרפית |

**לא:** ייבוא ספריית 30k פרומפטים לריפו · התקנת YouMind ככלי HQ · פרומפט שממציא מוצר/₪/Insights · החלפת Canva brand kit.

דוח שתילה: `docs/TASTE-SKILL-EMBED-he.md`.

## הכנת הוכחת רצפה בדפדפן (footrue ToolBox)

מקור: [footrue.com](https://footrue.com/) — כלי חינמיים **בדפדפן** (לפי האתר: בלי הרשמה / בלי העלאה לשרת).  
דוח: `packages/vfresearch/sources/2026-09-05-footrue.md`.  
גם: `vfcanva/WORKFLOW.md` שלב prep.

| צורך | כלי | מתי |
|---|---|---|
| iPhone HEIC → JPG/PNG | [HEIC to JPG](https://footrue.com/tools/heic-to-jpg) | לפני העלאה ל־Canva |
| רקע מפריע על דגם שנמסר | [Background Remover](https://footrue.com/tools/background-remover) | רק על קובץ רצפה אמיתי — לא להמציא מוצר |
| קובץ כבד / גדול מדי | [image-compress](https://footrue.com/tools/image-compress) / [image-resize](https://footrue.com/tools/image-resize) | לפני Canva |
| PDF הצעה / מסמך | [pdf-merge](https://footrue.com/tools/pdf-merge) וכו׳ | אדם במשרד; לא שליחה אוטומטית |

**לא:** MCP / התקנה מ־HQ · תחליף ל־Canva brand kit · collage/watermark כזהות מותג · מספרי תנועה/MRR מהאתר («אין ספירה»).
