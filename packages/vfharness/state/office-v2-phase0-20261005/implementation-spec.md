# Office v2 Phase 0 — implementation spec

Authority: Google Doc `15NMtyaUDjxiACPKEY_T5rW7IUFwtD2qU88yhbKQhEkw` (“VelvetOS Office v2 — MASTER PLAN v3 · FINAL START HERE · 2026-10-05”), modified 2026-10-05T17:00:24.935Z.

## Goal
Establish the Phase 0 safety/continuity/governance foundation on top of Reform v2 without changing production writers or replacing existing policy/state authority.

## Non-goals
- No WSL2/Docker installation yet.
- No durable-engine, model-gateway, NATS, feature-flag or MCP/A2A winner selection.
- No production credential migration.
- No new Instagram/Gmail/Drive/orders writer.
- No manufacturing cutover and no printer command path.

## Authority / sources of truth
- Target code baseline: `origin/main` at `81e5dbb28b7de6bead5fc581736f16f27b5059f0`.
- Work only in `D:\Velvet\Worktrees\office-v2-phase0-foundation-20261005`, branch `office-v2/phase0-foundation-20261005`.
- Project routing: `packages/velvetos/PROJECT-REQUEST-GATE.md` + `PROJECT-AUTHORITY-MANIFEST.json`.
- External-effect authority: existing `packages/velvetos/policy/policy-registry.json`; Office v2 contracts MUST NOT mint parallel authorization.
- Semantic state authority: existing `packages/velvetos/policy/state-evidence-model.json`.
- Jobs business truth: Google Sheet `VF HQ · jobs`.
- Live runtime/provider state is verified from the provider/runtime, never inferred from Git.

## Acceptance criteria
1. Timestamped live-state receipt exists outside Git and names exact repo SHAs, worktrees, connected nodes, live services/providers, health and known drift.
2. Production Capability Manifest names authority, provider, fallback, evidence, freshness and mutation safety for every Phase-0 critical capability.
3. Correlation contract and Contract Registry v0 exist as versioned definitions and do not duplicate policy authority.
4. External Effect Safety Contract defines intent, idempotency, exact policy decision binding, receipt/readback, unknown-outcome and reconciliation semantics; blind retry after unknown outcome is forbidden.
5. Project State Manifest + verifier demonstrate checkpoint → compact → verify → resume with PASS/PASS_WITH_WARNINGS/FAIL_CLOSED semantics.
6. Office v2 seven-class storage/lifecycle map is explicitly orthogonal to Reform v2 four semantic categories; Phase 0 adds no new live business/runtime truth to Git, while existing Reform v2 repo-hosted operational state remains under its prior authority until a later gated migration.
7. Backup/restore admission, credential/trust classes, Node Contract and Migration Ledger contracts exist.
8. Minimal Migration Console/report is read-only.
9. Baseline and post-change sensors are green; no production writer is added or changed.

## Evidence
- Off-repo: `D:\Velvet\Artifacts\OfficeV2\phase0\evidence\...`
- Runtime/project state: `D:\Velvet\State\OfficeV2\...`
- Versioned contracts: `docs/implementation/office-v2/phase0/`
- Targeted sensor: `python scripts/check-office-v2-phase0.py`
- Repository regression: `python scripts/check-policy-architecture.py` and `python scripts/check-all.py`.

## Known Phase-0 gaps at start
- WSL2 absent; Docker absent.
- `velvetos-velvet-factory` local main is three commits behind fresh `origin/main`.
- Instagram MCP provider label is `env` while live username is `velvets_cloud`; routing must not equate label and username.
- Maya host receipt expects adapter 0.9.33 while active registry path is 0.9.31-shadow.
- No versioned xTool binding was found in the current core repo; device capability remains UNVERIFIED until a canonical source is attached.
- Drive write / orders update do not yet have a clearly mapped external-effect authority in the current policy registry; mutation smoke stays blocked until that gap is resolved canonically.
