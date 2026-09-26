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
יעד: **כל 3 שעות** — `cron: "23 */3 * * *"` (8 ריצות ביום, בדקה 23 UTC). שינוי מפורש של הבעלים (2026-09-26).  
למה: בפועל GitHub הריץ רק ~6–8 ריצות ביום מתוך `*/5` (פער חציוני 3.7 שעות, 2026-09-17..25), בעוד שתזמונים דלילים בריפו הזה (6 שעות, יומי) רצים במלואם. הקצב החדש שווה או עולה על מה שרץ בפועל, בלי רעש. להרצה מיידית: `workflow_dispatch`. הנפח קטן (81 קבצים ב־17 ימים) והריצה מדפדפת וממשיכה, כך שאין אובדן.  
`runner.py` כותב את בלוק `schedule` מהקוד בכל ריצה, כך שהמצב לא נשאר מיושן.

## דוח השלמה (הפרדה חובה)

1. **מימוש** — הקוד והסכמות  
2. **בדיקות מבוקרות** — unittest + selftest  
3. **גישת Drive** — credentials על הרץ (תנאי)  
4. **הפעלה מתוזמנת** — workflow ירוק עם Drive API חי + `activation.proven`
