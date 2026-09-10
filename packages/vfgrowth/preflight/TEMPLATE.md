# פריפלייט · {{ID}}

תאריך (Asia/Jerusalem):  
פורמט: סטוריז / פיד / קרוסלה / ריל  
מושב: צמיחה + סטודיו  
שער: **חסום** עד א–ו עבור.

מחיר בפריים/כיתוב: `X ₪` או אין. בלי ₪ מומצא.  
CTA: לפי `constitution/PUBLIC_CTA.md`.  
חוזה קופי: `packages/vfcopy/SOFT-TOOLS-CONTRACT.md`. רובריקה: `CONTENT-RUBRIC.md`.

> Publish contract v2: אישור תוכן כללי או Canva edit אינו אישור לפרסום. השער חייב להיות מחובר ל־**תוצר הסופי המרונדר המדויק** ולגרסת הקופי המדויקת שעברה lint.

## א · Soft Tools / Copy Gate

```yaml
reader_first: <reader state / useful point / real proof>
voice_mode: process-short | product-story
marketing_aids:
  copywriting: APPLIED | N/A
  copy-editing: APPLIED | N/A
  marketing-psychology: APPLIED | N/A
template_or_prompt_frame: <path/name>
copy_path: <packages/vfcopy/...>
copy_version: <id or digest>
vfcopy_lint: PASS | FAIL | NEEDS_INPUT
vfcopy_lint_version: <same copy version/digest>
fact_gate: PASS | NEEDS_INPUT | FAIL
visual_copy_decision: TEXT_WINS | NO_TEXT | N/A
visual_copy_reason: <required for TEXT_WINS>
```

עובר רק אם הגרסה הסופית עברה בפועל:
`verified context → reader-first → VOICE + VOICE-CHART + voice/approved → vfmskill writing aids כשיווקי → template → velvet-hebrew-copy → ai-tells-he → check-vfcopy.py lint(actual final copy) → fact gate`.

`VOICE.md` בלבד, Brand Guardian, Rubric או CI/eval אינם תחליף. `NEEDS_INPUT` = חסום. שינוי קופי אחרי lint מבטל PASS ומחייב lint מחדש.

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
| הקופי עבר `SOFT-TOOLS-CONTRACT.md` על הגרסה הסופית? | |
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

**אסור waiver לקריאות/ניגודיות/אודיו שנשכח.** אישור על בסיס Canva edit/thumbnail בלבד אינו `PASS`. משנים, מייצאים מחדש, מחשבים `final_package_sha256` חדש ומריצים את השער מחדש.

שינוי מהותי בכיתוב אחרי lint → `vfcopy_lint: FAIL`/invalidated עד lint מחדש. שינוי מהותי בכיתוב, בוויזואל או באודיו אחרי Rubric/PREFLIGHT → `approval_invalidated: true` ומחזירים שער א–ה + QA final render.

**ו:** עבור / נכשל-סגור

## זכויות / פרטיות — scope

- owner-captured showcase של הדפסה: אין blanket model-license blocker.
- מדיה צד ג׳ / UGC / אדם מזוהה / פרטיות / מגבלה ידועה: gate פעיל.
- explicit public sale/paid promotion של המודל המצולם: מסלול commercial יכול להפעיל בדיקת רישיון מודל.
- זו מדיניות workflow פנימית; אין להסיק ממנה קביעה משפטית על רישיון מסוים.

## שער

`publish_gate: PASS` רק אם א+ב+ג+ד+ה+ו = עבור, `vfcopy_lint: PASS` תואם לגרסת הקופי הסופית, `fact_gate: PASS`, ה־Rubric ≥20/25, וה־QA של התוצר הסופי עבר. בווידאו נדרש גם `audio_gate: PASS`. אחרת `publish_gate: BLOCKED` / **נכשל-סגור**.
