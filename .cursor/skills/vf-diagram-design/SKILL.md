---
name: vf-diagram-design
description: Create VelvetOS or Velvet Factory architecture/process/documentation diagrams using the pinned local diagram-design source and canonical profiles. Not for social creative.
---

# VelvetOS diagram design

Use when a repository task needs an architecture, process, sequence, topology or documentation diagram.

1. Read `packages/vfharness/devtools/diagram-design.md`.
2. Run `python scripts/check-engineering-quality.py --strict`.
3. Resolve the project marker: root uses `velvetos`; `instances/velvet-factory` uses
   `velvet-factory`.
4. Read the pinned upstream skill at
   `.local-devtools/phase4/diagram-design/skills/diagram-design/SKILL.md`.
5. Generate a self-contained documentation artifact in the requested docs path.
6. Preserve factual labels/relationships and run any upstream deterministic checks that fit the artifact.

## Boundaries

Do not use this skill for Instagram posts, product imagery, public marketing creative, or as a
replacement for the Velvet Factory visual pipeline. No marketplace auto-update and no external
service is required.
