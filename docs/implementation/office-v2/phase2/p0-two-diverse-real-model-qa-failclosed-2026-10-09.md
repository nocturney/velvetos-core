# Office 2.0 P0 — Different-task local Qwen executor: two honest FAIL_CLOSED results

**Date:** 2026-10-09 | Issue [#612](https://github.com/nocturney/velvetos-core/issues/612) | **Status:** scoped **LAB execution and safety diagnostics PASS**, actual different-task coding **0/2 independent QA successes**. Overall Office P0 **PARTIAL**.

## Why it was built

The original v1 Worker is pinned to a safe `slug.py` fixture; its source and prior receipts must not be rewritten. PR #649 created two *prepared-only*, distinct coding problems on Chris Windows and MacMiniOffice. The new separate `scripts/vf_office_v2_p0_diverse_local_worker.py` implements explicit new, uniquely identifiable **LAB-only** admission, original-candidate re-verification, clean Git clone/branch, pinned Aider/model/budget, fsynced exclusive `RUNNING` journal, OS kernel worker+Aider PID/birth pin, one original local inference invocation, independent fresh-clone visible+hidden QA, immutable continuity checkpoint, and only-if-success receipt. The original prepared candidates and v1 Worker are never changed. It has **no** external-effect writer, fleet lease, scheduler, production permissions, automatic retry or WSL/Windows GUI mutation.

## Real Mac failures — correctly blocked

Two *different* new Task Envelopes were explicitly prepared and admitted on Mac Mini using local Aider 0.86.2, Ollama `127.0.0.1:11556`, `qwen3.5:4b` digest `7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13`. They each ran one real model-backed coding attempt and edited exactly the target file; **neither produced a success receipt** after independent QA rejected the result:

| Genuine attempt | Exact preserved Task Envelope | Independent visible QA | Independent 12 hidden QA | Original disposition |
|---|---|---|---|---|
| Inclusive interval merge | `p0-diverse-run-mac-merge-20261009-a`, Git base `336318a6440bbbc5efd6d56fec66007405722923` | **3/3 pass** | **FAIL** (malformed list-of-list not rejected as required tuple) | `FAIL_CLOSED / INDEPENDENT_QA_FAILED_UNKNOWN_JOURNAL` |
| Canonical ASCII identifier | `p0-diverse-run-mac-canonical-20261009-b`, Git base `c944a8b1ff44040925856517a65d47cc3e5cf834` | **1/3 pass** | **FAIL** (uppercase dropped; punctuation not collapsed) | `FAIL_CLOSED / INDEPENDENT_QA_FAILED_UNKNOWN_JOURNAL` |

The model failures expose real **quality limitations of this small model on different code tasks**, not the expected PR/coding green gate. Every first-attempt journal `receipt.json.running` remains present byte-identical and the original `receipt.json` remains absent; the code edits, original logs, kernel pins and Git branches remain inspectable. There were **no automatic retries, original-task resets or requeues**.

A subsequent **independent read-only diagnostic** `audit-failed-qa` from source commit `949f948ca42ea20e1c9d8f1052b5bcf3ac5ec955` separately confirmed both historical Worker/Aider native OS birth instances absent at audit time (this does **not** exclude escaped/detached descendants), ran fresh-clone QA for the original target bytes, re-checked original journal/kernel/envelope hashes before and after, and wrote **new separate audit files outside the original tasks**. Both audits, and their independent `verify-failed-audit` checks, **PASS**. The original source/task data were not edited.

- Merge audit original raw SHA256 `187da326e9f8931d6a1c08bff575a16f2615262a920e81b9351e45afd7e9d37a`, audit selfhash `4607bc34a9a7ed7668f74fb290bf50786243d2727c7b1f41eaee17d1ba806427`, original journal raw SHA256 `e909db6a1ab48bd5baaafece671c3a6cf825c6f804b7a273b7314e447fddd89d`.
- Canonical-tag audit raw SHA256 `12b61a9afda1148599dde31951519def6edda21072ba0e20d8f7a2792b18a3e8`, selfhash `25c4cd2f22c2790dffef6173c7aae746e1cbf5304a8b75e17bc3677cb408b547`, original journal SHA256 `dbf9fa62bfdf6c9da85586810e30dbc0a6fba4c10e6bd5286419375ba5f8e7a3`.
- Complete historical raw envelope, source and kernel-pin hashes, exact QA verification results and unchanged-original safety limits in `p0-two-diverse-real-model-qa-failclosed-2026-10-09.json`; raw files retained in original Mac `AgentEnvelopeLab/p0-diverse-execution-mac-20261009-{a,b}` and separate `p0-diverse-audit-mac-{merge,tag}-20261009-*` roots. A selfhash is an integrity check, **not an independent digital signature**.

## Windows: one model task admitted, NOT run

Windows Chris has a distinct fresh `canonical_tag.py` execution envelope `p0-diverse-run-win-canonical-20261009-b`, derived from Git base `9463e189c29f48e7a9a8c956a38e6f9cadcf8f8d`, created with a **byte-exact LF clone** after a first *admission-only* CRLF clone was correctly refused and preserved. The new envelope raw SHA256 is `c84d36677b514595773516d4ebc990dd29c94868be0cd1ad9e823eb694df175f`; no RUNNING journal or success receipt exists. Its `qwen3.5:9b` model was **not** launched: RTX 4080 SUPER resource telemetry showed active `mayapy` + `snapmaker-orca` and ~39% GPU usage with ~4.7GiB allocated. This lab did not preempt CAD/GUI work.

## Source/QA and boundaries

New isolated code source version that executed the first Mac model: `a90a42133526a6f4e989ac059ffc16e3a449a67b`; second Mac task and corrected Windows LF admission: `46cb07f5879d25c9a19a79f4c8e7bed713d381de`. New **read-only audit** execution source: `949f948ca42ea20e1c9d8f1052b5bcf3ac5ec955`, raw SHA256 `c08a8413f59a1924c013adc66f523c897f1e477fae810f2c76127699d4262087`. Pure offline admission/failed-audit negatives: **25/25 PASS** on both Windows and Mac. CI must run **only** `selftest`, historical static source/result validation; CI does not launch models, perform native process enumeration, revive failed tasks or automatically clear journals.

**Important remaining P0 blockers:** actual independently QA-green *different* tasks on two physical hosts, two separate protected coding PRs/serial verified postmerges, canonical #604 fleet lease + monotonic fencing, measured 1-vs-2 worker throughput/operator effort, model selection/prompt robustness and safe bounded original UNKNOWN reconciliation. The new general Worker **has not yet demonstrated coding success**, must not be promoted to the Office production code agent or P0 GREEN. Running another attempt requires **a new explicit Task Envelope and safe original failure disposition**, never resetting the original journal. On Mac, detached processes cannot be assumed absent merely because the original worker PID is gone.

No Codex CLI, remote paid API, new model subscription, production credentials/security changes, scheduler/watcher/autostart, customer/Instagram/WhatsApp/printer actions or Windows GPU contention.
