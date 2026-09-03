# סקירת קישורים שבועית · 2026-09-03

מושב: ייצור · Asia/Jerusalem  
רישום: packages/vfresearch/LINKS.json  
טריגר: קישור חדש מהבעלים (buildwithclaude) — אותו יום, לא מחכים לראשון.

## מה נבדק

| id | סטטוס | הערה |
|---|---|---|
| buildwithclaude-marketplace | הוטמע | דפוסי memory + architecture-audit + רישום MCP discovery |
| (שאר LINKS.json) | לא בסבב זה | רק הקישור החדש שנשלח |

## מה הוטמע

- `packages/vfmem/MEMORY-UPDATE.md` — משמעת recall/save/close מ־`agent-memory-discipline`
- `packages/vfharness/playbooks/agent-architecture-audit.md` — 12 שכבות ממופות ל־HQ
- `docs/MCP-FIT.md` — buildwithclaude כאינדקס גילוי (ליד awesome-mcp-servers)
- דוח מלא: `packages/vfresearch/sources/2026-09-03-buildwithclaude.md`

## מה חדש לחקור

- Sheets MCP עדיין הפער החי #1 (`MCP-FIT`) — לא מ־buildwithclaude
- AEO audit skill — watch עד פתיחת אתר ציבורי (`vfbiz`)
- UIZZE catalogue כמקור רפרנס לקונסולה פנימית (ליד Mobbin) — בלי MCP חובה

## מה דולג

| מה | למה |
|---|---|
| `/plugin marketplace add davepoon/buildwithclaude` | Claude Code vendor; Cursor = office |
| `npx skills add` | לא מותקן על Cloud Agent |
| context-memory hosted / memstack binary | יש `vfmem` + owner-memory בגיט |
| 3d-printer MCP | מדפסות על הרצפה — אין Print מ־HQ |
| WhatsApp send plugin | שליחת לקוח נשארת אנושית |
| OpenClaw / swarm hooks | נעול ב־`vfe2b` |
| cold-email / podcast copy agents | לא צינור VF |

## שורת בריף 05

שבועי קישורים — הוטמע buildwithclaude (memory + harness audit) ב־`vfmem`/`vfharness`
