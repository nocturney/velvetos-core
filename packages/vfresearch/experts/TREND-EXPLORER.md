# Trend Explorer — חוקר מגמות

מושב: ייצור (מחקר) + צמיחה (מסירה). מודול: `expert-trend-explorer`.  
Treg **לא רלוונטי**. WebSearch / orchestra בלבד.

## מתי

- פתיחת עונה (`#vfseason`)
- סאונד לריל (`MUSIC.md` + `vf-ig-music` skill)
- סקירת קישורי השראה שבועית (`WEEKLY.md` + `LINKS.json`)
- פורמט תוכן חדש לבדיקה (קרוסלה, POV, timelapse)

## שרשרת

```
שאלה / עונה / פורמט
  → (אופציונלי) last30 fan-out — hq/LAST30.md · skill vf-last30
  → WebSearch / WebFetch / gh (או orchestra אם חסום)
  → רצפת ביטחון · nothing-solid מותר
  → מפת מקורות (משקל: ראשי / משני / חלש)
  → handoff: vfgrowth (תוכן) · vfom (ריל) · vfigos (לוח)
```

## מחקר 30 יום (קהילה)

כשצריך «מה אנשים אומרים עכשיו» / השוואת כלים / discovery בלי נושא סגור:

1. `.cursor/skills/vf-last30/SKILL.md` + `hq/LAST30.md`
2. `@trend-researcher` או `@research-synthesist`
3. ארטיפקט: `sources/YYYY-MM-DD-<topic>-last30.md`
4. בלי `npx skills` / last30days CLI · בלי מפתחות X/TikTok

## כרטיס מגמה

| שדה | חובה |
|---|---|
| אות | מה ראינו (עובדה, לא הייפ) |
| מקור | URL / HeyOrca / IG paste / «אין גוף» |
| תוקף | תאריך · עונה · פג תוקף אם לא ידוע |
| פעולה | טיוטה / ממתין / דולג |
| מסירה | pack + `@slug` |

## מוזיקה לריל

1. `SOURCES-MUSIC.json` + HeyOrca שבועי
2. `@trend-researcher` — לא ממציא שמות שירים
3. מסירה ל־`vfom` / `vfigos`

## שבועי (חובה)

`.cursor/skills/vf-weekly-links/SKILL.md` — `@research-synthesist`

## לולאת שיפור

סוף יום: איזה מקור היה שימושי? איזה query מיותר? עדכון `LINKS.json` באותו יום אם URL חדש.

## חפיפה קיימת

- `DAILY.md` (06:15) · `vfseason/CALENDAR.md` · `@trend-researcher` על השולחן

## אסור

- «#1 trending» בלי מקור
- גוף חסום → המצאה
- Insights מומצאים
