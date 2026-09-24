# VelvetOS × text-to-cad

Status: **IMPLEMENTED / WINDOWS HOST VERIFIED / PRINT START DISABLED**

This integration extends the existing `vfprod` + `expert-3d-model` path. It does not create a second production source of truth.

## Runtime

- Upstream: `earthtojake/text-to-cad`
- Local clone: `%VELVET_PRINTLAB_ROOT%\tools\text-to-cad`
- Default PrintLab: `%USERPROFILE%\Documents\VelvetPrintLab`
- Dedicated Python env: `text-to-cad\.venv`
- CAD kernel: `cadgen` + build123d/OCP
- DfAM: upstream `dfam-check`
- Slicing: upstream `gcode` skill + the existing VelvetPrintLab OrcaSlicer router

The host bridge is `scripts/vf_cad.py`.

## Source-of-truth rule

`VelvetPrintLab\slicer-router\printer_matrix.json` remains the machine/profile authority. The bridge generates text-to-cad wrapper profiles from that matrix and the existing native machine/process/filament JSON files. Do not maintain a second handwritten printer matrix in Core.

Current logical printer keys:

- `h2d` — Bambu Lab H2D
- `u1` — Snapmaker U1 (three units)
- `ecc2` — Elegoo Centauri Carbon 2
- `c5` — Flashforge Creator 5
- `c5pro` — Flashforge Creator 5 Pro

## Safety boundary

CAD generation, STEP/STL/3MF export, DfAM measurement, local slicing and G-code validation are allowed engineering operations. This bridge never uploads, starts a print, heats, homes, jogs, or controls printer networking.

The existing printer matrix must keep all of these false:

`printer_network_control`, `upload`, `start_print`, `heating`, `motion`.

Physical printing remains a separate production-floor action.

## Operator commands

```bash
python scripts/vf_cad.py doctor
python scripts/vf_cad.py profiles
python scripts/vf_cad.py dfam --input path/to/model.stl --angle-limit 45
python scripts/vf_cad.py slice --input path/to/model.stl --printer u1 --output path/to/model.gcode
python scripts/vf_cad.py slice --input path/to/model.stl --printer u1 --output path/to/model.gcode --execute
```

Without `--execute`, slicing is a dry run. With `--execute`, it only runs the local slicer and then validates the generated G-code.

## Design workflow

Preferred functional-part path:

plain-language requirement → parametric CAD source → STEP master → STL/3MF sidecar → DfAM check → targeted CAD repair when needed → OrcaSlicer dry-run → local slice → G-code validation → human/production-floor handoff.

For organic/sculptural generation, 3D AI Studio remains a separate specialist route; do not force text-to-cad to replace it.

## Verification

A host is usable only after `python scripts/vf_cad.py doctor` reports PASS. Repository wiring alone is not host capability proof. Upstream updates require rerunning doctor and at least one CAD→mesh→DfAM→slice smoke before promotion.
