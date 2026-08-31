# סקירת ריפוז agent repos · 2026-08-31

מושב: ייצור · Asia/Jerusalem  
רישום: `packages/vfresearch/LINKS.json`  
מקור: שיחת בעלים — חמשה קישורי GitHub

## מה נבדק

| id | סטטוס | הערה |
|---|---|---|
| awesome-design-md | הוטמע | `vfbriefux/hq/DESIGN.md` |
| planning-with-files | הוטמע | תבניות + `vfharness/PLANNING-FILES.md` |
| GenAI_Agents | הוטמע חלקי | playbook `reflection-before-send` |
| oh-my-claudecode | דפוס בלבד | כבר ב-`vfe2b/crews/run.md` — לא התקנה |
| ruflo | דולג | `vfe2b/LOCK.md` — unattended swarms |

## מה הוטמע

### awesome-design-md → vfbriefux

- `packages/vfbriefux/hq/DESIGN.md` — טוקנים מ-`MAIL.html` (כהה/זהב/קרם, RTL, 640px)
- `packages/vfbriefux/hq/DESIGN-EMBED.md` — מפת מקור

### planning-with-files → vfharness

- `templates/task_plan.md`, `findings.md`, `progress.md`
- `PLANNING-FILES.md` — `state/<task-id>/` + checkpoint; בלי npm/hooks

### GenAI_Agents → vfagents

- `playbooks/reflection-before-send.md` — ביקורת לפני Gmail/IG send
- רישום ב-`fit.json`

## מה לא הוטמע (מכוון)

| ריפו | סיבה |
|---|---|
| oh-my-claudecode | Cursor = המשרד; pipeline כבר ב-`vfe2b` + orchestrators overlay |
| ruflo | meta-harness / swarms — נעול ב-`orchestrators.json` |
| GenAI — runtime | אין CrewAI/LangGraph/AutoGen חיים |
| planning-with-files — npm | hooks ל-Claude Code; Cloud Agent קורא קבצים ידנית |
| awesome-design-md — קטלוג | לא Stripe/Vercel; זהות VF בלבד |

## מה חדש לחקור

- אם Google `@google/design.md` lint/export נכנס למק הבעלים — `design-md lint` על `DESIGN.md`
- GenAI_Agents: עוד 2–3 playbooks (RAG inquiry, multi-step research) בסקירה שבועית הבאה

## בלוק 05

שבועי קישורים — הוטמע DESIGN.md + planning templates + reflection playbook (`vfbriefux`/`vfharness`/`vfagents`).
