# adr

מקור: `manage_adr`.  
אצלנו: החלטות שכבר כתובות בחוקה / שולחן. קריאה בלבד מהסקריפט.

## הרצה

```bash
python3 scripts/vfmem.py adr
```

## מה מופיע

- HQ לא שולח אינסטגרם / ג׳ימייל
- אין ₪ או Insights מומצאים
- איסוף שדרות, צינור אחד
- אין סודות בגיט
- אין `curl \| bash` של הבינארי DeusData מתוך הריפו

## כתיבה

שינוי ADR = עריכת המקור (`velvet-factory-desk.mdc`, `constitution/CONSTITUTION.md`, או `catalog.json` + `LOCK.md`).  
הסקריפט לא כותב החלטות חדשות.
