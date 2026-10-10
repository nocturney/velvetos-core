# Office 2.0 — #604 actual cross-host etcd provider lease + atomic KV fence (2026-10-10)

**Scoped LAB verdict: PASS for actual etcd-native atomic KV effects on TWO physical hosts. NOT production. NOT a general external Git/artifact fence. #604 placement-provider acceptance and #612 full P0 remain OPEN.**

## What was actually run

An entirely new, isolated **temporary** single-node etcd **v3.6.15** process on existing `MacMiniOffice.local` (Apple ARM64, LAN `192.168.0.217`) exposed the standard etcd v3 JSON gRPC Gateway to the existing **Chris Windows** host for a short synthetic experiment at `192.168.0.217:32379`. Dagu was not restarted; no Fleet Console, Office service, resident scheduler, production writer, original agent worktree/receipt, WSL distro or customer resource was touched.

The official [etcd v3.6.15 release](https://github.com/etcd-io/etcd/releases/tag/v3.6.15) from 2026-09-22 provided `etcd-v3.6.15-darwin-arm64.zip` (**24,037,957 bytes**, archive SHA-256 `c791b3b8e94845e130994f99dc5be7db4f57e6481d15f0a78e9bead7028d1e91`, independently equal to official GitHub asset digest). Extracted binaries were version-readback 3.6.15 with exact local hashes in the JSON receipt. Everything remained inside `p0-etcd604-provider-lab-20261010/runtime`; no global PATH, launchd, Windows startup or persistent service was installed.

On both independently connected machines, the **literal same Python stdlib-only** client source SHA-256 `139f8e144d8d858ee38febc209ae6ba8f960f7eee178dd85b5ba9ac8ecf31893` sent real HTTP/JSON requests to the same provider. Each claim generated an etcd lease with provider clock TTL, and issued an atomic **`/v3/kv/txn`** requiring **VERSION=0** on the isolated `lease` key. A winner's `mod_revision` is the monotonic fencing generation, with owner identity and lease attached; a loser revokes its unused TTL lease and has NO local claim file.

For a **synthetic effect stored *inside the same etcd***, the effect receiver used a **single server-side transaction** comparing current lease key `MOD=<generation>`, exact owner `VALUE`, and destination `effect VERSION=0`, then performing `requestPut` *inside the transaction*. This prevents the classic check-then-write gap **for this exact etcd KV write**, but **does not magically make Git push, filesystem writes or other stores atomic**. The destination was fixed under `/velvet-office2/lab604/etcd-revision-20261010`; model calls, real Git writes and production actions were zero.

## Actual observed transaction sequence

| Trial | Independent host observations | Provider-side outcome |
| --- | --- | --- |
| Two-host scheduled same-key claim | Mac and Win sent concurrent claims at same UTC epoch; Mac won generation **2**, Win denied at provider revision **2**, unused Win lease revoked | **Exactly one** current owner |
| First fenced effect + handoff | Mac generation 2 effect PUT accepted/read back; repeat denied; Mac revoked; Windows acquired generation **5** | Old Mac and new Win attempts to repeat the same effect both **denied**; existing effect count remains 1 |
| Short TTL expiry | Windows acquired generation **7**, TTL **6s**, allowed to expire without effect; Mac observed no owner at revision **8** and acquired generation **9** | Mac wrote exactly one KV effect; stale Win generation 7 denied afterward |
| Real renewal | Mac generation **12**, TTL **9s**, renew at about 5s; etcd returned renewed TTL **9s** | At about 10s after first claim, original 9s TTL already would have passed; atomic KV effect still **accepted** with unchanged generation |
| Actual provider outage | Mac generation **15**, TTL **20s**; exact synthetic etcd PID **67630** was SIGTERM stopped | Both Mac effect and Win provider observation **FAIL_CLOSED (exit 3)** while endpoint offline; no fallback effects |
| Same-data restart, then expiry | Same original etcd DB, new exact PID **68234**; original Mac lease initially still present after fast restart, then expired (revision **16**); Windows acquired generation **17** | Windows wrote one real atomic KV effect, old Mac generation 15 **denied** after restart |
| Independent final postcondition | Actual native `etcdctl` range/readback of exact namespace (provider revision **19**), plus separate Windows HTTP observations of all four scenarios | **Exactly 4 synthetic effect keys**, exactly 0 active lease keys, one effect per trial namespace |

Four accepted KV effect SHA-256 digests: race `4b807fa56468ba263cb7e35c8318095d183094b4f3d6b16fd1ec6642927dde02`; expiry `1b402124a276c262f1783b23a81da8bfb24b80895823fe321715c34e71a1e40b`; renew `cbafb47c8d80dee835d5b9978b04e1776922da7da63a970649036e3f42a7de0c`; outage `1cbf69a961f03f7f6c65f726cc08a6237e9085ec6b250391197bd111b3f4bb75`. **Seven accepted real leases** across two hosts at strictly increasing original provider revisions **2, 5, 7, 9, 12, 15, 17**, plus one explicitly denied competing Windows claim. These are NOT seven independent agent jobs or a performance/throughput benchmark.

A later attempt to revoke the already expired `renew` lease received a provider HTTP error and correctly **did not claim successful revocation**. The final native provider readback confirmed zero live lease keys. This genuine error is not hidden as a pass.

## Cleanup / local provenance

Both exact temporary Mac etcd processes (PIDs `67630`, `68234`) were SIGTERM stopped after exact executable/argument checks. Separate Mac readback observed **zero** synthetic-port listeners on `32379`/`32380` and no matching processes; **Chris Windows TCP** independently observed coordinator endpoint **not connectable** after shutdown. Pre-existing Mac Ollama and Windows Ollama/Maya processes remained running. No autostart, public Internet exposure or new job scheduler is left running.

The original host-local **seven provider-issued claim-state JSONs** (four Mac, three Windows) were retained in the respective dedicated LAB roots. Each raw state file has a byte hash in `p0-etcd-two-host-real-provider-atomic-kv-2026-10-10.json`; they are not copied to Git. Mac's retained stopped etcd single-node BoltDB file SHA-256 is `6270dd86521083f7b7130b804d318e98cb87e0374be4f8601d27484ed83bc548`. The JSON evidence is a **sanitized operator readback, not an independent signed receipt**. The original raw HTTP interactions were observed through native host terminal output, not an externally audited packet capture.

## Critical security/architecture boundary: not yet a production admission

**Do not install or adopt this exact service configuration for a live fleet.** This temporary standalone instance deliberately used **unauthenticated, plaintext HTTP on the private LAN**, no per-worker RBAC, no TLS/mTLS and one physical Mac node. A hostile client with raw direct access can issue `/v3/kv/put` and **bypass our gated transaction**. This pilot did **not** verify authenticating who may claim or mutate the effect keys. A single-node outage removes service until restart; there is no quorum/failover, network partition fault injection or clock-skew test.

**etcd-native atomic KV is only one transaction domain.** A Git push, filesystem artifact, Dagu job trigger, agent tool call, customer effect or protected merge is **not** fenced merely because Python read the latest etcd revision before acting. #604 must verify appropriate identity-bound **receiver-side atomic enforcement** in each actual effect sink, while #612 consumes the selected contract and reconciles UNKNOWN outcomes; otherwise the system stays FAIL_CLOSED. Mac native GitHub write authentication is independently blocked as documented in #604/#612. This does **not** select etcd over ready-made alternatives or deploy a second VelvetOS SoT.

## Code + reproducibility

- `scripts/vf_office_v2_604_etcd_provider_pilot.py`: exact local-lab host/endpoint/scenario key allowlist; live `claim/effect/revoke/renew/observe` commands require **manual** invocation against that exact LAB endpoint and use no paid API; offline `selftest` **13/13** on Mac and Windows. It is NOT run live by CI.
- `scripts/vf_office_v2_604_etcd_receipt_gate.py`: offline evidence validator, **31/31** scope, ownership, downgrade and overclaim adversarial cases; verifies pinned original model-free source hash, byte-pinned artifact hashes, TTL renewal, stale-denial, all four native-effect readbacks, shutdown and false authority.
- Existing `check-office-v2-contracts.py` invokes **only** `selftest` / `verify` in offline mode with source + evidence exact SHA pins, no live etcd, no Dagu, no model or Git write.
- This is a candidate evidence milestone under [#604](https://github.com/nocturney/velvetos-core/issues/604); #612 consumer [P0](https://github.com/nocturney/velvetos-core/issues/612) remains PARTIAL. **No candidate registry edits while another registry writer/PR remains open.**

**Required follow-up:** #604 compare footprint and lease/fencing semantics of Restate, existing Dagu + authoritative store, Nomad or other proven ready-made stack, design a **single authoritative identity-bound lease provider** with TLS/RBAC and HA, then prove a real **external** fenced Git/artifact receiver and physical Windows/Mac writer credentials/partition recovery before claiming autonomous coding PR delivery.
