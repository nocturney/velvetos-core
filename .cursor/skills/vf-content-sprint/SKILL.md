---
name: vf-content-sprint
description: Run Velvet Factory content autonomously through the Visual Foundry: real production/media proof, Asset Truth and Claim Provenance, Content Contract, Instagram decision passes, one shared Creative Manifest, specialist Creative Director/Media Librarian/Brand Guardian passes, progressive variants, targeted repair, HyperFrames/FFmpeg deterministic render, derivatives, fail-closed final quality gate, Exception Queue and Instagram publish/verification. Use for reels, stories, carousels, covers, production-to-content followups, media intake, finished-print content, or requests to operate content without routine owner approvals. Escalate only physical footage/staging, unclear rights/privacy, unsupported high-stakes claims, money/spend, customer WhatsApp, Print from HQ, destructive actions, or a hard blocker after failover.
---

# Content sprint — Velvet Visual Foundry

## VF_PUBLICATION_ROUTE_V1 - current publication scope

For Velvet Factory publication tasks, use `packages/vfom/PUBLICATION-PREP-EXECUTION.md` and the `publicationRoute` in `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json`. Canva/vfcanva are forbidden in this scope; provider notes labelled LEGACY below are not executable routes for VF. Other businesses and non-publication uses are unchanged.
Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

Use the existing office orchestrator only. Never install or simulate a second runtime, queue, catalog, creative-memory DB or renderer. HyperFrames is a deterministic render backend behind the existing Foundry capability, not a new authority/runtime.

`packages/vfom/INSTAGRAM-CONTENT-DECISION.json` is the mandatory Instagram strategy/retention/quality decision policy inside this existing flow. It does not create a new pack or agent runtime.

## Core flow

> LEGACY / provenance only for VF publication; not a provider route: **Cold-start invariant:** before candidate expansion or creative generation, validate the owner-approved visual-standard identity against `VISUAL-DNA.json` and the active Velvet Factory instance. Require Canva asset `MAHVL7PKpvE`, artifact SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`, and the canonical public/reference paths. Write `visualStandard.gate=PASS` into the Creative Manifest. Missing/mismatched authority is fail-closed: do not invent a generic substitute style.


1. Read `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VELVET-VISUAL-SYSTEM-PROMPT.md`, `packages/vfom/FOUNDRY.json`, `CREATIVE-AUTOPILOT.md`, `INSTAGRAM-CONTENT-DECISION.json`, `VISUAL-OS.md`, `VISUAL-DNA.json`, `CREATIVE-MANIFEST.schema.json`, `CONTENT-CONTRACT.schema.json`, `EDIT-DIRECTOR.md`, `MOTION-PRESETS.md`, `FORMAT-GENOMES.md`, `HYPERFRAMES-BACKEND.json`, `HYPERFRAMES-FRAME.md` and the mandatory public-copy invariant `packages/vfcopy/SOFT-TOOLS-CONTRACT.md`.
2. Start from real proof: `packages/vfprod/PRINT-DONE.md` / `print.done`, verified Media Vault item, named product/material/failure, or another evidenced opportunity. No invented floor scene.
3. Run decision-policy `content_matrix` candidate expansion before `saturation_scan`. Start from 3–5 Velvet-specific pillars and the eight configured angle families, bind every candidate to real proof/source refs, and use a current `SocialResearchPacket` from `packages/vfresearch/SOCIAL-INTELLIGENCE.md` when available. A single strong evidenced opportunity may record `not_applicable_single_evidence`; never silently skip. Generate many cheap candidates, not many final renders. Then run `saturation_scan` using `vfinsights`, office-learning and current `vfresearch` evidence. Name up to the configured seven saturated patterns only when evidence exists; otherwise record external saturation as unknown. Never invent trends. Produce evidence refs plus whitespace angles.
4. Run `anti_generic_check`. Reject, repair or archive anything that could belong to any 3D-print shop, feels stock/template-driven, merely says “look what came off the printer”, uses generic slogans, or lacks a real reason to exist. Prefer real decisions, failures, constraints, iterations, process details, before/after evidence and product proof.
5. Read Asset Truth from the canonical Media Vault. Missing `truth` means `unverified` for public factual claims. Build Claim Provenance separately: a real asset does not automatically prove every claim.
6. Choose one primary format through `format_selection` before storyboard/render. Pick Reel, carousel, post or Story according to how the evidence/story works; do not force every idea into all formats. Derivatives are allowed only when they preserve value.
7. Build a valid Content Contract before storyboard/render. Include objective, chosen format, factual `truthClaims`, synthetic allowed/forbidden uses, Subject Pack when identity/geometry matters, success thresholds and novelty decision.
8. Create one Creative Manifest for the content job. It coordinates strategy evidence, concept, hook tournament, shots, edit, retention, authority/voice, engagement, visual QA, cover, final gate and feed handoff; it is not a second state machine, media catalog or claim authority.
9. Run the configured `hook_tournament`: generate 8–15 cheap hook candidates containing **text + visual + motion** components, score each on clarity, curiosity, relevance, brand fit and visual potential, shortlist 3–5, then select one evidence-compatible winner. No clickbait. Document any reason for overriding the top score.
10. Invoke `.cursor/skills/velvet-creative-director/SKILL.md` for the proof-first concept, selected hook, format genome, exact shot plan, shot gaps, EDL, overlays and cover directions. Do not ask the owner to choose routine creative options.
11. Invoke `.cursor/skills/velvet-media-librarian/SKILL.md` to search/classify canonical Media Vault assets and write concrete asset refs, rights notes and exact gaps into the Manifest. If a critical physical shot is missing, stop only that blocked branch as `waiting_for_media`.
12. Use progressive variants: many cheap concepts/storyboards, fewer rough cuts, at most two full-quality renders by default. Do not spend a final render on an unranked concept.
> LEGACY / provenance only for VF publication; not a provider route: 13. Build/edit through `EDIT-DIRECTOR.md`; every public Hebrew text artifact MUST run the full `packages/vfcopy/SOFT-TOOLS-CONTRACT.md` chain: verified context -> `hq/reader-first-he.md` -> `VOICE.md` + `VOICE-CHART.md` + `voice/approved/` -> relevant template -> `velvet-hebrew-copy` -> `hq/ai-tells-he.md` -> `python3 scripts/check-vfcopy.py lint` on the ACTUAL final copy with verified context -> factual gate -> `TEXT_WINS`/`NO_TEXT` when visual copy applies. `VOICE.md` alone is never sufficient. Use `MOTION-PRESETS.md`; build/select cover through existing Canva/vfcovers paths.
14. Run `retention_pass` on the actual draft: Reel = 0–2 second hold, progression and payoff; carousel = slide-to-slide forward drive and no filler; post = opening lines that earn the read; Story = immediate context and one clear beat per frame. Remove filler instead of padding duration/slides.
15. Run `authority_voice_pass`: expertise must come from demonstrated work, decisions, constraints, reasons and proof. Remove guru language, empty hype, unsupported “leader/best” positioning, clichés and over-promotion.
16. Run `engagement_pass`: use a specific, natural question or tradeoff only when it genuinely fits. `engagementBait` must remain false; no “comment YES”, forced tagging, fake controversy or algorithm-first prompts.
17. For Reel/Story/feed video or multi-shot/motion composition, route render through `HYPERFRAMES-BACKEND.json`. Build the composition against `HYPERFRAMES-FRAME.md`, use only real/approved Media Vault refs, keep Hebrew as deterministic RTL layers, and create a request matching `HYPERFRAMES-RENDER.schema.json`. On an authorized Edge/Office host run `python3 scripts/vf_hyperframes.py plan <request>` before execution; then `run` for rough/review/final. HyperFrames is primary for these cases; `ffmpeg-svg-caption-composition` remains failover and is preferred for trivial single overlays/caption burn-in. Never silently install/change the pinned package from the content job.
18. Invoke `.cursor/skills/velvet-brand-guardian/SKILL.md` on actual rough/final outputs for deterministic + Brand/Hook/composition/Reality/Originality + subject/reference + artifact checks, feed continuity and repair instructions. Require evidence that the current copy version passed `vfcopy` lint/fact gate, plus Visual OS brandScore >=80 + CONTENT-RUBRIC >=20/25 + Content Contract + policy + rights + written PREFLIGHT. Brand Guardian never substitutes for the copy chain.
19. Run `visual_qa` on the actual mobile-ready artifact and record all critical checks: contrast, readability, crop, safe zones, hierarchy, branding, product visibility, Hebrew typography and mobile preview. Any failed critical check blocks publication and routes to repair.
20. Repair ordinary quality failures automatically and re-run the affected gates. Any copy rewrite after lint must be linted again; any material change after rubric/preflight invalidates those passes. Keep repair cycles bounded by `FOUNDRY.json`. Low quality is not an owner gate. If HyperFrames fails after one actionable retry, use `ffmpeg-svg-caption-composition` when it can preserve the intended artifact; never lower QA to make a renderer pass.
21. Run `final_quality_gate` fail-closed. It may reject publication. `visualStandard.gate=PASS` with the canonical owner-approved identity is mandatory for public visual work. PASS requires evidenced completion of saturation scan, anti-generic, format selection, hook tournament, retention, authority/voice, engagement and visual QA, plus Content Contract, final-copy pass, Visual OS, CONTENT-RUBRIC, rights, policy and publish preflight. Missing evidence is not PASS.
22. Final video render requires HyperFrames check/strict render (or documented failover), ffprobe verification and a render receipt. A render receipt proves the file and streams; it is NOT a publish receipt and does not authorize publishing. Write real derivative refs back to Media Vault and the Manifest. No second render database.
23. Use the Exception Queue policy. LOW-risk routine content may proceed under standing authorization only after the final quality gate passes; MEDIUM uses the existing approval path when policy requires; HIGH becomes `human_required`.
24. If `creativeAutonomy.publish.standingAuthorization=true`, LOW-risk routine organic content that passed every gate may be sent through `vfigos` without per-asset approval.
25. Never extend standing authorization to ₪/price, purchases/spend, Boost/Ads, auto-DM, customer WhatsApp, Print from HQ, unsupported claims, unclear rights/privacy, user tagging without opt-in, or irreversible destructive actions.
26. Never claim published without a real tool receipt and live verification evidence. Use the same-turn failover path when the publish tool is unavailable.
27. After verified publish, run `performance_feedback` only from measured evidence. Use format-relevant metrics when available: Reels — hold/watch/completion/shares; carousels — slide retention/saves/shares; posts — saves/shares; Stories — completion/exit/replies; all formats — profile actions, meaningful comments and inquiries where measured. Never invent unavailable Insights. Write learning only to existing `vfinsights`/office-learning, and do not promote a creative pattern before the configured minimum measured sample.
28. End exactly as `published_verified`, `performance_learned`, `ready_for_publish`, `waiting_for_media`, `human_required`, or `archived`.

## Truth rules

- `verified_real` = real source, not universal claim proof.
- `derived_real` = edited/composited from real source; keep provenance.
- `illustrative_ai` / `synthetic` = support only; never prove load, measurement, failure, success, geometry or customer result.
- Unsupported factual claim: remove/reframe automatically when possible; escalate only when the claim is business-critical and cannot be truthfully repaired.

## Decision evidence required in the Creative Manifest

Before `authorized_for_tool_publish`, the Manifest must contain evidence for:

- content-matrix candidate pool + proof/source refs, or explicit `not_applicable_single_evidence`;
- saturation scan + whitespace angle;
- anti-generic result and specificity proof;
- one chosen format with rejected alternatives/reason;
- hook tournament scores and winner;
- retention pass;
- authority/voice pass;
- engagement pass with `engagementBait=false`;
- all critical visual QA checks;
- `finalGate.status=PASS`.

Post-publish performance feedback is appended only when real evidence exists.

## Packs and tools

- `vfom` — Visual Foundry policy, Instagram decision policy, Creative Manifest, visual constitution, edit vocabulary and render-backend contract.
- `vfmedia` — canonical asset intake/catalog + Asset Truth.
- `vfcopy` — mandatory `SOFT-TOOLS-CONTRACT.md`: reader-first, voice, Hebrew copy, Humanizer/AI-tells, actual-copy lint and factual gate.
- HyperFrames — deterministic multi-shot/motion/RTL video backend through `scripts/vf_hyperframes.py`; never a creative authority or second runtime.
- `ffmpeg-svg-caption-composition` — deterministic fallback/simple-overlay path.
> LEGACY / provenance only for VF publication; not a provider route: - `vfcovers` + `vfcanva` — cover/visual production.
- `vfgrowth` — calendar, rubric, policy, preflight.
- `vfigos` — real Instagram tool send + verification/failover.
- `vfresearch` — public Social Intelligence / reference mechanics via `SOCIAL-INTELLIGENCE.md`; research only, never publish authority.
- `vfinsights` + office-learning — verified post-publish evidence and learning only; `CREATIVE-PERFORMANCE-PROFILE.json` is a measured prior, never a truth override.

## Human Required only

Physical footage/staging · rights/privacy/private CAD uncertainty · unsupported high-stakes claim that cannot be repaired · ₪/spend/Boost · customer WhatsApp/commercial commitment · Print from HQ · irreversible destructive action · hard blocker after documented failover/repair limit.

Owner surface is exception-only. Low creative quality, weak Hook, bad crop, subject drift, cover choice, caption rewrite, duplicate concept or ordinary render/tool failover are internal work, not reasons to bother Christian.

## Publication-prep execution gate

For Velvet Factory requests that mean prepare/treat/edit content for a potential publication, `packages/vfom/PUBLICATION-PREP-EXECUTION.md` is mandatory. This is an execution task: when usable images and an editing capability exist, selection/caption/planning alone is incomplete. Produce at least one real edited visual artifact, preserve Product Truth, run exact-final visual QA, and only then package copy for owner review. If visual execution is unavailable, fail closed as `visual_execution_unavailable`; never claim ready from raw photos plus copy. Resolve public CTA from current authority; never hardcode the business WhatsApp number into public content from memory.

## Brand asset + public CTA lock

`packages/vfom/BRAND-ASSET-LOCK.md` is mandatory for Velvet Factory public creative. Never ask a generative image model to invent/render a Velvet Factory logo, wordmark or logo-like brand lockup. If an exact owner-approved logo asset is not available to the job, use no logo. If it is available, composite that exact asset deterministically after generation/editing. Base generative prompts must explicitly say `NO LOGO · NO WORDMARK · NO PHONE NUMBER · NO WHATSAPP · NO CONTACT BAR`. Public CTA must resolve from `constitution/PUBLIC_CTA.md`; `050-2517000` is forbidden in public creative/caption unless the owner explicitly requests that exact public use in the current task.

## Creative transformation lock

For Velvet Factory publication-prep, `packages/vfom/CREATIVE-TRANSFORMATION-LOCK.md` is mandatory. Preserve the real product, but do not pass through raw/source photos as the finished creative. At least one review visual — normally the hero/first slide — must show a meaningful approved Velvet treatment around the source-locked product. Default to editing the real source image, not recreating the product from text. Multiple photos do not imply a carousel; if carousel is chosen, slide 1 must be a fully treated hero. `raw_passthrough=true`, an essentially untouched source carousel, or crop/exposure-only work presented as publication-grade is FAIL. Generative edits must explicitly contain NO LOGO, NO WORDMARK, NO PHONE NUMBER, NO WHATSAPP, NO CONTACT BAR, NO GENERATED HEBREW TEXT.

