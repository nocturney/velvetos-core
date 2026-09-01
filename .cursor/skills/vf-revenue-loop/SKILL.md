---
name: vf-revenue-loop
description: Run the IG-to-revenue closed loop — offer on every post, pipeline cards, timeline events, verified Insights snapshot, weekly pulse. Use for פרנסה מ-IG, revenue loop, monetize Instagram, or weekly revenue pulse.
---

# vf-revenue-loop

Module: `expert-revenue-loop`. Closes IG → inquiry → quote → pickup → retention → learning.

## When

- Planning IG content that should drive income
- Weekly revenue review
- Linking a post to pipeline / SKU
- After publish — schedule Insights snapshot

## Do this

1. Read `packages/vfgrowth/experts/REVENUE-LOOP.md`.
2. Every schedulable post needs an **Offer card** (SKU, price or `X ₪`, CTA, proof).
3. On inquiry → `TIMELINE-AUTO.md` event + pipeline card with `ig_post_ref`.
4. Insights: `vfinsights/experts/INSIGHTS-SNAPSHOT.md` — owner paste only.
5. Weekly: `vfops/playbooks/WEEKLY-REVENUE-PULSE.md`.

## Specialists

| Job | Slug |
|---|---|
| Offer on post | `@offer-lead-gen-strategist` |
| Pipeline ↔ IG | `@pipeline-analyst` |
| Close quotes | `@deal-strategist` |
| After pickup | `@customer-success-manager` |
| Email nurture | `@email-marketing-strategist` |
| Paid boost | `@paid-social-strategist` (lead gate) |
| Snapshot ingest | `@tracking-measurement-specialist` |

## Route

```bash
python3 scripts/vfmem.py who "revenue loop"
python3 scripts/vfmem.py who "insights snapshot"
```

## Laws

- No auto-DM · no boost without lead · no invented ₪/Insights
- WhatsApp human; Gmail send via tools OK
