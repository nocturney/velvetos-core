# effective-html — מפת בריף מייל

מקור: https://github.com/plannotator/effective-html  
תבנית חיה: `hq/brief-email.html`  
מבנה נעול: `packages/vfops/BRIEF.md` + `packages/vfops/hq/BRIEF-SLOTS.md`

## מתי

- HQ ממלא טיוטת בריף אחרי Calendar + Gmail read.
- Grok מקבל HTML או מעתיק ממנו לגוף המייל ב־07:00.
- Mobbin / Superdesign לא זמינים → עובדים ישירות על `brief-email.html`.

## skill → חריץ

| חריץ בריף | effective-html | הערה |
|---|---|---|
| מעטפת (כותרת, תאריך, פוטר) | `html` documents | RTL, כהה/זהב |
| 01 קודם החלטה | `html-plan` | כן/לא/דחה — בלי לחץ מזויף |
| 02 כסף בעבודה | `html` tables | רק מה שכבר במערכת |
| 03 הדפסה + תור | `html-plan` sequence | שעות תור מאומתות בלבד |
| 04 מונטיזציה | documents | וואטסאפ + איסוף שדרות |
| 05 משרד | `html-plan` | שורה אחת מהתזמורת |
| 06 עמוד | charts-and-data | רק מספרים שנמדדו |
| 07 פיד | documents | כריכות `#vfcovers` |

## התקנה אופציונלית (מק מקומי)

```bash
npx skills add plannotator/effective-html --skill html-plan
```

Cloud Agent: מספיק להשתמש ב־`brief-email.html` כרפרנס — לא חובה להתקין.
