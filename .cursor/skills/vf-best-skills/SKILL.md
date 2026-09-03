---
name: vf-best-skills
description: Standing forever bi-daily pass over LinklyAI/best-skills rankings until the owner stops it — discover, embed patterns into existing VelvetOS packs, renew the 48h timer every pass. Use when the user asks for best-skills, דירוג סקילים, LinklyAI, skills.sh leaderboard, דופק קבוע, or the every-2-days timer fires.
---

# Best Skills (bi-daily · forever until owner stops)

Use when the user asks for סקירת best-skills, LinklyAI rankings, skills.sh Top 100, דופק קבוע, or the **every-2-days** timer / follow-up fires.

**Standing order:** keep running every ~48h **forever** until the owner explicitly says to stop or change cadence. See `packages/vfresearch/TIMER.md`.

## Packs and specialists

- Pack: `vfresearch` (existing — do not open a new pack)
- Mention: `@research-synthesist` (and `@trend-researcher` if media/trend)
- Lead seat reads the brief line in block `05`
- Playbook: `packages/vfresearch/BEST-SKILLS.md`
- Timer: `packages/vfresearch/TIMER.md`
- State: `packages/vfresearch/BEST-SKILLS.json` (`standingForever: true`)

## Run

1. Read `BEST-SKILLS.md` + `BEST-SKILLS.json` + `TIMER.md`.
2. If `standingForever` is false → do not renew timer; stop after optional one-shot if owner asked.
3. Fetch today's rankings from https://github.com/LinklyAI/best-skills (`data/<date>/rankings/` or README). Prefer `gh api`; failover WebFetch / orchestra — never invent ranks.
4. Diff against `lastPass` / `watchlist` / `embedded`.
5. Embed useful **patterns in place** on existing packs. Open constitution only when a durable office improvement needs it (see playbook «מה מותר לפתוח»).
6. Write `packages/vfresearch/sources/YYYY-MM-DD-best-skills.md`.
7. Update `BEST-SKILLS.json` (`lastPass`, `dataDate`).
8. Set brief `05` line.
9. After catalog/pack/rule edits: `python3 scripts/check-all.py`.
10. **Mandatory:** renew/verify timer `vf-best-skills-bi-daily` per `TIMER.md` (`delaySeconds: 172800`). Note `timer: renewed|ok` in the artifact. Never end a standing pass without this.

## Forbidden

- `npx skills add` / marketplace install on Cloud Agent
- Second orchestrator runtime (OpenClaw, CrewAI, swarms)
- Auto-DM, boost without lead seat, Print from HQ
- Invented ₪, Insights, or ranking rows
- New pack per skill idea
- Claiming IG posted without a publish tool
- Ending a standing pass without renewing the timer

## Related

- Weekly inspiration links (separate): `vf-weekly-links` + `WEEKLY.md`
- Office learning: `vf-daily-learning`
- Harness: `vf-harness`
