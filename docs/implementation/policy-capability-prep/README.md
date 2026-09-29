# Policy Architecture Reform - capability pre-integration prep

Status: **NON_RUNTIME_DRAFT / Stage-3-safe preparation only**
Prepared: 2026-09-29
Controlling roadmap: `packages/velvetos/policy/reports/migration-map.json` + the canonical Policy Architecture Reform MASTER HANDOFF.

This folder is a subordinate capability backlog preparation surface. It is **not** a second Phase 0–9 program, policy registry, authority system, agent hierarchy, artifact store, scheduler, or runtime router.

## Live checkpoint used for this prep

- `origin/main`: `5f621d3ce984a6b1384461da8bbf1aeffe82a96a`.
- Latest main `VelvetOS Core Sensors`: run `36535708924`, completed `success`.
- Selector mode: `shadow`.
- Stage 3: `PREPARED_NOT_ACTIVE`.
- Stage 3 activation receipt: absent.
- Ruleset `23284099`: `enforcement=disabled`; existing deletion + non-fast-forward rules only.
- Fresh Stage 2 observation generated `2026-09-29T07:28:49Z`: 35 PRs, 74 runs, 1.6355 observation days, 0 critical misses, 1 classified/repaired noncritical miss, complete history, deterministic replay PASS.
- Gate: `eligible=false`; only blocker is `MINIMUM_OBSERVATION_DAYS_NOT_MET`.

No Stage 3 runtime behavior was changed by this preparation.

## Allowed scope before Stage 3 exit

This work is intentionally limited to research, classification, provenance, draft contracts, golden fixtures, interface design, and acceptance-test design. It does not activate new agents, capability routing, policy semantics, authority registries, publication behavior, AGENTS loading changes, selector enforcement, rulesets, or provider calls.
## Artifacts

- `upstream-classification.json` - evidence-backed ADAPT / IDEA_ONLY / REJECT / HOLD decisions for selected high-value upstream concepts, pinned to upstream commit `19392f7a08264ed00486a251f5b2098321771f94` and exact blob SHAs.
- `draft-contracts-and-fixtures.json` - compact cross-stage index of candidate fields, invariants and fixtures. It is a summary only; when a granular draft below exists, the granular draft is the deeper design input and neither artifact is authority.
- `stage4-action-receipt-v0.schema.json` + `stage4-action-receipt-test-vectors-v0.json` - exact-action receipt proposal and negative/golden cases; no validator/runtime wiring.
- `stage5-agent-harness-contract-v0.md` - maps upstream loop discipline onto the existing `vfharness`; no second orchestrator.
- `stage6-creative-os-archetypes-v0.json` - presentation-only Creative OS taxonomy under Product Truth.
- `stage6-prompt-asset-v0.schema.json` - prompt version/eval asset shape; not a registry, loader or policy authority.
- `stage7-research-router-v0.json` - event-driven research method decision table; no scheduler/provider execution.
- `stage7-cost-envelope-v0.schema.json` - bounded-cost envelope shape for future Stage 7C evaluation; it authorizes no spend.
- `stage7-work-ledger-record-v0.json` - continuation/audit index field inventory; storage remains TBD by Stage 7D.
- `stage8-printer-capability-fields-v0.json` - printer capability field inventory only; contains no Velvet Factory fleet values and grants no printer-control authority.
- `stage8-knowledge-record-v0.schema.json` - source-grounded Core/Instance knowledge shape; derived knowledge never overrides canonical operational truth.
- `stage9-acceptance-plan-v0.json` - final one-system acceptance obligations and remediation triggers; no cleanup is executed by this draft.

## Reform ownership map

| Capability family | Owning Stage | Current prep only | Future implementation boundary |
|---|---:|---|---|
| Human Gate / exact-action review evidence | 4 | receipt fields + negative vectors | extend canonical external-effect policy framework; review never replaces policy decision |
| Agent Harness / capability locality | 5 | execution-loop contract + descriptor fields | extend `vfharness`; nested/local instructions; no second orchestrator |
| Creative OS / prompt governance | 6 | editorial plan fields, Product Truth separation, prompt-eval concepts | integrate with Visible Text tiers and existing vfom/vfbrand/vfcopy surfaces |
| Safe learning / Research Router / cost envelopes / Work Ledger | 7A–7D | route tables, candidate records, retention constraints | use one event-driven research path and Stage 7 retention/cost authority |
| Print Ops / Knowledge Engine / Business Ops | 8 | field inventories and source-grounded fixtures | Core owns generic schemas/methods; VF Instance owns fleet/business facts |
| Deduplication / shim retirement | 9 | acceptance targets only | remove temporary mechanisms after consumer/coverage proof |

## Required capability-PR contract after Stage 3

Every future capability PR must state all of the following before implementation begins:

1. destination reform Stage;
2. canonical policy dependencies for every side effect;
3. instruction/context locality;
4. Core vs Instance data ownership;
5. verification and negative controls;
6. rollback path;
7. migration/compatibility effect;
8. explicit proof that the capability does not create parallel authority.

If any answer depends on an unopened Stage decision, the work remains specification-only.
## Upstream adoption rules

The reviewed upstream repository is a method/reference source, not an install target. Do not bulk-install it. Port only the minimal method, deterministic tool, or reference that survives VelvetOS authority review.

Classification meanings:

- `ADAPT` - useful method can be translated into an existing VelvetOS surface in the owning Stage.
- `IDEA_ONLY` - retain the design lesson, but importing the implementation would duplicate or conflict with existing authority/runtime.
- `HOLD` - potentially useful, but current evidence or destination architecture is insufficient for a safe implementation decision.
- `REJECT` - do not carry the mechanism forward. A rejected submechanism may still be named inside an ADAPT entry's exclusions.

Upstream-specific compliance, provider, UI, or storage assumptions never become VelvetOS obligations just because they appear in the source skill.

## Cross-stage invariants

- Machine-readable policy owns consequential decisions; capability metadata may only reference policy IDs.
- Product Truth owns physical product identity. Creative OS owns presentation only.
- `OWNER_REVIEW_CANDIDATE` and `ready_for_publish` are not publication authorization.
- Human review evidence cannot widen a higher safety invariant or replace a missing policy decision.
- Feature flags may control rollout exposure but cannot bypass policy.
- Research findings and derived knowledge cannot promote themselves into policy or owner authorization.
- Work Ledger is an index/continuation view over canonical artifacts, not a second store.
- Unknown facts remain unknown; no guessed printer, price, SLA, demand, cost, or business values.
- `NO_NEW_RECURRING_COST` remains default; paid-capable routes stay fail-closed without the future Stage 7C authority.

## Stage 3 protection

Do not use these drafts to justify any early Stage 3 activation. The fixed exit gate remains unchanged. The next runtime transaction is still the canonical Stage 3 cutover only after a fresh observation report says `eligible=true` with no blockers and the canonical preflight returns `ready=true`.

Until then, this folder may evolve only as non-runtime preparation.
