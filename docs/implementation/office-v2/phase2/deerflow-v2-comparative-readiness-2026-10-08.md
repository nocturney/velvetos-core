# DeerFlow 2.x ↔ VelvetOS Office v2 — source-pinned comparative readiness (2026-10-08)

**Status:** `RESEARCH_SOURCE_VERIFIED / ISOLATED_RUNTIME_NOT_STARTED / BENCHMARK_NOT_RUN / NO_PRODUCTION_AUTHORITY`  
**Canonical candidate:** `candidate-deerflow` — `RESEARCHED`, `BENCHMARK_REQUIRED`, queued in `agent-runtime` and `memory-context`.  
**Scope:** complete agent-runtime replacement, subsystem replacement, and hybrid composition.  
**Upstream:** [bytedance/deer-flow](https://github.com/bytedance/deer-flow) at pinned commit [`be34cc46d00b373407c22651dc20fdded4863af9`](https://github.com/bytedance/deer-flow/tree/be34cc46d00b373407c22651dc20fdded4863af9) (2026-10-08). Do **not** compare changing upstream `main` without a new pin and evidence.  
**Existing Office source:** `docs/implementation/office-v2/phase2/README.md`, `p0-shortlists-v0.json`, `golden-fixtures/`; persistent execution selection at `docs/implementation/office-v2/phase3/durable-execution-verdict-v0.json`.

## What was actually checked

| Item | Observed result |
| --- | --- |
| Public code source, commit, clean checkout | `PASS`: shallow checkout to `D:/Velvet/Repos/upstream/deer-flow`, commit `be34cc46...`, no local code changes observed |
| Root repository license | `MIT` with attribution; third-party licenses/model and SaaS terms are distinct |
| Current branch packaging | `backend/pyproject.toml` describes **2.2.0-dev**, Python `>=3.12`; pin exact commit, do not treat HEAD as a verified stable production release |
| Agent framework separability | Harness in `backend/packages/harness/deerflow/`; Gateway/App in `backend/app/`; thin extension API package. `deerflow.client.DeerFlowClient` available to run the same lifecycle programmatically |
| Harness → App dependency boundary | **PASS**: ran upstream `backend/tests/test_harness_boundary.py::test_harness_does_not_import_app` directly with local Python 3.12; confirms no prohibited `app.*` import in harness Python AST. Does **not** prove the runtime works |
| Local Python availability | Python **3.12 present** on Windows host; required `pytest` not installed in that interpreter |
| Containerized isolated LAB readiness via Desktop Commander LocalSystem | **BLOCKED**: Docker CLI unavailable to that remote session; direct WSL fails `WSL_E_LOCAL_SYSTEM_NOT_SUPPORTED`. This is an executor-access obstacle, not evidence DeerFlow itself fails |
| macOS host independent check | Mac Mini arm64 available; CLI `uv` present, default `python3` 3.9.6; Docker CLI not on PATH. No platform deployment assumed |
| Model credentials / actual LLM requests | **NOT RUN**; no third-party paid model keys inspected or supplied, no API costs authorized |
| Docker/compose health, sandbox escape, MCP, scheduler, persistent run semantics | **NOT RUN**. No network port was opened and no DeerFlow worker/service was started |

Sources: upstream `docs/ARCHITECTURE.md`, `backend/docs/ARCHITECTURE.md`, `backend/pyproject.toml`, `Install.md`, `README.md`, `LICENSE`, and upstream `backend/tests/test_harness_boundary.py`.

## Why this could supersede our current stack

DeerFlow 2.x offers a comparatively integrated LangGraph agent harness rather than isolated patterns: `make_lead_agent()`, subagents, thread-scoped sandbox/workspace, skill discovery, MCP tools, memory/context middleware, scheduler/Gateway, `RunManager`, and a programmatic client. These are concrete competing implementations of multiple Office v2 requirements. The distinction from the old 2026-08-31 "patterns only" review matters because that review did **not** benchmark the current 2.x runtime.

Important caution: its scheduler and long-running MCP task leasing are not automatically proof that any arbitrary lead-agent workflow survives a crash with **the same semantics** as Restate. The durable-execution contract already found a failing incumbent. DeerFlow must pass that exact contract (or run on top of the accepted durable spine) rather than win by feature count.

## Fair alternatives to benchmark

| Architecture | How to test | Avoid assuming |
| --- | --- | --- |
| **A. VelvetOS incumbent** | Existing `live-grokbot`/harness/approved policy adapters under identical synthetic provider inputs. When durable behavior is needed, record the existing Restate selection distinctly. | That existing code deserves preferential scoring because it is ours |
| **B. DeerFlow-first** | Pin upstream, deploy in isolated LAB, connect only fake/MCP test providers and dummy workspace, evaluate complete agent worker lifecycle and operator overhead. | That a UI demo proves human approvals, tenant isolation or exact-once external effects |
| **C. Hybrid** | VelvetOS canonical policy/tenant/effect gates + DeerFlow harness as a swappable agent worker + Restate for durable execution where contract requires it. Test explicit lifecycle and cancellation/receipt adapter. | That layering reduces complexity without measurable evidence |
| **D. Bare LangGraph / Microsoft Agent Framework alternatives** | Run the same contract using their own reference adapters, so DeerFlow is fairly compared with its underlying framework and other actual competitors. | That including only DeerFlow makes the shortlist objectively complete |

**Do not preselect B or C.** A possible loser is still a valid outcome if all same-contract tests pass and comparative operability/cost favors the incumbent.

## Required vendor-neutral Golden Fixtures — LAB only

1. `agent-approval-effect-reconciliation`: fake operator approval, verified policy denial, idempotent synthetic effect, readback receipt; malicious tool and missing authority inputs must be rejected.
2. `long-job-crash-resume` + the existing Phase 3A 20-step destructive contract: provider failure, restart/recovery, same-run resume, cancellation, retry, replay, move, exactly-once **simulated** external effect and truthful evidence. Measure whether DeerFlow alone or Restate+DeerFlow can meet it.
3. `morning-brief-compose-send-verify`: synthetic Gmail/Calendar/Drive responses and a fake send adapter. No real Gmail send.
4. `instagram-request-publish-live-verify`: existing policy-native approvals through a **synthetic** `vfigos` adapter; never invoke the live Instagram writer.
5. `3d-asset-dcc-slice-artifact`: synthetic CAD/slicer artifact and status receipts; no real printer operations.
6. Memory/context: provenance correctness, deletion, freshness, isolation across two fake tenants/threads, compaction recovery after restart, tool denial after privilege changes.
7. Operations/security: cold start, health, RAM/CPU/storage/network footprint, dependency/license and port exposure, non-loopback denial, sandbox path traversal, untrusted prompt/tool escalation, log redaction, backup/restore/teardown.

The scorecard must capture `fitness`, `safety`, `operability`, `evidence_quality`, wall time, resources, recurring/API cost (unknown stays `null`), operator load, rollback, source pin, reproducibility and written verdict. **No invented scores or `PASS` before an actual run.**

## Admission and implementation plan

1. **Read-only source pin (DONE):** isolated checkout, exact commit identity, MIT source review and harness import-boundary test.
2. **CANDIDATE review (NOT YET COMPLETE):** vendor security/trust audit, secrets model, role/tenant separation, model licensing and dependency chain; decide legal feasibility and LLM/provider cost with `NO_NEW_RECURRING_COST`.
3. **ADMITTED → LAB (NOT YET):** choose an accessible operator-owned isolated executor (not the Desktop Commander LocalSystem WSL path); digest-pin image/deps, synthetic creds, no full Windows drive mounts, loopback ingress, health, teardown, no unattended user-channel credentials.
4. **Reproducible fixture bake-off (NOT YET):** compare A/B/C/D above with identical contracts, minimize false "feature exists" scoring, retain negative tests and cost. Keep existing production Office/Instagram workflows unaffected.
5. **Decision gate:** if DeerFlow wins, choose full replacement, module replacement or hybrid. Only after verified rollback and SHADOW/PILOT gates can any runtime/effect authority change. A CI-green research PR is **not** a production promotion.

**Current engineering recommendation:** advance DeerFlow through full candidate admission, not only pattern reuse; prioritize agent-runtime and durable execution recovery fixtures. Do not interrupt the already selected Restate execution spine before a reproducible comparative result.
