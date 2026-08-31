---
name: vf-ig-music
description: Recommend Instagram-suitable music/sounds for @velvets_cloud from public weekly lists and IG-native paste — not Treg. Use when the user asks for מוזיקה לפוסט, סאונד לריל, trending audio, or מחקר מוזיקה.
---

# Instagram music researcher

Use when the user asks for מוזיקה / סאונד לריל או לפוסט, trending audio, «מה כדאי לשים באינסטגרם», or market/trend research for Reels music.

## Packs and specialists

- Pack: `vfresearch` (existing — **do not** open a new pack)
- Lead mention: `@trend-researcher` (also `@research-synthesist` for sources)
- Handoff: `@visual-storyteller` (`vfom`) → `@instagram-curator` (`vfigos`)
- Playbook: `packages/vfresearch/MUSIC.md`
- Source registry: `packages/vfresearch/SOURCES-MUSIC.json`
- Optional frame: `packages/vfmskill/vendor/social/references/short-form-video.md` (Audio Strategy)

## Run

1. `python3 scripts/vfmem.py who "מוזיקה אינסטגרם"` — confirm desk route.
2. Read `packages/vfresearch/MUSIC.md` and `SOURCES-MUSIC.json`.
3. Gather sources (**no Treg**):
   - Open HeyOrca weekly URL; cite the Instagram section with named sounds.
   - If owner/Grok pasted IG Trending / Professional dashboard / `@creators` names — include those.
   - Optional method URL from the registry. Blocked page → «אין גוף».
4. Match energy to content type (timelapse / hook / BTS / story) per the playbook table. Flag Business-library risk.
5. Write `packages/vfresearch/sources/YYYY-MM-DD-ig-music.md`.
6. Hand the brief to the content crew; `vfigos` reviews only. **HQ sends via tools** (`constitution/SEND.md`).

## If no live source

Output style-only guidance (tempo, ducking, IG search terms for Grok) and mark every track row **חסר מקור**. Do not invent song titles or “#1 trending this week”.

## Forbidden

Treg for this job, Instagram/Gmail/WhatsApp send, boost, auto-DM, new pack per idea, invented ₪ / Insights / blocked bodies, TikTok-first strategy without lead seat, copyrighted tracks outside the platform library without lead approval.
