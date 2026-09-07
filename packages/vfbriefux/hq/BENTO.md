# Bento/Slides — היכן זה מתאים ואיפה לא

מקור: [bento.page/agents.md](https://bento.page/agents.md) — פורמט `bento/slides`, קובץ HTML עצמאי עם JSON חי (`#bento-doc`), אנימציות מורף, גרפים, טבלאות.

## החלטה

**לא מחליף את בריף הבוקר (`MAIL.html` / `render_mail.py`).**
בריף הבוקר הוא **אימייל** ש-Gmail/Grok שולחים בפועל (`htmlBody` תצוגה 3). בריף אימייל חייב:
- להיות תואם ללקוחות מייל (Gmail, Outlook, Apple Mail).
- **בלי** `<script>` חי — לקוחות מייל חוסמים JavaScript תמיד.

Bento/Slides הוא בדיוק ההפך: קובץ `.bento.html` עצמאי עם runtime JS מלא (מורפים, ken-burns, ספירת מספרים) שרץ בדפדפן — **לא ב-inbox**. שליחתו כ-אימייל תיפול לגמרי (הלקוח יחסום את ה-`<script>`, יישאר JSON חשוף על המסך).

**לכן: Bento לא נכנס לצינור השליחה היומי.** הוא מתאים לפריט נפרד שנפתח בדפדפן, לא לאימייל.

## איפה זה כן שווה

חבילת **"דק שבועי/חודשי"** — לא בריף תפעולי, אלא סיכום קצר לכריסטיאן שנפתח פעם בשבוע/חודש בדפדפן (לא בג'ימייל):

- כיסוי: כותרת + תאריך + ken-burns עדין.
- שקף "מה יצא" — טבלה (לא צ'ארט) של תוכן שפורסם השבוע, מקור: `vfgrowth/CALENDAR.md` + `LEDGER.md`.
- שקף מספרים — **רק אם יש מספר אמיתי** מ-`vfinsights` / `LAST30.md`; אם אין — טקסט "אין ספירה", לא צ'ארט מומצא.
- שקף "מה למדנו" — מ-`packages/vfinsights/data/LEARNINGS.md` אם קיים.
- שקף "מה הצעד הבא" — 2–3 שורות מ-`DAILY-RETRO.md` / `WEEKLY-LOAD.md`.

זה ממש הפורמט ש-agents.md ממליץ עליו: מספרים→chart, השוואה/פירוט→table, לא קיר טקסט.

## איך זה מיושם — אוטומטי מלא

- **`scripts/vf_weekly_deck.py`** — קורא קבצים אמיתיים מהריפו (`LEARNINGS.md`, `LAST30.md`, `DAILY-RETRO.md`, `WEEKLY-LOAD.md`) ובונה:
  1. JSON בפורמט `bento/slides` → `packages/vfbriefux/hq/weekly-deck.bento-doc.json`.
  2. דק **HTML מוכן לפתיחה** — מוריד את מעטפת האפליקציה מ-bento.page ומזריק את ה-JSON לתוך בלוק `#bento-doc`, כותב ל-`docs/weekly-deck/<תאריך>.html` וגם ל-`docs/weekly-deck/index.html` (הכי עדכני).
  3. אם אין רשת / המעטפת השתנתה — כותב אזהרה וממשיך; ה-JSON עדיין נכתב לנתיב הדבקה ידני (ראו למעלה).
- **`.github/workflows/velvetos-weekly-deck.yml`** — רץ אוטומטית כל יום שישי 09:00 IDT (`cron: '0 6 * * 5'`), מריץ את הסקריפט, ומדביק (`git commit` + `push`) את `docs/weekly-deck/` לענף `main`.
- **GitHub Pages** — צריך הפעלה חד-פעמית של אדם: Settings → Pages → Source = `main` / `/docs`. אחרי זה הכתובת הקבועה היא `https://nocturney.github.io/velvetos-core/weekly-deck/` ומתעדכנת לבד כל שבוע.
- **הבריף** (`scripts/vfops_loop.py`) מוסיף אוטומטית שקע **"08 · סופש"** בימי שישי–שבת–ראשון עם הקישור לדק העדכני — אבל **רק** אם `docs/weekly-deck/index.html` כבר קיים (אין קישור מת). ביום חול השקע לא מופיע כלל.
- **אין מספרים מומצאים.** אם `LEARNINGS.md`/`LAST30.md` לא קיימים או ריקים — השקף המתאים כותב "אין ספירה" בטקסט רגיל, לא בצ'אר.

## לא עושים

- לא שולחים `.bento.html` כקובץ מצורף/גוף באימייל (חסימת `<script>`).
- לא מחליפים את `MAIL.html` / `render_mail.py` — הקישור בלבד נכנס לשקע 08 בבריף הקיים.
- לא בונים דיאגרמות/צ'ארטים ב-Bento ממספרים שלא נמדדו בפועל.
