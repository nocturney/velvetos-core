# PBR and material authoring

- Resolve the destination shading model before authoring. Prefer a standard interoperable model such as the target application's supported PBR/OpenPBR workflow when appropriate.
- Keep base color free from baked lighting unless the destination workflow explicitly expects it.
- Treat roughness/metalness/normal/height and other utility channels as data with the target color-space handling.
- For tangent-space normal maps, keep UVs and tangent basis consistent across bake and render. Confirm normal convention at export/import.
- Build large-scale material response before micro-detail. Layer wear, dust, edge effects and surface variation only when they support the real material/story.
- Avoid generator-driven sameness. Use baked curvature/AO as inputs, not as excuses for uniform procedural edge wear everywhere.
- Preserve graph/source editability when Designer or another procedural source is the material master.