# Office Control Plane — protected evidence persistence fix (2026-10-10)

## Original production failure and newly exposed blocker

The original Stage 7B learning-candidate validation failure is fixed by merged [PR #656](https://github.com/nocturney/velvetos-core/pull/656) and exact merged-main full CI [run 38037188735](https://github.com/nocturney/velvetos-core/actions/runs/38037188735), 118/118.

A **fresh real** [Office Control Plane run #38037323849](https://github.com/nocturney/velvetos-core/actions/runs/38037323849) on that fixed `main` then proved all earlier steps **including `Learning candidates from failed main runs` PASS**, but failed at **`Persist activation evidence only when materially changed`**:

```text
The following paths are ignored by one of your .gitignore files:
packages/velvetos/living-studio/data/signal-room.jsonl
hint: Use -f if you really want to add them.
```

The existing workflow used `git add -- "${existing[@]}"` on all five generated Living Studio paths even when some were deliberately gitignored. Local `packages/velvetos/living-studio/.gitignore` explicitly calls `data/signal-room.jsonl` and `data/receipts.jsonl` disposable runtime caches, not sources of truth. Forcing them into Git would cross that boundary. Additionally, the old materiality check used `git diff --quiet` on tracked paths, which silently ignored new untracked *allowed* activation files.

## Fail-closed implementation

Change only the **existing** `.github/workflows/office-control-plane.yml` persistence step:

1. Check each explicit generated path with `git check-ignore -q -- "$p"`. Intentionally ignored caches are **skipped and never force-added**. Any unexpected check-ignore error other than exit 1 fails closed.
2. Stage only existing, nonignored, explicitly listed activation/history/failure-museum paths. Stage learning candidates with `git add --ignore-removal` so this automatic ingest cannot delete historical candidates.
3. Evaluate material change against **`git diff --cached --quiet`** after staging, covering new untracked allowlisted evidence and avoiding empty commits.
4. Preserve the prior exact-SHA `scripts/push-main-with-check-all.sh main` machine-writer route. No direct main push, force push, new writer/scheduler, extra authority, or permission expansion.

`scripts/vf_office_control_persistence_lab.py` **extracts and executes that exact workflow Bash step** in a disposable Git repository with a local `push-main-with-check-all.sh` **stub that makes no network call**. Seven independent positive/negative scenarios check:

- ignored-only runtime streams are not committed;
- all new explicitly allowed activation/history/failure-museum/learning-candidate files are committed;
- ignored `signal-room.jsonl` and `receipts.jsonl` never enter Git;
- unchanged evidence yields no new commit;
- a deleted candidate is not automatically staged as a deletion;
- later tracked allowlisted changes are persisted;
- unrelated untracked files are not staged.

The existing `scripts/check-office-control-plane.py` contract runs this synthetic exact-step test during full-sensor CI and before scheduled Control Plane mutation.

## Evidence and scope

- Windows native Git Bash: **7/7 actual Bash-step fixture cases PASS**; `check-office-control-plane.py` PASS; `check-machine-writers.py` PASS with 6 allowlisted machine writers and no force pushes/unrestricted stage.
- The fixture's synthetic commits happen **only within disposable temp Git repos**. No live Office files, GitHub pushes, real credentials, customer actions, print work or paid APIs.
- Next required gates: independent Mac Bash-step fixture, protected exact-head CI and normal squash merge, merged-main full sensors, and a **fresh** real Office Control Plane run to confirm both learning verification AND authorized evidence persistence. Do not rerun old workflow commit (old code) and do not assert operational recovery before these pass.

## Reproduce

```sh
python scripts/vf_office_control_persistence_lab.py selftest
python scripts/check-office-control-plane.py
python scripts/check-machine-writers.py
```

Executable fixture LF source SHA-256: `5756a353dd8a72c42b973bd6d4d1b3cdf2fc3107c7e8a0cdd2f88013ef059fba`, pinned directly by `check-office-control-plane.py`. The sensor also asserts the actual Living Studio `.gitignore` still intentionally excludes `signal-room.jsonl` and `receipts.jsonl`.
