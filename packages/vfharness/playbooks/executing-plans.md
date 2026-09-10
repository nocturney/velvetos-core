# Executing plans — תוכנית כתובה → ביצוע

מקור דפוס: [obra/superpowers `executing-plans`](https://github.com/obra/superpowers/tree/main/skills/executing-plans).  
רתמה: `vfharness` · לפני: `writing-plans.md` · אחרי: `verification-before-claim.md`.

## מתי

יש `task_plan.md` / שדה `plan` ב־checkpoint אחרי אישור `brainstorm-gate`, וצריך לבצע בלי לדלג על אימותים.

## חוק ברזל

1. קרא את התוכנית במלואה לפני עריכה.
2. בצע **משימה אחת** בכל פעם — סמן in_progress → צעדים → אימות → completed.
3. **אל תדלג על Verify** שבתוכנית (`check-*.py` / self-test / diff קריא).
4. חסימה / פער בתוכנית / אימות שנכשל פעמיים → **עצור ושאל** — לא לנחש.

## תהליך

### 1. טען ובקר

- קרא `packages/vfharness/state/<task-id>/task_plan.md` (או checkpoint).
- אם יש חורים קריטיים / סיכון לנעילת ליבה → העלה לראש צוות לפני התחלה.
- אין שאלות → צור todo לפי משימות התוכנית והתחל.

### 2. בצע משימה

לכל Task בתוכנית:

1. הכרז: מבצע Task N.
2. עקוב אחרי הצעדים בסדר (2–5 דק׳ לוגית).
3. הרץ את אימות התוכנית; שמור פלט ב־checkpoint אם ארוך.
4. סמן הושלם רק אחרי אימות ירוק.

### 3. סיום

- אחרי כל המשימות: `verification-before-claim.md` לפני «סיימתי».
- אחרי שינוי קטלוג/כלל/פק: `python3 scripts/check-all.py`.
- עדכן `state/<task-id>.json` (`status`, `last_updated`).

## מתי לעצור מיד

| מצב | פעולה |
|---|---|
| חסר מקור / כלי `needsAuth` | failover לפי ORCHESTRA — לא להמציא גוף |
| סנסור אדום פעמיים | escalation template — לא ניחוש שלישי |
| התוכנית דורשת runtime שני / npx / אוטו־DM | דחה — נעילת ליבה |
| ₪ / Insights חסרים | כתוב `X ₪` / «אין ספירה» |

## לא (התאמת משרד)

- לא חובה `subagent-driven-development` / finishing-branch של obra — אין runtime שני
- לא worktree חובה על Cloud (workspace יחיד) — כן branch ייעודי לפי מדיניות git
- לא לדלג ל־main בלי אישור מפורש

## קשר

- `playbooks/brainstorm-gate.md` — אישור לפני תוכנית
- `playbooks/writing-plans.md` — כתיבת התוכנית
- `playbooks/systematic-debugging.md` — אם אימות נשבר על באג
- `playbooks/verification-before-claim.md` — לפני טענת סיום
- `playbooks/skill-first.md` — קרא סקיל לפני פעולה
