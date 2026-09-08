# קליטת מדיה אוטומטית — vfmedia

מושב: **תפעול**. קטלוג יחיד: `catalog.json`.  
`python3 scripts/vfmedia.py validate` הוא **validator בלבד** — לא מנגנון ניטור ולא קליטה.

## פקודות

```bash
# סטטוס עמיד (פאזות נפרדות)
python3 scripts/vfmedia.py intake status

# בדיקה מקומית בלי Drive
python3 scripts/vfmedia.py intake selftest

# ריצת קליטה מול Google Drive API (סביבת רקע עם credentials)
python3 scripts/vfmedia.py intake run --provider google --max-files 50

# ריצה מול ייצוא MCP / listing
python3 scripts/vfmedia.py intake run --provider listing --listing PATH.json --move-mode pending
# אחרי העברה ב־Drive MCP:
python3 scripts/vfmedia.py intake apply-moves --confirmed PATH.json
```

## פאזות (לדווח בנפרד)

| פאזה | משמעות | חוסם קליטה? |
|---|---|---|
| **רשום בקטלוג** (`registered`) | שורה ב־`catalog.json` | — |
| **אומת ונקלט** (`verified`) | הורדה אומתה + קובץ ב־`02 - מקור` | — |
| **נבדק חזותית** (`visualReview`) | תיאור לפי צפייה | **לא** — לא חוסם קליטת קובץ נגיש |

## עמידות

- מנעול ריצה: `state/intake.lock` (אין ריצות חופפות)
- עימוד: `state/intake-runner.json` → `pagination.pageToken`
- ניסיונות חוזרים: עד 3 לקובץ ב־`retries`
- מניעת כפילויות: לפי `sourceFile.id` בקטלוג הקנוני
- אירועים: `data/intake-events.jsonl` (`media.intake.registered` / `verified` / `failed` / `move_pending`)
- תור + בריף: `office/control/inbox.json` + `data/intake-brief.json` + HANDOFF phases

## תזמון

Workflow: `.github/workflows/vfmedia-intake.yml` — cron כל 6 שעות + `workflow_dispatch`.  
Exit `3` = חסר Drive auth בסביבת הרקע (Degraded/Blocked — לא מתיימרים שהקליטה רצה).

## חוקים

- אין קטלוג שני
- אין המצאת מק״ט / ₪ / Insights
- אין שינוי הרשאות שיתוף / מחיקה
- קליטה **לא** תלויה ב־Instagram או Gmail
- אין לסמן «קליטה אוטומטית הושלמה» בלי הוכחת הפעלה (`activation.proven`)
