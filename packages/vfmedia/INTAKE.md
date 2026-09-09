# קליטת מדיה אוטומטית — vfmedia

מושב: **תפעול**. קטלוג יחיד: `catalog.json`.  
`python3 scripts/vfmedia.py validate` הוא **validator בלבד** — לא מנגנון ניטור.

**הרשאות Drive לסביבת הרקע הן תנאי להשלמת הדרישה** — לא תוספת אופציונלית.

## פקודות

```bash
python3 scripts/vfmedia.py intake status
python3 scripts/vfmedia.py intake selftest
python3 -m unittest discover -s packages/vfmedia/tests -p 'test_*.py' -v
# או:
python3 packages/vfmedia/tests/test_intake_hardening.py

# רקע עם Google Drive API (חובה להשלמה)
python3 scripts/vfmedia.py intake run --provider google --max-files 50
```

## פאזות (לדווח בנפרד)

| פאזה | משמעות |
|---|---|
| **רשום בקטלוג** (`registered`) | שורה ב־`catalog.json` (נשמרת לפני העברת Drive) |
| **אומת ונקלט** (`verified`) | בייטים אמיתיים נבדקו + קובץ ב־`02 - מקור` |
| **נבדק חזותית** (`visualReview`) | אופציונלי; **לא** חוסם קליטה |

מטא־דאטה / `size` לבד ≠ הוכחת הורדה. בלי קובץ ממשי — נשארים `registered`.

## עמידות

- רישום לקטלוג **לפני** `move`; התאוששות אם ההעברה הצליחה אך השמירה נכשלה (`intake-recovery.jsonl`)
- מנעול מקומי + `concurrency` ב־GitHub Actions
- מיזוג קונפליקטים מול כותבים אחרים לקטלוג / תור
- Backoff מתועד (1m→5m→15m→1h→4h) — **אין** עצירה קבועה אחרי N כשלים
- Fingerprint / revision / checksum — שינוי תוכן באותו `fileId` לא יורש `versionApproval`
- כשל `git push` / persist = כשל מפורש (exit 4); מצבי Blocked/Degraded נשמרים גם כש־exit ≠ 0

## תזמון

Workflow: `.github/workflows/vfmedia-intake.yml`  
יעד: **כל 5 דקות** — `cron: "*/5 * * * *"` (מינימום מתועד של GitHub Actions).  
מגבלה ממשית: ריצות מתוזמנות הן best-effort ועשויות להתעכב תחת עומס הפלטפורמה — לא משנים את יעד 5 הדקות בשקט.

## דוח השלמה (הפרדה חובה)

1. **מימוש** — הקוד והסכמות  
2. **בדיקות מבוקרות** — unittest + selftest  
3. **גישת Drive** — credentials על הרץ (תנאי)  
4. **הפעלה מתוזמנת** — workflow ירוק עם Drive API חי + `activation.proven`
