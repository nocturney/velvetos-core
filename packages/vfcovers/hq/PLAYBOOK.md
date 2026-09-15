# כריכה לחבילה קיימת

## VF_PUBLICATION_ROUTE_V1 - current publication scope

For Velvet Factory publication tasks, use `packages/vfom/PUBLICATION-PREP-EXECUTION.md` and the `publicationRoute` in `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json`. Canva/vfcanva are forbidden in this scope; provider notes labelled LEGACY below are not executable routes for VF. Other businesses and non-publication uses are unchanged.
Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

קלט: מזהה פוסט (VF-G00x) + hook מ־`#vfcopy` / `#vfgrowth`.  
פלט: קובץ כריכה לבריף (גוף המייל ב־07:00 על Grok) ולסקירת `#vfigos`.

לא ממציאים תמונת מוצר. בלי קובץ מהרצפה — כריכה טיפוגרפית בלבד.

> LEGACY / provenance only for VF publication; not a provider route: לוח עומד: `vfgrowth/CALENDAR.md`. G003 בלי גלם = אין כריכת מוצר. G006 = טיפוגרפיה Canva (טרם הורכב).

## restraint (מ taste-skill brandkit — בריף בלבד)

> LEGACY / provenance only for VF publication; not a provider route: לוגיקת פרזנטציה, **לא** generator לזהות חדשה. Canva + `canva-brand-check` נשארים המקור.

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
> LEGACY / provenance only for VF publication; not a provider route: | חיפוש לפי מדיה (תמונה / וידאו / אתר) ומודל | כשצריך רפרנס סגנון — קודם **Canva**; `GenerateImage` רק failover |
| העתקת פרומפט + התאמת נושא | מחליפים נושא ל־**רצפה / דגם / איסוף שדרות** — לא סצנות אקשן/זומבי/דמויות זרות |
| Image → Prompt | רשות על **תמונת רצפה שנמסרה** בלבד — להרחבת תיאור לכריכה; לא המצאת מוצר |
| חבילות «travel edit / poster art» | רק אם יש צילום לקוח או הוכחת רצפה; אחרת כריכה טיפוגרפית |

> LEGACY / provenance only for VF publication; not a provider route: **לא:** ייבוא ספריית 30k פרומפטים לריפו · התקנת YouMind ככלי HQ · פרומפט שממציא מוצר/₪/Insights · החלפת Canva brand kit.

דוח שתילה: `docs/TASTE-SKILL-EMBED-he.md`.

## הכנת הוכחת רצפה בדפדפן (footrue ToolBox)

מקור: [footrue.com](https://footrue.com/) — כלי חינמיים **בדפדפן** (לפי האתר: בלי הרשמה / בלי העלאה לשרת).  
דוח: `packages/vfresearch/sources/2026-09-05-footrue.md`.  
> LEGACY / provenance only for VF publication; not a provider route: גם: `vfcanva/WORKFLOW.md` שלב prep.

| צורך | כלי | מתי |
|---|---|---|
> LEGACY / provenance only for VF publication; not a provider route: | iPhone HEIC → JPG/PNG | [HEIC to JPG](https://footrue.com/tools/heic-to-jpg) | לפני העלאה ל־Canva |
| רקע מפריע על דגם שנמסר | [Background Remover](https://footrue.com/tools/background-remover) | רק על קובץ רצפה אמיתי — לא להמציא מוצר |
> LEGACY / provenance only for VF publication; not a provider route: | קובץ כבד / גדול מדי | [image-compress](https://footrue.com/tools/image-compress) / [image-resize](https://footrue.com/tools/image-resize) | לפני Canva |
| PDF הצעה / מסמך | [pdf-merge](https://footrue.com/tools/pdf-merge) וכו׳ | אדם במשרד; לא שליחה אוטומטית |

> LEGACY / provenance only for VF publication; not a provider route: **לא:** MCP / התקנה מ־HQ · תחליף ל־Canva brand kit · collage/watermark כזהות מותג · מספרי תנועה/MRR מהאתר («אין ספירה»).

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

> LEGACY / provenance only for VF publication; not a provider route: Before any Velvet Factory concept, image selection/edit, Canva operation, cover, carousel, Story still, Reel cover, feed/grid plan, render or publish handoff, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Verify Canva asset `MAHVL7PKpvE` and artifact SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`. Record a PASS binding in the job/manifest/preflight before creative work continues.

> LEGACY / provenance only for VF publication; not a provider route: This gate is **fail-closed**: if the standard is unavailable, mismatched or unverified, stop the creative branch as `visual_standard_unavailable`; never fall back to a generic 3D-print, stock, template, Canva-default or model-default aesthetic. Real source product media remains Product Truth and outranks style; preserve product identity/geometry/material/color and apply the approved reference to composition, surroundings, light, crop, typography and finish.
