# Office v2 Phase 2 — Inventory, Contracts & Benchmark Engineering

Authority: START HERE Phase 2. Baseline: `main@4ee8ca0ef50df169be95d3c4fb8e6a2c5e6e4334` after Phase 1 GREEN and current-main compatibility CI.

Status: **FOUNDATION READY / PHASE 3A RESTATE WINNER RECORDED / 1 OF 6 P0 LANE WINNERS / FIVE LANES STILL OPEN / NO AUTOMATIC PRODUCTION AUTHORITY**.

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

## Owner browser automation repos - 2026-10-16

Twenty unique owner-provided browser/crawler/agent repositories enter the existing Candidate Registry as **research-only** (132 to 152), with five P0 queued challengers, thirteen non-P0 phase routes, and two source references. [Per-tool workflow routes and synthetic comparison gates](browser-automation-intake-2026-10-16.md) and [source-integrity receipt](browser-automation-intake-2026-10-16.json). No installation, LAB acceptance, new production authority, credentials, autonomous publishing or provider usage follows from registration.

## Candidate lifecycle

`DISCOVERED → RESEARCHED → CANDIDATE → ADMITTED → LAB → SHADOW → PILOT → PRODUCTION → FALLBACK → RETIRED`.

Exit verdicts at an appropriate stage: `REJECTED_WITH_REASON`, `BENCHMARKED_AND_LOST`, `SUPERSEDED`, `DEFERRED_WITH_REASON`.

Registry: `candidate-registry-v0.json`. Admission policy: `admission-policy-v0.md`. Standard scorecard: `scorecard.schema.json`.

## P0 shortlists

`p0-shortlists-v0.json` now tracks six P0 lanes with their incumbent and 2–3 challengers. **One of six** has a recorded benchmark verdict: `durable-execution` selected **Restate** (`candidate-restate`) as winner, with **Temporal** (`candidate-temporal`) as fallback, frozen under Phase 3A evidence. The other five lanes — `model-routing`, `tool-gateway-interoperability`, `memory-context`, `agent-runtime`, and `worker-fleet-placement` — still have `winner: null`, pending their own fixtures and scorecards. Shortlisting never grants LAB, PILOT or production authority. Phase 3B ZITADEL/OPA/OpenBao composition is a separate bounded security track, not another P0 shortlist winner.

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

## Real-world field outcomes (outside formal scorecards)

[Printed Talm lifestyle kettlebell: smooth SVG flush inlay on protected source mesh, 2026-10-24](field-evidence-2026-10-24-talm-kettlebell-smooth-vector-inlay.md) records an **owner-confirmed successful physical trial** after Blender Exact Boolean + OrcaSlicer dry-run, and a negative result for the previous global voxel CSG approach **for that task**. It is a scoped positive routing precedent for the incumbent Blender/Creative Craft fabrication chain, not a comparative Golden Fixture score, universal tool ranking, new registry, automatic candidate promotion or production permission. Preserve the original 68 registry imports and score only same-fixture comparisons.


## Research freeze / reopen

Research stops when requirements are covered, fixtures ran, security and operations were scored, rollback was tested or explicitly failed, and a verdict was recorded.

A frozen decision reopens only for material evidence: production regression; new requirement; major license/cost/maintenance change; security finding; OS/hardware feasibility change; candidate end-of-life/abandonment; or a credible new challenger against the same fixture.

## Pattern Adoption

A useful pattern may be adopted without adopting the product. `pattern-adoption-receipt.schema.json` records adopted parts, rejected parts, target contracts and evidence.

## What this foundation does not do

It does not install every candidate, choose a durable engine/model gateway/MCP-A2A gateway, move a business source of truth, or create a new production writer. Bake-offs start only after this foundation is GREEN.

## #595 triage batches 1, 2 and 4 — corrected rows (2026-10-18)

Cursor's KEEP/REJECT tables for the 46 software candidates in batches 1, 2 and 4 now live in [the corrected report](candidate-triage-batches-124-2026-10-18.md) and [the JSON inventory](candidate-triage-batches-124-2026-10-18.json). Claude's CLQ-8 verdict stands: batch 1 FAIL on the row 14 evidence text, batches 2 and 4 PASS. Four rows were corrected after a live GitHub REST check, and no KEEP or REJECT changed: row 14 `danielhanchen/llama.cpp` stays REJECT as a fork with no own commits (ahead 0, behind 2129); row 13 `dagger/container-use` stays KEEP, with the 2026-09-21 push identified as Dependabot while `main` last moved on 2026-08-12; row 20 `emilk/egui` stays KEEP under MIT OR Apache-2.0; row 24 `gastownhall/gastown` stays KEEP, and its API `pushed_at` of 2026-10-18 is a closed Dependabot push, not a `main` commit. This report does not edit the candidate registry and does not admit, install, or promote anything.

## Perplexity 10-tool scan — auditor verification (2026-10-18)

The auditor's read-only check of the 10-tool Perplexity scan is recorded in [the verification report](perplexity-10-tool-verification-2026-10-18.md) and [the JSON inventory](perplexity-10-tool-verification-2026-10-18.json). Source: [#595 comment 6249011608](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6249011608). License and `archived` were re-read from the GitHub API at 2026-10-18T11:16:07Z: all ten `archived` flags are false. AutoGen's README says the project is archived and no longer maintained and points to Microsoft Agent Framework. UFO has 18 published advisories and no patched version listed (API 2026-10-18T11:18:22Z). n8n v3 is Docker-only. The verified top 3 is CrewAI, LangGraph, and UFO localhost-only. Policy #632 does not block a sale by license. This report does not edit the candidate registry and does not admit, install, or promote anything.

## Durable repo-link intake (#595)

`scripts/vf_office_v2_link_intake.py <github-url>` records an incoming GitHub repo link in the one canonical `candidate-registry-v0.json`. It works offline. It normalizes case, `.git`, trailing slashes and sub-paths, and deduplicates against the `evidence_refs` of existing candidates. A new repo is appended as `DISCOVERED` / `BENCHMARK_REQUIRED` with a `NEEDS_SOURCE_REVIEW` `evaluation_route`. It is not promoted and gets no authority. Every outcome writes a receipt under `link-intake-receipts/`: `REGISTERED`, `DUPLICATE`, `INVALID_INPUT` or `NEEDS_SYNC`. `scripts/vf_office_v2_link_intake_selftest.py` (run by `scripts/check-office-v2-phase2.py`) proves that a link can't be lost, that duplicates add nothing and that historical rows don't change. COMPETITOR_NEUTRAL_ADMISSION_V1 applies.

**Batch entrypoint (AC5/AC6):** `python3 scripts/vf_office_v2_link_intake_batch.py <url> [<url> ...]` or `--file links.txt` (newline list) / `--file links.json` (URL strings or `{url, alias}` objects). `--alias <candidate-id-or-name>` is valid for one URL. The default is offline; only explicit `--metadata` performs bounded unauthenticated GitHub API reads. Owner/repo and candidate ID/name aliases deduplicate against the same registry. Every input produces a JSON triage record, file-backed receipt and next action. A newly registered offline link has `source_sync=NEEDS_SYNC` until upstream access is verified; an inaccessible/private source with opt-in metadata yields `status=NEEDS_SYNC` and a durable receipt instead of a fabricated public/reachable claim. Metadata never grants install or promotion authority. The Phase 2 check-all sensor runs `vf_office_v2_link_intake_batch_selftest.py`, including missing-result, forged-registration and removed-candidate mutations. The original 68 rows are untouched; there are no scheduled workflows.
