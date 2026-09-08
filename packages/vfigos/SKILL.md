# vfigos — סקירה, שיבוץ, ושליחה דרך כלים

מושב: צמיחה. Instagram office. **HQ שולח דרך כלים** (`SEND.md`).

מקבל חבילה מ־`#vfgrowth`+`#vfcovers`. בודק `#משובץ` `#לא-זז` `#לא-בוסט`.  
אין אוטו־DM, אין follow-back, אין צפיית סטורי כטריק. אין בוסט בלי ראש צוות.

**מאגר מדיה משותף:** [`docs/MEDIA-VAULT.md`](../../docs/MEDIA-VAULT.md) · קטלוג יחיד [`packages/vfmedia/catalog.json`](../vfmedia/catalog.json). תפעול בלבד קולט נכנס→מקור. עובדים על נגזרת ומוודאים `versionApproval` לגרסה המדויקת; אין קטלוג מקביל לכלי.

סדר שליחה: `packages/vfigos/SEND.md` + `constitution/SEND.md`.  
חיבור Publish/Insights/Stories: [`CONNECT-IG.md`](CONNECT-IG.md) — canonical [`adelaidasofia/instagram-mcp`](https://github.com/adelaidasofia/instagram-mcp) (`ready-codespace`, stdio; `remote_access` pending).  
אוטונומיית Cloud: [`REMOTE.md`](REMOTE.md) (Google Cloud Run · Streamable HTTP + bearer · scale-to-zero). Codespace: [`DEPLOY-CODESPACE.md`](DEPLOY-CODESPACE.md). 
לגאסי: [`LEGACY-IG-MCP.md`](LEGACY-IG-MCP.md) (`jlbadano/ig-mcp`).  
פריסה: [`DEPLOY-CODESPACE.md`](DEPLOY-CODESPACE.md).  
**validate → apply → verify** (`list_media`/`get_media`) לפני תג live.  
אם אין Publish MCP חי — Drive `create_file` + Gmail `send_message` באותו תור.  
תגיות: `#נשלח-מ-HQ` · `#ממתין-ל-כלי-IG`. Grok הוא גיבוי אופציונלי בלבד.

לוח עומד: `vfgrowth/CALENDAR.md` + `RHYTHM.md`. מסירת שיבוץ: `HANDOFF-STANDING-he.md`.  
Metricool אינו נדרש.
