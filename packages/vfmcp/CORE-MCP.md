# Office MCP בליבה

מושב: **ליבה**. לא פק חדש. לא סוד בגיט.

VelvetOS Core **מתקין** את כלי המשרד. מופע (הפקטורי / יופי / אחר) **כורך** `mcpBind` — משתמש במה שצריך, מדלג על השאר.

| שרת | איפה | VF (maker-print) |
|---|---|---|
| **Studio MCP Hub** | `.cursor/mcp.json` → `https://studiomcphub.com/mcp` | רק כלים חינמיים שימושיים (רקע / גודל). **לא** CMYK / `print_ready` — הסטודיו תלת־ממד. [`CONNECT-STUDIOHUB.md`](CONNECT-STUDIOHUB.md) |
| **Google Sheets** | Desktop `~/.cursor/mcp.json` (`mcp-gsheets`) | יומן `office/ledger/bindings.json`. בלי מפתח: CSV + Drive. [`CONNECT-SHEETS.md`](CONNECT-SHEETS.md) |
| **WhatsApp** | Desktop `lharries/whatsapp-mcp` (טלפון אישי) | חיפוש + טיוטה. **שליחה אסורה** — אדם `050-2517000`. [`CONNECT-WHATSAPP.md`](CONNECT-WHATSAPP.md) |
| **Gemini API** | env `GEMINI_API_KEY` + `scripts/vf_gemini.py` | **לא** מנוי `gemini.google.com`. לא aliargun / לא RLabs MCP. בלי מפתח: **חסר מפתח Gemini**. [`CONNECT-GEMINI.md`](CONNECT-GEMINI.md) · [`SUBSCRIPTIONS.md`](SUBSCRIPTIONS.md) |
| **ChatGPT API** | env `OPENAI_API_KEY` + `scripts/vf_chatgpt.py` | **לא** מנוי `chatgpt.com`. בלי מפתח: **חסר מפתח ChatGPT**. [`CONNECT-CHATGPT.md`](CONNECT-CHATGPT.md) |
| **Instagram MCP bridge** | Cloud Team MCP `instagram` / project remote bridge | Read, Insights and independent live verification. **Not scheduler authority; not Meta-owned.** Publication scheduler = `packages/vfigos/PUBLISHER.json` -> official Meta Instagram Graph API. DM off. |

**לגאסי:** `jlbadano/ig-mcp` — לא קנוני. [`vfigos/LEGACY-IG-MCP.md`](../vfigos/LEGACY-IG-MCP.md).

רשימת מכונה: [`core-mcp.json`](core-mcp.json). דוגמת Desktop: [`mcp.desktop.example.json`](mcp.desktop.example.json).

Cloud Agent רואה HTTP מ־Team MCP (כמו 3DAI / Instagram read-verify bridge). `npx` / `uv` / stdio מקומי לא רצים בענן בלי חיבור מרוחק — לכן Sheets וואטסאפ האישי נשארים ב־`~/.cursor`. Instagram קנוני: Cloud Team MCP `remote_access: ready` (2026-09-09).

אין ארנק / x402 בגיט. אין ₪ מומצא. HQ לא מדפיס.


## Publication authority · 2026-09-26
Cloudflare Publisher is the only active Instagram scheduler/queue. The official provider API is Meta Instagram Graph API. OpenPost is frozen. Canva/vfcanva are forbidden/removed. The Instagram MCP is a non-Meta-owned read/Insights/live-verification bridge. See `packages/velvetos/TOOL-STATUS.json`.
