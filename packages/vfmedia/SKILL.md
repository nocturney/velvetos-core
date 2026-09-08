# vfmedia — קטלוג מדיה משותף

מושב: **תפעול** לקליטה. לא סוכן חדש.

כספת Drive אחת + קטלוג אחד. נוהל: `docs/MEDIA-VAULT.md`.

## מתי

קובץ נכנס לכספת, צריך תיאור לפי צפייה, או ברור מי מעביר נכנס→מקור / בעבודה / מאושר.

## עשה

1. `docs/MEDIA-VAULT.md` + `FOLDERS.json` — רק ארבע התיקיות הנעולות.
2. שורה ב־`catalog.json` לפי `catalog.schema.json`. תיאור ממה שנראה.
3. תפעול מעביר נכנס → מקור. GrokBot: Drive MCP. Cursor: סכמה.
4. `python3 scripts/vfmedia.py validate`
5. Control Plane intake state: `office/control-plane.json` → media SoT stays this catalog (WIP/finished/BTS/unknown). Never a second catalog.

## אל תעשה

- קטלוג שני / גיליון מקביל
- להמציא מק״ט או ₪
- לחשוב שהעלאה או תיקיית «מאושר לפרסום» הם אישור גרסה
- לשנות הרשאות שיתוף או למחוק קבצים
- אוטו־DM / בוסט / Print מ־HQ
