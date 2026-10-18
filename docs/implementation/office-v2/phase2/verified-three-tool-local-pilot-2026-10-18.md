# Office 2.0 — verified three-tool pilot plan (CrewAI / LangGraph / UFO)

**Date:** 2026-10-18  
**State:** PLAN_ONLY / NOT INSTALLED / NOT RUN / NOT ADMITTED TO LAB  
**Authority:** [#595 auditor-verified research, comment 6249011608](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6249011608), [#612 P0 execution priority](https://github.com/nocturney/velvetos-core/issues/612), Phase 2 [admission policy](admission-policy-v0.md), existing [candidate registry](candidate-registry-v0.json) and [Golden Fixtures](golden-fixtures/).  
**Change scope:** This PR creates **documentation only**. It neither installs tools nor introduces a script, service, firewall rule, package lock, runtime permission, model cost, registry promotion or production change.

## 1. Purpose and decision to be made

Test whether two Windows-native/no-Docker Python agent approaches and one **localhost-only** Windows computer-use approach can perform *useful* Office 2.0 work with traceable inputs, bounded autonomy, independent verification and no new recurring expense:

1. **CrewAI**: issue-reading and structured executive triage.
2. **LangGraph**: durable, deterministic work-item handoff with interrupted-run recovery.
3. **Microsoft UFO**: attended, read-only desktop verification of the two resulting local artifacts, **only after a separate security GO**.

This is a small, gated comparison, **not** a decision to replace the existing Office 2.0 worker, Restate, Cursor or Cua, nor a new scheduler. Phase 2 candidate status stays as recorded; research/queued is not LAB admission, and a successful test does not grant PILOT/PRODUCTION authority. No production writer, social channel, printer, order system, GitHub mutation or customer application may be touched.

**Priority gate:** #612's independently verified P0 coding-worker / two-host / QA-recovery evidence takes precedence. Start runtime tests only after a named operator verifies an idle authorized Windows host, a free resource/lease window and no conflict with #604 Fleet or #602 Cua. If these are missing, record PARKED_CAPACITY; do not commandeer a working host.

## 2. Exact first useful tasks and evidence

All inputs are **curated, scrubbed, offline** exports from the same dated GitHub snapshot prepared by a human outside the tools: at least 20 open issues from nocturney/velvetos-core including current #612 and #595 context, with issue number, title, state, labels, updated-at, URL and the minimum relevant issue body. A human review removes secrets, customer data and unrelated private content. Store an input SHA-256 and a hand-written gold/reference sheet. Do not give the tools GitHub auth or a network-enabled issue fetcher. Pin the snapshot for all repeats; do not pretend an offline export is a live status read.

| Tool | First *real* bounded task | Required local output | Negative control / stop |
| --- | --- | --- | --- |
| **CrewAI** | Produce a concise Hebrew summary of 20 actual open issues grouped by blocker/owner/next action, identifying what needs human decision and preserving exact issue numbers and source URLs. The agents only transform the curated snapshot; no browsing, scraping, Python execution or external tools. | docs-style summary Markdown, structured issue-to-claim table, input hash, runtime/step/latency/resource receipt; every claim points to an issue row. | Inject one synthetic contradictory/unsupported item into a *separate* adversarial snapshot: must say UNKNOWN/NEEDS_REVIEW, never invent an owner, deadline or closed status. |
| **LangGraph** | Take five of those actual issues and build a typed next-action queue with a checkpoint after classification; deliberately interrupt before final assembly; resume from the same input/checkpoint and produce a single stable approval-required handoff. This tests #612 continuity semantics *without executing effects*. | next-actions JSON + human-readable handoff, checkpoint/restart/attempt IDs, exactly one output per issue, before/after hashes and replay receipt. | Replay the same checkpoint twice, corrupt a checkpoint and remove an issue: fail closed on tamper/missing evidence, zero duplicate steps, zero automatic approval. |
| **UFO** (conditional) | On a Windows test desktop, use File Explorer **read-only** to inspect the actual CrewAI summary and LangGraph handoff under the sandbox workspace, confirm the three expected output files exist with correct names and visible contents, and record a local GUI QA receipt. No printer/customer/production windows. | Allowed-window trace, comparison against artifact manifest, redacted screenshots stored locally, pass/fail for each expected file and operator observation. | Open an unexpected window, path outside sandbox or a network-dependent server: abort, close child processes and record SECURITY_BLOCKED; never auto-click a confirmation or execute shell/code. |

The UFO task is useful **only if** the security gate in section 3 is demonstrably met. If it cannot be met, a human performs the same GUI inspection as the baseline; report UFO as SECURITY_BLOCKED/NOT_RUN rather than fabricate a score.

**Proposed offline workspace**, all beneath the one approved drive root:

- D:\Velvet\Pilots\OfficeV2-VerifiedTrio\inputs — curated snapshots and gold labels, read-only for runner.
- D:\Velvet\Pilots\OfficeV2-VerifiedTrio\crew\ — CrewAI isolated workspace and outputs.
- D:\Velvet\Pilots\OfficeV2-VerifiedTrio\graph\ — LangGraph state, outputs and replay evidence.
- D:\Velvet\Pilots\OfficeV2-VerifiedTrio\ufo\ — UFO's disposable desktop test inputs and local receipts (only after security approval).
- D:\Velvet\Pilots\OfficeV2-VerifiedTrio\receipts\ — sanitized comparison results and hashes.

These are **proposed future locations**, not directories created by this PR. No write to the source repo or anywhere outside the subtree.

## 3. Security / version admission gates (fail closed)

### 3.1 Candidate version pins — NOT an installed or resolver-verified lock

At the eventual **separate installation/benchmark PR**, resolve an exact, compatible, hash-locked offline dependency set from trusted upstream releases; retain artifact digests, full upstream commit, Python version, dependency/license inventory and vulnerability scan receipt. Reject downgrades, unpinned transitives, an unresolvable combination or a new unremediated reachable high/critical CVE. The rows below are **required candidate pins/floors**, not a declaration that an environment already exists or that all CVEs have published fixes.

| Stack | Candidate exact version(s) for a future lock | Verified fix boundaries and remaining concerns |
| --- | --- | --- |
| **CrewAI** | crewai **1.15.28**; **do not add crewai-tools** for this tool-free task. If independently justified later, candidate crewai-tools **1.15.26** (never below 1.15.1), subject to compatibility and a fresh audit. | CVE-2026-62240 patched in crewai-tools 1.15.1. Research also reports CVE-2026-2275, -2286, -37008 and -37009; several upstream advisories do **not** provide machine-actionable patched-package ranges. A modern CrewAI pin alone does not prove a safe in-process CodeInterpreter or URL/RAG tool. **Prohibit CodeInterpreter, SandboxPython, dynamic code, arbitrary Python tool calls, URL-fetch/scrape/RAG tools and untrusted plugins**, even for localhost inputs. If the no-tools execution path cannot be shown to respect that boundary, mark BLOCKED_SECURITY. |
| **LangGraph** | langgraph **1.2.16**, langgraph-checkpoint **4.1.1**; if used at all, langgraph-sdk **0.4.6**; for persisted SQLite namespace stores, langgraph-checkpoint-sqlite **3.1.1**. No Postgres/server/API in this pilot. | langgraph 1.0.10 fixes CVE-2026-28277; checkpoint 3.0.0 fixes CVE-2025-64439 and 4.1.1 fixes CVE-2026-48775; SDK 0.3.15 fixes CVE-2026-48776 and 0.4.4 fixes CVE-2026-104873; SQLite store 2.0.11 fixes CVE-2025-64104 and 3.1.1 fixes CVE-2026-71433. Later exact pins clear **these known version floors only**, not the full dependency tree; rerun current advisories before a run. |
| **Microsoft UFO** | Source-release candidate **v3.0.10**, full tag commit and source hash to be verified and frozen before any test. | #595 identifies **18 repository advisories** (including CVE-2026-73296, -105793, -62316, -105791, -46544, -46414), with some official advisories displaying **no patched version**. **NO RUNTIME GO based merely on v3.0.10.** Independently map every relevant advisory to the exact frozen source and *disabled* entry points, prove no reachable affected interface, or obtain explicit owner/security risk decision under a separately reviewed change. Until then UFO remains SECURITY_BLOCKED. |

Primary advisory references:
- CrewAI: [CVE-2026-2275](https://github.com/advisories/GHSA-5w94-5wxp-rc42), [CVE-2026-2286](https://github.com/advisories/GHSA-pgf5-gw7r-wxg7), [CVE-2026-37008](https://github.com/advisories/GHSA-2q68-3cp7-72v9), [crewai-tools CVE-2026-62240](https://github.com/advisories/GHSA-mr4r-hcgx-8p4h).
- LangGraph: [CVE-2026-28277](https://github.com/advisories/GHSA-g48c-2wqr-h844), [CVE-2026-48775](https://github.com/advisories/GHSA-fjqc-hq36-qh5p), [SDK CVE-2026-104873](https://github.com/langchain-ai/langgraph/security/advisories/GHSA-fvww-7h3r-vfhp), [SQLite CVE-2026-71433](https://github.com/advisories/GHSA-47pj-3jcm-6whg).
- UFO: [repository security advisories](https://github.com/microsoft/UFO/security/advisories), [CVE-2026-73296 / Mobile MCP](https://github.com/microsoft/UFO/security/advisories/GHSA-24fq-m9rr-g3mm), [CVE-2026-46544 / session replay](https://github.com/microsoft/UFO/security/advisories/GHSA-29gc-vqjp-7fqf), [CVE-2026-105793 / press_key](https://github.com/microsoft/UFO/security/advisories/GHSA-5cjx-4375-4877). The verified #595 audit is the 2026-10-18 research baseline, **not** a timeless vulnerability clearance.

### 3.2 Identity, disk, network and tool surface

1. **Windows sandbox:** separate least-privileged local test identity, no administrator/SYSTEM, no production sessions, no shared browser profile, no mounted secret store, no write/push token. Restrict file ACLs and process/sandbox access to the single D:\Velvet\Pilots\OfficeV2-VerifiedTrio subtree; merely prompting a model to stay inside D:\Velvet is insufficient. Deny traversal via junctions/symlinks/reparse points and out-of-root child processes. If an enforceable boundary cannot be proven, **do not execute**.
2. **No secrets:** scrub environment, process arguments, cached profiles, issue exports, logs and screenshots. No .env, API keys, GitHub PAT, cookies, production OpenBao/ZITADEL/OPA credentials, customer/order details, Instagram/WhatsApp sessions or printer API keys. Set user TEMP/TMP/cache/output to the sandbox or block unsafe writes; validate the real filesystem boundary with a negative test. Use already approved, offline local inference only if available; no paid API calls, model downloads, telemetry or cloud fallback.
3. **No exposed port:** prefer zero listening sockets for CrewAI/LangGraph. UFO is **localhost-only** even in an approved future run: prohibit Galaxy, Mobile MCP, remote MCP, ADB bridges, cross-device control and WebSocket/HTTP servers outright unless separately scoped and independently reviewed. If a local component is strictly unavoidable, bind only 127.0.0.1 (or explicitly audited ::1), never 0.0.0.0/:: or a LAN address; enforce Windows Firewall inbound/outbound denies and verify effective listeners + remote-host refusal **before, during and after**. Loopback binding alone is not an authorization boundary (DNS rebinding/origin checks still matter). Any unknown listener/outbound connection is STOP.
4. **Effect denylist:** no shell, dynamic code execution, file deletion/move outside disposable output, git push/write, network fetch, privileged MCP, Docker host socket, task scheduler, autorun, clipboard exfiltration, production UI automation, customer channels or printer/CAD commands. Prompts and retrieved issue bodies are untrusted data, never policy instructions.
5. **Revalidation:** capture exact tag/lock/checksum/CVE scan, capacity lease, filesystem ACL, process tree, firewall rules and port scan in a sanitized preflight receipt. Changes in CVEs, versions, host ownership or source content invalidate admission.

## 4. Measurements and acceptance

Run the same pinned input through **at least 5 repeats** per admitted tool, including a clean cold attempt. Record attempt IDs, exact model digest/provider if a local model is used, startup/runtime p50/p95, CPU/RAM peak, tokens if exposed, incremental spend, human supervision minutes, timeout/failure reason, generated hashes and all unauthorized-effect attempts. Human baseline uses the same snapshot and review rubric. Do not compare disparate task types as a single agent-runtime winner: CrewAI vs LangGraph can share the issue-fidelity rubric; UFO is a **separate GUI verification** lane.

| Gate | Objective acceptance threshold |
| --- | --- |
| Hard safety (every run) | **0** non-loopback listeners, unauthorized egress, out-of-scope file access, secret exposures, production writes, paid calls and unattended GUI actions; negative controls **must deny**. Any breach = FAIL and immediate stop. |
| CrewAI issue quality | At least **20/20** input issue IDs trace to real snapshot rows, **0** invented issue IDs/statuses/deadlines, at least **90%** of a preselected 20-fact human-scored sample supported by correct row citations; unsupported/conflicting facts explicitly UNKNOWN. |
| LangGraph continuation | **5/5** selected issue handoffs contain valid IDs and human-approval marker; **5/5** interrupted/replayed attempts recover deterministically from verified checkpoints, **0** duplicate outputs or hidden approvals; tamper negative must fail. |
| UFO GUI (only if admitted) | At least **10** bounded read-only GUI actions on the sandbox fixture, **100%** expected artifact checks correct vs manifest, **0** out-of-scope windows, clicks or filesystem paths; unexpected window produces observable safe abort. |
| Performance/operability | 5-run p50/p95 + peak RAM/CPU + human-minutes and per-run statuses recorded, no P0 host lease conflict. The operator sets an enforceable host-specific resource ceiling **before** admission; hit ceiling or 10-minute per-attempt timeout -> stop. No unsupported speedup claim without matched human/worker baseline. |
| Evidence completeness | Every result has source SHA-256, input/output hashes, exact versions, run timestamps, signed-off human review, status in PASS / FAIL / BLOCKED_SECURITY / PARKED_CAPACITY / NOT_RUN. Missing fields mean **NOT VERIFIED**, never PASS. |

Passing a static document or CI does **not** pass the runtime pilot. Before a later comparative decision, benchmark against the existing Office 2.0 incumbent on the same relevant Golden Fixture and log a normalized scorecard in the existing Phase 2 evidence lane; follow independent QA, separate admission and owner approval.

## 5. Sequence, rollback and ownership

**Sequence:** (0) leave P0 #612 running; approve an idle resource slot; (1) review versions/advisories/rights and freeze a hash-locked supply chain in a *different, separately approved PR*; (2) preflight sandbox and negative access/network controls; (3) curate the same dated 20-issue snapshot and human baseline; (4) CrewAI read-only summary; (5) LangGraph checkpoint/replay; (6) UFO security review and conditional attended GUI run, or SECURITY_BLOCKED; (7) independent evidence review, baseline comparison and GO / REWORK / REJECT verdict. **Nothing in this plan triggers these steps automatically.**

**Rollback trigger:** any open/non-loopback socket, unexpected process or window, attempted external write/egress, secret/path-boundary leak, failed checkpoint integrity, resource conflict, newly relevant unpatched advisory or operator veto. Stop only the pilot child process tree; revoke only the pilot-specific identity/network exceptions; verify **zero** pilot listeners and no remaining child processes; quarantine sanitized receipts; remove only disposable contents of the approved test subtree after preserving hashes, and recheck original source hashes. The prepilot production/Office/P0 state was never changed, so **no production cutover or restore should be required**. If host state differs from baseline, mark RESTORE_REQUIRED, do not self-declare recovery. Do not delete other D:\Velvet material, reset existing worktrees or touch Fleet/SYSTEM.

| Role | Responsibility (proposed; runtime not authorized by this doc) |
| --- | --- |
| **Christian / owner** | Decide resource window, acceptable risk and GO/NO-GO; explicitly authorize or reject any UFO unresolved-advisory exception; approve later runtime scope. |
| **ChatGPT / document author** | Maintain this Phase 2 plan, security/evidence checklist, README pointer and documentation PR; **does not independently QA or merge its own PR**. |
| **Cursor / implementation operator** | In a *future separately authorized* isolated branch/host slot, prepare scrubbed issue fixture and CrewAI read-only run/receipts; never interfere with active P0 workers. |
| **Claude / comparison owner** | Independently specify/review LangGraph checkpoint/replay experiment and comparable rubric; no second scheduler or shared mutable worktree. |
| **Grok / independent QA** | Check source/CVE/version assertions, exact PR head, documentation scope, local + hosted checks and future execution receipts independently. Publish PASS/FAIL with evidence; merge decision remains outside the PR author's control. |
| **Attended Windows operator** | Only after owner + independent security approval, run/observe UFO under restricted identity, guard allowed UI windows and stop on boundary breach. No unattended deployment. |

**Exit decision:** only write down a winner after safety, fidelity, cost and incumbent-comparison evidence exist. Until then **PLAN_ONLY**; no registry promotion, no recurring automation, no tool installation and no business external effect.
