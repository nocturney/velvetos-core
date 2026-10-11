# Office 2.0 P0 / #604 — real same-UID separate-container synthetic signer custody LAB

**Date:** 2026-10-11. **Pre-admission status: LAB ONLY / no real Git writer.** This is a concrete, reversible test of one remaining #604 trust-boundary hypothesis, NOT an integration or a fix for [#675](https://github.com/nocturney/velvetos-core/pull/675)'s SAME-macOS-UID disposable Sink key theft and [#676](https://github.com/nocturney/velvetos-core/pull/676)'s pre-existing hardlink alias. Those earlier proofs remain true on the unconfined Mac host.

## Threat model and explicitly limited positive claim

The safe [#685](https://github.com/nocturney/velvetos-core/pull/685) pilot proved a Docker guest cannot read an outside synthetic host canary under one no-network read-only mount, and can run **previously SHA-pinned public Python**. For #604 the narrower next question is: **can two separate containers, both using numeric Unix UID 65534 and concurrently alive on the same fresh GitHub-hosted VM, keep a synthetic signer-only secret outside the uncredentialed worker's filesystem namespace?**

One **synthetic private HMAC key** is generated inside a *signer container* with `secrets.token_bytes(32)` and saved to an ephemeral `/sink` tmpfs mounted **only in that signer guest**. Its **bytes are never printed or copied into a host bind, Git file, real certificate store or worker environment**. The signer receives only a fixed public synthetic effect intent under `/public` and emits the HMAC signature and a bounded readiness result, then stays alive while the worker runs. No real GitHub token, TLS cert, ZITADEL/OpenBao secret, customer information, production provider or network is used.

A separate **uncredentialed worker container** runs concurrently under the **SAME UID 65534**, with read-only `/public` and private scratch `/tmp`, but no signer `/sink` mount, no Docker socket and no network. Its reference attack script deliberately attempts a direct read of `/sink/signer-only.key`, a hardlink alias of that path, a symlink alias read, forging an HMAC using known false-public bytes, querying non-loopback interfaces and public TCP egress. Each action must be denied. A complete positive lab result requires the signer to remain alive while the worker records denied attempts, actual Docker HostConfig verified for both, and a zero-privilege/workload-only outcome.

**Standard runner:** `ubuntu-24.04` GitHub-hosted ephemeral VM, PR-change-only dedicated `.github/workflows/office-p0-synthetic-signer-custody-lab.yml`, declared `permissions: {}`, `actions/checkout@v7 persist-credentials:false`, no `pull_request_target`, production jobs, model calls or paid API. The base Python image is pulled by the already proved immutable OCI digest `python@sha256:0a310eeecf4e1f5a0743f9a6520c90c88d089c903ca5fd283f501e3a805f5f89`.

## Initial independent static gates

Source: `scripts/vf_office_v2_604_hosted_signer_custody_lab.py`. Local selftest runs no Docker or generated-source QA: **19/19 PASS** on Mac at creation. It checks immutable image binding, source negative controls, strict expected signer+worker argv and 14 attempted unsafe privilege/network/capacity mutations. An attempted local `run` returns `FAIL_CLOSED`, reason `GH_HOSTED_LAB_CONTEXT_NOT_PRESENT`, exit 2. Live GitHub-hosted evidence and independent Chris Windows static check must pass before any broader note.

No branch protection, ruleset, system keychain, OS user, Windows Sandbox/WSL, Ollama service, established GitHub workflow, scheduler or production business action is changed by this work.

## Red boundary that this cannot close

The GitHub-hosted Docker **daemon and VM administrator** still have authority to inspect/attach containers and their memory/tmpfs. Neither is a separate hardware-backed trust root. Thus even if the worker cannot read the synthetic key, this pilot does **NOT** prove that a compromised agent or host can never access an operational Git signing key, does not create an actual credential-owning Sink, and does not address mTLS/RBAC custody, authenticated remote two-host routing, provider lease cutover, stale-owner GitHub push denial, durable `EFFECT_IN_FLIGHT`, unknown-effect reconciliation, protection of old scratch refs, or exactly-once effects across stores. The HMAC is an adversarial **synthetic negative test**, not an authorization system. Any positive outcome is `PASS_SAME_UID_SYNTHETIC_MOUNT_SEPARATION_ONLY`, **not** #604/P0 GREEN.

The current local [#683](https://github.com/nocturney/velvetos-core/pull/683) Worker fail-closed gate stays enabled; no arbitrary untrusted code is admitted. #604 continues to own the canonical provider and exclusive real Git Sink design; #612 is only a coding-agent consumer. No Codex, paid inference, installed daemon, real credential, customer, Instagram, printer or CAD change.
