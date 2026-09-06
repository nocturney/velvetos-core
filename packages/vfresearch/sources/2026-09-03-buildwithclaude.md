# תחקור buildwithclaude · 2026-09-03

מושב: ייצור · `@research-synthesist`  
מקור: [buildwithclaude.com](https://buildwithclaude.com/) · [davepoon/buildwithclaude](https://github.com/davepoon/buildwithclaude) (MIT)  
סטודיו: Velvet Factory · שדרות · איסוף · וואטסאפ `050-2517000` · IG `@velvets_cloud`  
לא פק חדש. לא `npx skills add`. לא marketplace של Claude Code על Cloud Agent.

## מה זה

אינדקס/מרקטפלייס לקהילת Claude Code: plugins, skills, agents, commands, hooks, ו־MCP.  
האתר מציג גם אינדקס קהילתי רחב (~27k plugins / ~4.4k skills / ~6k MCP — מספרי שיווק של האתר; לא ספירה שלנו).  
הריפו עצמו מחזיק אוסף מקוצר (agents / commands / hooks / skills / plugins) + `mcp-servers.json` (~199 ערכים Docker).

התקנה שלהם מיועדת ל־Claude Code (`/plugin marketplace add davepoon/buildwithclaude`).  
אצלנו **Cursor הוא המשרד** — מטמיעים דפוסים על פקים קיימים, לא מתקינים מרקטפלייס שני.

## מה כבר יש אצלנו (לא לשכפל)

| אצלם | אצלנו | דין |
|---|---|---|
| 117 agents בקטגוריות | Agency warehouse + שולחן 5 מושבים | warehouse נשאר off-desk |
| sales-marketing agents | `vfcopy` `vfgrowth` `vfsales` `vfigos` | כבר מכוסים |
| research agents | `vfresearch` + תזמורת | כבר מכוסים |
| MCP discovery | `docs/MCP-FIT.md` + `vfmcp` | אינדקס נוסף, לא החלפה |
| memory plugins (context-memory, memstack, basic-memory) | `vfmem` + `owner-memory.md` + checkpoints | דפוס משמעת — לא binary/hosted |
| anti-ui-slop / frontend-design-pro | `ui-finish-gate-reviewer` + taste-skill embed + Mobbin | חיזוק finish gate |
| webapp-testing (Playwright) | Cloud Agent computerUse + walkthrough | דפוס verify-in-browser |
| AEO / ai-search-visibility-audit | `@aeo-foundations-architect` (warehouse) | **watch** — אתר שיווקי ציבורי נעול |
| 3d-printer MCP (Orca/Bambu/OctoPrint…) | מדפסות על הרצפה | **skip** — אין Print מ־HQ |
| msapps-whatsapp / WhatsApp Business MCP | אדם ב־`050-2517000` | **skip send** — חוק AGENTS |
| OpenClaw / second runtime hooks | `vfe2b` LOCK | **skip** |

## מה הוטמע היום (דפוסים)

| מקור | לאן | למה |
|---|---|---|
| `agent-memory-discipline` | `packages/vfmem/MEMORY-UPDATE.md` | recall לפני פעולה; save אחרי החלטה/תיקון/כישלון; close במקום delete |
| `agent-architecture-audit` (12 שכבות) | `packages/vfharness/playbooks/agent-architecture-audit.md` | אבחון כשסוכן «נהיה גרוע» — code-first, לא prompt-first |
| `anti-ui-slop` finish gate | הערת חיזוק ב־`ui-finish-gate-reviewer` כבר קיימת (UIZZE) | אין שינוי חוק — כבר מיושר |
| אינדקס buildwithclaude | `docs/MCP-FIT.md` + `LINKS.json` | מקור גילוי שבועי ליד awesome-mcp-servers |

## מה לדחות / watch

| פריט | למה |
|---|---|
| `/plugin marketplace add` / `npx skills add` | Claude Code vendor; Cursor = office |
| `context-memory` hosted (Slova) | שולח prompt ל־API חיצוני; יש לנו קבצי markdown בגיט |
| `give-claude-eyes` (Qwen Omni) | מפתח DashScope; רילים → Canva/`vfom` + computerUse |
| `cashflow` plugin | ממציא/מודל כספי — אצלנו `vfcost`/`vfbooks` בלי ₪ מומצא |
| `ai-search-visibility-audit` על דומיין סטודיו | אתר שיווקי מ־HQ **נעול**; רלוונטי רק אם נפתח אתר תחת `vfbiz` |
| `sales-automator` cold email | VF = פניות נכנסות; cold-email אסור ב־MCP-FIT |
| `social-media-copywriter` (podcast-specific) | ספציפי ל־The Build Podcast — לא `@velvets_cloud` |
| Discord/Telegram notification hooks | אין ערוץ סטודיו כזה מ־HQ |
| Ralph / swarm / unattended orchestrators | נעול ב־`vfe2b` |

## סדר עדיפות ליישום (בלי התקנה עיוורת)

1. **משמעת זיכרון** — כבר הוטמע ב־`MEMORY-UPDATE.md` (היום).
2. **אבחון רתמה** — playbook 12-שכבות ב־`vfharness` (היום).
3. **Sheets MCP** — עדיין הפער #1 מ־`MCP-FIT` (לא מ־buildwithclaude).
4. **WhatsApp** — חיפוש/טיוטות בלבד אחרי אישור ראש צוות; שליחה אנושית.
5. **AEO audit** — רק אם/כשנפתח אתר ציבורי; עד אז warehouse `@aeo-foundations-architect` off-desk.
6. **UI finish + UIZZE/Mobbin** — כשעובדים על קונסולה פנימית (`COMMAND-SURFACE`), לא על אתר שיווקי.

## מקורות שנפתחו

- https://buildwithclaude.com/ (homepage, plugins, skills)
- https://buildwithclaude.com/skill/anti-ui-slop
- https://buildwithclaude.com/skill/agent-memory-discipline
- https://buildwithclaude.com/skill/ai-search-visibility-audit
- https://buildwithclaude.com/skill/agent-architecture-audit
- https://buildwithclaude.com/skill/webapp-testing
- https://github.com/davepoon/buildwithclaude (README, plugins/*, mcp-servers.json)
- Stories: frontend-design-pro · webapp-testing

## אסור שנשמר

אין ₪ · אין Insights · אין טענה ש־IG פורסם · אין התקנת FCC/Claude marketplace על Cloud · אין Print מ־HQ · אין אוטו־DM.
