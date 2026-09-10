# פריפלייט · {{ID}}

תאריך (Asia/Jerusalem):  
פורמט: סטוריז / פיד / קרוסלה / ריל  
מושב: צמיחה + סטודיו  
שער: **חסום** עד א–ו עבור.

מחיר בפריים/כיתוב: `X ₪` או אין. בלי ₪ מומצא.  
CTA: שלחו לנו הודעה כאן באינסטגרם · איסוף שדרות. לא «שלחו DM». לא וואטסאפ. (`PUBLIC_CURRENT_CTA`)  
קול: `VOICE.md` + `VOICE-CHART.md`. רובריקה: `CONTENT-RUBRIC.md`.

> Publish contract v2: אישור תוכן כללי או Canva edit אינו אישור לפרסום. השער חייב להיות מחובר ל־**תוצר הסופי המרונדר המדויק**.

## א · VOICE.md

- מצב (אחד): תהליך-קצר / סיפור-מוצר
- כיתוב: `packages/vfcopy/…`
- הוק חם? כן/לא
- פתיחת מגבלה / «מוכנים» / «בלי משלוח» / קופי דק? כן=נכשל

**א:** עבור / נכשל-סגור

## ב · Canva / vfcovers (לא JPEG גולמי) + ראיית ויזואל

- כלי: Canva MCP / vfcovers / vfcanva / Superdesign→render.py
- `edit_url` או נתיב PNG מורכב (אמיתי, לא מומצא):
- ראייה (thumbnail / export path / צילום מסך מקומי — חובה לפני עבור):
- JPEG גולמי מהמיטה/תיבה בלבד? כן=נכשל

**ב:** עבור / נכשל-סגור

## ג · ציון עצמי · רף סוכנות

| שאלה | כן/לא |
|---|---|
| סוכנות יקרה הייתה שולחת כמו שזה? | |
| העברית על `VOICE.md` + CTA נכון? | |
| הוויזואל עבר `EDIT-GATE.md`? | |
| 2–3 קומפס כתובים למטה? | |

לא אחד = נכשל-סגור. ביקורת עצמית כאן — לא Insights.

**ג:** עבור / נכשל-סגור

## ד · 2–3 קומפס (VOICE-RESEARCH)

| מי | מקור | מאמצים | דוחים |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

**ד:** עבור / נכשל-סגור

## ה · Rubric (`CONTENT-RUBRIC.md`)

| קהל | הוק/בהירות | קול | אמינות/חוק | פעולה | סה״כ | החלטה |
|---:|---:|---:|---:|---:|---:|---|
| _ | _ | _ | _ | _ | _/25 | עבור / חוזר ל-vfcopy |

עובר רק ≥20/25, בלי 1 בכל ציר, בלי דגל אדום.  
חסר ציון / סה״כ שגוי / «עבור» בלי טבלה = נכשל-סגור.

**ה:** עבור / נכשל-סגור

## ו · גרסת תוצר + QA על final render

- `caption_path`:
- `caption_sha256`:
- `visual_id` / `edit_url`:
- `visual_sha256` או export etag:
- `final_package_sha256`: sha256 של החבילה הסופית לפי סדר הפריימים/נכסים
- אושר בתאריך:

### שדות Publish Gate v2 — חובה לפני Instagram publish

```yaml
publish_gate_schema: 2
publish_gate: BLOCKED
approval_invalidated: false
qa_scope: exact-final-render
qa_reviewed_at: <ISO-8601>
content_rubric_total: <NN/25>
artifact_digest: sha256:<64-hex>
final_package_sha256: <64-hex>
brand_guardian: FAIL
copy_qa: FAIL
readability: FAIL
contrast: FAIL
```

כל שדה `PASS` נכתב רק אחרי בדיקה של הייצוא הסופי עצמו. בסטוריז, `brand_guardian`, `copy_qa`, `readability`, `contrast` חייבים להיות `PASS` לפני `publish_story`.

**אסור waiver לקריאות/ניגודיות.** ניסוח כמו «רכה אבל קריאה», «לא חוסם», «מספיק טוב» או אישור על בסיס Canva edit/thumbnail בלבד אינו `PASS`. משנים צבע/רקע/צל/overlay/מיקום, מייצאים מחדש, מחשבים `final_package_sha256` חדש ומריצים את השער מחדש.

שינוי מהותי בכיתוב או בוויזואל אחרי אישור → `approval_invalidated: true` ומחזירים שער א–ה + QA final render.

**ו:** עבור / נכשל-סגור

## שער

`publish_gate: PASS` רק אם א+ב+ג+ד+ה+ו = עבור, ה־Rubric ≥20/25, וה־QA של התוצר הסופי עבר. אחרת `publish_gate: BLOCKED` / **נכשל-סגור** — חסום שיבוץ ופרסום.
