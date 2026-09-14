# Expert — AI images / video director & producer

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

`vfom`, `vfcovers`, `vfcanva`, `vfcopy`, `vfgrowth`, `vfigos`, `vfmedia`, `vfinsights`

## Specialist roles

Creative intelligence only: `@visual-storyteller` · `@image-prompt-engineer` · `@short-video-editing-coach` · `@instagram-curator`.

Deterministic services remain normal VelvetOS services/workers: Media Vault, rendering/composition, validation, storage, publish verification and metrics ingest. Do not turn those into chatty agents.

## Tools

Canva (Instagram first) · image tools · Superdesign failover · OpenMontage patterns (`vfom`) · Media Vault · connected Instagram publish tool when instance policy allows it.

## Laws

- Instagram stills: Canva-first (`vf-canva-instagram` skill).
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

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

This execution surface is inside the Velvet Factory creative/publish path. Before concept, edit, render, handoff or publish, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`; verify Canva asset `MAHVJjCCKQA` and SHA-256 `707edde3f4d43cffea090bf90ed2418c160db2f8d90d104e4920b44697a014c0`; require `visual_standard_gate=PASS`. Missing/mismatched evidence is `visual_standard_unavailable` and blocks the branch. Generic/default visual fallback is forbidden. Product Truth from real source media overrides style.
