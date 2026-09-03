# Expert — Instance onboard (multi-frontend)

Module id: `expert-instance-onboard`

## Provides

Spin-up playbook for a new VelvetOS frontend instance repo: preset → `modulesEnabled` → per-instance memory → IG channel bind → desk attach. Not a second runtime.

Playbook: `packages/velvetos/experts/INSTANCE-ONBOARD.md`. Publish: `scripts/publish-instance.sh` + `REPOS.md`.

## Packs

`velvetos`, `vfops`, `vfmem`, `vfharness`

## Specialist

`@studio-operations` · `@business-strategist` · `@workflow-architect`

## Laws

- Core = backend; business = frontend repo under `instances/` → publish
- Per-instance memory: `vfops/data/owner-memory-<instance-id>.md` (not secrets)
- No invented ₪ / Insights / Origin slugs

Always present in core. An instance enables it via `modulesEnabled`.
