# Office 2.0 P0: manual fresh-attempt identity separation after UNKNOWN — 2026-10-09

**Scope:** issue #612, bounded **read-only** review of two already-existing local-model Task Envelopes. The tool neither makes a Task Envelope nor starts a worker or Job, creates a lease, or grants scheduler/retry authority. #604 alone owns placement and fleet leases.

## Independent readback of actual Windows LAB history

The new pure verifier `scripts/vf_office_v2_p0_fresh_attempt_lineage.py` was evaluated on Chris against the historical interrupted task **h** and successful-new-task **i** from PRs #640/#641, without writing to their original directories:

- Original interrupted `p0-win-job-guard-gpt6-nextchat-interrupt-20261009-h`: `UNKNOWN_RUNNING_JOURNAL_NO_BLIND_RETRY`. Exact original envelope SHA256 `6ffe743f004b98bfda42a7076d7374aea329308c880b331cd47add94c73e14b0`; original raw `receipt.json.running` SHA256 `798081231f7af3d13256de84653ca5abe283488b82b03fe67fe4477b0237cf18`. **No final receipt, never retried.**
- Different `p0-win-job-guard-gpt6-nextchat-newafterunknown-20261009-i`: sealed envelope SHA256 `9694d73817bea7c541dacf23c4c5eb9ce9e21b9f4e033210dc4757de259c04b1`; locally evaluated state `SUCCESS_CLAIM_NEEDS_INDEPENDENT_WORKER_VERIFY`.
- New task ID, Git base SHA, branch, absolute worktree path, and context-checkpoint path are **all distinct** from the original. The old journal stayed unchanged across the entire readback.
- The lineage checker **does not** independently re-run worker verification. Historical separate Worker QA for the already-executed `i` was recorded in merged PR #641. Never mislabel the read-only lineage test as a model run or admission.

## Code, tests and negative gates

Source base at clone: `5cd6dfda905231df25de3f1e6083454c30f49b29`; exact executed script was committed at `5f62a376af390bf7ed60d8fc508289e7ca6bf009`. Script Git blob `783575ff1784bb7165ec4cb1a73b1c643dccfed7`, raw Windows file SHA256 `b2eb921c37ace4f979f98433f069df07484e7b0b5f1e670c112efabf6a90ea73`.

**21/21 pure offline selftests** under temporary isolated data: separate acceptable unstarted/new success claim (still no authority), and denials for identity reuse (task ID, Git base, branch, worktree, checkpoint), invalid/aliased paths, Codex CLI, paid API, multiple attempts, non-LAB authority, modified/missing or conflicting old journal, conflicting or tampered new evidence, and symlinked envelope.

`inspect` calls canonical `vf_office_v2_p0_unknown_reconcile` for the original and the new Task Envelopes, hashes all relevant inputs before and after, and **never** changes the original evidence. Positive output is `DISTINCT_MANUAL_ATTEMPT_LINEAGE_ONLY_NOT_ADMISSION`, always with `original_unknown_retry_authorized=false`, `new_task_execution_authorized=false`, `autonomous_recovery_proven=false`, `all_orphan_descendants_excluded=false`, `fleet_lease_or_scheduler_authority=false`, and no model calls.

## What is NOT proven

Not a checkpoint-aware zero-touch recovery engine, exactly-once effects, atomic cross-host claim, distributed lease/fencing, escaped descendant containment, verified current worker liveness, autonomous failover, production runtime, or meaningful multi-cycle p50/p95 and resource data. A future admission step must independently reconcile host OS process identity and all descendant risks, acquire the **canonical #604 lease**, require exclusive fresh input/output and Git ownership, and receive explicit eligible authority before any model execution. SHA-256 seals and preserved byte hashes are not external digital signatures.

Raw sanitized result: `docs/implementation/office-v2/phase2/p0-manual-fresh-attempt-lineage-2026-10-09.json`. No paid API use, Codex CLI, background watcher, new scheduler, business writes, production credentials, printer or social actions.
