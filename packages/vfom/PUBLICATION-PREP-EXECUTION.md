# Velvet Factory — Publication Prep Execution Contract

Status: **MANDATORY · FAIL-CLOSED**

This contract applies whenever the owner gives product media and asks to prepare, treat, edit, package or make it ready for a potential publication/post, including Hebrew intents such as `תכין לפרסום`, `פרסום פוטנציאלי`, `תטפל כפרסום`, `תכין שנבחן`, or equivalent wording.

## Core rule

A publication-prep request is an **execution task**, not a planning-only task.

When usable product images are already present and an image/design editing capability is available, the response is incomplete until at least one real edited visual artifact is produced for review. Image selection, ordering, a caption, a crop recommendation, or a promise to "do one more visual pass before upload" do **not** satisfy the request.

If no editing capability is available, stop as `visual_execution_unavailable` and say exactly what could not be produced. Never present raw-image selection + copy as though the publication package is ready.

## Required sequence

`source review -> select strongest source(s) -> Product Truth lock -> source-image edit with meaningful creative delta -> exact-final visual QA -> copy/caption -> preview/package for owner review`

Do not publish unless the owner explicitly asks to publish or an existing standing authorization and publish gate actually allow it. `Prepare for publication` means produce the finished candidate for review, not post it live.

## Mandatory evidence

Before claiming `ready for review`, `prepared`, `draft ready`, or equivalent:

- `visual_standard_gate: PASS`
- `product_truth_gate: PASS`
- `visual_edit_performed: PASS`
- `creative_delta_gate: PASS`
- `raw_passthrough: false`
- `source_edit_mode: SOURCE_IMAGE_EDIT` (or documented deterministic equivalent)
- `hero_transformation_evidence: <real final artifact + visible presentation changes>`
- `visual_output_evidence: <real exported/generated artifact ref>`
- `exact_final_visual_qa: PASS`
- `public_cta_gate: PASS`

If any required field is missing, the state is `BLOCKED`, not ready.

## Owner correction - canonical publication route (2026-09-15)

For Velvet Factory publication creative, **Canva and vfcanva are not part of the canonical production pipeline**. Legacy references to Canva/vfcanva in older office documents are `UNSYNCED_LEGACY` for this scope and MUST NOT be used to route, generate, compose, export or approve a publication artifact.

Mandatory execution gates are now explicit and sequential:

`Authority Gate -> Request Classification -> Source Lock -> Product Truth Lock -> Reference Decomposition -> Creative Director Lock -> Source-Grounded Production -> Copy/Visible Text -> Brand Guardian -> Exact-Final QA -> Owner Review`

Every gate is fail-closed. A later gate cannot retroactively excuse a missing earlier gate. Tool availability never authorizes bypassing a gate.

### Reference-match gate

Before production, decompose the approved visual/editorial references into concrete visual grammar: product-to-frame ratio, environment, lighting direction/quality, depth, negative space, hierarchy, typography density, crop/inset behavior, annotations, surfaces and restrained accents. Record `reference_decomposition_evidence`.

Before delivery require `reference_match_gate: PASS`. Generic catalogue cards, contact sheets, template rails, spec-sheet layouts, or decorative annotation systems invented by the operator are FAIL unless directly justified by the approved reference grammar. Style references are `STYLE_ONLY`; they never supply product pixels or facts.

### Direction rejection

Owner feedback that a candidate is not aligned with the approved visual language sets `direction_status: REJECTED`. All candidates in that layout/treatment family become `REJECTED_FOR_REUSE` and MUST NOT be used as a source, reference, starting point or incremental revision. Restart from authority + approved references + verified product source.

### Product generation prohibition after drift

If a generative attempt alters/recreates the product, discard it. Do not regenerate the defective subject. Return to protected source pixels and deterministic masking/compositing or another source-grounded method.

## Public CTA

Never hardcode WhatsApp into public creative/caption from memory. Resolve CTA from current Velvet Factory authority (`constitution/PUBLIC_CTA.md` / instance policy). A business-contact phone record is not automatically a public CTA.

## Hard failure patterns

Reject as incomplete: caption-only delivery; photo-ranking-only delivery; raw photos presented as finished visual treatment; a carousel that is essentially untreated source photos; crop/exposure-only work presented as the creative result; generic "clean it later" promises; public WhatsApp CTA when current CTA authority forbids it; or claiming the package is publication-ready without a produced visual artifact.


## Brand asset lock

`packages/vfom/BRAND-ASSET-LOCK.md` is mandatory. No generative model may invent or approximate the Velvet Factory logo/wordmark. If no exact verified logo asset is available, omit the logo. If one is available, add that exact asset deterministically after generation/editing. Base generation must contain no phone number, WhatsApp, contact bar, logo or wordmark.

## Creative transformation lock

`packages/vfom/CREATIVE-TRANSFORMATION-LOCK.md` is mandatory. Product fidelity and creative transformation are simultaneous requirements: keep the product source-faithful while materially improving the presentation around it.

## Evidence extension v1 - executable contract

Use the existing Creative Manifest field `publicationEvidence`; the initial form is `packages/vfom/publication-evidence.TEMPLATE.json`. All file references are workspace-relative `{path, sha256}` objects. Product sources use `PRODUCT_SOURCE`; the three exact style/teaching references use `STYLE_ONLY` to mark them non-product inputs. Do not place private files in public Git to satisfy this contract.
Before production run `python3 scripts/vf_publication_evidence.py --manifest <manifest.json> --content-id <ID> --phase production`. Before review delivery run the same command with `--phase delivery`. Only the production phase permits production; it never authorizes delivery or publication.
`stages` records ordered names, PASS/UNPROVEN, timezone-aware start/completion timestamps and digest-bound evidence. `reference_decomposition` contains the ten concrete axes required by the validator. `product_protection` records the source-pixel method, protected regions and evidence. `tools` records actual tool IDs, not desired future calls.
`outputs` is an ordered list of exact `FINAL_VISUAL`/`FINAL_TEXT` files. The package digest is SHA-256 of compact sorted-key JSON containing ordered `{role,sha256}` rows. `copy_receipts` must bind the actual final text to vfcopy results. `review` binds job/package/source/reference hashes, reviewer, observations and separate source/reference/copy/brand/final checks; every final visual has full and distinct mobile-view evidence.
Set `creative_manifest_ref` in the existing PREFLIGHT. `vf_send_preflight.py`, `vf_project_preflight.py`, shared `vf_publish_bridge.stage_to_github` and recovery registration consume the evidence. Bare PASS flags or public-release booleans are not sufficient. Normalize/strip metadata BEFORE final review; staging preserves approved bytes. Bridge/recovery additionally require `--format` and `--package-sha256`.
A direction rejected for language mismatch cannot be used as a parent/source; record new rejection families in the existing `publicationRoute` policy. Rejecting a specific layout family does not ban purposeful detail panels, pictograms or editorial richness generally.

### Trust boundary and rollout

This code verifies files, digests, ordering and the consistency of submitted review evidence. It does NOT independently authenticate an unsigned reviewer statement, prove aesthetic taste, perform a cold-start model test or intercept tools invoked outside the canonical repository flow. Human/perceptual review remains required. Missing evidence stays BLOCKED. Code/CI success is not deployment, Project-settings synchronization or publication.
The exact 6.2 Project source snapshot is retained unchanged; the current scoped owner correction is in this contract and the existing machine policy. Actual ChatGPT Project settings and separate worker/frontend copies require their own synchronization receipts.
