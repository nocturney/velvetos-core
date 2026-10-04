# Stage 5 - Agent Harness and capability locality

Status: **STAGE 5 CLOSED | 5A CONTEXT LOCALITY + 5B HARNESS CONSOLIDATION + 5C WORKSPACE DISTRIBUTION + INTEGRATED GATE PASS**

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

## Integrated Stage 5 acceptance

`packages/velvetos/policy/reports/stage5-acceptance.json` closes Stage 5 against merged `main` `67bd5dc1bedfb98b850e4b5b09090dcd51598e48` and post-merge full-suite run `37175062910` / job `111355869001` (116/116 PASS). `check-policy-architecture.py` validates source-receipt hashes and regenerates the acceptance receipt byte-for-byte.

The gate passes all seven criteria:
1. Core/system context remains business-clean and bounded to the selected local guide.
2. Known routine requests load only root + the minimum routed domain instructions.
3. `packages/vfharness/LOOP.md` remains the single global execution-loop authority; no second orchestrator exists.
4. Workspace specialist craft remains available but routed-only, with no warehouse preload.
5. Workspace skill invocation creates no external-effect authority.
6. No context-warehouse regression is introduced across Core + Workspace distribution.
7. The post-5C main full sensor suite passes 116/116.

Stage 6 entry is allowed. The next stage may simplify Visible Text / creative / DCC ceremony by surface and risk, but it may not weaken truth, rights/privacy, commercial commitment, public-publish, spend, destructive action or exact-binding safeguards.

## Data ownership

Generic loop semantics belong to Core. Task checkpoints remain in the existing harness state model. Velvet Factory facts remain Instance/domain facts and are not introduced here.

## Rollback

Before Stage 5 adoption, rollback is deletion of this draft. After any future adoption, rollback must restore the prior `vfharness` behavior and instruction locality from Git history without migrating business state.

## Stage 6 handoff

Stage 5 is closed. `policy_id: project.request.preflight` remains router-only; no local guide, harness state, Workspace skill or specialist selection can replace a destination effect-authority policy. Stage 6 should reuse the locality and routed-specialist mechanics established here rather than broaden default context again.
