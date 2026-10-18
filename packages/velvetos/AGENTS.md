# VelvetOS Core package — local engineering guide

Scope: Core kernel architecture, module contracts, policy registry, instance attachment and Control/Office interfaces.

- Core is a backend kernel/catalog + contracts, not a business frontend, message broker or second nervous-system runtime.
- Business-specific identity/facts belong to `instances/<id>/` or the owning pack, not Core root.
- Use `KERNEL.md`, `LAYERS.md`, `REPOS.md`, `PROJECT-REQUEST-GATE.md`, `PROJECT-AUTHORITY-MANIFEST.json` and the exact package being changed.
- Extend existing Project Request / policy / sensor registries; do not create another capability router, agent harness or policy engine.
- External effects keep one canonical `policy_id`; evidence layers do not become authorities.
- Unknown/stale state remains explicit. No secrets, fabricated provider state, invented facts or hidden fallback.
- Instance scaffolds attach Core; do not host a second live business frontend inside Core.

## COMPETITOR_NEUTRAL_ADMISSION_V1 — Core engineering decisions

A competing agent runtime, orchestrator, memory layer or complete replacement for an incumbent is always eligible for documented research and fair comparison. Do not exclude a candidate solely because its functions overlap VelvetOS or require replacing previous work. Keep full replacement and hybrid compositions open. Register post-policy candidates in the existing Office v2 Candidate Registry, and queue credible over-capacity challengers in the lane rather than forgetting them. Legacy `no-second-orchestrator` bars only unapproved **production** duplication; isolated LAB experiments still require admission, security and cost gates. See `constitution/CONSTITUTION.md` and `docs/implementation/office-v2/phase2/admission-policy-v0.md`.

Verification: `python3 scripts/check-velvetos.py`, `python3 scripts/check-policy-architecture.py`, then `python3 scripts/check-all.py`.
Policy routing reference: `policy_id: project.request.preflight` is router-only; external effects stay with the registry-mapped effect authority.
