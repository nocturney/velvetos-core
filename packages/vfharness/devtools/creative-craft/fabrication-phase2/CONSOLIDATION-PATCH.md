# Consolidation Patch — Creative Craft ↔ Fabrication

Status: recommendation only; do not apply in this phase-2 fabrication chat.

## 1. Registry addition

Add exactly one Creative Craft tool identity named `fabrication`.
Do not mirror Fabrication Router intents as Creative Craft tools.

Suggested registry shape:

```json
"fabrication": {
  "display_name": "VelvetOS Fabrication",
  "lifecycle": "headless-cli",
  "domains": ["fabrication", "cad", "mesh", "3d-print", "engineering-drawing"],
  "production_surface": "canonical-vfprod-adapter-v1",
  "operations": ["route", "status", "dfam", "slice"],
  "blocked": [
    "raw-engine-selection",
    "raw-script-execution",
    "printer-network-control",
    "upload-to-printer",
    "start-print",
    "pause-cancel",
    "heating",
    "motion"
  ]
}
```

## 2. Pipeline addition

Add one high-level pipeline:

```json
"fabrication": {
  "steps": [
    {
      "tool": "fabrication",
      "required": true,
      "purpose": "delegate fabrication intent and execution to the canonical vfprod Fabrication Router"
    }
  ]
}
```

The pipeline must not contain copied routes such as `cad → dfam → gcode`.
Those remain data owned by `FABRICATION-ROUTER.json`.

## 3. Router operations

Add bounded Creative Craft commands for:
- `fabrication-status`;
- `fabrication-route --request ... [--file ...]`;
- `fabrication-dfam --input ... [--angle-limit ...]`;
- `fabrication-slice --input ... --printer <canonical-key> --output ... [--execute]`.

Each command delegates to the existing scripts; it does not reimplement their logic.

## 4. Delegation rules

- `fabrication-route` → `scripts/vf_fabrication_router.py decide`.
- `fabrication-status` → fabrication verify/doctor plus `vf_cad.py doctor`.
- `fabrication-dfam` → `scripts/vf_cad.py dfam`.
- `fabrication-slice` → `scripts/vf_cad.py slice`.
- If the returned canonical chain contains `vf-3d-router`, the adapter may internally invoke `scripts/vf_3d.py route`; it must never expose that as a bypass around the Fabrication Router.
- Never accept a caller-selected build123d/CadQuery/JSCAD/Blender route when the canonical router did not select it.
- Never accept caller-supplied printer profile paths; accept only canonical printer keys.

## 5. Required consolidation tests

1. `design a printable threaded bracket` resolves to `functional_part_to_print`.
2. `reconstruct this reference and preserve exact mounting holes` resolves to `reference_reconstruction` and then the existing 3D router.
3. `make this STL printable` resolves to `additive_redesign`.
4. `create an engineering drawing from the model` resolves to `engineering_drawing_pdf`.
5. `slice for U1 and validate the G-code` resolves to `slice_and_validate`.
6. A slice command defaults to dry-run unless local G-code generation is explicitly requested.
7. Local G-code generation ends with validator evidence and never performs printer I/O.
8. Prusa is not directly invoked until canonical discovery is available **and** profile parity plus the bounded vf_cad fallback path are accepted.
9. Bambu/Elegoo/Flash are not in the automatic fallback chain.
10. Shared Creative Craft lifecycle/session-preservation rules remain intact.

## 6. Runtime packaging

Do not hard-code the phase-2 worktree path into the final runtime adapter.
Package the final adapter with the normal Creative Craft deployment flow, while resolving canonical VelvetOS scripts from the deployed/core authority.
Preserve no-overwrite output behavior and job receipts.
