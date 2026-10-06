# ROUTINE — Velvet Factory office schedule

Asia/Jerusalem. Current recurring Grok Bot authority is the **three-routine minimal baseline** in `automation/grok/current-baseline.json` and `automation/grok/manifest.json`. Historical Stage 7C nine-routine wording is provenance, not current scheduler authority.

## Current scheduled cadence

| Time | Surface | Responsibility |
|---|---|---|
| **06:30** | Cognee Memory Sync | Refresh/verify the local derived Cognee/vfmem index; silent when healthy. |
| **18:30** | VelvetOS Office Loop | One meaningful end-of-day office sweep: state changes, handoff and learning. |
| **19:15** | Runtime Receipts Refresh | Refresh dependency-scoped runtime evidence from real observations only; never fabricate an observation. |

No other Grok routine is a recurring clock.

## Manual / event-driven capabilities

`Velvet Morning Brief` is manual/event-driven only. When justified, build the factual artifact with `python3 scripts/vfops_loop.py brief --write --date <YYYY-MM-DD>` and use the canonical delivery path. `backfill artifact is not a delivery receipt`.

`Velvet Research Seat` is also manual/event-driven only. The old **07:00 cutoff** and **09:00** brief remain historical workflow references, not active recurring clocks. Research output, when intentionally refreshed, continues to land in `packages/vfops/data/research.md`.

`Morning Delivery Guard`, `Weekly Research Accountability`, `Cognee Stable Updates`, `VelvetOS Integrity Guard`, and `PC Offline Retry` are disabled. `Cognee Stable Updates` is handled on demand through upstream review. There is no dedicated recurring routine manager.

Best-skills (`BEST-SKILLS`) and weekly inspiration (`WEEKLY.md` / שבוע) remain lifecycle capabilities, not fixed Grok clocks.

## Canonical ownership


`VelvetOS Office Loop` is the only scheduled office sweep and runs once at 18:30. It intentionally owns responsibilities that were previously split across separate Creative Autopilot, Evening Summary, Automation Steward, Media Intake desk checks, Publish Watch, Content Sprint and Insights Review automations. Those legacy recurring ChatGPT automations stay disabled. The former protected ChatGPT scheduler copies were retired at the verified 2026-09-19 Grok Bot cutover and must not be re-enabled as a second scheduler unless Christian explicitly changes the architecture.

`packages/vfops/LOOP.json` is a **consume/lifecycle map, not a clock source**. Historical labels such as `daily-07:00` or `daily-06:15` do not override the protected live automation set above.

`python3 scripts/vfops_loop.py run` remains a compatibility/manual consumer runner and sensor target. It is **not** the primary daily scheduler and must not be described as a scheduled run unless a real scheduler binding exists and is provider-proven.

## Machine-owned GitHub workflow roles

- `vfmedia-intake.yml` — high-frequency canonical Media Vault intake.
- `office-control-plane.yml` — watchdog/control-plane health, memory hygiene, gaps and handoff, plus CI-failure learning candidates (`vf_learning.py ingest-ci` → `packages/vfharness/state/learning-candidates/`); not a replacement scheduler for every office capability.
- `velvetos-research.yml` — research freshness/index/sensor verification around artifacts; any owner-facing research body is manual/event-driven.
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

- **Upstream/toolchain watch:** when an explicit research/upstream event justifies it, the Research Seat can run `python3 scripts/vf_upstream_watch.py check --write packages/vfresearch/sources/upstream-watch-latest.json`. It covers installed/runtime sources and repository-only skill/agent/pattern upstreams from `packages/velvetos/UPSTREAM-WATCH.json`. It never auto-upgrades. Detected updates are sticky until a reviewed adoption explicitly runs `vf_upstream_watch.py ack --repo … --evidence …`; compatibility/smoke evidence is required before that acknowledgement.
- **Bi-daily Best Skills:** `BEST-SKILLS.md` / `vf-best-skills` runs approximately every 48h until explicitly stopped. This is a standing lifecycle responsibility, not a second fixed-clock scheduler; timer/provider renewal evidence must remain honest.
- **Weekly inspiration links / קישורי השראה שבועיים:** `vfresearch/WEEKLY.md` + `LINKS.json`, followed by Print·Demand·Sound via `vfresearch/hq/PRINT-DEMAND.md`. The weekly cadence must emit real source/evidence or an explicit no-change/blocker state.
- MakerWorld/Printables candidate research runs behind `MAKERWORLD-SCAN.md` + license/slice/test gates; never promote directly to SKU/price.
- Calendar fill is readiness-driven; blocked items are skipped rather than force-filled.
- Daily learning/retro and owner-memory are owned by the Office Loop/end-of-day learning path.
- LAST30/community research remains monthly/on-demand unless the protected automation set explicitly changes.

An event-driven Morning Brief may consume `packages/vfops/data/research.md`; if research was not intentionally refreshed, the brief must show an honest gap rather than infer completion from a green workflow.

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


## Publisher authority update — 2026-09-26

OpenPost is frozen and has no recurring office responsibility or release/update watcher in scheduler authority. Scheduled Instagram truth comes from the Cloudflare Instagram Publisher; live publication truth still requires Meta/Instagram read-back. See selected `instance:surface:toolStatus` via `packages/velvetos/tool_status_resolver.py`.
