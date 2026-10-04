# Expert — Revenue loop (IG → פרנסה)

Module id: `expert-revenue-loop`

## Provides

Closed revenue loop: Instagram content with a monetized offer → inquiry → quote → payment → pickup → retention → measured learning. Every post ties to SKU/offer and pipeline card.

Playbook: `packages/vfgrowth/experts/REVENUE-LOOP.md`. Weekly pulse: `packages/vfops/playbooks/WEEKLY-REVENUE-PULSE.md`. Timeline auto: `packages/vfsales/hq/TIMELINE-AUTO.md`.

## Packs

`vfgrowth`, `vfconvert`, `vfsales`, `vfcopy`, `vfcost`, `vfinsights`, `vfsku`, `vfops`

## Specialists

`@offer-lead-gen-strategist` · `@pipeline-analyst` · `@deal-strategist` · `@customer-success-manager` · `@email-marketing-strategist`

## Laws

- Resolve public CTA, channel and fulfillment wording from the selected instance profile (`cta` + `fulfillment`) and the instance's public-CTA authority; Core carries no business handle, phone or pickup location.
- Price/currency values come only from verified instance/business sources; otherwise use the configured unknown-price placeholder.
- Insights only from verified instance analytics evidence; otherwise report unavailable rather than inventing a count.
- Business-contact send rules come from the selected instance policy/bindings; never promote an internal contact record into public CTA.
- Paid/boost actions follow the selected instance approval policy and external-effect gates.

Always present in core. An instance enables it via `modulesEnabled`.
