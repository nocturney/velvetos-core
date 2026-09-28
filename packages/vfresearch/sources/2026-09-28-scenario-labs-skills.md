# scenario-labs/skills — capability extraction review — 2026-09-28

Source: https://github.com/scenario-labs/skills  
Reviewed release: `skills-v0.48.0` (2026-09-26)  
Reviewed commit: `9624e295fa33168bc1be22a628c23ba132d1c959`  
License: MIT.

## Owner decision

Adopt the **capabilities**, not the Scenario product.

No Scenario MCP, subscription, credits, asset store, team administration or Scenario Quality
Gate is introduced. No new provider is added merely because the upstream repository
documents it.

## Embedded now

### 3D / fabrication

Mapped into the existing `vfprod` + `expert-3d-model` path:

- staged expert Blender loop: numeric brief -> stage -> measurable audit + multi-view review
  -> targeted repair -> evidence;
- specialist routing vocabulary for hard surface, sculpting, retopology, UV/baking,
  texturing/shading, lighting/rendering, Geometry Nodes, rigging, animation, previs,
  hair and Grease Pencil;
- AI-mesh-finishing discipline: generated mesh is a candidate; audit/repair/retopo before
  production or print claims;
- provider-neutral print-prep checks distilled from the ZBrush print workflow: units,
  manifold/self-intersection, profile-bound walls/clearance, splits/build volume,
  conditional hollow/drain review, export units and slicer dry-run.

Executable local planner: `scripts/vf_blender_expert.py`.
The 15 MIT Blender helper scripts are vendored locally under
`packages/vfprod/third_party/scenario-labs/blender/`; upstream SKILL/reference Markdown stays
research evidence only and is not imported as VelvetOS policy/authority.

3D AI Studio remains the existing external AI mesh capability, including models it exposes
such as Meshy/Tripo. Scenario 3D/model-family wrappers are therefore redundant and not
installed.

### Creative / Instagram

Mapped into the existing `vfom` Visual Foundry and `vf-content-sprint`:

- real-product-first product-shot discipline;
- fidelity inventory before edit;
- rubric before generation/edit;
- baseline + one bounded delta;
- never promote a drifted output to identity baseline;
- cheapest targeted repair per failure class;
- existing bounded identity/creative retry limits;
- freeze file-backed MASTER before derivatives;
- format adaptation as derivation from MASTER;
- deterministic text/brand overlays last;
- provider comparison only on normalized inputs/rubric;
- storyboard/video-ad/assembly/caption principles routed through existing
  HyperFrames/FFmpeg/video tooling.

Velvet Product Truth is stricter than the upstream generic consistency guidance: STYLE
references stay comparison-only for the Native Product Edit route and are not sent as
conditioning inputs.

## Explicitly skipped

- Scenario MCP/core loop and Scenario-specific upload/run/wait/download calls;
- paid/cloud Scenario image, video, audio and 3D model families;
- Scenario Quality Gate / Enterprise scoring;
- team/admin/usage/budget tools;
- workflow/app publishing into Scenario;
- model IDs, prices and plan assumptions;
- duplicate Meshy/Tripo/Rodin/Sparc3D routes where the existing provider stack already
  covers the need;
- Maya/Unreal/Unity runtime installation without a real current VelvetOS use case.

## Update policy

Register this repository in `packages/vfresearch/LINKS.json` and re-review upstream changes
through the existing weekly source pass. Upstream changes are candidates for grafting, not
automatic runtime updates. VelvetOS authority and acceptance tests remain the release gate.
