# gcloud operations — diagnose first, mutate through existing authority

Use the installed Google Cloud SDK as a bounded local operations surface. This playbook does not create a second deployment system or authorize cloud spend.

## Default posture

Prefer read-only diagnostics first:
- identify the active account/project/config without printing secrets;
- describe the named resource;
- read recent relevant logs with a narrow time/resource filter;
- compare observed runtime state with the repository deployment contract.

For Cloud Run, common read surfaces include service describe/list and Cloud Logging reads. Use the exact project/region/service from canonical repo or provider state; never guess them from a similar name.

## Mutation gate

A deploy/update/delete/traffic/IAM/billing mutation is allowed only when:
1. the current task explicitly calls for that change;
2. the existing repository deployment authority/playbook identifies the target;
3. cost/security/provider gates are satisfied;
4. the exact change has a rollback or prior revision path when practical.

Do not treat `gcloud run deploy` or another convenient CLI command as authority by itself.

## Diagnostics workflow

1. Resolve the canonical target and current config.
2. Describe current resource state.
3. Read focused logs/events for the failing interval.
4. Correlate with local revision/image/config evidence.
5. Apply the smallest authorized repair.
6. Re-describe and re-read logs.
7. Keep `implemented`, `deployed` and `provider_verified` separate.

## Hard stops

- Never print tokens, service-account private keys or secret values.
- Never switch project/account silently.
- Never broaden IAM to make a test pass.
- Never create paid resources as an automatic fallback.
- Never delete resources as cleanup without explicit authority.
