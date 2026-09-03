---
name: vf-best-skills
description: Bi-daily pass over LinklyAI/best-skills rankings — discover, embed patterns into existing VelvetOS packs, update constitution when durable. Use when the user asks for best-skills, דירוג סקילים, LinklyAI, skills.sh leaderboard, or the every-2-days timer fires.
---

# Best Skills (bi-daily)

Use when the user asks for סקירת best-skills, LinklyAI rankings, skills.sh Top 100, or the **every-2-days** timer / follow-up fires for this link.

## Packs and specialists

- Pack: `vfresearch` (existing — do not open a new pack)
- Mention: `@research-synthesist` (and `@trend-researcher` if media/trend)
- Lead seat reads the brief line in block `05`
- Playbook: `packages/vfresearch/BEST-SKILLS.md`
- State: `packages/vfresearch/BEST-SKILLS.json`

## Run

1. Read `BEST-SKILLS.md` + `BEST-SKILLS.json`.
2. Fetch today's rankings from https://github.com/LinklyAI/best-skills (`data/<date>/rankings/` or README). Prefer `gh api`; failover WebFetch / orchestra — never invent ranks.
3. Diff against `lastPass` / `watchlist` / `embedded`.
4. Embed useful **patterns in place** on existing packs. Open constitution only when a durable office improvement needs it (see playbook «מה מותר לפתוח»).
5. Write `packages/vfresearch/sources/YYYY-MM-DD-best-skills.md`.
6. Update `BEST-SKILLS.json` (`lastPass`, `dataDate`).
7. Set brief `05` line.
8. After catalog/pack/rule edits: `python3 scripts/check-all.py`.

## Forbidden

- `npx skills add` / marketplace install on Cloud Agent
- Second orchestrator runtime (OpenClaw, CrewAI, swarms)
- Auto-DM, boost without lead seat, Print from HQ
- Invented ₪, Insights, or ranking rows
- New pack per skill idea
- Claiming IG posted without a publish tool

## Related

- Weekly inspiration links (separate): `vf-weekly-links` + `WEEKLY.md`
- Office learning: `vf-daily-learning`
- Harness: `vf-harness`
