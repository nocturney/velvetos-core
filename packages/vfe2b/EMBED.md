# vfe2b — איך מטמיעים

חמישה צוותי עבודה + שכבת משמרת (Orca) + שכבת תזמורת (awesome-agent-orchestrators). כל צוות הוא נוהל משרד, לא מוצר חדש. מקורות: הרשימה של E2B; שכבת המשמרת מ-[stablyai/orca](https://github.com/stablyai/orca); שכבת התזמורת מ-[andyrewlee/awesome-agent-orchestrators](https://github.com/andyrewlee/awesome-agent-orchestrators) (194, 31.8.2026). הביצוע: הפאקים שכבר יש. אין להתקין Orca / amux / OpenClaw.

אם Agency desk (#3 / #4) כבר ממוזג, אפשר גם `@studio-operations` / `@instagram-curator`. הצוותים כאן לא תלויים בזה.

## 1. בריף בוקר — `crews/morning-brief.md`

**מהרשימה:** Lindy (תעדוף מייל), Cal.ai / Heymoon (יומן), CrewAI (תפקידים), AutoGen (אדם בשיחה), Taskuary (תיבה → משמרת אחת).

**אצלנו:**

1. קרא Gmail (`nocturney@gmail.com`) — תיבת דואר וחשבוניות. אין דיוור המוני.
2. קרא יומן `Asia/Jerusalem`. צור אירוע רק אם ביקשו.
3. צלב מול `vfseason` (סימני עונה) ו-`vfbriefux` (פורמט הבריף).
4. הוצא רשימה: דחוף / מחכה לאדם / אפשר אחר כך. בלי ₪. נקוב **עבודה אחת** למשמרת.
5. HQ **שולח** את בריף 07:00 ב־`send_message` + `htmlBody` תצוגה 3 (`vfbriefux/MAIL.html`). כלי נפל → Drive `create_file` + המשך.

## 2. מחקר — `crews/research.md`

**מהרשימה:** GPT Researcher (מתכנן + מבצעים), Aomni (תוכנית ואז מקורות; לא ממציא תוכן), Private GPT / Local GPT / GPT Runner (קבצים פרטיים), MemGPT (זיכרון ארוך), Dex (שער אדם, עצירה במבוי סתום).

**אצלנו:**

1. המתכנן כותב 5–8 שאלות מחקר. לא תשובות.
2. כל שאלה → מקור עם קישור או שם קובץ HQ. אם אין מקור — כתוב «חסר».
3. חומה / גוף חסום → «אין גוף». ניסיון חוזר קורא שוב, לא מנחש.
4. דוח קצר ב-`vfresearch/sources/`. אסור Insights מומצאים.
5. רישיון / STL / מודל תלת-ממד חדש → `vlicense` לפני קטלוג.

## 3. פנייה להזמנה — `crews/inquiry.md`

**מהרשימה:** Claygent / Kadoa (איסוף עובדות מהרשת), Docket AI (מהנדס מכירות מורכב), AskToSell **רק כדפוס שאלות** — לא סוגר עסקה. 5dive / humanlayer / paperclip — שער אדם ו־₪.

**אצלנו:**

1. שלף מהשרשור: חומר, כמות, מתי, גימור. חסר → שאלת אדם לוואטסאפ (טיוטה, לא נשלחת).
2. מחקר לקוח/הפניה רק ממקורות. אין סקרייפ שממציא לקוח.
3. מסלול: `vfconvert` → `vfsales` → `vfcost` (יחידות, בלי מחיר מכירה) → אדם.
4. ₪ רק אחרי ראש צוות. אין AutoQuote.
5. שרשור ג׳ימייל נקוב + טיוטה מוכנה (בלי ₪ חסר) → HQ `reply`.

## 4. תוכן — `crews/content.md`

**מהרשימה:** Wordware / GoCharlie / Wispy (טיוטה), Diagram / v0 (פריסה — אצלנו Superdesign/Canva), Claudexor (סיבוב מכסה).

**אצלנו:**

1. `vfcopy`: שיעורי בית, טיוטה, לינט קול.
2. `vfcovers`: כיסוי לבריף. Canva קודם.
3. `vfigos`: סקירה **ושליחה דרך כלים** (`SEND.md`). אין Publish MCP → Canva+Drive+Gmail באותו תור.
4. `vfgrowth`: ספרינט תוכן. בלי בוסט/DM.
5. לא ממציאים שעלה לפיד. לא יושבים על `#מוכן-ל-Grok`.

## 5. ספרים ומספרים — `crews/books-data.md`

**מהרשימה:** Julius / Vanna / Wren / Powerdrill / TalktoData (שאל את הנתונים). kodo (אימות לפני תשובה).

**אצלנו:**

1. קרא רק מה שכתוב ב-`vfbooks`, `vfcost`, `vfinsights`, או קובץ שצוין.
2. פתח את הקובץ. אם המספר חסר — «אין במקור». אל תמלא.
3. חשבוניות נכנסות: Invoice4U נשאר. אין החלפה ל-Bookipi מ-HQ.
4. תרשים רק מנתונים שאומתו בשלב 1.

## 6. משמרת (Orca) — `crews/run.md`

**מהרשימה / המקור:** Orca ADE (worktree isolation, handoff מול supervise, `worker_done` / `escalation` / `decision_gate`). לא מורידים את האפליקציה.

**אצלנו:**

1. שם העבודה שהמשתמש נתן = תיק אחד. לא לערבב לקוחות.
2. בוחרים **צוות קיים אחד** (בריף / מחקר / פנייה / תוכן / ספרים) ומריצים אותו.
3. Fan-out רק ל-`vfcopy` / `vfcovers`, עד שלוש גרסאות. אין fan-out של ₪ או שליחה.
4. סיום בכרטיס עם מצב אחד: `worker_done` / `escalation` / `decision_gate` (₪ בלבד).
5. שלוש החמצות על אותו נתון → עצירה, לא ניחוש.

## 7. תזמורת (orchestrators) — אותה משמרת, כרטיס עשיר יותר

**מהרשימה:** herdr, Fusion, kodo, tutti, Crewplane, NEEDLE, fractal, MartinLoop, Taskuary, Claudexor. נוהל: `ORCHESTRATORS.md`.

**אצלנו:**

1. הכרטיס חייב `דופק` + `אימות` + `ארטיפקט`. בלי אימות אין `worker_done`.
2. לא מתקינים multiplexers / ADE / נחיל / OpenClaw / Ralph בלי אדם.
3. שליחת Gmail/IG נשארת supervise עד שהכלי ירה או failover נכתב. `decision_gate` לא אומר «חכה לגרוק».

## SaaS אחר כך (לא עכשיו)

Lindy, Clay, Zapier Central, Gumloop, Julius, Relevance AI, Bardeen, Beam, GitHub Action רשמי — רק אם ראש צוות פותח מנוי. עד אז הדפוס רץ כנוהל Cursor.

## 8. תרחישים (Huginn) — `scenarios/`

**מהרשימה:** [huginn/huginn](https://github.com/huginn/huginn) — Scenarios, Events, `working?`, DeDuplication.

**אצלנו:**

1. ארבעה תרחישים: `morning-digest`, `inquiry-chain`, `weekly-links`, `content-live`.
2. כל צומת = event ב-checkpoint (`vfharness/templates/checkpoint.schema.json`).
3. `working?` = `python3 scripts/check-staleness.py` (בריף היום + LINKS לא ישנים).
4. Dedup פנייה: `vfconvert/hq/DEDUP.md`.
5. **לא** מתקינים Huginn Rails.

## בדיקה

```bash
python3 scripts/check-vfe2b.py
python3 scripts/check-staleness.py
```

אין UI חי. העקביות היא מול הנעילות, `catalog.json`, `scenarios.json`, ו־`orchestrators.json`.
