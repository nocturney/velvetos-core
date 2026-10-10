# Office Control Plane — canonical Handoff pair in protected machine-writer (2026-10-10)

## Actual blocker verified on GitHub Actions

Fresh actual [Office Control Plane run #38038022532](https://github.com/nocturney/velvetos-core/actions/runs/38038022532), on merged main `6ca639fd9b1602ec04dfa52c7774da8b5ec9f03a`, passed **Learning candidates from failed main runs** and skipped intentionally ignored Living Studio caches as expected. It created a scoped local commit `49c96246` with 5 allowed changed/new evidence paths, but the already-established protected `push-main-with-check-all.sh main` failed:

```text
Skipping intentionally ignored runtime projection: packages/velvetos/living-studio/data/signal-room.jsonl
[main 49c96246] office: persist Living Studio activation evidence / learning candidates
error: cannot rebase: You have unstaged changes.
::error::machine writer could not rebase onto current main
```

The local commit **was not pushed to main**. Real machine writer correctly refused a dirty checkout.

## Independent root-cause reproduction

On Windows, a fresh isolated LF clone at the exact `6ca639fd...` source base ran the real local `vf_control_plane.py watchdog/memory-hygiene/gaps/handoff` routines. `git status --porcelain` exposed **exactly two tracked edits** outside the existing writer allowlist:

- `office/control/HANDOFF.json`: `updatedAt` and `date` advanced from Oct 5 to Oct 10;
- `office/control/HANDOFF-he.md`: displayed handoff date advanced from Oct 5 to Oct 10.

The Handoff step deliberately writes both files via `build_handoff()`. They are documented **canonical manager-handoff artifacts** under `office/control-plane.json`, not disposable caches. Neither was staged by the previous activation-only allowlist. We did **not** stash, force-clean, force-push or circumvent the protected machine writer.

## Small explicit ownership fix

Modify only the **existing** Office Control Plane workflow's bounded `VELVET_MACHINE_WRITER_ALLOW` and `paths` array:

1. Explicitly add the two exact canonical paths `office/control/HANDOFF.json` and `office/control/HANDOFF-he.md`, generated during this very workflow's `Handoff validate` step. Remove the intentionally gitignored `signal-room.jsonl` and `receipts.jsonl` cache paths from the writer policy comment (their runtime-only checks still skip them).
2. After staging only allowlisted artifacts and candidate evidence with `git add --ignore-removal`, require a **clean unstaged tracked tree** with `git diff --quiet`. Any other tracked changes fail early, emit only their paths, and never reach rebase or protected push. Untracked unrelated files remain untouched; the protected helper remains the only push mechanism.
3. Continue checking the staged index for material changes; no-op runs do not commit; no automatic candidate deletions.

## Exact Bash-step adversarial QA

Extended `scripts/vf_office_control_persistence_lab.py` extracts and runs the **actual current workflow Bash block** inside a disposable throwaway Git repository with a no-network `push-main-with-check-all.sh` stub, and validates the canonical machine-writer allowlist. Strict **10/10** scenarios cover:

- Ignored-only runtime streams create no commit;
- newly created eligible evidence/candidate files persist;
- **both canonical JSON + Hebrew handoff files** persist as one bounded commit;
- ignored signal/receipt caches never enter Git;
- identical input yields no-op;
- attempted candidate deletion is refused and not staged;
- later updates to tracked allowed paths persist;
- unrelated untracked files are not admitted;
- an unapproved **tracked** policy change fails closed before commit;
- restoring that policy file permits an unchanged no-op.

No real GitHub push, fleet scheduler, paid model/API calls, production write or customer/Instagram/printer effects occur within this fixture. Both handoff files were actually present in the isolated live-source reproduction; the executed fixture is synthetic and never replaces the real protected run.

Exact fixture LF SHA-256: `3614e88a90ba6d71025497e3613cce22d93ed16d9e18174900ecba437a77fc59`; pinned by `check-office-control-plane.py`. An updated **10/10** test count is enforced by the canonical CI sensor.

## Pending real acceptance

- Protected exact-head PR CI and normal squash merge.
- Merged-main 118-sensor full suite green.
- Fresh Office Control Plane workflow dispatch on current main after merge: both Learning candidates + Persist activation evidence steps must pass. If the protected helper actually pushes a machine-generated commit, its own exact-head precheck and any required postpush full suite must also be observed. No claims of operational recovery until those complete.
- Issue #612 P0 remains PARTIAL: this is Office workflow correctness, not #604 provider-issued cross-host lease/agent zero-touch recovery.
