# Crew: content production

Source patterns: Wordware, GoCharlie, Wispy, Diagram, v0 (layout only).
Orchestrator overlay: existing `vfe2b` run desk only — **no second orchestrator**. Visual Foundry autonomy: `packages/vfom/CREATIVE-AUTOPILOT.md` + `FOUNDRY.json`. Mandatory Instagram decision policy: `packages/vfom/INSTAGRAM-CONTENT-DECISION.json`.
Packs: `vfcopy`, `vfcovers`, `vfigos`, `vfgrowth`, `vfom`, `vfmedia`, `vfinsights`.
Canonical public CTA funnel: `packages/vfgrowth/hq/PROFILE-TO-WHATSAPP.md` (historical filename; follow current public CTA contract).

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Creative Director | `vfom` | proof-first concept, format selection, hook tournament, shot plan, gaps | Ask owner to choose routine creative options |
| Truth/Contract | `vfmedia` + `vfom` | Asset Truth, Claim Provenance, Content Contract, Subject Pack | Treat real media as proof of an unsupported claim |
| Strategy | `vfom` + `vfinsights` + office-learning | saturation scan, whitespace, anti-generic check | Invent trends or external saturation evidence |
| Homework | `vfcopy` | Voice, facts, banned claims, authority/voice pass | Invent Insights |
| Variant Director | `vfom` | cheap concepts/storyboards → rough cuts → max 2 final renders | Render every idea at full quality |
| Edit Director | `vfom` | EDL from real assets + retention pass | Invent footage or pad weak content |
| Engagement | `vfom` | natural discussion prompt when relevant | Engagement bait or fake controversy |
| Cover | `vfcovers` | Build/select cover direction | Invent a Canva URL/brand value |
| QA/Repair | `vfom` + `vfgrowth` | deterministic + perceptual + reference + artifact + mobile Visual QA; targeted repair | Escalate routine low quality or lower gates to ship |
| Publisher | `vfigos` | Publish via connected tool when authorized and final quality gate PASS; verify receipt/live | Auto-DM, boost, fake publish |
| Learning | `vfinsights` + office-learning | Store recipe with verified performance evidence | Create a parallel creative-memory DB or invent metrics |
| Human | — | Physical footage, rights ambiguity, unsupported critical claim, ₪/spend, customer WhatsApp, Print | Routine hook/cover/cut decisions |

## Run

1. Start from real opportunity: `packages/vfprod/PRINT-DONE.md` / `print.done`, verified media intake, product/material/failure evidence. No invented floor scene.
2. Run `content_matrix` from `INSTAGRAM-CONTENT-DECISION.json`: expand 3â€“5 Velvet-specific pillars across the configured eight angle families, bind every candidate to real proof/source refs, and use `SocialResearchPacket` evidence when available. A single strong evidenced opportunity may record `not_applicable_single_evidence`; this is candidate expansion only and has no publish authority.
3. Run `saturation_scan`: use existing measured/history/research evidence; mark unknown when external evidence is unavailable. Find whitespace instead of merely polishing saturated patterns.
4. Run `anti_generic_check`. Archive or repair ideas that could fit any 3D-print shop, feel stock/template-like, or are empty “look what we printed” content.
5. Read Media Vault Asset Truth and build Claim Provenance.
6. Run `format_selection` and choose one primary Reel/carousel/post/Story based on how the evidence and story work. Do not generate every format by default.
7. Build `CONTENT-CONTRACT.schema.json` contract with evidence-linked `truthClaims`, chosen format, synthetic policy and Subject Pack if fidelity matters.
8. Run `hook_tournament`: 8–15 cheap text+visual+motion candidates, score clarity/curiosity/relevance/brand fit/visual potential, shortlist 3–5 and select one evidence-compatible winner without clickbait.
9. Run Creative Director from `vfom/CREATIVE-AUTOPILOT.md` + `VISUAL-OS.md` + `VISUAL-DNA.json`: proof-first concept + selected hook + shot list autonomously.
10. If critical physical footage is missing, emit a minimal `shotRequest` and mark `waiting_for_media`. Do not ask broad creative questions.
11. Use progressive variants from `FOUNDRY.json`: storyboard/mock first, then rough cuts, then at most two final renders by default.
12. Classify existing assets through Media Vault vocabulary and build EDL from `EDIT-DIRECTOR.md`.
13. Draft final Hebrew through the full `vfcopy/SOFT-TOOLS-CONTRACT.md` chain. Then run `retention_pass` on the actual draft; remove filler rather than extending duration or slide count.
14. Run `authority_voice_pass`: show decisions, constraints, reasons and proof; remove guru language, hype, clichés and unsupported superiority claims.
15. Run `engagement_pass`: any CTA/question must be naturally worth answering; `engagementBait=false` is mandatory.
16. Build/select cover. Canva first; failover per desk law. No raw JPEG as final branded cover.
17. Evaluation Engine + written PREFLIGHT + Visual OS brandScore >=80 + CONTENT-RUBRIC >=20/25 + Content Contract + policy + rights. Repair the smallest affected component and re-run internally within bounded cycles.
18. Run `visual_qa` on the actual mobile-ready artifact: contrast, readability, crop, safe zones, hierarchy, branding, product visibility, Hebrew typography and mobile preview are critical checks.
19. Run `final_quality_gate` fail-closed. It may reject publication. Missing evidence for any mandatory decision pass is a failure, not an implied PASS.
20. Render required derivatives through existing tools; save real derivative refs back to Media Vault. No second render catalog.
21. Authorization / Exception Queue:
   - LOW + instance `creativeAutonomy.publish.standingAuthorization=true` + final quality gate PASS -> `authorized_for_tool_publish`.
   - MEDIUM -> existing human approval path only when policy requires it.
   - HIGH -> `human_required`.
22. `vfigos` sends via a real connected Instagram publish tool. No receipt/live evidence -> honest Degraded/failover packet; never claim posted.
23. After verified publish, run `performance_feedback` from measured evidence only. Feed format-relevant watch/retention/saves/shares/profile actions/meaningful comments/inquiries into existing `vfinsights` + office-learning. No style-pattern promotion before the configured measured sample; preserve controlled variation.

## Human Required only

- physical reshoot/staging unavailable to office;
- unclear customer/media rights or private identity/CAD;
- unsupported high-stakes factual claim that cannot be removed/reframed truthfully;
- ₪, purchase, paid boost/ads;
- customer WhatsApp send/commercial commitment;
- Print from HQ;
- hard blocker after documented failover/repair limit.

## Done when

Exactly one outcome: `published_verified`, `performance_learned`, `ready_for_publish`, `waiting_for_media`, `human_required`, or `archived`. Never stop at “waiting for owner approval” solely because a routine creative choice exists.

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

This execution surface is inside the Velvet Factory creative/publish path. Before concept, edit, render, handoff or publish, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`; verify Canva asset `MAHVL7PKpvE` and SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`; require `visual_standard_gate=PASS`. Missing/mismatched evidence is `visual_standard_unavailable` and blocks the branch. Generic/default visual fallback is forbidden. Product Truth from real source media overrides style.
