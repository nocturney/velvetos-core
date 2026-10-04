# OpenMontage — מה נכנס למשרד

מקור: [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) (נקרא 2026-08-30).  
המאגר הוא סטודיו וידאו סוכני: 12 צינורות ב-`pipeline_defs/`, כלים ב-Python, Remotion/HyperFrames, שערי איכות, ומסלול «הדבק ריל שאתה אוהב».

כאן זה **מפה + נהלי משרד** על החבילות הקיימות. אין `make setup`. אין מפתחות fal/Veo/Kling בגיט. אין שליחת אינסטגרם מ-HQ. אין סצנת מיטה מומצאת. אין ₪ מומצא.

פק הקטלוג: [`packages/vfom/`](../packages/vfom/).  
מפה מכונה: [`packages/vfom/catalog.json`](../packages/vfom/catalog.json).  
בדיקה: `python3 scripts/check-vfom.py`.

## למה זה עוזר לסטודיו


OpenMontage כבר כתב את זה כמניפסטים. אנחנו לוקחים את הצורה, לא את המנוע.

## כבר יש אצלנו — לא לשכפל

| רעיון מ-OpenMontage | חבילה אצלנו | למה לא פק חדש |
|---|---|---|
| כיתוב + הוק | `vfcopy` | שיעורי בית → טיוטה → לינט |
| סקירה ושיבוץ | `vfigos` | HQ שולח/מפרסם דרך tools/policy; Grok גיבוי אופציונלי |
| הוכחת רצפה | `vfprod` | טיימלאפס אמיתי, לא ארכיון |

## להטמיע עכשיו (נהלים, לא רנדור)

| # | רעיון | מקור | נוהל | חבילות |
|---|---|---|---|---|
| 2 | טיימלאפס → קליפים מדורגים | `clip-factory.yaml` | [clip-factory](../packages/vfom/crews/clip-factory.md) | `vfprod`, `vfgrowth`, `vfcopy`, `vfigos` |
| 4 | אישור אדם על סצנות | Backlot + human_approval | [scene-gate](../packages/vfom/crews/scene-gate.md) | `vfigos`, `vfgrowth`, `vfcovers` |

## אחר כך — רק אם ראש צוות פותח

| רעיון | למה מחכים |
|---|---|
| Animated Explainer | רק עם הוכחת «איך מדפיסים» אמיתית. לא סרטון לימוד מומצא |
| Veo / Kling / fal / Suno | תקציב + עלות לפני קריאה. אין המרת דולר ל-₪ מ-HQ |

## דולג — לא אצלנו

אווטאר דובר, Talking Head, אנימציית דמות, דיבוב/לוקליזציה, פודקאסט, דמו מסך, מונטאז' ארכיון (NASA/Archive.org) במקום טיימלאפס, `publish-director` חי.

פירוט: [`packages/vfom/LOCK.md`](../packages/vfom/LOCK.md).

## איך משתמשים

1. בשיחת Cursor: `@vfom clip-factory על הטיימלאפס של <עבודה>` / `@vfom reference-plan` עם קישור.
2. הסוכן ממלא את התבנית מהנוהל. לא שולח. לא ממציא מיטה.
4. חסר גלם → **חסר**. עצור.

## סדר מומלץ לריל מהמיטה

1. `clip-factory` — אם יש טיימלאפס ארוך.
2. `hybrid-reel` — גלם + כיתוב + כריכה.
3. `scene-gate` — אדם על הסצנות.
4. `self-review` — ואז `vfigos`.
5. `reference-plan` — רק כשיש ריל ייחוס שרוצים לחקות *מבנה*, לא מראה מותג.
