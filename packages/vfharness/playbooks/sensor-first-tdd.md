# Sensor-first TDD — אדום לפני תיקון

מקור דפוס: [obra/superpowers `test-driven-development`](https://github.com/obra/superpowers/tree/main/skills/test-driven-development) · קרוב ל־mattpocock `tdd`.  
רתמה: `vfharness` · אחרי: `verification-before-claim.md` · באג: `systematic-debugging.md`.

## חוק ברזל (משרד)

```
NO PACK/RULE FIX WITHOUT A FAILING SENSOR (OR REPRO) FIRST
```

בלי אדום אמיתי — אין ירוק אמיתי. «נראה לי שתוקן» = לא תוקן.

## מתי חובה

| מצב | מה נחשב RED |
|---|---|
| שינוי `check-*.py` / קטלוג / כלל | הסנסור נכשל לפני התיקון |
| באג בסקריפט CLI | פקודה/fixture שמחזירה fail עקבי |
| רגרסיית פלייבוק | צעד שחזור כתוב שנשבר |
| טענת «סיימתי» אחרי שינוי פק | `python3 scripts/check-all.py` אדום→ירוק |

**חריגים (רק עם סיבה כתובה):** אבטיפוס זריק, קובץ תצורה בלבד, מסמך ללא לוגיקה. לא «אין זמן».

## מחזור RED → GREEN → REFACTOR

1. **RED** — כתוב/הרץ בדיקה שנכשלת על *הבאג או הדרישה הזו* (סנסור, CLI, fixture). ודא שהכישלון הוא הנכון (לא import חסר).
2. **GREEN** — שינוי מינימלי שמייצר ירוק. בלי ניקוי מסביב.
3. **REFACTOR** — נקה רק כשהירוק יציב; אחרי כל ניקוי — שוב סנסור.
4. **CLAIM** — רק אחרי GREEN + `verification-before-claim.md`.

## מיפוי לעמיתים

| TDD קלאסי | VF |
|---|---|
| unit test | `scripts/check-*.py` / fixture CLI |
| watch fail | פלט סנסור אדום מלא |
| minimal code | diff קטן על פק קיים |
| delete code-before-test | אל תשאיר «ייחוס» שכתבת לפני RED |

## מה לא

| דפוס | למה |
|---|---|
| «נוסיף retry ונמשיך» | מסתיר אדום |
| המצאת ₪ / Insights כדי ליישר סנסור | נעול |
| runtime בדיקות שני / Jest על Cloud בלי צורך | הסנסורים הקיימים הם ה־SoT |
| לדלג על RED כי «ברור מה לשנות» | ניחוש |

## קישורים

- `systematic-debugging.md` · `verification-before-claim.md` · `writing-plans.md` · `executing-plans.md` · `skill-first.md`
