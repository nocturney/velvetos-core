# vfcost — cost calculation local guide

Scope: deterministic material/internal cost calculation only.

- Use verified grams, material price and explicit cost inputs; refuse missing inputs rather than inventing them.
- Material/internal cost is not a sale price, quote or spend authorization.
- Sale-price/commitment decisions remain with their commercial policy/authority.
- External/paid provider cost follows `constitution/NO_NEW_RECURRING_COST.md` and `policy_id: cost.recurring.new`.
- Keep exact units/currency provenance and do not infer remaining budget from memory.

Verification: `python3 scripts/check-vfcost.py`.
