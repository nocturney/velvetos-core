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
| **3D AI Studio** | **ready** | namespace `3DAIStudio` · `get_credit_balance` אומת 2026-09-01 |
| WebSearch / WebFetch | ready · מקורי Cursor | כלי native בסוכן |
| GenerateImage | ready · מקורי Cursor | כלי native; אינסטגרם עדיין Canva קודם |
| Superdesign | skill · בלי CLI login | פלאגין על הדיסק |
| Treg | **לא רלוונטי** | לא login, לא `call`, לא failover |
| Mobbin | plugin · אין MCP כאן | namespace לא על Cloud Agent |
| FCC | לא כאן | נעול ב־`vffcc` |
| Gemini **API** | Desktop/Cloud env · `vf_gemini.py` | **לא** מנוי הדפדפן. בלי מפתח: **חסר מפתח Gemini**. `CONNECT-GEMINI.md` |
| ChatGPT **API** | Desktop/Cloud env · `vf_chatgpt.py` | **לא** מנוי `chatgpt.com`. בלי מפתח: **חסר מפתח ChatGPT**. `CONNECT-CHATGPT.md` · `SUBSCRIPTIONS.md` |

נזרע 31.8: תיקייה `VF HQ · משרד` + ארבעה גיליונות כותרת בלבד (`office/ledger/bindings.json`). גיליונות אישיים דולגו. לא ממציאים workbook ID; בלי binding כותבים **חסר גיליון**.

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
| צ'אט מנוי (`chatgpt.com`) | **לא** מדפדפן Cloud | `vf_chatgpt.py` אם יש `OPENAI_API_KEY`. Plus ≠ API. [`SUBSCRIPTIONS.md`](SUBSCRIPTIONS.md) |

### Gemini

| כלי שם | כאן | דין |
|---|---|---|
| Gmail / Drive / Calendar | אותם MCP | כבר מחובר |
| חיפוש Google / Deep Research | WebSearch + תזמורת | **wired** |
| YouTube / Maps / Photos | אין | WebSearch / תזמורת. Treg **לא רלוונטי** |
| WhatsApp / Messages / Phone **שליחה** | אין בכוונה | **skip** — אדם `050-2517000` |
| Imagen / וידאו | Canva + GenerateImage | **wired** לסטילס. לא Veo |
| צ'אט מנוי (`gemini.google.com`) | **לא** מדפדפן Cloud | `vf_gemini.py` אם יש מפתח. מנוי ≠ API. בלי אזעקות Google — [`SUBSCRIPTIONS.md`](SUBSCRIPTIONS.md) |
| MCP `aliargun/mcp-server-gemini` | לא מותקן | freeze יולי 2025 · מודלים 2.5 קשיחים |
| MCP `RLabs-Inc/gemini-mcp` | לא מותקן | מעודכן (3.x, יולי 2026) אבל עדיין API + Veo. לא פותר מנוי |

### Perplexity

| כלי שם | כאן | דין |
|---|---|---|
| חיפוש חי + ציטוטים | WebSearch / WebFetch | **wired** |
| Collections / העלאת קובץ | `vfresearch/sources/` + Drive | כבר כאן |
| Deep Research | תזמורת 06:15 | כבר כאן |
| סשן מנוי / Cloudflare | חומה 30.8 | failover מיד ל־WebSearch. אין גוף מומצא. לא `perplexity-user-mcp` ב־Cloud |

## מה הותקן / הופעל בריצה הזו

לא MCP חדש עם סוד. לא פק חדש.

1. **Canva** — סומן `ready` על השולחן. Cloud Agent קורא עיצובים (כולל `DAGoYmCu4c4`).
2. **`tools.web`** — WebSearch + WebFetch על השולחן. זה מקביל החיפוש של ChatGPT / Gemini / Perplexity / Grok.
3. **`tools.image`** — GenerateImage + Canva `generate-design`. אינסטגרם עדיין Canva קודם.
4. **גיליון דרך Drive** — `packages/vfbooks/SHEETS.md`. בלי workbook ID מומצא.
5. **שליחה מ־HQ** — Gmail `send_message` מותר. IG: `vfigos/SEND.md` + `constitution/SEND.md`. Treg לא רלוונטי.
6. **3D AI Studio** — HTTP `threedaistudio` → `https://mcp.3daistudio.com/mcp`. Desktop: `.cursor/mcp.json`. Cloud: namespace `3DAIStudio` **ready** (אומת 2026-09-01). פלייבוק `vfprod/3DAISTUDIO.md` + `CONNECT-3DAI.md`.
7. **Studio MCP Hub** — HTTP `studiomcphub` → `https://studiomcphub.com/mcp` ב־`.cursor/mcp.json`. VF מדלג CMYK/`print_ready`. `CONNECT-STUDIOHUB.md`.
8. **Sheets + WhatsApp בליבה** — רשומים ב־`core-mcp.json`. Desktop Connect (`CONNECT-SHEETS.md` / `CONNECT-WHATSAPP.md`). VF: יומן לפי bindings; וואטסאפ `send=false`. בלי Connect: `vf_office.py`.
9. **Gemini API + ChatGPT API (לא מנויי דפדפן)** — `vf_gemini.py` / `vf_chatgpt.py` + `SUBSCRIPTIONS.md`. Cloud לא פותח `gemini.google.com` / `chatgpt.com`. בלי מפתח: **חסר מפתח Gemini** / **חסר מפתח ChatGPT**.
10. **מארח מנויים = המק בשדרות** — מק ייעודי, לא PC ווינדוס. `HOST.md`. Gems/GPTs/Canvas/Deep Research/Perplexity Pro בכרום **על המק**. Codex + Gemini CLI שם בלי מפתח API. Cloud = `WebSearch` + קריאת `sources/`.

## מה לא הותקן — ולמה

| פער | למה לא |
|---|---|
| Publish MCP לאינסטגרם | אין namespace. failover: Canva+Drive+Gmail (`SEND.md`). לא ממציאים שעלה לפיד |
| וואטסאפ **שליחה** / מדפסות | MCP מותר לחיפוש/טיוטה. שליחת לקוח VF = אדם `050-2517000`. מדפסות ברצפה. `vf_office.py convert draft` |
| Treg | **לא רלוונטי** למשרד. לא login |
| Mobbin MCP | פלאגין על הדיסק; namespace לא על Cloud Agent. failover: `vfbriefux` |
| `mcp-gsheets` ב־`.cursor/mcp.json` של הפרויקט | מפתח שירות. Desktop `~/.cursor` בלבד (`CONNECT-SHEETS.md`) |
| Infobip / ManyChat ב־mcp.json | VF אין Infobip. אין אוטו־DM. Infobip רק למופע שכבר משלם |
| Studio Hub NFT / x402 | בלי ארנק בגיט. כלים חינמיים בלבד עד ראש צוות |
| FCC / `fcc-server` | נעול. לא על Cloud Agent |
| **Headroom** (`headroom-ai`) | **local optional** — proxy/MCP דורש תהליך מקומי; Cloud Agent sandbox. דפוס CCR/ContentRouter ב-`vfharness/playbooks/context-thrift.md` בלי dependency. Mac: `uv tool install "headroom-ai[all]"` + `headroom wrap cursor` אחרי lead seat |
| `aliargun/mcp-server-gemini` / `RLabs-Inc/gemini-mcp` ב־mcp.json | מפתח בגיט / npx על Cloud / Veo. מנוי הדפדפן לא מתחבר. `SUBSCRIPTIONS.md` + `vf_gemini.py` |
| `perplexity-user-mcp` / [vscode-perplexity-mcp](https://github.com/automations-project/vscode-perplexity-mcp) | patchright + עוגיות Cloudflare. צורך Pro בלי API — **רק מק**, לא Cloud. Experimental + ToS. auto-config דורס `.cursor`. `SUBSCRIPTIONS.md` |
| **Blender MCP** (`ahujasid/blender-mcp`) | **local optional** — דורש Blender + addon במק. Cloud Agent sandbox. קונספט/STL מ־HQ = 3DAI. פלייבוק: `vfprod/BLENDER-MCP.md` |
| **VoiceStudio MCP** (`debpalash/VoiceStudio`) | **skip על Cloud** — backend מקומי `:3900`. רילים = גלם רצפה (`vfom`). Desktop VO רק אחרי ראש צוות + `vlicense`. ראו `docs/MCP-FIT.md` · `sources/2026-09-05-voicestudio.md` |
| **CAD family** (Excalidraw / blender-open / blender-ai / blender-vxai / OpenSCAD / FreeCAD / SketchUp / multiCAD / SVGMaker) | רובם **skip על Cloud**. OpenSCAD/FreeCAD/Blender-siblings = Desktop optional אחרי ראש צוות. multiCAD/SketchUp = skip אלא אם האפליקציה במק. SVGMaker = later+API key. Excalidraw remote = later לדיאגרמות פנימיות. קטלוג: `vfprod/CAD-MCP.md` |
| **Archon** (`coleam00/Archon`) | **skip install** — תזמורת/harness שנייה. דפוסים ב־`vfe2b/ORCHESTRATORS.md` בלבד |
| **Fullstack Dev Skills** (`Jeffallan/claude-skills`) | **patterns only** — אין `/plugin install` / `npx skills` על Cloud. Common Ground → `vfmem/MEMORY-UPDATE.md` |
| 3D AI Studio REST / `uvx mcp-server-3daistudio` | מפתח + 2FA על המק בלבד. לא בגיט. המחבר הרשמי הוא HTTP OAuth |
| SharePoint / Outlook / Notion / Slack | לא ערימת שדרות |

## עדיפות Connectors לפי מושב

דפוס מ־[LobeHub ToolsEngine](https://github.com/lobehub/lobehub) (31.8.2026): סוכן רואה רק connectors של המושב שלו; agent-owned > desk > failover. לא marketplace של 10,000 כלים.

| מושב | פקים | namespace ראשי | failover (אותו תור) | אסור |
|---|---|---|---|---|
| ראש צוות | `vfops` | Gmail · Calendar | Drive `create_file` · «חסר לוח» | המצאת ₪ · blast |
| סטודיו | `vfconvert` · `vfsales` | Gmail | Drive · `#נשלח-מ-HQ` · טיוטת וואטסאפ | שליחת וואטסאפ ללקוח · auto-DM |
| צמיחה | `vfgrowth` · `vfigos` · `vfcovers` | Canva | `studio/render.py` → Superdesign → Drive+Gmail | Publish מזויף · boost |
| תפעול | `vfcost` · `vfbooks` | Gmail · Drive | CSV דרך Drive · `mcp-gsheets` אחרי Connect · «X ₪» / «אין ספירה» | Sheets ID מומצא |
| ייצור | `vfprod` · `vfresearch` | Drive · WebSearch · 3DAI | studiomcphub רקע/גודל · STL preflight · Blender MCP רק במק | Treg · גוף חסום · CMYK כצינור VF · Blender על Cloud |

כלים native (כל מושב): `WebSearch` / `WebFetch` · `GenerateImage` — עם שרשרת Canva קודם ל־IG.

דוח: `packages/vfresearch/sources/2026-08-31-lobehub.md`.

## Failover

כלי נפל → גיבוי באותו רגע (`constitution/ORCHESTRA.md`).  
לא ממציאים ₪, Insights, או גוף חסום.
