# Writing plans — אחרי אישור, לפני יישום

מקור דפוס: [obra/superpowers `writing-plans`](https://github.com/obra/superpowers/tree/main/skills/writing-plans).  
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

## כותרת חובה

```markdown
# <שם> — תוכנית יישום

**Goal:** משפט אחד
**Architecture:** 2–3 משפטים (פקים + קבצים)
**Spec / אישור:** קישור לצ׳אט או לקובץ עיצוב שאושר
**Constraints:** אין ₪ מומצא · אין runtime שני · אין npx · PUBLIC_CTA = הודעת Instagram · BUSINESS_CONTACT_RECORD וואטסאפ פנימי בלבד

## קבצים (מפת מבנה)

| קובץ | Create / Modify | אחריות |
|---|---|---|
| … | … | … |
```

## גודל משימה

משימה = יחידה קטנה עם מחזור אימות עצמאי (סנסור / self-test / diff קריא).  
קיפול setup+docs לתוך המשימה שהם משרתים. פיצול רק כשסוקר יכול לדחות משימה אחת בלי לדחות את שכנתה.

**כל צעד = פעולה אחת (2–5 דק׳ לוגית):**

1. כתיבה / עריכה ממוקדת  
2. הרצת בדיקה (`python3 scripts/check-*.py` / CLI self-test)  
3. אימות תוצאה צפויה  
4. commit לוגי (אם נדרש)

## תבנית משימה

```markdown
### Task N: <שם>

**Files:**
- Create: `packages/…`
- Modify: `packages/…`

**Verify:**
- Run: `python3 scripts/check-….py`
- Expect: OK / …

- [ ] Step 1: …
- [ ] Step 2: …
```

## YAGNI במשרד

- לא לפתוח פק חדש למשימה אחת — למפות לפק קיים (`BEST-SKILLS.md` / `REPOS.md`).
- לא להוסיף runtime / `npx skills` / OpenClaw.
- לא להמציא שורות דירוג / ₪ / Insights כדי «למלא תוכנית».

## דגלים אדומים

| מחשבה | מציאות |
|---|---|
| «נתחיל לכתוב ואז נתכנן» | תוכנית אחרי אישור brainstorm — לפני דיפ גדול |
| «משימה אחת = PR שלם» | לפצל לאימותים עצמאיים |
| «אין סנסור — נדלג» | לפחות diff + טענה מאומתת ב־verification-before-claim |

## לא

- להתקין obra/superpowers או subagent-driven-development runtime
- לשמור תוכניות מחוץ לגיט בלבד במשימות ארוכות (checkpoint חובה)

## קשר

- `playbooks/brainstorm-gate.md` — אישור לפני תוכנית
- `playbooks/skillstate.md` — \(P,\Sigma,O\) לכל צעד ארוך
- `playbooks/systematic-debugging.md` — כשהתוכנית נשברת על באג
- `playbooks/verification-before-claim.md` — לפני «סיימתי»
