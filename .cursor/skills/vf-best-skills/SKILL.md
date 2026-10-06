---
name: vf-best-skills
description: On-demand review of LinklyAI/best-skills rankings for a concrete adoption, content, or Office v2 decision. No standing timer; use when the user asks or current work needs fresh evidence.
---

# Best Skills — on demand

Use when the user asks for סקירת best-skills, LinklyAI rankings, skills.sh Top 100, or when a concrete tool/skill/content/Office v2 decision needs fresh ecosystem evidence.

**Current override (2026-10-06): No standing cadence.** The former ~48h standing cadence is retired. Age of `lastPass` is provenance only and never schedules work by itself. See `packages/vfresearch/TIMER.md`.

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
3. Fetch current rankings from https://github.com/LinklyAI/best-skills. Prefer `gh api`; fail over to WebFetch/orchestra. Never invent ranks. When the installed GitHub CLI exposes the current `gh skill` preview namespace, use `gh skill search` and `gh skill preview` as an additional discovery/inspection surface only. Preview before any sandbox install; record source/version/commit when pinning. `gh skill` is not a new authority and its preview status means behavior may change.
4. Diff against `lastPass`, `watchlist`, and `embedded`.
5. Embed useful **patterns in place** on existing packs. Change constitution only for a durable office improvement and preserve core locks.
6. Write `packages/vfresearch/sources/YYYY-MM-DD-best-skills.md`.
7. Update `BEST-SKILLS.json`: `lastPass`, `dataDate`, `lastArtifact`, `lastResult`.
8. Update brief block `05` when there is brief-worthy output.
9. After scoped catalog/pack/rule edits run the affected/domain sensors; reserve `python3 scripts/check-all.py` for repository-wide contract/authority changes or explicit acceptance/regression.
10. Verify the state/artifact pair. `lastPass` age is provenance only; never schedule work from age alone and never claim a fresh review without a matching artifact.

## Forbidden

- `npx skills add` / marketplace install on Cloud Agent.
- `gh skill install` directly into production merely because discovery found a candidate. Research/preview first; adoption still follows provenance, duplicate/conflict review, wrapper/merge classification and the existing skill-authoring checks.
- Second orchestrator runtime such as OpenClaw/CrewAI/swarms.
- Separate recurring automation just for Best Skills while Research Seat is active.
- Auto-DM, unapproved Boost/Ads, Print from HQ.
- Invented ₪, Insights, ranking rows, or timer receipts.
- New pack per skill idea.
- Claiming IG posted without a publish tool.

## Verification

A pass is complete only when the source was actually read, the dated artifact exists, `BEST-SKILLS.json` points to that artifact/date/result, and any edits pass their existing sensors. There is no cadence/freshness obligation when no concrete research need exists.

## Related

- Weekly inspiration links: `vf-weekly-links` + `WEEKLY.md`.
- Office learning: `vf-daily-learning`.
- Harness: `vf-harness`.
