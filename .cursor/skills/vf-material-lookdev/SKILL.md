---
name: vf-material-lookdev
description: Apply professional material authoring, UV-to-bake, PBR/OpenPBR, texture QA and material-response lookdev across Substance Painter, Substance Designer and related local DCC/render workflows. Use for high-to-low baking, mesh-map diagnosis, material authoring, texture-set cleanup, shader/export preparation, neutral material validation or lookdev verification. Product camera, hero lighting, reflection shaping and set presentation belong to vf-product-visualization-craft. Preserve existing Substance/DCC execution adapters and never add cloud spend or a second runtime. Use only when explicitly routed by Creative Craft, Fabrication Router, or another accepted VelvetOS pipeline for a matching task; do not auto-select this specialist from unrelated ambient context.
---

# Velvet Material Lookdev

Add material, bake and look-development craft on top of the accepted local execution stack.
Do not create a second Substance or DCC runtime.

## Workflow

1. Resolve the target renderer/application, shading model, texture convention and required outputs.
2. Read only the relevant references: `baking.md`, `pbr-authoring.md`, `openpbr.md`, `texture-pipeline-qa.md`, `product-lookdev.md`, `lookdev-qa.md`, `tool-routing.md`, and `provenance.md`. Use `product-lookdev.md` only for material-validation handoff; product presentation itself routes to `vf-product-visualization-craft`.
3. Validate the low/high mesh relationship and UV state before spending time on material authoring.
4. Bake utility maps, inspect them individually, repair projection/setup defects, then build materials.
5. Verify material response under more than one useful lighting condition and against the target export convention.
6. Re-open or re-import the exported textures/material package when possible before sign-off.

## Core rules

- Treat baking errors as geometry/projection/setup problems first; do not hide them with paint unless the repair is intentionally local and documented.
- Keep data maps and color maps in the correct color interpretation for the target pipeline.
- Preserve the target normal convention and tangent basis. Do not assume OpenGL versus DirectX or another convention.
- Build material response from physical/visual intent, not from one flattering light. Hand camera, hero lighting, reflection design and set styling to `vf-product-visualization-craft` after material truth is checked.
- Use masks/generators only after the mesh maps they depend on have passed inspection.
- Keep source textures, authored graphs and exported runtime textures distinguishable.

## Hard stops

- Do not call a material physically accurate without measured/reference evidence.
- Do not claim a clean bake from the final beauty view alone.
- Do not auto-install Substance plugins, assets or cloud services from a craft task.
- Do not invent missing texture licenses or source provenance.

## Completion contract

Report: `uv_ready`, `bake_passed`, `material_authored`, `lookdev_checked`, `export_checked`, and `source_provenance_known` as separate states.
