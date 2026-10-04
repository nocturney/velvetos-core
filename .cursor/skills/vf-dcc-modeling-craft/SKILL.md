---
name: vf-dcc-modeling-craft
description: Apply professional polygon, prop/object design, sculpt, character/creature, stylized collectible, retopology, subdivision, UV and mesh-surgery QA practice across Blender, Maya, 3ds Max, ZBrush and Meshmixer using the existing VelvetOS DCC execution adapters. Use for organic or hard-surface modeling, grounded props/products, sculpt-to-production workflows, character or creature form, stylized collectibles, deformation-ready topology, UV readiness, bake preparation, mesh repair/surgery or DCC geometry review. Preserve vf-3d-router and accepted host/runtime boundaries. Use only when explicitly routed by Creative Craft, Fabrication Router, or another accepted VelvetOS pipeline for a matching task; do not auto-select this specialist from unrelated ambient context.
---

# Velvet DCC Modeling Craft

For VelvetOS production/fabrication work, enter through the mandatory Fabrication Router first. Supply modeling craft and QA only after it delegates to `vf-3d-router` and that router selects a DCC route. Do not replace either router or install another Blender/Maya/Max/ZBrush runtime.

## Workflow

1. Classify the target as static, deforming, subdivision, sculptural, bake source, bake target or print mesh. More than one class may apply.
2. Read the relevant references: `prop-object-design.md`, `zbrush-sculpting.md`, `character-creature-stylized.md`, `anatomy-likeness-qa.md`, `meshmixer-surgery.md`, `topology-retopo.md`, `subdivision-sculpt.md`, `uv-bake-readiness.md`, `bake-diagnostics.md`, `asset-review-qa.md`, `tool-routing.md`, and `verification.md`.
3. Establish protected silhouette, proportions, interfaces and source/reference constraints before topology cleanup.
4. Use the simplest topology that satisfies the downstream requirement. Do not maximize quad count or density without purpose.
5. Run visual and structural checks on the actual exported artifact, not only the live scene.

## Core rules

- Preserve silhouette and functional geometry before local topology aesthetics.
- For deforming assets, place edge flow around expected deformation and keep avoidable poles/irregular valence away from critical bending regions.
- Treat automatic remesh/retopo as a starting point unless the downstream use proves it sufficient. Blender documentation explicitly notes that automatic remeshing generally does not produce deformation-ready topology.
- Freeze or explicitly account for transforms, normals, smoothing and modifiers before an export/bake step that depends on them.
- Separate sculpt/detail density from production topology density.
- Keep UV/bake requirements tied to the target renderer/material pipeline rather than one DCC application's defaults.

## Hard stops

- Do not claim deformation-ready topology from appearance alone.
- Do not claim a clean bake without inspecting the baked maps.
- Do not silently change protected dimensions when retopologizing or sculpting a functional part.
- Do not treat non-manifold repair as proof of printability.
- Do not add a second DCC MCP or weaken accepted host integrity controls.

## Completion contract

Report the applicable states separately: `form_locked`, `topology_checked`, `deformation_checked`, `uv_checked`, `bake_ready`, `export_checked`, `print_geometry_checked`.
