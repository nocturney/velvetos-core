# Bounded Cost Envelopes

Stage 4G adds a bounded authorization primitive under **policy_id: cost.recurring.new**.

This directory does **not** contain any active spend authorization. `TEMPLATE.json`
is inert and `fixtures/` is test-only. A real envelope is valid only after an
explicit owner approval and a full cost preflight have been captured and bound.

## Lifecycle

1. Run the normal full cost preflight and verify pricing/billing facts.
2. The owner explicitly approves one bounded envelope containing provider, exact product/plan, billing model, usage model, scope, aggregate ILS cap, overage behavior, expiry, and approval reference.
3. Bind the envelope to the exact preflight artifact SHA-256.
4. For matching calls, use `python scripts/vf_cost_preflight.py envelope-use ENVELOPE.json USE.json`.
5. Matching calls do **not** repeat full preflight or owner approval. They still require a fresh usage meter, aggregate cap headroom, and an exact-action receipt before the external paid effect.
6. Provider/plan/billing/usage/scope/cap/overage drift or expiry invalidates the envelope and returns `REQUIRE_OWNER_APPROVAL`.
7. Missing/stale meter evidence, a broken hard cap, unknown cost, or a cap breach fails closed.

## Non-goals

- No open-ended spend authorization.
- No emergency billing.
- No silent cap increase.
- No auto-renew assumption.
- No envelope for `COST_UNKNOWN`.
- No second policy engine: `scripts/vf_cost_preflight.py` remains the sole runtime decision boundary; `scripts/vf_cost_envelope.py` is a helper.
