# פערי כלים · Grok / ChatGPT / Gemini / Perplexity מול HQ

לא פק חדש. הטמעה על `vfmcp` + השולחן הקיים.  
נבדק 31.8.2026 על Cloud Agent `bc-4dd7d6a7` (`nocturney@gmail.com`).  
שליחה חיה נשארת אצל Grok Bot. HQ לא שולח.

## מה יש כאן עכשיו (אומת בריצה)

| כלי | סטטוס | איך אומת |
|---|---|---|
| Gmail | ready · קריאה | namespace `Gmail` |
| Calendar | ready · `Asia/Jerusalem` | namespace `Google-calendar` |
| Drive | ready · חיפוש לפי עבודה | namespace `Google-drive` |
| **Canva** | **ready** | `search-designs` החזיר `DAGoYmCu4c4` («Card - חגיגת האהבה שלכם») |
| WebSearch / WebFetch | ready · מקורי Cursor | כלי native בסוכן |
| GenerateImage | ready · מקורי Cursor | כלי native; אינסטגרם עדיין Canva קודם |
| Superdesign | skill · בלי CLI login | פלאגין על הדיסק |
| Treg | skill · בלי login | אין `treg` ב־PATH; אין namespace |
| Mobbin | plugin · אין MCP כאן | namespace לא על Cloud Agent |
| FCC | לא כאן | נעול ב־`vffcc` |

אין גיליון סטודיו בשם Velvet Factory ב־Drive. גיליונות אישיים דולגו. לא ממציאים workbook ID.

## מה יש אצלם (קטלוג רשמי + מפת HQ)

מקורות: [Grok Connectors](https://x.ai/news/grok-connectors) (מאי 2026) · [ChatGPT Apps](https://help.openai.com/en/articles/11487775-connectors-in-chatgpt) · [Gemini Connected Apps](https://support.google.com/gemini/answer/13695044) · תזמורת `constitution/ORCHESTRA.md` · `docs/BACKUP.md` (Grok Bot: IG / Gmail send / מדפסות).  
סשן חי בחשבון עלול להיות מאחורי חומת הזדהות — לא ממציאים גוף שנחסם.

### Grok / Grok Bot

| כלי שם | כאן | דין |
|---|---|---|
| שליחת אינסטגרם | אין בכוונה | **skip** — Grok / אדם + LIVE-PACKET |
| שליחת Gmail | אין בכוונה | **skip** — Deny קבוע |
| מדפסות | אין בכוונה | **skip** — רצפה לא מ־HQ |
| Google Workspace (Gmail/Drive/Docs/Sheets/Calendar) **כתיבה+שליחה** | Gmail/Drive/Calendar **קריאה**; Docs דרך Drive; Sheets בלי MCP שורות | קריאה כבר כאן. כתיבה/שליחה לא |
| Outlook / OneDrive / SharePoint | אין | **skip** — לא ערימת הסטודיו |
| Notion / Linear / GitHub (Grok) | GitHub דרך `gh` לקריאה | **later** — לא MCP חדש |
| חיפוש רשת / X / DeepSearch | WebSearch + תזמורת | **wired** 31.8 — `tools.web` |
| יצירת תמונה | GenerateImage + Canva | **wired** 31.8 — `tools.image` |
| Bring Your Own MCP | Canva HTTP MCP | לא אגרגטור 400 כלים |

### ChatGPT

| כלי שם | כאן | דין |
|---|---|---|
| Gmail / Drive / Calendar / Canva | אותם ארבעה חיים כאן | כבר מחובר. ChatGPT Gmail **send** — **skip** |
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
| YouTube / Maps / Photos | אין | Treg אחרי login, או **skip** |
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

## מה לא הותקן — ולמה

| פער | למה לא |
|---|---|
| שליחת IG / Gmail / וואטסאפ / מדפסות | חוקת HQ. נשאר Grok / אדם |
| Treg login | דורש דפדפן/קוד לבעלים. אין סרק. failover: WebSearch + «אין ספירה» |
| Mobbin MCP | פלאגין על הדיסק; namespace לא על Cloud Agent. failover: `vfbriefux` |
| Google Sheets MCP | אין גיליון סטודיו שכריסטיאן נקב בשמו. Drive מייצא CSV כשייש נקוב |
| WhatsApp MCP | חיפוש/טיוטה רק אחרי מספר מהבעלים. שליחה אסורה |
| Studio MCP Hub / instapdown | מפה ב־`docs/MCP-FIT.md`. חיבור ב־Cursor Settings, לא סוד בגיט |
| FCC / `fcc-server` | נעול. לא על Cloud Agent |
| SharePoint / Outlook / Notion / Slack | לא ערימת שדרות |

## Failover

כלי נפל → גיבוי באותו רגע (`constitution/ORCHESTRA.md`).  
לא ממציאים ₪, Insights, או גוף חסום.
