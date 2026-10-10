# #612 P0 — two-physical-host distinct historical coding-QA witness (2026-10-10)

This is a **new cross-host integrity check of ALREADY FINISHED real model runs**, NOT a fresh model dispatch, zero-touch PR pipeline, simultaneous two-host launch, native provider lease or production admission.

## Independently verified source evidence and original file readback

| | Chris Windows (past) | MacMiniOffice.local (past) |
|---|---|---|
| P0 Task ID | `p0-win-job-guard-gpt6-success-20261009-d` | `p0-diverse-run-mac-merge-guided-20261010-a` |
| Model/executor | Qwen3.5:9b / Ollama + Aider | Qwen3.5:4b / Ollama + Aider |
| Actual distinct code family | `slug.py` | `windows_merge.py` |
| Original Worker result | `SUCCEEDED`, separate original Worker `verify` PASS | `SUCCEEDED`, separate original Worker `verify` PASS |
| Independent QA in original receipt | 3/3 unit + 12/12 hidden PASS | 3/3 unit + 12/12 hidden PASS |
| Original receipt raw SHA-256, directly re-observed on its own host Oct 10 | `ca5b0f2960158f41ace3a54a396bb68957523e5f34d4738060e1791408fe4e70` | `f6dac1286bb1fad2ddb525ecf51d3fd86a9149d2a5cc8464f05c5569350cedda` |
| Original receipt embedded selfhash | `4424b020ead05e6d30bd4467f105792f98fc37f0aca039144f0413432a5eec02` | `431c9d94ac939c794da794e84175964508e77125397e1fcc36a5a7fdc8862524` |

Original raw receipts were **read-only hashed on their corresponding live host**. Their raw file hash and embedded selfhash intentionally differ: they measure different byte sets. The raw receipts remain host-local and **are not mounted or re-read by cloud CI**.

Both historical attempts have distinct Task IDs, Git bases and branches. Prior failed attempts remain preserved: an interrupted Windows Job with UNKNOWN/no-blind-retry and a failed Mac QA Task with original journal intact and no success receipt.

## Reproducible, narrow repo verifier

`scripts/vf_office_v2_p0_two_host_coding_witness.py` binds the two existing separately verified sanitized receipts; it calls both ORIGINAL existing source validators in `verify`, pins the two exact source JSON byte SHA-256, and checks cross-host uniqueness, QA, model cost, failure preservation and false-promotion flags.

- Windows source: `docs/implementation/office-v2/phase2/p0-supervised-aider-windows-job-2026-10-09.json` SHA-256 `7f690fd1da3b8f0dad5b84dca93133e86077b70287192eecc5f1d12e84c0a3a8`.
- Mac source: `docs/implementation/office-v2/phase2/p0-two-fresh-guided-model-qa-2026-10-10.json` SHA-256 `f032b75a5a16a1292d61390e3f47d53987aa7e7b3005309b5eef01dda0ef42d7`.
- Verifier LF source SHA-256 `93f34b7aa8fd9e4d58bf0d2ea07d2122393b8eda62503b140d7ca71edbc5a3b7`.
- 31/31 offline positive/adversarial scenarios, including false QA, source/receipt drift, task, host, branch, model, base collisions, paid spend, duplicate retries and false success on prior FAILED task. Each negative must cause its expected refusal.

```sh
python scripts/vf_office_v2_p0_two_host_coding_witness.py selftest
python scripts/vf_office_v2_p0_two_host_coding_witness.py verify
python scripts/check-office-v2-contracts.py
```

## What this closes, and what it DOES NOT

- **Verified:** there are at least two **different previously completed successful local-model coding Task Envelopes with independently checked QA on the two different physical hosts**. Original on-host raw receipt bytes were independently read back today, but CI's reproduction scope is the pinned sanitized original evidence/validators.
- **NOT VERIFIED:** same-time concurrency; a canonical cross-host lease or generation fence; a new model invocation today; end-to-end agent-generated protected PR plus independent CI merge; statistically representative benchmark throughput/p95; autonomous crash/requeue; absence of detached orphan processes; production authorization.
- Under #612, overall P0 stays **PARTIAL**. #604 keeps exclusive fleet-lease ownership; this audit does not create a scheduler or writer permission and does not touch the unrelated open Mac PR #652.
