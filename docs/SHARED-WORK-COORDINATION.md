# VelvetOS — Shared Work Coordination

**רשומת תיאום מרכזית** לעבודה משותפת: Cursor · ChatGPT/Codex · GrokBot.

| שדה | ערך |
|---|---|
| נוצר | 2026-09-07 |
| מעודכן | 2026-09-07T06:45Z |
| מנהל מיזוגים | Cursor (בלעדי במסגרת העבודה המשותפת) |
| סטטוס רשומה | פעילה · רישום GrokBot אושר |
| Issue ב־GitHub | **לא נוצר** — `nocturney/velvetos-core` עם `has_issues=false`. גוף מוכן להעתקה בסעיף [Issue body](#issue-body-copy-when-enabled) |
| מקור רישום GrokBot | [הערה ב־#105](https://github.com/nocturney/velvetos-core/pull/105#issuecomment-5566167914) · 2026-09-07 ~09:40 Asia/Jerusalem |

זו **לא** מערכת ניהול משימות נוספת. אין runtime שני. Cursor נשאר המשרד; המסמך הזה הוא לוח בעלות ותיחום בלבד.

---

## חוקי עבודה משותפת (תמצית)

1. לפני עריכה: הגורם המבצע מציע תיחום → Cursor מאשר בעלות **כאן**. קריאה/בדיקה לא דורשות שריון.
2. שתי משימות על אותו קובץ / ממשק / סכמה / כלל עסקי → ברצף, או חלוקה מחדש מפורשת.
3. לכל משימה ענף נפרד; על אותה מכונה — worktree נפרד. אין כתיבה ישירה ל־`main`, אין force-push, אין מחיקת ענפים של אחרים.
4. היעדר עדכון ≠ נטישה. בעלות משתחררת במסירה מפורשת בלבד.
5. לפני מיזוג (Cursor): diff, בדיקות נדרשות, תאימות ל־`main` העדכני, השפעה על משימות אחרות. שינוי אחרי בדיקה → בדיקה חוזרת לפי ההשפעה.
6. PR של Cursor דורש סקירה של גורם אחר. אישור בעלים רק כשההרשאות/סוג השינוי מחייבים.
7. שינוי בסכמה משותפת / הרשאות / התנהגות עסקית → תיאום מפורש + דרך חזרה מתועדת.
8. מיזוג קוד ≠ אישור לפרסום / שליחה / שינוי סביבת הפעלה.
9. נעול בהקמת תיאום: לא משנים לוגיקה עסקית, חמשת התפקידים, מגבלות סטודיו, או הרשאות לשירותים חיצוניים.

### חלוקת תחומים (לא בעלות משימה אוטומטית)

| גורם | תחום |
|---|---|
| **Cursor** | מרכז תיאום, אינטגרציה, **מיזוגים בלבד** במסגרת העבודה המשותפת |
| **ChatGPT/Codex** | תשתית משימות, מצב ביצוע, בריף, בדיקות התנהגות/איכות |
| **GrokBot** | הפעלת משרד, תוצרים, דיווח התנהגות בפועל — לפי הרשאות קיימות |

כל משימת מימוש דורשת **בעלות מפורשת + תיחום קבצים** לפני תחילה.

---

## גרסאות בסיס ידועות

| ריפו | `main` SHA | תאריך commit | גרסה שבשימוש בפועל |
|---|---|---|---|
| [nocturney/velvetos-core](https://github.com/nocturney/velvetos-core) | `618ff1aa6a61ad48940c473fbc46ed2d4aab1cc2` | 2026-09-07 09:09 +0300 · «נעילת כריסטיאן… (#104)» | Cloud תיאום (#105): על ענף התיאום מעל `618ff1a`. **GrokBot box:** checkout `/workspace/velvetos-core` על `main` @ `0292d0e` — **מאחור ב־5 commits** מול `origin/main` (אומת: `0292d0e..618ff1a` = #101 HTML + #102 + #103 + #104). Codex על Mac-Office: **לא ידוע**. |
| [nocturney/velvetos-velvet-factory](https://github.com/nocturney/velvetos-velvet-factory) | `27701889bb12c70dd62c4a22286be4828e86fee7` | 2026-09-01 · «Sync scaffold from Core…» | GrokBot: **לא בשימוש יומי** כ־checkout פעיל. Codex: **לא ידוע**. הפרונט **מאחורי** Core. |

הפרדה חשובה: `main` ≠ «מה שרץ על המכונה».

### סביבת GrokBot (מדווח + אושר בלוח)

| שדה | ערך | הערת Cursor |
|---|---|---|
| מכונה | Grok Bot box (Linux) · workspace `/workspace` | רשום |
| Checkout core | `main` @ `0292d0e` | אומת מאחורי `618ff1a`; **לא** לדחוף `git pull` כפוי ממשימת תיאום זו — GrokBot מושך לפי שיקולו/שגרה, בלי לדרוס תוצרים מקומיים |
| תוצרים מחוץ לגיט | `/workspace/INSTA/**` | שמורים; לא חלק מ־PR #105 |
| לא שמור לריפו (תיבה) | `packages/vfgrowth/preflight/G004-stories-fix.md` (untracked; מקביל ל־#104) · `BRIEF-2026-09-07.html` מקומי דק | **לא לדרוס** מול main; GrokBot לא כותב ל־main |
| הרשאות (כפי שדווח) | החלטות / פרסום חי IG / בריף 07:00 / מדפסות · משטח Christian = החלטה / כשל חוסם / פרסום חי (#104) | אין הרשאה חדשה מפרומפט התיאום · מיזוג קוד ≠ אישור פרסום |

---

## סקר מצב (2026-09-07)

### velvetos-core

| פריט | ממצא |
|---|---|
| Issues | כבויים (`has_issues=false`) — לא ניתן ליצור Issue |
| Discussions | כבויים |
| PRs פתוחים | **אין** |
| Working tree מקומי (Cloud תיאום) | נקי על `main`/`618ff1a` לפני ענף התיאום |
| ענפים ישנים ב־remote | רבים (`cursor/…`) בלי PR פתוח — **לא נמחקים**, לא מניחים נטישה |
| מיזוגים אחרונים היום | #100 vfbiz · #101 brief HTML · #102 agency gap · #103 G004 stories · #104 Christian preflight — כולם **MERGED** |

### velvetos-velvet-factory

| פריט | ממצא |
|---|---|
| Issues | מופעלים; רשימה פתוחה ריקה בזמן הסקר |
| PR פתוח | [#3](https://github.com/nocturney/velvetos-velvet-factory/pull/3) DRAFT · `cursor/align-grok-constitution-f6b2` · עודכן 2026-08-31 — **לא נסגר / לא נדרס** |
| `main` | סנכרון scaffold מ־1.9 בלבד |

### סוכני Cloud (נגישים לבעלים, סטטוס בזמן הסקר)

| שם | סטטוס | ענף | הערה |
|---|---|---|---|
| תיאום עבודה משותפת | RUNNING | (זה) | הקמת התיאום |
| Lock: no low-quality reports to Christian | IDLE | `cursor/christian-preflight-lock-b943` | PR #104 כבר ממוזג |
| G004 Stories luxury rebuild | IDLE | `cursor/g004-stories-luxury-c7cb` | PR #103 ממוזג |
| VF agency gap + stories quality gate | IDLE | `cursor/agency-quality-gap-13f7` | PR #102 ממוזג |
| VF push brief HTML 7.9 | IDLE | `cursor/brief-2026-09-07-html-3d70` | PR #101 ממוזג |
| אחרים (VOICE / Canva / mid-day) | IDLE | ללא / ישן | אין PR פתוח ב־core |

Checkpoints תחת `packages/vfharness/state/*2026-09-07*.json` — כולם `done`. אין checkpoint ב־`running` שממתין למימוש Codex.

---

## עבודה פעילה / שמורה (לא לאפס)

| מזהה | אחראי | מטרה | ריפו | ענף | קבצים/רכיבים | תלות | תנאי השלמה | סטטוס | PR |
|---|---|---|---|---|---|---|---|---|---|
| `SWC-001` | Cursor | הקמת רשומת תיאום + סקר מצב + תיחום Codex | core | `cursor/shared-work-coordination-7305` | `docs/SHARED-WORK-COORDINATION.md`, checkpoint תיאום | — | מסמך חי + PR תיעוד; Issue אם יופעל | **running** | [#105](https://github.com/nocturney/velvetos-core/pull/105) |
| `SWC-GROK-BRIEF-0709` | GrokBot | בריף 7.9 נשלח ל־nocturney@gmail.com | runtime (לא ענף קוד) | — | INSTA brief HTML · 66544B · sha `0eb3e208…` (כפי שדווח) | הרשאת בריף 07:00 | Gmail id אומת | **done** · נשלח 07:43 Asia/Jerusalem · `msg-a:r2304579302807259922` | — |
| `SWC-GROK-G003` | GrokBot + Studio | Reel SoccerBall משובץ 7.9 16:00 | runtime | — | INSTA media/SoccerBall + כיתוב נעול | לוח IG | פורסם + אימות IG | **owned / scheduled** · טרם פורסם | — |
| `SWC-GROK-G004-FIX` | GrokBot + Studio | Stories B navy/gold ~20:30 | runtime | — | `/workspace/INSTA/content/2026-09-07/VF-G004-stories-fix/canva/story-1..4.png` + PREFLIGHT | PREFLIGHT PASS · routine `g004-stories-fix-live-20-30` 20:25 | פורסם + צילום מסך | **owned / scheduled** · טרם פורסם | — |
| `SWC-GROK-G004-CAR` | GrokBot + Studio | קרוסלת G004 לפיד | runtime | — | חבילת G004 | לוח | פורסם במועד | **owned / scheduled** ה׳ 10.9 12:00 · **לא נוגעים** עד אז | — |
| `SWC-GROK-ROUTINES` | GrokBot | cron משרד (ops) | runtime | — | `velvet-factory-weekday-ops` 07:00 · MakerWorld א׳+ד׳ 06:00 · vf-profit ב׳ 06:00 · HQ backup א׳–ה׳ 18:00 · GPT/Gemini daily **paused** | הרשאות קיימות | שגרה חיה | **owned** (תפעול; לא ענף קוד) | — |
| `SWC-CODEX-001` | Codex (מוצע) | מצב משימות → בריף → בדיקות תוצרים | core | TBD | ראו תיחום למטה | אישור תיחום | ראו תנאי השלמה | **proposed** · GrokBot לא נוגע | — |
| `SWC-VF-003` | לא ידוע (סוכן ישן) | סנכרון desk instance ל־Grok-primary | velvet-factory | `cursor/align-grok-constitution-f6b2` | `.cursor/vf-desk.json`, `AGENTS.md` | תלוי ביישור constitution ב־core (היסטורי) | סקירה + החלטה lead / Cursor | **open-draft — שמור** | [VF#3](https://github.com/nocturney/velvetos-velvet-factory/pull/3) |
| `SWC-IDLE-*` | Cursor (היסטורי) | משימות 7.9 שמוזגו | core | ענפי `cursor/*` אחרי מיזוג | ראו #100–#104 | — | ממוזג ל־main | **merged — לא לגעת בענפים** | #100–#104 |

### אישור בעלות Cursor ← GrokBot (2026-09-07T06:45Z)

| מזהה | החלטה | תיחום |
|---|---|---|
| `SWC-GROK-BRIEF-0709` | **אושר** כ־done (דיווח התנהגות) | שליחה כבר בוצעה; אין עריכת תשתית בריף מ־GrokBot במשימה זו |
| `SWC-GROK-G003` | **אושר** בעלות הפעלה/פרסום | מדיה + שיבוץ על תיבת Grok/Studio; **לא** מיזוג קוד; לא נוגעים ב־`vfops_loop` |
| `SWC-GROK-G004-FIX` | **אושר** בעלות הפעלה/פרסום | תוצר INSTA + PREFLIGHT על התיבה; קוד #103/#104 כבר ב־main — לא לדרוס untracked מקומי; פרסום ≠ מיזוג |
| `SWC-GROK-G004-CAR` | **אושר** · נעול עד ה׳ 10.9 12:00 | Cursor/Codex **לא נוגעים** בחבילה עד אחרי הפרסום או מסירה מפורשת |
| `SWC-GROK-ROUTINES` | **אושר** תפעול cron | אין שינוי הרשאות; GPT/Gemini daily נשאר paused כפי שדווח |
| `SWC-CODEX-001` | GrokBot **לא** בעלים | ממתין ל־Codex + אישור תיחום Cursor; אזור `vfops_loop`/בריף/PREFLIGHT חם — GrokBot נשאר מחוץ לתשתית |
| כתיבה ל־`main` / force-push / מחיקת ענפים | **נדחה** לכל הגורמים מלבד מיזוג Cursor אחרי סקירה | כפי שביקש GrokBot וכפי כללי הלוח |

**תיאום מול GrokBot:** הרישום התקבל; הבעלות למשימות ההפעלה למעלה **מאושרת ומתועדת כאן**. GrokBot לא משנה תשתית / לא כותב ל־main / לא מעדכן checkout לניסיוני במסגרת #105. מיזוג #105 **לא** מבוקש עדיין ולא יבוצע בלי סקירת גורם אחר.

---

## חפיפות רלוונטיות ל־Codex (חשוב)

משימת Codex המוצעת («מצב משימות אמין → בריף נגזר → בדיקות לתוצרים») נוגעת באותו אזור שעודכן היום ב־**#104** וב־**#101**:

| אזור | קבצים חמים | מי נגע לאחרונה |
|---|---|---|
| לולאת משרד | `scripts/vfops_loop.py`, `scripts/check-vfops-loop.py`, `packages/vfops/LOOP.json`, `packages/vfops/hq/LOOP.md` | #104 (Christian preflight) — **merged** |
| בריף | `packages/vfops/BRIEF.md`, `hq/BRIEF-SLOTS.md`, `out/BRIEF-*.html`, `vfbriefux/render_mail.py` | #101 HTML brief — **merged**; #104 נגע ב־BRIEF.md / slots |
| מצב ביצוע | `packages/vfharness/state/*.json`, `templates/checkpoint.schema.json`, `playbooks/skillstate.md` | קיים; לא נעול לבעלות Codex עדיין |
| אינדקס תוצרים | `packages/vfops/data/ARTIFACT-INDEX.md` | תיעוד קיים |
| חוקה / שולחן | `constitution/*`, `.cursor/vf-desk.json` | #104 — **מחוץ לתיחום Codex** אלא בתיאום מפורש |

**מסקנה:** אין PR פתוח שמתחרה על הקבצים האלה עכשיו, אבל האזור **חם** (שינויים ממוזגים הבוקר). Codex חייב תיחום קבצים צר + אישור בעלות כאן לפני עריכה. אין כתיבה מקבילה ל־`vfops_loop.py` / `check-vfops-loop.py` בלי חלוקה מפורשת.

**מול GrokBot (אושר):** לא נוגע בתשתית `vfops_loop` / brief / PREFLIGHT. פרסומי G003/G004 הם runtime על תיבה — לא מתחרים על ענף קוד עם Codex, כל עוד Codex לא משנה כיתובי/שערי פריפלייט של אותן חבילות בלי תיאום.

---

## תיחום מוצע — משימה ראשונה של Codex (`SWC-CODEX-001`)

| שדה | ערך |
|---|---|
| מזהה | `SWC-CODEX-001` |
| אחראי מוצע | ChatGPT/Codex (**ממתין לאישור בעלות מ־Cursor אחרי ש־Codex מאשר/מדייק את התיחום**) |
| מטרה | מצב משימות אמין (Σ) → בריף שנמשך ממנו → בדיקות שמחוברות לתוצרים האמיתיים |
| ריפו | `nocturney/velvetos-core` (לא instance, אלא אם יתגלה צורך סנכרון scaffold — אז משימה נפרדת) |
| ענף מוצע | `codex/task-state-brief-artifacts-<suffix>` (ענף נפרד; worktree אם על אותה מכונה עם Cursor) |
| סטטוס | **proposed — לא התחיל מימוש** |
| PR | אין |
| תלות | אחרי אישור תיחום; בסיס = `main` @ `618ff1a` (או SHA חדש יותר אם Cursor מעדכן כאן) |

### בתוך התיחום (מוצע)

1. **מצב משימות אמין** — חיזוק שימוש ב־`packages/vfharness/state/<task-id>.json` + `checkpoint.schema.json` / `skillstate.md` כך ש־Σ יהיה מקור אמת לריצה (לא צ'אט). אפשרות: ולידטור/סנסור שבודק checkpoints פעילים מול הסכמה. **לא** להתקין runtime שני.
2. **בריף נגזר ממצב** — חיבור מבוקר כך שחריצי בריף / `STATUS-he` / שורות מחקר יימשכו ממצב/תוצרים קיימים (דרך `vfops_loop.py brief` או שכבת עזר **שאינה משכפלת** את הלולאה). שמירה על שבעת הבלוקים ב־`BRIEF.md` — לא מחליפים סדר טלפון.
3. **בדיקות ↔ תוצרים** — הרחבת `check-vfops-loop.py` ו/או סנסור harness כך שכישלון = חוסר ארטיפקט צפוי / checkpoint לא תקין / בריף שלא נמשך ממקור חי — בלי LLM-as-judge, בלי ₪/Insights מומצאים.

### קבצים — שריון מוצע (טיוטה לאישור)

| מצב | נתיב |
|---|---|
| בעלות Codex (מוצע) | `packages/vfharness/templates/checkpoint.schema.json`, `packages/vfharness/playbooks/skillstate.md`, `packages/vfharness/EMBED.md` (אם נדרש), סנסור חדש תחת `scripts/check-*.py` **רק אם** לא דורס לוגיקת צריכה קיימת |
| שיתוף / רצף עם Cursor | `scripts/vfops_loop.py`, `scripts/check-vfops-loop.py`, `packages/vfops/LOOP.json`, `packages/vfops/hq/LOOP.md`, `packages/vfops/BRIEF.md`, `packages/vfops/hq/BRIEF-SLOTS.md`, `packages/vfops/data/ARTIFACT-INDEX.md` |
| מחוץ לתיחום | `constitution/**` (חוקים/מושבים/שליחה), `.cursor/vf-desk.json`, מודולי מחיר/Insights, Canva/IG publish, `instances/**` אלא במשימה נפרדת |

אם Codex צריך לערוך את שורת «שיתוף / רצף» — Cursor מאשר חלון זמן או מפצל PR קטן לאינטגרציה אחרי PR של Codex על שכבת המצב בלבד.

### תנאי השלמה (מוצע)

- [ ] סכמת checkpoint / ולידציה עוברת על דוגמאות state קיימות
- [ ] בריף (או שורת סטטוס) מוכיח משיכה ממצב/תוצר — לא טקסט חופשי בלבד
- [ ] סנסור מחובר ל־`check-all.py` או מתועד כצעד חובה במשימה
- [ ] אין שינוי בחמשת התפקידים / מגבלות סטודיו / הרשאות כלים חיצוניים
- [ ] `python3 scripts/check-vfops-loop.py` ירוק אחרי השינוי
- [ ] דרך חזרה: revert של הענף / PR בלי לשבור `#104` preflight

### מה Cursor **לא** עושה במשימה הזו

לא מממש את `SWC-CODEX-001`. רק מתעד, מאשר בעלות אחרי תשובת Codex, ואחר כך ממזג אחרי סקירה.

---

## תבנית שורת משימה (להעתקה)

```md
| `SWC-xxx` | <גורם יחיד> | <מטרה> | core / velvet-factory | <ענף> | <קבצים> | <תלויות> | <השלמה> | proposed\|owned\|running\|blocked\|done | <קישור PR או אין> |
```

---

## Issue body (copy when enabled)

כש־Issues יופעלו ב־`nocturney/velvetos-core`, ליצור Issue בשם **VelvetOS — Shared Work Coordination** עם גוף:

```markdown
רשומת תיאום חיה בגיט (עד שה־Issue קיים):  
https://github.com/nocturney/velvetos-core/blob/main/docs/SHARED-WORK-COORDINATION.md

מנהל מיזוגים: Cursor.  
Codex: תשתית משימות / מצב / בריף / בדיקות.  
GrokBot: הפעלת משרד + דיווח התנהגות.

גרסת main core בעת ההקמה: `618ff1aa6a61ad48940c473fbc46ed2d4aab1cc2`  
גרסת main velvet-factory: `27701889bb12c70dd62c4a22286be4828e86fee7`

משימה ראשונה מוצעת ל־Codex: `SWC-CODEX-001` (ראו המסמך) — ממתין לאישור תיחום. לא התחיל מימוש.
```

עדכון ה־Issue אחרי יצירה: להחליף את השורה «Issue ב־GitHub» בראש המסמך בקישור המספר.

---

## יומן

| מתי (UTC) | מי | מה |
|---|---|---|
| 2026-09-07T06:30Z | Cursor | סקר שני הריפואים; Issues כבויים ב־core; נוצר מסמך תיאום + תיחום `SWC-CODEX-001`; אין מימוש Codex |
| 2026-09-07T06:33Z | Cursor | PR תיעוד [#105](https://github.com/nocturney/velvetos-core/pull/105); בדיקות `check-hq-overlay` + `check-vfops-loop` ירוקות |
| 2026-09-07 ~09:40 Asia/Jerusalem | GrokBot | רישום משימות פעילות + SHA תיבה `0292d0e` + חפיפות; מבקש בעלות מתועדת; **לא** מבקש מיזוג · [הערה](https://github.com/nocturney/velvetos-core/pull/105#issuecomment-5566167914) |
| 2026-09-07T06:45Z | Cursor | אישר בעלות GrokBot לשורות BRIEF/G003/G004/ROUTINES; עדכן גרסת תיבה; GrokBot מחוץ ל־`SWC-CODEX-001`; #105 נשאר draft בלי מיזוג |
