# planning-with-files — דפוס על vfharness

מקור: [OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files)  
רישום: `packages/vfresearch/LINKS.json` → `planning-with-files`

## מה לקחנו

שלושה קבצי markdown על דיסק — לא רק ב-context window:

| קובץ | תפקיד |
|---|---|
| `task_plan.md` | שלבים, checkboxes, החלטות |
| `findings.md` | מחקר, מקורות, גילויים |
| `progress.md` | יומן סsession, סנסורים, שליחות |

+ בסוף משימה ארוכה: `checkpoint.json` לפי `templates/checkpoint.schema.json` (כבר היה).

## מתי לפתוח תיקייה

משימה עם **5+ tool calls** או **3+ שלבים** (פנייה→הצעה, חבילת תוכן, סקירת קישורים שבועית, משמרת `vfe2b`).

משימה חד-פעמית (שאלה, סיעור מוחות) → **בלי** שלושת הקבצים.

## איפה על הדיסק

```
packages/vfharness/state/<task-id>/
├── task_plan.md      ← מהעתקת templates/task_plan.md
├── findings.md
├── progress.md
└── checkpoint.json   ← בסגירה
```

`<task-id>` = slug ASCII קצר (למשל `inquiry-yossi-stl`, `weekly-links-2026-08-31`).

## צעדים

1. צור `state/<task-id>/` והעתק שלוש תבניות; החלף `{{JOB_NAME}}`, `{{TASK_ID}}`, `{{PACK}}`, `{{DATE}}`.
2. בתחילת כל turn (או אחרי `/clear`): קרא שלושת הקבצים לפני החלטות.
3. גילוי → `findings.md`. פעולה → `progress.md`. שלב הושלם → סמן ב-`task_plan.md`.
4. לפני `worker_done`: אימות (kodo) + `checkpoint.json`.
5. נכשל פעמיים על אותו שדה → `templates/escalation.md`.

## מה **לא** מתקינים

- `npm install planning-with-files`
- Claude Code / Codex hooks (`UserPromptSubmit`, `PreCompact`, `Stop` gate)
- קבצים בשורש הריפו — רק תחת `state/<task-id>/`

Cursor Cloud Agent = המשרד. ההזרקה היא **קריאה מפורשת** של הקבצים, לא hook.

## קשר ל-vfe2b

| planning-with-files | vfe2b / harness |
|---|---|
| task_plan phases | `crews/run.md` משמרת |
| findings | `vfresearch` / מקור Gmail |
| progress log | סנסורים + `#נשלח-מ-HQ` |
| session recovery | `state/<task-id>/` + checkpoint |

## תבניות

- `templates/task_plan.md`
- `templates/findings.md`
- `templates/progress.md`
