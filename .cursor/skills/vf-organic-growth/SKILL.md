---
name: vf-organic-growth
description: Run the VelvetOS Organic Growth Control Plane — print.done to Reel/Story drafts, 07:00 approval pack, hashtags, community work orders, probabilistic attribution. Never auto-posts Instagram, never auto-DM, never treats WhatsApp as certain conversion. Use for צמיחה אורגנית, Decision Pack, מפעל תוכן, community poll, hashtag set, orders.json attribution, or organic growth overlay.
---

# Organic Growth Control Plane

## VF_PUBLICATION_ROUTE_V1 - current publication scope

For Velvet Factory publication tasks, use `packages/vfom/PUBLICATION-PREP-EXECUTION.md` and the `publicationRoute` in `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json`. Canva/vfcanva are forbidden in this scope; provider notes labelled LEGACY below are not executable routes for VF. Other businesses and non-publication uses are unchanged.
Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

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

## Verification

Before claiming completion, verify the routed target state or run the existing package/route sensor. Configuration, a draft, a command exit, or an agent statement alone is not success. If live/provider evidence is unavailable, report the state as `UNPROVEN`/blocked rather than COMPLETE.

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

> LEGACY / provenance only for VF publication; not a provider route: Before any Velvet Factory concept, image selection/edit, Canva operation, cover, carousel, Story still, Reel cover, feed/grid plan, render or publish handoff, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Verify Canva asset `MAHVL7PKpvE` and artifact SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`. Record a PASS binding in the job/manifest/preflight before creative work continues.

> LEGACY / provenance only for VF publication; not a provider route: This gate is **fail-closed**: if the standard is unavailable, mismatched or unverified, stop the creative branch as `visual_standard_unavailable`; never fall back to a generic 3D-print, stock, template, Canva-default or model-default aesthetic. Real source product media remains Product Truth and outranks style; preserve product identity/geometry/material/color and apply the approved reference to composition, surroundings, light, crop, typography and finish.

## Publication-prep execution gate

For Velvet Factory requests that mean prepare/treat/edit content for a potential publication, `packages/vfom/PUBLICATION-PREP-EXECUTION.md` is mandatory. This is an execution task: when usable images and an editing capability exist, selection/caption/planning alone is incomplete. Produce at least one real edited visual artifact, preserve Product Truth, run exact-final visual QA, and only then package copy for owner review. If visual execution is unavailable, fail closed as `visual_execution_unavailable`; never claim ready from raw photos plus copy. Resolve public CTA from current authority; never hardcode the business WhatsApp number into public content from memory.

