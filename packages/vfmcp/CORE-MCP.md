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

רשימת מכונה: [`core-mcp.json`](core-mcp.json). דוגמת Desktop: [`mcp.desktop.example.json`](mcp.desktop.example.json).

Cloud Agent רואה HTTP מ־Team MCP (כמו Canva / 3DAI). `npx` / `uv` מקומי לא רצים בענן — לכן Sheets וואטסאפ האישי נשארים ב־`~/.cursor`, לא בקובץ הפרויקט.

אין ארנק / x402 בגיט. אין ₪ מומצא. HQ לא מדפיס.
