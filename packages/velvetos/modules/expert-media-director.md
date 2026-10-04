# Expert — AI images / video director & producer

## VF_PUBLICATION_ROUTE_V1 - current publication scope

Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

Module id: `expert-media-director`

## Provides

End-to-end Velvet Visual Foundry direction and routine creative autonomy: opportunity qualification → Asset Truth + Claim Provenance → Content Contract → proof-first concept/shot plan → progressive variants → visual evaluation → targeted repair → render/derivatives → Exception Queue → publish handoff/tool send → evidence-backed learning. Extends `social-growth` and the existing content pipeline; **never** creates a second orchestrator/runtime/catalog/memory DB.

Primary playbooks/contracts:

- `packages/vfom/FOUNDRY.json`
- `packages/vfom/CONTENT-CONTRACT.schema.json`
- `packages/vfom/VISUAL-DNA.json`
- `packages/vfom/CREATIVE-AUTOPILOT.md`
- `packages/vfom/VISUAL-OS.md`
- `packages/vfom/EDIT-DIRECTOR.md`
- `packages/vfom/experts/MEDIA-DIRECTOR.md`

## Packs


## Specialist roles

Creative intelligence only: `@visual-storyteller` · `@image-prompt-engineer` · `@short-video-editing-coach` · `@instagram-curator`.

Deterministic services remain normal VelvetOS services/workers: Media Vault, rendering/composition, validation, storage, publish verification and metrics ingest. Do not turn those into chatty agents.

## Tools


## Laws

- Floor proof — no invented brand hex/fonts/scenes.
- Content Contract is required before storyboard/render for factual public content.
- Asset Truth is not Claim Truth: real media still requires evidence-linked claim provenance.
- Synthetic/illustrative AI may support atmosphere/transitions; it never proves a physical result.
- Subject Pack locks product identity/geometry when fidelity matters.
- Progressive commitment: concepts/storyboards before rough cuts; at most two full-quality renders by default.
- QA separates deterministic, perceptual, reference-fidelity and artifact checks; ordinary failures loop to targeted repair internally.
- Novelty/fatigue uses existing office-learning/vfinsights history, not a new memory store.
- Missing physical footage is a precise `shotRequest`, not a guessed scene.
- Routine creative decisions are autonomous; failed creative QA loops back internally.
- LOW-risk routine tool publish requires instance standing authorization + all preflight/contract/policy/rights gates + real receipt.
- No auto-DM, boost, invented prices/Insights, unsupported claims, customer WhatsApp send, or Print from HQ.

Always present in core. An instance enables it via `modulesEnabled`; per-instance `creativeAutonomy` chooses whether routine publishing may use standing authorization.

## Instance visual-standard gate — mandatory when configured

Compatibility enforcement marker: `VF_VISUAL_STANDARD_GATE`. This identifier is retained for the existing machine guard only; it does not encode business-specific authority or values.

Before public creative execution, resolve the selected instance profile and inspect `creativeAutonomy.ownerApprovedVisualStandard`. When `required=true`, load the instance-declared visual-standard document/reference plus the generic visual authority/DNA surfaces, verify the instance-declared artifact digest, and require the configured visual-standard gate to pass. Missing or mismatched required authority is fail-closed as `visual_standard_unavailable`; generic visual fallback is forbidden. Core does not embed a business-specific standard path, digest, location or brand value.
