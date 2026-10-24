# Office v2 Phase 2 Candidate Admission Policy v0

Authority: START HERE Phase 2. This policy defines benchmark admission; it grants no production authority.

## Admission order

`RESEARCHED → CANDIDATE → ADMITTED → LAB → SHADOW → PILOT → PRODUCTION`.

A candidate moves forward only when target-stage evidence exists. Availability, popularity, an easy install, incumbent failure, or prior discussion is never sufficient.

## COMPETITOR_NEUTRAL_ADMISSION_V1 — unbiased intake and replacement eligibility

Every plausibly relevant new alternative, including a direct competitor to the current core/office/agent runtime, is recorded as `DISCOVERED`/`RESEARCHED` in the canonical Candidate Registry **before** any "use patterns only", "skip", "we have a solution" or installation verdict. Record a source link, matching capability/fixture lane, whether it could replace the incumbent in whole or part or be composed with it, current evidence, and an explicit next decision. The historical 68-item source import is immutable; later candidates have `source_item_id: null` and a structured `comparison_review`.

A full benchmark shortlist remains 2–3 challengers for operational focus. Overflow goes in that lane's `queued_challengers`, not `REJECTED_WITH_REASON` or an untracked chat. Triage and promotion require comparable contract evidence, and previously frozen lanes can reopen for a credible challenger against the same fixture.

**Never decide from sunk cost or incumbent preference.** Exiting or deferring requires concrete capability/fixture, license, security, hardware, maintenance, cost, integration or migration/rollback evidence. "Overlaps our stack", "another orchestrator", "already implemented" or "we would need a rewrite" alone cannot justify rejection. LAB trials may compare replacement, parallel non-production or hybrid designs under isolation; unapproved production duplication is still prohibited.

**No authority expansion:** registry/research/queue state does not install software, grant network/credentials, change sources of truth, transfer external-effect authority or waive `NO_NEW_RECURRING_COST`.

## COMPOSITION_FIRST_ROLE_REVIEW_V1 — capability roles before competing shortlists

**Architecture principle:** take the best *verified* function from each appropriate source. Similarity of name, category, or broad "agent/fleet/gateway/memory" lane is **not** proof that two tools are substitutes. A shortlist is research/benchmark accounting, not an instruction to pick exactly one product across dissimilar layers. This refines `COMPETITOR_NEUTRAL_ADMISSION_V1`; it does not waive existing admission or production gates.

At intake/source review, before asserting candidate-versus-incumbent or two challengers are competitors, record in the existing `comparison_review.rationale` / `evaluation_route`:
1. **Primary role and contract:** what the component actually owns, its inputs/outputs, operating system, trust boundary and dependencies (e.g., durable workflow, multi-host placement, host transport, agent framework, browser execution, browser session pool, memory retrieval, context compaction, model serving, model gateway, identity, authorization, secrets, QA, UI).
2. **Relationship:** `TRUE_SUBSTITUTE` for substantially the same role/fixture; `COMPLEMENTARY` across roles; `PARTIAL_OVERLAP` where both own some shared function; or `UNKNOWN` until source evidence clarifies. These labels are descriptive review vocabulary **inside existing free-text fields**, not a new registry, JSON lifecycle, promotion verdict or source of authority.
3. **Three alternatives where plausible:** A = canonical baseline; B = a genuine same-role replacement; C = a minimal composition using compatible interfaces. Compare B and C on the same authorized end-to-end Golden Fixture, with component-level probes as needed. Measure completed/verified task output, false positives/negatives, crash/retry/UNKNOWN, resource and token use, wall time, operator intervention, security/rights, ongoing cost, dependency/version risk, maintenance, rollback and **net integration complexity**. Do not predeclare an all-in-one or multi-tool winner.
4. **One authority per effect:** a hybrid may have multiple components, but must preserve one canonical task owner, source of truth, effect-authorization decision, credential boundary and reconciliation/receipt path. Where two components both offer scheduling, routing, policy, retries or persistent state, explicitly assign ownership and disable/bypass the redundant mechanism only in an approved LAB design; never create silent double dispatch, double retries or competing production writers.
5. **Gate and next action:** `RESEARCHED` permits source/compatibility review. Composition is **not** an install recommendation: version pins, target rights, free host/resource lease, no paid API/recurring cost, credential/network review and the existing LAB→SHADOW→PILOT→PRODUCTION checks still apply. Preserve the incumbent and any frozen winner until a valid contract-matched improvement is demonstrated.

**Examples requiring role-aware interpretation of the *existing* registry (not new competing lanes):**
- `worker-fleet-placement`: Restate is selected for *durable execution*, Desktop Commander is an existing *remote host transport*, Nomad is a *placement scheduler*, Dagu/Kestra/Windmill are broader *job/workflow workers*, Ray is specialized *distributed compute*, and Browserless/Selenium Grid provide *browser sessions*. Compare true dispatch alternatives with one another; separately test whether a durable spine + placement + host adapter improves real two-host throughput.
- `agent-runtime`: agent frameworks (Pydantic AI / LangGraph) and ready-made coding agents should not be forced into a single winner with Quicksand (disposable sandbox), browser specialists (Browser Use / Skyvern) or workbench UI (OpenDots/OpenMuse). Keep one canonical envelope and prevent secondary approval/scheduler ownership.
- `memory-context`: Hindsight/Supermemory/Letta memory, Graphiti temporal relations, XERJ code retrieval and Context Mode tool-output/context budgeting serve partly different contracts. Compare each relevant derived function and a minimal combined approach against vfmem/Project State, which remains authoritative.
- `tool-gateway-interoperability`: ToolHive MCP server runtime/isolation, agentgateway protocol/API ingress and Bindu A2A discovery have potentially complementary roles **and overlaps** in gateway/policy features; compatibility and duplicate-authorization risks need source-backed checking.
- Model/provider/inference distinction: LiteLLM and TensorZero overlap as gateways but have differing provider abstraction/evaluation capabilities; Ollama/llamafile/Strata are *model serving*, not equivalent gateways. Only layer gateways together if an explicit interface test proves net benefit.
- Native binary investigations: Ghidra is a binary-analysis engine; REA documents a Ghidra provider and is an agent-facing investigation/Evidence interface. Assess composition first; direct Ghidra is a same-engine reference to measure the REA layer, not a winner-takes-all replacement for it (see owner #595 and archived pilot #606).

**Anti-patterns:** "already have something similar" cannot reject a source; "every extra capability must be installed" also cannot justify a hybrid. Keep the 2–3 active-benchmark challenger capacity, the 68-item historical import, existing candidate IDs, frozen verdicts, and existing one-source-of-truth / P0 resource safeguards intact. Source-level hypotheses and upstream claims are not VelvetOS runtime proofs.

## Derived Skill comparison lane (non-P0)

The `skill-capability-comparison` lane is an evidence/Golden Fixture review lane for individually indexed, provider-neutral Skill candidates. It is not a new P0 shortlist, install queue, scheduler, authority, or production deployment. Candidates retain explicit evaluation routes in the canonical Candidate Registry, and advancing any candidate still requires the normal admission/QA gates.

## CANDIDATE → ADMITTED

Require all of:
- bounded capability/contract scope and a named shortlist lane where relevant;
- license, maintenance and ownership review;
- security/trust review and credential class;
- platform/hardware feasibility;
- isolation plan;
- resource/cost capture plan;
- rollback/export/uninstall plan, or an explicit recorded rollback failure;
- relevant Golden Fixture mapping;
- no new production writer or source-of-truth claim.

## ADMITTED → LAB

Require a versioned definition, reviewed immutable dependencies where practical, LAB-only credentials, bounded network/storage paths, health probe, teardown path and evidence location.

## LAB → SHADOW

Require relevant Golden Fixtures through a capability adapter, standard scorecards, security/operations scoring and reconciliation evidence. SHADOW has no production authority.

## SHADOW → PILOT → PRODUCTION

Require explicit bounded scope, rollback proof, operator visibility, authority-map/policy changes if production mutation is introduced, and readback receipts. A failed incumbent does not auto-promote a challenger.

## Exit verdicts

`REJECTED_WITH_REASON`, `BENCHMARKED_AND_LOST`, `SUPERSEDED`, and `DEFERRED_WITH_REASON` are valid from any appropriate stage and retain evidence plus a reason.

## Resource and cost capture

Capture wall time, CPU/RAM, GPU/VRAM when relevant, storage/network, external/API cost, recurring cost, operator burden, and install/maintenance burden. No universal numeric improvement threshold is imposed.

## Freeze rule

Stop researching when requirements are covered, fixtures ran, security and operations were scored, rollback was tested or explicitly failed, and a verdict was recorded. Reopen only for material evidence defined by `research-freeze-record.schema.json`.
