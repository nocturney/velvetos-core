# רצפה

מושב: **ייצור**.  
מקור Gemini: Vision AI Monitor + Timelapse-to-Reel.  
מקור Perplexity: Maxel AI (חוות הדפסה אוטומטית).

## הקצאה (עד 4 מיטות, ידני)

Perplexity הציע סוכן שמקבל STL, חותך, ומקצה מדפסת לפי חומר / גודל / תאריך יעד.  
כאן: אדם על הרצפה בוחר מיטה פנויה. HQ ממליץ בלבד (`ROUTING.md` · `python3 scripts/vfprod.py route`) ולא דוחף G-code.

ארבע מיטות בקטלוג: `FLEET.json` (Bambu A/B · Snapmaker U1 · Elegoo Centauri). דגם/סדרה ריקים עד ספירת רצפה.

דשבורד חווה עתידי על ה־LAN (Watchtower) = **Edge בלבד** — פלייבוק: [`WATCHTOWER.md`](WATCHTOWER.md). כלי רצפה, לא פקודת Print מ־HQ.

## ניטור (משרד, לא דמון חי ב־HQ)

במשמרת:

1. להסתכל על המיטה: ספגטי, הינתקות, Layer Shift.
2. אם כשל — לעצור ידנית, לצלם פריים, לכתוב בבריף (`02`/`03`).
3. HQ לא מתחבר למצלמת מדפסת ולא עוצר הדפסה מרחוק. זה Grok/רצפה.

## אחרי הדפסה תקינה

פלייבוק מלא: [`PRINT-DONE.md`](PRINT-DONE.md) · תבנית: [`hq/PRINT-CARD-TEMPLATE.md`](hq/PRINT-CARD-TEMPLATE.md).

1. לשמור Timelapse / סטיל אם יש (נתיב Drive או קובץ מקומי). חסר גלם = **חסר** — לא ממציאים סצנה.
2. למלא **כרטיס Print-Done** (SKU, חומר מ־`MATERIAL.md`, גרמים/דקות אם נמדדו, רישיון). אירוע: `print.done`.
3. למסור לצמיחה (`vfom` clip-factory / hybrid-reel → `vfcopy` → Canva) כטיוטה — לא כפוסט חי.
4. שיבוץ רק אחרי `vfgrowth/PREFLIGHT.md` עבור. שליחה דרך כלים (`vfigos/SEND.md`).
5. Proof מהרצפה (מה שעל המיטה) — רק אם באמת על המיטה.

HQ לא מתחבר למצלמת מדפסת ולא דוחף Print מרחוק (Edge/רצפה בלבד). Watchtower על הקיר בשדרות לא משנה את הנעילה הזו.

אחרי הדפסה: וי תחזוקה ב־[`MAINTENANCE.md`](MAINTENANCE.md) לפני עבודה מורכבת הבאה. בריף 03: `python3 scripts/vfprod.py brief`.
