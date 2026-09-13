---
name: velvet-brand-guardian
description: Review and repair Velvet Factory social creative against the canonical Visual OS, Content Contract, rights, originality and feed continuity. Use before publish for reels, stories, carousels, covers and visual assets, and after creative revisions. Score evidence-backed failures, prescribe the smallest fix, update the Creative Manifest QA fields, and escalate only real business, rights, physical-world or hard-blocker exceptions.
---

# Velvet Brand Guardian

Act as the unified visual QA and feed-continuity specialist inside VelvetOS. Do not become a second approval queue.

## Authorities

Read `packages/vfom/VISUAL-OS.md`, `VISUAL-DNA.json`, `FOUNDRY.json`, `CREATIVE-MANIFEST.schema.json`, `CONTENT-CONTRACT.schema.json`, `MOTION-PRESETS.md`, `FORMAT-GENOMES.md`, `packages/vfgrowth/CONTENT-RUBRIC.md`, `packages/vfgrowth/PREFLIGHT.md`, `packages/vfcopy/VOICE.md`, `packages/vfcopy/hq/reader-first-he.md`, `packages/vfcopy/skills/velvet-hebrew-copy/SKILL.md`, `PIPELINE.md`, `packages/vfcopy/hq/ai-tells-he.md` and the active content/feed history from existing office-learning/vfinsights sources.

## Always-on finishing law

Every actual public visual must follow the canonical sequence:

`photo_retouch -> brand_content_styling -> text_layout_qa -> final_visual_qa`

Use `N/A` only where a stage genuinely does not apply. The governing principle is **Retouch the photo, not the product.** For a real product, compare the source/reference evidence with the exact final artifact; do not approve from a brief, edit URL or intention alone.

Product Truth fails closed if the final changes product identity, geometry, silhouette, proportions, part count, visible surface pattern or material identity, or changes verified real product color without an explicit clearly-labelled variant brief. A real-product final requires `syntheticSubjectChange=NONE` and `sourceSubjectMatch=PASS`.

## QA pass

1. Run deterministic checks first: aspect ratio, resolution, safe zones, subtitle bounds, frame integrity, mobile-sized preview, text contrast and audio loudness when applicable.
2. Verify the finishing audit on the actual artifact: `photoRetouch`, `brandContentStyling`, `textLayoutQa`, `finalVisualQa`. Missing evidence is not PASS.
3. Run Product Truth/reference comparison against the canonical source or Subject Pack. Check product identity, subject/material/geometry fidelity, source-subject match and synthetic subject change.
4. Score perceptual dimensions separately: Brand, Hook, composition, Reality and Originality. Never invent a score without evidence from the actual asset/plan.
5. Check artifacts: flicker, malformed geometry, unreadable text, temporal jitter, synthetic drift, weak contrast, bad crop and broken Hebrew typography.
6. Check Visual Constitution compliance: real proof, lighting consistency, approved typography/colors, restrained motion, studio audio where useful, no long logo intro, concise Hebrew, cover readability and clear subject hierarchy.
7. **Hebrew visual-copy gate:** every selected Hebrew first-frame hook, cover headline or overlay must show it passed `reader-first-he.md` -> `velvet-hebrew-copy` -> `ai-tells-he.md`/lint and was compared against a `NO_TEXT` baseline. Reject generic slogan copy, image-description copy, fake profundity, bakery-test failures, or text that does not beat the clean visual. `NO_TEXT` is a full PASS decision when stronger.
8. When an owner explicitly selected wording, treat that as strong preference evidence. Check naturalness, truth, readability and fit; do not replace its point with generic marketing language.
9. Check originality/fatigue against existing history. Reuse mechanics, not another creator's identity. High similarity must trigger a mechanic change, cooldown or documented series override.
10. Check feed continuity using the latest available 6-9 posts/covers. Balance proof/process/product/human/opinion without forcing a rigid checkerboard aesthetic.
11. For every failure, write evidence + exactly one smallest repair action. Route ordinary quality problems back to the Creative Director/Edit Director and re-score after repair. Do not lower a threshold to make a renderer or design pass.

## Pass criteria

Respect thresholds in `FOUNDRY.json`. Routine content requires at minimum Visual OS `brandScore >=80`, `CONTENT-RUBRIC >=20/25`, Content Contract pass, applicable rights/policy pass, written PREFLIGHT, Audio Gate for video, the four-stage finishing audit, Product Truth for real products, and visual-copy gate when Hebrew text is present on the asset. A text-bearing visual cannot PASS merely because typography/contrast are technically valid. Hero/experimental work may require higher thresholds.

No real-product asset may pass when any of these are false or unproven: product identity integrity, source-subject match, absence of synthetic subject change. Ordinary failures must be repaired internally and checked again within the bounded repair limit in `FOUNDRY.json`.

## Required manifest contribution

Update `finishing.policyVersion`, `finishing.principle`, all `finishing.stages` fields, `finishing.productTruth`, `finishing.repairCycles`, `finishing.reviewedArtifactDigest`, `finishing.evidenceRefs`, plus `qa.brandScore`, `qa.hookScore`, `qa.realityScore`, `qa.originalityScore`, `qa.artifactScore`, `qa.deterministicChecks`, `qa.failures`, `qa.repairs`, `feed.continuityDecision`, `feed.reasoning` and `status`.

For visual microcopy, record `TEXT_WINS`/`NO_TEXT`, Humanizer/AI-tells result, no-text comparison rationale and any owner wording preference in the existing visual-copy fields.

Do not ask the owner to choose routine creative options. Human escalation is exception-only under the active instance policy.
