# Best Skills · 2026-09-14

מקור: [LinklyAI/best-skills](https://github.com/LinklyAI/best-skills) · dataDate: **2026-09-13** (`data/2026-09-13/rankings`)  
מושב: מחקר/אורקסטרציה · Asia/Jerusalem  
טריגר: טיימר `vf-best-skills-bi-daily` · standingForever

הערה: אין תיקיית `data/2026-09-14/` במקור בזמן המעבר — דירוג אחרון זמין = 2026-09-13.

מעבר קודם באותו יום (Windows fallback) רשם `no-embed` + `timer: UNPROVEN`. מעבר Cloud זה **סוגר את הפער**: מטמיע `sensor-first-tdd` (PR #178 לא מוזג) ומחדש טיימר.

## Movers (VF-relevant)

| # | skill/repo | list | פעולה |
|---|---|---|---|
| 1 | find-skills | best-100 | כבר — `BEST-SKILLS.md` |
| 4 | grill-me | best-100 / buzz #2 | כבר — `vfconvert/hq/GRILL.md` |
| 33 / 40 | tdd (mattpocock) | best-100 / trending-7d | **הוטמע** → `sensor-first-tdd.md` |
| 36 | improve-codebase-architecture | best-100 / buzz | כבר — `agent-architecture-audit.md` (אין כפילות) |
| 1 | obra/superpowers | top-repos | חלקי+; TDD נסגר היום |
| 2 | mattpocock/skills | top-repos | כבר; TDD דרך sensor-first-tdd |
| — | requesting-code-review (obra) | superpowers | watch |
| — | Agent-Reach / chrome-devtools-mcp | top-repos | watch — בלי install |
| — | google-agents-cli / genmedia / reddit-automation / desktop-control | trending/buzz | דולג — מנדט |

## מה הוטמע

- `packages/vfharness/playbooks/sensor-first-tdd.md` — RED→GREEN→REFACTOR על `check-*.py` / CLI לפני תיקון פק
- מצביעים מ־`systematic-debugging.md` + `verification-before-claim.md` + `SKILL.md` (12b)
- רישום ב־`BEST-SKILLS.json` (`sensor-first-tdd`, lastPass 2026-09-14, dataDate 2026-09-13)

## Watchlist (עודכן)

- agent-reach · chrome-devtools-mcp · requesting-code-review
- obra finishing-branch / git-worktrees
- mattpocock codebase-design / domain-modeling (רק אם יימדד פער מול agent-architecture-audit)
- earthtojake-text-to-cad (CAD — בלי runtime שני)

## מה דולג

| מה | למה |
|---|---|
| npx skills / OpenClaw | מנדט Cloud |
| desktop-control / RPA | מחוץ ל־HQ Cloud |
| genmedia / Veo / Kling / avatar | נעול; Canva-first |
| Agent-Reach install | runtime שני |
| chrome-devtools-mcp blind install | GAP ב־vfmcp |
| google-agents-cli / azure / auto-DM | מנדט |
| improve-codebase-architecture embed כפול | כבר ב־agent-architecture-audit |

## טיימר

standingForever=true · `TIMER.md` · `timer: renewed` (`vf-best-skills-bi-daily` · delaySeconds 172800)

## בלוק 05

best-skills — הוטמע sensor-first-tdd (mattpocock tdd #33 + obra TDD → check-*.py); dataDate 2026-09-13; timer renewed; סוגר פער #178
