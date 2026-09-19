# ROUTINE — Velvet Factory office schedule

Asia/Jerusalem. The **live protected ChatGPT automation inventory** is the clock authority for owner-facing office work. This document describes responsibilities and cadence; it must not create or revive a second scheduler.

## Current protected daily cadence

| Time | Surface | Responsibility |
|---|---|---|
| **01:45** | Automation Integrity Guard | Verify/repair the protected active automation set before daily workloads. |
| **02:00** | Velvet Research Seat | Daily live research. Finish by the **07:00 cutoff** as `ready_for_brief`, `no_meaningful_findings`, or an explicit blocker. Consumer output is `packages/vfops/data/research.md` for the 09:00 brief. |
| **07:15** | OpenPost Release Watch | Daily condition watch for upstream OpenPost changes; silent when unchanged. |
| **09:00** | Velvet Morning Brief | Owner-facing V10.3 brief from current live sources. Delivery requires Gmail provider evidence, not a generated file. |
| **10:00** | Morning Delivery Guard | Verify TODAY'S 09:00 brief delivery; recover only if absent/unverified. |
| **10:30** | VelvetOS Office Loop | Post-brief operations: blockers, production→content, readiness/publishing and system drift. |
| **18:30** | VelvetOS Office Loop | Second sweep: changes since morning, autonomous completion, learning/state persistence and end-of-day handoff. |

Weekly / קאדנס שבועי: `Weekly Research Accountability` runs Friday at 12:00. Repository-owned GitHub workflows keep their own schedules; Office Loop consumes their evidence rather than duplicating their cron.

## Canonical ownership

`VelvetOS Office Loop` is the active office manager. It intentionally owns responsibilities that were previously split across separate Creative Autopilot, Evening Summary, Automation Steward, Media Intake desk checks, Publish Watch, Content Sprint and Insights Review automations. Those legacy recurring ChatGPT automations stay disabled unless Christian explicitly changes the architecture.

`packages/vfops/LOOP.json` is a **consume/lifecycle map, not a clock source**. Historical labels such as `daily-07:00` or `daily-06:15` do not override the protected live automation set above.

`python3 scripts/vfops_loop.py run` remains a compatibility/manual consumer runner and sensor target. It is **not** the primary daily scheduler and must not be described as a scheduled run unless a real scheduler binding exists and is provider-proven.

## Machine-owned GitHub workflow roles

- `vfmedia-intake.yml` — high-frequency canonical Media Vault intake.
- `office-control-plane.yml` — watchdog/control-plane health, memory hygiene, gaps and handoff; not a replacement scheduler for every office capability.
- `velvetos-research.yml` — research freshness/index/sensor verification around artifacts; the live Research Seat performs the owner-facing web research body.
- `readme-system-pulse.yml` — README/System Pulse refresh.
- `gmail-brief-send.yml` — one-shot production Gmail transport through the owner Apps Script bridge when `packages/vfops/out/gmail-send-request.json` is explicitly enabled.
- `velvetos-weekly-deck.yml` — weekly deck build path.
- publish-bridge cleanup — transport hygiene only.

## Content and publish lifecycle

Content is **readiness-driven**, not clock-authorized. A content opportunity starts from real production/media evidence and uses `vf-content-sprint` / Visual Foundry only when there is a justified candidate.

Before scheduling or publish, human-visible copy must pass `constitution/VISIBLE_TEXT.md` and the current `vfcopy` soft-tools chain. Visuals must pass the current edit/brand/scroll-stop/commercial QA gates. `scheduled`, `rendered`, `uploaded` and `authorized` are not `published_verified`; provider receipt + live verification are required.

After `liveVerified`, import only real performance evidence into `vfinsights`/office-learning. Missing metrics remain `אין ספירה`; weak metrics are internal learning, not a Red owner alert.

## Watchdog / failover

`python3 scripts/vf_office_watchdog.py [--write]` checks publish state, vault, dead-letter, follow-ups, CTA/profile drift and provider auth. Outcomes stay truthful: `OK`, `AUTOFIXED`, `PREPARED`, `WAITING_EXTERNAL_TOOL`, `DEAD_LETTER`, `RED_BLOCKER`.

No Instagram connection does **not** stop office work: continue intake, inspection, copy, design, derivatives, preflight, queue and readiness work. Never invent `live`.

## Recurring non-clock responsibilities

- **Bi-daily Best Skills:** `BEST-SKILLS.md` / `vf-best-skills` runs approximately every 48h until explicitly stopped. This is a standing lifecycle responsibility, not a second fixed-clock scheduler; timer/provider renewal evidence must remain honest.
- **Weekly inspiration links / קישורי השראה שבועיים:** `vfresearch/WEEKLY.md` + `LINKS.json`, followed by Print·Demand·Sound via `vfresearch/hq/PRINT-DEMAND.md`. The weekly cadence must emit real source/evidence or an explicit no-change/blocker state.
- MakerWorld/Printables candidate research runs behind `MAKERWORLD-SCAN.md` + license/slice/test gates; never promote directly to SKU/price.
- Calendar fill is readiness-driven; blocked items are skipped rather than force-filled.
- Daily learning/retro and owner-memory are owned by the Office Loop/end-of-day learning path.
- LAST30/community research remains monthly/on-demand unless the protected automation set explicitly changes.

The 09:00 brief consumes the daily research block from `packages/vfops/data/research.md`; if the daily body did not run, the brief must show an honest gap rather than infer completion from a green workflow.

## Truth rules

- No duplicate scheduler/runtime.
- Current merged/runtime authority wins over stale historical wording.
- Jobs/quotes/books/production states stay truthful: planned · in_progress · blocked · done · verified.
- No invented ₪, dates, customer facts, Insights or completion.
- Machine workflow success proves only what that workflow actually checks.
- Tool failover happens in the same turn when possible; failover never licenses fabricated evidence.
- Owner surface is exception-only. Routine creative quality, copy repair, crop, hook, cover, lint, provider failover and weak metrics stay internal.

## Human required only

Genuinely missing physical footage/staging after real search · unclear rights/privacy/private CAD/customer identity · unsupported high-stakes claim that cannot be repaired · price/spend/Ads/Boost/purchase · customer WhatsApp/commercial commitment · Print from HQ · irreversible destructive action · hard blocker after documented failover.

For routing/search before opening packs manually: `python3 scripts/vfmem.py who "<job>"` then `python3 packages/vfmem/scripts/vf_semantic_search.py "<question>"`.
