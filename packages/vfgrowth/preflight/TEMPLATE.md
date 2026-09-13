# פריפלייט · {{ID}}

תאריך (Asia/Jerusalem):  
פורמט: סטוריז / פיד / קרוסלה / ריל  
מושב: צמיחה + סטודיו  
שער: **חסום** עד כל השערים הרלוונטיים עוברים.

מחיר בפריים/כיתוב: `X ₪` או אין. בלי ₪ מומצא.  
CTA public: לפי `constitution/PUBLIC_CTA.md` / `PUBLIC_CURRENT_CTA` — **הודעה באינסטגרם** כשנדרש; בלי WhatsApp/טלפון ציבורי. Showcase יכול לבחור CTA ניטרלי/ללא CTA לפי intent הפעיל.  
חוזה טקסט: `constitution/VISIBLE_TEXT.md` + `packages/vfcopy/SOFT-TOOLS-CONTRACT.md`. רובריקה: `CONTENT-RUBRIC.md`.

> Publish contract v3: כל קובץ ב־Velvet Media הוא RAW. crop/resize/format/normalization בלבד אינם creative treatment. אישור תוכן כללי או Canva edit אינו אישור לפרסום; השער חייב להיות מחובר ל־**תוצר הסופי המרונדר המדויק** ולגרסת הקופי המדויקת שעברה Visible Text Gate + lint.

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

**א:** עבור / נכשל-סגור

## ב · RAW → Creative / ראיית ויזואל

```yaml
source_material_state: RAW
creative_treatment: FAIL
brand_treatment: FAIL
commercial_visual_qa: FAIL
scroll_stop_qa: FAIL
derivative_is_distinct_from_source: FAIL
creative_treatment_categories: <comma-separated; at least 3 real categories>
creative_edit_evidence: <real edit/export/review path or id>
```

קטגוריות creative תקפות: `composition`, `cleanup`, `background`, `lighting`, `color_grade`, `subject_separation`, `retouch`, `brand_system`, `typography`, `motion`, `audio`.

`crop`, `resize`, ratio, format conversion, metadata strip, compression, normalization וסידור שקופיות הם technical-only ואינם נספרים כטיפול קריאייטיבי.

- כלי: Canva MCP / vfcovers / vfcanva / Superdesign→render.py
- `edit_url` או נתיב PNG/JPEG מורכב אמיתי:
- ראייה של RAW:
- ראייה של exact final:
- מה השתנה מעבר ל־crop/resize:
- האם final מרגיש Velvet גם ב־NO_TEXT:
- JPEG גולמי / crop-only? כן=נכשל

**ב:** עבור / נכשל-סגור

## ג · ציון עצמי · רף סוכנות

| שאלה | כן/לא |
|---|---|
| סוכנות יקרה הייתה שולחת כמו שזה? | |
| `visible_text_gate: PASS` תואם לקופי הסופי? | |
| אם יש visual text — הוא מנצח `NO_TEXT` או שנבחר `NO_TEXT`? | |
| הוויזואל עבר RAW→Creative EDIT-GATE? | |
| ה־final מושך עין גם בלי לקרוא caption? | |
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

### שדות Publish Gate v3 — חובה לפני Instagram publish

```yaml
publish_gate_schema: 3
publish_gate: BLOCKED
approval_invalidated: false
source_material_state: RAW
qa_scope: exact-final-render
qa_reviewed_at: <ISO-8601>
content_rubric_total: <NN/25>
artifact_digest: sha256:<64-hex>
final_package_sha256: <64-hex>
visible_text_gate: FAIL
fact_gate: FAIL
brand_guardian: FAIL
copy_qa: FAIL
readability: FAIL
contrast: FAIL
creative_treatment: FAIL
brand_treatment: FAIL
commercial_visual_qa: FAIL
scroll_stop_qa: FAIL
derivative_is_distinct_from_source: FAIL
creative_treatment_categories: <at least 3 real categories>
creative_edit_evidence: <real evidence>
audio_gate: FAIL | PASS | N/A
```

כל שדה `PASS` נכתב רק אחרי בדיקה של הייצוא/טקסט הסופי עצמו. שינוי מהותי בכיתוב, בוויזואל או באודיו אחרי PASS מבטל את ה־PASS ומחייב gate מחדש.

**ו:** עבור / נכשל-סגור

## זכויות / פרטיות — scope

- owner-captured showcase של הדפסה: אין blanket model-license blocker.
- מדיה צד ג׳ / UGC / אדם מזוהה / פרטיות / מגבלה ידועה: gate פעיל.
- explicit public sale/paid promotion של המודל המצולם: מסלול commercial יכול להפעיל בדיקת רישיון מודל.

## שער

`publish_gate: PASS` רק אם כל השערים הרלוונטיים = עבור, `visible_text_gate: PASS` תואם ל־`text_sha256`, `vfcopy_lint: PASS`, `fact_gate: PASS`, ה־Rubric ≥20/25, וכל חמשת שערי RAW→Creative עברו. בווידאו נדרש גם `audio_gate: PASS`. אחרת `publish_gate: BLOCKED`.
