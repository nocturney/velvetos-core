# Scenario Labs capability graft — VelvetOS-native

Status: **INTEGRATED KNOWLEDGE / LOCAL EXECUTION ONLY**  
Upstream: `scenario-labs/skills` · release `skills-v0.48.0` · commit `9624e295fa33168bc1be22a628c23ba132d1c959` · MIT.

This file records the capabilities adopted from the open repository. VelvetOS does **not**
adopt Scenario as a product, runtime, MCP dependency, asset store, billing surface, quality
authority or provider router.

## Authority

The existing VelvetOS routes remain authoritative:

- fabrication choice: `scripts/vf_fabrication_router.py`;
- 3D engine choice: `scripts/vf_3d.py`;
- Blender execution/readiness: `packages/vfprod/BLENDER-MCP.md`;
- engineering master: STEP/B-rep when the routed task requires parametric CAD;
- external AI mesh provider: existing approved capability such as 3D AI Studio, subject to
  the existing cost/license gate;
- slicer: existing `vf_cad.py` / printer matrix dry-run;
- physical printer control: never authorized from HQ.

Exact upstream or local versions are provenance only. Runtime acceptance stays capability-based.

## Adopted Blender expert protocol

The reusable expert loop is now mandatory for `BLENDER_NATIVE` work:

1. turn the brief into measurable requirements and explicit unknowns;
2. lock source/reference evidence before geometry changes;
3. choose only the specialist domains actually needed;
4. build one stage;
5. run measurable mesh/domain checks **and** render a multi-view review sheet;
6. inspect the review artifact, not only command exit codes;
7. repair failed regions before advancing;
8. freeze/export only after the final audit;
9. for printable work, continue through print-prep gates and the existing slicer dry-run.

Executable planning helper:

```bash
python scripts/vf_blender_expert.py capabilities
python scripts/vf_blender_expert.py plan --request "<resolved request>"
```

The helper is provider-neutral. It never calls Scenario, never spends credits and never
controls a printer.

### Specialist capability set

The upstream family contributes a router protocol plus twelve specialist areas:

- hard-surface;
- sculpting;
- retopology;
- UV/baking;
- texturing/shading;
- lighting/rendering;
- Geometry Nodes;
- rigging;
- animation;
- previs/storyboard;
- hair;
- Grease Pencil.

Headless execution is preferred where the installed Blender supports it. Real sculpt/paint
brush strokes and some hair/Grease Pencil strokes may require an already-running live GUI
bridge. This is a capability distinction, not a Blender-version allowlist.

## AI mesh finishing

An AI-generated mesh is a **candidate**, never a printable or production-ready conclusion.

For an existing 3D AI Studio result (including a Meshy/Tripo-family result exposed through
that existing capability):

`provider result -> local file + provenance -> Blender audit -> repair/retopo as needed ->
UV/bake/material work as needed -> final geometry audit -> STL/3MF sidecars -> existing
DfAM/slicer dry-run`.

Do not add Scenario 3D, Meshy, Tripo, Rodin or another cloud account merely because an
upstream skill names it. The existing provider route wins unless a separate approved gap
justifies another provider.

## Provider-neutral print-prep knowledge

The useful print-prep ideas from the upstream ZBrush print specialist are normalized here
without making ZBrush a dependency:

- establish real units and final envelope before detail;
- inspect manifoldness, open boundaries, duplicates and self-intersections;
- evaluate minimum feature/wall thickness against the **actual process/printer/material
  profile**, not a copied universal number;
- evaluate mating clearance against the actual process/profile when parts must fit;
- check build volume and plan splits/keys at sensible boundaries;
- hollow/drain/trapped-volume review only when the process and job require it;
- verify exported part names, dimensions and units;
- keep an editable master plus STL/3MF sidecars;
- finish with the existing slicer dry-run and clearly separate digital evidence from a
  physical fit/print proof.

Numbers quoted in tutorials or vendor examples are calibration examples, not VelvetOS laws.

## Upstream capabilities deliberately not adopted as runtime

The following stay outside the runtime:

- Scenario MCP, OAuth/API keys, credits, storage, team administration and workflows;
- Scenario Quality Gate as an authority;
- Scenario cloud image/video/audio/3D model families;
- Scenario-specific model IDs, prices and plan tiers;
- a second DCC/router/catalog/queue;
- paid-provider failover by convenience.

Maya/Unreal/Unity expert families remain source material only until a real VelvetOS task
needs those DCCs and the local capability is installed and acceptance-tested.

## License/provenance

The source repository is MIT licensed. The upstream license text is retained at
`packages/vfprod/third_party/scenario-labs/LICENSE`. The 15 reusable Blender Python helpers
are vendored under `packages/vfprod/third_party/scenario-labs/blender/` and indexed by
`VENDOR-MANIFEST.json`; upstream normative Markdown is deliberately not vendored as an
authority. VelvetOS uses the adapted contracts in this file and the existing route/QA laws.
