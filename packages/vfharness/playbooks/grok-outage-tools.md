# כלים כשמכסת Grok ריקה

לא פק חדש. לא מושב שישי.  
מטרה: המשרד **לא נעצר** כש־Grok במכסה 100%.  
נמדד בסשן 31.8.2026 (Cloud Agent).

פיילאובר = אותו תפקיד כמו Grok, בלי תחושת מעבר.  
בריף 07:00: HQ קורא `send_message` אל `nocturney@gmail.com`. אין לחיצת Send אצל הבעלים.  
אינסטגרם: אין MCP Publish — LIVE-PACKET נשאר (אין כלי, לא מדיניות בלבד).

## מצב חי (31.8.2026)

| כלי | סטטוס בסשן | תפקיד בפיילאובר | נעול? |
|---|---|---|---|
| Gmail MCP | `ready` | קריאה + **`send_message`** בריף משרד אל `nocturney@gmail.com` | reply / forward / שליחה ללקוח — נעול |
| Calendar MCP | `ready` | קריאה + **`create_event`** למשבצת חיה שכבר בלוח התוכן | לא נעול לקריאה / אירוע משובץ |
| Drive MCP | `ready` | חיפוש לפי שם עבודה | לא (בלי תיקיות אישיות) |
| Canva MCP | `ready` | עיצוב / export · `.cursor/mcp.json` → `https://mcp.canva.com/mcp` | Publish ל־IG — אין כלי |
| `vfcanva/studio/render.py` | על הדיסק | PNG אם Canva נופל | לא |
| Superdesign | skill, אין namespace כאן | גרפיקה אם Canva נופל | failover ל־render.py |
| Treg | אין namespace | חי web / Insights | דולג · אין ספירה / HeyOrca למוזיקה |
| Mobbin | אין namespace | UX בריף | תבניות `vfbriefux` |
| ChatGPT / Gemini / Perplexity | אין MCP | מחקר 06:15 | דיסק + «אין חדש במשרד» |
| Instagram Publish | **אין MCP** | Grok היה כלי השליחה | נשאר LIVE-PACKET לאדם |
| WhatsApp | Desktop / טיוטת `vf_office` | שיחת לקוח | אדם שולח `050-2517000` (`send=false`) |

## מה HQ מפעיל לבד (בלי לחכות לבעלים)

1. קריאת תיבה / לוח / דרייב־לפי־שם.
2. `render_mail.py` ואז `send_message` — בריף 07:00 אל `nocturney@gmail.com` בלבד (`htmlBody` תצוגה 3 מ־`vfbriefux/MAIL.html` + כריכות `cid`). `create_draft` רק אם צריך לעצור לפני שליחה. MAIL-PACK הוא חלופת טקסט אם MCP נופל. בלי לחיצת בעלים.
3. `create_event` — משבצת חיה שכבר קיימת ב־`vfgrowth` (למשל G005 חמישי 12:00).
4. Canva + `render.py` + שקפים ב־`vfcovers`.
5. תור `#מוכן-ל-Grok` / `#פרסום-חי-דחוף` + LIVE-PACKET.

## מה נשאר נעול (אין כלי, לא רק מדיניות)

- העלאה ל־`@velvets_cloud` — אין MCP Publish לאינסטגרם במחסן / ב־Cloud Agent הזה. Grok היה השולח. חבילה: `vfigos/live/`.
- `send_message` ללקוח / `reply` / `forward` — Deny. בריף משרד אל עצמכם — **Allow** בפיילאובר.
- וואטסאפ / בוסט / אוטו־DM.

חיבור MCP חדש לשליחת אינסטגרם דורש מוצר + סודות מחוץ לגיט. לא ממציאים שרת ולא שמים מפתחות בריפו.

## Failover מיידי (אותו תור)

| נפל | מעבירים ל־ |
|---|---|
| Grok מכסה | הכלים בטבלה למעלה |
| Canva `needsAuth` | `packages/vfcanva/studio/render.py` → Superdesign |
| Treg / Mobbin / תזמורת בלי MCP | פקים על הדיסק · «אין ספירה» / «אין חדש במשרד» |
| Gmail MCP down | MAIL-PACK להדבקה ידנית · לא ממציאים פנייה |

נוהל פרסום: `playbooks/grok-failover.md`.  
מסמך קבע: `docs/GROK-FAILOVER.md`.
