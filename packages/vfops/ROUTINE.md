# שגרת משרד

מושב: **תפעול**. התזמורת רצה ב־Cursor. Grok לא גולש.

Gemini הציע Make/Zapier: פנייה → שורה בגיליון → התראת טלפון → **אישור קבלה אוטומטי ללקוח**.  
Perplexity הציע אותו חיבור (n8n/Make + ChatGPT) עם **צ׳אטבוט 24/7** באתר או באינסטגרם.

## יום

| שעה (Asia/Jerusalem) | מה | קובץ |
|---|---|---|
| 06:15 | תזמורת: ChatGPT **וגם** Gemini **וגם** Perplexity · failover מיד אם כלי נפל | `constitution/ORCHESTRA.md`, `vfresearch/DAILY.md` |
| 06:15–07:00 | צרכנים יומיים (בלי check-all / בלי G005 אוטומטי) | `python3 scripts/vfops_loop.py run` · אח״כ בריף |
| **07:00** | **Morning Brief** — עברית, קומפקטי: מה קרה / מה המשרד ביצע / מה מכין / live verify / צינור תוכן / Production→Content / מדיה / Yellow / רק Red אמיתי לבעלים | `python3 scripts/vfops_loop.py brief --write` · `BRIEF.md` · `hq/GATES.md` · `constitution/RISK.md` |
| **09:00** | **Media Intake** יומי — נכנס → קטלוג → אימות הורדה → מקור (תפעול / auto-intake). Upload ≠ approval. `validate` ≠ ניטור | `docs/MEDIA-VAULT.md` · `python3 scripts/vfmedia.py intake run` · `intake status` · `validate` רק לסכמה |
| **10:00** א׳/ג׳/ה׳ | **Content Sprint** — מועמדים, כיתוב, Canva, נגזרות, EDIT-GATE, PREFLIGHT, תור | skill `vf-content-sprint` · `vfgrowth` |
| **11:00** | **Publish Watch** — 36 שעות הבאות: scheduled≠live, failed, dead-letter, needsAuth | `python3 scripts/vf_office_watchdog.py` · `vfigos/PUBLICATION-STATES.md` |
| לפני שיבוץ | שער עריכה + פריפלייט — CTA = הודעת Instagram. נכשל-סגור = לא משבצים | `EDIT-GATE.md` · `PREFLIGHT.md` · `PUBLIC_CTA.md` |
| אחרי בריף | פוסט מתוכנן → Google Calendar (בלי לשאול משבצת) · מצב = `scheduled` לא live | `vfgrowth/CALENDAR-OPS.md` |
| אחרי `liveVerified` | Insights ב־24 שעות. חסר = «אין ספירה». מדדים חלשים ≠ Red | `vfinsights` · `constitution/RISK.md` |

## ערב / פעמיים בשבוע

| מתי | מה | קובץ |
|---|---|---|
| ראשון + חמישי ערב | **Insights Review** — רק מספרים מאומתים; למידה לצינור הבא; לא פינג לכריסטיאן על חולשה | `vfinsights` |
| סוף יום | רטרו למידה + owner-memory | `vfops/hq/DAILY-RETRO.md` · skill `vf-daily-learning` |

## Watchdog (תמיד)

`python3 scripts/vf_office_watchdog.py [--write]`  
בודק: צינור פרסום · vault · dead-letter · follow-ups · CTA · profile desired · IG needsAuth.  
פלט: OK / AUTOFIXED / PREPARED / WAITING_EXTERNAL_TOOL / DEAD_LETTER / RED_BLOCKER.  
לא לספאם את כריסטיאן.

## NO INSTAGRAM CONNECTION ≠ NO OFFICE WORK

כש־`instagram.status=needsAuth`: ממשיכים intake, inspection, copy, Canva, derivatives, preflight, queue, calendar candidates, feed audit. לא ממציאים live.

## שבוע

| מתי | מה | קובץ |
|---|---|---|
| פעם בשבוע (רמז: ראשון בבוקר) | סקירת **קישורי השראה והטמעה** שנשלחו — עדכונים + «מה חדש לחקור» + דופק **Print·Demand·Sound** | `vfresearch/WEEKLY.md`, `vfresearch/LINKS.json`, `vfresearch/hq/PRINT-DEMAND.md` |
| ראשון + רביעי (אחרי 06:15) | סריקת MakerWorld/Printables מאחורי שער רישיון — בלי שם מהאוויר, בלי סלייסר מ־HQ | `vfresearch/hq/MAKERWORLD-SCAN.md` · `python3 scripts/vfsku.py scan` |
| פעם בשבוע (רמז: ראשון אחרי בריף) | מילוי משבצות הלוח הקבוע — ריל א׳/ג׳ 16:00, קרוסלה ה׳ 12:00, סטוריז 20:30. חסום = דילוג | `vfgrowth/CALENDAR.md`, `LEDGER.md`, `HANDOFF-he.md` |
| פעם בשבוע (רמז: לפני מילוי לוח) | סקירת פניות עם קונספט בלבד או קובץ בעייתי → שימוש ב-3D AI Studio לפי `vfprod/3DAISTUDIO.md` לפני סלייסר | `vfprod/3DAISTUDIO.md`, `vfprod/CONNECT-3DAI.md` |

## כל יומיים

| מתי | מה | קובץ |
|---|---|---|
| כל ~48 שעות (טיימר · דופק לנצח עד שהבעלים עוצר) | סקירת דירוג **LinklyAI/best-skills** — הטמעת דפוסים + חידוש טיימר | `vfresearch/BEST-SKILLS.md`, `TIMER.md`, `BEST-SKILLS.json`, skill `vf-best-skills` |
| פעם בחודש / לפי דרישה | מחקר **30 יום / קהילה** (engagement) | `vfresearch/hq/LAST30.md`, skill `vf-last30`, `HQ-ROUTINE.md` |

לא מחליף את 06:15 (שם צ'אטים חדשים). כאן חוזרים על הרישום. קישור חדש באמצע השבוע → נרשם ב־`LINKS.json` **באותו יום**. אירוע Calendar רק אם ראש צוות מבקש.

GitHub workflows קיימים (daily research / weekly deck) נשארים נפרדים — לא לשכפל jobs.

מנדט מושב מחקר/אורקסטרציה: `packages/vfresearch/HQ-ROUTINE.md`.

לפני פתיחת פק או קובץ ידני לשאלה «מי מטפל ב…» — להריץ `python3 scripts/vfmem.py who "<job>"` ואז `python3 packages/vfmem/scripts/vf_semantic_search.py "<השאלה החופשית>"` כדי למשוך קטעים רלוונטיים.

מעבר ערב אחרי נעילה (כמו 30.8): רצים את 06:15 עכשיו. התוצר לבריף **של מחר**.

## בלוק 05 מהתזמורת

Cursor כותב ל־`packages/vfops/data/research.md` (הנתיב שהבריף 07:00 קורא) ועותק יום `BRIEF-YYYY-MM-DD.md`:

- יש הטמעה **ו-CLI שרץ**: «מה נבנה / יועל» + שם הפק + הפקודה.
- אין CLI ב-24ש: **«אין חדש במשרד»** — בדיוק. בלי קטלוג מזויף.
- פק יומי/`on-content` שלא הורץ: שורת **פער** בבריף (לא שקט).
- 31.8 פערי כלים: `vfresearch/sources/2026-08-31-orchestra.md` · מפה `vfmcp/GAP.md`.

HQ שולח את הבריף אל `nocturney@gmail.com` ב־`python -m vfops.gmail_brief_send` או ב־3 צעדי MCP (`docs/SEND-BRIEF-MCP.md`). לא `LOAD_FROM_FILE`. לא מחכים לגרוק.

## בריף לכריסטיאן — מה כן / לא

**כן (Red / החלטה אמיתית):** אישור בעלים · רכישה · מחיר לא ידוע · OAuth אנושי · פעולה הרסנית בפיד · מקור אמת שבור.

**לא:** מדדים חלשים · תיקוני איכות שגרתיים · הכנת תוכן · קליטת מדיה · failover שעובד · משימות שהמשרד יכול לפתור (Green/Yellow).

## מה לא נכנס לשגרה

| שלב שם | מה עושים ב־HQ | דילוג |
|---|---|---|
| פנייה חדשה | שורה פנימית בבלוק `02` / `vfconvert` | — |
| בירור חומר/כמות/זמן/גימור | אדם בהודעות Instagram (ציבורי) · רשומת וואטסאפ פנימית כבויה ל־outreach | צ׳אטבוט 24/7 |
| התראת טלפון | ראש צוות רואה בבריף | — |
| אישור קבלה אוטומטי | **לא.** | מייל/DM אוטומטי |
| Notion/Sheets חיצוני | לא חובה. הבריף הוא הגיליון | כפילות מערכת |
| Meta Suite / אוטו־DM / Metricool חובה | — | דולג |

Make/Zapier/n8n ללקוח — לא.  
PUBLIC_CURRENT_CTA = הודעת Instagram. BUSINESS_CONTACT_RECORD = `050-2517000` (לא CTA ציבורי).

כל ~48 שעות (טיימר) כבר כולל LinklyAI/best-skills. עבור תוכן אינסטגרם, להשתמש בסקיל `vf-canva-instagram` לפי `.cursor/skills/vf-canva-instagram/SKILL.md` לפני יציאה ל-Canva MCP.
