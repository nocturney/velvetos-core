# איך מחברים Studio MCP Hub

HTTP בלי מפתח בגיט. 18 כלים חינמיים (רקע, גודל, `print_ready`, CMYK). תשלום x402 / ארנק — **רק אחרי ראש צוות**. אין NFT מ־HQ.

פלייבוק ליבה: [`CORE-MCP.md`](CORE-MCP.md).  
VF: תלת־ממד — פריפלייט STL ב־`vfprod/PREFLIGHT.md`. לא מחליפים סלייסר ב־CMYK.

הריפו מגדיר ב-[`.cursor/mcp.json`](../../.cursor/mcp.json):

```json
"studiomcphub": {
  "type": "http",
  "url": "https://studiomcphub.com/mcp"
}
```

## A) Desktop

1. במחשב עם Cursor, לחץ:
   [הוסף Studio MCP Hub ל-Cursor](cursor://anysphere.cursor-deeplink/mcp/install?name=studiomcphub&config=eyJ1cmwiOiJodHRwczovL3N0dWRpb21jcGh1Yi5jb20vbWNwIn0=)
2. אשר `studiomcphub`.
3. Reload Window → Customize → MCPs.

אם הקישור לא נפתח:

`cursor://anysphere.cursor-deeplink/mcp/install?name=studiomcphub&config=eyJ1cmwiOiJodHRwczovL3N0dWRpb21jcGh1Yi5jb20vbWNwIn0=`

או הדבק את הבלוק למעלה ל־MCP Settings.

## B) Cloud Agent

`.cursor/mcp.json` לבדו לא מגיע לענן — **Team MCP** (אותו כלל כמו 3DAI).

1. [cursor.com/dashboard](https://cursor.com/dashboard) → Cloud Agents → **Integrations & MCP**
2. Add MCP server → HTTP
   - **Name:** `studiomcphub`
   - **URL:** `https://studiomcphub.com/mcp`
3. שמור. בכל משתמש: cursor.com/agents → MCP → הפעל `studiomcphub`.
4. OAuth / GCX רק אם צריך כלי בתשלום. כלים חינמיים עובדים בלי ארנק.

## מה VF משתמש / מדלג

| משתמש | מדלג |
|---|---|
| `search_tools` · `remove_background` · `resize_image` | `print_ready` · `convert_color_profile` · NFT · ארנק / x402 |

מופע נייר / יופי יכול להדליק `print_ready` ב־`mcpBind`.

## Failover

MCP אפור → Canva / `vfcanva/studio/render.py` / 3DAI + STL preflight. אין ₪ מ־GCX. HQ לא מדפיס.

מקור: [studiomcphub.com/mcp](https://studiomcphub.com/mcp) · [github.com/codex-curator/studiomcphub](https://github.com/codex-curator/studiomcphub)
