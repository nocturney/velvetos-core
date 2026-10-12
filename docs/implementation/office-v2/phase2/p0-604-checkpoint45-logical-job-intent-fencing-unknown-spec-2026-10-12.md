# Office 2.0 / #604 — Checkpoint 45: logical job, effect intent, worker identity and UNKNOWN gate

**Date:** 2026-10-12 (Asia/Jerusalem)  
**Authority:** DESIGN / READ-ONLY SPECIFICATION; NOT ADMITTED; NO PRODUCTION CHANGE  
**Source baseline:** `nocturney/velvetos-core` main `1fb06173a6af7ad7242a751f5853a4133170b2ce` at verification.  
**Owners:** #604 owns canonical fleet placement, lease/provider and effect authorization; #612 consumes that contract for the coding-agent workflow. Dagu is only a scheduler/executor candidate.  
**Scope of this checkpoint:** specify the **first unproven integration gate** without repeating accepted 2026-10-09/10 local SQLite, Git and etcd experiments or Dagu B1–G1.

## 1. Evidence inherited — NOT to be repeated as a new milestone

- [PR #704](https://github.com/nocturney/velvetos-core/pull/704) is merged on the above main SHA. Six physical hosts were read and the Dagu 2.18.2 portable binaries were verified. This does **not** establish a secure distributed Worker service or simultaneous CPU throughput.
- [Checkpoint 44 / #604 evidence](https://github.com/nocturney/velvetos-core/issues/604#issuecomment-6131365111): Dagu C1 returned `aborted` while child-step termination logged `operation not permitted`; no durable late-effect sentinel; classify **CANCEL_UNVERIFIED**, not safe cancellation. D1/E1 distributed CLI retries failed; Dagu `run_id` is **not** a durable logical job ID. F1 demonstrated **only serial same-disk app-level** dedupe. G1 demonstrated a valid-CA certificate with unrelated subject could self-assert a different `worker.id` and matching label; **CA trust is not host/role authorization**.
- Existing source: `p0-fenced-effect-consumer-contract-2026-10-10.md` and `scripts/vf_office_v2_p0_fenced_effect_consumer_lab.py` are synthetic denial-only, not atomic provider-side authority.
- Existing source: `p0-exclusive-git-sink-failclosed-offline-2026-10-10.md` (`32/32` offline) and `p0-native-git-crash-durable-unknown-reconcile-2026-10-10.md` (`19/19` on both operating systems) already cover in-memory denials, two local processes, SQLite write-ahead, native local Git CAS and crash-after-effect UNKNOWN. Do **not** count a repetition as another milestone. The latter explicitly demonstrated a process bypassing the putative sink.
- Existing source: `p0-real-etcd-expiry-github-epoch-cutover-2026-10-10.md` proved a **real negative**: an expired etcd owner with the still-current Git ref SHA successfully wrote to GitHub before marker cutover. A Git ref compare-and-swap does not atomically check etcd lease generation. `p0-real-etcd-mtls-rbac-identity-denial-2026-10-10.md` proved scoped real localhost etcd mTLS/RBAC and durable unleased intent, **but under one OS UID**, without sole Git credential custody.

All the above remain historical evidence, not a newly authorized active service. #604 is OPEN/RED; #612 is OPEN/PARTIAL.

## 2. Trust-boundary decisions

1. **Single canonical authority.** Reuse the #604-selected provider when approved; **do not** turn Dagu, a SQLite fixture, Task Envelope JSON, or a second scheduler into an independent lease/source of truth. No provider has been approved for production in this checkpoint.
2. **Separated principals.** A worker may submit an immutable proposal. Only a separately admitted, least-privilege *effect sink* may hold a scoped Git/API write credential and perform the effect. The reconciler must be able to check the canonical provider and destination without trusting a worker's claimed success. A process sharing Windows `SYSTEM` or macOS UID 501 with a worker does not demonstrate credential isolation.
3. **Identity admission is NOT Dagu label matching.** The admission boundary MUST verify a trusted `host_principal`/certificate subject or SAN against a versioned, deny-by-default allowlist binding exactly to `worker_id`, capabilities, authorized task class, target resource and permitted sink endpoint. Reject a valid-CA certificate whose declared `worker.id` or capability label conflicts with the bound identity; reject unknown CN/SAN; reject unauthenticated peers; use a real negative test for each. A label supplied by a worker is never authoritative.
4. **Sink-side exclusive write path.** All external changes require a privileged sink which serializes one resource/ref, authenticates the provider *inside the effect boundary*, keeps durable write-ahead intent, and has an independently verifiable single credential principal. A worker and unrelated process MUST demonstrably fail to bypass it; a local mutex, permissions on a file, Dagu mTLS or a green QA result do not establish that denial.
5. **No false exactly-once claim.** If an external provider cannot atomically enforce the monotonic fencing token at commit time, the integration must distinguish `intent accepted` from `effect committed` and freeze on all uncertain outcomes. GitHub ref SHA CAS protects the ref, **not** the lease epoch; expiry during an in-flight push cannot be prevented by a preflight-only lease read.

## 3. Proposed immutable logical intent envelope — `vf604.intent.v0` (not live schema)

The durable *logical* identity exists across fresh scheduler attempts. All digests bind exact bytes, not semantic filenames or worker claims.

```json
{
  "schema": "vf604.intent.v0",
  "job_key": "sha256:<canonical-task-and-effect-scope-bytes>",
  "intent_id": "<provider-issued stable id, unique for an effect>",
  "attempt_id": "<fresh, never-reused, provider-recorded uuid>",
  "dagu_run_id": "<optional scheduler correlation only>",
  "epoch": 7,
  "lease_id": "<canonical provider lease reference>",
  "provider_revision": "<monotonic provider observation>",
  "host_principal": "<authenticated identity, not self-declared label>",
  "worker_id": "<identity-map-bound id>",
  "capability": "<allowlisted verb>",
  "effect_kind": "git_ref_update",
  "target": {"repository": "<allowlisted scratch repo>", "ref": "refs/heads/<allowlisted scratch ref>"},
  "expected_source_sha256": "<hash of immutable trusted source bytes>",
  "expected_remote_sha": "<exact observed ref SHA>",
  "proposed_remote_sha": "<candidate commit SHA>",
  "authorized_until_provider_time": "<provider clock deadline>",
  "terminal_receipt_digest": null
}
```

- `intent_id + effect_kind + canonical target` must be unique in the authoritative ledger. A retry uses a new `attempt_id` and possibly a new epoch, **never** silently replaces the unresolved intent. Dagu can retry/re-enqueue only through the outer controller after recovery authorization.
- Validate schema, source digest, task scope, job ownership, existing UNKNOWN journal, signed policy provenance, principal-role map, provider generation and bounded deadline before *admission*. Untrusted workers cannot mint or raise epoch, choose a protected ref, broaden capabilities, or assert terminal success.
- A source SHA is a **content binding**, not a signature or authorization. A self-hash/receipt from an untrusted worker is also not source authenticity.

## 4. Proposed state machine and terminal evidence

| State | Meaning | Allowed successor | Authority |
| --- | --- | --- | --- |
| `SUBMITTED` | Logical request recorded; no effect authorized | `ADMITTED`, `DENIED` | provider / policy |
| `ADMITTED` | Authenticated principal, immutable scope and exact lease accepted | `INTENT_DURABLE`, `DENIED` | provider, sink |
| `INTENT_DURABLE` | Unleased write-ahead intent committed under authoritative CAS | `EFFECT_IN_FLIGHT`, `FROZEN_UNKNOWN` | credential sink |
| `EFFECT_IN_FLIGHT` | External operation possibly dispatched; **not** success | `COMMITTED_VERIFIED`, `FROZEN_UNKNOWN` | sink + independent readback |
| `FROZEN_UNKNOWN` | Crash, ACK loss, provider partition, lease expiry mid-effect, unverified cancel, identity drift or conflicting readback | `COMMITTED_VERIFIED`, `MANUAL_CLOSED_NO_RETRY` **only after** authenticated independent reconciliation and old writer quiescence | independent reconciler / owner gate |
| `COMMITTED_VERIFIED` | Canonical effect/readback matches exact intent + digest and provider state | terminal; no automatic replay | independent verifier |
| `DENIED` / `MANUAL_CLOSED_NO_RETRY` | Invalid or administratively closed attempt, with traceable reason | terminal for this attempt | policy / owner |

`CANCEL_REQUESTED` or Dagu `aborted` are **signals**, not terminal proof: state remains `FROZEN_UNKNOWN` until exact process-tree identity, late-effect sentinel and independent sink readback prove that no effect can still land. For external effects, even a verified killed process does not undo an already accepted provider write.

### Atomicity rule

The single authoritative provider may atomically CAS **its own** lease/intent state; local SQLite can transactionally update its *own* rows. Neither fact makes the GitHub effect atomic with an etcd record. The sink must keep the irreversible provider-call interval serialized and block cutover while an old call could still finish. If that proof is unavailable, **no new writer** and no automatic retry; leave `FROZEN_UNKNOWN` and require operator review. Define provider-specific idempotency or commit-time fencing separately for each effect type.

## 5. Next accepted negative tests — do only the delta

| ID | New acceptance test | Required evidence | Failure / refusal criterion |
| --- | --- | --- | --- |
| `I01` | Two different principals concurrently claim same `intent_id` across distinct physical hosts | Real single-provider CAS log, lease generation and attempts; one admitted sink call maximum | both effect calls admitted, stale owner can write, or provider state not independently checked |
| `I02` | Old host after lease expiry **knows the latest remote SHA** | The actual privileged sink rejects stale epoch before GitHub write; remote ref is unchanged | old owner writes or bypasses sink, even when Git expected SHA is current |
| `I03` | Crash before external effect | Durable *unleased* intent survives authoritative provider restart, destination unchanged, UNKNOWN freeze | automatic retry on no-ACK/no-ref-change alone |
| `I04` | Crash **after** destination accepts external effect, **before** receipt | Native provider readback, exact candidate/effect linkage; UNKNOWN preserved until reconcile | duplicate effect or inferred success from worker status |
| `I05` | ACK loss, conflicting remote read, mid-push lease expiry | Old sink process-tree shut down or conclusively fenced, quarantine of future writer, authenticated readback | automatic reassignment, silent SUCCESS, unsafe quick TTL handoff |
| `I06` | G1 replay: CA-valid worker presents mismatched `worker.id`/label | Bound cert subject/SAN + authenticated policy denial with no job execution | mTLS alone accepts self-selected role |
| `I07` | Valid cert under unauthorized host or capability, worker tries sink credential/direct provider write | Actual negative OS/network/server-side denial under separate principal | worker or same-UID process can read credential or invoke an accepted write |
| `I08` | C1 replay with long-lived process tree and durable late-effect sentinel | OS process-tree birth identity, bounded kill confirmation, sentinel after cancellation window, sink readback | mere Dagu `aborted` is treated as effect cancellation |
| `I09` | Provider unavailable/partitions at each decision boundary | All new writes frozen; exact UNKNOWN durable after restart | permissive fallback to labels/local clock/in-memory lease |
| `I10` | Trusted policy source digest changed while a worker is pending | Immutable trusted policy baseline rejects new bytes, all input hashes retained | code/QA executed from untrusted proposal without reviewer/pinned baseline |

**Gate sequencing:** Start with a no-network fixture that emits **new** failure-sensitive test vectors only where coverage differs from prior accepted scripts. Then use a **separate OS identity/credential holder** and bounded scoped real-provider scratch resource in an explicitly approved LAB; do not move directly to six Dagu Workers or to protected `main`. A two-host mTLS trial requires explicit key custody, network/firewall scope, revocation plan and rollback approval. The two-host native credential denial and in-flight external effect race—not another SQLite green-count—are the material unresolved steps.

## 6. Per-gate receipt contract

Every acceptance receipt must include `test_id`, exact source commit/digest, tool/binary version, provider endpoints and scopes (without secrets), real host and authenticated principal, `intent_id`, all attempt IDs, epoch / provider revision / bounded clock, process-tree birth/termination evidence where relevant, **actual** provider and remote readbacks, negative-control result, cleanup and rollback, source evidence location and independent verifier. `UNKNOWN` and failures are append-only; never overwrite the raw optimistic receipt with a later corrected conclusion.

**Promotion is forbidden unless**: independent credential custody; enforceable worker certificate-to-role binding; durable *authoritative* intent; observed native provider stale-owner denial (including latest remote SHA); crash / lost-ACK reconciliation; verified cancellation effects; strict OS principal isolation; independently verified source/QA; and narrow approved two-host scope are all evidenced. Portability of Dagu binaries, a green synthetic test, or a protected docs PR is not a substitute.

## 7. Changes explicitly NOT made by this checkpoint

No Dagu process/service/port was started, no new host accounts, keys, certs, Firewall/SSH/WinRM or privileged OS configuration, no credential reading/installation, no GitHub scratch-ref or protected-main effect (apart from the documentation-only branch commit carrying this draft), no production runtime change, no Ollama paid calls/Codex CLI, no customer data/printing/Instagram, no Chris main reboot, and no assertions of six-host secure fleet admission. This is an actionable **design checkpoint** only; follow-up implementation needs a separately constrained, evidence-based PR and security approvals where indicated.