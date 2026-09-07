---
name: vf-organic-growth
description: Run the VelvetOS Organic Growth Control Plane — print.done to Reel/Story drafts, 07:00 approval pack, hashtags, community work orders, probabilistic attribution. Never auto-posts Instagram, never auto-DM, never treats WhatsApp as certain conversion. Use for צמיחה אורגנית, Decision Pack, מפעל תוכן, community poll, hashtag set, orders.json attribution, or organic growth overlay.
---

# Organic Growth Control Plane

## Packs

- Policy: `constitution/ORGANIC_GROWTH.md`
- Factory: `packages/vfgrowth/ORGANIC-GROWTH.md`
- Floor: `packages/vfprod/PRINT-DONE.md`
- Brief: `packages/vfbriefux/hq/GROWTH-BRIEF.md`
- CLI: `python3 scripts/vf_organic_growth.py brief --write`

## Do this

1. Read the constitution file. Control plane **does not publish**.
2. Require a real `print.done` (status/operator). Do not infer from G-code.
3. If media quality fails: write the 15-second handheld ask. Do not invent a Reel.
4. Draft Reel for the **next CALENDAR.md 16:00 slot** (Sun/Tue only — no weekday-every-day reel).
5. Draft Story poll for 20:30 Sun–Thu from `poll-library.json` (floor can actually run it).
6. Put assets in `approval-queue.json` at `pending_human_approval`.
7. 07:00 Decision Pack: [אישור] [עריכה] [דחייה]. Approve → `approved_for_manual_posting` only.
8. Attribution via `vfsales/data/orders.json` + `vfinsights/ATTRIBUTION.md`. Missing = «אין ספירה».

## Do not

- Auto-post, auto-DM, boost, follow, tag users without opt-in
- Poll → Print from HQ (`pending_ops` only)
- Invent ₪ / Insights / heat/strength claims
- Mark `posted_manually` from Core
- Promise certain conversion from a WhatsApp ping
