# Learning lifecycle — candidate to durable policy

Source pattern: selective `affaan-m/ECC` continuous-learning / learn-eval ideas, implemented inside VelvetOS memory and checkpoint governance. No observer daemon, plugin runtime, or second memory backend is introduced.

## Goal

Prevent two failure modes:

1. Useful lessons disappear at session end.
2. One-off observations are promoted too quickly into durable rules.

## Lifecycle

`signal -> candidate -> evidence -> accepted/rejected -> promoted -> superseded/pruned`

Signals may come from checkpoints, daily retro, owner corrections, repeated sensor failures, production incidents, repeated route misses, or repeated successful repairs.

Candidate records live under:

`packages/vfharness/state/learning-candidates/<candidate_id>.json`

Schema fields:

```json
{
  "schema": "vf.learning-candidate.v1",
  "candidate_id": "learn-...",
  "trigger": "specific observable condition",
  "action": "bounded response",
  "scope": "task|project|owner",
  "confidence": 0.5,
  "status": "candidate",
  "evidence": ["checkpoint:..."],
  "first_seen": "ISO-8601",
  "last_seen": "ISO-8601",
  "owner_correction": false,
  "promote_to": null,
  "supersedes": null
}
```

## Confidence rules

- Confidence is evidence strength, not model certainty.
- New candidates should normally start between `0.3` and `0.5`.
- Repeated independent evidence can raise confidence.
- Owner correction is strong evidence, but still must not silently override constitutional or safety rules.
- Never invent evidence to reach a threshold.

## Promotion

Promotion requires all of:

- `status=accepted`;
- at least one concrete evidence reference;
- destination named in `promote_to`;
- no unresolved contradiction with current constitution/rules;
- human/repetition gate required by the destination still applies.

Before creating a new skill/rule/playbook, run overlap review:

`Save | Improve then Save | Absorb into <existing> | Drop`

Prefer absorb/update over skill proliferation.

## Pruning

Reject or prune candidates that are stale, contradicted, duplicate, unsupported, or too task-specific. Never delete history that is needed to explain a prior policy; mark supersession instead.

## Verification

`python3 scripts/check-learning-lifecycle.py`
