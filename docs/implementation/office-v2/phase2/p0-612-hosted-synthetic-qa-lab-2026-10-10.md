# Office 2.0 P0 / #612 — GitHub-hosted, no-credential synthetic generated-code QA LAB

**Status: CANDIDATE / LAB; never a production Agent executor, Git writer, scheduler, Sandbox promotion or credential sink.**

## Problem

PR #682 proved independent generated Python QA was executed by the existing Mac user chris UID501 and **NT AUTHORITY\\SYSTEM Session 0** on Chris Windows, without an independently verified OS sandbox. PR #683 deliberately blocked direct local Diverse Worker `admit`, `execute` and generated-code `independent_qa` while this is unresolved. Production Git credential custody and etcd→GitHub epoch fencing remain RED under #604, and must not be conflated with functional code QA.

## Ready-made candidate: GitHub-hosted ephemeral standard Linux runner

This pilot reuses **GitHub Actions**, already the canonical protected CI provider in the existing repository, **not a new scheduler or production writer**. The dedicated workflow is `.github/workflows/office-p0-hosted-synthetic-qa.yml`, with only the `pull_request` change-trigger for its own files and `workflow_dispatch` for explicit manual use. It declares `permissions: {}` (no token scopes), `actions/checkout@v7` with `persist-credentials: false`, a standard Ubuntu 24.04 GitHub-hosted runner, eight-minute job timeout, no secrets, no production environment and no paid model/cloud API. Before QA it refuses non-`github-hosted` context, wrong repo, non-Linux, unexpected credential-related environment and persistent local Git auth headers. **These are scoped operational checks, not cryptographic attestation or a universal security boundary.**

The source archive contains TWO SHA256-pinned existing Qwen/Aider results; the actual locally observed source hashes are unchanged:

| Prior produced artifact | Existing source SHA256 | Fixture | Expected |
| --- | --- | --- | --- |
| Mac Qwen3.5:4b canonical tag | `b2ec92fed514a5e0e37aeca31155fe0d04cdfde70a3d46fafeeb9a09b0ef1ccb` | `canonical-tag-v1` | 3 visible + 12 hidden PASS |
| Windows Qwen3.5:9b interval merge | `e625ea816531000df82d15144f3155ebd59a868a2dd89c81c1f254115bafb2b9` | `merge-windows-v1` | 3 visible + 12 hidden PASS |

The existing fixture registry's visible/hidden test contents are separately hash-pinned, not constructed from model output. The hosted runner copies only exact source bytes into a NEW temporary repository-free QA directory, supplies a minimal child environment (no Git/GitHub/cloud tokens), bounds CPU/file-size/open files and process timeout, and executes unit/hidden tests. A third **known-broken public seed** acts as a negative QA control and must be rejected. No real customer, workspace, business, social, CAD or printer data is read by fixture code. No model call is made by this pilot. Successful replay of **previous** source bytes is NOT a new model algorithm or two newly generated PRs.

Source: `scripts/vf_office_v2_p0_hosted_synthetic_qa_lab.py`. The local `selftest` performs only SHA/spec/context consistency checks: **19/19 PASS** on Mac with **zero generated-source subprocesses**, zero Git mutations, zero models. An explicit local `run` attempt returns `GH_HOSTED_LAB_CONTEXT_NOT_PRESENT` exit2 **before** model-generated code is launched; the local guard is deliberate. A positively observed GitHub-hosted job and exact test results are required before changing this candidate from LAB to VERIFIED_SYNTHETIC_QA.

## Limits and activation gate

- GitHub Actions job logs and provider identity can prove where this **bounded synthetic fixture** ran. The environment vars themselves can be spoofed and do not provide TPM/hardware attestation.
- GitHub-hosted runners may have outbound internet connectivity and their default user may have privileged access *inside the disposable hosted guest*. This workflow does **not** prove network isolation or accept arbitrary unknown untrusted programs; all executed source bytes are prior known code with exact immutable hashes.
- `permissions: {}` + no persisted checkout credentials ensures no intentional GitHub write grant; this does **not** revoke unrelated existing GitHub credentials/workflows/Windows Git native authentication and is **not** the exclusive #604 Git Sink.
- The job cannot access local Ollama without an independently approved service bridge; this is **QA of previously generated code**, not autonomous code generation, durable worker recovery, model throughput or unattended PR delivery.
- No production promotion or local guard bypass. Owner #612 may take hosted QA as an alternate **narrow** test surface, while #604 alone owns fleet placement / sole Git credentials. A fresh same-fixture accepted 1-vs-2 workload after security admission is still required for P0 GREEN.
- If the new workflow fails due missing public checkout permissions or Actions policy, keep LAB RED and fix only the minimal scoped workflow within a protected PR; never introduce `pull_request_target`, write permissions, production secrets, paid API or a blanket override of local Worker guards.

No current local system ACL/account, firewall/TCC/Defender, Windows Sandbox/WSL, production process, scheduled publisher, other workflow, token, Git credential or model installation was altered.
