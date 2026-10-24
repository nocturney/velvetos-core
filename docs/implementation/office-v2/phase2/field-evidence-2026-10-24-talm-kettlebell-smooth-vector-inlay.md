# Real-world field evidence: Talm lifestyle kettlebell — smooth vector flush inlay

**Reported:** 2026-10-24 (Asia/Jerusalem)  
**Class:** owner-confirmed physical-print outcome, plus earlier file-backed mesh and slicer QA  
**Domain:** existing-mesh customization, curved SVG/decal as separate printable inlay, protected mechanical interfaces  
**Scope:** incumbent tools `live-blender`, `live-creativecraft` and the existing Fabrication Router / 3D / slicer chain. This is **not** a new candidate, benchmark winner, scorecard, source of truth, or authority change.

## Field verdict: positive, bounded

The Velvet Factory owner reported: **"הדפסתי, עשית עבודה מצויינת!"** ("I printed it; you did excellent work"). This confirms a completed physical trial print and strong owner satisfaction with its result. The print date, actual printer/filament/settings, customer delivery, payment, series quantity, and mating-part/thread fit were not separately verified. No fabricated repeat count, physical measurement or controlled A/B score is claimed.

Primary business evidence and owner report: [Talm print success, detailed case and preserved workflow](https://docs.google.com/document/d/1xrd3ocmJWA4VcWxSGEedUho_2FLRytIB7lW1MK1-K8M/edit); [customer order source folder](https://drive.google.com/drive/folders/11AgALJ0IXiMbYgLJ9aPPxIpOZwTy-H3R).  
Business record: `VF HQ · jobs` — `VF-20261024-001` is a **trial-print** record, not shipment/payment closure.

## Actual compared approaches (not a randomized same-fixture bake-off)

| Phase | Tool or technique | Evidence | Task-level conclusion |
| --- | --- | --- | --- |
| Existing source | Original `ketbot.stl`, logo `talm.svg` | Preserve silhouette and threaded top; color mapping is secondary to splitting geometry into aligned parts | Treat original mechanical surfaces and logo paths as inputs, not surfaces to globally rebuild |
| Rejected iteration | Variant C, `0.10 mm` voxel CSG / global remesh | Topology / 3MF validity was insufficient: owner found surface noticeably rough; some comparison sections showed localized thread deviation | **Negative evidence for global voxelization in this specific finish-and-interface-preservation task**, not a universal rejection of voxel remeshing |
| Revised mesh construction | Blender 5.2.2 LTS headless, SVG vector paths, radial projection, local `BOOLEAN EXACT` difference + intersect | Body and logo exported as two closed/manifold meshes, with a nominal `0.72 mm` radial inlay depth and `198°` wrap; same cutter used for complementary volumes | **Positive evidence for this bounded Blender workflow** |
| Geometry QA | Original-mesh region comparison and volume conservation | All 197,510 triangles fully above `Z > 17 mm` matched original source bit-for-bit; body `6815.637339 mm³`, logo `149.956760 mm³`, original `6965.499661 mm³`; absolute volume sum delta `0.094438 mm³` (~0.00136%) | Strong digital evidence that the protected upper region was unchanged; not a physical fit guarantee |
| Preparation / validation | OrcaSlicer 2.5.0-dev with a Bambu H2D *QA profile*, two 0.4 mm nozzles, 0.12 mm layers | Sliced successfully; 193 layers, distinct assignments in layers 17–137 and separately metered materials. Multi-part 3MF passed `manifold=yes` import. | **Positive evidence for import/dry-run slicing**; do not assume this was the physical print's machine/profile |
| Trial print | Owner-operated printer | Printed successfully; explicit positive owner feedback | **Positive physical outcome**; no claim of measured thread mating or validated volume production |

**Product shape:** nominal 38.131714 × 38.131714 × 23.280397 mm overall; the accepted split file stores body and lettering as aligned parts with colors user-selectable in the slicer.

**Artifact provenance:** local delivery path on authorized host `Chris`:  
`D:\\Velvet\\Output\\CreativeCraft\\Kettlebell_Inlay_Experiment_20261023\\Delivery_Trial_C_Smooth_VectorFlush_20261023\\`  
`Kettlebell_TALM_TrialReady_Smooth_Inlay.3mf` is the success-family model; do **not** select old `Kettlebell_Variant_C_HighRes_2Color.3mf` as the winning artifact. A later postprint local snapshot of the first file was observed at 13,106,314 bytes with SHA-256 `42d71344cb4ccf7b6832cd810d4cfc45c320e3c6ce725953ee497878ed7d327b`. Earlier ZIP/source representations differ in bytes. **No proof that the owner's physical print used exactly this later saved byte snapshot**; do not silently promote its hash to physical-print provenance.

## Routing lesson for existing authorities — narrowly scoped

For a user-supplied organic/curved **existing** mesh with a functional interface that must remain unchanged, and a vector logotype required as *flush, separately printable material*:

1. Continue to enter through the **existing** `packages/vfprod/FABRICATION-ROUTER.md`; let `vf-3d-router` select the accepted engine for the actual geometry class. Do not introduce another routing owner.
2. Treat original STL and SVG as immutable geometry/reference masters. Protect the thread/mating-region mesh. Do not globally voxelize for a local text cut when surface finish and interface identity matter.
3. As a **task-scoped positive precedent**, prefer a vector-derived conformal cutter with Blender local Exact Boolean complementary solids when the verified route supports it; keep body and inlay as one aligned multi-part assembly. Do not prematurely bake customer color decisions into geometry.
4. Gate by manifold/closed edges, source-region invariance, volume/placement, visual finish at intended size, actual slicer dry-run and owner-facing trial outcome. Record what each gate *cannot* establish.

The negative Variant C result and positive Exact-Boolean print **support a scenario-specific routing hint**, not a globally increased Blender score or any reduction in parametric CAD, DfAM, slicer selection, printer safety or owner-approval requirements. Tool availability and runtime health are separate from dated outcome evidence.

## Next comparable fixture / promotion gate

Existing [Office v2 Phase 2 Golden Fixtures](README.md#golden-fixtures) already include **"3D asset → DCC → slice → artifact"**. For genuine priority reweighting, replay comparable source meshes, one protected thread and one different interface, consistent logo/nozzle, and the same QA rubric across Exact Boolean and voxel/local alternative routes. Capture source/output hashes, compute/duration, fail/retry count, surface texture, thin-stroke appearance, independent fit measurement and physical outcome. Only then submit standard `scorecard.schema.json` values and consider evidence-backed promotion within the existing policy. This case does **not** satisfy a comparative Golden Fixture run.

**Links:** [Creative Craft QA engineering](../../../../packages/vfharness/devtools/creative-craft/skill/references/creative-qa-engineering.md), [`live-blender` / `live-creativecraft` incumbents](candidate-registry-v0.json).  
