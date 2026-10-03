# vfigos — local Instagram action guide

Scope: Instagram transport, queue, schedule and publish/readback execution.

- Canonical external-effect authority is `policy_id: instagram.publish`.
- Read `SEND.md`, `CAPABILITIES.json` and the exact routed publication evidence; do not load the full creative warehouse for a transport-only task.
- Scheduling/queue state is not publication. Claim published only after provider receipt + live readback.
- LOW-risk routine publication may proceed without per-asset owner approval only when the canonical evaluator returns `ALLOW` and required content evidence is exact-bound.
- Boost/ads, auto-DM, rights/privacy ambiguity and other protected effects remain separate policies.
- Transport/runtime readiness is evidence, never authorization.

Verification: Instagram policy/publication sensors and `python3 scripts/check-publication-evidence.py`.
