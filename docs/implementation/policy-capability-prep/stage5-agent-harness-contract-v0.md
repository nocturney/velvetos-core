# Stage 5 draft - Agent Harness and capability locality

Status: **STAGE 5 ACTIVE | 5A CONTEXT LOCALITY + 5B HARNESS CONSOLIDATION + 5C WORKSPACE DISTRIBUTION IMPLEMENTED | STAGE 5 GATE REMAINS**

## Purpose

Prepare the shared execution shape requested by the integrated handoff without creating a second agent runtime. The upstream `agent-harness` source contributes a loop discipline only. VelvetOS already has `vfharness`; any later adoption must extend that surface rather than install or recreate the upstream harness.

## Proposed shared loop

`GOAL → PLAN → EXECUTE → VERIFY → RETRY/ESCALATE → CLOSE`

Semantics:
- **GOAL:** bounded intent with explicit completion evidence.
- **PLAN:** ordered tasks, dependencies, policy preconditions and verification targets.
- **EXECUTE:** use the routed existing pack/tool; never simulate an unavailable specialist.
- **VERIFY:** machine evidence where deterministic verification exists; provider/live readback where external effects require it.
- **RETRY:** capped and approach-changing, not repeated identical calls.
- **ESCALATE:** only after the documented retry/failover budget or a true human-required gate.
- **CLOSE:** refused while required evidence is missing, a blocking gate is open or the target state is unverified.

## Authority boundary

The harness never:
- creates ALLOW/DENY semantics;
- changes a policy decision;
- treats its own plan/state as owner authorization;
- converts a missing receipt into a waiver;
- authorizes paid/provider use;
- authorizes publication, send, delete, permission mutation or other external effects.

Every consequential task must name and satisfy the canonical `policy_id` chosen by the destination Stage 4 framework.

## Context locality proposal

| Surface | May contain after Stage 5 | Must not contain |
| --- | --- | --- |
| Root `AGENTS.md` | Core identity, authority hierarchy, hard boundaries, scope selection, test pointers | VF business facts, printer fleet facts, domain creative instructions |
| Domain/package-local guide | domain instructions and verification closest to code | unrelated business/domain context |
| Instance surface | Velvet Factory bindings, verified local facts and instance-specific operational context | generic Core law duplicated as local authority |
| Harness state | task plan, observations, evidence refs, retry/escalation state | policy authority or permanent business facts |

Stage 8 remains the final owner of Core/Instance placement. Stage 5 may establish locality mechanics but must not guess future instance facts.

### Stage 5A implementation receipt

Stage 5A implements only the locality mechanics above. Root `AGENTS.md` is now Core-only; domain instructions live next to their owning packages; `PROJECT-AUTHORITY-MANIFEST.json#instructionLocality` selects root + one primary guide per routed domain with warehouse default `off`. Baseline/acceptance evidence is pinned in `packages/velvetos/policy/reports/stage5a-context-locality-baseline.json` and `stage5a-context-locality.json`. The external-effect policy registry is hash-identical to the Stage 4 acceptance snapshot, so this locality change does not alter authorization semantics. Capability routing/loop evolution remains later Stage 5 work.

### Stage 5B implementation receipt

Stage 5B consolidates the shared execution contract without creating a new runtime. `packages/vfharness/LOOP.md` is the only global loop authority; `packages/vfharness/AGENTS.md`, `packages/vfharness/SKILL.md`, the Cursor harness skill/rule and `docs/HARNESS.md` are pointer-only secondary surfaces. Cross-tool continuation remains `office/control/HANDOFF.json` + `packages/vfmem/HANDOFF.md`; handoff carries context/state only and never becomes an orchestrator or policy authority. Specialized playbooks and historical harness state remain intact. Acceptance evidence is pinned in `packages/velvetos/policy/reports/stage5b-harness-consolidation.json`.

### Stage 5C implementation receipt

Stage 5C stabilizes workspace distribution without expanding the warehouse. `nocturney/velvetos-workspace-distribution` PR #3 / merge `4fa715dc78275b87a942658b26b74608932d8d50` publishes Workspace Stack `1.6.0` with the desired skill count unchanged at 35. `creative-craft` remains the ambient natural-language router; the eight professional craft specialists remain available workspace-wide but are explicitly **routed-only**, selected by intent/pipeline and never ambient-preloaded. Workspace invocation has `authorizationEffect=NONE`; it cannot grant publish/send/spend/delete/permission authority. The distribution verifier enforces the exact specialist set, standards-compliant `name`/`description` frontmatter, `warehousePreload=false` and router continuity; Creative Craft structural evals pass 56/56. Core acceptance evidence is pinned in `packages/velvetos/policy/reports/stage5c-workspace-distribution.json`.

## Upstream elements intentionally not adopted

- upstream per-domain committed harness manifests as a second source of capability truth;
- upstream plugin/agent installation;
- a separate loop controller runtime;
- closure based on worker self-report;
- broad context loading from every domain.

## Verification design for Stage 5

When Stage 5 is active, acceptance should prove:
1. a Core-only task does not load VF creative/printer/business context;
2. the nearest domain guide resolves correctly;
3. an Instance task receives its verified binding without moving generic policy authority into the Instance;
4. required policy/receipt gates cannot be waived by harness state;
5. retry limits and escalation preserve the existing `vfharness` failure discipline;
6. close fails when target evidence is absent.

No check or sensor is added by this preparation bundle.

## Data ownership

Generic loop semantics belong to Core. Task checkpoints remain in the existing harness state model. Velvet Factory facts remain Instance/domain facts and are not introduced here.

## Rollback

Before Stage 5 adoption, rollback is deletion of this draft. After any future adoption, rollback must restore the prior `vfharness` behavior and instruction locality from Git history without migrating business state.

## Entry gate

Implementation may begin only after Stage 3 completes and the reform reaches Stage 5 through the Stage 4 gate. Until then this document is design input only.
Stage 5 routing reference: `policy_id: project.request.preflight` remains router-only; no local guide or harness state can replace a destination effect-authority policy.
