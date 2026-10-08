# AGENTS.md — VelvetOS Core

PRODUCT: VelvetOS Core
ROLE: shared backend kernel
PROJECT: velvetos-core
TEST: python3 scripts/check-all.py
LINT: python3 scripts/check-policy-architecture.py

VelvetOS Core is the shared backend kernel for laws, contracts, modules, policies and sensors. Business frontends attach Core through `instances/<id>/` and their own repositories; business identity and operating facts do not belong in this root guide.

## ALWAYS-ON ROUTING

Before substantive work, resolve:
- `packages/velvetos/PROJECT-REQUEST-GATE.md`
- `packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json`

No substantive work starts before `project_preflight: PASS`. The manifest decides the domain, authority mode and local instruction guide. Load this root guide plus only the selected domain-local `AGENTS.md`; do not preload unrelated specialist guides or warehouse capabilities.

Unknown domain, missing local instructions, contradictory authority or stale critical evidence stays fail-closed. Do not fall back to remembered chat context when current authority is unresolved.

## GLOBAL BOUNDARIES

- External effects use the single canonical effect-authority `policy_id` in `packages/velvetos/policy/policy-registry.json`. Routing, evidence, transport, QA and runtime health do not authorize effects by themselves.
- `NO_NEW_RECURRING_COST` remains global. New or changed paid-capable behavior follows `constitution/NO_NEW_RECURRING_COST.md`; general permission to install or operate is not spend approval.
- Never invent money, provider state, receipts, permissions, source bodies, metrics or operational facts. Unknown remains unknown.
- Never commit secrets. Keep personal/private sources outside normal traversal unless the request explicitly names them.
- Core is not a second office, message broker, nervous-system runtime or live business frontend.
- Extend existing manifests, registries, policies and harnesses instead of creating parallel routers, catalogs or policy engines.
- Provider/tool success is not inferred. Claims such as sent, published, synced, deployed or deleted require the canonical postcondition evidence.
- Irreversible/destructive, permission, rights/privacy and physical-world effects remain protected by their mapped policy boundary.

## VISIBLE TEXT

**Visible Text Gate is global.** Human-visible AI-authored or rewritten text follows `constitution/VISIBLE_TEXT.md` on the actual candidate text.

Surface selection remains explicit, including `customer-message`, `owner-brief`, `human-document` and `ui-microcopy`. Tool/skill existence is not proof that the gate ran; unproven candidate execution remains `UNPROVEN`.

Verification: `scripts/check-visible-text-gate.py`.

## INSTRUCTION LOCALITY

The root guide is intentionally small. Domain-specific operating instructions live beside their owning package and are selected by `PROJECT-AUTHORITY-MANIFEST.json#instructionLocality`.

Rules:
- root + selected local guide only by default;
- specialist/capability loading follows the already-selected route;
- local guides are instruction/evidence surfaces, never new authorization engines;
- a task crossing multiple routed domains may load one primary local guide per selected domain;
- keep unrelated domain context unloaded.

## VERIFICATION

Run the routed sensor set for scoped changes, then `python3 scripts/check-all.py` for repository-wide changes. Do not claim success when a required computational sensor fails.

For Kernel architecture, instance attachment and repository boundaries, use `packages/velvetos/AGENTS.md`, `packages/velvetos/KERNEL.md`, `packages/velvetos/LAYERS.md` and `packages/velvetos/REPOS.md`.
Policy routing boundary: `policy_id: project.request.preflight` is a router only; destination external effects remain owned by their registry-mapped effect authority.
