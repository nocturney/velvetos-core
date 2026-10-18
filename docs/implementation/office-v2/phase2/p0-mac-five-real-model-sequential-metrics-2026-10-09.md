# Office v2 #612 — five independently verified real Mac local-model coding cycles

Date: 2026-10-09. Status: **FIVE SEQUENTIAL SYNTHETIC Mac LAB RUNS PASS; NOT DISTRIBUTED AUTONOMY OR PRODUCTION ACCEPTANCE**.

## Why / scope

The previously proven P0 two-host Aider work demonstrated correctness/containment, but did not supply repeated timing distributions. To start collecting repeatable performance observations without interrupting a busy Windows NVIDIA GPU and existing CAD/GUI apps, five **new and different** Mac Mini Task Envelopes were prepared sequentially. Each was independently admitted by the canonical `vf_office_v2_p0_local_model_fixture.py`, then executed by the original `vf_office_v2_p0_local_model_worker.py` and **separately** verified using its `verify` command. This is real Qwen3.5:4B inference via local Ollama and Aider 0.86.2, NOT a mock agent, but the code task is the same synthetic Python `slug.py` fixture in five fresh Git repos. All runs use distinct task IDs, base commits, branches, output paths and context checkpoints; no original UNKNOWN Task Envelope was retried.

## Exact observed timing and independent QA

| Task suffix | Worker elapsed seconds | Visible QA | Hidden QA | Independent Worker verify |
|---|---:|---:|---:|---|
| 01 | 44.632 | 3/3 | 12/12 | PASS |
| 02 | 47.229 | 3/3 | 12/12 | PASS |
| 03 | 46.331 | 3/3 | 12/12 | PASS |
| 04 | 45.228 | 3/3 | 12/12 | PASS |
| 05 | 48.576 | 3/3 | 12/12 | PASS |

**Observed sample statistics:** min **44.632s**, max **48.576s**, arithmetic mean **46.399s**, median/p50 **46.331s**. A nearest-rank `ceil(0.95*n)` p95 of this **five-observation sample** is **48.576s** (simply its maximum); it is **not a reliable estimate of production p95**, an SLA, or CI/PR end-to-end time. It excludes manual dispatch/review overhead, queue placement, machine startup and protected GitHub merge time.

Every receipt reported `SUCCEEDED`, `model_invocations_min=1`, the same expected resulting `slug.py` SHA256 `456f89bec0af23e6287e88956b8b85e992d4926b89e9613238bee7f77302ab45`, exact 3 unit+12 hidden PASS in independent fresh-clone QA, and zero additional paid API spend. Each of the five separate `verify` calls returned `status=PASS` and `offline_fixture=false`. The receipts had distinct self-hashes, distinct raw byte SHA256 and separate OS kernel-birth pins. Full hash details and exact 5 envelope Git bases are in `p0-mac-five-real-model-sequential-metrics-2026-10-09.json`.

## Provenance / original raw evidence

- Host: `MacMiniOffice.local`; local Ollama `127.0.0.1:11556`, model `qwen3.5:4b` digest `7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13`.
- Executed scripts from clean repository `nocturney/velvetos-core` SHA `b1147951747ca38550fee9da118e6b51447d0215`: model worker raw source SHA256 `7b4cb176c9c66351f9658c08589f45ec94d50c2a8b6450fe8e5cb1d8f09d86f7`, fixture source SHA256 `a1b6687cb6da7631b954077911b8c4986f8547c1197b613a1000bb13a274a47d`.
- Exact raw receipts/envelopes/kernel pins retained **on the Mac host only** inside the exclusive, non-production `AgentEnvelopeLab/p0-repeat-metrics-mac-20261009/p0-repeat-metrics-mac-20261009-0{1..5}` directories. Their raw SHA256 values are pinned in the sanitized JSON for separate host-local re-verification. Self-hashes alone are **not externally signed attestation**.
- CPU/RAM/VRAM samples were not captured as time series during these executions. The exact inference call and tokens count are unknown. Do not invent those values.
- No Mac scheduler, new daemon, fleet lease or external-effect writer was created; no use of Codex CLI or paid API, no auto retry, no Windows model contention, no credentials/customer/printer/publishing actions.

## Future P0 gates

The narrow metric study does not establish a reliable long-tailed p95, CPU/RAM/VRAM peaks, token-level accounting, operator-time baseline, two-host concurrency, cross-host lease/fencing, autonomous safe crash recovery, or diverse-real-repo coding throughput. Those remain prerequisites for overall P0 GREEN and require #604 canonical owner-backed placement/lease on actual worker tasks. The static offline report checker validates logical/sha constraints and negative controls, **never** replays an LLM or grants execution authority.
