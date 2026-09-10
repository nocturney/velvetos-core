---
name: vf-content-sprint
description: Run Velvet Factory content autonomously through the Visual Foundry: real production/media proof, Asset Truth and Claim Provenance, Content Contract, one shared Creative Manifest, specialist Creative Director/Media Librarian/Brand Guardian passes, progressive variants, targeted repair, render/derivatives, Exception Queue and Instagram publish/verification. Use for reels, stories, carousels, covers, production-to-content followups, media intake, finished-print content, or requests to operate content without routine owner approvals. Escalate only physical footage/staging, unclear rights/privacy, unsupported high-stakes claims, money/spend, customer WhatsApp, Print from HQ, destructive actions, or a hard blocker after failover.
---

# Content sprint — Velvet Visual Foundry

Use the existing office orchestrator only. Never install or simulate a second runtime, queue, catalog, creative-memory DB or renderer.

## Core flow

1. Read `packages/vfom/FOUNDRY.json`, `CREATIVE-AUTOPILOT.md`, `VISUAL-OS.md`, `VISUAL-DNA.json`, `CREATIVE-MANIFEST.schema.json`, `CONTENT-CONTRACT.schema.json`, `EDIT-DIRECTOR.md`, `MOTION-PRESETS.md`, `FORMAT-GENOMES.md` and the mandatory public-copy invariant `packages/vfcopy/SOFT-TOOLS-CONTRACT.md`.
2. Start from real proof: `packages/vfprod/PRINT-DONE.md` / `print.done`, verified Media Vault item, named product/material/failure, or another evidenced opportunity. No invented floor scene.
3. Qualify the opportunity. Check novelty/fatigue against existing office-learning/vfinsights history. Archive weak/duplicate opportunities with a reason instead of producing filler.
4. Read Asset Truth from the canonical Media Vault. Missing `truth` means `unverified` for public factual claims. Build Claim Provenance separately: a real asset does not automatically prove every claim.
5. Build a valid Content Contract before storyboard/render. Include objective, format, factual `truthClaims`, synthetic allowed/forbidden uses, Subject Pack when identity/geometry matters, success thresholds and novelty decision.
6. Create one Creative Manifest for the content job. It coordinates concept, hooks, shots, edit, cover, QA and feed handoff; it is not a second state machine, media catalog or claim authority.
7. Invoke `.cursor/skills/velvet-creative-director/SKILL.md` for concept, 3-5 first-frame candidates, format genome, exact shot plan, shot gaps, EDL, overlays and cover directions. Do not ask the owner to choose routine creative options.
8. Invoke `.cursor/skills/velvet-media-librarian/SKILL.md` to search/classify canonical Media Vault assets and write concrete asset refs, rights notes and exact gaps into the Manifest. If a critical physical shot is missing, stop only that blocked branch as `waiting_for_media`.
9. Use progressive variants: many cheap concepts/storyboards, fewer rough cuts, at most two full-quality renders by default. Do not spend a final render on an unranked concept.
10. Build/edit through `EDIT-DIRECTOR.md`; every public Hebrew text artifact MUST run the full `packages/vfcopy/SOFT-TOOLS-CONTRACT.md` chain: verified context -> `hq/reader-first-he.md` -> `VOICE.md` + `VOICE-CHART.md` + `voice/approved/` -> relevant template -> `velvet-hebrew-copy` -> `hq/ai-tells-he.md` -> `python3 scripts/check-vfcopy.py lint` on the ACTUAL final copy with verified context -> factual gate -> `TEXT_WINS`/`NO_TEXT` when visual copy applies. `VOICE.md` alone is never sufficient. Use `MOTION-PRESETS.md`; build/select cover through existing Canva/vfcovers paths.
11. Invoke `.cursor/skills/velvet-brand-guardian/SKILL.md` for deterministic + Brand/Hook/composition/Reality/Originality + subject/reference + artifact checks, feed continuity and repair instructions. Require evidence that the current copy version passed `vfcopy` lint/fact gate, plus Visual OS brandScore >=80 + CONTENT-RUBRIC >=20/25 + Content Contract + policy + rights + written PREFLIGHT. Brand Guardian never substitutes for the copy chain.
12. Repair ordinary quality failures automatically and re-run the affected gates. Any copy rewrite after lint must be linted again; any material change after rubric/preflight invalidates those passes. Keep repair cycles bounded by `FOUNDRY.json`. Low quality is not an owner gate.
13. Render relevant derivatives through existing tools only and write real derivative refs back to Media Vault and the Manifest. No second render database.
14. Use the Exception Queue policy. LOW-risk routine content may proceed under standing authorization; MEDIUM uses the existing approval path when policy requires; HIGH becomes `human_required`.
15. If `creativeAutonomy.publish.standingAuthorization=true`, LOW-risk routine organic content that passed every gate may be sent through `vfigos` without per-asset approval.
16. Never extend standing authorization to ₪/price, purchases/spend, Boost/Ads, auto-DM, customer WhatsApp, Print from HQ, unsupported claims, unclear rights/privacy, user tagging without opt-in, or irreversible destructive actions.
17. Never claim published without a real tool receipt and live verification evidence. Use the same-turn failover path when the publish tool is unavailable.
18. After verified publish, ingest only real performance evidence into existing `vfinsights`/office-learning. Store the creative recipe with evidence and link the learning state in the Manifest; never create a second creative-memory database.
19. End exactly as `published_verified`, `performance_learned`, `ready_for_publish`, `waiting_for_media`, `human_required`, or `archived`.

## Truth rules

- `verified_real` = real source, not universal claim proof.
- `derived_real` = edited/composited from real source; keep provenance.
- `illustrative_ai` / `synthetic` = support only; never prove load, measurement, failure, success, geometry or customer result.
- Unsupported factual claim: remove/reframe automatically when possible; escalate only when the claim is business-critical and cannot be truthfully repaired.

## Packs and tools

- `vfom` — Visual Foundry policy, Creative Manifest, visual constitution and edit vocabulary.
- `vfmedia` — canonical asset intake/catalog + Asset Truth.
- `vfcopy` — mandatory `SOFT-TOOLS-CONTRACT.md`: reader-first, voice, Hebrew copy, Humanizer/AI-tells, actual-copy lint and factual gate.
- `vfcovers` + `vfcanva` — cover/visual production.
- `vfgrowth` — calendar, rubric, policy, preflight.
- `vfigos` — real Instagram tool send + verification/failover.
- `vfinsights` + office-learning — verified post-publish evidence and learning only.

## Human Required only

Physical footage/staging · rights/privacy/private CAD uncertainty · unsupported high-stakes claim that cannot be repaired · ₪/spend/Boost · customer WhatsApp/commercial commitment · Print from HQ · irreversible destructive action · hard blocker after documented failover/repair limit.

Owner surface is exception-only. Low creative quality, weak Hook, bad crop, subject drift, cover choice, caption rewrite, duplicate concept or ordinary tool failover are internal work, not reasons to bother Christian.
