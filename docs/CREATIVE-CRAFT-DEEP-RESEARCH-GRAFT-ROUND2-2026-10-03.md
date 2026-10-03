# Creative Craft deep research graft — round 2 — 2026-10-03

## Decision
The second research round augments the already-implemented craft baseline. It does not replace the first round and does not create new specialist Skills.

Architecture remains:
- creative-craft = routing + cross-domain QA protocol
- vf-cad-design-craft = product/CAD/form authority
- vf-dcc-modeling-craft = mesh/sculpt/topology authority
- vf-material-lookdev = material/optical/product-visualization authority
- vf-post-production-craft = editorial/cine/color/comp/motion/restoration authority
- vf-image-design-craft = 2D/art-direction/vector/typography authority
- vf-technical-illustration-craft = technical communication authority
- vf-fabrication-craft and vf-prepress-qa remain local/core authorities

## Verified research sources used
- AcademySoftwareFoundation/OpenPBR — Apache-2.0; v1.1.1 (2026-04-17).
- AcademySoftwareFoundation/OpenColorIO-Config-ACES — BSD-3-Clause; project version 4.0.0.
- Netflix/vmaf — BSD-2-Clause-Patent; objective media-QA component only.
- iart-ai/motion-design-skills — MIT; motion language/restraint/consistency patterns.
- dcc-mcp/dcc-texture-pipeline — MIT; deterministic OIIO/OCIO texture-pipeline QA.
- beiming183-cloud/industrial-product-design-gbt — MIT; design-DNA, maturity gates, evidence authority and TBD discipline.
- Autodesk University Reliable Modeling — copyrighted training; paraphrase/cite only.
- CompStart Lensing/Tech Check — public craft reference; no reusable license verified, paraphrase/cite only.

## New/expanded references
- creative-craft/references/creative-qa-engineering.md
- vf-cad-design-craft: design-gates.md, robust-parametric-modeling.md, surface-quality-qa.md
- vf-dcc-modeling-craft: asset-review-qa.md
- vf-material-lookdev: openpbr.md, texture-pipeline-qa.md
- vf-post-production-craft: color-management.md, compositing-tech-check.md, media-qa.md
- vf-image-design-craft: typography-layout-qa.md
- vf-technical-illustration-craft: assembly-graphics.md
- vf-fabrication-craft: dfam-lifecycle.md
- vf-prepress-qa: color-output-qa.md

Existing references were deepened where the research added non-duplicative craft:
- topology-retopo.md
- product-lookdev.md
- editing.md
- motion-direction.md
- video-restoration.md

## Rejected secondary-source claims
Do not encode secondary-report numeric rules as standards without current primary-source confirmation. In particular:
- OpenPBR does not justify a universal 30–240 sRGB base-color clamp.
- OpenPBR does not justify a universal roughness >= 0.02 rule.
- Intermediate metalness is not universally invalid in OpenPBR.
- EBU R128 programme loudness is -23 LUFS, not -24 LUFS; destination specifications still override generic broadcast guidance.

## Deployment state
- Core/source Skill files updated.
- %USERPROFILE%\.agents\skills updated.
- D:\Velvet\Runtime\CreativeCraft\skill updated.
- Workspace distribution prepared as version 1.4.0 with 33 desired-state Skills unchanged.
- Creative Control Center reads the new references and exposes the additional expertise.
