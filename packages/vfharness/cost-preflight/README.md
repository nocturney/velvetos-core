# Cost preflight

Use this gate before installing, connecting, provisioning, authenticating to a billing-capable service, making a first paid-capable API call, scheduling a metered workload, or changing a billing-relevant setting.

1. Copy TEMPLATE.json to a task-specific evidence file.
2. Fill every required field from current provider/account evidence.
3. Run: python3 scripts/vf_cost_preflight.py path/to/preflight.json
4. Continue only when the command returns PASS.

The canonical law is constitution/NO_NEW_RECURRING_COST.md. Unknown cost fails closed. A successful login, existing account, trial, free-tier label, or available credit is not proof of zero incremental cost.
