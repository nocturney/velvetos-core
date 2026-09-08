# Failover — ניהול משרד Velvet Factory / VelvetOS

**Date:** 2026-09-08  
**Scope:** מעבר זמני ומבוקר של **ניהול המשרד** בין מנהלים נתמכים.  
**לא:** בנייה מחדש של המערכת · פק חדש · runtime שני · vault מדיה מקביל.

מסמך זה הוא **נקודת הכניסה** כשהמנהל הראשי אינו זמין.  
פיילאובר כלי/MCP (Canva, Gmail, API…) נשאר ב־[`constitution/ORCHESTRA.md`](../constitution/ORCHESTRA.md) + [`packages/vfharness/playbooks/degraded-mode.md`](../packages/vfharness/playbooks/degraded-mode.md).  
פיילאובר מכסת **Grok Bot** בלבד: [`GROK-FAILOVER.md`](GROK-FAILOVER.md) · [`packages/vfharness/playbooks/grok-failover.md`](../packages/vfharness/playbooks/grok-failover.md).

---

## מטרת המסמך

לאפשר מעבר מהיר ובטוח של ניהול משרד Velvet Factory / VelvetOS במקרה שהמנהל הראשי אינו זמין.

המחליף **לא בונה** את המערכת מחדש. הוא קורא את מקור האמת הקיים וממשיך מאותה נקודה.

---

## מנהלים נתמכים

| מנהל | תפקיד בפיילאובר |
|---|---|
| **ChatGPT** | מנהל ראשי / orchestration, בריפים, קופי, תפעול והחלטות משרדיות |
| **Perplexity** | גיבוי לניהול + מחקר עדכני ובדיקות חיצוניות |
| **Gemini** | גיבוי לניהול, במיוחד כשעבודה עם Google / Drive רלוונטית |
| **Grok** | גיבוי נוסף לניהול ותוכן |
| **Cursor** | גיבוי טכני לריפו, קוד, אוטומציות ותיעוד. **לא** ברירת מחדל לניהול לקוחות או תוכן אלא אם הוגדר אחרת |

סדר מועדף כש־ChatGPT נפל: Perplexity → Gemini → Grok → Cursor (טכני).  
סדר זה **לא** מחליף החלטת ראש צוות מפורשת, ואינו מבטל את טבלאות הכלי ב־`ORCHESTRA.md`.

---

## מקור האמת

לפני כל פעולה, המנהל המחליף חייב לקרוא לפחות:

1. [`docs/FAILOVER.md`](FAILOVER.md) (מסמך זה)
2. [`docs/SHARED-WORK-COORDINATION.md`](SHARED-WORK-COORDINATION.md)
3. [`docs/MEDIA-VAULT.md`](MEDIA-VAULT.md)
4. [`CHANGELOG.md`](../CHANGELOG.md)

בנוסף עליו **לאתר בפועל** ולקרוא מסמכים רלוונטיים מסוג HANDOFF / STATUS / RULES / OPERATIONS / CONTENT / SOCIAL / BRIEF.

### מיקומים ידועים בריפו (לא להמציא שמות — לאמת קיום)

| סוג | נתיבים קיימים (דוגמאות חיות) |
|---|---|
| **HANDOFF** | `packages/vfgrowth/HANDOFF-he.md` · `packages/vfigos/HANDOFF-STANDING-he.md` · `packages/vfcovers/g005/HANDOFF-he.md` · `packages/vfharness/templates/handoff.md` · `packages/vfops/out/*/handoff.txt` · checkpoints `packages/vfharness/state/<task-id>/handoff.md` |
| **STATUS** | `packages/vfops/hq/STATUS-he.md` |
| **RULES** | `AGENTS.md` · `constitution/` · `.cursor/vf-desk.json` · `.cursor/rules/` (רק לפי desk / `@slug`) |
| **OPERATIONS** | `packages/vfops/` (`LOOP.json`, `ROUTINE.md`, `hq/LOOP.md`, `DAILY-RETRO.md`) · `constitution/STUDIO.md` · `constitution/SEND.md` |
| **CONTENT** | `packages/vfgrowth/` (`CALENDAR.md`, `LEDGER.md`, `CONTENT-RUBRIC.md`, `EDIT-GATE.md`) · `packages/vfcopy/` · `packages/vfcovers/` · `packages/vfprod/PRINT-DONE.md` |
| **SOCIAL** | `packages/vfigos/` · `packages/vfgrowth/experts/SOCIAL-BOOSTER.md` · `constitution/ORGANIC_GROWTH.md` |
| **BRIEF** | `packages/vfops/BRIEF.md` · `packages/vfops/BRIEF-YYYY-MM-DD.md` · `packages/vfops/hq/brief-*.json` · `packages/vfops/out/BRIEF-*.html` |

אם קיימת סתירה: העדף **state פעיל** והוראות עדכניות יותר (checkpoint / SWC / HANDOFF חי), אלא אם מסמך מחייב (`AGENTS.md` / חוקה) אומר אחרת — ואז המדריך מנצח את השיחה.

---

## כללי Velvet Factory שחייבים להישמר

- סטודיו קטן להדפסות תלת־ממד בשדרות.
- איסוף עצמי בלבד.
- אין משלוח ארצי.
- הזמנות ופניות דרך WhatsApp ואינסטגרם.
- אין להמציא מחירים (`X ₪` / «אין ספירה» כשחסר מקור).
- אין להבטיח מועד מוכנות ללא מידע אמיתי.
- אין Auto-DM.
- אין Meta Business Suite (שיבוץ ב־`instagram.com`).
- אין להוסיף מערכת חדשה אלא אם היא מחליפה מערכת קיימת או מורידה עבודה ידנית ממשית.
- תוכן עסקי בעברית טבעית, קצרה ולא תאגידית.
- אם המשרד יכול לסגור משהו בעצמו — לא להפוך אותו למשימה לבעלים.
- עם זאת, הבעלים חייב לקבל שקיפות מלאה לגבי מה בוצע, מה בתהליך ומה מתוכנן.
- CTA: WhatsApp `050-2517000` / איסוף שדרות — לא «שלחו DM».
- HQ שולח Gmail/Instagram **דרך כלים** (`constitution/SEND.md`) — לא מחכים לאדם ללחוץ Send אם הכלי זמין.
- אין Print מ־HQ. אין secrets בגיט.

---

## מבנה הבריף לבעלים

הבריף צריך לכלול:

### בוצע

מה המשרד סגר מאז הבריף הקודם.

### בתהליך

מה מתבצע כרגע ומה הסטטוס.

### מתוכנן

מה המשרד מתכוון לבצע בהמשך.

### דורש ממך

רק דברים שבאמת דורשים פעולה של הבעלים, כגון:

- בחירה בין מודלים שכבר סוננו, למשל מ-MakerWorld.
- אישור מוצר / קופי / פרסום.
- תשלום.
- הזמנה.
- פעולה פיזית שהמשרד אינו יכול לבצע.
- החלטה עסקית מהותית.

### חריגים / חסימות

תקלות, סיכונים, שינויי כיוון או משהו שהבעלים צריך לדעת.

הבריף הוא כלי שקיפות וקבלת החלטות, לא רשימת מטלות שהמשרד מחזיר לבעלים.

תבנית בריף קיימת: `packages/vfops/BRIEF.md` + לולאה `python3 scripts/vfops_loop.py brief` · שליחה לפי `constitution/SEND.md` / `docs/SEND-BRIEF-MCP.md`.

---

## כלל תוכן חובה: תהליך → מוצר מוגמר

אם פורסם צילום או וידאו של מוצר:

- בהדפסה
- בתהליך
- לפני גימור

חובה:

1. לפתוח מעקב עבור אותו מוצר.
2. לחשב או להעריך מתי צפוי להיות מוכן, לפי זמן ההדפסה, תור הייצור ושלבי הגימור (בלי להמציא מועד בלי נתונים — «חסר» אם אין מקור).
3. לתכנן פרסום המשך של המוצר המוגמר.
4. להכניס לבריף את מועד או חלון הפרסום המתוכנן.
5. לא לסגור את שרשרת התוכן עד שהתוצאה הסופית פורסמה, או שהתקבלה החלטה מפורשת שלא לפרסם.

שרשרת ברירת מחדל:

`תהליך → מוכן → צילום סופי → פרסום`

### שכבות state קיימות (לא ליצור מנגנון מקביל)

| שכבה | שימוש |
|---|---|
| `packages/vfgrowth/LEDGER.md` + `CALENDAR.md` + `HANDOFF-he.md` | מעקב מועמדים / משבצות / מסירה |
| `packages/vfprod/PRINT-DONE.md` + כרטיסי `vfprod/hq/cards/` | גשר Print→Post אחרי הדפסה תקינה |
| `constitution/ORGANIC_GROWTH.md` + `scripts/vf_organic_growth.py` | טיוטות + Decision Pack 07:00 (בלי autopost) |
| `packages/vfgrowth/data/content_events.jsonl` | יומן אירועי תוכן אם קיים |
| checkpoints `packages/vfharness/state/` | מצב משימה + `component_state` |

---

## מדיה

השתמש במקור המדיה המשותף הקיים: [`docs/MEDIA-VAULT.md`](MEDIA-VAULT.md) · קטלוג יחיד `packages/vfmedia/catalog.json`.

אין ליצור media vault מקביל.

שמור על הזרימה הקיימת (כפי שמוגדר בנוהל הכספת):

`חומר גלם → בעבודה/עריכה → מאושר לפרסום → פורסם → ארכיון`

העלאה ≠ אישור. תיקיית «מאושר לפרסום» לבד ≠ הוכחת אישור. אין שינוי הרשאות שיתוף. אין מחיקת קבצי vault. אין מק״ט / ₪ מומצא.

---

## פרוטוקול כניסה לתפקיד

כאשר כלי חלופי מקבל את ניהול המשרד, הוא חייב קודם:

1. לקרוא את מקורות האמת (סעיף למעלה).
2. לזהות משימות פתוחות (`SHARED-WORK-COORDINATION.md` · HANDOFF · STATUS · checkpoints).
3. לזהות חסימות.
4. לבדוק מה כבר בוצע כדי למנוע עבודה כפולה (`CHANGELOG.md` · יומן SWC · ארטיפקטים ב־`vfops/out/`).
5. להוציא לבעלים **«דוח השתלטות»** קצר:
   - מצב המשרד כרגע.
   - משימות פתוחות.
   - חסימות.
   - מה יבוצע ראשון.
   - מה דורש כרגע את הבעלים, אם בכלל.

רק לאחר מכן להמשיך בעבודה.

ערוץ דוח: Gmail `send_message` לבריף/הודעת משרד כשהכלי זמין; אחרת Drive `create_file` + המשך (`ORCHESTRA.md`). תבנית מסירת סשן: `packages/vfharness/templates/handoff.md`.

---

## Prompt קבוע להעברת ניהול

העתק את הבלוק הבא לכלים כשנכנסים כמנהל זמני:

⸻

אתה נכנס כרגע כמנהל זמני של משרד Velvet Factory / VelvetOS במקום המנהל הראשי שאינו זמין.

אל תבנה את המערכת מחדש ואל תשנה מדיניות רק משום שאתה מעדיף דרך אחרת.

קודם כל קרא את:

docs/FAILOVER.md

ולאחר מכן:

docs/SHARED-WORK-COORDINATION.md
docs/MEDIA-VAULT.md
CHANGELOG.md

ואתר כל מסמך HANDOFF / STATUS / RULES / OPERATIONS / CONTENT / SOCIAL / BRIEF רלוונטי.

התייחס לריפו ול-state הפעיל כמקור האמת.

לפני ביצוע פעולות הפק “דוח השתלטות” קצר הכולל:

* מה מצב המשרד כרגע.
* אילו משימות פתוחות קיימות.
* אילו חסימות קיימות.
* מה אתה מתכוון לבצע ראשון.
* מה דורש כרגע את הבעלים, אם בכלל.

לאחר מכן המשך לנהל את המשרד עצמאית ככל האפשר, תוך שקיפות מלאה בבריפים ושמירה על כל הכללים שב-docs/FAILOVER.md.

⸻

---

## החזרה למנהל הראשי

כש-ChatGPT או המנהל הראשי חוזר:

המחליף חייב להשאיר handoff מסודר עם:

- מה בוצע.
- מה השתנה.
- מה עדיין פתוח.
- אילו החלטות התקבלו.
- מה דורש תשומת לב.

אין למחוק state או היסטוריה כדי «לנקות» את המעבר.

אם בוצעה עבודה משמעותית, יש לעדכן גם את:

[`docs/SHARED-WORK-COORDINATION.md`](SHARED-WORK-COORDINATION.md)

שמור גם checkpoint תחת `packages/vfharness/state/` לפי תבנית `packages/vfharness/templates/handoff.md`.

---

## אבטחה

אין להכניס למסמכי handoff:

- passwords
- API tokens
- secrets
- credentials

מותר לציין רק את שם ה-secret/config או היכן הוא מנוהל (למשל «חסר מפתח Gemini» / `CONNECT-CHATGPT.md` / סוד סביבה בדשבורד).

אין לפתוח `chatgpt.com` / `gemini.google.com` מ־Cloud Agent. אין לשמור עוגיות דפדפן בריפו.

---

## קשר למנגנונים קיימים (מיזוג, לא כפילות)

| מנגנון | תפקיד | יחס ל־FAILOVER |
|---|---|---|
| `constitution/ORCHESTRA.md` | Failover **כלים** באותו תור | נשאר מקור לטבלאות MCP/API |
| `docs/GROK-FAILOVER.md` | מכסת Grok Bot | תת־מקרה; מצביע לכאן לניהול משרד מלא |
| `packages/vfharness/playbooks/degraded-mode.md` | `component_state: Degraded` | מצב תפעולי של רכיב, לא החלפת מנהל |
| `packages/vfharness/templates/handoff.md` | מסירת סשן/משמרת | תבנית לדוח השתלטות / חזרה |
| `docs/SHARED-WORK-COORDINATION.md` | לוח בעלות Cursor·Codex·GrokBot | מקור אמת למשימות פתוחות במעבר |

---

## בדיקה

אחרי שינוי במסמך זה או בקישוריו:

```bash
python3 scripts/check-vfharness.py
python3 scripts/check-all.py
```
