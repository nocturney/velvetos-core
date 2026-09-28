# Research Seat · 2026-09-29

State: `ready_for_brief`
Observed run: 2026-09-29 ~02:11–02:25 Asia/Jerusalem (before 07:00 cutoff).
Seat: Velvet Research Seat
Path: live WebSearch/WebFetch + GitHub CLI shallow clone / `gh` failover (Cloud Agent launch blocked: Cursor usage exhausted / on-demand required). No chatgpt.com / gemini.google.com / perplexity.ai browser.

## Current authority / context
- Read packages/vfresearch/DAILY.md, packages/vfops/ROUTINE.md, BEST-SKILLS.md/json, TIMER.md, hq/MAKERWORLD-SCAN.md, prior `research.md` on main (27.9), anti-recycle vs open PR #405 (28.9 OPEN/unmerged — findings not treated as main, not recycled).
- Best Skills: standingForever=true; `lastPass=2026-09-27` (≥44h) → **EXECUTED**. See `2026-09-29-best-skills.md` + BEST-SKILLS.json update (dataDate 2026-09-28).
- Official MakerWorld/Printables scan: **Tuesday** → cadence sun+wed → exactly **«לא יום סריקה»**. No invented model names.
- Social Intelligence: no policy-change signal; PUBLIC_CURRENT_CTA = Instagram message / איסוף שדרות. WhatsApp 050-2517000 desk-only. Auto-DM skipped.
- Owner research email: default NO (ordinary ready_for_brief). Tool-updates email: armed separately (upstream pending with newDetection).

Anti-recycle: 27.9 covered intake worksheet, quote packet, finish ladders, auto-fail QC, batchable organizers, desk-reset club. PR #405 (28.9, still OPEN) covered weekly ops calendar, material cover days, approval-event policy, sample-vs-production holds — **not** re-sold today. Prefer pickup windows, material-aware queue planning, staffed ETAs, and work-photo checklist.

## Same-day public research body

### 1. Fixed pickup windows instead of always-available door (fulfillment / owner time)
Sources:
- https://hackaday.com/2020/07/08/3d-printering-selling-prints-and-solving-the-pickup-problem/ — Hackaday, Donald Papp, published 2020-07-08, fetched live 2026-09-29.
- Supporting pattern (search index 2026 guides): define hold/no-show rules and labeled staging — EuroSaleOnline “Master Local Pickup Sales” (2026 guide) was Cloudflare-blocked on fetch; pattern noted only as corroboration, not as primary body.

Evidence: Local pickup looks “free” until schedules fail to match and the maker starts staying home for doorbells. Hackaday’s durable fix is **fixed pickup days/hours** (example in source: Tue/Thu evening windows) so the rest of the week stays productive. Self-serve lockbox is optional and location-dependent; VF already constrains to איסוף שדרות — the actionable part is publishing windows + a hold policy, not inventing nationwide shipping.

Action: map onto `vfops` / `vfsales` — short customer-facing pickup-window note + internal hold/no-show line on the ready→collected board. Distinct from freeze→print→QA→ready board work (28.9 PR, not main) — this is **calendar boundaries for handoff**, not production stages. No invented ₪.

Confidence: high for fixed-window discipline; medium for whether VF wants staffed windows only vs any self-serve assist.

Limitation: Hackaday piece is older (2020) but primary and still the clearest pickup-problem writeup; strip shipping/Paczkomat alternatives. EuroSale page blocked — do not over-cite.

### 2. Highest-impact filament/nozzle change first (queue planning)
Sources:
- https://simplyprint.io/blog/print-queue-scheduling/ — SimplyPrint, Albert Møller Nielsen, published 2026-06-24, fetched live 2026-09-29.
- https://printago.io/features/materials — Printago material-aware routing (product page, fetched 2026-09-29).

Evidence: SimplyPrint Queue v2’s To-Do list ranks the **single spool/nozzle/bed change that unlocks the most queued jobs**, instead of walking the farm guessing. Working-hours-aware ETAs stop pretending a 02:00 finish is “ready” when nobody clears beds until staffed morning. Printago’s material-aware routing states the same operator truth: jobs wait until a printer has a compatible filament loaded; exact color vs “any PLA” is an explicit matching choice.

Action: map onto `vfprod` / `vfsku` — morning floor checklist: (1) list jobs by loaded filament, (2) name the one change that unlocks the most waiting plates, (3) batch same-material runs before novelty one-offs. Pattern only — do **not** adopt SimplyPrint/Printago SaaS or RFID dependency. Distinct from 27.9 colour-batch SKU notes — this is **daily unlock ordering**, not catalog design.

Confidence: high for the unlock-first habit; low for any vendor ETA claim (18h/week survey is their marketing — not used as VF metric).

Limitation: Vendor blogs. Take the planning habit; ignore AutoPrint/lights-out and national-ship framing.

### 3. Staffed working hours on the board so “done” means pickup-ready
Sources:
- Same SimplyPrint Queue v2 article (2026-06-24), section “Working hours and real finish times”.

Evidence: A print that ends at 02:00 is not ready for customer pickup until someone clears the bed, QC’s, packs, and marks ready during staffed hours. Their queue shades unstaffed time so “until all done” reflects reality. For a pickup-only studio this maps cleanly: machine-done ≠ איסוף-מוכן.

Action: map onto `vfops` — two timestamps or states on the board: `print_finished` vs `ready_for_pickup`, with ready only after QC+pack during a staffed window. Aligns with finding #1 windows. No invented Insights/@velvets_cloud metrics.

Confidence: high for the two-state split; medium for exact Hebrew label wording.

Limitation: Same vendor source as #2; keep the state machine, drop farm-scale Gantt claims.

### 4. Repeatable product-photo checklist from real prints (content that sells)
Sources:
- https://printie.com/blog/2025-11-10-3d-print-product-photography — Printie, Tyler Reece, published 2025-11-10 (updated same day), fetched live 2026-09-29.

Evidence: Conversion-quality photos need consistent lighting, simple backdrop, **scale reference**, honest texture close-up, 3–4 fixed angles per SKU, batch shooting before tearing down the set, minimal edits, and one lifestyle/in-use frame. File naming by SKU+angle enables reuse across IG posts without re-shoots. Phone + soft light is enough; heavy filters hurt trust.

Action: map onto `vfgrowth` / `vfcopy` — standing “צילום מק״ט” checklist (hero / scale / texture / lifestyle) shot from **actual finished jobs** before pickup, not staged generic renders. Strip Printie fulfillment CTA. Distinct from older three-reel cadence notes — this is **per-SKU visual hygiene**, not posting calendar.

Confidence: high for the checklist; medium for how many angles VF needs per one-off custom vs repeat SKU.

Limitation: Printie is a fulfillment vendor. Take photography habits only; no outsourcing, no Etsy/ship framing. No invented engagement Insights.


## ממצאים — Top for the 09:00 brief
1. חלונות איסוף קבועים + מדיניות החזקה — `vfops`/`vfsales` (Hackaday pickup problem; איסוף שדרות).
2. שינוי חוט/זרבובית שמשחרר הכי הרבה עבודות קודם — `vfprod`/`vfsku` (SimplyPrint Queue v2 pattern / Printago material-aware; בלי SaaS).
3. `print_finished` ≠ `ready_for_pickup` עד QC+אריזה בחלון מאויש — `vfops`.
4. צ׳ק־ליסט צילום מק״ט מעבודות אמיתיות (hero/scale/texture/lifestyle) — `vfgrowth`/`vfcopy` (Printie photography 2025-11-10).

## Upstream watch (not in research.md summary)
- `python3 scripts/vf_upstream_watch.py check --write …/upstream-watch-latest.json` → summary: sources=95, pendingUpdates=40, newDetections=29, failed=0, autoUpgrade=false. checkedAt 2026-09-28T23:12:34Z (box UTC during run).
- Full review written to `upstream-review-latest.json` for all 40 pending (wait=7, review=1, ignore=32, update=0). Notable: bambulab/BambuStudio **wait** (head moved; latestRelease still v02.08.02.61; public beta 2.8.4 shrinkage warning + ADMesh fix documented at FilamentFeed 2026-09-24 — no auto-upgrade). OrcaSlicer **wait**. cognee **wait** (v1.6.1 pin; head commits). LinklyAI/best-skills **ignore** (consumed by Best Skills pass).
- `python3 scripts/vf_upstream_email.py render --arm --consume-notify` → armed=true enabled=true digest=a9941abf2a2310ad (pending=40). Delivery claimed only after workflow success + Gmail message ID.

## Best Skills
Due/executed. Ranking snapshot **2026-09-28**. Result: `no-embed-existing-coverage`. grill-with-docs (#6 best-100) is codebase/ADR interrogation — not a measured gap vs customer-facing `vfconvert/hq/GRILL.md` (grill-me). ui-taste remains watch. See `2026-09-29-best-skills.md`.

## MakerWorld
Tuesday → **לא יום סריקה**.

## Owner notify
- Research email: **NO**
- Tool-updates email: armed (separate path); see workflow outcome in seat report.

## Searches / sources log
1. WebSearch: small 3D printing studio operations workflow pickup Instagram 2026
2. WebSearch: 3D print shop batch scheduling filament changeover downtime 2025 2026
3. WebSearch: Bambu Studio 2.8.4 Public Beta shrinkage 2026
4. WebSearch: 3D print product photography Instagram maker studio
5. WebFetch: Hackaday pickup problem; SimplyPrint queue scheduling; Printago materials; Printie photography; FilamentFeed 2.8.4; LinklyAI best-100 + trending-7d CSVs 2026-09-28
6. EuroSaleOnline local-pickup guide: Cloudflare blocked — not used as primary evidence
7. PR #405 left OPEN/unmerged; not used as main research body
