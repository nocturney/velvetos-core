# Office v2 Context Pressure & Compaction Runbook v0

The Continuous Conversation Runtime is a **project-continuity layer**, not semantic memory and not business truth.

Required flow:

`project work → context pressure detection → Project State checkpoint → compaction → Post-Compaction Verification → resume`

## Pressure inputs

Exact provider remaining-context metrics are optional. Never invent them.

When a provider metric is unavailable, use explicit observable signals:

- **turn_volume** — accumulated conversation/tool turns since last verified checkpoint;
- **unresolved_decisions** — unresolved/frozen decision pressure;
- **tool_activity** — number/complexity of tool executions since checkpoint;
- **checkpoint_age** — elapsed work/change volume since last verified checkpoint;
- **upcoming_risk** — external effect, migration gate, authority change or risky edit ahead;
- **manual_trigger** — user/operator asks for handoff/compact/checkpoint or execution decides a checkpoint is prudent.

A heuristic score may be recorded only when its input signals are recorded. Suggested neutral weighting for comparable runs:

`pressure = 0.20*turn_volume + 0.20*unresolved_decisions + 0.20*tool_activity + 0.15*checkpoint_age + 0.20*upcoming_risk + 0.05*manual_trigger`

Each normalized input is 0..1. This score is advisory, not provider telemetry.

## Triggers

- **manual trigger** — checkpoint immediately; score may remain null and `pressure_basis=MANUAL_TRIGGER`.
- **pressure >= 0.65** — checkpoint + compact before additional risky work.
- **pressure 0.50..0.64** — checkpoint before next major tool/migration batch.
- **authority/external-effect/rollback uncertainty** — checkpoint before continuing regardless of score.

## Checkpoint rules

The manifest stores references, not copies of business truth or workflow journals. It must include every minimum field in `project-state-manifest.schema.json`.

Before compaction:
1. seal a content hash;
2. ensure authority refs and active external effects are current;
3. record current migration gate + rollback point;
4. include prohibited actions;
5. include explicit resume instructions.

## Compaction rules

Compaction may reduce only conversational working context:
- de-duplicate bounded working-set references;
- retain only recent observational chatter where older observations are already represented by durable evidence;
- preserve exact Project State fields outside `context`.

It must not silently rewrite:
- current goal;
- frozen decisions;
- active tasks;
- blockers;
- authorities;
- active external effects;
- artifact/document refs;
- migration phase/gate;
- rollback point;
- prohibited actions.

## Post-Compaction Verification

Run `vf_office_v2_continuity.py verify` against the pre- and post-compaction manifests.

- `PASS` — exact critical state preserved.
- `PASS_WITH_WARNINGS` — no critical mismatch, but noncritical reference drift needs attention.
- `FAIL_CLOSED` — critical state mismatch; do not start new external effects.

Authority, active external effect, rollback or prohibited-action mismatch explicitly blocks new external effects until resolved.

## Resume

Resume from the newest sealed checkpoint only after verifier PASS/PASS_WITH_WARNINGS is understood. A new chat/session must read:
1. authoritative START HERE/plan reference;
2. Project State Manifest;
3. verifier receipt;
4. Production Capability Manifest;
5. current Migration Ledger/Console report.

The chat transcript itself is not the source of truth for project continuation.
