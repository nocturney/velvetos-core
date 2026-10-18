# Office 2.0 — agent-composition staged intake (2026-10-10)

**Status: Phase 2 research/queue integration only.** This is not a runtime deployment, Golden Fixture success, approved new provider, recurring charge, production action or second scheduler.

**Owners:** [P0 implementation #612](https://github.com/nocturney/velvetos-core/issues/612), [Fleet #604](https://github.com/nocturney/velvetos-core/issues/604). Canonical state lives only in [Candidate Registry](candidate-registry-v0.json) and [P0 shortlists](p0-shortlists-v0.json); [A/B/C experiment plan](agent-composition-plan-v0.json) is a research handoff, not a separate scheduling system.

## Decision: compare one product, one specialist, and selective modular composition

**A:** incumbent GrokBot/Office system only. **B:** same task owner invoking *one* bounded Hermes or Rakazo worker. **C:** one replaceable runtime plus separately admitted governance, Spaces UI and derivative memory; no independent second scheduler, permission owner or source of truth. Adopt only proven parts; never glue together all agent processes indiscriminately.

| Canonical ID | Source | Initial role |
| --- | --- | --- |
| `candidate-rakazo` | [Rakazo (elie222)](https://github.com/elie222/rakazo) | agent-runtime, multi-agent, sandbox |
| `candidate-hermes-agent` | [NousResearch Hermes Agent](https://github.com/NousResearch/hermes-agent) | agent-runtime, skills, memory |
| `candidate-agent-zero` | [Agent Zero (agent0ai)](https://github.com/agent0ai/agent-zero) | agent-runtime, linux-gui, browser |
| `candidate-copilotkit-openbot` | [CopilotKit OpenBot](https://github.com/CopilotKit/OpenBot) | agent-runtime, policy-gateway, audit |
| `candidate-copilotkit-openmuse` | [CopilotKit OpenMuse](https://github.com/CopilotKit/openmuse) | agent-ui, proactive, long-running-tasks |
| `candidate-copilotkit-opendots` | [CopilotKit OpenDots](https://github.com/CopilotKit/OpenDots) | agent-ui, spaces, documents |
| `candidate-anil-open-dots` | [Anil-matcha/open-dots](https://github.com/Anil-matcha/open-dots) | approval, coding-worker, telegram |
| `candidate-diggerhq-opendots` | [diggerhq/opendots](https://github.com/diggerhq/opendots) | delegation, topic-memory, long-running-tasks |
| Existing `candidate-letta` | [Letta](https://github.com/letta-ai/letta) | Memory-context challenger, source ID preserved |
| Existing `candidate-opendots` | `prior-research://agents` | Unresolved historical identity — **must not** alias to any of three distinct OpenDots repositories |

All eight additions are `RESEARCHED/BENCHMARK_REQUIRED/NOT_RUN/authority_role=NONE`, `source_item_id=null`, with provenance and replacement/component/hybrid options. Original 68 inventory rows and legacy 82 IDs remain untouched; existing benchmark *active* shortlists stay frozen. Overflow is `queued_challengers`, not a decision or LAB admission.

## Handoff into the existing Office stages

**Phase 2 (now):** source, license, paid dependencies, OS/hardware and security review; version-pin only after admission, no live installs. The existing Phase 2 sensor validates registry/queue consistency and the A/B/C plan.

**P0 #612 + Phase 3A:** reuse the canonical Task Envelope/Worker Receipt/Project State and protected Git PR pipeline. Restate's already selected durable architecture is not being replaced, nor is it automatically given production ownership; alternative durability needs the identical 20-step destructive benchmark.

**Phase 3B:** apply the existing identity → OPA decision → brokered exact-scope secret → effect gate → sanitized audit. OpenBot's CEL/approval ideas are candidates to evaluate, not an authorized second policy engine. Negative controls: injection via email/browser, OTP/reset links, stolen creds, unapproved send/publish/purchase, browser/shell exfiltration, denied delegation or provider fallback.

**Phase 3C:** keep the existing neutral model-routing contract; local-first zero-new-recurring-cost tool+vision benchmarks, explicit measured resource/token receipts, no Codex CLI or assumption that hosted free tiers are production-viable.

**Phase 3D (not yet implemented here):** after CANDIDATE → ADMITTED → isolated LAB gates, run identical synthetic Golden Fixtures for A/B/C and negative controls. Score evidence, QA, approvals, crash/cancel/UNKNOWN, memory deletion/provenance, rollback, cost and operator burden. B and C are not automatically better than A.

**Phase 3E / #604:** Rakazo/Agent Zero Linux container success is not evidence of native Windows/Mac GUI execution, two-host fleet placement or failover. No competing worker scheduler or lease owner; route through existing #604 evidence.

**SHADOW → PILOT → PRODUCTION:** only after version pins, independent QA, comparative scorecards, security/legal review, scope-limited approval, effect-owner map, readback and tested rollback. A failed incumbent does not automatically authorize its challenger.

## Dependencies and limitations worth retaining

CopilotKit/OpenDots/OpenBot/OpenMuse depend on CopilotKit Intelligence for key conversation paths; permissively licensed UI does not make the service free or independent. Anil-matcha/open-dots uses Boat/Claude and has unresolved root LICENSE in our 2026-10-10 review. diggerhq/opendots depends on OpenComputer. Agent Zero offers a Docker GUI and a host bridge that must remain disabled. Letta must never replace canonical vfmem/Project State from research alone. No external effects or provider calls have been run as evidence for these candidates.

**Next engineering gate:** choose a single contender, complete license/security/cost/isolation preflight, implement a typed fixture adapter with sanitized outcome receipts, then compare A/B/C fairly without production credentials, subscriptions or automatic promotion.

References: [Admission policy](admission-policy-v0.md) · [standard scorecard](scorecard.schema.json) · [Phase 3B](../phase3b/README.md) · [Phase 3C](../phase3c/README.md) · [P0 worker](p0-worker-offline-contract-2026-10-08.md).
