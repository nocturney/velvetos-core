---
name: vf-best-skills
description: Standing forever ~48h pass over LinklyAI/best-skills rankings until the owner stops it — discover and embed useful patterns into existing VelvetOS packs. The canonical scheduler authority is Velvet Research Seat; use when best-skills is due, the user asks for rankings, or Research Seat detects stale lastPass.
---

# Best Skills (~48h · forever until owner stops)

Use when the user asks for סקירת best-skills, LinklyAI rankings, skills.sh Top 100, דופק קבוע, or when **Velvet Research Seat** detects that `lastPass` is due.

**Standing order:** keep running about every 48h forever until the owner explicitly says to stop or change cadence. See `packages/vfresearch/TIMER.md`.

## Packs and specialists

- Pack: `vfresearch` — existing only; do not open a new pack.
- Mention: `@research-synthesist` and `@trend-researcher` when relevant.
- Lead seat reads the brief line in block `05`.
- Playbook: `packages/vfresearch/BEST-SKILLS.md`.
- Cadence authority: `packages/vfresearch/TIMER.md` + Velvet Research Seat.
- State: `packages/vfresearch/BEST-SKILLS.json` (`standingForever`, `lastPass`, `lastArtifact`, `lastResult`).

## Run

1. Read `BEST-SKILLS.md` + `BEST-SKILLS.json` + `TIMER.md`.
2. If `standingForever` is false, do not schedule another pass; perform only an explicit one-shot request.
3. Fetch current rankings from https://github.com/LinklyAI/best-skills. Prefer `gh api`; fail over to WebFetch/orchestra. Never invent ranks.
4. Diff against `lastPass`, `watchlist`, and `embedded`.
5. Embed useful **patterns in place** on existing packs. Change constitution only for a durable office improvement and preserve core locks.
6. Write `packages/vfresearch/sources/YYYY-MM-DD-best-skills.md`.
7. Update `BEST-SKILLS.json`: `lastPass`, `dataDate`, `lastArtifact`, `lastResult`.
8. Update brief block `05` when there is brief-worthy output.
9. After catalog/pack/rule edits run `python3 scripts/check-all.py`.
10. Verify the state/artifact pair. A `lastPass` older than 52h is stale and must be handled by Research Seat; never claim fresh without a matching artifact.

## Forbidden

- `npx skills add` / marketplace install on Cloud Agent.
- Second orchestrator runtime such as OpenClaw/CrewAI/swarms.
- Separate recurring automation just for Best Skills while Research Seat is active.
- Auto-DM, unapproved Boost/Ads, Print from HQ.
- Invented ₪, Insights, ranking rows, or timer receipts.
- New pack per skill idea.
- Claiming IG posted without a publish tool.

## Verification

A pass is complete only when the source was actually read, the dated artifact exists, `BEST-SKILLS.json` points to that artifact/date/result, and any edits pass their existing sensors. Research Seat freshness is the cadence proof; an unavailable external subscription namespace is not a blocker by itself.

## Related

- Weekly inspiration links: `vf-weekly-links` + `WEEKLY.md`.
- Office learning: `vf-daily-learning`.
- Harness: `vf-harness`.
