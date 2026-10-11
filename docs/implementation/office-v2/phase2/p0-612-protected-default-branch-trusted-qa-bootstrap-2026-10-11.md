# Office #612 / #604 — protected-default-branch C1 verifier bootstrap

**2026-10-11 · Two protected sequential PR phases, not one same-PR issuer. P0 PARTIAL.**

## Concrete gap closed in design

Prior [#700](https://github.com/nocturney/velvetos-core/pull/700) established that [#698](https://github.com/nocturney/velvetos-core/pull/698)'s genuine passing 3+12 Mac C1 QA used a workflow introduced by the PR itself. An unchanged `check-all.yml` does not prove the check's untrusted HEAD-launched helper scripts immutable. This work introduces a **different default-branch `workflow_run`** chain:

1. Existing protected `VelvetOS Core Sensors` runs on `pull_request`. It may execute candidate scripts, but **no positive Git Sink authority follows from that green signal alone**.
2. **Only after** completion SUCCESS of that named Core workflow, the NEW `office-p0-protected-base-c1-qa.yml` receives a `workflow_run` event. GitHub only executes `workflow_run` definitions present on the **default branch**. There are no `pull_request_target` triggers, no secrets and **`permissions: {}`** at workflow and job level (important because a `workflow_run` trigger can otherwise obtain a privileged token).
3. The job checks out `github.sha` (protected main policy) into `policy/` and `github.event.workflow_run.head_sha` (untrusted PR HEAD) into `candidate/`, `persist-credentials:false` on both. Runs **only** `policy/scripts/vf_office_v2_p0_protected_base_c1_qa.py` using `python3 -I -B`. The candidate's own workflows, imports, tests and runtime scripts are **not called**. Git checks verify both checked-out HEAD SHAs, no persisted local `http.*.extraheader`, exact policy code and YAML Git tree blobs.
4. The trusted code parses `GITHUB_EVENT_PATH` for exact GitHub Core workflow ID **352155264**, `workflow_run.event=pull_request`, success/completed, same-repository HEAD SHA, and canonical default branch. A PR can supply only ONE exact bounded [request](p0-612-protected-base-c1-qa-request-2026-10-11.json) shape. No request in a PR -> `SKIP_NO_QA_REQUEST_ON_PR_HEAD`, no guest/model/API effect.
5. For an exact request, **only** the original existing model-generated C1 source (480 bytes, SHA256 `084d446873fb871ad444f7704b7868b72e599829b9da6e0a2fca0f972d4dae6a`, Git blob `7ec37475b86cabe728b95be37e38e984a74e6264`) and its original provenance are read from `candidate/`. The independently reviewed AST, fixture, 3 visible + 12 hidden cases, OCI digest-pinned Python Docker image, no-network/nonroot/read-only guest setup and negative isolation probes are **all imported from protected `policy/`**. Generated source can only execute **inside** the guest. C1's previously verified 3+12 result is preserved; a NEW triggered GitHub job must independently pass again before a live protected-policy claim.
6. Guest emits structured source SHA, head/base, security negative results and **no Git writer authority**; candidate request with `UNKNOWN`, fake Git token, malformed source, forged issuer or altered manifest cannot grant a write.

### Two-phase evaluation — essential for genuine pretrust

**Phase A (THIS BOOTSTRAP PR):** land trusted runner and workflow from reviewable code through ordinary protected PR, plus Office static selftests / LF cross-OS policy. **DO NOT claim pretrusted positive hosted QA** when testing Phase A: at this time the new workflow does not exist on default branch. Scope is source-only and 37 offline negative tests on both physical machines; no Docker/model source execution on them.

**Phase B (DIFFERENT FOLLOW-ON PR):** after Phase A's normal protected merge + exact-main full 118/118 green, submit a separate **data-only request JSON**. The existing Core Sensors run must first pass; *then* independent default-branch `workflow_run` should run `policy/` code from a previously merged commit and read only the follow-on PR's source bytes. Verify actual checkout SHAs, full guest 3/3 visible + 12/12 hidden and all security flags in original GitHub job logs. Never transform the bootstrap PR's own `workflow_run` into retroactive policy evidence. Reject run that only reports a green check name without trustworthy event/checkout readback. Subsequent original source receipts remain immutable.

**Safety/security boundary and remaining gate:** this is NOT a general untrusted-code sandbox guarantee, a GitHub-native expired etcd lease reject, OS/daemon-exclusive Github App signer principal, independent attestation of model weights, signed decision record, restored UNKNOWN post-crash or an end-to-end agent-written PR. No privileged credential is supplied by this experiment; even a successful Phase B returns `git_sink_credential_custody_proven=false` and `production_authority=false`. [#604](https://github.com/nocturney/velvetos-core/issues/604) is still RED, [#612](https://github.com/nocturney/velvetos-core/issues/612) PARTIAL. Do not confuse an adequate independent *verifier* with an authoritative *writer*.

### Portable static QA and no side effects

Run on fresh SHA-pinned Windows and Mac clones using their existing Python runtimes:

```sh
python -I -B scripts/vf_office_v2_p0_protected_base_c1_qa.py selftest
python -B scripts/check-office-v2-contracts.py
python -B scripts/update-readme-snapshot.py --check
python -B scripts/fix-readme-bidi.py --check
```

Expected offline selftest: **`PASS_37_OFFLINE_PROTECTED_BASE_ISSUER_NEGATIVES_ONLY`**, 37 tests, **0** Git writes, Docker calls, local model executions, network/provider/model calls, token reads or production authority. CI job `run` is intentionally **unavailable** on local physical hosts and cannot be invoked as a replacement for GitHub's future default-branch event. The `.github/workflows/...yml` file is explicitly `text eol=lf` in `.gitattributes` because native Windows with `core.autocrlf=true` initially checked out YAML as CRLF while Mac LF, even though the code was identical; do not change the original archival model bytes.

**Scope of Phase A:** One trusted human-authored runner, one new noncredentialed default-branch workflow, `.gitattributes` targeted LF line, Office contracts hash/negative checks, README/Snapshot refresh and this report only. No additional scheduling service, system configuration, producer/production effects, OS account/ACL, live Git token, model invocation or Codex.
