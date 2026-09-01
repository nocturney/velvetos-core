# Instagram Publish — חיבור ופערים

חשבון: **@velvets_cloud**. פרוטוקול שליחה: [`SEND.md`](SEND.md) · חוקה: [`constitution/SEND.md`](../../constitution/SEND.md).

## מצב נוכחי (2026-09-01)

| שכבה | סטטוס |
|---|---|
| Canva MCP | **ready** — עיצוב / export |
| Instagram **Publish** MCP | **אין** ב-Cursor Cloud Agent |
| Failover HQ | Canva + Drive `create_file` + Gmail `send_message` |
| תג תור | `#ממתין-ל-כלי-IG` עד ש-Publish מחובר |

אין להמציא שפורסם לפיד אם Publish לא רץ.

## מה לבדוק ב-Dashboard

1. [cursor.com/dashboard](https://cursor.com/dashboard) → **Cloud Agents** → **Integrations & MCP**
2. חפש אינטגרציה **Meta**, **Instagram**, או **Facebook Business**
3. אם קיימת — הוסף כ-Team MCP + OAuth ב־[cursor.com/agents](https://cursor.com/agents)
4. עדכן `.cursor/vf-desk.json` → `tools.instagramPublish.status` מ־`not-available` ל־`ready`

## מסלולים עד שיש Publish MCP

### A) Failover אוטומטי (ברירת מחדל HQ)

```
vfcopy (כיתוב) → Canva (מדיה) → Drive (חבילה) → Gmail (nocturney@gmail.com)
```

תגיות: `#נשלח-מ-HQ` + `#ממתין-ל-כלי-IG`

### B) פרסום חי דחוף

- אדם בטלפון / Meta Business Suite
- או Grok Bot כ**גיבוי** (לא שער ראשי) — `LIVE-PACKET.md`

### C) API צד שלישי (אופציונלי, לא בגיט)

סוכן Agency `carousel-growth-engine` מזכיר Upload-Post API — **רק** אחרי אישור ראש צוות:

- מפתח ב־`~/.cursor/` או Dashboard, **לא** ב-repo
- עדיין עומד בחוק: אין אוטו-DM, CTA וואטסאפ `050-2517000`

### D) Meta Graph API (עתידי)

דורש Facebook App + Business account + review. לא מוטמע ב-HQ — פתח פק/`vfmcp` רק אם ראש צוות מבקש.

## אחרי חיבור Publish

1. עדכן `tools.instagramPublish` ב־`vf-desk.json`
2. הרץ `python3 scripts/check-vf-desk.py`
3. בדיקה: טיוטה ל־`@velvets_cloud` → `#נשלח-מ-HQ` **בלי** `#ממתין-ל-כלי-IG`
4. שורה ב־`CHANGELOG.md`

## מה לא

- ManyChat / בוט DM — אסור (`compliance.noAutoDm`)
- «שלחו DM» בכיתוב
- Treg
