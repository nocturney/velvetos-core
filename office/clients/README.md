# office/clients · תבניות בלבד

הקבצים כאן הם **תבניות**. אין לקוחות אמיתיים בריפו הציבורי.

| תבנית | מתי | נכנס ל |
|---|---|---|
| `INTAKE-TEMPLATE.md` | פנייה חדשה / לקוח חוזר לא מתועד | אחרי מילוי → רשומת לקוח |
| `CLIENT-RECORD-TEMPLATE.md` | אחרי Intake | מקור פרטי מחוץ לגיט הציבורי |

## מקור פרטי (חי)

- רשומות לקוח חיות: Drive / תיבת משרד פרטית שהבעלים מצביע עליה — **לא** commit ל־`office/clients/` עם שמות/טלפונים.
- ליד / פנייה: `packages/vfconvert/` + Gmail thread שצוין.
- מחיר: רק אחרי GRILL + סכום מראש צוות (`vfsales/QUOTE.md`, `vf_quote_ladder.py`).
- SLA תגובה: `packages/vfsales/SLA.md` — מחייב תהליך פנימי; **לא** שולח הודעות אוטומטיות ולא יוצר התחייבות חדשה מול לקוח בלי אדם.

## זרימה

```
פנייה → Intake (תבנית) → Client Record (פרטי)
      → SLA תגובה ראשונה (בלי ₪)
      → GRILL / quote ladder
      → fulfill / close
      → (אופציונלי) דוח חודשי מתבנית vfops
```

תרחישי חניכה: `office/learning/SCENARIOS.md`.
