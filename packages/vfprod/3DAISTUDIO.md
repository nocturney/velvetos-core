# 3D AI Studio — מנוי הסטודיו

מושב: **ייצור** (`vfprod`). לא פק חדש.  
חשבון: [www.3daistudio.com](https://www.3daistudio.com) — מנוי בעלים.  
חיבור: [`CONNECT-3DAI.md`](CONNECT-3DAI.md) · MCP: `https://mcp.3daistudio.com/mcp` (`threedaistudio`)  
שער: `vlicense/GATE.md` · כרטיס: `vfsku` · סלייס: `vfcost` + `hq/PLAYBOOK.md`.

אין מפתח בגיט. אין ₪ מומצא. אין הדפסה מ־HQ. אין קטלוג אוטומטי.

## מה זה בשביל Velvet Factory

שולחן אחד (Meshy / Tripo / Rodin / Hunyuan / Prism) שמייצר רשת מתמונה או מטקסט, מתקן טופולוגיה, ממיר פורמט, ומייצא STL / 3MF להדפסה.

זה **לא** מחליף סלייסר, לא מחליף אישור ראש צוות, ולא מחליף הוכחת רצפה לאינסטגרם.

| שלב בצינור | מה 3DAI נותן | מה נשאר אצלנו |
|---|---|---|
| פנייה / שיחה | קונספט מתמונה או תיאור — לאישור ויזואלי | אדם בוואטסאפ `050-2517000` |
| הצעה | קובץ לבדיקת כדאיות אחרי ייצוא | סלייס + `vfcost` + ₪ מראש צוות |
| הדפסה | STL/3MF + גודל פיזי בס״מ + remesh | אדם על המיטה. HQ לא דוחף למדפסת |
| איסוף | — | שדרות בלבד |
| תוכן | רנדור קונספט | לא «הוכחת מיטה». Canva / רצפה |

## זרימה (אחרי אישור קונספט)

1. MCP (Desktop, OAuth) או אתר: Text/Image → 3D → גודל בס״מ → STL/3MF.
2. Drive לפי שם העבודה.
3. `vlicense` + ארבע וי ב־`CHECKLIST.md` + סלייס.
4. מחיר מכירה רק אחרי סכום מראש צוות. בלי סלייס — «X ₪».

שאלה מועילה (אחרי אישור): «המר ל־STL, סקלה ל־10 ס״מ להדפסה» — לא «תמחר» ולא «שלח למדפסת».

אחרי ייצוא STL: `python3 scripts/vf_office.py print preflight model.stl` (`PREFLIGHT.md`) — תיבת גבול בלבד. אין ₪ ואין שעות.

## שכבות

| שכבה | מתי |
|---|---|
| MCP `threedaistudio` | Desktop `.cursor/mcp.json` או Cloud Team MCP — `CONNECT-3DAI.md` |
| אתר | תמיד גיבוי אם MCP נפל |
| API Dashboard | לא נדרש למחבר הרשמי. מפתח רק ב־env במק אם ראש צוות רוצה באצ׳ |

Cloud Agent: namespace `3DAIStudio` **ready** (אומת 2026-09-01 — `get_credit_balance`). Desktop: `.cursor/mcp.json`. Cloud: Team MCP + OAuth ב-cursor.com/agents (`CONNECT-3DAI.md`).

עריכת Blender מקומית (Desktop בלבד, אחרי ראש צוות): [`BLENDER-MCP.md`](BLENDER-MCP.md) — לא על Cloud Agent; לא מחליף את השכבה הזו לקונספט/STL.  
משפחת CAD/DCC נוספת (OpenSCAD / FreeCAD / SketchUp / multiCAD / …): [`CAD-MCP.md`](CAD-MCP.md) — רובם skip על Cloud.

## מה ליישם (על פקים קיימים)

| עבודה | איך | נעילה |
|---|---|---|
| תמונת לקוח → דמות / מזכרת | Image to 3D אחרי רקע נקי | אישור קונספט. לא הצעת מחיר |
| «מעמד ל…» בלי STL ציבורי | Text to 3D אחרי חיפוש `vlicense` | מותג ישראלי = עצירה |
| תיקון רשת לפני סלייס | remesh / mesh repair + STL | לא מחליף `stlforge` אם הקובץ כבר אצלנו |
| גודל פיזי | המרה עם ס״מ | סלייסר מאמת. HQ לא ממציא שעות |
| שרשרת חוזרת | Flow template באתר | לא באצ׳ מכירה |
| רנדור לאישור | render מתוך 3DAI | לא הוכחת רצפה ל־IG |

לא מיישמים: מק״ט בלי אישור + סלייס · הדפסה מ־HQ · מחיר מקרדיטים · העתקת מותג ישראלי · אוטו־DM של STL · פק `vf3dai`.

מודל מ־3DAI = אותו שער כמו Meshy/Tripo: **לא «ציבורי מסחרי» אוטומטית**.

## צינור קצר — פנייה עם תמונה

```
פנייה + תמונה
  → @discovery-coach: מידות / שימוש / איסוף
  → ראש צוות: כן לקונספט?
  → 3DAI (MCP או אתר) → STL בדרייב
  → vlicense + CHECKLIST + סלייס
  → vfsales רק אחרי סכום
  → אדם מדפיס → איסוף שדרות
```

## Failover

| מה נפל | מעבירים מיד ל־ |
|---|---|
| MCP לא מחובר / `needsAuth` | אתר 3DAI + דרייב + ממשיכים |
| API / מפתח חסר | אתר. לא ממציאים מפתח |
| האתר למטה | מאגר פתוח ב־`vlicense` או הדמיה דו־ממדית (`GenerateImage` / Canva) |
| אין קרדיטים בדשבורד | «חסר קרדיט ספק» לראש צוות. לא ממציאים ₪ |

ארטיפקט failover: `vfresearch/sources/YYYY-MM-DD-orchestra.md`.
