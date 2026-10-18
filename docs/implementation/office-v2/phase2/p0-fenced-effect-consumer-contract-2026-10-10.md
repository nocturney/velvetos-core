# P0 #612 / #604 — effect-boundary lease consumer contract (synthetic LAB, 2026-10-10)

## Why this gate exists

A local one-attempt `O_EXCL` RUNNING journal and a read-only batch Task Envelope collision audit are not a canonical cross-host lease. A stale Windows agent can wake up after an upstream #604 fleet provider rotates an owner to a Mac agent. If the integration trusts the old worker's once-valid snapshot or local PID alone, it may write to a shared artifact or Git ref after losing ownership.

#604's owner [consumer requirements](https://github.com/nocturney/velvetos-core/issues/604#issuecomment-6087398500) require provider-issued monotonic fencing generation, provider-time expiry, and **atomic validation at every actual code/effect mutation**. #612 must consume that authority, never mint a competing lease.

## What was implemented

`scripts/vf_office_v2_p0_fenced_effect_consumer_lab.py` is a **pure offline denial-only contract**. The only accepted provider tag is `SYNTHETIC_FAKE_PROVIDER_ONLY_NOT_CANONICAL`, and the CLI only permits `selftest`. It cannot connect to any fleet provider or effect sink.

The contract binds a claim to the existing strict LAB Task Envelope and validates exact Task/attempt, host/worker, worktree path, Git base, branch, resource identity, lease ID and strictly positive integer generation. A single complete fake-provider observation must carry one ACTIVE lease, a provider clock and revision, and bounded unexpired TTL. Its dry-run effect preflight re-checks an independently supplied latest observation and rejects moved revision/content or split ownership. It **never** returns a write, dispatch, production, retry or orphan-exclusion authorization.

47 deterministic Windows unit scenarios include: valid but nonauthoritative structural read; independent provider clock; ten foreign-owner lease fields; ten altered-claim fields; expired, revoked, unbounded or bool-typed timestamps/generations; stale or changed observation revisions; provider partition; ambiguous multi-lease payload; spoofed producer authority; preserved one-attempt budget; an old Windows owner refused after a fake cross-host handoff; and a new Mac owner still refusing real effects. Each negative requires the *specific* refusal code; an unexpectedly accepted negative fails.

Source LF SHA-256: `1359f5fbaf6902dbc02cf86e8174d11b0912f76f69b72df2ba48c98581d85dc5`. The Office contract sensor verifies this exact hash, all 47 tests, and absence of dispatches, real leases, model calls, commits, production effects and retries.

## Strict nonclaims and actual next owner gate

- **NO canonical lease provider integrated.** An arbitrary user-created JSON payload, a synthetic source name, or passing this script's `inspect` check can never authorize a worker.
- **NO actual atomic write boundary.** Comparing two snapshots is insufficient: a provider can revoke a lease *after* the second read but *before* Git or artifact mutation. Real adoption requires #604-approved, provider-enforced *atomic generation check with the effect* (or an equivalent fenced sink) and tests against simultaneous Windows/Mac contenders, partition and clock skew.
- **NO crash/retry/external-effect reconciliation.** An old `UNKNOWN` Task Envelope remains `NO_BLIND_RETRY` until independently reconciled. Native OS process identity and detached descendant exclusion remain separate gates.
- **NO scheduler, external API cost, child processes, machine changes, production/customer/social/printer writes.**
- This is a reusable consumer contract and negative-test specification, **not evidence of distributed ownership already working**. #604 retains provider selection/claims/renew/revoke; #612 owns agent Task Envelope, QA and PR lifecycle.

## Reproduce

```sh
python scripts/vf_office_v2_p0_fenced_effect_consumer_lab.py selftest
python scripts/check-office-v2-contracts.py
python scripts/update-readme-snapshot.py --check
```
