# פריפלייט · {{ID}}

תאריך (Asia/Jerusalem):  
פורמט: סטוריז / פיד / קרוסלה / ריל  
מושב: צמיחה + סטודיו  
שער: **חסום** עד א–ו עבור.

מחיר בפריים/כיתוב: `X ₪` או אין. בלי ₪ מומצא.  
CTA: לפי `constitution/PUBLIC_CTA.md`: showcase יכול להיות ללא CTA / engagement / הודעת Instagram ניטרלית; commercial משתמש ב־Instagram message. אין WhatsApp.  
קול: `VOICE.md` + `VOICE-CHART.md`. רובריקה: `CONTENT-RUBRIC.md`.

> Publish contract v2: אישור תוכן כללי או Canva edit אינו אישור לפרסום. השער חייב להיות מחובר ל־**תוצר הסופי המרונדר המדויק**.

## א · VOICE.md

- מצב (אחד): תהליך-קצר / סיפור-מוצר
- public intent: `showcase` / `commercial`
- כיתוב: `packages/vfcopy/…`
- הוק חם? כן/לא
- פתיחת מגבלה / «מוכנים» / «בלי משלוח» / קופי דק? כן=נכשל
- אם `showcase`: אין «הזמנות», «רוצים אחד כזה/משלכם», מחיר/זמינות של המודל המצולם או ניסוח הצעת מכר.

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

### Audio Gate — חובה לריל / סטורי וידאו

לקרוסלה/סטילס: `audio_gate: N/A`.

```yaml
audio_gate: PASS | FAIL | N/A
audio_mode: source | music | sfx | source_plus_music | source_plus_sfx | intentional_silence
audio_stream_present: true | false
audio_loudness_measurement: <measurement or N/A>
audio_noise_clipping: PASS | FAIL | N/A
audio_sync: PASS | FAIL | N/A
audio_story_fit: PASS | FAIL | N/A
intentional_silence_reason: <required only when mode=intentional_silence>
```

כלל: audio stream חסר או near-silent = **FAIL** כברירת מחדל. עצם קיום stream אינו PASS. שקט עובר רק אם הוא החלטה קריאייטיבית מכוונת, מנומקת ונבדקה. מוזיקה/SFX עוברים דרך `vf-ig-music` / `vfresearch/MUSIC.md` כאשר רלוונטי.

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
audio_gate: FAIL | PASS | N/A
```

כל שדה `PASS` נכתב רק אחרי בדיקה של הייצוא הסופי עצמו. בסטוריז/ריל וידאו גם `audio_gate` חייב להיות `PASS` לפני publish. בסטילס/קרוסלה הוא `N/A`.

**אסור waiver לקריאות/ניגודיות/אודיו שנשכח.** ניסוח כמו «רכה אבל קריאה», «לא חוסם», «מספיק טוב», «יש stream אז סבבה» או אישור על בסיס Canva edit/thumbnail בלבד אינו `PASS`. משנים צבע/רקע/צל/overlay/מיקום/אודיו, מייצאים מחדש, מחשבים `final_package_sha256` חדש ומריצים את השער מחדש.

שינוי מהותי בכיתוב, בוויזואל או באודיו אחרי אישור → `approval_invalidated: true` ומחזירים שער א–ה + QA final render.

**ו:** עבור / נכשל-סגור

## זכויות / פרטיות — scope

- owner-captured showcase של הדפסה: אין blanket model-license blocker.
- מדיה צד ג׳ / UGC / אדם מזוהה / פרטיות / מגבלה ידועה: gate פעיל.
- explicit public sale/paid promotion של המודל המצולם: מסלול commercial יכול להפעיל בדיקת רישיון מודל.
- זו מדיניות workflow פנימית; אין להסיק ממנה קביעה משפטית על רישיון מסוים.

## שער

`publish_gate: PASS` רק אם א+ב+ג+ד+ה+ו = עבור, ה־Rubric ≥20/25, וה־QA של התוצר הסופי עבר. בווידאו נדרש גם `audio_gate: PASS`. אחרת `publish_gate: BLOCKED` / **נכשל-סגור** — חסום שיבוץ ופרסום.
