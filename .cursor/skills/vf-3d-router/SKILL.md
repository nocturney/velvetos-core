---
name: vf-3d-router
description: Route and execute VelvetOS 3D modeling and print-prep work across the existing Text-to-CAD and local Blender stack. Use for creating, reconstructing, repairing, measuring, validating or preparing 3D models for printing. Select TEXT_TO_CAD for functional parametric geometry, BLENDER_NATIVE for organic/reference/mesh work, and HYBRID_CAD_THEN_BLENDER when both constraint classes matter. Preserve the existing printer authority and zero-new-recurring-cost policy.
---

# VelvetOS 3D Router

Use this skill for requests to create, modify, reconstruct, inspect, repair or prepare a 3D model.

## Authorities

Read only the relevant production authorities:
- `packages/vfprod/SKILL.md`
- `packages/vfprod/experts/3D-MODEL.md`
- `packages/vfprod/TEXT-TO-CAD.md`
- `packages/vfprod/BLENDER-MCP.md`
- `packages/vfprod/SCENARIO-EXPERT-CAPABILITIES.md` for the provider-neutral expert domain/gate graft.
- `constitution/NO_NEW_RECURRING_COST.md` when adding/changing an external component.

Do not create a second 3D pack, printer matrix, slicer router or office runtime.

## Route first

Run:

```bash
python scripts/vf_3d.py route --request "<resolved user request>"
```

Treat that result as the engine-selection contract.

When the resolved route contains Blender (`BLENDER_NATIVE` or `HYBRID_CAD_THEN_BLENDER`), also run:

```bash
python scripts/vf_blender_expert.py plan --request "<resolved user request>"
```

Use its specialist domains and gates as the execution/QA plan. It is local planning knowledge only; it never authorizes Scenario cloud, a paid provider or printer control.

- `TEXT_TO_CAD`: functional parametric parts, explicit dimensions/tolerances, holes/threads/fits, assemblies, STEP/B-rep masters.
- `BLENDER_NATIVE`: organic/sculptural form, image/reference reconstruction, mesh repair/refinement, UV/form work.
- `HYBRID_CAD_THEN_BLENDER`: build/freeze functional interfaces in CAD first; use Blender only for the non-critical form layer; re-measure protected interfaces before handoff.

## Craft layer

After engine selection, load only the craft skill that applies; these skills refine practice and QA but never change the engine-selection contract or authority boundaries:
- `TEXT_TO_CAD` or other parametric CAD work -> `.cursor/skills/vf-cad-design-craft/SKILL.md`.
- `BLENDER_NATIVE` or DCC topology/sculpt/UV work -> `.cursor/skills/vf-dcc-modeling-craft/SKILL.md`.
- `HYBRID_CAD_THEN_BLENDER` -> apply CAD craft to protected functional geometry first, then DCC craft to the non-critical form layer.
- Any UV-to-bake, Substance, PBR, texture or lookdev task -> also apply `.cursor/skills/vf-material-lookdev/SKILL.md` after geometry/UV state is established.
- Any additive print-prep, slicer calibration/profile, orientation/support or G-code review task -> apply `.cursor/skills/vf-fabrication-craft/SKILL.md` before the existing DfAM/slicer/G-code gates. It never gains printer-control authority.

The craft layer is advisory/verification knowledge only. Existing Text-to-CAD, Blender expert, DfAM, slicer, export and printer boundaries remain authoritative.

## Execute

Before live Blender execution run `python scripts/vf_3d.py doctor`.
Follow the Runtime version policy below.
For local Blender scripts, materialize the script under `VELVET_3D_JOB_ROOT` and execute through
`python scripts/vf_3d.py run-pass --script <path>`; do not bypass the script safety gate.

Use `blender-ai-mcp` as the normal bounded interactive Blender tool surface when an MCP client is available.
Launch it through `python scripts/vf_3d.py mcp-server`; that adapter locks `llm-guided`/stdio,
RPC loopback, Hugging Face offline mode, vision off and telemetry off. Resolve the RPC port
from the installed hardened addon instead of assuming a release-specific value.
Prefer macro/workflow tools plus deterministic measure/assert tools over raw Python.
Use `design-os-3d-blender` for headless passes and production geometry gates.

## Runtime version policy

Use the tools actually installed on the host. Do not hard-code or allowlist a Blender,
blender-ai-mcp, design-os, Text-to-CAD or slicer version/commit. Treat exact versions,
source revisions, hashes and paths as receipt provenance only.

Run `python scripts/vf_3d.py doctor` to discover the selected installed Blender and verify
that the addon exists and is enabled in that same installation. A component receipt is
current only when its recorded version matches the locally installed version. After an
upgrade, refresh acceptance evidence before a release/acceptance claim. Runtime discovery
may proceed when live capability checks pass; stale historical evidence is not a version ban.

OrcaSlicer selection is dynamic through `vf_cad.py`; `ORCASLICER_BIN` is an explicit
override and matrix executable/version fields are hints, not runtime pins.

For a printable Blender result, run the applicable `vf_3d.py gate`, then the existing DfAM/slicer checks.
A digital gate is not a physical-print proof.

## Reference-driven reconstruction

Adopt the workflow pattern, not the Claude dependency:
1. source manifest and source-of-truth lock;
2. identify parts/landmarks and orthographic or multiview constraints;
3. build the simplest geometry that satisfies those constraints;
4. compare views and measurements;
5. repair only failed regions;
6. gate before export.

Patterns may be informed by `cc-blender-skill`, but its runtime is not authoritative.

## Hard boundaries

- Never upload/start/heat/move a printer.
- Never route paid/external AI generation as an automatic fallback.
- Never expose a Blender control listener beyond loopback.
- Never replace STEP/B-rep with BLEND when the engineering master requires parametric CAD.
- Never claim printability from appearance alone.
- Never invent dimensions, tolerances, material behavior, source/license, or physical-test evidence.

## Completion

For implementation changes run `python scripts/check-vf-3d-router.py`.
For host readiness require `python scripts/vf_3d.py doctor`.
For a new/changed local stack also run `python scripts/vf_3d.py benchmark`.
Report code/configured, host-ready, geometry-gated and physically-proven as separate states.
