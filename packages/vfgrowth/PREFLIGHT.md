# פריפלייט פיד / סטוריז — לפני שיבוץ

מושב: **צמיחה + סטודיו**. לא פק חדש.  
נעילה 7.9.2026 ~09:02 (Asia/Jerusalem) — כריסטיאן.  
Visible Text extension: 11.9.2026.  
הכלים תופסים **איכות לפני** שיבוץ / פרסום חי. לא אחרי.

חוקה: `constitution/STUDIO.md` · `constitution/VISIBLE_TEXT.md` · `ORCHESTRA.md` · `SEND.md`.  
שער עריכה: `EDIT-GATE.md`. חוזה קופי חובה: `../vfcopy/SOFT-TOOLS-CONTRACT.md`. קול public: `vfcopy/VOICE.md` + `vfcopy/VOICE-CHART.md`. קומפס/מחקר קול: `vfcopy/VOICE-RESEARCH.md`.  
רובריקת איכות: [`CONTENT-RUBRIC.md`](CONTENT-RUBRIC.md). UGC: [`UGC.md`](UGC.md). מסירה: `HANDOFF-he.md`.  
`PUBLIC_CURRENT_CTA` מוגדר ב־`constitution/PUBLIC_CTA.md`; כשנדרש CTA ציבורי הוא **הודעת Instagram** בניסוח העברי המאושר, וה־intent (`showcase`/`commercial`) קובע אם ואיזה CTA נדרש.

**בלי ארטיפקט כתוב ב־`preflight/<id>.md` עם שער = עבור = לא משבצים.**  
נכשל-סגור → חסום שיבוץ. מתקנים במשרד. **לא** מעבירים לכריסטיאן «רמה נמוכה».

## מה חייב להיות כתוב

| # | בדיקה | עובר רק אם |
|---|---|---|
| א | **Visible Text + SOFT-TOOLS-CONTRACT + VOICE** | כל AI-authored copy שהקהל רואה עבר `public-social` Visible Text Gate על **הגרסה הסופית**: verified context → reader-first → VOICE/VOICE-CHART/`voice/approved/` → relevant vfmskill aids → template → `velvet-hebrew-copy` → `ai-tells-he.md` → `python3 scripts/check-vfcopy.py lint` / surface-aware gate על actual final copy → fact gate. חובה `visible_text_gate=PASS`, `surface`, `text_sha256`/copy digest, ו־`vfcopy_lint=pass` |
| א2 | **Visual microcopy** | אם יש cover/first-frame/overlay/slide text: גם `visual-microcopy` gate, 3–5 candidates + `NO_TEXT`, Creative Director/Brand Guardian, והחלטת `TEXT_WINS` מנומקת או `NO_TEXT`. אם אין טקסט ויזואלי: `N/A` מתועד |
| ב | **Canva / vfcovers** + ראיית ויזואל | `edit_url` אמיתי מ־Canva MCP **או** PNG מ־`vfcovers` / `vfcanva`. לא JPEG גולמי. ראייה: thumbnail/export path או צילום מסך מקומי — לא «נראה טוב» בעל־פה |
| ג | **ציון עצמי מול רף סוכנות** | ביקורת עצמית כתובה. כל שורת רף = כן. לא = נכשל-סגור |
| ד | **VOICE-RESEARCH / קומפס / ייחוד כשנדרש** | בודקים **2–3 קומפס/כיוונים** כשיש טעם אמיתי בהשוואה; מקורות רלוונטיים ומה מאמצים/דוחים; אין חיקוי זהות ואין ספירת עוקבים מומצאת |
| ה | **CONTENT-RUBRIC** | טבלת Rubric מלאה (5 צירים), ≥20/25, בלי 1 ובלי דגל אדום |
| ו | **גרסת תוצר** | `artifact_digest` + `final_package_sha256` + `text_sha256`/copy digest תואמים לגרסאות שאושרו. שינוי קופי אחרי gate/lint מחייב gate מחדש; שינוי מהותי אחרי Rubric/PREFLIGHT מבטל approval |

חסר אחד מהשערים הרלוונטיים = **נכשל-סגור**. אין «כמעט» ואין שיבוץ על תנאי. `needs_input` = חסום עד שהחסר נסגר.

בדיקת מבנה (קיום קבצים) ≠ הוכחת ביצוע. CI/eval של הכלי אינו receipt לקופי ספציפי. `visible_text_gate: PASS` תקף רק אם השרשרת הופעלה על הטקסט המדויק.

## שדות Copy / Visible Text evidence

```yaml
visible_text_gate: PASS | FAIL | UNPROVEN
visible_text_surface: public-social
text_sha256: <64-hex exact final public copy>
truth_checked: PASS | FAIL
reader_first: PASS | FAIL
copy_authority: PASS | FAIL
humanizer_ai_tells: PASS | FAIL
vfcopy_lint: PASS | FAIL | NEEDS_INPUT
vfcopy_lint_surface: public-social
fact_gate: PASS | NEEDS_INPUT | FAIL
marketing_aids:
  copywriting: APPLIED | N/A
  copy-editing: APPLIED | N/A
  marketing-psychology: APPLIED | N/A
visual_text_gate: PASS | N/A
visual_copy_decision: TEXT_WINS | NO_TEXT | N/A
visual_text_sha256: <64-hex | N/A>
```

`N/A` לכלי/שלב מותר רק כשהוא באמת לא רלוונטי למשטח, ורצוי עם סיבה קצרה. מקור הכלל: `vfcopy/SOFT-TOOLS-CONTRACT.md`.

## ציון עצמי — רף סוכנות יקרה

כותבים כן/לא. לא ממציאים Insights. לא ממציאים ₪.

1. סוכנות פרסום יקרה הייתה שולחת את הפריים והכיתוב כמו שהם?
2. `visible_text_gate: PASS` ו־`text_sha256` שייכים לקופי **הסופי** שנמצא בחבילה?
3. אם יש טקסט על ויזואל: הוא עבר `visual-microcopy` + `NO_TEXT` comparison, והאם הוא באמת מוסיף פואנטה?
4. הוויזואל עבר `EDIT-GATE.md` וכל בדיקות Brand Guardian הרלוונטיות?
5. נבחנו 2–3 קומפס/כיוונים כשזה רלוונטי, או תועד למה אין צורך?
6. אין ₪/מק״ט/לקוח/Insights/claim מומצאים; media/version/publication states תקינים.
7. CTA/intent תואמים `PUBLIC_CURRENT_CTA` / `PUBLIC_CTA.md` ולסוג הפוסט; private-contact rules לא דולפים לפיד.

לא אחד = נכשל-סגור. מתקנים במשרד.

## VOICE-RESEARCH / קומפס / ייחוד

רק מקור אמיתי שנבדק או היסטוריית feed/Visual OS. `VOICE-RESEARCH.md` הוא מקור ההשוואה הקנוני כשעושים קומפס קופי. כשנדרשת השוואה, בוחנים 2–3 קומפס/כיוונים אמיתיים ומנסחים מה מאמצים ומה דוחים; לא משכפלים זהות חיצונית. אין ספירת עוקבים/“#1”/handle מומצא.

## נכשל-סגור — לא למעלה

| עושים במשרד | אסור על משטח כריסטיאן / ראש צוות |
|---|---|
| חסום שיבוץ ב־`HANDOFF-he.md` | «רמה נמוכה» |
| תיקון copy chain / Canva / audio / evidence באותו תור | דוח בושה «לא השתמשתם בכלים» |
| `UNPROVEN` כשאין receipt אמיתי | להפוך ידנית ל־PASS |
| מדדים חלשים — לוג פנימי בלבד | פינג בצ׳אט על Insights חלשים |

**אל תפנה לכריסטיאן על מדדים חלשים**; הם נשארים evidence פנימי ללמידה אלא אם הם דורשים החלטה/חסם אמיתי. משטח אליו: **החלטה** · **חסם קשיח** · **פרסום חי שדורש אותו בלבד**.

## ארטיפקט

נתיב חובה לפני שיבוץ:

```
packages/vfgrowth/preflight/<G00X-or-sku>.md
```

העתק מ־`preflight/TEMPLATE.md`. `vfops_loop.py handoff` מדפיס את הנתיב. בלי נתיב + שער PASS = השורה נשארת חסומה.

אין Publish מכאן. אין ₪ מכירה מומצא. אין Insights מומצאים.

מפעל אורגני (`ORGANIC_GROWTH.md`): אחרי PREFLIGHT — `policy_checked` ואז תור. אישור אדם ≠ פרסום.
