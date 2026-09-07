# Watchtower — דשבורד חווה על הרצפה (Edge)

מושב: **ייצור** (`@studio-producer`).  
לא פק חדש. לא runtime שני. לא Print מ־HQ.

מוצר: [Watchtower 3D Printer Dashboard](https://watchtower3d.com/) · קמפיין: [Kickstarter](https://www.kickstarter.com/projects/watchtower3d/watchtower-3d-printer-dashboard-and-farm-management)  
סטטוס אצלנו: **כוונת רכישה עתידית** — אין התקנה, אין רישיון מאומת, אין ₪ מחיר אצלנו.

## מה זה אצלם (מ־watchtower3d.com, 7.9.2026)

דשבורד מקומי (LAN) לצי מדפסות מעורב. הטענות בדף המוצר:

- פרוטוקולים: Bambu Lab · PrusaLink · OctoPrint · Klipper
- התקנה על דסקטופ או Raspberry Pi; גילוי אוטומטי ברשת; בלי פלאגין/שינוי קושחה (לפי הדף)
- תור + ניתוב עבודה לפי סוג/חומר/סטטוס; דפדפן קבצים לצי; ניהול סלילים
- אזעקות מאוחדות (HMS / Klipper / PrusaLink)
- 100% מקומי; גישה מרוחקת רק במנהרה מוצפנת אם פותחים אותה
- רישיון lifetime בהשקה (לפי הדף) — מחיר VF: **X ₪** עד חשבונית/דף תשלום מאומת

Kickstarter עצמו היה חסום ב־Cloudflare מהענן — **אין גוף קמפיין** מכאן (pledges / תאריך משלוח / Elegoo). לא ממציאים.

## איפה זה יושב אצלנו

```
Office / HQ     Cursor desk · בריף · הצעות · IG     לא מדפיס, לא פותח מצלמת מיטה
Kernel          velvetos-core · חוזים · סנסורים      לא daemon IoT, לא broker
Edge            Watchtower על LAN שדרות              מדבר עם המדפסות
```

Watchtower = **שכבת Edge / עצבים** (`LAYERS.md`) — מחליף את הפער ש־FLOOR.md כבר סימן: HQ לא מריץ חווה; אדם+כלי רצפה מריצים.

זה **לא** Maxel-מ־HQ (נדחה ב־`docs/SHARES-2026-08-30.md`). אותו מוצר על הרצפה — מותר. אותו מוצר כפקודה מ־Cloud Agent — אסור.

## מה כל שכבה עושה אחרי רכישה

| שכבה | Watchtower | VelvetOS |
|---|---|---|
| Edge | סטטוס חי, תור מקומי, מצלמה, start/stop, סלילים, אזעקות | אדם על המיטה מאשר שכבה ראשונה; כרטיס `print.done` |
| Kernel | — | חוזה `print.done` / `sync.completed` על דיסק; `component_state` |
| Office | תצוגת קיר / טלפון ברשת הסטודיו | תור הזמנות (`הדפסה`→`איסוף`), כדאיות, `vfcost`, תוכן אחרי PREFLIGHT |

## צינור משותף (לא אינטגרציית MQTT בליבה)

```
פנייה → שיחה → הצעה → [סלייס Orca] → תור VF (job/SKU)
                                      ↓
                         Watchtower (מיטה פנויה על הרצפה)
                                      ↓
                         הדפסה תקינה → כרטיס PRINT-DONE.md
                                      ↓
                         vfom טיוטת ריל → PREFLIGHT → vfigos
```

נתונים שמותר למשוך **רק אם Watchtower באמת מדד** (ייצוא / צילום מסך / קובץ JSON מקומי → Drive `create_file` או `vfprod/hq/cards/`):

- מדפסת / מיטה
- דקות הדפסה
- גרמים / סליל (ל־`MATERIAL.md` ו־`vfcost` — לא ל־₪ מכירה)
- נתיב timelapse / still
- הצלחה / כשל (כשל = עצירה ידנית + שורה בבריף 02/03, לא דוח בושה לכריסטיאן)

חסר מדידה = **חסר**. אנליטיקת «cost» של Watchtower ≠ מחיר הצעה. `vfcost` נשאר גרמים × ILS/ק״ג מאומת.

## נעול

- אין Print / pause / resume מ־HQ או מ־Cloud Agent דרך Watchtower.
- אין חיבור Core→מצלמת Bambu/Snapmaker/Elegoo כדמון בריפו.
- אין פרסום אוטומטי כשהדפסה נגמרת (Print→Post = כרטיס → טיוטה → PREFLIGHT).
- אין אוטו־DM, בוסט, משלוח ארצי, סקר→הדפסה.
- אין להפוך את Watchtower ל־orchestrator שני (Orca ADE / CrewAI / event bus).
- מנהרה מרוחקת = Mac/Pi בשדרות בלבד (`vfmcp/HOST.md`). Cloud לא פותח אתר מדפסת.
- Elegoo / Snapmaker: **לא ברשימת הפרוטוקולים** בדף Watchtower (7.9) — לפני רכישה לאמת מיטה-מיטה. פער = נשארים על היצרן + אדם.

## שלבי אימוץ (כשיגיע רישיון)

1. **יום 1 — כלי רצפה בלבד.** Pi או `Mac-Office` על ה־LAN. מסך קיר. בלי bind ל־HQ.
2. **ייצוא ידני.** אחרי הדפסה תקינה: כרטיס `PRINT-DONE.md` + אירוע `print.done` (`layer: edge`).
3. **תצוגה במשרד.** פורטלט בריף 03 / command surface = **קריאה** של סטטוס מייצוא — לא כפתור Print. רק אחרי שורה ב־`capabilities.json`.
4. **סנכרון.** `sync.completed` כשיש host ששוטף buffer. בלי host = לא ממציאים טלמטריה.
5. **Degraded.** Watchtower נפל → רצפה ידנית (`FLOOR.md`) · `component_state: Degraded` · אין ניחוש שעות תור.

## מקורות / פערים

| מקור | מה לקחנו | מה חסר |
|---|---|---|
| https://watchtower3d.com/ | פרוטוקולים, מקומי, תור, סלילים | מחיר VF, Elegoo |
| Kickstarter | כוונת רכישה של הבעלים | גוף קמפיין חסום Cloudflare מהענן |
| `FLOOR.md` / `PRINT-DONE.md` | אדם על מיטה; כרטיס אחרי הצלחה | — |
| `LAYERS.md` | Edge ≠ Core daemon | — |

## קישורים

- רצפה: [`FLOOR.md`](FLOOR.md)
- כרטיס אחרי הדפסה: [`PRINT-DONE.md`](PRINT-DONE.md)
- שכבות: `packages/velvetos/LAYERS.md`
- אירועים: `packages/velvetos/schema/events.catalog.json`
- Host שדרות: `packages/vfmcp/HOST.md`
