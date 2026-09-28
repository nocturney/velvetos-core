# Living docs governance

VelvetOS keeps a small set of canonical document roles instead of accumulating competing status files.

## Roles

- **Constitution / authority:** `AGENTS.md` and explicit permission/security docs.
- **System map:** README and package maps explain what exists and where ownership lives.
- **Operational status:** machine-readable runtime receipts/checkpoints/automation state, not prose snapshots.
- **History:** CHANGELOG, merged PRs, and immutable task/handoff history.
- **Playbooks:** reusable execution procedures; never treated as proof that deployment actually happened.

## Rules

1. A status document may describe how to inspect state, but current truth must come from machine-readable state or live provider evidence.
2. Prose must not claim a worker, connector, automation, deployment, or publication is healthy without naming its evidence source.
3. When a fact can drift independently of git, do not hard-code it as permanent current state in a long-lived doc.
4. Prefer links to canonical manifests/checkpoints over copied lists.
5. New root-level status/map documents require an explicit role not already served by an existing canonical doc.
6. Deprecated docs must point to their replacement rather than silently remaining authoritative.

## Current runtime truth

Use:

- `packages/vfharness/runtime/expected-components.json` for expected ownership.
- `packages/vfharness/state/runtime/*.json` for observed deployment/runtime receipts when available.
- `scripts/check-runtime-doctor.py --strict` for deployment proof. Locally and on pull_request CI an expired receipt is only a WARN; for a deployment claim run it with `VF_RUNTIME_RECEIPTS_STRICT=1` (the mode push/schedule/workflow_dispatch CI uses).
- task checkpoints and handoffs for in-progress work state.

## Verification

`python3 scripts/check-living-docs.py`
