# VF Project 6.5 multi-source composition — implementation plan

**Goal:** Promote the owner's 2026-09-20 multi-source composition correction into the canonical VelvetOS creative/publication authority and ChatGPT Project cold-start bundle, while preserving Product Truth separation and making Revision 6.5 the only active Project bundle reference.

**Spec / approval:** Owner instruction in the current ChatGPT Project conversation: update relevant repository files, prepare the Project update bundle, and eliminate active stale manifest/revision references.

**Authority / SoT:** `packages/velvetos/PROJECT-REQUEST-GATE.md`, `packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json`, `packages/vfom/VISUAL-OS.md`, `packages/vfom/PUBLICATION-PREP-EXECUTION.md`, current Revision 6.4 Project bundle, and the owner's 2026-09-20 correction.

**Non-goals:** No new runtime, pack, publication action, business-offering change, CTA change, Product Truth relaxation, or removal of historical revision evidence.

## Tasks

### Task 1 — Canonical 6.5 Project bundle
Create Revision 6.5 authority/instructions/asset manifest and update `LATEST.json`.
Verify exact identity, hashes, four aesthetic references, Product Truth separation, and 8,000-character Project Instructions limit.

### Task 2 — Runtime bindings and sensors
Update `PROJECT-AUTHORITY-MANIFEST.json`, `vf_project_preflight.py`, `vf_publication_evidence.py`, tests, and `.gitattributes` so active code resolves only Revision 6.5 and publication evidence requires all four aesthetic reference identities.

### Task 3 — Creative authority propagation
Update `VISUAL-OS.md`, `PUBLICATION-PREP-EXECUTION.md`, `VISUAL-STANDARD-ENFORCEMENT.json`, and Project Request Gate with the verified source-set model, SAME_FRAME_CROP vs ALTERNATE_VERIFIED_SOURCE provenance, layout-diversity rule, and Revision 6.5 fallback minimum.

### Task 4 — Proof and merge
Review branch diff against the owner correction; confirm active 6.4 manifest references are gone except explicitly historical/archival files; inspect CI/sensor results; merge only if required checks are green.

## Acceptance criteria
- Active Project identity is Contract 6 / Revision 6.5 / `VF-PROJECT-6.5-MULTI-SOURCE-COMPOSITION`.
- Active manifest/preflight/evidence references point to `ASSET-MANIFEST-v6.5.json` and `PROJECT-AUTHORITY-v6.5.txt`.
- Four aesthetic references are required; Product Truth QA imagery remains forbidden for creative conditioning.
- Verified photos of the same physical product may form a source set.
- A hero zoom is always a literal same-frame crop; a different verified frame is explicitly alternate-source provenance and never masquerades as a zoom.
- No synthetic missing angle/detail.
- Visual language remains coherent without forcing identical templates.
- Revision 6.4 files may remain only as historical/superseded evidence, never as active pointers.
