# איך מחברים את 3D AI Studio ל-Cursor

מנוי בתשלום ב-[www.3daistudio.com](https://www.3daistudio.com).  
פלייבוק: [`3DAISTUDIO.md`](3DAISTUDIO.md).  
אין מפתח API בגיט. OAuth בלבד.

## הכי קל: מהפרויקט (אחרי pull)

הריפו כבר מגדיר את השרת ב-[`.cursor/mcp.json`](../../.cursor/mcp.json):

```json
"3daistudio": {
  "type": "http",
  "url": "https://mcp.3daistudio.com/mcp"
}
```

1. ב-**Cursor Desktop** (לא Cloud Agent): `Ctrl+Shift+P` → `View: Open MCP Settings`.
2. אמור להופיע `3daistudio`. לחץ **Connect**.
3. בדפדפן — Login ל-3D AI Studio → Allow.
4. צ'אט Agent מקומי: «ייצא את המודל האחרון ל-STL» (אחרי אישור קונספט).

## דרך האתר (אם Connect לא נפתח)

1. Login ב-[3daistudio.com](https://www.3daistudio.com).
2. Settings → **AI Assistants (MCP)** → Cursor → Allow.
3. חזור ל-Cursor → MCP → Connect על `3daistudio`.

מקור: [Updates v6.5](https://www.3daistudio.com/Updates) · [MCP](https://www.3daistudio.com/MCP) — «Available on all paid plans.»

## מה לא לעשות

| חיפוש | למה |
|---|---|
| Marketplace / Plugins | אין תוסף חנות |
| Cloud Agent / `cursor.com/agents` | OAuth של 3DAI לא מגיע לענן |
| API key ב-`mcp.json` | OAuth בלבד — אין סוד בגיט |
| Flow → Bob | עוזר קנבס פנימי, לא MCP |
| הדפסה / ₪ מקרדיטים מ-HQ | רצפה + אדם. `vlicense` + סלייס |

## Failover

אם MCP אפור / `needsAuth`:

1. עבודה ישירות באתר (Text/Image → 3D → STL/3MF).
2. Drive `create_file` / העלאה לפי שם העבודה.
3. אין המצאת מפתח או ₪.

## אחרי Connect ירוק

הודע ל-HQ: «3DAI מחובר ב-Desktop».  
מושב: `@studio-producer` · `vfprod` · `3DAISTUDIO.md`.
