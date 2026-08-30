# vfe2b — איך מטמיעים

חמישה צוותי עבודה + שכבת משמרת (Orca). כל צוות הוא נוהל משרד, לא מוצר חדש. מקור הרעיון: הרשימה של E2B; שכבת המשמרת מ-[stablyai/orca](https://github.com/stablyai/orca). הביצוע: הפאקים שכבר יש. אין להתקין Orca.

אם Agency desk (#3 / #4) כבר ממוזג, אפשר גם `@studio-operations` / `@instagram-curator`. הצוותים כאן לא תלויים בזה.

## 1. בריף בוקר — `crews/morning-brief.md`

**מהרשימה:** Lindy (תעדוף מייל), Cal.ai / Heymoon (יומן), CrewAI (תפקידים), AutoGen (אדם בשיחה).

**אצלנו:**

1. קרא Gmail (`nocturney@gmail.com`) — תיבת דואר וחשבוניות בלבד. אל תשלח.
2. קרא יומן `Asia/Jerusalem`. צור אירוע רק אם ביקשו.
3. צלב מול `vfseason` (סימני עונה) ו-`vfbriefux` (פורמט הבריף).
4. הוצא רשימה: דחוף / מחכה לאדם / אפשר אחר כך. בלי ₪.
5. עצור. אדם מחליט מה נכנס למשמרת.

## 2. מחקר — `crews/research.md`

**מהרשימה:** GPT Researcher (מתכנן + מבצעים), Aomni (תוכנית ואז מקורות; לא ממציא תוכן), Private GPT / Local GPT / GPT Runner (קבצים פרטיים), MemGPT (זיכרון ארוך).

**אצלנו:**

1. המתכנן כותב 5–8 שאלות מחקר. לא תשובות.
2. כל שאלה → מקור עם קישור או שם קובץ HQ. אם אין מקור — כתוב «חסר».
3. דוח קצר ב-`vfresearch`. אסור Insights מומצאים.
4. רישיון / STL / מודל תלת-ממד חדש → `vlicense` לפני קטלוג.

## 3. פנייה להזמנה — `crews/inquiry.md`

**מהרשימה:** Claygent / Kadoa (איסוף עובדות מהרשת), Docket AI (מהנדס מכירות מורכב), AskToSell **רק כדפוס שאלות** — לא סוגר עסקה.

**אצלנו:**

1. שלף מהשרשור: חומר, כמות, מתי, גימור. חסר → שאלת אדם לוואטסאפ.
2. מחקר לקוח/הפניה רק ממקורות. אין סקרייפ שממציא לקוח.
3. מסלול: `vfconvert` → `vfsales` → `vfcost` (יחידות, בלי מחיר מכירה) → אדם.
4. ₪ רק אחרי ראש צוות. אין AutoQuote.

## 4. תוכן — `crews/content.md`

**מהרשימה:** Wordware / GoCharlie / Wispy (טיוטה), Diagram / v0 (פריסה — אצלנו Superdesign/Canva).

**אצלנו:**

1. `vfcopy`: שיעורי בית, טיוטה, לינט קול.
2. `vfcovers`: כיסוי לבריף. לא פוסט חי.
3. `vfigos`: תזמון/סקירה. **HQ לא שולח.** Grok משבץ במובנה.
4. `vfgrowth`: ספרינט תוכן. בלי בוסט/DM.

## 5. ספרים ומספרים — `crews/books-data.md`

**מהרשימה:** Julius / Vanna / Wren / Powerdrill / TalktoData (שאל את הנתונים).

**אצלנו:**

1. קרא רק מה שכתוב ב-`vfbooks`, `vfcost`, `vfinsights`, או קובץ שצוין.
2. אם המספר חסר — «אין במקור». אל תמלא.
3. חשבוניות נכנסות: Invoice4U נשאר. אין החלפה ל-Bookipi מ-HQ.
4. תרשים רק מנתונים שאומתו בשלב 1.

## 6. משמרת (Orca) — `crews/run.md`

**מהרשימה / המקור:** Orca ADE (worktree isolation, handoff מול supervise, `worker_done` / `escalation` / `decision_gate`). לא מורידים את האפליקציה.

**אצלנו:**

1. שם העבודה שהמשתמש נתן = תיק אחד. לא לערבב לקוחות.
2. בוחרים **צוות קיים אחד** (בריף / מחקר / פנייה / תוכן / ספרים) ומריצים אותו.
3. Fan-out רק ל-`vfcopy` / `vfcovers`, עד שלוש גרסאות. אין fan-out של ₪ או שליחה.
4. סיום בכרטיס עם מצב אחד: `worker_done` (טיוטה לסקירה) / `escalation` (חסר, טיוטת וואטסאפ) / `decision_gate` (₪ לראש צוות, או שליחה ל-Grok).
5. אחרי handoff ל-Grok — HQ לא ממשיך «לבדוק אם נשלח». שלוש החמצות על אותו נתון → עצירה, לא ניחוש.

## SaaS אחר כך (לא עכשיו)

Lindy, Clay, Zapier Central, Gumloop, Julius, Relevance AI, Bardeen, Beam — רק אם ראש צוות פותח מנוי. עד אז הדפוס רץ כנוהל Cursor.

## בדיקה

```bash
python3 scripts/check-vfe2b.py
```

אין UI חי. אין דפדפן לאמת שליחה. העקביות היא מול הנעילות והמניפסט.
