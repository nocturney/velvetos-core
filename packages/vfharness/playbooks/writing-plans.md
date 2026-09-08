# Writing plans — תכנית לפני קוד (דפוס VF)

מקור דפוס: [obra/superpowers `writing-plans`](https://github.com/obra/superpowers/tree/main/skills/writing-plans) + [`executing-plans`](https://github.com/obra/superpowers/tree/main/skills/executing-plans).  
רתמה: `vfharness` · לא runtime שני · לא `docs/superpowers/plans/` vendor path.

## מתי

משימה רב־שלבית (5+ tool calls / 3+ שלבים) **אחרי** שער brainstorm (`brainstorm-gate.md`) ולפני עריכה כבדה.

חד־פעמי / שאלה / סיעור מוחות → בלי תכנית מלאה.

## איפה על הדיסק (קיים)

| תוצר | נתיב VF |
|---|---|
| תכנית שלבים | `state/<task-id>/task_plan.md` (`templates/task_plan.md`) |
| תצוגה מקדימה קצרה | `planned_steps[]` ב־`checkpoint.json` |
| ממצאים | `findings.md` |
| יומן ביצוע | `progress.md` |
| סגירה | `checkpoint.json` + `verification-before-claim.md` |

אין תיקיית `docs/superpowers/plans/`. Cursor = המשרד.

## כתיבת תכנית (דפוס)

1. **Goal** משפט אחד + **Architecture** 2–3 משפטים (בלי ₪ / Insights מומצאים).
2. מפת קבצים: Create / Modify / Test — נתיבים מדויקים כשאפשר.
3. משימות בגודל ביס: כל צעד ~2–5 דק׳ לוגיות; כל משימה מסתיימת בתוצר שניתן לבדוק (סנסור / CLI / ארטיפקט).
4. אילוצים גלובליים מהמדריך: אין אוטו־DM, אין npx על Cloud, CTA `050-2517000`, failover לפי `ORCHESTRA.md`.
5. אחרי אישור ראש צוות (אם נדרש) → העתק ל־`planned_steps` ב־checkpoint לפני ביצוע כבד.

## ביצוע תכנית (דפוס executing-plans)

1. טען `task_plan.md` + checkpoint · בדוק ביקורתית · שאל אם יש פער קריטי.
2. לכל משימה: in_progress → בצע → הרץ אימות שצוין → completed.
3. חסימה / סנסור אדום פעמיים → הסלמה (`templates/escalation.md`) — לא ניחוש.
4. סיום רק אחרי אימות (`verification-before-claim.md`) + עדכון checkpoint.

## מה לא

| דפוס vendor | VF |
|---|---|
| `docs/superpowers/plans/…` | `packages/vfharness/state/<task-id>/` |
| subagent-driven-development runtime | Cursor desk + `vfe2b/crews/run.md` |
| git-worktrees חובה | לא חובה ב־HQ; branch רגיל מספיק |
| TDD בכל צעד | כשיש סנסור/`check-*.py` — כן; אחרת ארטיפקט + verification |

## קישורים

- `PLANNING-FILES.md` · `brainstorm-gate.md` · `oma-patterns.md` · `LOOP.md` · `EMBED.md`
- Skill desk: `vf-harness` · `@workflow-architect`
