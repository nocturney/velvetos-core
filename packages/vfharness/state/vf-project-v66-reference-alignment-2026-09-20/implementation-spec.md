# VF Project 6.6 reference-alignment — implementation spec

## Goal
Promote the owner's 2026-09-20 clarification into the canonical ChatGPT Project bundle and VF creative/publication authorities so the instructions match the approved references exactly: generic camera-angle labels are discouraged by default, but orientation labels are allowed when the orientation itself adds useful information. Preserve all Revision 6.5 multi-source, Product Truth, brand, CTA, layout-diversity and evidence rules.

## Non-goals
- No new creative runtime, pack, service category, CTA policy, logo policy or Product Truth relaxation.
- No change to the four approved aesthetic reference assets.
- No publication or Project-settings installation.
- No deletion of historical Revision 6.5 files.

## Authority / SoT
- Owner clarification in the current Project conversation.
- `packages/velvetos/chatgpt-project/PROJECT-AUTHORITY-v6.5.txt`
- `packages/velvetos/chatgpt-project/PROJECT-INSTRUCTIONS-v6.5.txt`
- `packages/vfom/VISUAL-OS.md`
- `packages/vfom/PUBLICATION-PREP-EXECUTION.md`
- `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json`
- Four approved aesthetic references in the active asset manifest.

## Acceptance criteria
1. Active Project identity is Contract 6 / Revision 6.6 / `VF-PROJECT-6.6-REFERENCE-ALIGNED-MULTI-SOURCE`.
2. Project Instructions say generic camera-angle labels are avoided by default, but orientation labels are permitted when orientation itself adds useful information; otherwise copy names the concrete feature revealed.
3. Authority, Visual OS, publication contract, machine policy and Creative Director all express the same rule without a blanket prohibition.
4. Multi-source provenance remains unchanged: only `SAME_FRAME_CROP` may be presented as a zoom; `ALTERNATE_VERIFIED_SOURCE` is allowed and explicit.
5. Active pointers, validators and tests reference only Revision 6.6; Revision 6.5 remains historical only.
6. Full sensor suite and CI pass.
7. A complete install bundle is produced with authority, instructions, manifest, Product Truth guide, four aesthetic references, two approved logo rasters, install guide and build record; all hashes are verified.

## Evidence
- Targeted string/policy tests for the camera-label rule and active 6.6 bindings.
- `scripts/check-all.py` through CI.
- Active-pointer scan after merge.
- SHA-256 verification of every package file.

## Risk / gates
This is a scoped policy/bundle change. Repository merge may be completed after CI. ChatGPT Project installation and behavioral cold-start PASS remain separate and must not be claimed without direct evidence.
