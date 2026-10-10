# Office 2.0 P0 / #612 — same-fixture two-host coding outcome and throughput observation

**Date:** 2026-10-10 UTC. **Verdict: PARTIAL, NOT P0 GREEN.** Two real physical machines were running local Qwen/Aider in overlapping intervals, and the Mac produced independently QA-accepted Python artifacts. The Windows runs failed independent QA. This experiment is a negative control against declaring a 2-worker speedup merely because both hosts ran.

## Exact experiment and source-of-truth limits

- Canonical GitHub `main` at start: `823caed3ed04893f462009b28571afea09eb1e8c` (prior [#681](https://github.com/nocturney/velvetos-core/pull/681) merge and full-main CI green). Reused that exact Worker source SHA-256 `9ed3f0b495008c44249867c87b664aa7b75178049b1c7d53f37d557bd12cfafb`. No new source changes were installed on either host for the model runs.
- Fixed, public synthetic **`canonical-tag-v1`** task on both machines; exact matching seed SHA `49db6ebb…b56f1`, visible QA SHA `55ada6c9…d668`, hidden QA SHA `fd3b2860…9db` and public `PUBLIC_SPEC_STATE_MACHINE_V2` prompt SHA `4b97af9e…92e`. Full digests and attempt-specific raw evidence hashes are in the adjacent [sanitized JSON](p0-612-two-host-same-fixture-throughput-negative-2026-10-10.json).
- Windows Chris used `qwen3.5:9b`, local Ollama port 11555 and existing pinned Aider 0.86.2; MacMiniOffice.local used `qwen3.5:4b`, port 11556 and the existing pinned Mac Aider. Different models are **not** a model-speed comparison. Each fresh bounded Task Envelope had its own Git clone/branch, one permitted attempt, 175-second timeout, no new paid API and no production effect authorization.
- Both model outputs were verified by the existing Worker/independent QA contracts. Failed originals were **not** retried or overwritten. Host readbacks sampled the original local receipts and raw SHA-256 values. Public CI can validate only this sanitized historical evidence and its anti-overclaim invariants; **it cannot replay or cryptographically authenticate raw host files that are not in Git.**

## Observed outcomes

| Fresh task | Host / phase | Host-command wall time | Independent QA | Quarantined source |
| --- | --- | ---: | --- | --- |
| win-a1 | Chris Windows / solo | **91.638 s** | **FAILED**, visible exit 1, hidden exit 1 | SHA `72056d73…50bc70` |
| mac-b1 | Mac Mini / solo | **62.343 s** | **PASS**, 3 visible + 12 hidden | SHA `b2ec92fe…cb691974` |
| win-b1 | Chris Windows / overlapping | **41.877 s** | **FAILED**, visible exit 1, hidden exit 1 | SAME SHA `72056d73…50bc70` |
| mac-c1 | Mac Mini / overlapping | **60.451 s** | **PASS**, 3 visible + 12 hidden | SAME SHA `b2ec92fe…cb691974` |

The Windows parallel shell started **20:31:02.318 UTC**; the Mac parallel shell started **20:31:08 UTC**. Their measured wall windows overlapped for **36.195 seconds**. In that parallel wave, **one** artifact passed QA, **not two**. The Mac's separate Worker elapsed values were 60.359 and 58.474 seconds; the above table instead uses host-command wall times including its bounded overhead and QA.

**Repeated source bytes are not distinct algorithms.** The two Mac accepted sources are byte-identical, including to an earlier already accepted Mac solution; the two Windows failures are also byte-identical. Inspection against the *public* task spec found the same branch-condition error in both Windows outputs: an underscore separator is appended when the previous character is **not** ASCII-alphanumeric, rather than at the transition **from** a maximal alphanumeric run into a separator. This reproduces an actual repeated Qwen9B failure despite the public profile; it does not depend on revealing any private hidden QA vectors.

## Preserved failures

- On Mac, a separate earlier `mac-a1` attempt was rejected during OS birth-pin capture with `PSUTIL_REQUIRED_NO_FALLBACK_TO_UNPINNED_PS`, after 1.386 seconds in the default system Python. Its original RUNNING journal persists, and it has **no** final success receipt or kernel pin. The exact number of model calls for this failed pre-pin window remains **unknown**, not zero by assertion. The next attempt used a **new** task ID and the already-installed Aider Python containing `psutil`; no software was installed.
- Both Windows failed-QA original journals remain RUNNING/UNKNOWN. Separate zero-model-call `audit-failed-qa` and `verify-failed-audit` passed on each, confirming absent success receipt, actual independent QA failure and denial of original retry. Audit selfhashes: `c63a7259…98a08d` (win-a1) and `fae125b8…bc007` (win-b1). Neither audit changes the original evidence.
- No active Aider processes were observed after the experiment. Existing Ollama services were left unchanged.

## Do not overstate throughput, cost or security

There are only **two comparable observed model attempts per host**, with only **two QA successes**, both on the same Mac and yielding the same source. No statistically defensible p50/p95 comparison, accepted distinct PRs/hour, universal model ranking, autonomous crash recovery, distributed epoch/lease fencing or model-token/cost measurement exists here. Incremental paid API spend was zero, but electrical/hardware cost and attribution of model-server CPU/RAM/GPU peak were not measured. The observed overlap establishes concurrent *execution*, not accelerated independently correct coding throughput.

**Important new security blocker surfaced:** The Windows Remote Desktop Commander context is `NT AUTHORITY\\SYSTEM` in **Session 0**. The model-generated Python source was tested by independent QA in that OS context, without a demonstrated OS sandbox or verified separate low-privilege worker account. A clean Git clone, sanitized environment and Python subprocess do **not** create a privilege boundary. Mac user `chris` likewise is not proven to be a separately confined low-trust worker. Treat prior synthetic run evidence as a bounded research result, **not untrusted-code-production admission**, and **do not start further generated-code execution on these privileged/unconfined contexts** until isolation is verified. Do not claim a ready Mac `sandbox-exec` solution: [#676](https://github.com/nocturney/velvetos-core/pull/676) proved a real hard-link alias bypass. A read-only `sudo -n -u nobody id -u` check on Mac returned *a password is required*; no user account, permission, keychain, Windows Session 1, WSL or production service was changed.

## Reusable evidence validator

`python3 scripts/vf_office_v2_p0_two_host_throughput_gate.py selftest`: **19/19** local policy checks (18 negative mutations). `verify` recomputes the recorded overlap, rejects false success/agent/credential/sandbox/p95 claims and binds the observed output/audit hashes to the exact fixture IDs. This is a **sanitized-evidence consistency verifier**, not a signed source witness or a scheduler. Integrate it only as a read-only Office sensor.

**Next priority:** #604 sole security/fleet owner must establish a real OS/credential isolation gate and protect exclusive Git Sink custody; #612 then restarts generated-code execution only inside proven isolation, restores independent source QA, and measures repeated 1-vs-2 **accepted distinct tasks** with resource/token/operator metrics. No Codex CLI, paid API, new queue, production credentials, Instagram, printer, CAD or customer effect was introduced.
