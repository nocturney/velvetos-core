# Research Seat · 2026-09-27

State: `ready_for_brief`
Observed run: 2026-09-27 ~02:05–02:25 Asia/Jerusalem (before 07:00 cutoff).
Seat: Velvet Research Seat
Path: live WebSearch/WebFetch + GitHub CLI shallow clone / `gh` failover (Cloud Agent launch blocked: Cursor usage exhausted / on-demand required). No chatgpt.com / gemini.google.com / perplexity.ai browser.

## Current authority / context
- Read AGENTS.md, instances/velvet-factory/AGENTS.md, packages/vfops/ROUTINE.md + LOOP.json, constitution/VISIBLE_TEXT.md, packages/vfresearch/DAILY.md, BEST-SKILLS.md/json, TIMER.md, hq/MAKERWORLD-SCAN.md, prior `research.md` (26.9), `2026-09-26-orchestra.md`.
- Best Skills: standingForever=true; `lastPass=2026-09-24` (~72h at this wake; due ≥44h, stale >52h) → **EXECUTED**. See `2026-09-27-best-skills.md` + BEST-SKILLS.json update.
- Official MakerWorld/Printables scan: **Sunday** → cadence sun+wed → **ran**. Primary pages Cloudflare-blocked («אין גוף»); candidates listed with UNPROVEN license. See `2026-09-27-makerworld-scan.md`.
- Social Intelligence: no policy-change signal; PUBLIC_CURRENT_CTA = Instagram message / איסוף שדרות. WhatsApp 050-2517000 desk-only. Auto-DM / keyword automation sources skipped.
- Owner email: default NO. Do not enable `packages/vfops/out/gmail-send-request.json`.

Anti-recycle: 20.9–26.9 already covered intake spine; acceptance/first-article; filament lot/label; quote-speed; written quote approval; deposit-after-quote; three-reel week; production handoff packet; pre-pickup automatic-fail QC; staffed hours+bed-clear; workflow-before-printers; PrusaSlicer 3.0 alpha; Bambu 2.8.4 Public Beta; drying temps; ColorMix/Lightweight; QC-before-cleanup; FPY/batching metrics; SUNLU; revision-delta after quote; prototype/pilot/production freeze; lead-time phases+buffer; 10-unit FPY gate; supports-on process frames; Best Skills 24.9 no-embed. Those are **not** re-sold today.

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

### 5. Social Intelligence
Result: `nothing-solid` for @velvets_cloud policy change.

Observed 2026-09-27: Instagram auto-DM / keyword funnels continue to conflict with PUBLIC_CURRENT_CTA and no-auto-DM — **skipped**. No Insights invented.

### 6. MakerWorld / Printables scan (Sunday)
Ran. Primary MakerWorld + Printables model pages returned Cloudflare interstitials («אין גוף»). Search-index candidates recorded with **UNPROVEN** license in `2026-09-27-makerworld-scan.md`. SHELF: אין שם להציע. No invented model names as cleared commercial candidates.

### 7. Slicer watch (continuity only — not headline)
- Bambu Studio `v02.08.04.57` (2.8.4 Public Beta) published 2026-09-22T11:56:36Z — already briefed → **no re-sell**.
- PrusaSlicer `version_3.0.0-alpha12` published 2026-09-21T14:34:20Z — continuity only.
- OrcaSlicer latest official remains **v2.4.2** (2026-07-07). No new September 2026 official release observed via `gh api` 2026-09-27.

### 8. Best Skills (stale → executed)
`lastPass` 2026-09-24 → ~72h stale. Ranking snapshot dataDate **2026-09-26** (UTC README). Result: `no-embed-existing-coverage`. Details in `2026-09-27-best-skills.md`. BEST-SKILLS.json updated.

## ממצאים — Top for the 09:00 brief
1. Pre-price quote intake worksheet / short briefing form → vfconvert.
2. Minimum quote packet + one controlling revision → vfconvert/vfsales.
3. Three surface-finish lanes before approval → vfsales/vfconvert/vfprod.
4. Automatic-fail QC list + breakage-first packing for pickup → vfprod.
5. Best Skills: due/stale pulse executed; no-embed-existing-coverage (dataDate 26.9).
6. MakerWorld Sunday: Cloudflare; licenses UNPROVEN; אין שם להציע.

## Searches performed (same-day)
- `small 3D printing business order intake checklist customer file requirements 2026`
- `3D print shop packaging finish standards customer photo approval local pickup 2026`
- `MakerWorld trending functional organizers household printables commercial license 2026`
- `Printables.com commercial license desk organizer tray free model September 2026`
- `site:github.com LinklyAI best-skills trending skills September 2026`
- WebFetch: GP3D Asset 01 intake · GP3D what-to-send · GP3D surface finish · Printie QC/packing 2026-07-06 · PrintCal briefing checklist · MakerWorld model 2064110 · Printables 1316736 / 996199 / 1639591 (all three Cloudflare)
- gh api: bambulab/BambuStudio, prusa3d/PrusaSlicer, SoftFever/OrcaSlicer|OrcaSlicer/OrcaSlicer releases
- LinklyAI/best-skills README rankings Last updated 2026-09-26

## Skips
- Revision-delta / prototype-pilot-production / lead-time phases / 10-unit FPY / supports-on frames — anti-recycle from 26.9.
- Bambu 2.8.4 Public Beta + PrusaSlicer 3.0 alpha — continuity watch only.
- Instagram auto-DM / ManyChat — CTA + no-auto-DM locks.
- National shipping / Printie outsourcing pitch / invented ₪.
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
`ready_for_brief` — same-day external body with primary URLs + 4 actionable findings + Best Skills due pulse + MakerWorld Sunday scan with honest Cloudflare/UNPROVEN licenses, finished before 07:00 Asia/Jerusalem.
