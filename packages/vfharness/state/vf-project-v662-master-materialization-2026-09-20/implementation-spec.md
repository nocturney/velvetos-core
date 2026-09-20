# VF Project 6.6.2 — creative-master materialization bridge

## Trigger
Post-6.6.1 cold-start test. The system correctly completed the post in the first response and used a verified alternate source for a real detail, but the strongest styled visual created earlier in the run was not actually used as the final compositing base. The final artifact regressed toward the raw source. This proves that policy-level `creative_master` selection exists, but the selected master can remain conversation/UI-only instead of becoming a file-backed input for deterministic finalization.

## Goal
Make the selected creative master a concrete, hash-bound, file-backed artifact before deterministic typography/graphics/logo/insets begin. Prevent a conversation-only/provider-only preview from being treated as a usable finalization base until it is materialized.

## Scoped corrections
1. **Plan materialization before generation/editing.** Before choosing the creative tool, determine whether the final composition needs deterministic overlays. If yes, select a route whose output can be materialized as a local file or fetchable provider result. Do not create a UI-only master and discover only at finalization that it cannot be composed.
2. **Materialization gate.** A selected `creative_master` is eligible for deterministic finalization only after it has a local path + SHA-256 and a verified materialization receipt. The bytes must decode as supported media.
3. **Provider/UI-only results.** A conversation image, provider task id or remote URL is not itself the file-backed master. If the provider returns a fetchable URL, materialize those exact bytes through the authorized download route, then register them. If only a UI-only image exists and it cannot be materialized, do not silently rebuild from raw source.
4. **Allowed fallback when master is not materializable.** Either (a) continue with a file-backed provider/route that preserves the selected direction before final overlays, (b) if deliberately appropriate, finish on the exact same provider result as a NO_TEXT final, or (c) block only the deterministic-overlay branch. Recreating the scene from the raw product source is not materialization and cannot satisfy continuity.
5. **Exact-byte handoff.** Final compositor inputs must reference the registered master path+SHA. The final review binds both creative-master SHA and materialization-receipt SHA.
6. **Bridge utility.** Add `scripts/vf_creative_master_bridge.py` to register a local image into a canonical task workspace, decode/validate it, copy exact bytes, compute SHA-256 and write a receipt. Verification mode re-checks path, digest and decodability without network access.
7. **No regression to 6.6.1.** First-response completion, multi-source provenance, Product Truth, camera-label alignment, brand/CTA locks, no-Canva route and final-vs-master QA remain in force.

## Non-goals
- No generic image downloader or new external provider.
- No automatic spending/selection of a paid image provider.
- No weakening of deterministic Hebrew rules.
- No permission to use generated Hebrew/logo/contact details.
- No publishing action.

## Acceptance criteria
1. Active identity is Contract 6 / Revision 6.6.2 / `VF-PROJECT-6.6.2-CREATIVE-MASTER-MATERIALIZATION`.
2. Project Instructions and Authority require materialization planning before creative-tool selection when deterministic overlay is expected.
3. A delivery-phase `creative_master` must have a validated local file and `creative_master_materialization` receipt.
4. Receipt must bind exact source/input artifact SHA to exact materialized local SHA/path and decode successfully.
5. Conversation-only/provider-only results cannot pass delivery evidence without materialization.
6. Rebuilding from raw source cannot be accepted as materialization of a generated/edited master.
7. Structural sensors and bridge tests pass; full `check-all`/CI passes.
8. Complete Project install bundle is generated and SHA-verified.

## Evidence
- Unit-style sensor for bridge register/verify and tamper detection.
- Publication-evidence regression tests for missing/mismatched materialization receipt.
- Project preflight assertions for materialization policy.
- PR review + full VelvetOS Core Sensors.
- Active-pointer scan after merge.
- SHA-256 verification of install bundle.

## Risk / gates
Repository merge may proceed after green CI. ChatGPT Project installation and post-patch cold-start behavior remain separate evidence states.
