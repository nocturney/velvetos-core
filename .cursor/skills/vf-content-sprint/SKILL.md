---
name: vf-content-sprint
description: Run Velvet Factory content autonomously through the Visual Foundry: real production/media proof, Asset Truth and Claim Provenance, Content Contract, proof-first creative direction, progressive variants, visual evaluation, targeted repair, render/derivatives, Exception Queue and Instagram publish/verification. Use for reels, stories, carousels, covers, production-to-content followups, media intake, finished-print content, or requests to operate content without routine owner approvals. Escalate only physical footage/staging, unclear rights/privacy, unsupported high-stakes claims, money/spend, customer WhatsApp, Print from HQ, destructive actions, or a hard blocker after failover.
---

# Content sprint — Velvet Visual Foundry

Use the existing office orchestrator only. Never install or simulate a second runtime, queue, catalog, creative-memory DB or renderer.

## Core flow

1. Read `packages/vfom/FOUNDRY.json`, `CREATIVE-AUTOPILOT.md`, `VISUAL-OS.md`, `VISUAL-DNA.json`, `CONTENT-CONTRACT.schema.json` and `EDIT-DIRECTOR.md`.
2. Start from real proof: `packages/vfprod/PRINT-DONE.md` / `print.done`, verified Media Vault item, named product/material/failure, or another evidenced opportunity. No invented floor scene.
3. Qualify the opportunity. Check novelty/fatigue against existing office-learning/vfinsights history. Archive weak/duplicate opportunities with a reason instead of producing filler.
4. Read Asset Truth from the canonical Media Vault. Missing `truth` means `unverified` for public factual claims. Build Claim Provenance separately: a real asset does not automatically prove every claim.
5. Build a valid Content Contract before storyboard/render. Include objective, format, factual `truthClaims`, synthetic allowed/forbidden uses, Subject Pack when identity/geometry matters, success thresholds and novelty decision.
6. Act as proof-first Creative Director: choose concept, 3–5 first-frame candidates, one winner, and a complete shot plan. Do not ask the owner to choose routine creative options.
7. Search/classify assets through the canonical Media Vault. If a critical physical shot is missing, emit the smallest exact `shotRequest` and stop only that blocked branch as `waiting_for_media`.
8. Use progressive variants: many cheap concepts/storyboards, fewer rough cuts, at most two full-quality renders by default. Do not spend a final render on an unranked concept.
9. Build the EDL using `packages/vfom/EDIT-DIRECTOR.md`; draft Hebrew through `vfcopy/VOICE.md` and build/select the cover through existing Canva/vfcovers paths.
10. Run Evaluation Engine: deterministic checks + Brand/Hook/composition/Reality/Originality + subject/reference fidelity + artifact checks. Also require Visual OS brandScore >=80 + CONTENT-RUBRIC >=20/25 + Content Contract + policy + rights + written PREFLIGHT.
11. Repair ordinary quality failures automatically and re-run QA. Route the failure to the smallest targeted fix; keep repair cycles bounded by `FOUNDRY.json`. Low quality is not an owner gate.
12. Render relevant derivatives through existing tools only and write real derivative refs back to Media Vault. No second render database.
13. Use the Exception Queue policy. LOW-risk routine content may proceed under standing authorization; MEDIUM uses the existing approval path when policy requires; HIGH becomes `human_required`.
14. Read the active instance profile. If `creativeAutonomy.publish.standingAuthorization=true`, LOW-risk routine organic content that passed every gate may be sent through `vfigos` without per-asset approval.
15. Never extend standing authorization to ₪/price, purchases/spend, Boost/Ads, auto-DM, customer WhatsApp, Print from HQ, unsupported claims, unclear rights/privacy, user tagging without opt-in, or irreversible destructive actions.
16. Never claim published without a real tool receipt and live verification evidence. Use the same-turn failover path when the publish tool is unavailable.
17. After verified publish, ingest only real performance evidence into existing `vfinsights`/office-learning. Store the creative recipe with evidence; never create a second creative-memory database.
18. End exactly as `published_verified`, `performance_learned`, `ready_for_publish`, `waiting_for_media`, `human_required`, or `archived`.

## Truth rules

- `verified_real` = real source, not universal claim proof.
- `derived_real` = edited/composited from real source; keep provenance.
- `illustrative_ai` / `synthetic` = support only; never prove load, measurement, failure, success, geometry or customer result.
- Unsupported factual claim: remove/reframe automatically when possible; escalate only when the claim is business-critical and cannot be truthfully repaired.

## Subject Lock

When product fidelity matters, use Content Contract `subjectPack`: real reference asset ids, geometry/material/color invariants and `mustNotChange`. Reject or replace generated shots that drift from the actual product.

## Packs and tools

- `vfom` — Visual Foundry policy, Creative/Edit/Publishing direction.
- `vfmedia` — canonical asset intake/catalog + Asset Truth.
- `vfcopy` — Hebrew copy/VOICE.
- `vfcovers` + `vfcanva` — cover/visual production.
- `vfgrowth` — calendar, rubric, policy, preflight.
- `vfigos` — real Instagram tool send + verification/failover.
- `vfinsights` + office-learning — verified post-publish evidence and learning only.

## Human Required only

Physical footage/staging · rights/privacy/private CAD uncertainty · unsupported high-stakes claim that cannot be repaired · ₪/spend/Boost · customer WhatsApp/commercial commitment · Print from HQ · irreversible destructive action · hard blocker after documented failover/repair limit.

Owner surface is exception-only. Low creative quality, weak Hook, bad crop, subject drift, cover choice, caption rewrite, duplicate concept or ordinary tool failover are internal work, not reasons to bother Christian.
