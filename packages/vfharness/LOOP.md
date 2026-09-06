# לולאת סוכן — גבולות והסלמה

לא קריאת מודל אחת. מחזור חסום: תכנן → בצע → אמת → תקן → התקדם או הסלם.

מצע הביצוע במשימה ארוכה הוא **מצב מובנה** (checkpoint), לא היסטוריית השיחה — דפוס SKILLSTATE (`playbooks/skillstate.md`): בכל צעד \(A_t=(P,\Sigma_t,O_t)\); אחרי עדכון מאומת זורקים reasoning.

```
plan = steps on an existing pack
write planned_steps[] to checkpoint   # plan preview — OMA embed, no second runtime
Σ = load checkpoint                   # SKILLSTATE execution state
for step in plan:
    O = latest observation only       # not full chat / tool dump
    for attempt in 1..2:
        result = do(step)             # prompt = (P, Σ, O)
        verdict = sensor_or_field_check(result)
        if verdict.passed:
            Σ = Σ ⊕ state_patch       # write checkpoint; discard R_t
            break
        if not verdict.retryable: escalate
    else:
        escalate("retry budget exhausted")
return best artifact + unresolved
```

## גבולות (משרד, לא דמו)

| גבול | ברירת מחדל | למה |
|---|---|---|
| ניסיונות לצעד | 2 | בלי לולאה אינסופית |
| אותו סנסור נכשל | 3 ואז עצירה | פער במדריך או בסנסור |
| שליחה חיצונית | HQ דרך כלים (`SEND.md`) | לא מחכים לגרוק / לאדם |
| ₪ בלי מקור | אסור | כותבים `X ₪` |
| Treg | לא בשימוש | WebSearch / תזמורת |
| Replay שיחה מלאה | אסור במשימה ארוכה | רק \(P,\Sigma,O\) — `skillstate.md` |

כשנגמר התקציב: מחזירים את הארטיפקט הטוב ביותר, מה שנגמר, מה שפתוח, וסיבת העצירה. לא מסתירים כשל מאחורי עברית שוטפת.

## הסלמה היא לא כישלון

חבילת הסלמה (`templates/escalation.md`):

- ההחלטה שצריך מאדם
- האפשרות המומלצת
- מה כבר נוסה
- מה קורה אם אין תשובה (ברירת המחדל הבטוחה: לא לשלוח, לא להמציא ₪)
- מצביע לארטיפקט

## כישורי היום

| כישור | איפה הלולאה נעצרת |
|---|---|
| בריף בוקר | אחרי רשימת דחוף / מחכה לאדם. אדם מחליט משמרת. |
| פנייה | אחרי טיוטת הצעה. אדם שולח בוואטסאפ. |
| תוכן | אחרי סקירת `vfigos`. Grok משבץ/שולח. |

## רקע

בזמן שאדם סוקר, אפשר לתכנן את הצעד הבא על פק קיים. אסור לשלוח בינתיים.
