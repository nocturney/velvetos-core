# Creative Craft 2.0 source provenance matrix

Verified: 2026-10-03. This matrix governs reuse for the 2.0 craft pass. Execution authority never comes from an external craft source.

| Source | Verified revision/date | License/status | High-value scope | Runtime baggage | 2.0 reuse policy |
| --- | --- | --- | --- | --- | --- |
| sideshowroberto/vfx-agent-toolkit | 67bb588d41d02aed7efef7ad7fd84e57ae261d69; 2026-09-15 | MIT repo; some adapted material has separate origins | compositing, shot setup, render-pass and VFX QA patterns | Nuke/Maya/Blender/Houdini integrations and scripts | Paraphrase craft only; no foreign execution layer or copied scripts |
| jeremieLouvaert/ComfyUI-Prompt-Vault | 59969e74569cb05bcdfcd0b3109aaeab52755510; 2026-08-15 | MIT | photographic vocabulary, lens/light/set reasoning | prompt-library runtime not needed | Concepts only; author local product-visualization doctrine |
| google/filament | 70d2da5e9b7014e1a4207d737aa8dc41b59880a2; 2026-10-02 | Apache-2.0 | PBR semantics and renderer-aware material reasoning | Filament renderer | Concepts only; renderer-specific numeric guidance is never universal policy |
| tomana/agent_skills | 3e9aafee35c60056ca317e341d90b9fb4b793e5f; 2026-10-03 | MIT | printability checks, numeric verification, evidence-before-done | trimesh/manifold3d/Blender scripts | Selective paraphrase; keep Velvet fabrication authority and typed execution unchanged |
| NVIDIA-Omniverse/omniverse-labs | 71a7c9d5ef51039c5c1c3ea6bbe640f8d47f15d1; 2026-09-29 | repo software Apache-2.0; docs/non-software CC-BY-4.0; file headers may override | UV/material troubleshooting, audit order, USD/MaterialX handoff reasoning | Blender/OVRTX recipes and audit script | Paraphrase + attribution; do not copy scripts or ambiguous-license prose |
| damionrashford/media-os | 5014c1e8b23fd3e18d49926d9aa147d15a3aa08e; 2026-05-31 | MIT; model licenses vary | restoration stage ordering, model/license discipline, worst-frame QA | many model runtimes and wrappers | Craft/QA concepts only; no model/runtime installation or permanent model-name policy |
| calesthio/generative-media-skills | 8c85352d5d75d4dcbe58480bd138e37b9742bab1; 2026-07-14 | MIT | product-truth QA, shot direction, eval/rubric patterns | large provider-oriented skill library | Adapt evaluation/craft patterns; no provider routing or second runtime |
| Deno2026/deno-creator-skills | 007b2cfc30a392abd60925bbd48227ddafcaf393; 2026-10-02 | GPL-3.0 | editorial/post workflow patterns | Premiere kits, workflows and publishing scripts | Concept-only/paraphrase; no copied distributed content or runtime |
| magnus919/agent-skills | 54d81f7e02051df2f31130a136dc68f8add42130; 2026-09-30 | MIT; color-management skill cites third-party technical sources | color-management failure modes and scene/display-referred reasoning | ImageMagick/ArgyllCMS/LittleCMS scripts | Concepts only; keep underlying-source provenance and no new dependencies |
| scenario-labs/skills | 20a518d4d61c67b1153d0b68a4e3acd2e4e1f03d; 2026-10-03 | MIT | sculpt/modeling and production QA patterns | external execution recipes | Secondary concepts only; current Velvet DCC adapters remain authoritative |

## Public/vendor reference sources

- Foundry Nuke lens-distortion/STMap documentation: vendor-copyright documentation; paraphrase workflow concepts only.
- Blackmagic Design Resolve training: vendor-copyright training; paraphrase color/VFX craft only.
- Higgsfield DaVinci Resolve MCP/colorist material: package reports MIT, but bundled LUT/DCTL assets are excluded until asset-level rights are verified.
- Polycount Wiki: license not conclusively verified in this pass; use verified concepts only and author local doctrine.
- Deakins forum, StudioBinder and In Depth Cine: editorial/public references; paraphrase cinematography concepts only.
- Follygon, FlippedNormals, Proko and ZClassroom: commercial/public training; paraphrase anatomy/sculpt/likeness concepts only; never vendor media or course content.
- Xometry, Protolabs and GD&T Basics: public technical guidance; use function/process-aware concepts, not provider numbers as universal standards.
- NASA Human Integration Design Handbook and NASA-STD-3001 Vol. 2 Rev F (2026-07-14): public NASA sources; use task/population-scoped human-system concepts.
- DINED anthropometric database: current multi-population reference; no embedded tables until reuse rights and exact population/date/measure scope are verified.
- Carbon Design System: Apache-2.0 repository; use system-level hierarchy/token concepts, not IBM brand identity.
- Shopify Polaris: restricted/modifed reuse terms; concept-only, no copied UI assets/components.
- Butterick's Practical Typography: all-rights-reserved reference; paraphrase general typography craft only.
- Material Design: use general system principles; exact assets only when their own license is explicitly required and recorded.

## Numeric and authority policy

Any hard numeric rule must carry source, scope, version/date and override authority. Process/material/provider/destination specifications override generic craft guidance. Rejected universal rules remain rejected: no universal OpenPBR base-color clamp, no universal minimum roughness, no exactly-binary metalness rule, no universal DFM wall/draft/kerf/tolerance value, no universal anthropometric percentile, and no destination-independent codec/HDR/loudness threshold.
