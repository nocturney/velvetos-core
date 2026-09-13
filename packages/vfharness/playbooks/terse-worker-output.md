# Terse worker protocol — Caveman-pattern embed

Source pattern: `JuliusBrussee/caveman`. Scope is deliberately narrow: internal agent-to-agent / checkpoint payloads only.

Use this to reduce token waste between workers without degrading human-facing briefs, explanations, customer copy, handoffs, or decisions.

## Internal format

Prefer: `state -> evidence -> next_action -> blockers`.

- No greetings, scene-setting, motivational prose, repeated task restatement, or conclusion recap.
- Keep exact IDs, paths, errors, commands, receipts, and hashes intact.
- One fact per line when writing checkpoint/progress payloads.
- Omit reasoning history once a verified checkpoint contains the sufficient state.

## Never apply to

`owner-brief`, `customer-message`, `sales-proposal`, `human-document`, public social copy, UI microcopy, incident explanations to a human, or any artifact governed by `constitution/VISIBLE_TEXT.md`.

This complements `context-thrift.md` and SKILLSTATE; it is not a global response style.
