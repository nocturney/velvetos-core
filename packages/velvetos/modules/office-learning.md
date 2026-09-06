# Office — continual learning

Module id: `office-learning`

## Provides

Living office culture: every specialist reviews the day's conversations, promotes durable facts to shared memory, and improves tomorrow's routing. **Not** a second runtime or auto-DM.

Playbooks:

- Lead ritual: `packages/vfops/hq/DAILY-RETRO.md`
- Memory writes: `packages/vfmem/MEMORY-UPDATE.md`
- Mastery + layers: `packages/vfops/hq/MASTERY-MEMORY.md` (DeepTutor pattern — no second runtime)
- Harness loop: `packages/vfharness/playbooks/daily-learning.md`
- Skill: `.cursor/skills/vf-daily-learning/SKILL.md`

## Packs

`vfops`, `vfmem`, `vfharness`, `vfgraft`

## Specialist

`@chief-of-staff` · `@studio-operations` · `@workflow-architect`

## Laws

- Guides (`AGENTS.md`, pack `SKILL.md`) = what should happen
- Checkpoints (`vfharness/state/`) = what happened in a task
- Shared memory (`vfmem` routes, `vfgraft` graph, `vfops/data/owner-memory.md`) = what everyone inherits
- No secrets, PHI, or personal folders in promoted memory
- Learning ≠ inventing ₪, Insights, or blocked bodies
- Corrections / failures / better approaches trigger same-day promote (self-improving pattern — no second runtime). See `DAILY-RETRO.md` triggers + bi-daily `vfresearch/BEST-SKILLS.md`
- Deeper durable lessons (optional numbered records): `vfops/hq/LEARNING-RECORDS.md` (teach pattern from mattpocock — no second teaching runtime)

Always present in core. An instance enables it via `modulesEnabled`.
