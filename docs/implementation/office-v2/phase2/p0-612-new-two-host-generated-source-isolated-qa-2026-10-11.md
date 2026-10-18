# Office 2.0 #612 — new, different Qwen source outputs from both hosts; isolated hosted QA

**Date:** 2026-10-11. **Scope:** two new single-attempt source-only local inference tasks plus one narrowly locked credential-free GitHub-hosted Docker QA job. LAB only, no production API, PR-writing agent or Git Sink.

## What really ran on connected hosts

Both experiments used a locally reachable Ollama API with public synthetic prompts, `temperature=0`, one request each, without running or importing generated Python:

| Host | Model / local port | Public fixture | Candidate SHA-256 | Local inference seconds | Output tokens |
| --- | --- | --- | --- | ---: | ---: |
| Chris Windows (DCC SYSTEM) | Qwen3.5:9B / 11434 | merge-windows-v1 | `65bf260ac6f29c74337e0bea3c1079f7b0203cd9b1a0eade1b96569e19557bc1` | 6.391 | 317 |
| MacMiniOffice.local (DCC chris) | Qwen3.5:4B / 11556 | canonical-tag-v1 | `337c6c159f5de53d3628a213a815b835a830ed72ee1b97e915f29ed609540677` | 17.821 | 319 |

Each local job retained its own `request.json`, raw `response.json`, static candidate and `receipt.json` in unique LAB task directories. They were one-shot with no retry. The original raw response hashes and prompt hashes, model token counts, fixed source hashes and non-execution claims were transcribed from those actual generated local receipts to the sanitized `p0-612-new-two-host-local-ollama-text-only-2026-10-11.json` manifest. The repo archives only two exact candidate source byte sequences under `.py.txt` filenames outside default Worker entrypoints; this file suffix does NOT prevent intentional execution by Python or provide OS isolation. Never execute these archives on either physical host. This provenance is a checked receipt and hash chain, **not cryptographic attestation of a model's identity or perfect absence of all side effects**.

Static manual inspection found that Windows Qwen9B implemented strict `type(endpoint) is int` and adjacency merging; Mac Qwen4B emitted a faulty procedure with duplicates, missing lowercase and incorrect separators. Neither candidate has been executed on either physical host. These are *review predictions*, not QA results.

## Narrow independent test boundary

The new `vf_office_v2_p0_hosted_new_source_review_lab.py` handles **ONLY these two SHA-pinned sources**, public original fixtures and existing #685 Docker execution controls. Pure local selftest checks hashes, bounded AST, rejects unreviewed imports/dynamic calls/mutation of source registration, and rejects changed Docker privilege/network flags. It never executes candidate code, launches Docker or calls a model on local hosts.

A separate PR-only hosted `ubuntu-24.04` workflow declares `permissions: {}`, checks out public source with `persist-credentials: false`, runs static selftest first, then pulls immutable OCI Python RepoDigest already observed in #685. Each known reviewed source is copied into a fresh temp public fixture and executed **only inside a new non-root Docker guest**, `--network=none --read-only --cap-drop=ALL no-new-privileges`, no Docker socket or secrets mounted, read-only source mount, limits on memory/CPU/PIDs/FD/files. Actual Docker HostConfig is inspected, native negative controls deny networking/host canary/UID0/filesystem writes, and independent 3-visible + 12-hidden tests compare expected outcomes. One source is expected PASS and the Mac source is expected FAIL — *no false green for the failing candidate*.

**Actual hosted proof:** [PR #695 GitHub Actions run #38117158715](https://github.com/nocturney/velvetos-core/actions/runs/38117158715) **SUCCESS**, job `114404233722`, tested PR source head `83671e69d31b28a00024a94393d4b0c0387a2bed`. Two exact-source model outputs each ran in a distinct disposable Docker guest after real inspected nonroot UID65534, zero-network, read-only mount/root, ALL capabilities dropped, no-new-privileges, CPU/memory/PID limits, no exported writer credential, no Docker socket or host canary, and blocked `setuid(0)`. **Windows 9B newly generated merge source: 3/3 visible and 12/12 hidden PASS. Mac 4B newly generated tag source: visible FAIL, hidden FAIL.** The Mac negative was correctly *rejected as an algorithm*, not falsely accepted. The workflow result is `PASS_ONE_NEW_SOURCE_QA_AND_ONE_NEW_SOURCE_REJECTED`, NOT two accepted PR/algorithms or general sandbox proof. 24/24 AST/model-free static PASS and no model inference on the CI runner. Both physical hosts separately passed 24/24 static checks and direct local `run` FAIL_CLOSED exit2. Full protected Core Sensors and postmerge main CI remain separate required gates before release.

## Explicit limits

A bounded fixed two-sample Docker QA exercise does **not** grant arbitrary future generated-code execution, native Windows SYSTEM source execution, model-driven autonomous PR, independent two-job GitHub writer custody, OS kernel escape resistance, exactly-once cross-store effects, distributed agent failover, or broad #604 P0 completion. The Docker administrator on the test VM remains privileged over its guests, as verified in #688; the test does not place actual signer keys there. Both local Worker run/verify gates from #691 and #683 stay blocked. No Codex CLI, paid model/API, production writer, customer, social, printer, CAD or active host security setting changed.
