# Research Seat · 2026-09-27

State: `ready_for_brief`
Observed run: 2026-09-27 ~02:05–02:25 Asia/Jerusalem (before 07:00 cutoff). Executor EXTRA findings appended ~02:10–02:20 Asia/Jerusalem (same branch / same ready_for_brief).
Seat: Velvet Research Seat
Path: live WebSearch/WebFetch + GitHub CLI shallow clone / `gh` failover (Cloud Agent launch blocked: Cursor usage exhausted / on-demand required). No chatgpt.com / gemini.google.com / perplexity.ai browser.

## Current authority / context
- Read AGENTS.md, instances/velvet-factory/AGENTS.md, packages/vfops/ROUTINE.md + LOOP.json, constitution/VISIBLE_TEXT.md, packages/vfresearch/DAILY.md, BEST-SKILLS.md/json, TIMER.md, hq/MAKERWORLD-SCAN.md, prior `research.md` (26.9), `2026-09-26-orchestra.md`.
- Best Skills: standingForever=true; `lastPass=2026-09-24` (~72h at this wake; due ≥44h, stale >52h) → **EXECUTED**. See `2026-09-27-best-skills.md` + BEST-SKILLS.json update.
- Official MakerWorld/Printables scan: **Sunday** → cadence sun+wed → **ran**. Primary pages Cloudflare-blocked («אין גוף»); candidates listed with UNPROVEN license. See `2026-09-27-makerworld-scan.md`.
- Social Intelligence: no policy-change signal; PUBLIC_CURRENT_CTA = Instagram message / איסוף שדרות. WhatsApp 050-2517000 desk-only. Auto-DM / keyword automation sources skipped.
- Owner email: default NO. Do not enable `packages/vfops/out/gmail-send-request.json`.

Anti-recycle: 20.9–26.9 already covered intake spine; acceptance/first-article; filament lot/label; quote-speed; written quote approval; deposit-after-quote; three-reel week; production handoff packet; pre-pickup automatic-fail QC; staffed hours+bed-clear; workflow-before-printers; PrusaSlicer 3.0 alpha; Bambu 2.8.4 Public Beta; drying temps; ColorMix/Lightweight; QC-before-cleanup; FPY/batching metrics; SUNLU; revision-delta after quote; prototype/pilot/production freeze; lead-time phases+buffer; 10-unit FPY gate; supports-on process frames; Best Skills 24.9 no-embed. Those are **not** re-sold today. **Extras skip (anti-recycle):** Versely weekly content engine + 25.9 three-reel Mon/Wed/Fri cadence — not re-opened as an EXTRA finding.

## Same-day public research body

### 1. Quote intake worksheet before price language hardens (inquiry→order)
Sources:
- https://www.goodprints3d.com/blogs/3d/gp3d-asset-01-quote-intake-worksheet-for-cleaner-3d-printing-quotes — GoodPrints3D, published 2026-04-24, fetched live 2026-09-27.
- Supporting: https://printcal.co/en/blog/3d-printing-briefing-checklist/ — PrintCal, published 2026-05-16, fetched 2026-09-27.

Evidence: Ugly quote threads usually start before pricing. GP3D Asset 01 gives an 8-block intake: buyer/job identity; what is being made; files/references/geometry; quantity and stage (exploratory / sample-first / pilot / production); material/finish/use; fit/tolerance/approval risk; timing/delivery; open risks before quoting. Route each request to quote / hold-for-more-info / discovery / sample-first **before** promising a number. PrintCal’s minimum briefing (file? function? critical dimension? quantity? finish? deadline?) is the short WhatsApp/DM form of the same habit — mark missing answers as estimate notes rather than fake-closed prices.

Action: map onto `vfconvert` / inquiry chain — standing Hebrew intake checklist (short for IG/WhatsApp, full worksheet for real custom jobs) that decides lane before any ₪ language. Distinct from 26.9 revision-delta (post-quote file change) and from earlier “quote-speed” notes — this is **pre-price completeness**. No invented ₪ fields as VF policy; structure only. Pickup-Sderot: delivery block = איסוף readiness, not carrier ship-to.

Confidence: high for the intake structure; medium for which VF jobs need the full 8-block vs the 6-question short form.

Limitation: GP3D is course-adjacent educational surface; PrintCal is a SaaS quote tool. Take the briefing habit, not a paid toolkit or national-ship framing.

### 2. Minimum quote packet — one controlling file + named revision (conversion quality)
Sources:
- https://www.goodprints3d.com/blogs/3d/what-to-send-for-a-custom-3d-printing-quote-files-specs-and-questions-that-speed-up-pricing — GoodPrints3D, published 2026-04-12, fetched 2026-09-27.

Evidence: A useful quote needs one clearly identified current file/reference package; part name + revision + quantity/variants; use environment; material/color/finish/delivered condition; critical dims/mating/acceptance; sample vs pilot vs production stage; packaging/label/inspection needs; destination + in-hand date. Name the request lane (print-ready / needs repair / no STL yet / prototype+later production) so the shop does not price production when the buyer needs design help. Prefer `part_revC_2026-07-18.step` over `final2.stl`. When STEP + STL + photo + drawing disagree, resolve or hold — do not price the conflict.

Action: map onto `vfconvert` / `vfsales` — customer-facing “מה לשלוח להצעה” note + internal checklist that refuses to treat a folder of unexplained attachments as quote-ready. Distinct from #1 (intake fields) — this is **attachment/revision hygiene**. No invented ₪.

Confidence: high for controlling-file discipline; medium for when VF should require STEP vs accept STL-only.

Limitation: Same educational surface; strip PO/barcode/enterprise receiving. Adapt destination to איסוף שדרות.

### 3. Surface-finish lanes before quote approval (owner situational + conversion)
Sources:
- https://www.goodprints3d.com/blogs/3d/what-surface-finish-to-expect-from-a-custom-3d-printed-part-before-you-approve-a-quote — GoodPrints3D, published 2026-04-12, fetched 2026-09-27.

Evidence: If finish matters, name it before approval. Default expectation for FDM is process-correct (layer lines, seams, support evidence), not injection-mold polish. Separate three lanes: (A) hidden/utility → functional finish OK; (B) customer-facing → controlled cosmetic with named visible faces; (C) presentation/photo sample → different commercial job, not a free upgrade. Quote must state included cleanup vs extra labor; one approved sample is not batch finish unless the approval note says what the sample proved. Finish often fails in packing (rubbing, labels on protected faces), not only on the bed.

Action: map onto `vfsales` / `vfconvert` / `vfprod` — three Hebrew finish-lane labels on the job card + “faces מוגנים” field before written approval. Distinct from 26.9 prototype/pilot/production stage freeze (release baseline) and from prior pre-pickup QC — this is **cosmetic scope language before price hardens**. No invented Insights.

Confidence: high for the three-lane pattern; medium for which VF products default to lane B.

Limitation: Buyer-education tone; take the naming habit. Packaging protection adapts to pickup handoff, not carrier transit.

### 4. Written automatic-fail QC list + packing that prioritizes breakage risk
Sources:
- https://printie.com/blog/2026-07-06-printie-qc-and-packing-standards-the-checks-every-order-passes-before-it-ships — Printie, published/updated 2026-07-06, fetched 2026-09-27.

Evidence: Core rule: if a defect risks function, structure, customer expectation, **or repeatability**, do not ship. Automatic fails (no judgment): collapsed/torn support zones, bed-adhesion fails, under-extrusion, distorting layer shifts, severe warping affecting fit/flatness/appearance, delamination, missing geometry, broken critical features, severe surface damage a reasonable customer would call defective, dimensional distortion. “Ship as-is” is never default; hesitation → escalate. Kickback outcomes: reprint / rework-only-if-fully-fixes / escalate / file-related failed-print path. Packing: lowest breakage risk beats material use, speed, and neatness; no free rattle; separate parts that can scuff; wrong box → change box. Repeat breakage → redesign pack for that product.

Action: map onto `vfprod` / pre-pickup path — publish a short automatic-fail list for floor + “היסוס = העלאה” + pickup bag rules (no rattle, protect thin features, separate cosmetic faces). Distinct from earlier generic “QC before cleanup” and from 25.9 pre-pickup fail notes — this adds a **named auto-fail inventory + packing priority**. No invented ₪ who-pays policy for VF; pattern only.

Confidence: high for the auto-fail + packing-priority pattern; medium for exact VF list wording (translate carefully).

Limitation: Printie is a fulfillment vendor publishing SOPs for trust. Take the inspection/pack rules, not outsourcing or ship-from-warehouse framing. Adapt “ship” → איסוף מוכן.

### 5. Batchable organizer SKUs + full cost stack (EXTRA)
Sources:
- https://layermath.com/blog/uk-etsy-seller-2400-per-month — LayerMath case study, published March 2026, fetched live 2026-09-27 (executor EXTRA).

Evidence: A lean UK Etsy seller (~£2,400/mo snapshot in the source) specialises in functional home organisers / desk accessories / small storage — not novelty one-offs. Nearly every SKU is flat-bed printable (low overhang risk), colour-batched on the same filament runs, and reuses the same G-code across orders. Pricing is built bottom-up: material + electricity + labour (setup/post/pack) + machine depreciation + marketplace fees — then sanity-checked against the market. Volume stays sane by grouping orders by colour/material, packing in blocks, and treating the farm as a batch machine rather than a project shop. Source quotes their own UK/Etsy £ figures; those are **not** VF prices.

Action: map onto `vfsku` (3–5 repeatable PLA/PETG organizer-class SKUs that share flat-bed / same-G-code habits) / `vfprod` (colour-run batch days + pack blocks) / `vfconvert` (full cost-stack fields: material, power, labour, depreciation, fees — structure only). **No invented ₪ amounts** and no invented SKU marketing names. Distinct from earlier FPY/batching metric notes — this is **catalog design + cost-stack discipline for repeatable organizers**.

Confidence: medium — pattern is clear; UK/Etsy fee and letterbox-mail framing do not transfer.

Limitation: Source is a UK Etsy marketplace case with LayerMath calculator CTA. VF is pickup/IG only (PUBLIC_CURRENT_CTA = Instagram message / איסוף שדרות). Strip Etsy fees, national shipping, and £ revenue claims; keep batchable-SKU + full cost-stack habits.

### 6. Tiny local pickup “desk reset” recurring SKU (EXTRA)
Sources:
- https://printie.com/blog/2025-10-29-3d-print-subscription-products — Printie, published 2025-10-29, fetched live 2026-09-27 (executor EXTRA).

Evidence: Subscriptions only work when the product is naturally recurring (replacement parts, consumable accessories, monthly theme packs). Cadence must be realistic and visible; deep discounts hurt margin; skip/pause/easy-cancel reduce chargebacks. Production foundation = repeatable SKUs, stable materials, clear lead times. Demand planning tip in source: keep ~two cycles of material buffer and pre-print a small next-cycle cushion when designs are stable. Fulfillment calendar should name freeze → print → QA → pack → ship as one moved unit. Example framing in source: a small “Monthly Desk Reset Pack” (cable clip / pen holder / desk hook class) that stays batchable. Start small; inconsistent fulfillment kills the model.

Action: map onto `vfsku` / `vfsales` as a **tiny local pickup club** (not a national shipping subscription) — one small desk-accessory cadence for איסוף שדרות, skip/pause friendly, no invented SKU name as LIVE. Map production rhythm onto `vfops`: freeze → print → QA → ready-for-pickup calendar (adapt “ship” → איסוף מוכן). Material buffer + small pre-print cushion when the design is frozen. Distinct from 25.9 three-reel content cadence (skipped as anti-recycle) — this is **physical recurring SKU ops**, not IG posting rhythm.

Confidence: medium-low — pattern is useful; Printie is a fulfillment SaaS selling outsourcing.

Limitation: Take the recurring-product + cadence + skip/pause + freeze→QA calendar habits. Do **not** adopt Printie outsourcing, national ship-from-warehouse, or invented ₪/subscriber metrics. Adapt fully to Sderot pickup + Instagram CTA.

### 7. Social Intelligence
Result: `nothing-solid` for @velvets_cloud policy change.

Observed 2026-09-27: Instagram auto-DM / keyword funnels continue to conflict with PUBLIC_CURRENT_CTA and no-auto-DM — **skipped**. No Insights invented.

### 8. MakerWorld / Printables scan (Sunday)
Ran. Primary MakerWorld + Printables model pages returned Cloudflare interstitials («אין גוף»). Search-index candidates recorded with **UNPROVEN** license in `2026-09-27-makerworld-scan.md`. SHELF: אין שם להציע. No invented model names as cleared commercial candidates.

### 9. Slicer watch (continuity only — not headline)
- Bambu Studio `v02.08.04.57` (2.8.4 Public Beta) published 2026-09-22T11:56:36Z — already briefed → **no re-sell**.
- PrusaSlicer `version_3.0.0-alpha12` published 2026-09-21T14:34:20Z — continuity only.
- OrcaSlicer latest official remains **v2.4.2** (2026-07-07). No new September 2026 official release observed via `gh api` 2026-09-27.

### 10. Best Skills (stale → executed)
`lastPass` 2026-09-24 → ~72h stale. Ranking snapshot dataDate **2026-09-26** (UTC README). Result: `no-embed-existing-coverage`. Details in `2026-09-27-best-skills.md`. BEST-SKILLS.json updated.

## ממצאים — Top for the 09:00 brief
1. Pre-price quote intake worksheet / short briefing form → vfconvert.
2. Minimum quote packet + one controlling revision → vfconvert/vfsales.
3. Three surface-finish lanes before approval → vfsales/vfconvert/vfprod.
4. Automatic-fail QC list + breakage-first packing for pickup → vfprod.
5. Batchable organizer SKUs + full cost stack (no invented ₪; pickup/IG only) → vfsku/vfprod/vfconvert. **EXTRA**
6. Tiny local pickup “desk reset” recurring SKU (skip/pause; freeze→print→QA→ready) → vfsku/vfsales/vfops. **EXTRA**
7. Best Skills: due/stale pulse executed; no-embed-existing-coverage (dataDate 26.9).
8. MakerWorld Sunday: Cloudflare; licenses UNPROVEN; אין שם להציע.
9. Skipped EXTRA: Versely weekly content engine / 25.9 three-reel Mon/Wed/Fri — anti-recycle.

## Searches performed (same-day)
- `small 3D printing business order intake checklist customer file requirements 2026`
- `3D print shop packaging finish standards customer photo approval local pickup 2026`
- `MakerWorld trending functional organizers household printables commercial license 2026`
- `Printables.com commercial license desk organizer tray free model September 2026`
- `site:github.com LinklyAI best-skills trending skills September 2026`
- WebFetch: GP3D Asset 01 intake · GP3D what-to-send · GP3D surface finish · Printie QC/packing 2026-07-06 · PrintCal briefing checklist · MakerWorld model 2064110 · Printables 1316736 / 996199 / 1639591 (all three Cloudflare)
- WebFetch EXTRA: LayerMath UK Etsy seller £2,400/mo case (Mar 2026) · Printie 3D print subscription products (2025-10-29)
- Search EXTRA: `3D print shop batchable organizer SKU full cost stack material electricity labour depreciation fees 2026` · `3D print subscription desk accessories local pickup recurring SKU cadence skip pause 2025 2026`
- gh api: bambulab/BambuStudio, prusa3d/PrusaSlicer, SoftFever/OrcaSlicer|OrcaSlicer/OrcaSlicer releases
- LinklyAI/best-skills README rankings Last updated 2026-09-26

## Skips
- Revision-delta / prototype-pilot-production / lead-time phases / 10-unit FPY / supports-on frames — anti-recycle from 26.9.
- **Versely weekly content engine EXTRA + 25.9 three-reel Mon/Wed/Fri** — skipped as anti-recycle (not re-sold as EXTRA).
- 26.9 themes — not recycled into EXTRA findings.
- Bambu 2.8.4 Public Beta + PrusaSlicer 3.0 alpha — continuity watch only.
- Instagram auto-DM / ManyChat — CTA + no-auto-DM locks.
- National shipping / Printie outsourcing pitch / invented ₪ / invented SKU marketing names / UK Etsy £ as VF prices.
- Clearing MakerWorld/Printables candidates without readable license — fail-closed.
- Inventing ₪, Insights, customers, Origin slugs, LIVE, shelf SKU names.
- Owner research email — not sent.
- Enabling gmail-send-request — left false / untouched.
- Cloud Agent launch: blocked on Cursor usage; GitHub CLI failover used.
- npx skills / second runtime.

## Best Skills note
Due=**true** / stale (~72h since `lastPass` 2026-09-24). Pass executed. `lastResult=no-embed-existing-coverage`. See companion artifact.

## Owner email
Default **NO**. Findings are Morning Brief consumer material only — not a research-path/tool stale fix and not a hard blocker.

## Cutoff / freshness
`ready_for_brief` — same-day external body with primary URLs + 6 actionable findings (4 base + 2 executor EXTRA: batchable organizer cost-stack; local pickup desk-reset club) + Best Skills due pulse + MakerWorld Sunday scan with honest Cloudflare/UNPROVEN licenses. Versely/three-reel EXTRA skipped (anti-recycle). Base body + EXTRA amend finished before 07:00 Asia/Jerusalem.

## Phase 9 engineering reconciliation

The zero-cost implementation branch also evaluated the current agent/tool ecosystem for a unique engineering gap. After reconciling against the fresher 2026-09-26 Best Skills snapshot, the decision remains `NO_ADDITIONAL_DEV_LAB_JUSTIFIED`: agent-browser/browser-use stay watch, ui-taste is covered by existing UI-quality controls, gh-cli-readonly-agent is covered by GitHub connector + local git, and no second runtime/scheduler/authority is introduced. Incremental recurring cost remains 0.
