# VelvetOS Control API — local guide

Scope: typed projection gateway for the Control Center.

- This package is a read-first projection over canonical VelvetOS sources, not a SoT, queue, broker or second runtime.
- Keep server-side auth/secrets out of client payloads and repo content.
- Unknown/stale/disconnected source state stays explicit; never replace missing state with zero/empty success.
- Actions remain fail-closed unless a safe canonical route exists; this API cannot invent authorization.
- Read `README.md`, schemas and the exact adapter involved. Do not load VF creative/fabrication/business context for ordinary API work.
- Policy/receipt decisions remain with their canonical `policy_id`.

Verification: `python3 scripts/check-control-api.py`.
Policy routing reference: `policy_id: project.request.preflight` is router-only; API projection state cannot authorize an external effect.
