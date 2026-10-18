# שערי בריף — אישור בלחיצה, לא סגירה אוטומטית

מושב: **תפעול** (`@studio-operations`). לא פק חדש.

Morning Brief נשאר תצוגה 3 (`MAIL.html`) כאשר הוא מופעל. חריץ **01** מקבל כפתורי כן / דחה / דחה-למועד רק לפריטים שבאמת דורשים החלטת בעלים; Organic Growth שגרתי עובר `instagram.publish` ויופיע כאן רק אם policy החזיר `REQUIRE_OWNER_APPROVAL` / `human_required`.

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
   - `content` — במסלול owner-required בלבד, `yes` מספק את האישור הנקודתי ואז החבילה עדיין חייבת exact-final `PREFLIGHT.md` + `instagram.publish` לפני `vfigos`. לא Publish מכאן.

## מה זה לא

- לא zero-touch על ₪ או וואטסאפ לקוח (`050-2517000` נשאר אדם).
- לא Print מ־HQ.
- לא קריאת `in:inbox` למילוי Morning Brief (חוק הבריף נשאר; אין cutoff שעוני).

אירוע דיסק: `brief.gate_applied`.
