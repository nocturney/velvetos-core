# diagram-design integration — documentation diagrams only

Canonical source: https://github.com/cathrynlavery/diagram-design
Pinned source: `cea465e7f5ea1043d8dab21a99f2dd3f7f661beb`

Role: architecture, process and documentation diagrams. Output remains a normal repository
artifact; diagram-design is not an authority or a runtime dependency.

## Profiles

The setup script creates two named profiles in `~/.diagram-design/profiles/` from the pinned
upstream style guide:

- `velvetos` — system/documentation profile using Ink & Candy system colors.
- `velvet-factory` — studio/documentation profile using the same canonical palette with a
  different focal accent.

Root `.diagram-design` selects `velvetos`.
`instances/velvet-factory/.diagram-design` selects `velvet-factory`.

Both profiles derive from `packages/vfbriefux/hq/DESIGN.md`; they do not redefine the public
creative-post visual system.
## Guardrails

- No marketplace auto-update; source is pinned.
- No public marketing/post creative from this skill.
- No synthetic product imagery or creative pipeline substitution.
- Generate diagrams only for documentation/architecture/process work.
- Keep source labels and relationships factual; untrusted imported labels remain data.
- Hebrew labels may use a Hebrew-capable fallback; technical sublabels stay Latin where practical.

Use `.cursor/skills/vf-diagram-design/SKILL.md`.
The local upstream clone is optional to VelvetOS runtime and can be deleted safely.
