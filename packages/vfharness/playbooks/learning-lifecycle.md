# Learning lifecycle — observation to durable memory

Stage 7B canonical contract. No observer daemon, plugin runtime, second memory backend, or forced daily quota is introduced.

## Goal

Keep useful learning without turning every observation into durable truth or duplicating the same fact across owner-memory, vfmem, Cognee, and office-learning.

## Canonical lifecycle

`observation -> candidate -> evidence/recurrence -> promoted durable fact/pattern -> superseded/expired`

Negative terminal outcomes remain `rejected` and legacy `pruned`.

| Stage | Existing surface | Authority |
|---|---|---|
| observation | task checkpoint / retro / measured domain evidence | evidence only |
| candidate | `packages/vfharness/state/learning-candidates/<id>.json` | candidate status + evidence refs only |
| evidence/recurrence | candidate `status=accepted` with concrete refs / owner correction | promotion eligibility only |
| promoted durable | exactly one named `promote_to` SoT | current durable truth |
| superseded/expired | candidate/history + target's normal history mechanism | historical context only |

`office-learning` owns the process, not the facts. `vfmem` routes and canonically verifies. `owner-memory.md` owns durable owner-specific facts only when no more-specific SoT owns them. Cognee is a derived semantic index with no writeback.

## Candidate record

Candidate records live under `packages/vfharness/state/learning-candidates/` using `vf.learning-candidate.v1`.

Statuses:
- `candidate` — bounded hypothesis/signal.
- `accepted` — evidence/recurrence triaged as worthy of promotion review; still not durable truth.
- `promoted` — written to one explicit `promote_to` canonical destination.
- `superseded` / `expired` — no longer current.
- `rejected` — evidence did not support promotion.
- `pruned` — legacy terminal compatibility status; new expiry should use `expired`.

## Automatic CI signal source

`office-control-plane.yml` may ingest failed main-branch workflows into candidates. Ingest is deterministic/idempotent and **never changes candidate status automatically**. More failures add evidence; they do not auto-promote.

## Promotion gate

Promotion requires all of:
1. current candidate status is `accepted`;
2. concrete evidence exists;
3. `promote_to` names exactly one existing canonical destination;
4. current canonical source is re-read and contradiction/authority scope checked;
5. destination-specific repetition/human gate is satisfied.

An explicit owner correction is strong human evidence and may satisfy the human/repetition part when the destination allows it; it does not bypass safety, constitution, or canonical verification.

No daily quota exists. A retro with no meaningful durable learning ends with no memory promotion.

Before creating a new skill/rule/playbook:
`Save | Improve then Save | Absorb into <existing> | Drop`

Prefer absorb/update over proliferation. Never copy the same current fact into owner-memory and a domain SoT as two authorities; after promotion, the candidate/old memory entry is provenance/history.

## Supersession / expiry

Do not silently delete history needed to explain prior behavior. Mark the learning candidate `superseded` or `expired` and let the promoted destination's normal history mechanism preserve provenance. Derived Cognee data is refreshed from canonical sources and is never the closure mechanism.

## Verification

`python3 scripts/check-learning-lifecycle.py`
