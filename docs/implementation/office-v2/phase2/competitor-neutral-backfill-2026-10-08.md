# Office v2 — ביקורת ראשונית על פסילות מתחרים היסטוריות (2026-10-08)

**Authority:** `constitution/CONSTITUTION.md#COMPETITOR_NEUTRAL_ADMISSION_V1` and `docs/implementation/office-v2/phase2/admission-policy-v0.md`.  
**Original inventory:** 68 immutable source rows; historical canonical candidate prefix 82 entries remains in place.  
**Audit status:** `FIRST_PASS_PARTIAL`; this is NOT certification that every prior repository was recovered or that performance tests were completed.  
**Canonical tracking:** `candidate-registry-v0.json` + `p0-shortlists-v0.json`; this report is an evidence and handoff receipt, **not another registry**.  
**Related:** [issue #595](https://github.com/nocturney/velvetos-core/issues/595), [policy PR #593](https://github.com/nocturney/velvetos-core/pull/593).

## Scope of first pass

Read-only snapshot reviewed:
- `packages/vfe2b/catalog.json`: 47 picks, of which 21 `embed`, 20 `later`, 6 `skip`.
- `packages/vfe2b/orchestrators.json`: 30 picks, including explicit second-desk/no-swarm exclusions.
- `packages/vfresearch/LINKS.json`: 109 curated research links. A link to a list or pattern source is **not** automatically a runnable competitor.
- `docs/implementation/office-v2/phase2/candidate-registry-v0.json`: 83 entries **before** this backfill, including DeerFlow and 68 original source rows; matching requires name/alias/origin and cannot use raw count subtraction.
- `packages/vfe2b/LOCK.md`, `DEER-FLOW-PATTERNS.md`, `ORCHESTRATORS.md`, `crews/run.md`, `.cursor/skills/vf-run/SKILL.md`, and machine `D:/Velvet/Runtime/repo-intake-links-20261007.py`.
- Public upstream read-only metadata/license/README where noted. Research signals are not test results.

## Material findings and actions

| Technology | Historical reason | Current evidence / distinction | Concrete action |
| --- | --- | --- | --- |
| [DeerFlow](https://github.com/bytedance/deer-flow) | "patterns only, no second runtime" | Active 2.x full agent harness; could replace runtime or form a hybrid. Current comparison is not yet run. | Previously added as `candidate-deerflow`, in agent runtime + memory queue; [separate source-pin and LAB-readiness report](deerflow-v2-comparative-readiness-2026-10-08.md). |
| [OpenClaw](https://github.com/openclaw/openclaw) | Persistent chat/WhatsApp assistant and unattended authority | Active MIT gateway/agent infrastructure. Restricting customer channels is a policy boundary, not evidence that all its internal capabilities lose. | Reopen historical `deferred-openclaw` to `BENCHMARK_REQUIRED`; queue for agent-runtime under synthetic LAB. |
| [CrewAI](https://github.com/crewAIInc/crewAI) | "Pattern only. Do not add a CrewAI runtime." | Active MIT multi-agent orchestration; no same-fixture comparison against incumbent recorded. | Reopen `deferred-crewai`, queue for agent-runtime. |
| [LangGraph](https://github.com/langchain-ai/langgraph) | "Another runtime" / old deferral | Active MIT; important foundation of DeerFlow itself, useful as both direct competitor and composition. | Reopen `deferred-langgraph`, queue separately so DeerFlow success is not mistaken for bare-LangGraph success. |
| [Ruflo](https://github.com/ruvnet/ruflo) | Unattended swarm | Active MIT meta-harness; bounded swarms may still meet isolated agent-runtime contract. | Reopen `deferred-ruflo`, queue for agent-runtime. |
| [AutoGen](https://github.com/microsoft/autogen) | Generic prior defer | **Upstream explicitly says maintenance mode**; directs new users to [Microsoft Agent Framework](https://github.com/microsoft/agent-framework). | Keep AutoGen as evidence-based deferred compatibility reference; register the current MIT successor separately and queue it. |
| [LobeHub](https://github.com/lobehub/lobehub) | "Already have Cursor" / patterns-only | Active chief-agent/operator product. **Community License** permits certain unmodified commercial uses but requires separate commercial licensing to develop and distribute a derivative. | Register `candidate-lobehub` and queue agent-runtime; license review before any modification/distribution. |
| [Bindu](https://github.com/GetBindu/Bindu) | "No second runtime/x402" | A2A identity/discovery may have value without cryptocurrency transactions. Licensing yet to be resolved. | Register `candidate-bindu`, queue tool-gateway interoperability, keep public-payment features disabled. |
| [Flowise](https://github.com/FlowiseAI/Flowise) | "Would be second office OS" | Original repository is **archived** and its README confirms it; this is a legitimate contemporary maintenance concern, unlike the old reason. | Retain historical review as `ARCHIVED_UPSTREAM`; inspect official migration/successor before any new candidate; no forced LAB. |
| [Orca](https://github.com/stablyai/orca) | "Cursor is the office" | More specifically a coding-agent/worktree IDE rather than a universal business agent runtime. | Replace generic historical deferral reason with distinct-role explanation; design developer-workflow fixture before selecting or rejecting. |
| [Superset](https://github.com/superset-sh/superset) | Second coding desk | Active coding-agent orchestration, credible competitor for developer-workflow, not automatically interchangeable with business execution. | Retain provenance in `LINKS.json`; research a dedicated developer-workflow lane and check redistribution license. |
| [Huginn](https://github.com/huginn/huginn) | Patterns only, no Rails daemon | Active MIT event/rule automation; useful against scheduling/event delivery, different from general LLM agent runtime. | Retain research link; define event-automation contract instead of forcing it into an irrelevant agent-runtime lane. |
| [Open Interpreter](https://github.com/OpenInterpreter/open-interpreter) | "Coding stack stays Cursor" | Computer-use/execution capability must be compared by security-limited fixtures, not software overlap. | Keep on separate computer-use lane triage alongside Cua/UFO after #597 rather than broad production access. |
| [UFO](https://github.com/microsoft/UFO) | Blanket no unattended desktop control | Current Cua pilot PR #597 says bounded provider research occurred; records `NOT_NEEDED_BASELINE_SUFFICIENT`, subject to actual merged receipts. | Do not silently equate "not necessary in this baseline" with "inferior forever"; reconsider on a verified gap. |
| Gumloop, Magic Loops, Taskade, Relevance AI | "Same as existing crews/seats" | Overlap rationale is inadequate alone; SaaS license, cost, live effect controls and role fit require separate measurement. | `TRIAGE_PENDING` in #595; no paid trial or automatic production deployment. |
| Superagent, amux, Archon, oh-my-claudecode | "Already Cursor / another runtime" | Ambiguous or narrower developer-tool offerings; product identity and present maintenance/license must be reconciled. | `TRIAGE_PENDING`; resolve upstream identity, run independent developer-workflow tests where appropriate. |

### Why this is a real gap

Several records say only "prior decision deferred" or "already covered", without benchmark receipts. Such a record is historical provenance but **not** technical evidence that the alternative is worse. The earlier `no-second-orchestrator` lock correctly restricted unapproved **production duplication**, but was improperly used as an entry veto. All future replacement, hybrid, or incumbent-retention decisions must be supported by comparable Golden Fixture evidence and scoped legal/security/operational review.

## Canonical backfill from this pass

- Existing records: `deferred-openclaw`, `deferred-crewai`, `deferred-langgraph`, `deferred-ruflo` changed to `RESEARCHED / BENCHMARK_REQUIRED / NONE`; all are **queued**, not installed.
- Existing records: `deferred-autogen` gets evidence-based maintenance rationale with successor cross-reference; `deferred-orca` gets a scope-specific developer-workflow comparison action. Historical source IDs are unchanged.
- New records: `candidate-microsoft-agent-framework`, `candidate-lobehub`, `candidate-bindu` with sources, constraints, review scopes and no production authority.
- Existing candidate: DeerFlow remains `RESEARCHED / BENCHMARK_REQUIRED`; source pin and static boundary verification are documented, **not** a full functional pass.
- Original 68 source rows and existing active 2–3 challenger sets remain unchanged; credible extras are only in `queued_challengers`.

## What remains open (issue #595)

1. Deduplicate all 109 research-link sources against the entire historical source import and related chats/source files, using explicit origin aliases instead of display-name matching; this first pass **does not** certify that reconciliation.
2. Review legacy `embed` choices as well as `skip`/`later` choices: a "pattern embedded" claim is not proof an actual runtime or feature could not outperform our own.
3. Complete current upstream source/license/maintenance review for the remaining ambiguous or proprietary candidates. In particular, avoid installing paid SaaS or inferring license permission from GitHub visibility.
4. Implement tested durable per-link intake from each authorized conversation/source to canonical review + queue with a receipt; no automatic ingestion of all previous chats is assumed.
5. Perform contract-matched Golden Fixtures in isolation. Only a verified winner proceeds to shadow/pilot behind existing cost, identity, security, rollback and effect-authority gates.

**No known external effect, credentials, production writer, canonical business data or existing Office v2 task was changed by this backfill.**
