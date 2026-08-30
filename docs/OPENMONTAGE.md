# OpenMontage — מה נכנס למשרד

מקור: [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) (נקרא 2026-08-30).  
המאגר הוא סטודיו וידאו סוכני: 12 צינורות ב-`pipeline_defs/`, כלים ב-Python, Remotion/HyperFrames, שערי איכות, ומסלול «הדבק ריל שאתה אוהב».

כאן זה **מפה + נהלי משרד** על החבילות הקיימות. אין `make setup`. אין מפתחות fal/Veo/Kling בגיט. אין שליחת אינסטגרם מ-HQ. אין סצנת מיטה מומצאת. אין ₪ מומצא.

פק הקטלוג: [`packages/vfom/`](../packages/vfom/).  
מפה מכונה: [`packages/vfom/catalog.json`](../packages/vfom/catalog.json).  
בדיקה: `python3 scripts/check-vfom.py`.

## למה זה עוזר לסטודיו

Velvet Factory כבר מצלם מיטה ומוציא טיוטת ריל (`vfgrowth` / `vf-content-sprint`). חסר היה **צינור הפקה**: איך חותכים טיימלאפס ארוך, איך שכבת Canva לא בולעת את ההדפס, ואיך אדם מאשר סצנות לפני Grok.

OpenMontage כבר כתב את זה כמניפסטים. אנחנו לוקחים את הצורה, לא את המנוע.

## כבר יש אצלנו — לא לשכפל

| רעיון מ-OpenMontage | חבילה אצלנו | למה לא פק חדש |
|---|---|---|
| Instagram Reels 1080×1920 | `vfcanva` | `ig_reel_cover` / `ig_story` ב-`FORMATS.json` |
| כיתוב + הוק | `vfcopy` | שיעורי בית → טיוטה → לינט |
| כריכה / פריים ראשון | `vfcovers`, `vfcanva` | Canva; Superdesign רק אם Canva מנותק |
| סקירה ושיבוץ | `vfigos` | HQ לא שולח. Grok שולח |
| הוכחת רצפה | `vfprod` | טיימלאפס אמיתי, לא ארכיון |

## להטמיע עכשיו (נהלים, לא רנדור)

| # | רעיון | מקור | נוהל | חבילות |
|---|---|---|---|---|
| 1 | תכנון מריל ייחוס | `cinematic.yaml` reference_input | [reference-plan](../packages/vfom/crews/reference-plan.md) | `vfgrowth`, `vfresearch`, `vfcopy`, `vfcanva` |
| 2 | טיימלאפס → קליפים מדורגים | `clip-factory.yaml` | [clip-factory](../packages/vfom/crews/clip-factory.md) | `vfprod`, `vfgrowth`, `vfcopy`, `vfigos` |
| 3 | גלם + שכבת עיצוב | `hybrid.yaml` | [hybrid-reel](../packages/vfom/crews/hybrid-reel.md) | `vfprod`, `vfcanva`, `vfcovers`, `vfcopy`, `vfigos` |
| 4 | אישור אדם על סצנות | Backlot + human_approval | [scene-gate](../packages/vfom/crews/scene-gate.md) | `vfigos`, `vfgrowth`, `vfcovers` |
| 5 | סיכון מצגת + לינט לפני מסירה | Production governance | [self-review](../packages/vfom/crews/self-review.md) | `vfigos`, `vfcopy`, `vfcanva` |

## אחר כך — רק אם ראש צוות פותח

| רעיון | למה מחכים |
|---|---|
| Animated Explainer | רק עם הוכחת «איך מדפיסים» אמיתית. לא סרטון לימוד מומצא |
| Animation / Remotion / HyperFrames / ffmpeg | מנוע שני. Canva קודם |
| Veo / Kling / fal / Suno | תקציב + עלות לפני קריאה. אין המרת דולר ל-₪ מ-HQ |

## דולג — לא אצלנו

אווטאר דובר, Talking Head, אנימציית דמות, דיבוב/לוקליזציה, פודקאסט, דמו מסך, מונטאז' ארכיון (NASA/Archive.org) במקום טיימלאפס, `publish-director` חי.

פירוט: [`packages/vfom/LOCK.md`](../packages/vfom/LOCK.md).

## איך משתמשים

1. בשיחת Cursor: `@vfom clip-factory על הטיימלאפס של <עבודה>` / `@vfom reference-plan` עם קישור.
2. הסוכן ממלא את התבנית מהנוהל. לא שולח. לא ממציא מיטה.
3. Canva לכריכה. `vfigos` לסקירה. Grok Bot משבץ ושולח.
4. חסר גלם → **חסר**. עצור.

## סדר מומלץ לריל מהמיטה

1. `clip-factory` — אם יש טיימלאפס ארוך.
2. `hybrid-reel` — גלם + כיתוב + כריכה.
3. `scene-gate` — אדם על הסצנות.
4. `self-review` — ואז `vfigos`.
5. `reference-plan` — רק כשיש ריל ייחוס שרוצים לחקות *מבנה*, לא מראה מותג.
