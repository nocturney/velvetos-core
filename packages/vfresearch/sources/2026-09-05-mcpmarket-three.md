# תחקור MCP Market · שלושה קישורים · 2026-09-05

מושב: ייצור · `@research-synthesist`  
סטודיו: Velvet Factory · שדרות · איסוף · וואטסאפ `050-2517000` · IG `@velvets_cloud`  
לא פק חדש. לא התקנת MCP על Cloud Agent. לא תזמורת שנייה.

## מקורות שנשלחו

| id | mcpmarket (חסום Cloudflare) | גוף פתוח שנפתח |
|---|---|---|
| mcpmarket-blender-mcp | https://mcpmarket.com/server/blender-model-context-protocol | [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) README |
| mcpmarket-archon | https://mcpmarket.com/server/archon | [coleam00/Archon](https://github.com/coleam00/Archon) README + archon.diy |
| mcpmarket-fullstack-skills | https://mcpmarket.com/server/fullstack-dev-skills-plugin | [Jeffallan/claude-skills](https://github.com/Jeffallan/claude-skills) README + SKILLS_GUIDE + COMMON_GROUND |

`WebFetch` על דפי mcpmarket → «We're verifying your browser» → **אין גוף**. failover מיד ל־GitHub / docs פתוחים (לא ממציאים את דף השוק).

## 1) Blender Model Context Protocol

**מה זה:** addon בתוך Blender + שרת MCP (`uvx blender-mcp`) — סוכן שולט בסצנה (אובייקטים, חומרים, קוד Python, Poly Haven / Hyper3D).  
**דין HQ:** **local optional** אחרי ראש צוות. Cloud Agent **לא** מריץ Blender. קונספט/STL מ־HQ נשאר **3D AI Studio** (`vfprod/3DAISTUDIO.md`).  
**הוטמע:** `packages/vfprod/BLENDER-MCP.md` + שורות ב־`GAP.md` / `MCP-FIT.md` / `3DAISTUDIO.md`.

## 2) Archon

**mcpmarket (סיכום מחיפוש, לא גוף מלא):** «Agenteer» ישן — בונה סוכנים עם Pydantic/LangGraph.  
**GitHub חי (2026-09):** harness builder — YAML workflows, worktrees, שערי אימות/אישור אדם, CLI/Web.  
**דין HQ:** **skip install** (תזמורת שנייה / ADE). דפוסים בלבד על `vfe2b` + `vfharness`.  
**הוטמע:** שורת דפוס ב־`ORCHESTRATORS.md` + pick ב־`orchestrators.json` + `docs/ORCHESTRATORS.md`.

דפוסים שנלקחו (בלי runtime):

| דפוס Archon | אצלנו |
|---|---|
| YAML phases + validation gates | לולאת `vfharness` + `אימות` |
| human approval loop | `decision_gate` · ₪ לראש צוות · וואטסאפ אדם |
| isolated worktree per run | תיק משמרת אחד ב־`vfe2b/crews/run.md` (לא worktree multiplexer) |
| deterministic bash nodes + AI nodes | סנסורים (`check-*.py`) מול כתיבת סוכן |
| `archon-ralph-dag` / unattended | **skip** — נעול ב־`LOCK.md` |

## 3) Fullstack Dev Skills Plugin (Jeffallan)

**מה זה:** ~67 skills ל־Claude Code (שפות/פריימוורקים/DevOps) + `/common-ground` + workflow commands (Jira).  
mcpmarket מציג «19 skills» — מספר ישן; הריפו הפתוח גדול יותר.  
**דין HQ:** **patterns only**. אין `npx skills` / `/plugin install` על Cloud Agent. Warehouse של 273 כבר off-desk; לא משכפלים 67 מומחי fullstack לתוך הליבה.  
**הוטמע:** דפוס Common Ground (ESTABLISHED / WORKING / OPEN) ב־`vfmem/MEMORY-UPDATE.md`; הערת discovery ב־`MCP-FIT.md` + `BEST-SKILLS` watch.

| דפוס Jeffallan | אצלנו | דין |
|---|---|---|
| Common Ground tiers | `MEMORY-UPDATE.md` + `owner-memory.md` | **embed** |
| Feature Forge → implement → test | פנייה → grill → packs | כבר יש (`vfconvert`) |
| decision trees / multi-skill | `vfmem who` + desk route | כבר יש |
| Atlassian MCP / Jira epics | — | **skip** — לא ערימת שדרות |
| Language specialists (Nest/Django/…) | Agency warehouse | **off-desk** עד `@slug` מפורש |
| RAG Architect / Fine-Tuning | — | **skip** — לא פרנסת הסטודיו היום |

## מה הוטמע (קבצים)

- `packages/vfprod/BLENDER-MCP.md`
- `packages/vfprod/3DAISTUDIO.md` (קישור צולב)
- `packages/vfmcp/GAP.md`
- `docs/MCP-FIT.md`
- `packages/vfe2b/ORCHESTRATORS.md` + `orchestrators.json`
- `docs/ORCHESTRATORS.md`
- `packages/vfmem/MEMORY-UPDATE.md`
- `packages/vfresearch/LINKS.json` + בריף 05

## אסור שנשמר

אין ₪ · אין Insights · אין התקנת Blender/Archon/claude-skills על Cloud · אין Print מ־HQ · אין אוטו־DM · אין גוף Cloudflare מומצא · אין תזמורת שנייה.
