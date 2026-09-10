# שער עריכה — לפני שיבוץ / Publish

מושב: **סטודיו**. לא פק חדש.  
חוקה: `constitution/STUDIO.md`. מסירה: `HANDOFF-he.md`.  
פריפלייט כתוב (חובה): [`PREFLIGHT.md`](PREFLIGHT.md). חוזה קופי ציבורי חובה: `../vfcopy/SOFT-TOOLS-CONTRACT.md`. בלי ארטיפקט `preflight/<id>.md` = **נכשל-סגור**.

**אסור** לשבץ או לפרסם JPEG גולמי עם טקסט מעליו בלבד (טקסט-על-קובץ-רצפה).  
**חובה** לעבור כלי עריכה אמיתי **ו** את שרשרת הקופי המלאה. `VOICE.md` בלבד אינו gate. בלי קישור עריכה / PNG מורכב / `vfcopy_lint=pass` על גרסת הקופי הנוכחית = **לא משבצים**.  
צמיחה רשאית לרשום Insights חלשים בלוג פנימי. **אל תפנה לכריסטיאן על מדדים חלשים.** אין «רמה נמוכה» לצ׳אט.

## כלים מותרים (לפי סדר)

| סדר | כלי | איפה | מה נחשב עבר שער |
|---|---|---|---|
| 1 | **Canva MCP** (`generate-design` / `canva-edit-design`) | Cloud + Desktop | `edit_url` אמיתי מ־MCP |
| 2 | **vfcovers / vfcanva** | Cloud | `compose_slides.py` או `packages/vfcanva/studio/render.py` → PNG |
| 3 | **Gemini browser** (עריכת תמונה) | **מק בשדרות בלבד** — `vfmcp/HOST.md` | קובץ ערוך מהמק. Cloud **לא** פותח `gemini.google.com` |
| 4 | Failover | Cloud | Superdesign → אם נפל: `studio/render.py` |

## שער קופי מחייב

כל caption / Reel / Story / carousel / cover / first-frame / overlay ציבורי הוא גלם עד שעבר את `packages/vfcopy/SOFT-TOOLS-CONTRACT.md` על הגרסה הסופית:

`verified context → reader-first → VOICE + VOICE-CHART + voice/approved → template → velvet-hebrew-copy → ai-tells-he → check-vfcopy.py lint(actual final copy) → factual gate → TEXT_WINS/NO_TEXT (אם רלוונטי)`.

Brand Guardian, Rubric, Canva, אישור אדם או CI/eval אינם תחליף לשער זה. שינוי טקסט אחרי lint מבטל את ה־pass ומחייב lint מחדש; שינוי מהותי אחרי PREFLIGHT/Rubric מחייב גם אותם מחדש.

## מה לא עובר

- JPEG מהמיטה / מתיבת Grok עם כיתוב רק בפריים האינסטגרם
- טקסט מודבק על הקובץ הגולמי בלי Canva / compose / render
- קישור Canva מומצא
- סצנת רצפה שלא נמסרה
- קופי שלא עבר `SOFT-TOOLS-CONTRACT.md` על הגרסה הנוכחית
- `needs_input`/fact gate לא פתור
- ₪ בפריים · וואטסאפ / `050-2517000` / `wa.me` כ־CTA ציבורי כשאסור לפי החוקה · אוטו־DM
- **סטוריז או פיד** בלי `edit_url` מ-Canva MCP או PNG מ-`vfcovers` / `vfcanva`
- סטוריז מוצר במצב תהליך-קצר / הוק מגבלה («לא משקולת», «בלי משלוח»)
- מדיה AI / נגזרת מהותית בלי metadata להצהרת פלטפורמה כשנדרש
- שיבוץ בלי `versionApproval` כשיש פריט כספת · או claim live בלי אימות

גלם בתיבת Grok (G004) = חומר גלם. אחרי שער העריכה **ואחרי** `preflight/G004.md` עבור — ורק אז — שיבוץ instagram.com / Calendar.  
סטוריז G004: `packages/vfcopy/G004-STORIES-FIX.md` + `STORIES.md`.

סטוריז = `publish_story` על Instagram MCP הקנוני אחרי Canva/vfcovers (לא JPEG גולמי). נכשל-סגור = חסום שיבוץ, תיקון במשרד — לא הסלמה לכריסטיאן.

כל טקסט לסטוריז/פיד חייב להגיע דרך `packages/vfcopy`. כיתובים שנכתבו מחוץ ל-vfcopy נחשבים גלם עד שיועברו דרך החוזה ויעברו lint על הטקסט הסופי.  
לפני שיבוץ: `PREFLIGHT.md` + `CONTENT-RUBRIC.md` (≥20/25) + ראיית ויזואל + digest גרסה. בדיקת מבנה בלבד אינה שיפוט עיצוב.
