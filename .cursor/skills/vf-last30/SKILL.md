---
name: vf-last30
description: Run Velvet Factory last-30-days community research (people-scored, multi-source) for any topic — embed of mvanhorn/last30days-skill patterns on existing vfresearch tools. Use when the user asks for last 30 days, מה אומרים ברשת, מחקר קהילה, discovery טרנדים, A vs B community take, or last30days.
---

# Last 30 days research (VF embed)

Use when the user asks for מחקר 30 יום אחרונים, what people say online, community scored research, topic discovery, tool comparison from recent discussion, or mentions last30days / last 30 days.

## Packs and specialists

- Pack: `vfresearch` (existing — do not open a new pack)
- Playbook: `packages/vfresearch/hq/LAST30.md`
- Mention: `@research-synthesist` (synthesis + citations) and/or `@trend-researcher` (season / discovery / content handoff)
- Related: `expert-trend-explorer` · `WEEKLY.md` · `BEST-SKILLS.md` · `MUSIC.md` (IG sound only)
- Pattern source: [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) — **patterns only**

## Run

1. Read `packages/vfresearch/hq/LAST30.md`.
2. Pick mode: `topic` | `comparison` | `discovery`.
3. Pre-flight: resolve GitHub user/repo and communities when applicable; reframe keyword traps.
4. Fan-out with office tools: `WebSearch` / `WebFetch` / `gh api` / orchestra failover. No X/TikTok keys. No `npx skills` / last30days CLI on Cloud Agent.
5. Apply confidence floor; allow **nothing-solid** (honest empty) — never invent trends, track names, ₪, or Insights.
6. Write `packages/vfresearch/sources/YYYY-MM-DD-<topic>-last30.md`.
7. Hand off embeds to an existing pack, or line for brief block `05` when office-relevant.
8. After catalog/pack edits: `python3 scripts/check-all.py`.

## Forbidden

- Installing last30days plugin / CLI / `npx skills` on Cloud Agent
- Auto-DM, boost without lead seat, Print from HQ
- Invented ₪, Insights, citations, or blocked bodies
- New pack per research idea
- Claiming IG posted without a publish tool
- Presenting a thin Web-only skim as if the full vendor engine ran — label the run as VF embed

## Related

- Weekly inspiration links: `vf-weekly-links`
- Best-skills bi-daily: `vf-best-skills`
- IG music: `vf-ig-music` (HeyOrca — not this skill for track names)
