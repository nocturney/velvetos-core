# Executing plans — תוכנית כתובה → ביצוע

מקור דפוס: [obra/superpowers `executing-plans` + v6.3 SDD discipline](https://github.com/obra/superpowers).  
רתמה: `vfharness` · לפני: `writing-plans.md` · אחרי: `verification-before-claim.md`.

## מתי

יש `task_plan.md` / שדה `plan` ב־checkpoint אחרי אישור `brainstorm-gate`, וצריך לבצע בלי לדלג על אימותים.

## חוק ברזל

1. קרא את התוכנית במלואה לפני עריכה; אם יש `Spec / אישור`, הוא מקור הסמכות והתוכנית היא פירוש שלו — לא להפך.
2. בצע **משימה אחת** בכל פעם — in_progress → צעדים → אימות → review נדרש → completed.
3. **אל תדלג על Verify** שבתוכנית (`check-*.py` / self-test / receipt / diff קריא).
4. פער/עמימות שאינם חוצים stop class מקבלים **safe ruling מתועד** וממשיכים; לא עוצרים על כל ambiguity.
5. Ruling לעולם לא עוקף sensor נדרש, receipt חסר, human/constitutional gate או סמכות של ה־Spec.

פורמט ruling קנוני:

```text
Ruling: <decision> — <why> — <cost_if_wrong>
```

## תהליך

### 1. טען סמכות + preflight עם ראיות

- קרא `packages/vfharness/state/<task-id>/task_plan.md` (או checkpoint).
- קרא את `Spec / אישור` שמופיע בכותרת; זה המקור המחייב ל־scope/authority.
- לפני Task 1 כתוב `state/<task-id>/preflight.md` (או שדה `preflight` ב־checkpoint) עם טבלה אמיתית — לא משפט "הכול נקי".

טבלת preflight חובה:

| בדיקה | Producer / Owner | Consumer / Dependent | משטח משותף | ממצא | פעולה |
|---|---|---|---|---|---|
| כל זוג Tasks שנוגע באותו קובץ/ממשק | Task N | Task M | file/interface/state | compatible / conflict | continue / ruling / stop |
| self-consistency לכל Task | Task N | Task N | files ↔ steps ↔ verify | consistent / gap | continue / ruling / stop |

כללים:

- כל Task מקבל לפחות שורת self-consistency אחת.
- כל זוג Tasks שחולק קובץ, schema, state, interface או output/input מקבל שורת producer/consumer.
- אם אין משטחים משותפים, כתוב את שורות ה־self-consistency; "scan is clean" בלי rows אינו evidence.
- conflict מקומי והפיך → ruling לפני ביצוע.
- conflict שחוצה stop class → הסלמה לפני Task 1.

### 2. בצע משימה

לכל Task בתוכנית:

1. הכרז: מבצע Task N.
2. עקוב אחרי הצעדים בסדר.
3. שינוי executable behavior / bugfix → `implementation-discipline.md` ומחזור RED → GREEN → REFACTOR כשאפשר לבדוק התנהגות.
4. הרץ את אימות התוכנית; שמור receipt/checkpoint אם הפלט ארוך.
5. אם נדרש review, העבר fresh-context packet לפי `critique-review.md`.
6. סמן הושלם רק אחרי proof ירוק וה־review הנדרש ללא blocker/important פתוח.

### 3. Rulings, not stalls

כשניסיון נכשל או מתגלה ambiguity:

1. retry תחום.
2. fallback קיים.
3. downgrade scope שמייצר artifact בטוח אם אפשר.
4. אם עדיין חסום וההחלטה **מקומית, הפיכה, ללא external side effect וללא authority/security gate** — כתוב ruling והמשך.
5. אחרת — הסלם.

אם משתמשים ב־`vf_graceful_escalation.py`, `safe_ruling` חייב להיות opt-in עם `safe_to_rule=True`; ברירת המחדל fail-closed.

Ruling אינו "החלפת בדיקה בהחלטה". Required sensor אדום נשאר אדום; אפשר לכל היותר להמשיך למשימות בלתי־תלויות ולשמור את הרכיב `UNPROVEN`/`BLOCKED`.

### 4. Parallel dispatch — רק עצמאות אמיתית

מותר fan-out כשיש 2+ משימות בלתי־תלויות ש:

- אינן כותבות לאותו file/schema/state;
- אינן producer/consumer זו של זו;
- אינן תלויות באותה החלטה לא פתורה;
- יכולות לקבל context צר משלהן.

לכל worker/agent שלח רק:

```text
Goal:
Spec / authority pointer:
Inputs:
Files / scope:
Constraints / non-responsibility:
Expected artifact:
Required proof:
```

אסור nested fan-out ללא צורך; implementer/reviewer לא פותחים שרשרת agents משלהם כברירת מחדל.

Fan-in:

1. קרא outputs/receipts.
2. בדוק conflict מול preflight + diff בפועל.
3. הרץ proof אינטגרטיבי / full suite הנדרש.
4. אם shared state הופיע בדיעבד — עצור parallel path ועבור לביצוע סדרתי.

אם אין יכולת להריץ agents במקביל, בצע סדרתית עם אותם scopes; אל תעמיס את כל ההיסטוריה לכל worker.

### 5. סיום

- אחרי כל המשימות: fresh whole-plan review לשינוי מהותי, ואז `verification-before-claim.md` לפני «סיימתי».
- אחרי שינוי קטלוג/כלל/פק: `python3 scripts/check-all.py`.
- לפני טענה ש־worker/automation/connector **רץ בפועל**: `python3 scripts/check-runtime-doctor.py --strict` וה־receipts הנדרשים.
- עדכן `state/<task-id>.json` (`status`, `completed_steps`, `unresolved`, `last_updated`).

## Stop classes — כאן כן עוצרים

| מצב | פעולה |
|---|---|
| פעולה הרסנית/בלתי־הפיכה או מחיקת מידע ללא rollback ברור | עצור והסלם |
| security / secrets / permissions / auth boundary | עצור והסלם לפי המדיניות |
| external side effect שמחייב gate מפורש (למשל merge ל־main, publish/boost/DM/payment לפי החוקה) | אל תעקוף gate |
| התוכנית שבורה כך שכל מסלול הוא ניחוש | עצור, תקן plan/spec עם האדם |
| חסר מקור / כלי `needsAuth` | failover לפי ORCHESTRA; אם אין מסלול מורשה — הסלם |
| required sensor/receipt נכשל | לא ruling מעליו; תקן/fallback או השאר `UNPROVEN`/`BLOCKED` |
| ₪ / Insights חסרים | `X ₪` / «אין ספירה»; לא ruling שממציא עובדה |
| runtime שני / `npx skills` / auto-DM | דחה — נעילת ליבה |

## Fresh review — בלי להרעיל עצמאות

שינוי מהותי רגיל מקבל reviewer טרי אחד לפני merge/claim. reviewer רואה **את המוצר והדרישה, לא את היסטוריית המחשבות של הכותב**: Goal, Spec, base/head או diff, proof receipts, out-of-scope. High-risk ממשיך ל־2 reviewers עצמאיים לפי `critique-review.md`.

Reviewer לא מריץ מחדש suite רק כי receipt קשה לקריאה; קודם קוראים evidence קיים. אם evidence stale/ambiguous/לא מכסה את הטענה — מריצים מחדש.

## לא (התאמת משרד)

- לא מתקינים `obra/superpowers` / subagent runtime — אין runtime שני.
- לא worktree חובה על Cloud (workspace יחיד) — branch ייעודי לפי מדיניות git.
- לא לדלג ל־main בלי המדיניות/אישור הרלוונטיים.
- לא להפוך ruling לדרך לעקוף QA או authority.

## קשר

- `playbooks/brainstorm-gate.md` — אישור לפני תוכנית
- `playbooks/writing-plans.md` — כתיבת התוכנית + dependencies
- `playbooks/implementation-discipline.md` — test-first לשינויי התנהגות
- `playbooks/critique-review.md` — fresh review / high-risk convergence
- `playbooks/systematic-debugging.md` — אם אימות נשבר על באג
- `playbooks/verification-before-claim.md` — לפני טענת סיום
- `playbooks/skill-first.md` — קרא skill לפני פעולה
