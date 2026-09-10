# vfmedia — קטלוג מדיה משותף

מושב: **תפעול** לקליטה. לא סוכן חדש.

כספת Drive אחת + קטלוג אחד. נוהל: `docs/MEDIA-VAULT.md`.

## מתי

קובץ נכנס לכספת, צריך תיאור לפי צפייה, צריך לקבוע Asset Truth, או ברור מי מעביר נכנס→מקור / בעבודה / מאושר.

## עשה

1. `docs/MEDIA-VAULT.md` + `FOLDERS.json` — רק ארבע התיקיות הנעולות.
2. קליטה אוטומטית: `python3 scripts/vfmedia.py intake run` (או `selftest` / `status`). ראה `INTAKE.md`.
3. שורה ב־`catalog.json` לפי `catalog.schema.json`. פאזות: רשום / אומת / חזותי — בנפרד.
4. כשיש ראיה מספקת, הוסף `truth` לאותה שורה: `verified_real|derived_real|illustrative_ai|synthetic|unverified`, מקור, זכויות ושימושים. אם חסר `truth`, Visual Foundry מתייחס לנכס כ־`unverified` לצורכי טענות.
5. זכור: Asset Truth אינו Claim Truth. טענה ציבורית על מדידה/עומס/כשל/הצלחה חייבת לעבור `packages/vfom/CONTENT-CONTRACT.schema.json` עם evidence refs אמיתיים. AI לא מוכיח תוצאה פיזית.
6. תפעול מעביר נכנס → מקור (או runner + Drive MCP apply-moves). GrokBot: Drive MCP. Cursor: סכמה + runner.
7. `python3 scripts/vfmedia.py validate` — **רק** בדיקת סכמה; לא ניטור תיקייה.
8. Control Plane intake state: `office/control-plane.json` → media SoT stays this catalog. Never a second catalog.

## אל תעשה

- קטלוג שני / גיליון מקביל
- להמציא מק״ט או ₪
- להעלות truth level בלי evidence
- לחשוב שהעלאה או תיקיית «מאושר לפרסום» הם אישור גרסה
- להשתמש ב־`synthetic`/`illustrative_ai` כהוכחה לתוצאה פיזית
- לשנות הרשאות שיתוף או למחוק קבצים
- אוטו־DM / בוסט / Print מ־HQ
