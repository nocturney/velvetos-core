# CAD native technology matrix — 2026-10-08 checkpoint

This updates the reviewed 2026-10-07 intake against canonical `main` at `d838d790`. Commit `3878717c` is an ancestor of main; AI3D phases 0–12 are on main through PR #601, with the Phase 13 acceptance and Phase 14 printer-validation branches clean and merged. This is a **provider decision record**, not permission to create another CAD authority or install a stack in bulk.

| Technology | Current bounded evidence / role | Targeted disposition | License/cost gate before further use |
| --- | --- | --- | --- |
| OpenCASCADE (OCCT) | B-Rep operations already exposed by canonical build123d 0.11.1 / FreeCAD 1.1.3 routes | **REUSE_EXISTING**; benchmark a direct native kernel only for a measured STEP-healing/performance gap | LGPL-2.1 + OCCT exception; record release-specific linking/notice obligations, no new recurring cost assumed |
| CGAL | Robust geometry candidate; not a canonical capability | **ISOLATED_BENCHMARK_ONLY** when an exact mesh/intersection golden fixture fails incumbents | Package-level LGPL-3/GPL-3 split; commercial license may be required; no blanket commercial clearance |
| libigl | Already proven as bounded `sidecar_libigl` 2.6.3 in AI3D Phase 6 | **KEEP_EXISTING_PROVIDER**, do not duplicate | Primarily MPL-2.0; copyleft/other third-party modules need per-module audit |
| Open3D | Existing `sidecar_open3d` 0.20.0 downsample + ICP evidence, reused in scan-to-CAD | **KEEP_EXISTING_PROVIDER**, use current point-cloud route | MIT; retain attribution and exact version/fixture evidence |
| OpenVDB | Phase 6 explicitly leaves it CANDIDATE, no proven native Windows geometry runtime | **DEFER** until a sparse-volume/SDF fixture demonstrates a gap | License depends on pinned source/release: current upstream indicates Apache-2.0 relicense, older documentation MPL-2.0; verify pinned version and dependencies |
| Assimp | Multi-format asset exchange, not exact CAD kernel | **ON_DEMAND_IMPORT_FIXTURE** only for a format not reliably covered by existing adapters | BSD-3-Clause; attribution and sample-asset licensing separate |
| Eigen | Linear algebra support library | **DEPENDENCY_ONLY**, never a CAD provider | MPL-2.0 for modern Eigen; verify exact bundled-version licenses |
| Ceres Solver | Nonlinear fitting/calibration candidate, overlaps existing bounded primitive and geomdl fits | **DEFER_UNTIL_MEASURED_FITTING_GAP** | Ceres core New BSD; optional SuiteSparse can add GPL/commercial obligations; no automatic dependency install |
| PCL | Point-cloud processing overlap with proven Open3D | **DEFER**, only comparative benchmark if Open3D fails a specific fixture | BSD-3-Clause, attribution; complexity and dependency cost remain unmeasured |
| MeshLib | Repair/ICP/boolean candidate overlaps Trimesh, Manifold3D, PyMeshLab and Open3D | **NONCOMMERCIAL_ISOLATED_REVIEW_ONLY**; not admitted for VF production or reusable commercial tooling | Current upstream source-available license requires commercial license for commercial use; separate owner/license and cost gate |

## Other CAD intake decisions

**VTracer** is the existing isolated raster-to-SVG provider pilot, not a new photo, geometry, fabrication or manufacturing authority. Its 2026-10-07 PASS receipt is for a **synthetic 64×64 four-color image only**. No verified owner-approved real dog-keychain source fixture was located in the accessible local project/artifact directories on 2026-10-08. Consequently no real photo proof, fixed-palette manufacturing acceptance, canonical vector/geometry wiring or printer-ready artifact is claimed. When a real approved fixture is available, require immutable source hash, approved palette (at most four exact colors), complete SVG paint validation, repeat-run artifact hashing, vector/geometry QA and green CAD/fabrication sensors before any scoped provider integration.

**cad-agent** is an unproven alternative rendering/visual-feedback loop (build123d code execution behind HTTP/Docker). Existing CAD and Blender visual providers must be compared on a named render/feedback golden fixture first. Do not install, expose port 8123, mount credentials or grant a second CAD authority without measurable missing coverage plus license/security/cost review.

**bambu-cli** remains eligible only as a read-only status/telemetry candidate: no start, upload, heating, movement or other printer mutation in this intake path. Printer and fabrication authority remains the canonical existing router.

## Provenance and next gate

Canonical evidence: `docs/implementation/ai-3d-modeling-engineering-core/README.md`, Phase 6/7/9 acceptance receipts, `packages/vfharness/state/vtracer-pilot-2026-10-07.json`, and the original `packages/vfresearch/sources/2026-10-07-repo-intake.md`. Existing registered providers must not be downgraded to mere candidates or duplicated.

License source checks (2026-10-08):
- https://www.occt3d.com/dev/doc/overview/html/occt_public_license.html
- https://www.cgal.org/license.html
- https://libigl.github.io/license/
- https://www.open3d.org/
- https://github.com/AcademySoftwareFoundation/openvdb
- https://github.com/assimp/assimp
- https://eigen.tuxfamily.org/dox-3.3/group__TopicSparseSystems.html
- https://ceres-solver.readthedocs.io/latest/license.html
- https://pointclouds.org/about/
- https://github.com/MeshInspector/MeshLib

No new library, daemon, external service, runtime authority, hardware action, recurring cost or production fixture is approved by this matrix.
