# Crew: content production

Source patterns: Wordware, GoCharlie, Wispy, Diagram, v0 (layout only).
Orchestrator overlay: existing `vfe2b` run desk only — **no second orchestrator**. Creative autonomy: `packages/vfom/CREATIVE-AUTOPILOT.md`.
Packs: `vfcopy`, `vfcovers`, `vfigos`, `vfgrowth`, `vfom`, `vfmedia`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Creative Director | `vfom` | concept, first-frame ranking, shot plan, gaps | Ask owner to choose routine creative options |
| Homework | `vfcopy` | Voice, facts, banned claims | Invent Insights |
| Edit Director | `vfom` | EDL from real assets | Invent footage |
| Cover | `vfcovers` | Build/select cover direction | Invent a Canva URL/brand value |
| QA | `vfgrowth` | Visual OS + Rubric + policy + PREFLIGHT | Escalate routine low quality |
| Publisher | `vfigos` | Publish via connected tool when authorized; verify receipt/live | Auto-DM, boost, fake publish |
| Human | — | Physical footage, rights ambiguity, ₪/spend, customer WhatsApp, Print | Routine hook/cover/cut decisions |

## Run

1. Start from real opportunity: `packages/vfprod/PRINT-DONE.md` / `print.done`, verified media intake, product/material/failure evidence. No invented floor scene.
2. Run Creative Director from `vfom/CREATIVE-AUTOPILOT.md` + `VISUAL-OS.md`: choose concept + best first frame + shot list autonomously.
3. If critical physical footage is missing, emit a minimal `shotRequest` and mark `waiting_for_media`. Do not ask broad creative questions.
4. Classify existing assets through Media Vault vocabulary and build EDL from `EDIT-DIRECTOR.md`.
5. Draft Hebrew through `vfcopy/VOICE.md`; funnel/CTA authority remains `packages/vfgrowth/hq/PROFILE-TO-WHATSAPP.md` + current constitution. No invented ₪/claims/Insights.
6. Build/select cover. Canva first; failover per desk law. No raw JPEG as final branded cover.
7. Written PREFLIGHT + Visual OS brandScore >=80 + CONTENT-RUBRIC >=20/25 + policy + rights. If quality fails, repair and re-run internally.
8. Authorization:
   - instance `creativeAutonomy.publish.standingAuthorization=true` + all gates pass -> `authorized_for_tool_publish`.
   - otherwise -> existing human approval path.
9. `vfigos` sends via a real connected Instagram publish tool. No receipt/live evidence -> honest Degraded/failover packet; never claim posted.
10. After verified publish, ingest real performance evidence when available and feed office-learning.

## Human Required only

- physical reshoot/staging unavailable to office;
- unclear customer/media rights or private identity/CAD;
- ₪, purchase, paid boost/ads;
- customer WhatsApp send/commercial commitment;
- Print from HQ;
- hard blocker after documented failover.

## Done when

Exactly one outcome: `published_verified`, `ready_for_publish`, `waiting_for_media`, or `human_required`. Never stop at “waiting for owner approval” solely because a routine creative choice exists.
