# XERJ — local code retrieval / memory candidate intake (2026-10-21)

**State:** RESEARCH_ROUTED_NOT_EXECUTED · **Candidate:** candidate-xerj-org-xerj · **Authority:** NONE · **Owner's source:** https://github.com/xerj-org/xerj

## Source evidence (not host/runtime proof)

- Immutable upstream source: [XERJ at 050a12e9ac66f1c3fd279b365d769936e07939da](https://github.com/xerj-org/xerj/tree/050a12e9ac66f1c3fd279b365d769936e07939da) (observed 2026-10-21); [pinned README](https://github.com/xerj-org/xerj/blob/050a12e9ac66f1c3fd279b365d769936e07939da/README.md), [Apache-2.0 license](https://github.com/xerj-org/xerj/blob/050a12e9ac66f1c3fd279b365d769936e07939da/LICENSE), [security model](https://github.com/xerj-org/xerj/blob/050a12e9ac66f1c3fd279b365d769936e07939da/docs/SECURITY_MODEL.md), and [agent-memory recipe](https://github.com/xerj-org/xerj/blob/050a12e9ac66f1c3fd279b365d769936e07939da/docs/recipes/agentic-memory.md).
- Release available during intake: [v1.0.0-rc.97](https://github.com/xerj-org/xerj/releases/tag/v1.0.0-rc.97), published 2026-10-19. RC status, binary digest, host compatibility, performance, safety, and API behavior have **not** been verified on a VelvetOS machine.
- Upstream describes an optional local-first Rust engine: autoindex of code, documents and logs; BM25 / kNN / hybrid retrieval, symbol-aware code search, Elasticsearch-compatible API, MCP tools, and namespaced agent-memory API. These are **upstream capability claims**, not test results here.
- The default embedding path is lexical hashing, **not neural semantic comprehension**. Neural embeddings require a separate opt-in mode/model with its own host/resource and supply-chain checks. Upstream token-savings figures are not VelvetOS benchmark evidence.

## Placement in existing work — no new service or catalogue

- Canonical source of truth: [Office v2 Phase 2 Candidate Registry](candidate-registry-v0.json), ID **candidate-xerj-org-xerj** (RESEARCHED / BENCHMARK_REQUIRED / NOT_RUN / NONE).
- **P0 memory-context:** append XERJ to existing **queued_challengers**, preserving incumbent-current-memory (vfmem canonical authority plus Cognee optional derived retrieval) and the three active challengers. Queue means eligible for fair comparative triage, **not LAB admission or winner promotion**.
- **Supplemental engineering evaluation route:** code-retrieval-agent-context, owned by [#612 local coding/QA baseline](https://github.com/nocturney/velvetos-core/issues/612), with [#595 candidate intake](https://github.com/nocturney/velvetos-core/issues/595) handling source/rights/triage. This is not a seventh P0 winner lane, worker/orchestrator replacement, second skill catalogue, or permission to modify SliceBridge.
- Treat XERJ indexes and its memory namespaces as **replaceable derived search/recall only**. Canonical git/source facts, vfmem verification, effect approvals and the Office durable state machine remain authoritative; a search result or stored memory cannot authorize an effect or override current state.

## Contract-matched A/B/C evaluation proposal — NOT RUN

| Arm | Target | Evidence to collect |
| --- | --- | --- |
| A: incumbent | Existing local code-search/manual reference workflow; vfmem canonical verification, local TF-IDF/Cognee-derived recall | Current retrieval hit quality, time and actual token usage |
| B: XERJ-derived | Pinned XERJ binary in isolated, approved local LAB, indexed over **the same approved immutable corpus** | Source-line fidelity, BM25/semantic/hybrid relevance, MCP query behavior, query/token costs, resources |
| C: composition | Existing authoritative vfmem and coder workflow with optional XERJ-derived search results | Net correctness/latency/cost impact and failure fallback without duplicate authority |

Use approved synthetic or public licence-reviewed code/docs/log corpora only; no production secrets, customer/order information, privileged file trees, or automatic unreviewed OSS cloning. Cover symbol definition and cross-file dependencies, reference coding, multilingual Hebrew/English queries, exact vs semantic retrieval, repeated/incremental indexing, code changed since index, and hostile/prompt-injection content. On the memory lane, test time-dependent contradictory facts, precise canonical citations/hashes, metadata filters, delete/forget visibility, and cross-namespace isolation.

**Record actual measurements**: recall@k / MRR or nDCG on labelled queries, false-positive/unsupported-answer rate, provenance and source freshness, p50/p95 indexing/search latency, cold/warm behavior, peak CPU/RAM/disk, file-change cost, real input/output tokens per solved task, quality at equal tool/model settings, repeatability, crash/restart and rollback. Do not import the upstream 2.7x savings figure as an observed result. Score full derived-layer replacement, component replacement and hybrid independently.

## Admission, security and next gate

1. First complete the independently verified [#612](https://github.com/nocturney/velvetos-core/issues/612) local source-to-PR/QA/recovery baseline and record fair same-task fixture and acceptance criteria. Compare without displacing active P0 shortlist members; triage the overflow using the existing Phase 2 queue.
2. Before any binary download, host run, MCP wiring or model pull: separately approve licence/dependency/release-SHA verification, cost-free host capacity, sandbox and storage boundaries, scoped API-key RBAC and data deletion/restore, no user credential inheritance, outbound restrictions and a tested rollback. **Do not run --insecure on shared LAN/fleet**, or expose port 9200 to a network; use authentication and loopback in any future admitted LAB.
3. External reranking providers can transmit text off-device; leave them disabled unless explicitly reviewed and approved. MCP tools are retrieval tools, **not write authority**; isolate XERJ's indexed content from untrusted model instructions.
4. Require standard Phase 2 scorecard, independent QA and exact-host test receipts before any CANDIDATE/ADMITTED/LAB/winner change. Until then: **research and queue only; no installation, clone, service, credentials, autostart, scheduler, production writer or cost commitment**.

**Reopen trigger:** A fair head-to-head fixture or a material security/quality/operations change. Capability overlap with vfmem/Cognee alone is not a reason to reject XERJ.
