# Cognee backend for vfmem

Status: optional local derived semantic index. `vfmem` remains canonical.

## Why

Cognee adds persistent semantic recall across harnesses without changing VelvetOS
authority. It indexes selected canonical files and returns context. A recall result
is never permission, policy, live operational truth, finance truth, production truth,
or publication truth.

## Runtime

Pinned contract: `packages/vfmem/cognee.json`.

Windows reference host:

```powershell
py -3 -m venv "$HOME\.velvetos\cognee-venv"
& "$HOME\.velvetos\cognee-venv\Scripts\python.exe" -m pip install "cognee[gliner]==1.6.0"
$env:VFMEM_COGNEE_PYTHON="$HOME\.velvetos\cognee-venv\Scripts\python.exe"
```

The adapter forces local/keyless extraction by default, isolates Cognee storage below
`~/.velvetos/cognee`, and ignores ambient provider credentials in its child process.
Remote providers require the explicit process-scoped opt-in
`VFMEM_COGNEE_ALLOW_REMOTE=1`; this is not a standing authorization.

## Sync and recall

```bash
python packages/vfmem/scripts/vf_cognee.py doctor
python packages/vfmem/scripts/vf_cognee.py sync
python scripts/vfmem.py recall "why did we choose this workflow?"
```

Sync builds a content-hash versioned dataset. It never writes back into canonical
memory. A new source digest creates a new dataset and atomically moves only the local
state pointer after all configured sources complete. Old datasets are retained for
rollback/audit until an explicit maintenance policy is added.

If Cognee is missing, unsynced, unhealthy, or returns invalid output,
`vfmem.py recall` falls back to the built-in local graph/search path.

## Trust boundary

Configured sources may contain historical facts. Retrieval therefore carries
`requiresCanonicalVerification=true`. Before action, resolve the relevant current
Git/live source. This is especially mandatory for prices, debt/payment state, print
state, stock, schedules, publication status, and contact/CTA policy.

Do not ingest secrets, raw chats, customer-sensitive records, or live finance /
production / publication state directly into Cognee.

## Runtime updater

The repository ships a local staging/promote/rollback helper:

```bash
python packages/vfmem/scripts/vf_cognee_runtime.py status
python packages/vfmem/scripts/vf_cognee_runtime.py stage --version X.Y.Z
python packages/vfmem/scripts/vf_cognee_runtime.py promote --receipt <receipt.json>
python packages/vfmem/scripts/vf_cognee_runtime.py rollback
```

`stage` accepts only exact stable semantic versions, creates a separate virtual
environment, installs the exact candidate and runs the synthetic keyless smoke against
an isolated staging data root. `promote` refuses to proceed unless the staged version
matches the current Git `pinnedVersion`; it renames the previous live venv into a
timestamped rollback directory and restores it automatically if the post-promotion
doctor fails. `rollback` restores the newest rollback venv and verifies it.

## Update procedure

Stable updates are monitored weekly.

1. Read the upstream stable release and compatibility notes.
2. Create a staging venv; never upgrade the live venv in place.
3. Install the exact candidate version.
4. Run a synthetic keyless smoke in an isolated staging data root.
5. Run VelvetOS static sensors.
6. Update `pinnedVersion` in `cognee.json` through a reviewed Git change.
7. Only after the Git pin and tests are green, promote the staging venv.
8. Keep the previous venv as rollback; if any post-promotion doctor/smoke fails,
   restore it and keep the old pin.

No prerelease/dev/rc build is auto-promoted. No update may convert Cognee into a
source of truth or enable a cloud model provider implicitly.