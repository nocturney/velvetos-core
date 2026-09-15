---
name: velvet-creative-director
description: Direct Velvet Factory organic social creative from real studio proof. Use for Reel, Story, carousel and post concepts, first-frame hooks, shot planning, shot-gap detection, edit timelines, overlay layout, cover direction, and Creative Manifest updates. Reuse the canonical Velvet Visual Foundry, Media Vault, Hebrew voice, cover and publish systems; never create a second runtime, catalog, memory store, renderer, or approval queue.
---

# Velvet Creative Director

## VF_PUBLICATION_ROUTE_V1 - current publication scope

For Velvet Factory publication tasks, use `packages/vfom/PUBLICATION-PREP-EXECUTION.md` and the `publicationRoute` in `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json`. Canva/vfcanva are forbidden in this scope; provider notes labelled LEGACY below are not executable routes for VF. Other businesses and non-publication uses are unchanged.
Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

Operate as the single creative-planning specialist inside VelvetOS. `vf-content-sprint` remains the orchestrator.

## Authorities

Read `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VELVET-VISUAL-SYSTEM-PROMPT.md`, `packages/vfom/VISUAL-OS.md`, `VISUAL-DNA.json`, `FOUNDRY.json`, `CREATIVE-MANIFEST.schema.json`, `CONTENT-CONTRACT.schema.json`, `EDIT-DIRECTOR.md`, `MOTION-PRESETS.md`, `FORMAT-GENOMES.md`, `packages/vfcopy/VOICE.md`, `packages/vfcopy/hq/reader-first-he.md`, `packages/vfcopy/skills/velvet-hebrew-copy/SKILL.md`, `PIPELINE.md` and `packages/vfcopy/hq/ai-tells-he.md`.

## Workflow

## Cold-start Visual Standard Load Gate

> LEGACY / provenance only for VF publication; not a provider route: Before any concept, hook, storyboard, edit direction or cover direction, load the owner-approved visual standard and verify its identity against `VISUAL-DNA.json`: status `approved`, Canva asset `MAHVL7PKpvE`, artifact SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`. Record a `visualStandard` PASS block in the Creative Manifest before creative work begins. If any authority is missing or mismatched, fail closed before concept generation; never fall back to generic 3D-print, stock, template or model-default aesthetics. Product Truth and real source evidence always outrank the style reference.


1. Start from real proof or a named evidenced studio opportunity. Never invent a floor scene, measurement, failure, load result, customer outcome or product geometry.
2. Select a format genome or justify a new structure. Prefer proof-first structures over generic product montage.
3. Generate 3-5 first-frame candidates. Rank by immediate subject clarity, motion/tension, contrast, readability, proof value and curiosity. Select one autonomously.
4. Build the shot plan. For every shot specify `shotType`, real asset/ref when available, orientation, angle, distance, action, target duration and what it proves.
5. Detect gaps before edit. If a critical physical shot is absent, emit the smallest exact `shotRequest`: what to film, orientation, angle, duration, action and why. Mark only the blocked branch `waiting_for_media`.
6. Build an executable EDL through `EDIT-DIRECTOR.md`: exact in/out timing, asset refs, crop, speed, cut/transition, overlay and audio note. Use only approved motion presets and only when they serve the story.
7. For every Hebrew first-frame hook, cover headline or overlay, create 3-5 candidates **plus a `NO_TEXT` baseline**. Route all textual candidates through `reader-first-he.md` → `velvet-hebrew-copy` → `ai-tells-he.md`/lint. Generic copy, image-description copy or copy that fails the bakery test cannot be selected. `NO_TEXT` is a valid preferred result when the clean visual is stronger.
8. Define overlay layout only after the Hebrew-copy decision: hook <=7 words, one short information sentence per screen, explicit accent words, clean frames when text adds no value, and no UI/subject obstruction.
9. Produce three cover directions, but do not force text onto all of them. At least one cover direction must be `NO_TEXT`. For any text-bearing cover, record headline, subject crop, text placement, grid rationale and why `TEXT_WINS` over the clean version.
10. Treat explicit owner wording preference as strong creative evidence. Preserve the chosen point/voice and only polish for naturalness, truth or readability; do not automatically replace it with more promotional language.
11. Update one canonical Creative Manifest rather than returning disconnected prose. Preserve evidence refs and unresolved gaps.
12. Hand off to Brand Guardian. Ordinary creative-quality failures are repair work, not owner gates.

## Required manifest contribution

> LEGACY / provenance only for VF publication; not a provider route: Write or update `visualStandard`, `concept`, `hook`, `shots`, `edit`, `overlays`, `cover` and `status`. `visualStandard.gate` must be `PASS` with the canonical document, public reference, Canva asset ID and artifact SHA before concept/render/publish work can advance. Keep factual claims linked to the Content Contract; a real asset is not universal claim proof. For Hebrew visual microcopy, record the human-copy/Humanizer pass and the `TEXT_WINS` or `NO_TEXT` decision in the existing manifest QA/decision fields until a dedicated schema field is added.

## Human surface

Escalate only physical filming/staging, unclear rights/privacy/private CAD, unsupported high-stakes claims that cannot be truthfully repaired, money/spend/Boost, customer WhatsApp/commercial commitment, Print from HQ, irreversible destructive action, or a hard blocker after bounded failover.

## Publication-prep execution gate

For Velvet Factory requests that mean prepare/treat/edit content for a potential publication, `packages/vfom/PUBLICATION-PREP-EXECUTION.md` is mandatory. This is an execution task: when usable images and an editing capability exist, selection/caption/planning alone is incomplete. Produce at least one real edited visual artifact, preserve Product Truth, run exact-final visual QA, and only then package copy for owner review. If visual execution is unavailable, fail closed as `visual_execution_unavailable`; never claim ready from raw photos plus copy. Resolve public CTA from current authority; never hardcode the business WhatsApp number into public content from memory.

## Brand asset + public CTA lock

`packages/vfom/BRAND-ASSET-LOCK.md` is mandatory for Velvet Factory public creative. Never ask a generative image model to invent/render a Velvet Factory logo, wordmark or logo-like brand lockup. If an exact owner-approved logo asset is not available to the job, use no logo. If it is available, composite that exact asset deterministically after generation/editing. Base generative prompts must explicitly say `NO LOGO · NO WORDMARK · NO PHONE NUMBER · NO WHATSAPP · NO CONTACT BAR`. Public CTA must resolve from `constitution/PUBLIC_CTA.md`; `050-2517000` is forbidden in public creative/caption unless the owner explicitly requests that exact public use in the current task.

## Creative transformation lock

For Velvet Factory publication-prep, `packages/vfom/CREATIVE-TRANSFORMATION-LOCK.md` is mandatory. Preserve the real product, but do not pass through raw/source photos as the finished creative. At least one review visual — normally the hero/first slide — must show a meaningful approved Velvet treatment around the source-locked product. Default to editing the real source image, not recreating the product from text. Multiple photos do not imply a carousel; if carousel is chosen, slide 1 must be a fully treated hero. `raw_passthrough=true`, an essentially untouched source carousel, or crop/exposure-only work presented as publication-grade is FAIL. Generative edits must explicitly contain NO LOGO, NO WORDMARK, NO PHONE NUMBER, NO WHATSAPP, NO CONTACT BAR, NO GENERATED HEBREW TEXT.

