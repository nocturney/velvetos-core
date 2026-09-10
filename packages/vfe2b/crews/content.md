# Crew: content production

Source patterns: Wordware, GoCharlie, Wispy, Diagram, v0 (layout only).
Orchestrator overlay: existing `vfe2b` run desk only — **no second orchestrator**. Visual Foundry autonomy: `packages/vfom/CREATIVE-AUTOPILOT.md` + `FOUNDRY.json`.
Packs: `vfcopy`, `vfcovers`, `vfigos`, `vfgrowth`, `vfom`, `vfmedia`, `vfinsights`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Creative Director | `vfom` | proof-first concept, first-frame ranking, shot plan, gaps | Ask owner to choose routine creative options |
| Truth/Contract | `vfmedia` + `vfom` | Asset Truth, Claim Provenance, Content Contract, Subject Pack | Treat real media as proof of an unsupported claim |
| Homework | `vfcopy` | Voice, facts, banned claims | Invent Insights |
| Variant Director | `vfom` | cheap concepts/storyboards → rough cuts → max 2 final renders | Render every idea at full quality |
| Edit Director | `vfom` | EDL from real assets | Invent footage |
| Cover | `vfcovers` | Build/select cover direction | Invent a Canva URL/brand value |
| QA/Repair | `vfom` + `vfgrowth` | deterministic + perceptual + reference + artifact checks; targeted repair | Escalate routine low quality |
| Publisher | `vfigos` | Publish via connected tool when authorized; verify receipt/live | Auto-DM, boost, fake publish |
| Learning | `vfinsights` + office-learning | Store recipe with verified performance evidence | Create a parallel creative-memory DB |
| Human | — | Physical footage, rights ambiguity, unsupported critical claim, ₪/spend, customer WhatsApp, Print | Routine hook/cover/cut decisions |

## Run

1. Start from real opportunity: `packages/vfprod/PRINT-DONE.md` / `print.done`, verified media intake, product/material/failure evidence. No invented floor scene.
2. Qualify novelty/value. Compare against existing content history; archive filler/near-duplicates with a reason.
3. Read Media Vault Asset Truth. Build `CONTENT-CONTRACT.schema.json` contract with evidence-linked `truthClaims`, synthetic policy and Subject Pack if fidelity matters.
4. Run Creative Director from `vfom/CREATIVE-AUTOPILOT.md` + `VISUAL-OS.md` + `VISUAL-DNA.json`: choose proof-first concept + best first frame + shot list autonomously.
5. If critical physical footage is missing, emit a minimal `shotRequest` and mark `waiting_for_media`. Do not ask broad creative questions.
6. Use progressive variants from `FOUNDRY.json`: storyboard/mock first, then rough cuts, then at most two final renders by default.
7. Classify existing assets through Media Vault vocabulary and build EDL from `EDIT-DIRECTOR.md`.
8. Draft Hebrew through `vfcopy/VOICE.md`; funnel/CTA authority remains `packages/vfgrowth/hq/PROFILE-TO-WHATSAPP.md` + current constitution. No invented ₪/claims/Insights.
9. Build/select cover. Canva first; failover per desk law. No raw JPEG as final branded cover.
10. Evaluation Engine + written PREFLIGHT + Visual OS brandScore >=80 + CONTENT-RUBRIC >=20/25 + Content Contract + policy + rights. If quality/fidelity/artifact checks fail, repair the smallest affected component and re-run internally within bounded cycles.
11. Render required derivatives through existing tools; save real derivative refs back to Media Vault. No second render catalog.
12. Authorization / Exception Queue:
   - LOW + instance `creativeAutonomy.publish.standingAuthorization=true` + all gates pass -> `authorized_for_tool_publish`.
   - MEDIUM -> existing human approval path only when policy requires it.
   - HIGH -> `human_required`.
13. `vfigos` sends via a real connected Instagram publish tool. No receipt/live evidence -> honest Degraded/failover packet; never claim posted.
14. After verified publish, ingest real performance evidence and creative recipe into existing office-learning/vfinsights. Respect minimum sample before style recommendations and keep exploration room.

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
