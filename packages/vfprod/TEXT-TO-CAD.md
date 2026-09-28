# VelvetOS × text-to-cad

Status: **IMPLEMENTED / WINDOWS HOST VERIFIED / PRINT START DISABLED**

This integration extends the existing `vfprod` + `expert-3d-model` path. It does not create a second production source of truth.

## Runtime

- Upstream: `earthtojake/text-to-cad`
- Adopted release: `v0.7.0` at `fafa7b057d8f2c3347ff422f0515380123a4b1d4` (2026-09-27; staged + host-smoke gated)
- Local clone: `%VELVET_PRINTLAB_ROOT%\tools\text-to-cad`
- Default PrintLab: `%USERPROFILE%\Documents\VelvetPrintLab`
- Dedicated Python env: `text-to-cad\.venv`
- CAD kernel: `cadgen` + build123d/OCP
- Project-pinned upstream Skills: `cad`, `cad-viewer`, `dfam-check`, `dfm`, `dxf`, `engineering-drawing`, `gcode`, `sdf`, `sendcutsend`, `srdf`, `step-parts`, `urdf`
- Agent copies: `.agents/skills/` (Cursor/Codex/Antigravity/Gemini and compatible agents) + `.grok/skills/`
- Skill lock: `skills-lock.json`
- DfAM: upstream `dfam-check`
- Slicing: upstream `gcode` skill + the existing VelvetPrintLab OrcaSlicer router
- Decision authority: `FABRICATION-ROUTER.md` + `FABRICATION-ROUTER.json`

The host bridge is `scripts/vf_cad.py`; route inspection is `scripts/vf_fabrication_router.py`. The subordinate engine layer is `CAD-ENGINE-REGISTRY.json` + `scripts/vf_cad_stack.py`: build123d/cadgen remains primary, CadQuery and JSCAD are local secondary engines, and CAD/CAE Copilot/Forgent3D remain bounded pilots.

## Runtime version policy

VelvetOS does not require a specific Text-to-CAD or OrcaSlicer release. It uses the local clone/environment and discovers the installed OrcaSlicer at runtime; `ORCASLICER_BIN` is an explicit override and `printer_matrix.json` version/executable fields are compatibility hints/snapshots, not an allowlist. Upstream tools may pin their own internal Python dependencies; those are the tool's compatibility contract, not a VelvetOS runtime version lock. After upgrades, rerun `vf_cad.py doctor` and the CAD→DfAM→slice smoke.

## Source-of-truth rule

`VelvetPrintLab\slicer-router\printer_matrix.json` remains the machine/profile authority. The bridge generates text-to-cad wrapper profiles from that matrix and the existing native machine/process/filament JSON files. Do not maintain a second handwritten printer matrix in Core.

Current logical printer keys:

- `h2d` — Bambu Lab H2D
- `u1` — Snapmaker U1 (three units)
- `ecc2` — Elegoo Centauri Carbon 2
- `c5` — Flashforge Creator 5
- `c5pro` — Flashforge Creator 5 Pro

## Skill scope

Installed and enabled: CAD creation/editing, CAD Viewer, additive DfAM, non-additive DFM, DXF, engineering drawings, G-code/slicer orchestration, SDF/SRDF/URDF, STEP Parts lookup and SendCutSend preflight.

The upstream `bambu-labs` skill is deliberately **excluded**. Printer handoff/control is not part of this integration.

Use `FABRICATION-ROUTER.md` before selecting a skill. The router may prefer native reasoning/vision or 3D AI Studio when they are a better fit than parametric CAD.

## Safety boundary

CAD generation, STEP/STL/3MF/GLB export, visual review, DfAM/DFM analysis, DXF/drawing generation, local slicing and G-code validation are allowed engineering operations. This integration never uploads, starts a print, pauses/cancels a print, heats, homes, jogs, or controls printer networking. SendCutSend is preflight-only and may not submit an order.

The existing printer matrix must keep all of these false:

`printer_network_control`, `upload`, `start_print`, `heating`, `motion`.

Physical printing remains a separate production-floor action.

## Operator commands

```bash
python scripts/vf_fabrication_router.py list
python scripts/vf_fabrication_router.py route --intent functional_cad_create_edit
python scripts/vf_fabrication_router.py skill --name cad
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

## Deterministic CAD tool decision

Text-to-cad remains the default for plain-language functional parts, parametric source-first workflows, DfAM and the normal slicer handoff.

Use the scoped CLI-Anything FreeCAD adapter only when the task materially benefits from explicit iterative FreeCAD operations, structured JSON commands, FreeCAD-specific workbench operations, or headless STEP/STL/FCStd export:

`python scripts/vf_cli_anything.py doctor`
`python scripts/vf_cli_anything.py freecad -- <args>`

After a CLI-Anything export, return to this canonical bridge for DfAM, printer-profile routing, OrcaSlicer and G-code validation. CLI-Anything never owns printer profiles or physical printer control. Its `preview`, `motion` and `repl` groups are disabled in VelvetOS because the pinned Windows portable GUI-preview path did not terminate reliably. The pinned CLI-Anything 3MF harness is not routable while its known hole-detection/resize tests are failing.

Registry and evidence: `packages/vfharness/devtools/cli-anything.json` and `packages/vfharness/state/cli-anything-phase5-promotion-2026-09-27.json`.

## Verification

Repository wiring must pass `python scripts/check-vf-fabrication-router.py` and `python scripts/vf_fabrication_router.py verify`. A host is usable only after both `python scripts/vf_fabrication_router.py doctor` and `python scripts/vf_cad.py doctor` report PASS. Repository wiring alone is not host capability proof.

Host acceptance covers: cadgen/OCP pins; CAD Viewer loopback launch; DfAM measurement/orientations; DFM measurement; STEP Parts read/download/checksum; DXF generation; engineering-drawing PDF generation; URDF/SRDF/SDF validation; Orca/G-code discovery/validation. SendCutSend remains preflight-only. Upstream updates require rerunning the doctors and representative smokes before promotion.
