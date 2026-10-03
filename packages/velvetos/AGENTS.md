# VelvetOS Core package — local engineering guide

Scope: Core kernel architecture, module contracts, policy registry, instance attachment and Control/Office interfaces.

- Core is a backend kernel/catalog + contracts, not a business frontend, message broker or second nervous-system runtime.
- Business-specific identity/facts belong to `instances/<id>/` or the owning pack, not Core root.
- Use `KERNEL.md`, `LAYERS.md`, `REPOS.md`, `PROJECT-REQUEST-GATE.md`, `PROJECT-AUTHORITY-MANIFEST.json` and the exact package being changed.
- Extend existing Project Request / policy / sensor registries; do not create another capability router, agent harness or policy engine.
- External effects keep one canonical `policy_id`; evidence layers do not become authorities.
- Unknown/stale state remains explicit. No secrets, fabricated provider state, invented facts or hidden fallback.
- Instance scaffolds attach Core; do not host a second live business frontend inside Core.

Verification: `python3 scripts/check-velvetos.py`, `python3 scripts/check-policy-architecture.py`, then `python3 scripts/check-all.py`.
Policy routing reference: `policy_id: project.request.preflight` is router-only; external effects stay with the registry-mapped effect authority.
