# VelvetOS — Shared Work Coordination

**רשומת תיאום מרכזית** לעבודה משותפת: Cursor · ChatGPT/Codex · GrokBot.

| שדה | ערך |
|---|---|
| נוצר | 2026-09-07 |
| מעודכן | 2026-09-08T11:20Z |
| מנהל מיזוגים | Cursor (בלעדי במסגרת העבודה המשותפת) |
| סטטוס רשומה | פעילה · **#105 MERGED** (`cb4dd02`) · GrokBot אושר · Codex שלב א׳ ממוזג ב־#108 · Cursor #109–#114 ממוזגים |
| Issue ב־GitHub | **לא נוצר** — `nocturney/velvetos-core` עם `has_issues=false`. גוף מוכן להעתקה בסעיף [Issue body](#issue-body-copy-when-enabled) |
| מקור רישום GrokBot | [הערה ב־#105](https://github.com/nocturney/velvetos-core/pull/105#issuecomment-5566167914) · 2026-09-07 ~09:40 Asia/Jerusalem |
| מקור ACK Codex | סקירת head `6610a70` + תיחום `SWC-CODEX-001` שלב א׳ · 2026-09-07 (ChatGPT Work / Linux) |
| Failover מנהל משרד | [`docs/FAILOVER.md`](FAILOVER.md) — ChatGPT → Perplexity / Gemini / Grok / Cursor · לא בונים מערכת מחדש |

זו **לא** מערכת ניהול משימות נוספת. אין runtime שני. Cursor נשאר המשרד; המסמך הזה הוא לוח בעלות ותיחום בלבד.

**כשמנהל ראשי אינו זמין:** קרא [`docs/FAILOVER.md`](FAILOVER.md) לפני פעולה — דוח השתלטות, המשך מה־state החי, ועדכון לוח זה בחזרה למנהל הראשי.

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
| **GrokBot** | הפעלת משרד, תוצרים, דיווח התנהגות בפועל — לפי הרשאות קיימות · **כספת מדיה:** Drive MCP על ארבע התיקיות הנעולות |

### כספת מדיה (נעול Christian · 8.9.2026)

| גורם | בעלות |
|---|---|
| **תפעול** | קליטה: נכנס → מקור. לא מאשר פרסום מההעלאה |
| **Cursor** | סכמת הקטלוג היחיד (`packages/vfmedia/catalog.schema.json`) + חיישן |
| **GrokBot** | עבודה על קבצים דרך **Drive MCP** — לא קטלוג שני, לא שינוי הרשאות שיתוף |

נוהל: `docs/MEDIA-VAULT.md`. קטלוג אחד. העלאה ≠ אישור. תיקיית «מאושר לפרסום» לבד ≠ הוכחת אישור. לא מוחקים קבצים. לא ממציאים ₪ / מק״ט.

כל משימת מימוש דורשת **בעלות מפורשת + תיחום קבצים** לפני תחילה.

---

## גרסאות בסיס ידועות

| ריפו | `main` SHA | תאריך commit | גרסה שבשימוש בפועל |
|---|---|---|---|
| [nocturney/velvetos-core](https://github.com/nocturney/velvetos-core) | `cb4dd02ff9ef639258ceda86f58edb8499e0dde1` | 2026-09-07 · «Shared Work Coordination (#105)» | Cloud ACK זה: על `main` @ `cb4dd02`. **GrokBot box:** עדיין מדווח `0292d0e` — כעת **~25 commits מאחורי** `origin/main` (אומת `0292d0e..cb4dd02`). **אין handoff / אין pull אוטומטי** אחרי מיזוג #105. **Codex:** שלב א׳ ממוזג ב־#108 (`06f9854`); SHA checkout מקומי עדיין **לא ידוע**. |
| [nocturney/velvetos-velvet-factory](https://github.com/nocturney/velvetos-velvet-factory) | `27701889bb12c70dd62c4a22286be4828e86fee7` | 2026-09-01 · «Sync scaffold from Core…» | GrokBot: **לא בשימוש יומי**. Codex: לא נדרש לשלב א׳. הפרונט **מאחורי** Core. |

הפרדה חשובה: `main` ≠ «מה שרץ על המכונה».

### סביבת GrokBot (מדווח + אושר בלוח)

| שדה | ערך | הערת Cursor |
|---|---|---|
| מכונה | Grok Bot box (Linux) · workspace `/workspace` | רשום |
| Checkout core | `main` @ `0292d0e` (מדווח) | מאחורי `cb4dd02` ב־~25 commits. **אין pull אוטומטי** אחרי מיזוג #105 — עדכון תיבה = **מעבר גרסה במסירה מתואמת** בלבד |
| תוצרים מחוץ לגיט | `/workspace/INSTA/**` | שמורים; לא חלק מ־PR #105 |
| לא שמור לריפו (תיבה) | `packages/vfgrowth/preflight/G004-stories-fix.md` (untracked) · brief HTML מקומי | **לא לדרוס**; GrokBot לא כותב ל־main |
| הרשאות (כפי שדווח) | החלטות / פרסום חי IG / בריף 07:00 / מדפסות · משטח Christian (#104) | מיזוג #105 ≠ אישור פרסום / שינוי סביבה |

### סביבת Codex (מדווח + אושר בלוח)

| שדה | ערך | הערת Cursor |
|---|---|---|
| מכונה | ChatGPT Work · **Linux נפרד** (לא Mac-Office) | תוקן אחרי סקירת Codex על #105 |
| Checkout | לא ידוע (לא דווח אחרי #108) | לפני שלב ב׳: לדווח SHA |
| שלב א׳ | ממוזג [#108](https://github.com/nocturney/velvetos-core/pull/108) @ `06f9854` | בעלות שלב א׳ הושלמה |
| שלב ב׳ (בריף / `vfops_loop`) | **לא אושר** | דורש תיחום נפרד |

---

## סקר מצב (2026-09-07)

### velvetos-core

| פריט | ממצא |
|---|---|
| Issues | כבויים (`has_issues=false`) — לא ניתן ליצור Issue |
| Discussions | כבויים |
| PRs פתוחים | **אין** (נכון ל־2026-09-07T14:04Z) |
| Working tree מקומי (Cloud ACK) | ענף `cursor/swc-105-merged-ack-7305` מעל `cb4dd02` |
| ענפים ישנים ב־remote | רבים (`cursor/…`) בלי PR פתוח — **לא נמחקים**, לא מניחים נטישה |
| מיזוגים אחרונים היום | #100–#104 · #105 תיאום · #106–#107 מחקר · #108 Codex שלב א׳ · #109–#114 Cursor embed — כולם **MERGED** |

### velvetos-velvet-factory

| פריט | ממצא |
|---|---|
| Issues | מופעלים; רשימה פתוחה ריקה בזמן הסקר |
| PR פתוח | [#3](https://github.com/nocturney/velvetos-velvet-factory/pull/3) DRAFT · `cursor/align-grok-constitution-f6b2` · עודכן 2026-08-31 — **לא נסגר / לא נדרס** |
| `main` | סנכרון scaffold מ־1.9 בלבד |

### סוכני Cloud (נגישים לבעלים, סטטוס בזמן הסקר)

| שם | סטטוס | ענף | הערה |
|---|---|---|---|
| תיאום עבודה משותפת | RUNNING | (זה) | הקמת התיאום + ACK Codex |
| Lock: no low-quality reports to Christian | IDLE | `cursor/christian-preflight-lock-b943` | PR #104 כבר ממוזג |
| G004 Stories luxury rebuild | IDLE | `cursor/g004-stories-luxury-c7cb` | PR #103 ממוזג |
| VF agency gap + stories quality gate | IDLE | `cursor/agency-quality-gap-13f7` | PR #102 ממוזג |
| VF push brief HTML 7.9 | IDLE | `cursor/brief-2026-09-07-html-3d70` | PR #101 ממוזג |
| אחרים (VOICE / Canva / mid-day) | IDLE | ללא / ישן | אין PR פתוח ב־core |

Checkpoints תחת `packages/vfharness/state/*2026-09-07*.json` — רובם `done`. Checkpoint תיאום זה: **done** אחרי מיזוג #105 ע״י `nocturney` (2026-09-07T14:02:49Z).

---

## עבודה פעילה / שמורה (לא לאפס)

| מזהה | אחראי | מטרה | ריפו | ענף | קבצים/רכיבים | תלות | תנאי השלמה | סטטוס | PR |
|---|---|---|---|---|---|---|---|---|---|
| `SWC-001` | Cursor | הקמת רשומת תיאום + סקר מצב + תיחום Codex | core | `cursor/shared-work-coordination-7305` | `docs/SHARED-WORK-COORDINATION.md`, checkpoint תיאום | — | מסמך חי + מיזוג | **done · merged #105** (`cb4dd02`) · 2026-09-07T14:02Z ע״י nocturney | [#105](https://github.com/nocturney/velvetos-core/pull/105) |
| `SWC-GROK-BRIEF-0709` | GrokBot | בריף 7.9 נשלח ל־nocturney@gmail.com | runtime (לא ענף קוד) | — | INSTA brief HTML · 66544B · sha `0eb3e208…` (כפי שדווח) | הרשאת בריף 07:00 | Gmail id אומת | **done** · נשלח 07:43 Asia/Jerusalem · `msg-a:r2304579302807259922` | — |
| `SWC-GROK-G003` | GrokBot (Studio מסייע) | Reel SoccerBall משובץ 7.9 16:00 | runtime | — | INSTA media/SoccerBall + כיתוב נעול | לוח IG | פורסם + אימות IG | **owned / scheduled** · טרם פורסם | — |
| `SWC-GROK-G004-FIX` | GrokBot (Studio מסייע) | Stories B navy/gold ~20:30 | runtime | — | `/workspace/INSTA/content/2026-09-07/VF-G004-stories-fix/canva/story-1..4.png` + PREFLIGHT | PREFLIGHT PASS · routine `g004-stories-fix-live-20-30` 20:25 | פורסם + צילום מסך | **owned / scheduled** · טרם פורסם | — |
| `SWC-GROK-G004-CAR` | GrokBot (Studio מסייע) | קרוסלת G004 לפיד | runtime | — | חבילת G004 | לוח | פורסם במועד | **owned / scheduled** ה׳ 10.9 12:00 · **לא נוגעים** עד אז | — |
| `SWC-GROK-ROUTINES` | GrokBot | cron משרד (ops) | runtime | — | `velvet-factory-weekday-ops` 07:00 · MakerWorld א׳+ד׳ 06:00 · vf-profit ב׳ 06:00 · HQ backup א׳–ה׳ 18:00 · GPT/Gemini daily **paused** | הרשאות קיימות | שגרה חיה | **owned** (תפעול; לא ענף קוד) | — |
| `SWC-CODEX-001` | Codex → Cursor merge | שלב א׳: קריאה+ולידציה של מצב משימות + פלט מובנה | core | `cursor/swc-codex-001-phase-a-6de7` | ראו [לוח בעלות](#ownership-swc-codex-001) | ממוזג ל־main | 8 תנאי השלמה | **done · merged #108** (`06f9854`) | [#108](https://github.com/nocturney/velvetos-core/pull/108) |
| `SWC-CURSOR-VFCOPY` | Cursor | תיקון מודל check-vfcopy + בדיקות התנהגות | core | `cursor/fix-vfcopy-content-lint-c62b` | `scripts/check-vfcopy.py` | — | lint ירוק + behavioral | **done · merged #109** | [#109](https://github.com/nocturney/velvetos-core/pull/109) |
| `SWC-CURSOR-RETRO` | Cursor | שחזור DAILY-RETRO + עומס + לוג | core | `cursor/restore-daily-retro-c62b` | `packages/vfops/hq/DAILY-RETRO.md` | — | מדריך+לוג משוחזרים | **done · merged #110** | [#110](https://github.com/nocturney/velvetos-core/pull/110) |
| `SWC-CURSOR-VFOPS-RUN` | Cursor | הפרדת run/brief/check לצרכנים יומיים | core | `cursor/vfops-daily-consumers-c62b` | `scripts/vfops_loop.py` | — | בלי רקורסיית check-all | **done · merged #111** | [#111](https://github.com/nocturney/velvetos-core/pull/111) |
| `SWC-CURSOR-RESEARCH` | Cursor | מפת מפעילי מחקר + index fail-closed | core | `cursor/research-routines-activation-c62b` | `scripts/vfresearch_cadence.py` + workflow | לא כפול ל-GrokBot | status evidence בלבד | **done · merged #112** | [#112](https://github.com/nocturney/velvetos-core/pull/112) |
| `SWC-CURSOR-QUALITY` | Cursor | חיבור CONTENT-RUBRIC לשער שיבוץ | core | `cursor/content-quality-gates-c62b` | PREFLIGHT + check-vfcopy | — | Rubric≥20 + digest | **done · merged #113** | [#113](https://github.com/nocturney/velvetos-core/pull/113) |
| `SWC-CURSOR-TEMPLATES` | Cursor | חיבור תבניות Intake/SLA/דוח | core | `cursor/office-templates-wiring-c62b` | office/clients + vf_office_report | בלי PII בגיט | fixtures מסומנים | **done · merged #114** | [#114](https://github.com/nocturney/velvetos-core/pull/114) |
| `SWC-VF-003` | לא ידוע (סוכן ישן) | סנכרון desk instance ל־Grok-primary | velvet-factory | `cursor/align-grok-constitution-f6b2` | `.cursor/vf-desk.json`, `AGENTS.md` | תלוי ביישור constitution ב־core (היסטורי) | סקירה + החלטה lead / Cursor | **open-draft — שמור** | [VF#3](https://github.com/nocturney/velvetos-velvet-factory/pull/3) |
| `SWC-IDLE-*` | Cursor (היסטורי) | משימות 7.9 שמוזגו | core | ענפי `cursor/*` אחרי מיזוג | ראו #100–#104 | — | ממוזג ל־main | **merged — לא לגעת בענפים** | #100–#104 |
| `SWC-MEDIA-VAULT` | Cursor | נעילת כספת מדיה + קטלוג יחיד `vfmedia` | core | `cursor/media-vault-da7e` | `docs/MEDIA-VAULT.md`, `packages/vfmedia/*` | אין שינוי Drive sharing | נוהל + סכמה + סנסור ירוק | **owned** · conflict with #129 resolved · check-all 28/28 | [#131](https://github.com/nocturney/velvetos-core/pull/131) |

| `SWC-MEDIA-VAULT-RECONCILE` | Cursor (הוראת בעלים; Codex הכין patch שנחסם ב־403) | פתרון קונפליקט #130/#131 בלבד; ללא שינוי בבעלות הקבועה | core | `cursor/media-vault-procedure-eaaf` | `AGENTS.md`, `CHANGELOG.md`, `constitution/CONSTITUTION.md`, `docs/MEDIA-VAULT.md`, רשומה זו, `packages/vfigos/{SKILL,SEND}.md`, `packages/vfops/LOOP.json`, `scripts/check-vfmedia.py`, checkpoint `media-vault-reconcile-2026-09-08/` | squash `4b66515` on main (integration tip `8f0fe6c`) | קטלוג יחיד + ראיות יכולת מיוחסות + בדיקות | **done · merged #130** (`4b66515`) · 2026-09-08T06:46:10Z · post-merge check-all 28/28 · vfmedia kept · תפעול intake · no Drive ops | [#130](https://github.com/nocturney/velvetos-core/pull/130) |

### סדר מיזוג (Cursor embed-fix) — סגור 2026-09-07

#109–#114 **ממוזגים כולם** לפני/עם סגירת #105. אין תור מיזוג פתוח ב־core כרגע. GrokBot G003/G004/ROUTINES + VF#3 **לא ננגעו**.

### אישור בעלות Cursor ← GrokBot (2026-09-07T06:45Z)

| מזהה | החלטה | תיחום |
|---|---|---|
| `SWC-GROK-BRIEF-0709` | **אושר** כ־done (דיווח התנהגות) | שליחה כבר בוצעה; אין עריכת תשתית בריף מ־GrokBot במשימה זו |
| `SWC-GROK-G003` | **אושר** · אחראי יחיד = **GrokBot** · Studio = מסייע | מדיה + שיבוץ על תיבת Grok; Studio מסייע בלבד; **לא** מיזוג קוד; לא נוגעים ב־`vfops_loop` |
| `SWC-GROK-G004-FIX` | **אושר** · אחראי יחיד = **GrokBot** · Studio = מסייע | תוצר INSTA + PREFLIGHT על התיבה; קוד #103/#104 כבר ב־main — לא לדרוס untracked מקומי; פרסום ≠ מיזוג |
| `SWC-GROK-G004-CAR` | **אושר** · אחראי יחיד = **GrokBot** · Studio = מסייע · נעול עד ה׳ 10.9 12:00 | Cursor/Codex **לא נוגעים** בחבילה עד אחרי הפרסום או מסירה מפורשת |
| `SWC-GROK-ROUTINES` | **אושר** תפעול cron | אין שינוי הרשאות; GPT/Gemini daily נשאר paused כפי שדווח |
| `SWC-CODEX-001` | GrokBot **לא** בעלים | שלב א׳ בבעלות Codex (ראו מטה); GrokBot מחוץ לתשתית |
| כתיבה ל־`main` / force-push / מחיקת ענפים | **נדחה** לכל הגורמים מלבד מיזוג Cursor אחרי סקירה | כפי שביקש GrokBot וכפי כללי הלוח |

**תיאום מול GrokBot:** הרישום התקבל; הבעלות למשימות ההפעלה למעלה **מאושרת ומתועדת כאן**. GrokBot לא משנה תשתית / לא כותב ל־main. **#105 מוזג** ל־`main` @ `cb4dd02` ע״י nocturney (2026-09-07T14:02Z) — **עדיין אין pull אוטומטי לתיבה**; מעבר גרסה במסירה מתואמת בלבד. מיזוג קוד ≠ אישור פרסום.

### אישור בעלות Cursor ← Codex (2026-09-07T06:55Z) — `SWC-CODEX-001` שלב א׳

| החלטה | ערך |
|---|---|
| תפקיד / חלוקת אחריות | **מקובל** — Cursor ממזג; Codex תשתית מצב/בריף/בדיקות; GrokBot הפעלה |
| תיחום שלב א׳ | **אושר** כפי שהציע Codex |
| ענף | `codex/swc-001-task-state` |
| בסיס מימוש מאושר | `618ff1aa6a61ad48940c473fbc46ed2d4aab1cc2` (`main` בזמן ה־ACK) |
| שלב ב׳ (בריף חי / `vfops_loop`) | **לא אושר** — דורש תיחום נפרד + אישור מפורש |
| מחוץ לתיחום שלב א׳ | בריף חי, סכמה משותפת (`checkpoint.schema.json`), חבילות G003/G004, שערי פרסום, הרשאות, instance, VF PR #3 |

<a id="ownership-swc-codex-001"></a>

#### לוח בעלות קבצים — `SWC-CODEX-001` שלב א׳

| נתיב | בעלות | חפיפה | הערה |
|---|---|---|---|
| `scripts/vf_task_state.py` | **Codex בלעדי** (חדש) | אין | קריאת מצב, ולידציה, סיכום מובנה |
| `scripts/check-vf-task-state.py` | **Codex בלעדי** (חדש) | אין | בדיקות התנהגות + גילוי אוטומטי ב־`check-all.py` |
| `packages/vfharness/playbooks/skillstate.md` | **Codex בלעדי לכתיבה בשלב א׳** | קובץ קיים (תיעוד) — אין משימה אחרת פעילה עליו | תיעוד שימוש + משמעות תוצאות אימות; **לא** לשכתב את רעיון ה־embed / לא להתקין runtime שני |
| `packages/vfharness/state/swc-codex-001.json` | **Codex בלעדי** (checkpoint משימה זו) | אין | לא לשכתב checkpoints של גורמים אחרים |
| נתוני בדיקה | תיקייה זמנית מקומית אצל Codex | — | לא בלוח; לא נכנס ל־main כ־fixtures קשיחים בלי תיאום |

**חפיפות שנבדקו — אין צמצום נדרש לשלב א׳:**

| קובץ / אזור | משימה אחרת | מסקנה |
|---|---|---|
| `scripts/vfops_loop.py` / `check-vfops-loop.py` | #104 ממוזג; חם | **מחוץ** לשלב א׳ — שלב ב׳ בלבד אחרי אישור |
| `packages/vfharness/templates/checkpoint.schema.json` | אין בעלות פעילה | **מחוץ** לשלב א׳ (Codex לא מרכך סכמה; אי־תאימות היסטורית מדווחת) |
| `packages/vfharness/state/*.json` (אחרים) | checkpoints קיימים | **קריאה בלבד**; כתיבה רק ל־`swc-codex-001.json` |
| G003/G004 / PREFLIGHT / VF#3 | GrokBot / שמור | **מחוץ** לתיחום |

---

## חפיפות רלוונטיות ל־Codex (חשוב)

משימת Codex נוגעת באזור שעודכן היום ב־**#104** וב־**#101**, אך **שלב א׳ מאושר מצמצם** לשכבת קריאה/ולידציה בלבד:

| אזור | קבצים חמים | מי נגע לאחרונה | שלב א׳ |
|---|---|---|---|
| לולאת משרד | `scripts/vfops_loop.py`, `scripts/check-vfops-loop.py`, `packages/vfops/LOOP.json`, `packages/vfops/hq/LOOP.md` | #104 — **merged** | **לא נוגעים** |
| בריף | `packages/vfops/BRIEF.md`, `hq/BRIEF-SLOTS.md`, `out/BRIEF-*.html`, `vfbriefux/render_mail.py` | #101 / #104 | **לא נוגעים** (חיבור = שלב ב׳) |
| מצב ביצוע | `packages/vfharness/state/*.json`, `templates/checkpoint.schema.json`, `playbooks/skillstate.md` | קיים | קריאה + `skillstate.md` + סקריפטים חדשים; **בלי** שינוי סכמה |
| אינדקס תוצרים | `packages/vfops/data/ARTIFACT-INDEX.md` | תיעוד קיים | מחוץ לשלב א׳ אלא אם נדרש לקריאה בלבד |
| חוקה / שולחן | `constitution/*`, `.cursor/vf-desk.json` | #104 | **מחוץ** |

**מול GrokBot (אושר):** לא נוגע בתשתית `vfops_loop` / brief / PREFLIGHT. פרסומי G003/G004 הם runtime על תיבה — לא מתחרים על ענף קוד עם Codex בשלב א׳.

---

## תיחום מאושר — `SWC-CODEX-001` שלב א׳

| שדה | ערך |
|---|---|
| מזהה | `SWC-CODEX-001` |
| אחראי | ChatGPT/Codex |
| מטרה שלב א׳ | שכבת קריאה וולידציה של מצב משימות קיים + פלט מובנה (לחיבור בריף בהמשך) |
| ריפו | `nocturney/velvetos-core` |
| ענף | `codex/swc-001-task-state` |
| סטטוס | **done · merged #108** (`06f9854`) · 2026-09-07T11:55Z |
| PR | [#108](https://github.com/nocturney/velvetos-core/pull/108) |
| בסיס מימוש (היסטורי) | `main` @ `618ff1aa6a61ad48940c473fbc46ed2d4aab1cc2` בעת ACK; נחת על main דרך #108 |

### בתוך התיחום (שלב א׳)

1. קריאת checkpoints קיימים תחת `packages/vfharness/state/`.
2. הבחנה בין **סטטוס מדווח** לבין **השלמה שאומתה**.
3. פלט מובנה עם מקור + סטטוס אימות (לחיבור בריף בשלב ב׳ — לא בשלב א׳).
4. סנסור `check-vf-task-state.py` + חיבור לגילוי `check-all.py`.
5. תיעוד ב־`skillstate.md` למשמעות תוצאות האימות.
6. Checkpoint משימה: `packages/vfharness/state/swc-codex-001.json` בלבד.

### מחוץ לתיחום (שלב א׳)

- בריף חי / `vfops_loop.py` / `check-vfops-loop.py` / `LOOP.json` / `BRIEF.md`
- שינוי `checkpoint.schema.json` (אין ריכוך סכמה להסתרת אי־תאימות)
- G003/G004 / שערי פרסום / הרשאות / instance / VF PR #3
- שכתוב checkpoints של גורמים אחרים

### תנאי השלמה (מאושרים — שלב א׳)

1. רשומה לא תקינה מזוהה עם סיבה ברורה.
2. תוצר מקומי חסר או תוצר שלא אומת ≠ השלמה מאומתת.
3. נתיב ממכונה אחרת / קישור חיצוני = **לא נבדק בסביבה הנוכחית** (לא אוטומטית «תוצר חסר»).
4. משימה חסומה ≠ הצלחה.
5. פלט מובנה נגזר מרשומות מצב, עם מקור וסטטוס אימות.
6. אי־תאימות היסטורית מדווחת במפורש; לא מרככים סכמה.
7. בדיקות התנהגות + `check-all.py`; הפרדה בין כשלים קיימים לכשלים שהשינוי יצר.
8. מסירה = PR לסקירת Cursor, עם תוצאות בדיקה ודרך חזרה.

### שלב ב׳ (לא אושר עדיין)

חיבור הפלט לבריף — תיחום נפרד + אישור מפורש ל־`vfops_loop.py` ולבדיקותיו.

### מה Cursor **לא** עושה במשימה הזו

לא מממש את `SWC-CODEX-001`. מתעד, מאשר בעלות, ממזג אחרי סקירה.

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

משימה ראשונה של Codex: `SWC-CODEX-001` שלב א׳ — בעלות אושרה; ענף `codex/swc-001-task-state`.
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
| 2026-09-07T06:46Z | Cursor | ACK מפורש ב־PR #105 על שלוש השורות BRIEF/G003/G004-FIX; אין handoff גרסה / אין pull לתיבת Grok עכשיו |
| 2026-09-07T06:55Z | Cursor | ACK Codex: תפקיד מקובל; `SWC-CODEX-001` שלב א׳ **owned**; בסיס `618ff1a`; לוח בעלות ל־4 קבצים; תיקון סביבת Codex=Linux/ChatGPT Work; GrokBot אחראי יחיד + Studio מסייע; checkpoint תיאום `status: blocked` בלי `crew: null`; אין אישור מיזוג #105 עדיין |
| 2026-09-07T11:55Z | Cursor/nocturney | `SWC-CODEX-001` שלב א׳ ממוזג [#108](https://github.com/nocturney/velvetos-core/pull/108) (`06f9854`) |
| 2026-09-07 ~13:00–13:11Z | Cursor/nocturney | #109–#114 ממוזגים (vfcopy / retro / vfops / research / quality / templates) |
| 2026-09-07T14:02Z | nocturney | [#105](https://github.com/nocturney/velvetos-core/pull/105) **MERGED** (`cb4dd02`) — ready_for_review → merged |
| 2026-09-07T14:04Z | Cursor | ACK לוח: `SWC-001` done; main=`cb4dd02`; GrokBot נשאר @ `0292d0e` בלי pull; אין PRs פתוחים ב־core |
| 2026-09-08T05:40Z | Cursor | כספת מדיה נעולה: `docs/MEDIA-VAULT.md` + `packages/vfmedia` (קטלוג אחד). תפעול=קליטה; GrokBot=Drive MCP; Cursor=סכמה. בלי שינוי שיתוף Drive |
| 2026-09-08T05:50Z | Cursor | #131 rebase/merge על `main` אחרי #129: נשמרים MEDIA-VAULT + סכמת vfmedia + בעלות SWC; CHANGELOG משאיר גם את בריף Gmail CLI. בלי שינוי שיתוף Drive |
| 2026-09-08T11:20Z | Cursor | נוהל Failover מנהל משרד: `docs/FAILOVER.md` (ChatGPT→Perplexity/Gemini/Grok/Cursor). מיזוג עם GROK-FAILOVER / ORCHESTRA / handoff template — בלי מערכת כפולה |
