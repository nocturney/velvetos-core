# משטח פקודות (Command Surface)

דפוסים מ־Twenty (⌘K), Monday (agents + permissions), NocoBase (AI עם הרשאות), Zoho One (OS לאפליקציות).

לא אפליקציה חיה בריפו. זה **חוזה** לממשק עתידי ולסוכני HQ: כל פעולה חייבת להופיע ב־`capabilities.json`.

## עקרונות

1. **Registry לפני כפתור** — אם אין שורה ב־`capabilities.json`, הממשק לא מציג פעולה והסוכן לא ממציא אותה.
2. **Human-in-loop** — פעולות עם `gate: lead` דורשות ראש צוות (₪, בוסט, TikTok, מודעות).
3. **אותו מנדט כמו Cursor** — שליחת Gmail/IG דרך כלים מותרת; אוטו־DM אסור; אין המצאת ₪/Insights.
4. **תצוגה ≠ מושב** — הקונסולה לא יוצרת מושב שישי ולא runtime שני.

## קיצורי ניווט (השראה Twenty)

| מפתח רעיוני | לאן |
|---|---|
| G → P | לוח צינור (`PIPELINE-BOARD.md`) |
| G → B | בריף / portlets |
| G → C | capabilities list |
| G → T | ציר לקוח (`vfsales/hq/CUSTOMER-TIMELINE.md`) |
| ⌘K | חיפוש capability + job folder |

## מיפוי מושבים → אזורים בממשק

| מושב | אזור UI | פקים |
|---|---|---|
| ראש צוות | Home portlets + החלטות | `vfops`, `vfbriefux`, `vfharness` |
| סטודיו | פניות + הצעות | `vfconvert`, `vfsales`, `vfcopy` |
| תפעול | כסף / ספרים | `vfcost`, `vfbooks`, `vfbiz` |
| ייצור | תור הדפסה / מק״ט | `vfprod`, `vfsku`, `vlicense` |
| צמיחה | לוח תוכן / Insights | `vfgrowth`, `vfcovers`, `vfigos`, `vfinsights` |

## קבצים

- רשימת יכולות: [`capabilities.json`](capabilities.json)
- לוח צינור: [`PIPELINE-BOARD.md`](PIPELINE-BOARD.md)
- Portlets לבריף: `packages/vfbriefux/hq/PORTLETS.md`
- ADR: `docs/OFFICE-OS-EMBED-he.md`
