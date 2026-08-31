# 3D AI Studio — מנוי הסטודיו

מושב: **ייצור** (`vfprod`). לא פק חדש.  
חיבור: [`CONNECT-3DAI.md`](CONNECT-3DAI.md) · MCP: `https://mcp.3daistudio.com/mcp`  
שער: `vlicense/GATE.md` · סלייס: `vfcost` + `hq/PLAYBOOK.md`.

אין מפתח בגיט. אין ₪ מומצא. אין הדפסה מ-HQ.

## מה זה בשביל Velvet Factory

רשת מתמונה או מטקסט → remesh → ייצוא STL/3MF לסלייס.  
**לא** מחליף סלייסר, אישור ראש צוות, או הוכחת רצפה לאינסטגרם.

| שלב | 3DAI | אצלנו |
|---|---|---|
| פנייה | קונספט ויזואלי | אדם `050-2517000` |
| הצעה | קובץ לבדיקה | סלייס + `vfcost` |
| הדפסה | STL/3MF | אדם על המיטה |
| תוכן | רנדור קונספט | Canva / רצפה — לא «הוכחת מיטה» |

## זרימה (אחרי אישור קונספט)

1. MCP (Desktop) או אתר: Text/Image → 3D → גודל בס״מ → STL/3MF.
2. Drive לפי שם העבודה.
3. `vlicense` + ארבע וי ב-`CHECKLIST.md` + סלייס.
4. מחיר רק אחרי סכום מראש צוות — «X ₪» בלי סלייס.

## שכבות

| שכבה | מתי |
|---|---|
| MCP `threedaistudio` | Cursor Desktop + OAuth |
| אתר | תמיד גיבוי אם MCP נפל |
| API Dashboard | לא נדרש למחבר הרשמי |

Cloud Agent: `threedaistudio.status` = `needsAuth` עד OAuth בדסקטופ.
