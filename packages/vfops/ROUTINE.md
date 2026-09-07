# שגרת משרד

מושב: **תפעול**. התזמורת רצה ב־Cursor. Grok לא גולש.

Gemini הציע Make/Zapier: פנייה → שורה בגיליון → התראת טלפון → **אישור קבלה אוטומטי ללקוח**.  
Perplexity הציע אותו חיבור (n8n/Make + ChatGPT) עם **צ׳אטבוט 24/7** באתר או באינסטגרם.

## יום

| שעה (Asia/Jerusalem) | מה | קובץ |
|---|---|---|
| 06:15 | תזמורת: ChatGPT **וגם** Gemini **וגם** Perplexity · failover מיד אם כלי נפל | `constitution/ORCHESTRA.md`, `vfresearch/DAILY.md` |
| 06:15–07:00 | צרכנים יומיים (בלי check-all / בלי G005 אוטומטי) | `python3 scripts/vfops_loop.py run` · אח״כ בריף |
| 07:00 | בריף בוקר — **לולאה מושכת פקים** | `python3 scripts/vfops_loop.py brief --write` · `BRIEF.md` · `hq/LOOP.md` |
| אחרי בריף | פוסט מתוכנן → Google Calendar (בלי לשאול משבצת) | `vfgrowth/CALENDAR-OPS.md` |
| לפני שיבוץ | שער עריכה + פריפלייט כתוב — לא JPEG גולמי. נכשל-סגור = לא משבצים | `vfgrowth/EDIT-GATE.md` · `vfgrowth/PREFLIGHT.md` · `constitution/STUDIO.md` |
| אחרי פרסום חי (HQ דרך כלים / `#נשלח-מ-HQ`) | Insights ב־24 שעות. אם אין מספר — «אין» | `vfinsights` |
| אחרי פרסום חי + לפני פוסט חדש | מילוי `packages/vfinsights/data/posts.csv` מנתוני Instagram Professional Dashboard + הרצת `python3 packages/vfinsights/scripts/vf_insights_loop.py` | `vfinsights/LEARNINGS.md` |

## שבוע

| מתי | מה | קובץ |
|---|---|---|
| פעם בשבוע (רמז: ראשון בבוקר) | סקירת **קישורי השראה והטמעה** שנשלחו — עדכונים + «מה חדש לחקור» | `vfresearch/WEEKLY.md`, `vfresearch/LINKS.json` |
| פעם בשבוע (רמז: ראשון אחרי בריף) | מילוי משבצות הלוח הקבוע — ריל א׳/ג׳ 16:00, קרוסלה ה׳ 12:00, סטוריז 20:30. חסום = דילוג | `vfgrowth/CALENDAR.md`, `LEDGER.md`, `HANDOFF-he.md` |
| פעם בשבוע (רמז: לפני מילוי לוח) | סקירת פניות עם קונספט בלבד או קובץ בעייתי → שימוש ב-3D AI Studio לפי `vfprod/3DAISTUDIO.md` לפני סלייסר | `vfprod/3DAISTUDIO.md`, `vfprod/CONNECT-3DAI.md` |

## כל יומיים

| מתי | מה | קובץ |
|---|---|---|
| כל ~48 שעות (טיימר · דופק לנצח עד שהבעלים עוצר) | סקירת דירוג **LinklyAI/best-skills** — הטמעת דפוסים + חידוש טיימר | `vfresearch/BEST-SKILLS.md`, `TIMER.md`, `BEST-SKILLS.json`, skill `vf-best-skills` |
| פעם בחודש / לפי דרישה | מחקר **30 יום / קהילה** (engagement) | `vfresearch/hq/LAST30.md`, skill `vf-last30`, `HQ-ROUTINE.md` |

לא מחליף את 06:15 (שם צ'אטים חדשים). כאן חוזרים על הרישום. קישור חדש באמצע השבוע → נרשם ב־`LINKS.json` **באותו יום**. אירוע Calendar רק אם ראש צוות מבקש.

מנדט מושב מחקר/אורקסטרציה: `packages/vfresearch/HQ-ROUTINE.md`.

לפני פתיחת פק או קובץ ידני לשאלה «מי מטפל ב…» — להריץ `python3 scripts/vfmem.py who "<job>"` ואז `python3 packages/vfmem/scripts/vf_semantic_search.py "<השאלה החופשית>"` כדי למשוך קטעים רלוונטיים.

מעבר ערב אחרי נעילה (כמו 30.8): רצים את 06:15 עכשיו. התוצר לבריף **של מחר**.

## בלוק 05 מהתזמורת

Cursor כותב ל־`packages/vfops/data/research.md` (הנתיב שהבריף 07:00 קורא) ועותק יום `BRIEF-YYYY-MM-DD.md`:

- יש הטמעה **ו-CLI שרץ**: «מה נבנה / יועל» + שם הפק + הפקודה.
- אין CLI ב-24ש: **«אין חדש במשרד»** — בדיוק. בלי קטלוג מזויף.
- פק יומי/`on-content` שלא הורץ: שורת **פער** בבריף (לא שקט).
- 31.8 פערי כלים: `vfresearch/sources/2026-08-31-orchestra.md` · מפה `vfmcp/GAP.md`.

HQ שולח את הבריף ב־Gmail `send_message` אל `nocturney@gmail.com`. לא מחכים לגרוק.

## מה לא נכנס לשגרה

| שלב שם | מה עושים ב־HQ | דילוג |
|---|---|---|
| פנייה חדשה | שורה פנימית בבלוק `02` / `vfconvert` | — |
| בירור חומר/כמות/זמן/גימור | אדם בוואטסאפ (`vfcopy`, `vfconvert`) | צ׳אטבוט 24/7 |
| התראת טלפון | ראש צוות רואה בבריף | — |
| אישור קבלה אוטומטי | **לא.** אדם בוואטסאפ 050-2517000 | מייל/DM אוטומטי |
| Notion/Sheets חיצוני | לא חובה. הבריף הוא הגיליון | כפילות מערכת |
| Meta Suite / אוטו־DM | — | דולג |

Make/Zapier/n8n ללקוח — לא. סגירה = אדם ב־050-2517000.

כל ~48 שעות (טיימר) כבר כולל LinklyAI/best-skills. עבור תוכן אינסטגרם, להשתמש בסקיל `vf-canva-instagram` לפי `.cursor/skills/vf-canva-instagram/SKILL.md` לפני יציאה ל-Canva MCP.
