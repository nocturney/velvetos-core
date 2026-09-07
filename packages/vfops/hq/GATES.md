# שערי בריף — אישור בלחיצה, לא סגירה אוטומטית

מושב: **תפעול** (`@studio-operations`). לא פק חדש.

הבריף 07:00 נשאר תצוגה 3 (`MAIL.html`). חריץ **01** מקבל כפתורי כן / דחה / דחה-למועד לכל פריט פתוח ב־`GATES.json`.

## מה זה כן

1. ריכוז נתונים **מדיסק** — `orders.json` + סנאפשוט Invoice4U + לולאה. לא קריאת inbox למילוי הבריף.
2. לחיצת אדם במייל (`mailto:` חזרה ל־`nocturney@gmail.com`) או CLI:

```
python3 scripts/vfops_loop.py gate --id G-001 --decision yes
python3 scripts/vfops_loop.py gate --id G-001 --decision no
python3 scripts/vfops_loop.py gate --id G-001 --decision defer
```

3. אחרי `yes`:
   - `quote` — עובר לתור רצפה **רק** אם יש סכום מראש צוות. אחרת נשאר `ממתין לסכום`.
   - `content` — עובר ל־`vfigos` **אחרי** `PREFLIGHT.md` עבור. לא Publish מכאן.
   - `b2b-line` — לא פותח את הקו. רק רושם החלטה ל־`vfbiz/hq/decisions/`. הנעילה ב־`LOCK.md`.

## מה זה לא

- לא zero-touch על ₪ או וואטסאפ לקוח (`050-2517000` נשאר אדם).
- לא Print מ־HQ.
- לא קריאת `in:inbox` ל־07:00 (חוק הבריף נשאר).

אירוע דיסק: `brief.gate_applied`.
