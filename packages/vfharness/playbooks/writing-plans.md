# Writing plans — אחרי אישור, לפני יישום

מקור דפוס: [obra/superpowers `writing-plans`](https://github.com/obra/superpowers/tree/main/skills/writing-plans), עם delta מ־v6.3 ל־Spec authority + conflict preflight.  
רתמה: `vfharness` · לפני: `brainstorm-gate.md` · אחרי: `executing-plans.md` + `verification-before-claim.md` · מצב: `state/<task-id>.json`.

## מתי

אחרי ש־`brainstorm-gate` קיבל אישור אנושי, ולפני עריכות מרובות / משימה Architectural או Bounded רחבה.

**Spike:** אין תוכנית קבצים — דוח ממצאים מספיק.  
**Bounded קטן (קובץ אחד):** רשימת צעדים בצ׳אט מספיקה.  
**Architectural / רב־פק:** כותבים תוכנית בדיסק.

## איפה שומרים

```
packages/vfharness/state/<task-id>/task_plan.md
```

או צמוד ל־checkpoint: `packages/vfharness/state/<task-id>.json` עם שדה `plan` קצר.  
לא `docs/superpowers/plans/` — זה של obra; אצלנו הרתמה.

## סמכות התוכנית

`Spec / אישור` הוא pointer מחייב להחלטה שאושרה — שיחה, ADR, design/spec או instruction קנוני. התוכנית **אינה רשאית להרחיב סמכות, להחליש gate או להמציא requirement** שלא קיים ב־Spec/constitution.

אם התוכנית מתנגשת עם ה־Spec: ה־Spec מנצח; מתקנים את התוכנית לפני/במהלך preflight. אם ה־Spec עצמו עמום, `executing-plans.md` מסווג safe ruling מול stop class.

## כותרת חובה

```markdown
# <שם> — תוכנית יישום

**Goal:** משפט אחד
**Architecture:** 2–3 משפטים (פקים + קבצים)
**Spec / אישור:** קישור לצ׳אט / ADR / קובץ עיצוב שאושר — מקור סמכות מחייב
**Constraints:** אין ₪ מומצא · אין runtime שני · אין npx · gates לפי constitution/AGENTS.md

## קבצים (מפת מבנה)

| קובץ | Create / Modify | אחריות |
|---|---|---|
| … | … | … |

## Shared surfaces / dependencies

- files/interfaces/state שיותר מ־Task אחד נוגע בהם
- producer → consumer relations
- external/provider/human gates
- final integration proof
```

הסעיף `Shared surfaces / dependencies` אינו preflight בפני עצמו; הוא חומר הגלם ל־evidence-bearing matrix ש־`executing-plans.md` כותב לפני Task 1.

## גודל משימה

משימה = יחידה קטנה עם מחזור אימות עצמאי (סנסור / self-test / receipt / diff קריא).  
קיפול setup+docs לתוך המשימה שהם משרתים. פיצול רק כשסוקר יכול לדחות משימה אחת בלי לדחות את שכנתה.

**כל צעד = פעולה אחת:**

1. כתיבה / עריכה ממוקדת  
2. הרצת בדיקה (`python3 scripts/check-*.py` / CLI self-test / provider receipt)  
3. אימות תוצאה צפויה  
4. review/commit לוגי אם נדרש

## תבנית משימה

```markdown
### Task N: <שם>

**Files:**
- Create: `packages/…`
- Modify: `packages/…`

**Depends on:** Task / source / interface, או `none`
**Produces:** artifact/interface/state שהמשך התוכנית צורך
**Consumes:** artifact/interface/state קיים

**Verify:**
- Run: `python3 scripts/check-….py`
- Expect: OK / …

- [ ] Step 1: …
- [ ] Step 2: …
```

## תכנון ל־test-first

לשינוי executable behavior, bugfix או automation:

- כתוב בתוכנית מהו ה־RED proof: test/reproduction/sensor שצריך להיכשל **לפני** התיקון ובאיזו סיבה צפויה.
- כתוב את ה־GREEN proof: אותה התנהגות עוברת אחרי המימוש + regression proof רלוונטי.
- אל תמציא test טקסי ל־Markdown/copy/data/config שאין להם behavior executable; שם proof דטרמיניסטי/structural/receipt מתאים יותר.

## תכנון parallelism

סמן משימות כ־parallel-safe רק אם אין shared-write state, אין producer/consumer ביניהן ואין gate משותף לא פתור. ה־preflight בזמן execution הוא זה שמאשר בפועל; label בתוכנית אינו הוכחה.

## YAGNI במשרד

- לא לפתוח פק חדש למשימה אחת — למפות לפק קיים (`BEST-SKILLS.md` / `REPOS.md`).
- לא להוסיף runtime / `npx skills` / OpenClaw.
- לא להמציא שורות דירוג / ₪ / Insights כדי «למלא תוכנית».
- לא להוסיף worktree חובה כשמדיניות ה־workspace לא דורשת אותו.

## דגלים אדומים

| מחשבה | מציאות |
|---|---|
| «נתחיל לכתוב ואז נתכנן» | תוכנית אחרי אישור brainstorm — לפני diff גדול |
| «משימה אחת = PR שלם» | לפצל לאימותים עצמאיים |
| «אין סנסור — נדלג» | לפחות proof מתאים + verification-before-claim |
| «שתי משימות נוגעות באותו קובץ אבל נריץ parallel» | shared-write => סדרתי או הפרדה אמיתית |
| «התוכנית אמרה, אז אפשר לעקוף Spec/gate» | Spec/constitution הם authority; plan הוא execution argument בלבד |

## לא

- להתקין obra/superpowers או subagent-driven-development runtime
- לשמור תוכניות מחוץ לגיט בלבד במשימות ארוכות (checkpoint חובה)
- להשתמש ב־plan כתחליף ל־evidence-bearing preflight

## קשר

- `playbooks/brainstorm-gate.md` — אישור לפני תוכנית
- `playbooks/executing-plans.md` — preflight + rulings + fan-out/fan-in
- `playbooks/implementation-discipline.md` — RED → GREEN → REFACTOR
- `playbooks/skillstate.md` — \(P,\Sigma,O\) לכל צעד ארוך
- `playbooks/systematic-debugging.md` — כשהתוכנית נשברת על באג
- `playbooks/verification-before-claim.md` — לפני «סיימתי»
