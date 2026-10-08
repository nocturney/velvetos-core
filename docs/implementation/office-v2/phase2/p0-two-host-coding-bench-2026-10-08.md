# Office 2.0 P0 — actual two-host local coding concurrency and forced-worker-loss LAB (2026-10-08)

Canonical owner: [#612](https://github.com/nocturney/velvetos-core/issues/612). **LAB evidence only; no production writer, no autonomous scheduler, no new API or Codex CLI.** Evidence: `p0-two-host-coding-bench-2026-10-08.json`; pure offline evidence verifier: `scripts/vf_office_v2_p0_two_host_benchmark_verify.py`. Manual-only fixture producer: `labs/p0_identical_fixture_aider.py`.

## Actual controlled exercise

Two connected hosts, Chris Windows and MacMiniOffice.local, used **the same source Git blob** `62f22e42701997037df6454501a22f03c8d53433` and same tests SHA-256 `81134cc5640d34646e2419bcc4c4be737dac1a6ca98b35ba9282bd69fa7b5f60`. Each host had two distinct fresh, clean, committed Git fixture directories, serial and parallel. Windows had local Ollama Qwen 3.5:9B; Mac had local Qwen 3.5:4B; **the same host/model configuration was retained between serial and parallel phases**, but the two machines and model sizes differ. Aider 0.86.2 ran local `ollama_chat/` models, at most 170s per attempt, isolated HOME/XDG paths and no paid API. This is not a network or OS sandbox.

For each of the **four real model edits**, base unittest was red; model wrote exactly `slug.py`; 3/3 unittest passed and 12/12 unseen edge cases passed when the resulting file was replayed into a separate clean Git clone. Unit outcomes and replayed SHA-256 were compared to signed receipts. No customer data or business side effects. **No auto-retry on failed execution.**

| Mode | Win local model | Mac local model | Dispatch wall |
|---|---:|---:|---:|
| Serial, one at a time | 27.625s | 52.34s | **99.133s** |
| Parallel overlap | 26.5s | 51.279s | **51.281s** |

Parallel overlap independently observed: **26.499s**. Dispatch-wall ratio **1.933×**. Sum of serial model-call wall times 79.965s divided by parallel wall yields **1.559×**; the 1.933× dispatch figure also includes a real one-at-a-time dispatch gap (approximately 19.17s) and must **not** be sold as pure inference acceleration.

## Actually forced worker process loss

A separate local Mac isolated Git fixture used the canonical `vf_office_v2_p0_worker.py` and pinned `vf_office_v2_continuity.py` contract. It launched one real fixture subprocess, observed journal + partial `started.txt` and verified the direct child PID/parent ownership, then sent **SIGKILL to the exact worker parent PID and the exact owned sleeping child**. No unrelated process was stopped. Readback confirmed: worker exit -9, RUNNING journal preserved, final receipt **absent**, `started.txt` present, `result.txt` absent. A second attempted `run` with the **same** envelope and receipt was explicitly rejected `DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY`; no false success or blind replay. The journal and partial output were retained for explicit reconciliation. **No autonomous resume/cross-host failover was exercised.**

## Explicit operator reconciliation and safe NEW attempt

After the forced worker loss, a separate isolated Mac operation first checked that the original `receipt.json.running` remained present, the original final receipt was absent, only `started.txt` was dirty and no original `sleep_job.py` subprocess was still active. **No automatic retry or deletion of the old journal was performed.** An entirely new Git checkout was created from the clean committed source; a new, reviewed offline-only quick fixture was committed with its own base SHA, envelope/task ID `p0-verified-new-attempt-after-loss-002`, fresh checkpoint and receipt path. The new Task Envelope executed to `SUCCEEDED`, and a **separate OS process** executed the worker `verify` command with `PASS`. The original unknown journal and partial output remained quarantined and unchanged. Signed reissue receipt SHA256: `287368342dbaba1c6b4f32b8ecfbc0d00d38a64f996a489ad29fdb2f1ee68883`. A new fifth independent negative check re-seals a false success and confirms the verifier rejects it.

**Scope:** This demonstrates a safe **operator-mediated reissue of a different locally pinned synthetic task** after explicit reconciliation, not resumption of the killed model task, not automated failover, not dual-host worker loss recovery, and not production promotion. No external business effects.

## Independent verification and restrictions

Windows verifier independently re-read mirrored signed Mac receipts plus local Windows receipts, recomputed five sealed SHA-256 receipt digests, compared source hashes, exact changed paths, unittest counts and independent replay hashes, verified serial non-overlap and parallel time overlap, and rejected four tampered/unsafe negative cases. **PASS_SCOPED_LAB**; independent summary receipt SHA-256 `b7d00c7bfeb458521a02c3bb16d00e665ec14626da9798ec7fc5fe1a6bfc0029`. The tracked static Office contracts sensor now runs the portable evidence verifier in GitHub CI, so future accidental changes to evidence fail closed.

**Not proven:** production scheduling, autonomous worker startup/placement, durable cross-host failover and reconciliation/resume, a killed live coding model, p50/p95 from repetitions, peak CPU/RAM/VRAM, independent human reviewer approval, or per-model same-size cross-host equivalence. Dagu scheduler/placement remains exclusively #604; this trial used authenticated remote dispatch and never touched the existing Fleet coordinator processes or reserved OfficeV2-Lab. No new automation or third authority.

**Next #612 gate:** implement one admitted, bounded model worker through the existing Task Envelope with a genuine crash→reconciliation receipt and safe fresh attempt; select host placement only through #604 once its comparator is accepted. Measure additional matched tasks/repetitions with host resource peaks, preserve independent QA and strict PR/CI/postmerge.
