# פריפלייט · {{ID}}

תאריך (Asia/Jerusalem):  
פורמט: סטוריז / פיד / קרוסלה / ריל  
מושב: צמיחה + סטודיו  
שער: **חסום** עד כל השערים הרלוונטיים עוברים.

מחיר בפריים/כיתוב: `X ₪` או אין. בלי ₪ מומצא.  
CTA public: לפי `constitution/PUBLIC_CTA.md` — **הודעת Instagram** כשנדרש; בלי WhatsApp/טלפון ציבורי. Showcase יכול לבחור CTA ניטרלי/ללא CTA לפי intent הפעיל.  
חוזה טקסט: `constitution/VISIBLE_TEXT.md` + `packages/vfcopy/SOFT-TOOLS-CONTRACT.md`. רובריקה: `CONTENT-RUBRIC.md`.

> Publish contract v2: אישור תוכן כללי או Canva edit אינו אישור לפרסום. השער חייב להיות מחובר ל־**תוצר הסופי המרונדר המדויק** ולגרסת הקופי המדויקת שעברה Visible Text Gate + lint.

## א · Visible Text / Copy Gate

```yaml
visible_text_gate: FAIL
visible_text_surface: public-social
text_sha256: <64-hex exact final caption/public copy>
truth_checked: FAIL
reader_first: FAIL
reader_first_note: <reader state / useful point / real proof>
copy_authority: FAIL
humanizer_ai_tells: FAIL
voice_mode: process-short | product-story | showcase
marketing_aids:
  copywriting: APPLIED | N/A
  copy-editing: APPLIED | N/A
  marketing-psychology: APPLIED | N/A
template_or_prompt_frame: <path/name>
copy_path: <packages/vfcopy/...>
copy_version: <id or digest>
vfcopy_lint: FAIL | PASS | NEEDS_INPUT
vfcopy_lint_surface: public-social
vfcopy_lint_version: <same exact text version/digest>
fact_gate: FAIL | PASS | NEEDS_INPUT
surface_qa: FAIL | PASS
visual_text_gate: PASS | FAIL | N/A
visual_copy_decision: TEXT_WINS | NO_TEXT | N/A
visual_copy_reason: <required for TEXT_WINS; N/A otherwise>
visual_text_sha256: <64-hex | N/A>
```

עובר רק אם הגרסה הסופית עברה בפועל:
`verified context → reader-first → public VOICE/VOICE-CHART/approved voice → relevant vfmskill writing aids → template → velvet-hebrew-copy → Humanizer/ai-tells → scripts/vf_visible_text.py --surface public-social על actual final copy → fact gate → surface QA`.

אם יש cover/first-frame/overlay/slide text: בנוסף `visual-microcopy` gate עם 3–5 candidates + `NO_TEXT`, Creative Director/Brand Guardian, והחלטת `TEXT_WINS` מנומקת או `NO_TEXT`.

`VOICE.md` בלבד, Brand Guardian, Rubric או CI/eval אינם תחליף. `NEEDS_INPUT` / `UNPROVEN` = חסום. שינוי קופי אחרי PASS מבטל את ה־PASS ומחייב gate מחדש.

**א:** עבור / נכשל-סגור

## ב · Canva / vfcovers + ראיית ויזואל

- כלי: Canva MCP / vfcovers / vfcanva / Superdesign→render.py
- `edit_url` או נתיב PNG מורכב (אמיתי, לא מומצא):
- ראייה (thumbnail / export path / צילום מסך מקומי — חובה לפני עבור):
- JPEG גולמי מהמיטה/תיבה בלבד? כן=נכשל

**ב:** עבור / נכשל-סגור

## ג · ציון עצמי · רף סוכנות

| שאלה | כן/לא |
|---|---|
| סוכנות יקרה הייתה שולחת כמו שזה? | |
| `visible_text_gate: PASS` תואם לקופי הסופי? | |
| אם יש visual text — הוא מנצח `NO_TEXT` או שנבחר `NO_TEXT`? | |
| הוויזואל עבר `EDIT-GATE.md`? | |
| 2–3 קומפס/כיוונים כשנדרש? | |

לא אחד = נכשל-סגור. ביקורת עצמית כאן — לא Insights.

**ג:** עבור / נכשל-סגור

## ד · קומפס / ייחוד

| מי/מה | מקור | מאמצים | דוחים |
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
- `text_sha256` / `caption_sha256`:
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
visible_text_gate: FAIL
text_sha256: <64-hex>
brand_guardian: FAIL
copy_qa: FAIL
readability: FAIL
contrast: FAIL
audio_gate: FAIL | PASS | N/A
```

כל שדה `PASS` נכתב רק אחרי בדיקה של הייצוא/טקסט הסופי עצמו. `visible_text_gate` חייב להיות `PASS` ולהתאים ל־`text_sha256` של הקופי הנוכחי. בווידאו `audio_gate` חייב להיות `PASS`; בסטילס/קרוסלה הוא `N/A`.

**אסור waiver לקריאות/ניגודיות/אודיו/קופי שנשכח.** אישור על בסיס Canva edit/thumbnail או CI בלבד אינו `PASS`. משנים, מייצאים מחדש/מחשבים hashes חדשים ומריצים את השער הרלוונטי מחדש.

שינוי מהותי בכיתוב אחרי lint/Visible Text Gate → invalidated עד gate מחדש. שינוי מהותי בכיתוב, בוויזואל או באודיו אחרי Rubric/PREFLIGHT → `approval_invalidated: true` ומחזירים את השערים הרלוונטיים.

**ו:** עבור / נכשל-סגור

## זכויות / פרטיות — scope

- owner-captured showcase של הדפסה: אין blanket model-license blocker.
- מדיה צד ג׳ / UGC / אדם מזוהה / פרטיות / מגבלה ידועה: gate פעיל.
- explicit public sale/paid promotion של המודל המצולם: מסלול commercial יכול להפעיל בדיקת רישיון מודל.
- זו מדיניות workflow פנימית; אין להסיק ממנה קביעה משפטית על רישיון מסוים.

## שער

`publish_gate: PASS` רק אם כל השערים הרלוונטיים = עבור, `visible_text_gate: PASS` תואם ל־`text_sha256`, `vfcopy_lint: PASS` תואם לאותה גרסה, `fact_gate: PASS`, ה־Rubric ≥20/25, וה־QA של התוצר הסופי עבר. בווידאו נדרש גם `audio_gate: PASS`. אחרת `publish_gate: BLOCKED` / **נכשל-סגור**.
