---
name: vf-living-studio
description: VelvetOS Living Studio connective tissue — World Model, Studio Pulse, Universal Intake, Skills registry, Invisible Work, Failure Museum. Use for living studio, world model, studio pulse, universal intake, skill route, capability unification, or commissioning.
---

# Living Studio

## Pack

- Layer: `packages/velvetos/living-studio/`
- Registry: `REGISTRY.json` (22 Skills + Living capabilities)
- CLI: `python3 scripts/vf_living_studio.py`
- Sensor: `python3 scripts/check-living-studio.py`

## Do this

1. Read `office/control-plane.json` — SoTs stay canonical.
2. Prefer existing pack routes from `REGISTRY.json` over new subsystems.
3. `world-model` / `pulse` / `signal-room` are projections — not databases.
4. `intake` classifies + routes + receipt into existing SoTs.
5. Brand Voice → `velvet-hebrew-copy` / `vf-hebrew-copy`.
6. After edits: `python3 scripts/check-living-studio.py` then `check-all.py`.

## Do not

- Create a second Control Plane, media catalog, decision journal, or handoff store
- Invent ₪ / Insights / liveVerified
- Resume paused routines without owner
- Auto-DM / boost / Print from HQ
- Mark implemented because a markdown file exists — require behavioral tests
