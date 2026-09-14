# לולאת סוכן — גבולות, rulings והסלמה

לא קריאת מודל אחת. מחזור חסום: תכנן → בצע → אמת → retry/fallback/downgrade → ruling בטוח או הסלם.

מצע הביצוע במשימה ארוכה הוא **מצב מובנה** (checkpoint), לא היסטוריית השיחה — דפוס SKILLSTATE (`playbooks/skillstate.md`): בכל צעד \(A_t=(P,\Sigma_t,O_t)\); אחרי עדכון מאומת זורקים reasoning.

```text
plan = steps on an existing pack
write planned_steps[] to checkpoint   # plan preview — OMA embed, no second runtime
preflight = evidence matrix           # shared files/interfaces + self-consistency
Σ = load checkpoint                   # SKILLSTATE execution state
for step in plan:
    O = latest observation only       # not full chat / tool dump
    result = retry(step, budget=2)
    if not passed: result = fallback(step)
    if not passed: result = downgrade_scope(step)
    if not passed and safe_to_rule(step):
        result = ruling(step)          # local + reversible + no authority gate
    if not passed:
        escalate(step)
    if passed:
        Σ = Σ ⊕ state_patch            # write checkpoint; discard R_t
return best verified artifact + unresolved
```

מימוש הסולם: `scripts/vf_graceful_escalation.py`.

## גבולות (משרד, לא דמו)

| גבול | ברירת מחדל | למה |
|---|---|---|
| ניסיונות retry זהים לצעד | 2 | בלי לולאה אינסופית |
| fallback | פעם אחת לפי כלי/מסלול קיים | לא לנסות את אותו דבר בשם אחר |
| downgrade scope | artifact בטוח וחלקי אם אפשר | לא להישאר עם ידיים ריקות |
| safe ruling | opt-in בלבד אחרי classification | אוטונומיה בלי עקיפת authority |
| required sensor אדום | לא ניתן לעקיפה ב־ruling | evidence > claims |
| Replay שיחה מלאה | אסור במשימה ארוכה | רק \(P,\Sigma,O\) — `skillstate.md` |

## Safe ruling

Ruling מותר רק כשההחלטה:

- מקומית והפיכה;
- אינה security/secrets/permissions/auth boundary;
- אינה פעולה הרסנית/בלתי־הפיכה;
- אינה external side effect שמחייב human/constitutional gate;
- אינה ממציאה עובדה, ₪, Insights או receipt;
- אינה מחליפה required sensor/test/provider proof.

פורמט:

```text
Ruling: <decision> — <why> — <cost_if_wrong>
```

בקוד `safe_to_rule=False` הוא ברירת המחדל. caller חייב לאשר במפורש `safe_to_rule=True`; ruling malformed או guard חסר → escalation רגיל.

## Evidence-bearing preflight

לפני Task 1 בתוכנית מרובת משימות: `playbooks/executing-plans.md` מחייב טבלה עם:

- שורה לכל Task שמוכיחה self-consistency של files/steps/verify;
- שורה לכל זוג Tasks שחולק file/interface/state/output-input;
- producer/consumer relation + conflict finding + פעולה.

"preflight clean" בלי rows אינו evidence.

## Parallel fan-out

Parallelism מותר רק למשימות עצמאיות ללא shared-write state וללא producer/consumer relation. כל worker מקבל Goal + Spec pointer + scope + constraints + expected artifact + proof. אחרי fan-in מריצים conflict check ו־integration proof. אם מתגלה shared state — חוזרים לסדרתי.

## כשאין פתרון בטוח

עוברים להסלמה (`templates/escalation.md`) עם:

- ההחלטה שצריך מאדם;
- האפשרות המומלצת;
- מה כבר נוסה;
- מה קורה אם אין תשובה — safe default;
- מצביע לארטיפקט/receipt.

הסלמה אינה כישלון; היא stop class מוכר. לא מסתירים כשל מאחורי עברית שוטפת.

## Stop classes

עוצרים במקום ruling כאשר יש:

1. destructive/irreversible action;
2. security/secrets/permissions/auth boundary;
3. external side effect שחייב gate מפורש לפי constitution/policy;
4. תוכנית שבורה כך שכל מסלול הוא ניחוש;
5. required sensor/receipt שנכשל — אפשר להמשיך רק עבודה בלתי־תלויה, אבל הרכיב נשאר `UNPROVEN`/`BLOCKED`.

## כישורי היום

| כישור | איפה הלולאה נעצרת |
|---|---|
| בריף בוקר | אחרי artifact מאומת + gates החלים; לא ממציאים נתון חסר |
| פנייה/הצעה | לפי authority של הערוץ וה־SEND policy; מחיר חסר נשאר `X ₪` |
| תוכן | אחרי QA/gates/receipt החלים; publish claim רק עם proof חי |

## רקע

בזמן שמחכים להחלטה אנושית מותר להתקדם במשימות **בלתי־תלויות** שאינן מושפעות מה־gate. אסור לבצע את ה־side effect החסום או לטעון שהוא הושלם.
