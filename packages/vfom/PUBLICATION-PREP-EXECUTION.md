# Velvet Factory — Publication Prep Execution Contract

Status: **MANDATORY · FAIL-CLOSED**

This contract applies whenever the owner gives product media and asks to prepare, treat, edit, package or make it ready for a potential publication/post, including Hebrew intents such as `תכין לפרסום`, `פרסום פוטנציאלי`, `תטפל כפרסום`, `תכין שנבחן`, or equivalent wording.

## Core rule

A publication-prep request is an **execution task**, not a planning-only task.

When usable product images are already present and an image/design editing capability is available, the response is incomplete until at least one real edited visual artifact is produced for review. Image selection, ordering, a caption, a crop recommendation, or a promise to "do one more visual pass before upload" do **not** satisfy the request.

If no editing capability is available, stop as `visual_execution_unavailable` and say exactly what could not be produced. Never present raw-image selection + copy as though the publication package is ready.

## Required sequence

`source review -> select strongest source(s) -> Product Truth lock -> visual edit/retouch -> exact-final visual QA -> copy/caption -> preview/package for owner review`

Do not publish unless the owner explicitly asks to publish or an existing standing authorization and publish gate actually allow it. `Prepare for publication` means produce the finished candidate for review, not post it live.

## Mandatory evidence

Before claiming `ready for review`, `prepared`, `draft ready`, or equivalent:

- `visual_standard_gate: PASS`
- `product_truth_gate: PASS`
- `visual_edit_performed: PASS`
- `visual_output_evidence: <real exported/generated artifact ref>`
- `exact_final_visual_qa: PASS`
- `public_cta_gate: PASS`

If any required field is missing, the state is `BLOCKED`, not ready.

## Public CTA

Never hardcode WhatsApp into public creative/caption from memory. Resolve CTA from current Velvet Factory authority (`constitution/PUBLIC_CTA.md` / instance policy). A business-contact phone record is not automatically a public CTA.

## Hard failure patterns

Reject as incomplete: caption-only delivery; photo-ranking-only delivery; raw photos presented as finished visual treatment; generic "clean it later" promises; public WhatsApp CTA when current CTA authority forbids it; or claiming the package is publication-ready without a produced visual artifact.


## Brand asset lock

`packages/vfom/BRAND-ASSET-LOCK.md` is mandatory. No generative model may invent or approximate the Velvet Factory logo/wordmark. If no exact verified logo asset is available, omit the logo. If one is available, add that exact asset deterministically after generation/editing. Base generation must contain no phone number, WhatsApp, contact bar, logo or wordmark.
