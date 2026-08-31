# פערי כלים · Grok / ChatGPT / Gemini / Perplexity מול HQ

לא פק חדש. הטמעה על `vfmcp` + השולחן הקיים.  
נבדק 31.8.2026 על Cloud Agent `bc-4dd7d6a7` (`nocturney@gmail.com`).  
**HQ שולח ג׳ימייל ואינסטגרם דרך כלים** (`constitution/SEND.md`). Treg **לא רלוונטי**. Drive יוצר מסמכים (`create_file`).

## מה יש כאן עכשיו (אומת בריצה)

| כלי | סטטוס | איך אומת |
|---|---|---|
| Gmail | ready · קריאה **ושליחה** (`send_message` / `reply` / `forward`) | namespace `Gmail` |
| Calendar | ready · `Asia/Jerusalem` | namespace `Google-calendar` |
| Drive | ready · חיפוש **ויצירה** (`create_file`) | namespace `Google-drive` |
| **Canva** | **ready** | `search-designs` החזיר `DAGoYmCu4c4` («Card - חגיגת האהבה שלכם») |
| WebSearch / WebFetch | ready · מקורי Cursor | כלי native בסוכן |
| GenerateImage | ready · מקורי Cursor | כלי native; אינסטגרם עדיין Canva קודם |
| Superdesign | skill · בלי CLI login | פלאגין על הדיסק |
| Treg | **לא רלוונטי** | לא login, לא `call`, לא failover |
| Mobbin | plugin · אין MCP כאן | namespace לא על Cloud Agent |
| FCC | לא כאן | נעול ב־`vffcc` |
| **3D AI Studio** | מנוי בעלים · **לא על Cloud Agent** | אתר + `vfprod/3DAISTUDIO.md`. MCP רשמי = OAuth מ־Settings, בלי מפתח בגיט |

אין גיליון סטודיו בשם Velvet Factory ב־Drive. גיליונות אישיים דולגו. לא ממציאים workbook ID.

## מה יש אצלם (קטלוג רשמי + מפת HQ)

מקורות: [Grok Connectors](https://x.ai/news/grok-connectors) (מאי 2026) · [ChatGPT Apps](https://help.openai.com/en/articles/11487775-connectors-in-chatgpt) · [Gemini Connected Apps](https://support.google.com/gemini/answer/13695044) · תזמורת `constitution/ORCHESTRA.md` · `constitution/SEND.md` (HQ שולח דרך כלים).  
סשן חי בחשבון עלול להיות מאחורי חומת הזדהות — לא ממציאים גוף שנחסם.

## סשן חי 31.8 (דפדפן, Christian Plus/Pro)

אומת ב־`bc-0d7c7cd6`. לא קטלוג רשמי — רק מה שנראה במסך.

| שולחן | מחברים חיים | דין HQ |
|---|---|---|
| ChatGPT Plus | Gmail מחובר (`nocturney@gmail.com`) — קריאה / low-risk. חיפוש + Create image מובנים | HQ כבר שולח Gmail. אין מחבר נוסף להתקין |
| Gemini Plus | Workspace ON (Gmail/Calendar/Docs/Drive/Keep/Tasks) · Search ON · YouTube ON. **Canva OFF**. Ads / Business Profile / GitHub OFF | Canva כבר ready כאן. לא מדליקים Canva בגימיני בשביל הסטודיו |
| Perplexity Pro | Connectors ריק (Discover/All/Connected/Available) | אין מחבר להתקין. חיפוש מובנה → `tools.web` |
| Grok (`grok.com` / `x.com/i/grok`) | **חומת התחברות X** — אין גוף מחברים | לא ממציאים. failover: כלים כאן + תזמורת |

אין מחבר חי אצלם שחסר כאן וחובה להתקין היום. Publish IG עדיין חסר אצל כולם במסך הזה.

### Grok / Grok Bot

| כלי שם | כאן | דין |
|---|---|---|
| שליחת אינסטגרם | Canva + `vfigos/SEND.md` (אין Publish MCP) | **wired failover** — Drive + Gmail `send_message` אותו תור |
| שליחת Gmail | `send_message` / `reply` / `forward` | **wired** — HQ שולח |
| מדפסות | אין בכוונה | **skip** — רצפה לא מ־HQ |
| Google Workspace (Gmail/Drive/Docs/Sheets/Calendar) **כתיבה+שליחה** | Gmail **שליחה**; Drive `create_file`; Calendar קריאה; Sheets דרך Drive | **wired** 31.8 — `SEND.md` |
| Outlook / OneDrive / SharePoint | אין | **skip** — לא ערימת הסטודיו |
| Notion / Linear / GitHub (Grok) | GitHub דרך `gh` לקריאה | **later** — לא MCP חדש |
| חיפוש רשת / X / DeepSearch | WebSearch + תזמורת | **wired** 31.8 — `tools.web` |
| יצירת תמונה | GenerateImage + Canva | **wired** 31.8 — `tools.image` |
| Bring Your Own MCP | Canva HTTP MCP | לא אגרגטור 400 כלים |

### ChatGPT

| כלי שם | כאן | דין |
|---|---|---|
| Gmail / Drive / Calendar / Canva | אותם ארבעה חיים כאן | כבר מחובר. HQ Gmail **send_message** מותר |
| חיפוש רשת / Deep Research | WebSearch + `vfresearch` | **wired** |
| DALL·E / יצירת תמונה | GenerateImage + Canva `generate-design` | **wired** |
| Code interpreter | Shell | כבר כאן |
| Canvas | Superdesign / Canva | failover קיים |
| Notion / Slack / HubSpot / Zapier | אין | **skip** — לא הסטודיו |
| Custom GPT | פקים + skills | לא מתקינים GPT כפול |

### Gemini

| כלי שם | כאן | דין |
|---|---|---|
| Gmail / Drive / Calendar | אותם MCP | כבר מחובר |
| חיפוש Google / Deep Research | WebSearch + תזמורת | **wired** |
| YouTube / Maps / Photos | אין | WebSearch / תזמורת. Treg **לא רלוונטי** |
| WhatsApp / Messages / Phone **שליחה** | אין בכוונה | **skip** — אדם `050-2517000` |
| Imagen / וידאו | Canva + GenerateImage | **wired** לסטילס. לא Veo |

### Perplexity

| כלי שם | כאן | דין |
|---|---|---|
| חיפוש חי + ציטוטים | WebSearch / WebFetch | **wired** |
| Collections / העלאת קובץ | `vfresearch/sources/` + Drive | כבר כאן |
| Deep Research | תזמורת 06:15 | כבר כאן |
| סשן מנוי / Cloudflare | חומה 30.8 | failover מיד ל־ChatGPT+Gemini. אין גוף מומצא |

## מה הותקן / הופעל בריצה הזו

לא MCP חדש עם סוד. לא פק חדש.

1. **Canva** — סומן `ready` על השולחן. Cloud Agent קורא עיצובים (כולל `DAGoYmCu4c4`).
2. **`tools.web`** — WebSearch + WebFetch על השולחן. זה מקביל החיפוש של ChatGPT / Gemini / Perplexity / Grok.
3. **`tools.image`** — GenerateImage + Canva `generate-design`. אינסטגרם עדיין Canva קודם.
4. **גיליון דרך Drive** — `packages/vfbooks/SHEETS.md`. בלי workbook ID מומצא.
5. **שליחה מ־HQ** — Gmail `send_message` מותר. IG: `vfigos/SEND.md` + `constitution/SEND.md`. Treg לא רלוונטי.
6. **3D AI Studio** — פלייבוק על `vfprod/3DAISTUDIO.md` (מנוי מאושר). לא MCP חדש בגיט. לא מפתח.

## מה לא הותקן — ולמה

| פער | למה לא |
|---|---|
| Publish MCP לאינסטגרם | אין namespace. failover: Canva+Drive+Gmail (`SEND.md`). לא ממציאים שעלה לפיד |
| וואטסאפ / מדפסות | אין MCP וואטסאפ. מדפסות ברצפה. אדם `050-2517000` |
| Treg | **לא רלוונטי** למשרד. לא login |
| Mobbin MCP | פלאגין על הדיסק; namespace לא על Cloud Agent. failover: `vfbriefux` |
| Google Sheets MCP | אין גיליון סטודיו שכריסטיאן נקב בשמו. Drive מייצא CSV כשייש נקוב |
| WhatsApp MCP | חיפוש/טיוטה רק אחרי מספר מהבעלים. שליחה אסורה |
| Studio MCP Hub / instapdown | מפה ב־`docs/MCP-FIT.md`. חיבור ב־Cursor Settings, לא סוד בגיט |
| FCC / `fcc-server` | נעול. לא על Cloud Agent |
| **3D AI Studio MCP** | מנוי יש. חיבור OAuth מ־Settings שלהם (Cursor Desktop / סביבת ענן). לא URL מומצא ב־`mcp.json`. Failover: אתר + Drive |
| 3D AI Studio REST / `uvx mcp-server-3daistudio` | מפתח + 2FA על המק בלבד. לא בגיט |
| SharePoint / Outlook / Notion / Slack | לא ערימת שדרות |

## Failover

כלי נפל → גיבוי באותו רגע (`constitution/ORCHESTRA.md`).  
לא ממציאים ₪, Insights, או גוף חסום.
