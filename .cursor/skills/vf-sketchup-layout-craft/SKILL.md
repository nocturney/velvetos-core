---
name: vf-sketchup-layout-craft
description: Apply professional SketchUp 2026 and LayOut spatial-modeling and drawing-set practice for rooms, workshops, booths, racks, furniture, staging, architectural-style layouts and documentation. Use for SketchUp model organization, components/groups, tags/scenes, LayOut viewports, dimensions, title blocks, drawing sets or model-reference QA. Execution must use an accepted local integration when available; do not pretend a live adapter exists when it does not.
---

# Velvet SketchUp + LayOut Craft

Use SketchUp for spatial/design intent and LayOut for associative documentation. Do not treat it as a replacement for manufacturing CAD when exact parametric engineering masters are required.

## Workflow

1. Resolve units, real-world scale, deliverable type and whether the model is conceptual, fabrication-adjacent or documentation-only.
2. Read `model-structure.md`, `scenes-tags.md`, `layout-docs.md`, `verification.md`, and `tool-routing.md` as relevant.
3. Build reusable objects as groups/components and keep raw geometry from unintentionally sticking across logical parts.
4. Use scenes/tags to control documented views rather than duplicating geometry for each sheet.
5. In LayOut, keep viewports linked to the SketchUp model and verify references before export.

## Hard stops

- Do not claim manufacturing tolerances or fit from a spatial SketchUp model unless independently dimensioned/verified for that purpose.
- Do not explode or unlink associative documentation without a documented reason.
- Do not invent room/site dimensions.
- Do not claim live Ruby/automation execution unless an accepted integration is available at runtime.

## Completion contract

Report `model_scale_verified`, `structure_checked`, `scenes_tags_checked`, `layout_references_current`, `dimensions_checked`, `drawing_set_exported` separately.