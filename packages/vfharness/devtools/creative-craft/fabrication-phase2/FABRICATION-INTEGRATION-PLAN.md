# Creative Craft Phase 2 — Fabrication / CAD / Slicer Integration

Date: 2026-10-01
Status: implementation + consolidation proposal
Scope: Creative Craft consumes the existing fabrication subsystem; it does not replace any fabrication authority.

## Non-negotiable authority boundary

Creative Craft owns only the high-level creative/fabrication domain handoff.
`packages/vfprod/FABRICATION-ROUTER.md/.json` remains the fabrication-intent authority.
`scripts/vf_3d.py` remains the 3D engine-selection authority beneath the Fabrication Router.
`packages/vfprod/CAD-ENGINE-REGISTRY.json` remains subordinate implementation selection beneath the `cad` route.
`VelvetPrintLab\slicer-router\printer_matrix.json` remains the printer/profile authority.
No Creative Craft code may create a second printer matrix, slicer matrix, DfAM authority, CAD engine registry or 3D router.

The physical boundary remains unchanged: no printer networking, upload, start, pause/cancel, heat, home or motion.
Validated G-code ends at a human print-floor handoff.

## Boundary ownership

1. Creative Craft decides only whether the request belongs to fabrication versus another creative domain.
2. Fabrication Router resolves the fabrication intent and required chain.
3. `vf-3d-router` is entered only when the Fabrication Router selects it.
4. The 3D router chooses `TEXT_TO_CAD`, `BLENDER_NATIVE` or `HYBRID_CAD_THEN_BLENDER`.
5. Text-to-CAD/CAD stack chooses its subordinate execution engine; Creative Craft never chooses build123d/CadQuery/JSCAD directly.
6. DfAM owns additive digital manufacturability checks.
7. The canonical slicer route owns local slicing and G-code validation.
8. Human production owns any physical printer action.

## End-to-end routing matrix

| Fabrication intent | Canonical chain | Notes |
| --- | --- | --- |
| Functional exact part | Fabrication Router → cad → cad-viewer | STEP/B-rep master when engineering authority is required. |
| Functional part to print | cad → cad-viewer → dfam-check → gcode | New/materially changed mesh must pass DfAM before slicing. |
| Reference reconstruction with exact interfaces | native vision → vf-3d-router → cad-viewer | 3D router chooses CAD, Blender or hybrid; hidden dimensions remain unknown. |
| Reference reconstruction to print | native vision → vf-3d-router → dfam-check → gcode | Protected interfaces are re-measured after any Blender refinement. |
| Existing STL/mesh repair | dfam-check → vf-3d-router → dfam-check → cad-viewer | Existing mesh normally drives Blender; parametric rebuild may still resolve to Text-to-CAD. |
| Existing slice-ready mesh | dfam-check → gcode | Requires explicit canonical printer key/profile; G-code validation is mandatory. |
| Organic/sculptural model | 3D AI Studio or BLENDER_NATIVE → dfam-check | External paid generation never becomes an automatic fallback. |
| Standard purchased component | step-parts → cad → cad-viewer | Search real component geometry before inventing placeholders. |
| Engineering drawing | engineering-drawing | Geometry remains owned by its CAD/model master. |
| Flat cut profile | dxf → cad-viewer | Do not confuse a cut profile with a printable 3D mesh. |
| CNC/sheet-metal/injection review | dfm | Non-additive manufacturability path. |
| Robot description | urdf / srdf / sdf → cad-viewer | Use the description skill matching the requested artifact. |
| Workshop/site/layout planning | SketchUp + LayOut proposal route | Spatial/layout/documentation only; not tolerance-critical part authority. |
| Technical publication | engineering-drawing/XVL → Corel DESIGNER/InDesign | Publication tools annotate/compose; they do not mutate the engineering master. |

## CAD / modeling decision rules

**Text-to-CAD / build123d-cadgen** is the default for plain-language functional parametric geometry, explicit dimensions, holes, fits, threads, assemblies and STEP/B-rep masters.
It remains the normal first choice even when another installed CAD application could technically perform the job.

**OpenSCAD Nightly** is preferred when the requested source itself should be procedural `.scad`, the geometry is naturally expressed as deterministic CSG/mathematics, or a fixture/jig should be regenerated from a small parameter set.
It is not a fallback for arbitrary engineering CAD, complex assembly work, rich B-rep editing or drawings.
The current Update Sentinel routing state reports `openscad-nightly=available`, but there is still no typed fabrication adapter/engine. Its future integration should therefore be a subordinate typed engine/provider under the existing `cad` authority, not a new intent router.

**FreeCAD / CLI-Anything** is preferred only for explicit iterative FreeCAD operations, FreeCAD-specific workbench commands, or headless FCStd/STEP/STL export.
Plain-language generation stays on Text-to-CAD.
FreeCAD is an adapter, not DfAM, slicer or printer authority.
The isolated CLI-Anything runtime was restored in this phase and `vf_cli_anything.py doctor` plus the strict 106-test/real U1 acceptance pass again.

**Fusion** should enter only where the safe typed provider has an accepted operation.
Today that means bounded inspection/electronics reads, undo/redo and disposable typed box→STL/STEP operations.
General geometry writes, arbitrary Python, raw fusion_mcp_execute and modification of existing user documents remain blocked.
Therefore Fusion is not currently a general fabrication fallback; broader use is a Missing Integrations item requiring typed sketch/feature operations and acceptance evidence.

**Blender** is preferred for organic/sculptural/reference-driven work, existing mesh repair/refinement and non-critical form layers.
When exact interfaces also matter, use `HYBRID_CAD_THEN_BLENDER`: create/freeze the functional STEP master first, refine only non-critical form in Blender, then re-measure protected interfaces.
BLEND may be the form master; it must not replace a required STEP/B-rep engineering master.

**Meshmixer** currently fits as controlled mesh review only.
The accepted surface exposes probe/list/info/import/screenshot, not trusted repair/remesh/make-solid operations.
Actual repair should stay on Blender/vf-3d-router until typed Meshmixer repair operations exist and pass acceptance.

## Engineering DCC entry rules

- **Inventor**: enter when the source/customer authority is Inventor-native, a mechanical assembly/drawing must preserve native structure, or a future typed native operation is demonstrably better than conversion. Do not become the default for ordinary parts already served by Text-to-CAD.
- **AutoCAD**: enter for DWG/DXF-native 2D shop drawings, legacy CAD exchange and exact 2D drafting. Do not use as the master for a normal FDM parametric solid.
- **3ds Max**: use for existing Max assets, modifier-driven hard-surface/visual mesh work or presentation geometry; never as dimensional engineering authority.
- **Maya**: conceptually belongs to Maya-native assets, topology/deformation/retopology workflows and complex mesh authoring; not for tolerance-critical STEP/B-rep. Current routing state is `needs_compatibility_repair`, so it is **not routable now** until its post-update compatibility gate passes again.
- **ZBrush**: use for high-resolution sculptural detail, reliefs and organic surface work; downstream decimation/repair/DfAM is mandatory before print claims.
- **SketchUp 2026**: complementary spatial design for rooms, booths, racks, workshop/printer-farm layout and installation planning.
- **LayOut**: sheets, dimensions, presentation/documentation and PDF/DWG/DXF handoff from SketchUp spatial models.
- **XVL Studio**: once Missing Integrations verifies a live route, prefer for large product assemblies, exploded/service views and technical-illustration source generation; until then it is not routable.

## Slicer policy

1. **OrcaSlicer is canonical and preferred.** `vf_cad.py doctor` currently passes and selects the installed OrcaSlicer 2.4.2 path dynamically.
2. **PrusaSlicer is the intended fallback #1, but not yet an automatic fallback.** Current canonical `gcode discover` now sees `prusa-slicer` at `C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe`. However, `vf_cad.py` still builds Orca-native wrapper profiles and explicitly executes the Orca backend. Until printer/material/process profile parity and a bounded fallback adapter are accepted, Creative Craft must fail closed rather than call Prusa directly.
3. **CuraEngine would be fallback #2 only if installed/discovered and profile parity is proven.** It is not installed now.
4. **Bambu Studio remains non-preferred.** It has an official CLI, but current upstream reports still show CLI/headless/preset reliability problems, including a Windows slicing report. Promotion requires a local Windows smoke with canonical profile inputs and deterministic G-code validation.
5. **ElegooSlicer 1.5.3.5 and Flash Studio Desktop 1.7.18 are reference oracles only.** They may be inspected for vendor machine/material/profile defaults and compared with the canonical Orca/Prusa configuration. They do not receive slicer-authority or printer-control status.
6. **No silent profile translation.** A fallback slicer is usable only if the same printer/material/process intent can be represented and validated. Otherwise return BLOCKED with the missing profile evidence.
7. Every fallback result must record the actual backend/version, profile source/hash and reason for fallback.
8. No slicer route may upload, start, pause/cancel, heat, home, jog or otherwise control a printer.

Current executable order is `OrcaSlicer → BLOCKED` because the canonical wrappers are Orca-native.
Target order after profile-parity acceptance is `OrcaSlicer → PrusaSlicer → CuraEngine (if later installed/verified) → BLOCKED`.
Bambu Studio is outside that automatic fallback order.
Vendor slicers are outside that automatic fallback order.

## Creative Craft adapter contract

Creative Craft should gain one thin tool identity: `fabrication`.
It should not mirror every Fabrication Router intent into the Creative Craft registry.

Public typed operations proposed:
- `route(request, files[])`: delegates to `vf_fabrication_router.py decide`; read-only.
- `status()`: delegates to Fabrication Router verify/doctor and relevant host checks; read-only.
- `dfam(input, angle_limit)`: delegates to `vf_cad.py dfam`; never mutates the source artifact.
- `slice(input, printer_key, output, execute=false)`: delegates to `vf_cad.py slice`; default dry-run; local execute only creates G-code and automatically validates it.
- `three_d_route(request)`: internal-only helper when the canonical fabrication plan contains `vf-3d-router`; not a user-selectable bypass.

Blocked operations: raw engine selection, raw script execution, printer network access, upload, start_print, pause/cancel, heat, motion, arbitrary Fusion execution, arbitrary Blender Python, and handwritten printer-profile overrides.

## Verification artifacts at every boundary

**Creative Craft → Fabrication Router**
- resolved owner request;
- input artifact paths + SHA-256 where files exist;
- explicit dimensions/constraints and a separate unknowns list;
- requested output class;
- Fabrication Router decision receipt: intent, chain, confidence, reason and printer-actions=false.

**Fabrication Router → CAD/3D engine**
- canonical route identity;
- Geometry IR/spec or source/reference manifest;
- units and coordinate assumptions;
- protected interfaces/dimensions;
- source/license provenance where external assets exist.

**CAD/3D engine → DfAM**
- editable master reference (STEP and/or BLEND/SCAD/FCStd as routed);
- mesh sidecar path + SHA-256;
- units, bounding box and scale receipt;
- protected-interface measurement receipt after any Blender stage;
- engine/version/path as provenance, never as a runtime allowlist.

**DfAM → slicer**
- DfAM report tied to the exact mesh hash;
- orientation decision/assumptions;
- relevant process/material assumptions;
- no reuse after mesh bytes or relevant print process change.

**Slicer → G-code validator**
- dry-run command receipt;
- canonical printer key;
- wrapper/native profile paths + hashes;
- printer-matrix source/hash;
- actual slicer backend/version;
- output G-code path + SHA-256.

**Validator → human print floor**
- validation PASS/WARN/BLOCKED result;
- bounds/temperature/movement/extrusion checks;
- unresolved warnings;
- explicit statement that digital validation is not physical-print proof;
- no upload/start token or printer-control capability.

## Technical documentation handoff

Engineering geometry remains upstream.
For a single dimensioned manufacturing sheet, keep `engineering-drawing` as the canonical generator.
Use Corel DESIGNER after geometry generation when the task needs technical illustration, callouts, exploded presentation, image composition or branded finishing.
Use InDesign for multi-page manuals, instructions, catalogs or publication layout; it must consume approved geometry/drawing assets rather than edit CAD.
Use XVL, once connected and accepted, for large-assembly/exploded/service-view preparation; pass vector/raster/metadata outputs downstream to Corel DESIGNER/InDesign.
Each publication must retain revision, units and a reference/hash to the engineering master it documents.

## Gaps → Runtime Repairs

- Repair Maya's current `needs_compatibility_repair` state before any fabrication workflow can route through Maya.
- Keep OpenSCAD Nightly update-health/compatibility checks in the Runtime Repairs owner chat.
- After any slicer/CAD/Blender upgrade, refresh capability smoke/evidence instead of version-pinning.
- Prusa backend discovery itself is now PASS; the remaining Prusa gap is profile parity/fallback integration, not discovery.

## Gaps → Missing Integrations

- Add a typed OpenSCAD adapter/engine beneath the existing `cad` authority; support source-first SCAD build/export and deterministic receipts.
- Add a bounded Prusa fallback/profile adapter beneath the canonical gcode/vf_cad route, with verified printer/material/process parity before automatic fallback is allowed.
- Expand Fusion only through bounded typed sketch/feature/export operations; do not expose raw Fusion execution.
- Add SketchUp/LayOut typed read/export or bounded authoring surface if automation is desired.
- Evaluate/bridge XVL Studio before routing production work to it.
- Optional: add typed Meshmixer repair/remesh operations only if the official API surface can be safely bounded and regression-tested.
- Vendor slicer oracle adapters for ElegooSlicer/Flash Studio are optional read/reference work; no physical control.

## Gaps → Skills Research

- OpenSCAD source-first procedural modeling skill/patterns that preserve explicit parameters and deterministic rebuilds.
- SketchUp/LayOut spatial-planning and installation-documentation workflow patterns.
- XVL technical-publication/exploded-view workflows once the runtime integration is known.
- Mesh repair skill patterns that remain engine-neutral and can dispatch through `vf-3d-router` rather than binding directly to a DCC.

## Changes implemented in this isolated worktree

The shared/final `CreativeCraftRouter.py` and `creative-craft-registry.json` were intentionally left unchanged.

Implemented in the canonical fabrication layer:
- `scripts/vf_fabrication_router.py`: recognizes printable creation, explicit slicing/G-code requests, reference reconstruction and existing-mesh repair intent; recognizes existing `vf-3d-router` as a virtual routed component.
- `packages/vfprod/FABRICATION-ROUTER.json`: additive redesign now delegates repair/refinement through the existing 3D router; added reference reconstruction intents.
- `packages/vfprod/FABRICATION-ROUTER.md`: documents the existing 3D sub-router boundary and updated automatic chains.
- `scripts/vf_3d.py`: recognizes explicit STL/3MF mentions and reference-reconstruction wording so mesh repair and protected-interface reconstruction reach Blender/hybrid routing when appropriate.
- `scripts/check-vf-fabrication-router.py` and `scripts/check-vf-3d-router.py`: new regression cases cover the handoff acceptance examples.

Validation after changes:
- `python scripts/check-vf-3d-router.py` → PASS.
- `python scripts/check-vf-fabrication-router.py` → PASS.
- "design a printable threaded bracket" → `functional_part_to_print`.
- "reconstruct this reference and preserve exact mounting holes" → `reference_reconstruction` → existing `vf-3d-router`.
- "make this STL printable" → `additive_redesign` → DfAM → existing `vf-3d-router` → DfAM.
- "create an engineering drawing from the model" → `engineering_drawing_pdf`.
- "slice for U1 and validate the G-code" → `slice_and_validate`.
- `python scripts/vf_cad.py doctor` → PASS with Orca selected, printer safety fields false, and canonical gcode discovery seeing PrusaSlicer.
- `python scripts/vf_3d.py doctor` → PASS for Blender 5.2.2 LTS, hardened local blender-ai-mcp and design-os acceptance.
- `python scripts/vf_cli_anything.py doctor` → PASS after restoring the isolated CLI-Anything runtime.
- `python scripts/check-cli-anything-pilot.py --strict` → PASS: 106 headless tests plus real FreeCAD → DfAM → Orca U1 → G-code validation.
- Current Update Sentinel snapshot: Inventor/AutoCAD/3ds Max/ZBrush/Fusion/Meshmixer/OpenSCAD available; Maya `needs_compatibility_repair`.

## Consolidation instruction

Consolidation should add one Creative Craft `fabrication` adapter/tool and one high-level fabrication pipeline.
That adapter must delegate to the existing Fabrication Router and must not copy the intent table into Creative Craft.
Use the adjacent machine-readable contract as the source for the allowed typed operations and boundary receipts.
Do not merge a direct Prusa/Bambu/vendor-slicer execution path into Creative Craft.
Do not expose `vf-3d-router` as a parallel top-level creative router; it is entered only from the canonical Fabrication Router.
