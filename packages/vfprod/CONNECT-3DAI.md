# איך מחברים את 3D AI Studio ל-Cursor

מנוי בתשלום ב-[www.3daistudio.com](https://www.3daistudio.com).  
פלייבוק: [`3DAISTUDIO.md`](3DAISTUDIO.md).  
אין מפתח API בגיט. OAuth בלבד.

## הכי קל: לחץ על הקישור (Desktop)

1. במחשב שבו מותקן Cursor, לחץ:  
   [הוסף 3D AI Studio ל-Cursor](cursor://anysphere.cursor-deeplink/mcp/install?name=threedaistudio&config=eyJ1cmwiOiJodHRwczovL21jcC4zZGFpc3R1ZGlvLmNvbS9tY3AifQ==)
2. Cursor ישאל אם להתקין שרת MCP בשם `threedaistudio`. אשר.
3. בדפדפן — Login ל-3D AI Studio → Allow.
4. ברשימת MCP אמור להופיע `threedaistudio` (Connect / ירוק).

אם הקישור לא נפתח, העתק לכתובת בדפדפן:

`cursor://anysphere.cursor-deeplink/mcp/install?name=threedaistudio&config=eyJ1cmwiOiJodHRwczovL21jcC4zZGFpc3R1ZGlvLmNvbS9tY3AifQ==`

**הערה:** ב-Cursor 3.15.6 deeplink עלול לא לעבוד — עדכן ל-3.15.12+ או הוסף ידנית למטה.

## מהפרויקט (אחרי pull)

הריפו מגדיר ב-[`.cursor/mcp.json`](../../.cursor/mcp.json) — **שם השרת חייב `threedaistudio`** (לא `3daistudio`; Cursor לא מציג מפתחות שמתחילים בספרה):

```json
"threedaistudio": {
  "url": "https://mcp.3daistudio.com/mcp"
}
```

1. פתח את **שורש הריפו** `velvet-factory-headquarters-os` ב-Cursor (לא תת-תיקייה).
2. `Ctrl+Shift+P` → **Developer: Reload Window**.
3. Customize → **MCPs** — אמור להופיע `threedaistudio`.
4. Connect → Allow בדפדפן.

## בלי קישור: הוספה ידנית

1. `Ctrl+Shift+P` → `View: Open MCP Settings`.
2. הוסף ל-`mcp.json` (או הדבק את כל הקובץ):

```json
{
  "mcpServers": {
    "canva": {
      "type": "http",
      "url": "https://mcp.canva.com/mcp"
    },
    "threedaistudio": {
      "url": "https://mcp.3daistudio.com/mcp"
    }
  }
}
```

3. שמור → Reload Window → Connect על `threedaistudio`.

## דרך האתר (גיבוי)

1. Login ב-[3daistudio.com](https://www.3daistudio.com).
2. Settings → **AI Assistants (MCP)** → Cursor → Allow.
3. חזור ל-Cursor → MCP → Connect.

מקור: [MCP](https://www.3daistudio.com/MCP) · v6.5 — «Available on all paid plans.»

## רואים רק Canva?

| סיבה | תיקון |
|---|---|
| לא עשית pull / Reload | `git pull` + Reload Window |
| שם ישן `3daistudio` | שנה ל-`threedaistudio` |
| Canva מ-global, פרויקט לא נטען | פתח את שורש הריפו או השתמש ב-deeplink למעלה |
| deeplink שבור (Cursor ישן) | עדכן Cursor או הוסף ידנית |

## Failover

אם MCP אפור / `needsAuth`: אתר → Drive → אין מפתח / ₪ מומצאים.

## אחרי Connect ירוק

«3DAI מחובר ב-Desktop» · `@studio-producer` · `3DAISTUDIO.md`.
