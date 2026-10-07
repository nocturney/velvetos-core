# Office — continual learning

Module id: `office-learning`

## Provides

Living office culture: learning is scoped to seats/domains that actually changed or received new evidence. Participating specialists capture meaningful observations/candidates and promote only evidence-gated durable facts; untouched seats do not run an empty daily ritual. **Not** a second runtime, second memory store, auto-DM, or daily promotion quota.

Playbooks:

- Lead ritual: `packages/vfops/hq/DAILY-RETRO.md`
- Retro → signal: `packages/vfops/hq/RETRO-SIGNALS.md` + `scripts/vf_retro_signals.py`
- Memory writes: `packages/vfmem/MEMORY-UPDATE.md`
- Mastery + layers: `packages/vfops/hq/MASTERY-MEMORY.md` (DeepTutor pattern — no second runtime)
- Harness loop: `packages/vfharness/playbooks/daily-learning.md`
- Skill: `.cursor/skills/vf-daily-learning/SKILL.md`
- SoC ADR: `packages/velvetos/ADR-THREE-LAYERS.md`

## Packs

`vfops`, `vfmem`, `vfharness`, `vfgraft`

## Specialist

`@chief-of-staff` · `@studio-operations` · `@workflow-architect`

## Laws

- Guides (`AGENTS.md`, pack `SKILL.md`) = what should happen
- Checkpoints (`vfharness/state/`) = what happened in a task
- `office-learning` = lifecycle/process owner only; it stores no durable fact. `vfmem` routes/verifies canonical memory, `owner-memory.md` owns durable owner-specific facts, and domain SoTs own promoted policy/pattern truth.
- No secrets, PHI, or personal folders in promoted memory
- Learning ≠ inventing ₪, Insights, or blocked bodies
- Corrections / failures / better approaches trigger same-day **capture/triage**, not automatic promotion. A same-day promotion is allowed only when the existing destination gate is already satisfied (for example an explicit owner correction plus canonical verification). See `DAILY-RETRO.md` and `packages/vfharness/playbooks/learning-lifecycle.md`.
- Deeper durable lessons (optional numbered records): `vfops/hq/LEARNING-RECORDS.md` (teach pattern from mattpocock — no second teaching runtime)

Always present in core. An instance enables it via `modulesEnabled`.
