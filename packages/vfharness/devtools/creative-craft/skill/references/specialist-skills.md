# Specialist Skills consumed by Creative Craft

Creative Craft references these Skills at the stage where their professional method is needed. It does not copy their instructions into one monolithic prompt.

| Skill | Role | Common pipelines |
| --- | --- | --- |
| `velvet-creative-director` | public creative planning authority via vfom | product image, short social, public 3D visualization, public technical explainer |
| `vf-image-design-craft` | art direction/moodboards, raster/vector identity, graphic systems, mixed-media/editorial design and export QA | product image, vector/logo/layout, visual direction |
| `vf-product-visualization-craft` | product camera/lens, studio lighting, reflection shaping, shot systems, hero/catalog/turntable presentation | 3D product visualization |
| `vf-post-production-craft` | editorial, cinematography, color, motion/kinetic type, audio, restoration and delivery craft | social, long edit, color, enhancement, derivatives |
| `vf-vfx-compositing-craft` | plate/lens setup, roto/key, tracking/matchmove, render-pass reconstruction, CG integration and VFX shot QC | vfx composite |
| `vf-speech-qa` | TTS/ASR/pronunciation/back-transcription/consent QA | narration/subtitles, social, long edit, explainer |
| `vf-technical-illustration-craft` | projection/exploded/callout/dimension/parts and technical-publication craft | technical illustration/publication/explainer |
| `vf-prepress-qa` | print/PDF exact-artifact preflight | print-bound image/vector, engineering publication |
| `vf-material-lookdev` | baking/PBR, texture/material response and material QA | PBR material, 3D/product material handoff |
| `vf-dcc-modeling-craft` | prop/object design, sculpt/character/stylized, topology/retopo/UV and mesh-surgery craft | 3D visualization, collectibles, mesh work |
| `vf-cad-design-craft` | industrial/product design, Fusion form/generative CAD, design intent, fit/tolerance, functional datums and DFM context | fabrication/CAD, product design, technical downstream context |
| `vf-sketchup-layout-craft` | spatial/associative drawing-set craft | spatial planning, publications sourced from SketchUp/LayOut |
| `vf-bom-costing` | evidenced BOM/cost tables | document/report/BOM, engineering publication when a BOM exists |

## Ownership boundaries

- Product geometry/form remains CAD/DCC truth; material response remains Material Lookdev; Product Visualization owns camera/light/reflection/set presentation only.
- VFX owns shot integration; Post owns editorial, creative color, motion/audio/restoration and final delivery.
- A host that spans domains does not merge their authority. Resolve/Fusion or After Effects availability never makes one specialist the owner of every stage.

## Embedded patterns

- Probe/read back before mutation where possible.
- Keep a job-owned editable master plus independent derivative.
- Use file-backed handoffs and SHA-256 lineage across tools.
- Inspect the exact output artifact rather than trusting a tool's success response.
- Prefer named presets/profiles and declarative specs over arbitrary arguments or scripting.
- Preserve pre-existing user sessions; stop only agent-owned GUI sessions.
- Product/engineering/source truth survives every creative stage.
- A successful render/adapter receipt never grants publish authorization.
- BOM/costing never invents prices, tax, FX, ledger facts, or approval.
