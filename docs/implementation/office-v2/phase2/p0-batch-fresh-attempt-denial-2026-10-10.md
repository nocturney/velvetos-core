# P0 #612 — read-only multi-attempt lineage collision guard (2026-10-10)

## Scope and failure closed

The previously established `vf_office_v2_p0_fresh_attempt_lineage.py` compares one new manual synthetic attempt with an older preserved UNKNOWN attempt. That does **not** establish uniqueness *among several* otherwise-fresh attempts. Two new envelopes may each be distinct from the original yet share a task ID, Git base, branch, checkpoint, or worktree.

The new `scripts/vf_office_v2_p0_batch_lineage_guard.py` accepts one old `envelope.json` and corresponding `receipt.json` location plus 2–16 already-existing fresh envelope/receipt path pairs. It runs the canonical per-pair read-only reconciler, then rejects a collision in **any** of five dimensions across the complete set including the old attempt. The script fingerprints input files before and after, refuses symlinked direct inputs, and emits only a bounded denial-only report. This is a second conservative inspection layer, not an authorization system.

### Offline proof

- Windows Python 3.11: 15/15 cases passed: positive distinct-two-attempt proof; 10 negative collisions (new vs old and new vs new across five dimensions); three unsafe authority/budget/executor refusals; subsequent clean acceptance after denials.
- `python scripts/check-office-v2-contracts.py`: PASS, now exercises the new refusal tests. `python scripts/update-readme-snapshot.py --check`: PASS.
- No model invocations, scheduler leases, retries, API spend, production writes, or process termination.

### Known boundaries

- This does not certify the absence of stale/orphan processes or validity of historical QA. It does not reserve identities, solve concurrent check-then-dispatch races, or establish a #604 owner lease. A read-only PASS **cannot** authorize a worker, a fresh retry or a production action.
- The canonical single-pair checker remains the source of the old UNKNOWN/no-blind-retry rules; if any fresh pair is inadmissible even for inspection, the batch refuses.
- Next ownership gate remains explicit #604 scheduler/lease integration and live process fencing; do not introduce a competing scheduler.
