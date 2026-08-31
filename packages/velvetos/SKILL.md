# velvetos — ליבת VelvetOS

תשתית (לא מושב שישי). מערכת ניהול עסק + סושיאל אוטונומי.  
ה־tenant הפעיל היום: **velvet-factory** (שימוש נוכחי לא נשבר).

## מתי

- «VelvetOS», אוניברסלי, tenant חדש, multi-IG, עסק אחר
- לפני שממציאים פק חדש לעסק חדש

## עשה

1. קרא `KERNEL.md` + `ACTIVE.json`.
2. טען `tenants/<activeTenant>.json` — אלה עובדות הסטודיו לסיבוב.
3. צינור: `PIPELINE.md`. ערוצים: `CHANNELS.md`.
4. דוגמאות בלבד: `tenants/_examples/` — לא להפעיל בלי ראש צוות.
5. אחרי שינוי: `python3 scripts/check-velvetos.py` ו־`python3 scripts/check-all.py`.

## אל תעשה

- לא לשנות `ACTIVE.json` בלי ראש צוות
- לא פק חדש לכל עסק
- לא להמציא ₪ / Insights / handles
- לא אוטו־DM / בוסט
- לא להחליף את Velvet Factory כשה־ACTIVE הוא `velvet-factory`

Mention: `@workflow-architect` / `@studio-operations` · skill: `.cursor/skills/vf-velvetos/SKILL.md`
