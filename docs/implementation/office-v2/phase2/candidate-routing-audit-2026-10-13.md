# Office v2 — Candidate routing gap audit (2026-10-13)

**Scope:** review of **pre-Kitten** `main` Phase 2 registry (108 candidates, source import 68 fixed) and six existing `p0-shortlists-v0.json` lanes; do not treat this file as a new runtime registry, scheduler, source of truth or production approval. KittenTTS intake and plan are separately appended at [speech comparison](speech-tts-comparison-2026-10-13.md).

**Owner:** existing [Office candidate intake #595](https://github.com/nocturney/velvetos-core/issues/595); P0 coding and QA [#612](https://github.com/nocturney/velvetos-core/issues/612); fleet [#604](https://github.com/nocturney/velvetos-core/issues/604). All canonical stage/authority decisions remain in existing master registry, appropriate issue and Office Master v3.

## Finding — do not equate "outside the P0 shortlist" with "forgotten"

- **108** records at the pre-change snapshot. **46** appear as incumbent, active challenger or queued challenger in the six core P0 lanes. **62** do not appear in those P0 lanes.
- These 62 include production incumbents, Phase 1/3B LAB-validated substrates, deferred/reserve options and research for later phases. **They are not 62 missed tests.**
- A narrower routing-metadata gap: **24** records are `RESEARCHED / BENCHMARK_REQUIRED` with `shortlist_lanes: []`; **one additional** `CANDIDATE / BENCHMARK_REQUIRED` record (`partial-cognee`) also has no named lane. These **25** records warrant explicit routing/triage receipts. A further `candidate-nvidia-openshell` has named `agent-sandbox-isolation` lane outside core P0; it is scoped after the P0 worker proof in #612, not orphaned.
- Several of the 25 already have a broad phase directive in #612 / Office Master v3: notably skill-evaluation tools, memory candidates and business systems. The deficit is **per-candidate linked owner/next-gate evidence**, not proof that every evaluation was forgotten.
- This audit provides provisional phase mapping **without promoting**, installing or filling the active 2–3 benchmark slots. Reconcile and persist any necessary registry `shortlist_lanes` or `queued_challengers` changes in a subsequent **small protected PR** only after alias, fit and actual lane-owner validation.

## Routing actions — missing named comparison lane (25)

| Canonical candidates | Count | Existing owner / phase | Next actionable gate | Why not in a current P0 core shortlist |
| --- | ---: | --- | --- | --- |
| `candidate-skillopt`, `candidate-nvidia-skillevaluator`, `candidate-agent-skill-eval` | 3 | #612 agent quality/Skills benchmarking after real coding-worker baseline | Compare controlled skill/prompt improvement vs existing Promptfoo and postcondition QA; avoid Codex quota/new paid inference; store scorecard | **Already mentioned explicitly in #612**, but skill quality is not one of the six core engine shortlists |
| `candidate-memu`, `candidate-mem0`, `candidate-deja-vu`, `partial-cognee` | 4 | #612 memory/continuity + Office Phase 3 memory-context | Verify exact upstream role/license; run temporal contradiction, provenance, deletion and fresh-vs-stale recall fixture after Project State checkpoints work | Baseline memory shortlist is full; derived recall cannot replace Project State or the durable queue |
| `candidate-opendots`, `candidate-useagent`, `candidate-pi-desktop`, `candidate-laya`, `candidate-reef`, `candidate-icepick` | 6 | #595 source/provenance triage; #612 agent-runtime Phase 3D as eligible | Pin real upstream identity, contract fit, resource/rights; route credible runtime/UX challengers to existing `agent-runtime` queue by protected PR, otherwise record evidence-backed distinct disposition | Historical import lacks enough product-specific evidence to select a bounded LAB safely; especially `candidate-opendots` has ambiguous historical source identity |
| `candidate-a2a`, `candidate-agent-reach` | 2 | Office Phase 3 tool/MCP/A2A interoperability; #595 triage | Distinguish protocol/pattern vs runnable provider; map typed-contract interoperability fixture and gateway shortlist/queue if a true contender | A2A may be a protocol rather than a deployable challenger; contract-level role must be established first |
| `candidate-erpnext`, `candidate-twenty`, `candidate-akaunting`, `candidate-spoolman`, `candidate-carbon`, `candidate-inventree` | 6 | Office Phase 5 business/manufacturing authority selection | Route to order → quoting → inventory → production → payment fixture; compare with working incumbent workflows, migration/export/rollback and no second business source of truth | Domain authority bake-offs are deliberately later than surviving Office P0, but the specific vendor-level gate needs stronger linkage |
| `candidate-paperless`, `candidate-manyfold`, `candidate-kitsu`, `candidate-ayon` | 4 | Office Phase 5 document authority / Phase 6 asset, 3D and creative pipeline | Separate document/asset/production-tracking contracts; read-only evidence first, then isolated export and integration fit tests | Not P0 runtime competitors; no common fit/decision gate existed at candidate-record granularity |

**Totals: 3 + 4 + 6 + 2 + 6 + 4 = 25 (24 `RESEARCHED` + 1 `CANDIDATE`).** This is a route triage inventory, not an instruction to install/test all candidates immediately.

## Named but not active — explanations for other likely perceived omissions

- **KittenTTS:** previous in-chat mention only; it was *not* in the 108-row canonical registry and had no speech evaluation slot. Fixed in the proposed registry append plus the dedicated [speech comparison](speech-tts-comparison-2026-10-13.md), owner #595 Phase 2 now and Phase 4/6 controlled benchmark once independent capacity exists.
- **FreeVideo / Compositor:** both already have evidence-backed late Phase 6/8 creative scheduling and clear resource/rights/compatibility gates in their registry records and #595/#627. Delayed **LAB**, not dropped **intake**.
- **Agent-runtime challengers:** many are in `agent-runtime.queued_challengers` even when not in the 2–3 benchmark slots. Queued is **not rejected**; it preserves fair promotion evaluation without contention.
- **OpenShell:** `agent-sandbox-isolation` is an acknowledged non-P0 lane after #612 coding-worker proof, with real integration/sandbox fixture needed.
- **DBOS:** credible reserve after the earlier durable-execution comparison; the winner is already recorded as Restate under the corrected Phase 3A bake-off. Reopen only on contract-relevant evidence; preserve prior receipts.
- **AutoGen:** documented upstream maintenance-mode successor Microsoft Agent Framework is registered separately. Historical AutoGen remains a reference, not an auto-install target.
- **OpenPost:** recorded deferred authority state cannot be treated as a new tool test; reconcile actual publishing ownership before any production activation.
- **Already installed/imported tools:** `IMPORT_EXISTING` and `LAB_VALIDATED` do not mean "unassigned competitor"; fresh runtime health is a separate question and should never be inferred from historical registry status.

## Corrective delivery protocol (use only existing services)

1. **Now:** add KittenTTS with unique candidate ID + dated evidence and `speech-tts-local` evaluation lane. Keep VoiceStudio current health `UNKNOWN` until fresh doctor, while retaining the historical QA PASS.
2. **Now, in parallel:** #595 intake owner reviews these 25 routing lines, resolves actual source aliases and the existing plan owner. Record `ROUTED`, `NEEDS_RESEARCH`, or `BLOCKED` and one material next trigger per record. Do **not** silently convert a research record to LAB or discard an incumbent competitor.
3. **First noncontending eligible work:** #612 runs its existing coding/quality fixtures and Phase 3 memory tests as resources permit; other phase owners prepare source/rights/fixture matrices read-only. No duplicate recurring automation or overloaded GPU.
4. **Protected follow-up PR:** update the canonical registry `shortlist_lanes` / existing P0 `queued_challengers` only for genuinely comparable options and lock the new routing integrity sensor into `scripts/check-office-v2-phase2.py`, rather than creating a second catalog.
5. **Acceptance:** future user-supplied GitHub link (e.g., KittenTTS) produces a deduplicated canonical candidate/known incumbent lookup and visible `needs_sync` when unavailable; independent fresh-chat regression must pass before declaring durable intake solved.

**Evidence/currentness:** snapshot based on `main` read on 2026-10-13, before this scoped branch; exact live host health, unreconciled original research links and future scheduled execution are **not** verified here. Source planning documents: [Office Master v3](https://docs.google.com/document/d/15NMtyaUDjxiACPKEY_T5rW7IUFwtD2qU88yhbKQhEkw/edit), [P0 #612](https://github.com/nocturney/velvetos-core/issues/612), [Intake #595](https://github.com/nocturney/velvetos-core/issues/595).
