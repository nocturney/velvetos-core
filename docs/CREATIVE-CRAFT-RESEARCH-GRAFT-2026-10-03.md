# Creative Craft Research Graft — 2026-10-03

Status: IMPLEMENTED_PENDING_FINAL_VALIDATION
Scope: fold the high-value creative craft researched in the owner conversation into the already-accepted VelvetOS specialist Skills without creating duplicate routers or foreign runtimes.

## Architecture decision

The research originally produced many candidate Skill names. The active repository already has a cleaner specialist layer, so the implementation grafts the useful professional method into six existing Skills rather than installing 20–30 overlapping third-party Skills.

External Skills are knowledge/provenance sources only unless separately accepted as execution surfaces. Existing VelvetOS adapters, typed tools, authority boundaries, Update Sentinel and Creative Craft remain authoritative.

## Grafted into vf-cad-design-craft

- Industrial/product design methodology from shawnlix/claude-product-designer-skill -> references/product-design.md.
- Fusion Form/T-Spline and surface-development craft -> references/fusion-form-surfacing.md.
- Constraint/generative exploration discipline -> references/fusion-generative.md.
- Foster1202/cad-modeling-fusion-skill contributes MIT-licensed parametric/manufacturing patterns without replacing the accepted Fusion provider.
- Product design keeps brief -> divergence -> orthographic form -> cavity/ergonomics -> mechanism feasibility -> neutral form -> CMF discipline.
- Numeric fit, ergonomic, structural and DFM claims remain evidence-driven; no imported magic numbers become policy.

## Grafted into vf-dcc-modeling-craft

- Grounded prop/object design from arjun988/blender-skills -> references/prop-object-design.md.
- Scenario Labs ZBrush core sculpt craft -> references/zbrush-sculpting.md.
- Scenario character/creature + stylized collectible reasoning -> references/character-creature-stylized.md.
- Meshmixer bounded repair/surgery craft -> references/meshmixer-surgery.md.

- The Scenario execution scripts are not adopted; only senior-form, anatomy, stylization and review methods are paraphrased.
- Pose/print ideas are folded selectively into collectible craft and handed to canonical Fabrication/DfAM for actual print constraints.

## Grafted into vf-material-lookdev

- Blender lookdev and set-dressing discipline from arjun988/blender-skills.
- Scenario Maya lookdev/lighting principles where they generalize safely beyond Maya execution.
- Product photography/visualization thinking -> references/product-lookdev.md.
- Neutral clay, one-variable iteration, scale-aware shading, reflection design, restrained imperfection, hero/detail/context sequencing and controlled set dressing are now explicit.

## Grafted into vf-post-production-craft

- Cinematography craft from fal-ai-community plus Blender camera-language research -> references/cinematography.md.
- LottieFiles motion-design philosophy -> references/motion-direction.md.
- SkillMedev kinetic typography -> references/kinetic-typography.md.
- Topaz Video preservation/restoration/creative reasoning -> references/video-restoration.md.
- Existing Resolve editing/color/Fusion/Fairlight craft remains and is now complemented by shot language, motion direction and restoration QA.
- External model/provider routing is removed; current accepted local Resolve/AE/Premiere/Fusion/Topaz/HyperFrames surfaces remain execution authority.
- Hard numeric timing/model choices are heuristics only and must be checked against the current project/runtime.

## Grafted into vf-image-design-craft

- SkillMedev Moodboard Builder -> references/moodboard-art-direction.md.
- Pulse Community Agency Illustrator logo construction/QA -> references/vector-identity.md.
- Affinity-oriented mixed-media/editorial craft -> references/mixed-media-editorial.md.

- Art direction now distinguishes emotional target, inspiration vs execution references and an explicit anti-board.
- Vector identity now emphasizes primitive construction, negative space, optical alignment, canonical geometry and multi-size/export QA.
- Mixed-media/editorial guidance keeps vector/raster/photo/type editable and uses grid, hierarchy and page rhythm rather than ad-hoc collage.

## Grafted into vf-technical-illustration-craft

- Corel DESIGNER / CorelDRAW Technical Suite publication practice -> references/technical-publication.md.
- Existing exploded/projection/callout craft remains authoritative for illustration.
- New publication guidance covers multi-step assembly/service sheets, source revision continuity, parts/BOM mapping, view consistency and exact-output verification.

## Tool-to-specialist registry binding added

- Autodesk Fusion -> vf-cad-design-craft.
- Autodesk Meshmixer -> vf-dcc-modeling-craft.
- DaVinci Resolve Studio -> vf-post-production-craft.
- Topaz Video -> vf-post-production-craft.
- Affinity -> vf-image-design-craft.
- CorelDRAW -> vf-image-design-craft + vf-prepress-qa.
- Corel DESIGNER -> vf-technical-illustration-craft.

The same registry changes were applied to source and D:\Velvet\Runtime\CreativeCraft\creative-craft-registry.json so runtime/source do not intentionally diverge.

## Intentionally merged rather than separate Skills

- product-photography -> product-lookdev + cinematography.
- set-dressing -> product-lookdev.
- camera-cinematography -> cinematography.
- motion-color/light -> existing color craft + motion-direction.
- Maya lookdev/lighting -> vf-material-lookdev + existing post/DCC craft.
- ZBrush pose/print -> character/stylized craft + canonical Fabrication/DfAM.
- editorial-layout-design -> mixed-media-editorial.
- exploded-assembly-communication + technical-publication-graphics -> vf-technical-illustration-craft.

## Intentionally not adopted as separate production Skills

- Whole external Blender/Scenario/Adobe packs: SKIP wholesale; avoid duplicate runtimes, triggers and conflicting authority.
- Generic character/creature Blender Skills: SKIP as separate authority; Scenario-derived craft is deeper and consolidated locally.
- Generic fusion360-expert/persona packs: SKIP as-is; retain only evidence-backed patterns.
- Web/frontend typography-system: SKIP as-is; it is not the right authority for Illustrator/Affinity/AE craft.
- External cloud/model routing from fal, Nano Banana or Topaz Platform: not adopted by this graft.
- Arbitrary Python/COM/eval/MCP escape hatches: remain blocked by current typed-surface policy.

## Explicit current exclusion

Topaz Gigapixel is excluded by the latest accepted Creative Craft scope and MUST NOT be recreated or made routable by this implementation. Earlier conversation research about a possible image-upscale Skill is historical only. Existing conservative raster resampling/source-fidelity guidance remains in vf-image-design-craft.

## Sources / license notes

- shawnlix/claude-product-designer-skill — MIT.
- Foster1202/cad-modeling-fusion-skill — MIT.
- arjun988/blender-skills — MIT.
- scenario-labs/skills — MIT.
- SkillMedev/skills — MIT.
- LottieFiles/motion-design-skill — MIT.
- Pulse-Community-Agency/adobe-illustrator-logo-designer — MIT.
- fal-ai-community/skills — MIT.
- calesthio/generative-media-skills — MIT.
- samuelgursky/davinci-resolve-mcp — MIT.
- aedev-tools/adobe-agent-skills — Apache-2.0 patterns already referenced by post craft.

All imported knowledge is paraphrased/condensed into local references; foreign execution scripts/runtimes were not copied by this graft.

## Validation target

The implementation is complete only after:
- all six updated Skills pass repository skill health/structure checks;
- every referenced local file exists;
- source/runtime Creative Craft registry copies match;
- Creative Craft/router/tool-authority checks pass;
- full repository check-all returns the accepted baseline without hiding Maya fail-closed state;
- no push/merge occurs without a fresh owner authorization.
