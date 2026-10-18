# Office 2.0 P0 #612 — Live GitHub ref CAS: two distinct Windows clients, one winner

**Executed 2026-10-10 | Status: SCOPED PASS, P0 overall remains PARTIAL.**

This experiment moves beyond the **synthetic stale-observation denial-only** gate merged in [PR #654](https://github.com/nocturney/velvetos-core/pull/654). It actually attempts two conflicting Git updates against **one remote GitHub ref** using expected old SHAs, and proves remote Git rejects the stale contender. It is **NOT** a real #604-issued lease, monotonic generation, atomic fencing at all independent effects, a two-physical-host writing race, or an autonomous agent PR writer.

## Fully isolated remote target and actors

- GitHub `nocturney/velvetos-core`; exact `main` at experiment start **`1237f2c2f09f65937a9543a60edaa7b3e3c6d36f`** ([previous PR #660](https://github.com/nocturney/velvetos-core/pull/660) merged, exact postmerge Core Sensors [#38045735409](https://github.com/nocturney/velvetos-core/actions/runs/38045735409) SUCCESS).
- A completely new and temporary **nonprotected, lab-only remote ref** `refs/heads/lab/office-p0-cas-20261010-gpt6-j01` was checked absent and then created pointing exactly to the original main SHA. No production/main ref was updated by this experiment.
- **Chris / Windows client A:** independent full LF clone `AgentEnvelopeLab/p0-git-cas-race-win-20261010-01/repo`. New local synthetic commit `99389febd5c3212b61f314f9d4fe96bdf8893b0e`, parent exactly `1237f2c2...`; synthetic change only `docs/implementation/office-v2/phase2/cas-only/win-owned.txt`.
- **Chris / Windows client B:** different independent LF clone `AgentEnvelopeLab/p0-git-cas-race-win-20261010-02/repo`. New local commit `79969cf5b9088696880a43013c7b7cbba82510fd`, same original parent, different scratch-only file `win-second-owned.txt`.
- **MacMiniOffice.local:** third independent clone/local synthetic commit `200ec212ede7e9c56cf21eee3c0a4a7512209e59` with the same base, but **was not authorized to write**: native Mac `git push --dry-run` failed `could not read Username for 'https://github.com'`, `gh auth status` reported no GitHub login and SSH public-key auth was rejected. We did not transfer credentials, bypass permissions, or count Mac as a remote writer. Mac participated in **read-only cross-host Git ref readbacks**.

## Actual GitHub effect-boundary attempt and outcomes

Two Windows **native Git client processes were launched concurrently** from the separate clones, both targeting one scratch ref using the same exact old SHA:

```text
git push --porcelain \
  --force-with-lease=refs/heads/lab/office-p0-cas-20261010-gpt6-j01:1237f2c2f09f65937a9543a60edaa7b3e3c6d36f \
  origin HEAD:refs/heads/lab/office-p0-cas-20261010-gpt6-j01
```

| Evidence from actual Git CLI | Result |
|---|---|
| Client A original push | **ACCEPTED**, GitHub remote `1237f2c2..99389feb` |
| Client B concurrent push | **REJECTED** with `[rejected] (stale info)` |
| Immediate remote readback on Windows | Exactly winning commit `99389feb...` |
| Independent remote readback on Mac | Exactly winning commit `99389feb...` |
| Stale Client B attempted the same original expected SHA once more | **REJECTED again**, status **exit code 1** |
| Cleanup using `--force-with-lease=ref:99389feb...` | **Deleted precisely this scratch ref**, observed exit 0 |
| Final independent Windows+Mac readbacks | Scratch ref **ABSENT**; `main` **unchanged** at `1237f2c2...` |

**Honest logging limitation:** The original two Git push output lines unambiguously showed accepted/rejected responses, but a separate PowerShell `toUpperCase()` formatting command failed immediately afterward, so the first two native `$LASTEXITCODE` values were **not preserved**. Do **not** invent original numeric statuses. The subsequent explicit stale retry exit **1** and scratch deletion exit **0** were captured normally, and the winner was independently read back before deletion on **both** hosts.

This was real GitHub **remote atomic ref update comparison**, not a fake local reference fixture. The deleted scratch ref can no longer be used for further writes. This does **not** show #604's provider lease mint/renew/revoke/expiry, the right to do a Git write under Office policy, or revalidation immediately before every possible non-Git effect. A Git CAS protects the target Git ref, not other artifacts or actions outside that ref. There was **only one physical writing host**, although Windows and Mac both successfully read back the resulting remote state.

## Offline contract & reproducibility

The sanitized historical receipt is `p0-two-client-real-github-ref-cas-2026-10-10.json` (adjacent file). Source `scripts/vf_office_v2_p0_remote_git_cas_witness.py`, exact SHA256 `ae737c0767647431565d3744ed11394b8d4b62de7babb7f42d0f4a1b874cc49d`, verifies exact SHA/ref/one-winner/stale-denial/safe-delete/independent host readbacks and **25/25** adversarial false-claim/false-permission negative controls. The `verify` and `selftest` modes are **strictly offline**. A separate, explicitly manual `readback --repo <isolated lab repo>` mode verifies currently absent scratch ref and exact main SHA from GitHub **without writes**; CI must never call this live mode.

**No original Task Envelope, Worker Receipt, UNKNOWN journal, model, printer, social/customer service, credential store, main, other production branch, or CAD process was changed.** No Codex, paid model/API calls, reboot, new scheduled task, scheduler or daemon.

### Next owner gates (still unmet)

#604 alone can select the single canonical lease provider and issue fencing generations with atomic claim/renew/revoke; #612 must consume a *real provider-issued ownership token* in each authorized effect receiver before real Git/artifact changes. Only then may authorized Windows/Mac workers test cross-host concurrent claims, loss/rejoin, stale-owned effects, network partitions, no-blind-retry and protected agent-authored PRs. On Mac, obtaining native Git write access requires an authorized Mac-side login; it cannot be inferred from the read-only Git ref check.

**Overall P0 PARTIAL; this proof cannot be promoted into any production workflow.**
