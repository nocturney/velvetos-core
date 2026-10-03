# vfbiz — offering/business-shape local guide

Scope: offering shape and business-facing commercial structure.

- Canonical offering language is `packages/vfbiz/OFFERING.md` plus the active Instance binding.
- Quantity/customer type are job attributes unless the canonical offering says otherwise.
- Do not invent sale prices, services, shipping promises, customer segments or commercial commitments.
- Public/instance facts stay out of Core root; resolve them from Instance and current authority.
- Price/spend/commitment effects remain protected by their canonical policies.

Verification: `python3 scripts/check-vf-offering.py`.
Policy routing reference: `policy_id: project.request.preflight` is router-only; commercial effects remain with their mapped effect authority.
