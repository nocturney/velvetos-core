# Creative Craft specialist authoring standard

Use this standard for every new Creative Craft specialist and for significant edits to an existing specialist.

## Control-plane contract

- Trigger on domain/task intent, not only a tool or application name.
- Keep SKILL.md concise: routing boundary, workflow, hard stops, completion contract, and direct reference links.
- Put deep doctrine in one-level `references/` files. Every referenced file must exist.
- Keep craft doctrine, tool routing, execution authority, and verification as separate concerns.
- A craft Skill may choose methods and QA; it may not grant itself a new runtime, arbitrary scripting surface, cloud spend, publish authority, printer control, or Product/Engineering Truth.
- Preserve upstream authorities such as Fabrication Router, vf-3d-router, vfom/Creative Director, Update Sentinel, typed adapters, and review/publish gates.
- State the owning boundary and the handoff boundary when neighboring specialists overlap.
- Preserve a job-owned editable master and source lineage when the domain supports it.

## Reference quality

- Every reference must provide non-obvious decision, diagnostic, critique, or verification value.
- Prefer locally authored doctrine distilled from verified sources over vendoring third-party prose.
- Record external provenance/license status in the specialist provenance reference.
- For unlicensed, ambiguous, vendor-copyright, forum, book, course, or standard-derived material: paraphrase concepts only and never copy figures/assets/tables.
- Do not copy paywalled ISO/ASME or other controlled standards language.
- Fixtures should be locally generated or CC0 where practical; record source/license/hash/version for every external fixture.

## Numeric discipline

- Never turn a source-specific number into a universal rule.
- A hard threshold must name its source, scope, version/date, and override authority.
- Manufacturing values remain process/material/machine/geometry dependent.
- Human-factor values remain population/task/context dependent.
- Broadcast/streaming/color/delivery values remain destination/version dependent.
- When primary evidence is absent, keep the value unresolved instead of inventing a safe-looking default.

## Produce -> critique -> refine

1. Define acceptance dimensions before production.
2. Produce the simplest artifact/state that tests the intended direction.
3. Critique as: observation -> likely cause -> corrective action -> verification.
4. Test the defect at the level where it occurs: geometry, UV, material, color, frame sequence, vector, PDF, or G-code.
5. Use neutral diagnostics before beauty conditions when presentation can hide a defect.
6. Capture worst/stress cases, not only representative frames.
7. Refine only the failed dimensions; do not destabilize already-passing constraints.
8. Re-open/read back the exact output and bind evidence to source revision/tool version/hash when available.

## Eval requirement

A significant Skill change requires at least one matching eval case. Compare the accepted baseline and candidate with the same brief and evidence. Record criterion-level deltas and negative-control results. Keep a graft only when its targeted criteria improve without authority, safety, context-size, trigger, or regression degradation.

## Red flags

Stop and re-check when a source license is unclear, a new dependency appears, a hard number lacks scope, two specialists claim the same decision authority, an execution example bypasses a typed surface, a successful tool call is being treated as artifact proof, or a quality improvement changes protected product/engineering/source truth.
