# vfmskill — איך מטמיעים

חמישה עשר כישורים מ־[coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills). כל כישור הוא נוהל משרד על פק קיים, לא מוצר חדש.

אם Agency desk כבר ממוזג, אפשר גם `@content-creator` / `@instagram-curator` / `@sales-engineer`. הכישורים כאן לא תלויים בזה.

קודם תמיד: `.agents/product-marketing.md`. אם חסר שדה — «חסר», לא המצאה.

## 1. קופי — `copywriting` + `copy-editing` + `marketing-psychology`

**מהספרייה:** מסגרות בהירות, לינט, שפה של לקוח.

**אצלנו:**

1. כל קופי ציבורי מתחיל מ־`packages/vfcopy/SOFT-TOOLS-CONTRACT.md`; vfmskill הוא שכבת מתודולוגיה בתוך השרשרת ולא מסלול מקביל.
2. קרא `packages/vfcopy/hq/PLAYBOOK.md`, `hq/reader-first-he.md` לפני טיוטה, `VOICE.md` + `VOICE-CHART.md` + `voice/approved/`, ואת `hq/ai-tells-he.md` לפני final.
3. הפעל `copywriting` + `marketing-psychology` בזמן framing/draft ו־`copy-editing` לפני final, ואז העבר דרך `velvet-hebrew-copy` ו־`python3 scripts/check-vfcopy.py lint` על הטקסט הסופי עם context מאומת.
4. CTA לפי `constitution/PUBLIC_CTA.md`; אין להעתיק CTA מה־vendor. אין ₪ בלי מקור, אין הבטחת זמן בלי verification, אין customer/Insights claim בלי proof.
5. טיוטה שנכתבה כאן נשארת raw candidate עד שעברה fact gate, CONTENT-RUBRIC ו־PREFLIGHT במסלול הקנוני.

## 2. תוכן ואינסטגרם — `social` + `content-strategy` + `video` + `image`

**מהספרייה:** עמודי תוכן, ריל, גרפיקה, לוח.

**אצלנו:**

1. חומר רק מעבודה גמורה / קובץ Drive שהמשתמש נקב. חסר הוכחה = חלקי.
2. ריל/סטורי/קרוסלה עוברים דרך `.cursor/skills/vf-content-sprint/SKILL.md`; כל טקסט ציבורי שם כפוף ל־`vfcopy/SOFT-TOOLS-CONTRACT.md`.
3. כריכה ב־`vfcovers` / `vfcanva`. Superdesign רק אם Canva לא מחובר.
4. `vfigos` סוקר/שולח רק אחרי gates הקנוניים; אין claim live בלי tool receipt + verification.
5. בלי TikTok, בוסט, follow-back, או צפיית־סטורי כטריק.

## 3. פנייה והצעה — `customer-research` + `offers` + `sales-enablement`

**מהספרייה:** VOC, בניית הצעה, נספחי מכירה.

**אצלנו:**

1. שלף משרשור: חומר, כמות, מתי, גימור. חסר → שאלת אדם לוואטסאפ.
2. מסלול: `vfconvert` → `vfprod` → `vfcost` → `vfsales` + `vfcopy`.
3. ₪ רק אחרי ראש צוות. אחרת `X ₪`. אין AutoQuote.
4. עצור. אדם שולח + Invoice4U.

## 4. מחקר ותוכנית — `competitor-profiling` + `marketing-ideas` + `marketing-plan` + `launch`

**מהספרייה:** פרופיל מתחרה, רעיונות, תוכנית, השקה.

**אצלנו:**

1. מקורות עם קישור או שם קובץ HQ. אין קישור = «חסר».
2. מספרי עוקבים / Insights רק ממקור שראית. אחרת ריק.
3. השקת מק״ט: `vlicense` לפני קטלוג. `vfseason` לפני באצ׳ עונתי.
4. B2B כקו נעול עד שראש צוות פותח. לוגו / QR / מפיות = דוגמאות, לא קטלוג סגור.

## 5. בסיס — `product-marketing`

המסמך ב־`.agents/product-marketing.md` הוא ההקשר שכל כישור למעלה קורא קודם.

עדכון רק בעובדות מהמשרד (חוקה, פקים, שרשור שצוין). אין למלא הוכחות, ₪, או Insights מהאוויר.

## SaaS / מודעות / אתר — לא עכשיו

`ads`, `emails`, `pricing`, `cro`, `seo-audit` וכל ה־skip ב־`LOCK.md`. רק אם ראש צוות פותח.

## בדיקה

```bash
python3 scripts/check-vfmskill.py
python3 scripts/check-soft-tools-pipeline.py
```

אין UI חי. אין דפדפן לאמת שליחה. העקביות היא מול הנעילות, החוקה, ה־manifest וה־copy/preflight evidence.
