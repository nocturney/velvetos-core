# תזמורת · 2026-08-31 (Asia/Jerusalem)

שני מעברים באותו יום: 06:15 (פיילאובר Grok, אין MCP לשולחנות) ואחר כך פערי כלים (`bc-4dd7d6a7`).

## 06:15 · שולחנות בלי MCP

אותה שאלת `vfresearch/DAILY.md`.  
שולחנות ChatGPT / Gemini / Perplexity **אין להם MCP** על Cloud Agent הזה.

| נפל | למה | עבר ל־ | גוף |
|---|---|---|---|
| ChatGPT | אין כלי MCP בסשן | פקים שכבר על הדיסק | אין גוף חדש · לא הומצא |
| Gemini | אין כלי MCP בסשן | פקים שכבר על הדיסק | אין גוף חדש · לא הומצא |
| Perplexity | אין כלי MCP בסשן | פקים שכבר על הדיסק | אין גוף חדש · לא הומצא |

שלושתם לא נפתחו. אין «מחכים לבעלים» בלי תוצאה: התוצר הוא **פיילאובר Grok החי** על פקים קיימים (`2026-08-31-grok-failover.md`).

## מעבר פערי כלים · `bc-4dd7d6a7`

מיועד לבריף **1.9.2026 07:00** בלוק `05`.

### מה נשאל

איזה כלים מותקנים/מופעלים אצל Grok / ChatGPT / Gemini / Perplexity שלא קיימים או לא מופעלים כאן — למצוא פערים ולהתקין מה שחסר/נדרש.

### מה נבדק כאן (גוף אמיתי)

| כלי | גוף |
|---|---|
| Gmail / Calendar / Drive MCP | ready |
| Canva MCP | ready. `search-designs` → `DAGoYmCu4c4` |
| WebSearch / WebFetch / GenerateImage | native Cursor, לא היו על השולחן |
| Treg CLI | אין ב־PATH |
| Mobbin | פלאגין; אין namespace |
| Drive Sheets בשם VF | אין. גיליונות אישיים דולגו |
| Gmail אחרון על כלים | Canva Sign-in with Google 30.8 |

### מה נבדק אצלם

| שולחן | גוף |
|---|---|
| Grok Connectors (רשמי, מאי 2026) | Workspace (כולל Sheets + **שליחת** מייל), Outlook, SharePoint, Notion, Linear, GitHub, BYO-MCP. Grok Bot HQ: IG send / Gmail send / מדפסות |
| ChatGPT Apps (עזרה רשמית) | Gmail/Drive/Calendar/Canva + חיפוש + תמונה. Gmail send אחרי אישור — **דולג** |
| Gemini Connected Apps (עזרה רשמית) | Workspace + WhatsApp/Phone **שליחה** — **דולג** |
| Perplexity | חיפוש+ציטוטים. חומת מנוי/Cloudflare ב־30.8. אין גוף שני |

דפדפן חי 31.8 (`bc-0d7c7cd6`): ChatGPT = Gmail קריאה בלבד; Gemini = Workspace+Search+YouTube ON, Canva OFF; Perplexity = Connectors ריק; Grok = חומת X — **אין גוף**. לא ממציאים מחברי Grok.

### מה הוטמע

| ממצא | פק | לא |
|---|---|---|
| Canva ready על Cloud Agent | `vf-desk.json` `canva.status=ready` | שליחת IG |
| WebSearch/WebFetch על השולחן | `tools.web` · `vfresearch` | גוף חסום מומצא |
| GenerateImage + Canva generate | `tools.image` | כריכת IG בלי Canva-first |
| גיליון דרך Drive כשייש שם | `vfbooks/SHEETS.md` | Sheets MCP בלי ID |
| מפת פער | `vfmcp/GAP.md` | פק כלים חדש |

### Failover שבוצע

Treg בלי login → WebSearch + «אין ספירה».  
Mobbin בלי namespace → `vfbriefux`.  
אין גיליון VF → «חסר גיליון», בלי שורות מומצאות.  
שליחת IG אצלם לא נראתה במסך. Gmail send — HQ שולח כאן (`SEND.md`). Treg לא רלוונטי.

## בלוק 05

```
05 · משרד
מה נבנה / יועל: פיילאובר Grok + פערי כלים — Canva ready + web/image; HQ שולח דרך כלים (`SEND.md`); בריף HTML תצוגה 3; סשן חי: GPT Gmail / Gemini Workspace / Perplexity ריק / Grok חומה (`vfmcp/GAP.md`)
```
