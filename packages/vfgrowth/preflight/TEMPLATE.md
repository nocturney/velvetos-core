# פריפלייט · {{ID}}

## VF_PUBLICATION_ROUTE_V1 - current publication scope

For Velvet Factory publication tasks, use `packages/vfom/PUBLICATION-PREP-EXECUTION.md` and the `publicationRoute` in `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json`. Canva/vfcanva are forbidden in this scope; provider notes labelled LEGACY below are not executable routes for VF. Other businesses and non-publication uses are unchanged.
Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

תאריך (Asia/Jerusalem):  
פורמט: סטוריז / פיד / קרוסלה / ריל  
מושב: צמיחה + סטודיו  
שער: **חסום** עד כל השערים הרלוונטיים עוברים.

מחיר בפריים/כיתוב: `X ₪` או אין. בלי ₪ מומצא.  
CTA public: לפי `constitution/PUBLIC_CTA.md` / `PUBLIC_CURRENT_CTA` — **הודעה באינסטגרם** כשנדרש; בלי WhatsApp/טלפון ציבורי. Showcase יכול לבחור CTA ניטרלי/ללא CTA לפי intent הפעיל.  
חוזה טקסט: `constitution/VISIBLE_TEXT.md` + `packages/vfcopy/SOFT-TOOLS-CONTRACT.md`. רובריקה: `CONTENT-RUBRIC.md`.  
מותג: `packages/vfbrand/BRAND-SOURCE-OF-TRUTH.md`.

> LEGACY / provenance only for VF publication; not a provider route: > Publish contract v3: כל קובץ ב־Velvet Media הוא RAW. crop/resize/format/normalization בלבד אינם creative treatment. מוצר אמיתי חייב לעבור Product Truth: מותר לשפר את הצילום, אסור לשנות את האובייקט. אישור תוכן כללי או Canva edit אינו אישור לפרסום; השער חייב להיות מחובר ל־**תוצר הסופי המרונדר המדויק** ולגרסת הקופי המדויקת שעברה Visible Text Gate + lint.

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

## ב · RAW → Creative + Product Truth

```yaml
source_material_state: RAW
creative_treatment: FAIL
brand_treatment: FAIL
commercial_visual_qa: FAIL
scroll_stop_qa: FAIL
derivative_is_distinct_from_source: FAIL
product_truth_gate: FAIL
subject_identity_integrity: FAIL
synthetic_subject_change: NONE | PRESENT
source_subject_match: FAIL
brand_source_lock: FAIL
creative_treatment_categories: <comma-separated; at least 3 real categories>
creative_edit_evidence: <real edit/export/review path or id>
```

קטגוריות creative תקפות: `composition`, `cleanup`, `background`, `lighting`, `color_grade`, `subject_separation`, `retouch`, `brand_system`, `typography`, `motion`, `audio`.

`crop`, `resize`, ratio, format conversion, metadata strip, compression, normalization וסידור שקופיות הם technical-only ואינם נספרים כטיפול קריאייטיבי.

Product Truth למוצר אמיתי:
- אותו אובייקט פיזי חייב להישאר זהה בין RAW ל־final.
- `synthetic_subject_change: NONE` חובה.
- אין שינוי geometry, silhouette, proportions, part count, visible surface pattern או product identity.
- background/cleanup מותר רק אם אינו משנה את המוצר ואינו יוצר claim מומצא.
- master brand asset בלבד; אין לוגו מומצא ואין palette משוער כשקיים SVG מאושר.

- כלי/יכולת עריכה: <capability actually used; no provider shortcut>
- `creative_edit_evidence`: <real artifact/review/export reference>
- ראייה של RAW / source refs:
- ראייה של exact final:
- מה השתנה מעבר ל־crop/resize:
- איך נשמרה זהות המוצר:
- האם final תואם את הרפרנסים המאושרים ואת Brand Source of Truth:
- JPEG גולמי / crop-only / synthetic subject? כן=נכשל

**ב:** עבור / נכשל-סגור

## ג · ציון עצמי · רף סוכנות

| שאלה | כן/לא |
|---|---|
| סוכנות יקרה הייתה שולחת כמו שזה? | |
| `visible_text_gate: PASS` תואם לקופי הסופי? | |
| אם יש visual text — הוא מנצח `NO_TEXT` או שנבחר `NO_TEXT`? | |
| הוויזואל עבר RAW→Creative EDIT-GATE? | |
| המוצר ב־final הוא אותו מוצר פיזי שב־RAW? | |
| אין synthetic subject change? | |
| נעשה שימוש בלוגו/שפה מה־Brand Source of Truth? | |
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
- `visual_id` / `creative_edit_evidence`:
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
visual_standard_gate: FAIL
visual_standard_document: packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md
> LEGACY / provenance only for VF publication; not a provider route: visual_standard_canva_asset_id: MAHVL7PKpvE
visual_standard_artifact_sha256: df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897
product_truth_source_refs: <real source refs>
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
product_truth_gate: FAIL
subject_identity_integrity: FAIL
synthetic_subject_change: PRESENT
source_subject_match: FAIL
brand_source_lock: FAIL
creative_treatment_categories: <at least 3 real categories>
creative_edit_evidence: <real evidence>
visual_edit_performed: FAIL
creative_delta_gate: FAIL
raw_passthrough: true
source_edit_mode: <SOURCE_IMAGE_EDIT | DETERMINISTIC_COMPOSITE | VIDEO_EDIT | N/A>
hero_transformation_evidence: <final artifact ref + visible presentation changes>
visual_output_evidence: <real edited artifact ref>
exact_final_visual_qa: FAIL
public_cta_gate: FAIL
brand_asset_gate: FAIL
generated_brand_mark: PRESENT
logo_usage: NONE
logo_source_ref: NONE
logo_render_method: NONE
public_phone_absent: FAIL
audio_gate: FAIL | PASS | N/A
```

כל שדה `PASS` נכתב רק אחרי בדיקה של הייצוא/טקסט הסופי עצמו. שינוי מהותי בכיתוב, בוויזואל או באודיו אחרי PASS מבטל את ה־PASS ומחייב gate מחדש.

**ו:** עבור / נכשל-סגור

## זכויות / פרטיות — scope

- owner-captured showcase של הדפסה: אין blanket model-license blocker.
- מדיה צד ג׳ / UGC / אדם מזוהה / פרטיות / מגבלה ידועה: gate פעיל.
- explicit public sale/paid promotion של המודל המצולם: מסלול commercial יכול להפעיל בדיקת רישיון מודל.

## שער

`publish_gate: PASS` רק אם כל השערים הרלוונטיים = עבור, `visible_text_gate: PASS` תואם ל־`text_sha256`, `vfcopy_lint: PASS`, `fact_gate: PASS`, ה־Rubric ≥20/25, RAW→Creative עבר, Product Truth עבר (`product_truth_gate: PASS`, `subject_identity_integrity: PASS`, `synthetic_subject_change: NONE`, `source_subject_match: PASS`) ו־`brand_source_lock: PASS`. בווידאו נדרש גם `audio_gate: PASS`. אחרת `publish_gate: BLOCKED`.

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

> LEGACY / provenance only for VF publication; not a provider route: This execution surface is inside the Velvet Factory creative/publish path. Before concept, edit, render, handoff or publish, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`; verify Canva asset `MAHVL7PKpvE` and SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`; require `visual_standard_gate=PASS`. Missing/mismatched evidence is `visual_standard_unavailable` and blocks the branch. Generic/default visual fallback is forbidden. Product Truth from real source media overrides style.

## Required evidence extension v1

```yaml
creative_manifest_ref: <workspace-relative Creative Manifest JSON>
creative_manifest_sha256: <64-hex SHA-256 of the exact approved Creative Manifest bytes>
reference_match_gate: UNPROVEN
creative_director_lock: UNPROVEN
```

Fill publicationEvidence using `packages/vfom/publication-evidence.TEMPLATE.json`. Never copy PASS flags from an example. Actual files and review/lint receipts must match their digests. Policy or output changes invalidate the binding. Run the production and delivery gates; image review remains mandatory.
