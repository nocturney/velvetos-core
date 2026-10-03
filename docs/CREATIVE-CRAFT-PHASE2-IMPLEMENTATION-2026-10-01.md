# Creative Craft Phase 2 — implementation handoff

Date: 2026-10-01
Scope: professional craft + QA layer for the installed creative/fabrication/media stack.
Source brief: owner-provided "02 - Comprehensive Skills Research - Creative Craft Phase 2 Handoff".

## Result

Phase 2 implemented eleven narrow provider-neutral specialist Skills in `.cursor/skills`.
The shared/final Creative Craft router was deliberately NOT edited in this phase.
No second orchestrator runtime, automatic cloud-spend path, printer-control path or publishing authority was added.

The architecture is now:

`existing router/authority -> relevant craft Skill -> accepted execution adapter -> exact-output QA`

Craft Skills teach professional practice and verification. They do not replace existing execution, policy or source-of-truth layers.

## Added Skills

| Skill | Primary craft responsibility |
| --- | --- |
| `vf-cad-design-craft` | Parametric design intent, constraints, interfaces, fits/threads/tolerances, assemblies, CAD verification |
| `vf-dcc-modeling-craft` | Topology, retopology, subdivision, sculpt, UV readiness, mesh QA |
| `vf-material-lookdev` | Baking, mesh-map diagnosis, PBR/OpenPBR authoring, texture/lookdev QA |
| `vf-post-production-craft` | Editorial, color, compositing/motion, audio post, delivery QC |
| `vf-prepress-qa` | Print preflight, links/fonts, bleed, separations, overprint, exact print-PDF inspection |
| `vf-fabrication-craft` | Slicer calibration, orientation/supports, profile discipline, G-code review |
| `vf-sketchup-layout-craft` | SketchUp spatial modeling plus LayOut associative drawing-set practice |
| `vf-technical-illustration-craft` | Corel DESIGNER/XVL exploded/projected views, callouts, dimensions, parts mapping |
| `vf-image-design-craft` | Non-destructive raster/vector work, composition and exact-export QA |
| `vf-speech-qa` | Local TTS/ASR, pronunciation, transcript back-check, consent/license QA |
| `vf-bom-costing` | BOM structure, units, cost rollups, scenarios, formula/reconciliation QA |

Each Skill has a concise `SKILL.md`, `agents/openai.yaml`, and focused `references/` material for progressive loading.

## Existing-flow integrations

### `vf-3d-router`

Added a thin Craft Layer after engine selection:
- parametric CAD -> `vf-cad-design-craft`;
- Blender/DCC topology, sculpt or UV -> `vf-dcc-modeling-craft`;
- hybrid CAD+Blender -> CAD craft on protected interfaces first, then DCC craft on form;
- UV/bake/Substance/PBR/lookdev -> `vf-material-lookdev`;
- additive print-prep/slicer/G-code review -> `vf-fabrication-craft`.

Engine selection, Text-to-CAD, Blender expert planning, DfAM, slicer/export gates and printer boundaries remain authoritative.

### `vf-content-sprint`

Video/motion work now invokes `vf-post-production-craft` before the existing HyperFrames/render path.
Raster/vector publication-prep work now invokes `vf-image-design-craft` for editing/export craft only.
Product Truth, Creative Manifest, Visual OS, brand locks, approval and publishing gates still win.

### Post-production speech handoff
`vf-post-production-craft/references/tool-routing.md` routes TTS/ASR/pronunciation/back-check work to `vf-speech-qa` before audio finishing. Speech QA never receives content or publish authority.

## Infrastructure integrations

### GitHub CLI

`vf-best-skills` now recognizes the installed `gh skill` preview namespace as an additional discovery/preview surface when available:
- use search/preview for research;
- preview before any sandbox install;
- record source/version/commit when pinning;
- never install a discovered Skill directly into production merely because it appears useful;
- existing provenance, duplicate/conflict, wrapper/merge and skill-authoring gates remain authoritative.

### Google Cloud SDK

Added `packages/vfharness/playbooks/gcloud-ops.md`.
Default behavior is read/describe/log first, then the smallest authorized mutation through the existing deployment authority.
No silent project/account switches, IAM broadening, secret exposure or automatic paid-resource creation.

### 7-Zip

Added `packages/vfharness/playbooks/deterministic-packaging.md`.
The packaging contract is stage -> manifest -> archive -> `7z t` integrity test -> clean extraction/content proof -> archive hash/receipt.
Normal packaging forbids source-deleting options and does not create self-extracting executables by default.

`vf-harness` now points to both infrastructure playbooks.

## Research decisions embedded

- CAD uses design-intent/constraint discipline rather than universal fit values.
- DCC distinguishes appearance from deformation/topology/bake readiness.
- Fabrication uses calibration/profile evidence rather than magic-number settings.
- Materials inspect baked maps and destination conventions, not only beauty views.
- Post production separates edit/color/composite/audio/delivery and verifies the rendered artifact.
- Prepress treats the print-provider specification as authority instead of assuming one bleed/PDF-X/CMYK rule.
- SketchUp/LayOut is treated as spatial/documentation craft, not a manufacturing-CAD replacement.
- Technical illustration preserves engineering geometry/part identity.
- Image/vector work preserves editable masters and source/product truth.
- Speech treats runtime, model license and voice consent as separate checks.
- BOM/costing never invents prices, rates, tax or FX assumptions.

## Explicit non-claims / unresolved execution

This phase does not claim new live execution connectivity merely because craft knowledge exists.

- SketchUp/LayOut: craft Skill exists; live Ruby/automation execution must use a separately accepted integration if/when available.
- Blackmagic Fusion Studio standalone: first-class post craft exists; execution still depends on the accepted integration available at runtime.
- Substance Sampler/Modeler: craft may inform work, but the current DCC/Adobe handoff does not establish an accepted official adapter.
- Topaz Video and other optional tools: craft routing does not itself prove automation connectivity.
- Prepress applications without an accepted adapter may still require manual/other approved execution.
- `vf-bom-costing` does not become bookkeeping/ledger authority.

## Validation performed

- All eleven source Skill folders were freshly checked with the Skill frontmatter/structure validator: 11/11 PASS.
- Remote worktree `SKILL.md` files were read back after writing; no generated TODO template remains.
- Referential-integrity review confirmed all eleven Skills have `agents/openai.yaml` and every local reference named by the Skill exists in its folder.
- Speech/BOM duplicate reference drafts were consolidated onto one canonical filename set; redundant copies were archived under `D:\\Velvet\\Archive\\CreativeCraft\\phase2-redundant-20261001` rather than left ambiguous in the active Skills.
- Router edits were read back after application, including fabrication after geometry verification, image/vector craft for still publication prep, speech QA for TTS/ASR work, and prepress QA for print-bound image/vector output.
- Authority review confirms no new printer-control or publish authority in the new Skills.
- The final/shared Creative Craft Skill was not edited, per the Phase 2 brief.

## Repository-native validation

Fresh repository-native validation was run after integration fixes.

- `python scripts/check-vf-3d-router.py` -> PASS.
- `python scripts/check-vf-fabrication-router.py` -> PASS (`skills=12 printer-send=disabled costs=PASS`).
- `python scripts/check-vfops-loop.py` -> PASS after registering all eleven new active `vf-*` Skills in `packages/vfops/LOOP.json`.
- Full `python scripts/check-all.py` -> **113/116 PASS** after the Phase 2 fixes.
- `check-hq-overlay.py`, `check-creative-system.py`, `check-speech-layer.py`, `check-tool-authority.py`, `check-vf-cad-integration.py`, `check-vf-cad-stack.py`, `check-vf-3d-router.py`, `check-vf-fabrication-router.py`, `check-vfops-loop.py` and the other relevant domain sensors PASS in the final full-suite run.

The three remaining failures are not caused by the Phase 2 specialist layer and must not be hidden:
1. `check-skill-health.py`: one active warning remains in the separate/uncommitted `packages/vfharness/devtools/creative-tools/fusion-provider/skill/SKILL.md` surface (no verification language). The Phase 2 technical-illustration warning was fixed and no new Phase 2 Skill remains in the active-warning list.
2. `check-staleness.py`: the repository has no 2026-10-01 morning brief artifact after the staleness cutoff.
3. `check-velvet-health.py`: fails only because it aggregates the same remaining `skill_health` failure.

At the time of this Phase 2 run, the full runner reported expired runtime receipts as WARN in local mode; those were not Phase 2 capability proofs. Stage 4F (2026-10-03) supersedes that event-based behavior with dependency-scoped `CODE_VALID / DEPLOYMENT_VALID / RUNTIME_HEALTHY` proof, so unrelated stale runtime evidence is no longer part of ordinary code validation.

Therefore: Phase 2 wiring/domain sensors are green, but the shared worktree is **not globally green / merge-ready** until the unrelated skill-health warning and current-day brief staleness are resolved by their owning workstreams.

## Consolidation next step

The later Creative Craft consolidation should stay thin. It should route to these specialists plus the already-existing routers/adapters, load only the relevant references, and preserve one authority per decision.
Do not copy the specialist knowledge into one monolithic Creative Craft prompt.

Recommended consolidation priority:
1. wire the final high-level Creative Craft router to the eleven specialists;
2. resolve/accept any still-missing execution adapters in their separate connectivity workstreams;
3. run repo-native skill/architecture sensors;
4. smoke-test representative end-to-end tasks per domain;
5. only then call the architecture production-ready.


## Connectivity closure — 2026-10-02

This section supersedes the earlier execution-connectivity caveats above for the Phase 2 candidate layer. It does not change the authority model or the final/shared Creative Craft router.

Final Phase 2 candidate status:
- **11 accepted capabilities / 0 blocked**.
- Shared/final Creative Craft router remains untouched.
- All accepted adapters remain localhost-only / typed / bounded and do not expose arbitrary scripting.
- Runtime/source integrity gate PASS: every installed Phase 2 adapter/worker matches its source SHA-256.
- All Python adapters compile successfully; installer/rollback/host PowerShell parse with zero errors.
- All Phase 2 Scheduled Tasks return to Ready after testing; no listeners remain on 6781-6790 after cleanup.
- Microsoft ClickToRunSvc is restored to its captured baseline: Stopped / Disabled.

Execution capabilities now accepted:
1. InDesign — official COM; typed compose/export.
2. Corel PHOTO-PAINT — official COM; typed raster transform.
3. Blackmagic Fusion Studio — official scripting API; bounded solid/render workflow.
4. OpenSCAD — official CLI; bounded SCAD -> STL/3MF.
5. Microsoft Office — Word/Excel/PowerPoint COM through controlled InteractiveToken workers with service-state restoration.
6. Adobe Acrobat — official COM inspection.
7. SketchUp — official C API, headless; SketchUp.exe is not required for accepted model creation/inspection.
8. LayOut — official C API, headless; create/save/PDF export accepted. PDF export requires preloading bundled pdflib.dll and LayOutControllers.dll; no vendor binary modification is performed.
9. Adobe Media Encoder 26.3.2 — official Watch Folder workflow using H.264 / Match Source - High bitrate. Remote AME API remains disabled; AME is launched on demand and only an owned instance is cleaned up.
10. XVL Studio Corel Edition -> Corel DESIGNER — official GUI workflow plus Corel COM; accepted XVL .xv2 -> editable CDR/PDF illustration output.
11. XVL HTML5 Publisher — bundled xvlgenhtm.exe CLI; accepted .xv2 -> HTML5 viewer package.

XVL Player SDK / direct XVL SDK API is **not installed**, but is now an optional future capability rather than a Phase 2 blocker because two accepted XVL workflows are available.

SketchUp native EXE note:
- The local SketchUp.exe remains a mixed-install build (26.1.256 executable with 26.1.185 DLL set) and is not relied upon by the accepted C API path.
- Repair/update of the GUI installation can be handled separately if Ruby/UI-only capabilities are later required.

Evidence:
- `docs/evidence/creative-tools/missing-integrations-phase2/candidate-matrix.json`
- Final candidate-matrix SHA-256 at closure: `CD38995388833377FF4F428C62C672690AC89D07F6933F1D1F32FEFF67E703E3`
- Phase status in the matrix: `COMPLETE`, accepted_count=11, blocked_count=0.

The next architectural step is a separate consolidation task: wire the shared Creative Craft router to these already-accepted specialist/candidate capabilities without duplicating their logic or widening authority.
