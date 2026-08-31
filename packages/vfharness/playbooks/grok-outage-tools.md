# כלים · Grok מנהל · תחליף מלא במכסה

מודל: [`constitution/GROK.md`](../../constitution/GROK.md).

**שוטף:** Grok שולח. **מכסה 100%:** הטבלה למטה = **תחליף מלא** (לא גיבוי).

פיילאובר = אותו תפקיד כמו Grok, בלי תחושת מעבר.  
בריף 07:00 במכסה: HQ `send_message` אל `nocturney@gmail.com`.  
**IG:** HQ **Publish ישיר** ל-`@velvets_cloud` — חובה לחבר MCP (לא LIVE-PACKET לאדם כברירת מחדל).

## מצב חי (31.8.2026 → יעד)

| כלי | סטטוס | שוטף | במכסה (תחליף מלא) |
|---|---|---|---|
| **Grok Bot** | מנהל ראשי | Gmail · IG · מדפסות | — (מכסה ריקה) |
| Gmail MCP | `ready` | Grok | **`send_message`** בריף + שרשורים |
| Calendar MCP | `ready` | Grok / HQ | קריאה + `create_event` משובץ |
| Drive MCP | `ready` | Grok / HQ | חיפוש + `create_file` |
| Canva MCP | `ready` | Grok / HQ | עיצוב · **export · Publish IG** |
| **Instagram Publish** | **wire-required** | Grok | **HQ Publish ישיר** — חובה לחבר |
| Cursor HQ | `ready` | עיבוד מואצל | **שליחה + Publish** |
| ChatGPT / Gemini / Perplexity | תזמורת | עיבוד | עיבוד + failover מחקר |
| `render.py` / Superdesign | על הדיסק | failover Canva | failover Canva |
| WhatsApp | **אין MCP** | אדם `050-2517000` | אדם |

## חובת חיבור — Publish IG

1. Cursor Team MCP — Instagram Publish ל-`@velvets_cloud` (סודות ב-Dashboard, לא בגיט).
2. Canva — export + publish path ל-IG (`vfigos/SEND.md`).
3. עד ש-MCP מחובר: failover Gmail+Drive **באותו תור** — `#ממתין-ל-כלי-IG` (אין MCP Publish).

## מה HQ מפעיל במכסה

1. תיבה / לוח / Drive לפי שם עבודה.
2. `render_mail.py` → `send_message` — בריף HTML תצוגה 3 + כריכות `cid`. `create_draft` רק לעצירה לפני שליחה.
3. **Publish IG** — קרוסלה / ריל / פוסט / סטורי ישיר ל-`@velvets_cloud`.
4. Canva + `render.py` + `vfcovers`.
5. `#פרסום-חי-דחוף` + LIVE-PACKET — **HQ Publish**, לא «מחכים לגרוק».

## מה נשאר נעול

- `send_message` **ללקוח** / blast — Deny (בריף משרד אל עצמכם — Allow).
- וואטסאפ / בוסט / אוטו־DM.
- Print מ-HQ.

**אדם** מעלה ב-IG **רק** אם Publish MCP + Gmail נפלו.

## Failover מיידי

| נפל | מעבירים ל־ |
|---|---|
| Grok מכסה | כל הטבלה (תחליף מלא) |
| Publish MCP | Canva export + Gmail+Drive · `#ממתין-ל-כלי-IG` |
| Canva `needsAuth` | `render.py` → Superdesign |
| Gmail MCP | MAIL-PACK · לא ממציאים פנייה |

נוהל: `grok-failover.md` · `docs/GROK-FAILOVER.md`.
