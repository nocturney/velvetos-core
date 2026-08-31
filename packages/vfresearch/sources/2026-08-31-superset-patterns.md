# מחקר · superset-sh/superset · 2026-08-31

נושא: IDE לסוכני קוד מקביליים (git worktrees) — מה ללמוד במשרד Velvet Factory בלי runtime שני.

מקור: https://github.com/superset-sh/superset  
גוף: README + docs (setup-teardown-scripts, automations). נקרא 31.8.2026.  
רישיון: Elastic License 2.0 — self-host חינם; לא לעטוף ולמכור כשירות.

**לא** Apache Superset לדשבורדים. זה משרד קידוד: Claude Code, Cursor Agent, Codex וכו' — כל משימה ב-worktree נפרד.

## מה Superset מציע

| יכולת | תיאור קצר |
|---|---|
| Parallel workspaces | 100+ agents, worktree + branch לכל workspace |
| Agent monitoring | working indicators, completion chimes, dock badges |
| Lifecycle scripts | `.superset/config.json`: setup / teardown / run |
| Automations | cron (RRule) → workspace חי לבדיקה, לא רק דוח |
| CLI / SDK / MCP | ניהול workspaces מחוץ ל-UI |
| Built-in skills | `superset:*` skills ב-launch |

## שאלות המחקר

1. **פק חדש?** — לא. נופל ל־`vfe2b` + `vfharness` + `vffcc` (offload מקומי). מקור: `AGENTS.md`.
2. **משרד שני?** — לא. Superset = ADE/worktree desktop. מקור: `packages/vfe2b/LOCK.md` + `skipFamilies`.
3. **מה כבר מוטמע?** — בידוד משמרת, דופק, אימות, ארטיפקט, fan-out מוגבל, Cloud Agent על branch. מקור: `crews/run.md`, `ORCHESTRATORS.md`.
4. **מה לקחת כדפוס?** — lifecycle scripts → environment builds; automations-as-workspace → Cloud Agent scheduled; `config.local.json` → override מקומי בלי git.
5. **שולחים מ-HQ?** — לא דרך Superset automations. Gmail/IG נשארים `constitution/SEND.md`.

## מיפוי דפוס → פק קיים

| דפוס Superset | פק / נוהל HQ | verdict |
|---|---|---|
| worktree isolation | `vfe2b/crews/run.md` — תיק עבודה אחד | embed (כבר) |
| working / blocked / idle | כרטיס `דופק` | embed (כבר) |
| verify before done | `אימות` + `vfharness` sensors | embed (כבר) |
| artifact on disk | `ארטיפקט` + `vfharness/state/` | embed (כבר) |
| compare N variants | fan-out עד 3 ב־`vfcopy`/`vfcovers` בלבד | embed (מוגבל) |
| setup / teardown / run | Cloud Agent `environment.json` | embed (להעתיק כשיש dev server) |
| wait for setup before agent | environment build gate | embed (כבר) |
| scheduled automations | `vfops` בריף 07:00 · `vfresearch/WEEKLY.md` | embed (כבר) |
| 100 parallel coding agents | — | skip |
| Superset desktop / CLI / MCP כמשרד | — | skip |
| parallel coding על Mac (ניסוי) | `vffcc/playbooks/local-offload.md` | later · אחרי ראש צוות |

## מה לא מתקינים

- Superset כמשרד HQ או תחליף Cursor
- MCP של Superset לתזמורת Gmail / Canva / IG
- automations ששולחות ללקוח או לפיד בלי כלי HQ
- fan-out של ₪, רישיון, או שליחה

## הטמעה בפועל (31.8.2026)

- רישום ב־`packages/vfresearch/LINKS.json`
- `Superset` ב־`orchestrators.json` → `skipFamilies` (parallel coding desktop ADE)
- שורת lifecycle scripts ב־`packages/vfe2b/ORCHESTRATORS.md`
- הערה אופציונלית ב־`vffcc/playbooks/local-offload.md` — offload מקבילי על Mac בלבד

אין ₪. אין Insights. אין גוף מומצא.
