# שער עריכה — לפני שיבוץ / Publish

מושב: **סטודיו**. לא פק חדש.  
חוקה: `constitution/STUDIO.md`. מסירה: `HANDOFF-he.md`.  
פריפלייט כתוב (חובה): [`PREFLIGHT.md`](PREFLIGHT.md). חוזה קופי ציבורי חובה: `../vfcopy/SOFT-TOOLS-CONTRACT.md`. בלי ארטיפקט `preflight/<id>.md` = **נכשל-סגור**.  
מקור אמת למותג: [`../vfbrand/BRAND-SOURCE-OF-TRUTH.md`](../vfbrand/BRAND-SOURCE-OF-TRUTH.md).

## חוק RAW מחייב

**כל חומר שנכנס ל־Velvet Media הוא RAW INPUT.** מיקום בתיקייה, שם קובץ, crop קיים או איכות צילום אינם הוכחת עריכה, מיתוג או אישור. גם קובץ בשם `final`, `post`, `cover` או דומה נשאר RAW עד שנוצרה ממנו נגזרת קריאייטיבית ונבדקה.

`crop` / `resize` / שינוי ratio / format conversion / metadata strip / compression / normalization / שינוי סדר שקופיות הם **טרנספורמציות טכניות בלבד**. הם לעולם אינם מספיקים לבדם כדי לעבור את שער העריכה.

לפני `ready_for_publish` חייבת להתקיים נגזרת ברורה ונפרדת מן המקור, עם טיפול קריאייטיבי אמיתי בהתאם לחומר: לפחות שלושה מתחומי `composition`, `cleanup`, `background`, `lighting`, `color_grade`, `subject_separation`, `retouch`, `brand_system`, `typography`, `motion`, `audio`. לא כל תחום נדרש בכל נכס; אבל crop/resize בלבד = FAIL.

## Product Truth — חובה לפני כל תוכן מוצר אמיתי

עיצוב יפה אינו רשאי לשנות את האובייקט שאנו מציגים למכירה או כ־showcase.

```yaml
product_truth_gate: FAIL
subject_identity_integrity: FAIL
synthetic_subject_change: NONE | PRESENT
source_subject_match: FAIL
brand_source_lock: FAIL
```

כללים:

- `product_truth_gate: PASS` רק אם ה־final מציג את אותו אובייקט פיזי שנראה ב־RAW המאושר.
- `subject_identity_integrity: PASS` דורש שמירה על silhouette, geometry, proportions, part count, visible surface pattern ו־identity של המוצר.
- `synthetic_subject_change` חייב להיות `NONE` לכל פוסט/קרוסלה/סטורי/cover שמייצג מוצר אמיתי.
- AI/Generative Fill מותר לכל היותר לסביבת הצילום/רקע כאשר האובייקט עצמו נשמר בדיוק, ואסור להשתמש ברקע מומצא כהוכחת שימוש/קנה־מידה/עמידות/סביבה.
- אם אי אפשר להשוות את ה־final ל־RAW ולהראות שזה אותו מוצר — **FAIL**.
- מקור אמת למותג הוא `packages/vfbrand/BRAND-SOURCE-OF-TRUTH.md`. אין להמציא VF mark, אין orange default, ואין palette משוער כאשר קיים master SVG.

**אסור** לשבץ או לפרסם JPEG גולמי עם טקסט מעליו בלבד, JPEG גולמי שנחתך ל־4:5 בלבד, או AI render שמחליף/משנה את המוצר האמיתי.  
**חובה** לעבור כלי עריכה אמיתי **ו** את שרשרת הקופי המלאה. `VOICE.md` בלבד אינו gate. בלי קישור עריכה / PNG-JPEG מורכב / evidence לנגזרת / `vfcopy_lint=pass` על גרסת הקופי הנוכחית = **לא משבצים**.

## מה נבדק על ה־exact final

ה־PREFLIGHT חייב להוכיח על הייצוא הסופי עצמו:

- `creative_treatment: PASS`
- `brand_treatment: PASS`
- `commercial_visual_qa: PASS`
- `scroll_stop_qa: PASS`
- `derivative_is_distinct_from_source: PASS` — distinct בפרזנטציה, **לא בזהות המוצר**
- `product_truth_gate: PASS`
- `subject_identity_integrity: PASS`
- `synthetic_subject_change: NONE`
- `source_subject_match: PASS`
- `brand_source_lock: PASS`
- `creative_treatment_categories`: לפחות שלושה טיפולים אמיתיים, לא technical-only
- `creative_edit_evidence`: מזהה/נתיב אמיתי לנגזרת ולביקורת שלה
- השוואת RAW → derivative: האם הקומפוזיציה, הניקוי, הטון וההיררכיה השתפרו בלי לשנות את המוצר

`NO_TEXT` הוא החלטת visual-copy לגיטימית, אבל **לא** פוטר מטיפול מותגי. גם תמונה נקייה ללא טקסט חייבת להרגיש מכוונת, עקבית ומוכנה מסחרית.

## כלים מותרים (לפי סדר)

| סדר | כלי | איפה | מה נחשב עבר שער |
|---|---|---|---|
| 1 | **Canva MCP** | Cloud + Desktop | `edit_url` אמיתי + exact-final visual review + subject integrity |
| 2 | **vfcovers / vfcanva** | Cloud | PNG/JPEG + evidence לטיפול מעבר ל-crop + source/final comparison |
| 3 | **Gemini browser** (עריכת תמונה) | **מק בשדרות בלבד** — `vfmcp/HOST.md` | קובץ ערוך מהמק + exact-final QA + no subject mutation |
| 4 | Failover | Cloud | Superdesign → אם נפל: `studio/render.py` + exact-final QA |

### שימוש ב־AI בתמונות מוצר

- אסור image generation כתחליף לצילום המוצר האמיתי.
- אסור subject stylization / replacement / regeneration כאשר התוצר אמור לייצג מוצר קיים.
- מותר cleanup/background assistance רק כאשר נשמרת זהות המוצר; אם הכלי אינו יכול להבטיח זאת, עוברים לעריכה לא־גנרטיבית.

## שער קופי מחייב

כל caption / Reel / Story / carousel / cover / first-frame / overlay ציבורי הוא גלם עד שעבר את `packages/vfcopy/SOFT-TOOLS-CONTRACT.md` על הגרסה הסופית:

`verified context → reader-first → VOICE + VOICE-CHART + voice/approved → template → velvet-hebrew-copy → ai-tells-he → check-vfcopy.py lint(actual final copy) → factual gate → TEXT_WINS/NO_TEXT (אם רלוונטי)`.

Brand Guardian, Rubric, Canva, אישור אדם או CI/eval אינם תחליף לשער זה. שינוי טקסט אחרי lint מבטל את ה־pass ומחייב lint מחדש; שינוי מהותי אחרי PREFLIGHT/Rubric מחייב גם אותם מחדש.

## מה לא עובר

- כל נכס שיצא ישירות מ־`01 - נכנס` / `02 - מקור` לפרסום
- crop/resize/format/normalization בלבד
- AI/generated render שמחליף את המוצר המצולם או משנה geometry/surface/detail
- מוצר שנראה טוב יותר בתמונה אך אינו יכול להתקבל מה־RAW כאותו אובייקט
- לוגו VF מומצא/מחודש במקום master asset
- orange כ־brand default בניגוד ל־Brand Source of Truth
- JPEG מהמיטה / מתיבת Grok עם כיתוב רק בפריים האינסטגרם
- טקסט מודבק על הקובץ הגולמי בלי Canva / compose / render
- קישור Canva מומצא
- סצנת רצפה שלא נמסרה
- קופי שלא עבר `SOFT-TOOLS-CONTRACT.md` על הגרסה הנוכחית
- `needs_input`/fact gate לא פתור
- ₪ בפריים · וואטסאפ / `050-2517000` / `wa.me` כ־CTA ציבורי כשאסור לפי החוקה · אוטו־DM
- **סטוריז או פיד** בלי `edit_url` מ-Canva MCP או PNG/JPEG מורכב מ-`vfcovers` / `vfcanva`
- מדיה AI / נגזרת מהותית בלי metadata להצהרת פלטפורמה כשנדרש
- שיבוץ בלי `versionApproval` כשיש פריט כספת · או claim live בלי אימות
- `brand_guardian: PASS` שמבוסס על sharpness/crop/reality בלבד בלי commercial/scroll-stop/product-truth review

כל טקסט לסטוריז/פיד חייב להגיע דרך `packages/vfcopy`. כיתובים שנכתבו מחוץ ל-vfcopy נחשבים גלם עד שיועברו דרך החוזה ויעברו lint על הטקסט הסופי.  
לפני שיבוץ: `PREFLIGHT.md` + `CONTENT-RUBRIC.md` (≥20/25) + ראיית RAW/final + digest גרסה. בדיקת מבנה בלבד אינה שיפוט עיצוב.
