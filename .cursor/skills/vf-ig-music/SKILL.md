---
name: vf-ig-music
description: Recommend Instagram-suitable music/sounds for @velvets_cloud from trend and market research. Use when the user asks for מוזיקה לפוסט, סאונד לריל, trending audio, what music to use on Instagram, or מחקר מוזיקה.
---

# Instagram music researcher

Use when the user asks for מוזיקה / סאונד לריל או לפוסט, trending audio, «מה כדאי לשים באינסטגרם», or market/trend research for Reels music.

## Packs and specialists

- Pack: `vfresearch` (existing — **do not** open a new pack)
- Lead mention: `@trend-researcher` (also `@research-synthesist` for sources)
- Handoff: `@visual-storyteller` (`vfom`) → `@instagram-curator` (`vfigos`)
- Playbook: `packages/vfresearch/MUSIC.md`
- Optional frame: `packages/vfmskill/vendor/social/references/short-form-video.md` (Audio Strategy)

## Run

1. `python3 scripts/vfmem.py who "מוזיקה אינסטגרם"` — confirm desk route.
2. Read `packages/vfresearch/MUSIC.md`.
3. Gather **live** sources only:
   - Treg if logged in — search catalog, **say price**, then `call`. Never invent Insights.
   - Owner/Grok list from Instagram music library (named aloud).
   - Written URL with a real body. Blocked page → «אין גוף», do not invent.
4. Match energy to content type (timelapse / hook / BTS / story) per the playbook table.
5. Write `packages/vfresearch/sources/YYYY-MM-DD-ig-music.md`.
6. Hand the brief line to the content crew; `vfigos` reviews only. **HQ does not send.**

## If no live source

Output style-only guidance (tempo, ducking, IG search terms for Grok) and mark every track row **חסר מקור**. Do not invent song titles or “#1 trending this week”.

## Forbidden

Instagram/Gmail/WhatsApp send, boost, auto-DM, new pack per idea, invented ₪ / Insights / blocked bodies, TikTok-first strategy without lead seat, copyrighted tracks outside the platform library without lead approval.
