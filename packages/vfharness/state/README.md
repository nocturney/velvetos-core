# Checkpoints

המודל שוכח כל סשן. הקבצים כאן זוכרים.

כתוב `<task-id>.json` לפי `../templates/checkpoint.schema.json` אחרי כל צעד משמעותי במשימה רב-שלבית.

- `running` — יש צעד הבא
- `blocked` — חסר מקור / שדה / אישור אדם; או `gate` פתוח (₪ / אדם)
- `escalated` — חבילת `templates/escalation.md`
- `done` — אפשר למחוק אחרי שהארטיפקט יושב בפק הקבוע

## שדות משמרת (אופציונלי)

| שדה | מתי |
|---|---|
| `goal` | תנאי סיום אחד (DeerFlow `/goal`) — לא ₪ |
| `planned_steps` | לפני ביצוע — תצוגה מקדימה של 3–8 צעדים (דפוס OMA, בלי runtime שני) |
| `crew` | שם הצוות מ-`vfe2b/crews/` |
| `outcome` | `worker_done` / `escalation` / `decision_gate` בסגירה |
| `pulse` | `working` / `blocked` / `idle` — דופק |
| `verification` | סנסור או שדה שנקרא; או `חסר` |
| `gate` | `{ kind, waiting_for, reason }` — שער עמיד עד אישור |

דוגמה חיה: `../templates/checkpoint.example-run.json`. קבלה: `../templates/run-receipt.md`.

אל תשמור סודות, שמות מלאים מיותרים, או ₪ מומצא.

משימות חד-פעמיות לא צריכות קובץ כאן.
