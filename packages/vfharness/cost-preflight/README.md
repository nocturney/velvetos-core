# Cost Preflight evidence

Canonical law: `constitution/NO_NEW_RECURRING_COST.md`.

Before installing, connecting or first-calling a new external/cloud-connected component, create a JSON preflight from `TEMPLATE.json` and validate it with:

```sh
python3 scripts/vf_cost_preflight.py validate path/to/preflight.json
```

`PAID_REQUIRED` and `COST_UNKNOWN` fail closed without complete explicit owner approval. `EXISTING_PAID_CAPABILITY` must prove the proposed workload cannot increase the bill. `FREE_TIER_LIMITED` must document quota controls and overage behavior. `PAID_OPTIONAL` must be locked to the free path.

A general instruction such as "install what is needed" is not approval to spend.

Compatibility: the validator also accepts the compact action-oriented preflight used by Fabrication Router (`component`, `action`, `classification`, current evidence/date, incremental/overage/cap/paid-feature booleans). Invoke compact evidence as `python3 scripts/vf_cost_preflight.py path/to/preflight.json`; the detailed schema remains `python3 scripts/vf_cost_preflight.py validate path/to/preflight.json`. Both formats enforce the same fail-closed classifications and explicit-approval boundary.
