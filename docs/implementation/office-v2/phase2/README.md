# Office v2 Phase 2 — Inventory, Contracts & Benchmark Engineering

Authority: START HERE Phase 2. Baseline: `main@4ee8ca0ef50df169be95d3c4fb8e6a2c5e6e4334` after Phase 1 GREEN and current-main compatibility CI.

Status: **FOUNDATION READY / BENCHMARKS NOT YET RUN / NO WINNERS**.

## Objective

Turn all prior research into a closed, measurable decision system. The source inventory contains 68 prior/live items; the Phase 2 Candidate Registry preserves all 68 and adds four explicit incumbent composition baselines.

## Non-negotiable rules

- Contracts come before executable fixtures.
- Default shortlist: incumbent plus 2–3 serious challengers.
- No item may remain “we talked about it once”; every imported item has a meaningful decision verdict.
- Candidate availability, installability or incumbent failure never grants production authority.
- There is no universal “20% better” or “100% of contract” requirement. The decision gate is fitness, safety, operability and evidence.
- Benchmark fixtures target capability semantics, not product-specific APIs.

## COMPETITOR_NEUTRAL_ADMISSION_V1 — never silently discard credible alternatives

- Every new repo/tool/challenger with plausible contract fit enters the **existing** `candidate-registry-v0.json`, even if it replaces the entire current stack, duplicates an incumbent, or challenges a frozen winner. Preserve provenance and an evidence-based comparison path; the fixed original 68-source import remains intact.
- Compare **incumbent vs complete alternative vs composition/hybrid**, where applicable. Pre-existing investment, "second orchestrator", "we already have it", and shortlist capacity are never standalone rejection reasons.
- Keep the main benchmark shortlist at incumbent plus 2–3 challengers. Additional credible alternatives go into `queued_challengers` for that same lane with a next evaluation gate; queued means **not rejected and not admitted to LAB**. A challenger may replace a shortlist participant only after recorded, fair triage — never via silent omission.
- A credible new challenger or substantive evidence can trigger the existing research-freeze reopen rule. A previous winner keeps its bounded authority until safe, separately approved promotion; discovery/research does not authorize installation in production.
- New, post-policy registry entries must carry `comparison_review` with review scope, evidence state and explicit replacement/hybrid options. The Phase 2 sensor checks the rule and that all queued IDs are resolvable in the registry.

## Agent composition intake — 2026-10-10

Eight distinct upstream agent candidates and the historical Letta memory candidate are now recorded as research/queued challengers, with the ambiguous historical OpenDots identity preserved separately. See [staged research handoff](agent-composition-intake-2026-10-10.md) and [A/B/C machine-readable comparison plan](agent-composition-plan-v0.json). This is **not** LAB admission, production promotion, authorization to spend, use new credentials or start another scheduler. The existing Phase 2 sensor enforces the candidate and queue invariants.

## Owner-submitted 19-repo intake — 2026-10-13

All 19 repositories from the owner-provided GitHub batch, including corrected `anus-dev/ANUS`, are registered for **research-only** comparative routing. Nine full agent-harness challengers are queued in the existing `agent-runtime` overflow; the other ten have named non-P0 phase/owner routes. [Intake and execution map](owner-repo-intake-2026-10-13.md) · [immutable batch receipt](owner-repo-intake-2026-10-13.json). This does **not** preempt #612 P0 proof, admit LAB execution, grant model/host credentials or produce benchmark winners.

## Owner assurance, security and binary tools intake — 2026-10-14

Owner-submitted [iFixAi](https://github.com/ifixai-ai/iFixAi), [PentAGI](https://github.com/vxcontrol/pentagi) and [Ghidra](https://github.com/NationalSecurityAgency/ghidra) now have immutable source pins and **phase-routed, research-only** Candidate Registry entries (128 → 131). Routes: iFixAi → #612 agent-quality/Promptfoo comparison, PentAGI → #595 isolated security-assurance review, and Ghidra → #606 parked P1 shipped-binary/REA comparison. No core P0 shortlist change, installation, scans, model spend, credentials, autostart, tool authority or LAB promotion follows from this intake. The existing Phase 2 sensor enforces all three source identities and routing/false-promotion negative controls. [Routing and admission gates](owner-assurance-binary-tools-intake-2026-10-14.md) · [fixed source receipt](owner-assurance-binary-tools-intake-2026-10-14.json).

## Owner-supplied llamafile local inference — 2026-10-14

[Mozilla AI llamafile](https://github.com/mozilla-ai/llamafile) is now source-pinned in the canonical Candidate Registry as `candidate-mozilla-ai-llamafile` (`RESEARCHED / BENCHMARK_REQUIRED / NOT_RUN`), count 131 → 132; historical imports and all P0 shortlists remain unchanged. This is a Phase 3C **local inference-provider** Ollama comparison routed under #612 after its independently verified local coding-worker baseline, **not** a model-routing gateway contender. No download, LAB admission, background service, added spend or production authority. [Source and benchmark gate](owner-local-inference-llamafile-intake-2026-10-14.md) · [immutable source receipt](owner-local-inference-llamafile-intake-2026-10-14.json).

## Candidate lifecycle

`DISCOVERED → RESEARCHED → CANDIDATE → ADMITTED → LAB → SHADOW → PILOT → PRODUCTION → FALLBACK → RETIRED`.

Exit verdicts at an appropriate stage: `REJECTED_WITH_REASON`, `BENCHMARKED_AND_LOST`, `SUPERSEDED`, `DEFERRED_WITH_REASON`.

Registry: `candidate-registry-v0.json`. Admission policy: `admission-policy-v0.md`. Standard scorecard: `scorecard.schema.json`.

## P0 shortlists

`p0-shortlists-v0.json` defines pre-benchmark sets only. A shortlist is not a winner declaration. Initial lanes are durable execution, model routing, tool-gateway interoperability, memory/context and agent runtime. Every lane has its incumbent and 2–3 serious challengers with `winner: null`.

## Golden Fixtures

Executable fixture contracts live under `golden-fixtures/` and are validated/planned/evaluated by `scripts/vf_office_v2_golden_fixture.py`.

Current core fixtures:
- Instagram request → publish → live verify.
- Customer → quote → production → ready/paid.
- 3D asset → DCC → slice → artifact.
- Agent → approval → external effect → reconciliation.
- Long job → crash → resume.
- Morning Brief → compose → send → verify.

The multi-node worker loss/recovery fixture is intentionally deferred until that lane becomes active, exactly as START HERE allows.

The runner never performs an external mutation directly. An effectful benchmark must use a separately admitted provider adapter and return a generic adapter receipt; the runner evaluates that receipt against capability semantics, evidence requirements and resource capture.

## Research freeze / reopen

Research stops when requirements are covered, fixtures ran, security and operations were scored, rollback was tested or explicitly failed, and a verdict was recorded.

A frozen decision reopens only for material evidence: production regression; new requirement; major license/cost/maintenance change; security finding; OS/hardware feasibility change; candidate end-of-life/abandonment; or a credible new challenger against the same fixture.

## Pattern Adoption

A useful pattern may be adopted without adopting the product. `pattern-adoption-receipt.schema.json` records adopted parts, rejected parts, target contracts and evidence.

## What this foundation does not do

It does not install every candidate, choose a durable engine/model gateway/MCP-A2A gateway, move a business source of truth, or create a new production writer. Bake-offs start only after this foundation is GREEN.
