# vfdsh — איך מטמיעים

חמישה צוותים. כל צוות הוא נוהל משרד, לא התקנת `dsh`. מקור הרעיון: [awesome-dsh-plugin](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin). הביצוע: הפאקים שכבר יש.

אם Agency desk כבר ממוזג, אפשר גם `@studio-producer` / `@bookkeeper-controller`. הצוותים כאן לא תלויים בזה.

## 1. ראיית רצפה — `crews/floor-vision.md`

**מהרשימה:** Modlens (OCR + layout כעדות JSON), Vision Toolkit / PictureReader (קריאת תמונה לטקסט), pbr-render (תצוגת GLB/GLTF), phone-lens כדפוס קלט בלבד.

**אצלנו:**

1. קרא רק קובץ / Drive / צילום שהמשתמש נקב בשמו. אין סצנת רצפה מומצאת.
2. רשום מה נראה: חומר, צבע, הצמדה, פגם. אם לא נראה — «לא נראה בתמונה».
3. STL / GLB: הערות מקובץ או מסלייסר. אין הבטחת מיטה בלי שם אמיתי.
4. רישיון לפני הדפסה חוזרת → `vlicense`.
5. עצור. אדם מחליט אם מדפיסים.

## 2. מסמכים בתיבה — `crews/inbox-docs.md`

**מהרשימה:** MinerU (PDF/Office → Markdown), dsh-attachment-formats, dsh-pdf, DSH-Office / dsh-cowork (קריאה מוגבלת).

**אצלנו:**

1. Gmail קריאה בלבד (`nocturney@gmail.com`) או קובץ שצוין. אל תשלח.
2. שלוף מהמסמך: ספק, תאריך, מספר חשבונית, סכום **רק אם כתוב**. אחרת «אין במקור».
3. פנייה / מידות / גימור חסרים → שאלת אדם לוואטסאפ.
4. ₪ מכירה רק אחרי ראש צוות.

## 3. זיכרון קטלוג — `crews/catalog-memory.md`

**מהרשימה:** Engramory (עובדה לקובץ Markdown), MemSearch / Co-Engram (Markdown ב-git), dsh-project-memory (ציטוט מקור + BM25), WeKnora כדפוס KB בניהול המשתמש.

**אצלנו:**

1. הזיכרון הוא עצי הפאקים + CHANGELOG. אין שרת OpenViking/MemOS מ-HQ.
2. כל טענה → נתיב קובץ או קישור. אין מקור → «חסר».
3. כתיבה לקטלוג רק כהערת אדם / ראש צוות ביקש. לא ממציאים SKU.

## 4. לוח צינור — `crews/pipeline-board.md`

**מהרשימה:** dsh_workflow (שמור / נשלט / ניתן לחידוש), DSH Taskboard (הסוכן מגיש רק ל-in_review), verification gate (עדות לפני סיום), tech-lead (כלים לקריאה), dsh-kanban, dsh-ambiguity-handling.

**אצלנו:**

1. עמודות: פנייה → שיחה → הצעה → הדפסה → איסוף.
2. חסר חומר / כמות / מתי / גימור → לא מנחשים. שואלים.
3. «בוצע» רק עם עדות: נושא מייל, שם קובץ, סימן יומן. בלי עדות → נשאר ב-review.
4. אין הקצאת מדפסת מ-HQ.

## 5. נכסי עיצוב / תלת-ממד — `crews/design-assets.md`

**מהרשימה:** Superdesign skill (כבר על השולחן), TongFlow (זרימות תמונה/תלת-ממד שמורות), iPolloWork / deepseek-idesign (סטודיו ויזואלי), WaveSpeed 3D כ-SaaS אחר כך.

**אצלנו:**

1. `vfcopy` → טיוטה. `vfcovers` / `vfcanva` → כיסוי. `vfigos` → סקירה/תזמון.
2. Canva אם מחובר. אם לא: `Canva לא מחובר` + `packages/vfcanva/CONNECT.md`.
3. אין סצנת רצפה מומצאת על הגרפיקה. אין Insights על השקף.
4. HQ לא שולח. Grok משבץ.

## SaaS / תוסף DSH אחר כך (לא עכשיו)

OpenViking, WeKnora server, TongFlow runtime, WaveSpeed, dsh-market — רק אם ראש צוות פותח. עד אז הדפוס רץ כנוהל Cursor.

## בדיקה

```bash
python3 scripts/check-vfdsh.py
```

אין UI חי. אין דפדפן לאמת שליחה. העקביות היא מול הנעילות והמניפסט.
