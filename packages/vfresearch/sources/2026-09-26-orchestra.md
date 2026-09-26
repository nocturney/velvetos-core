# Research Seat · 2026-09-26

State: `ready_for_brief`
Observed run: 2026-09-26 ~02:01–02:25 Asia/Jerusalem (before 07:00 cutoff).
Seat: Velvet Research Seat
Path: live WebSearch/WebFetch + GitHub CLI shallow clone / `gh` failover (Cloud Agent launch blocked: Cursor usage exhausted / on-demand required). No chatgpt.com / gemini.google.com / perplexity.ai browser.

## Current authority / context
- Read AGENTS.md, instances/velvet-factory/AGENTS.md, packages/vfops/ROUTINE.md + LOOP.json, constitution/VISIBLE_TEXT.md, packages/vfresearch/DAILY.md, BEST-SKILLS.md/json, TIMER.md, prior `research.md` (25.9), `2026-09-25-orchestra.md`.
- Best Skills: standingForever=true; `lastPass=2026-09-24` (~47.4h at this wake; target ~48h) → **NOT due**. Leave BEST-SKILLS.json untouched.
- Official MakerWorld/Printables scan: **Saturday** → cadence sun+wed only → **skipped** (honest skip; no invented candidates / no fake makerworld artifact).
- Social Intelligence: no policy-change signal; PUBLIC_CURRENT_CTA = Instagram message / איסוף שדרות. WhatsApp 050-2517000 desk-only. Auto-DM / keyword automation sources skipped.
- Owner email: default NO. Do not enable `packages/vfops/out/gmail-send-request.json`.

Anti-recycle: 20.9–25.9 already covered intake spine; acceptance/first-article; filament lot/label; quote-speed; written quote approval; deposit-after-quote; three-reel week; production handoff packet; pre-pickup automatic-fail QC; staffed hours+bed-clear; workflow-before-printers; PrusaSlicer 3.0 alpha; Bambu 2.8.4 Public Beta; drying temps; ColorMix/Lightweight; QC-before-cleanup; FPY/batching metrics; SUNLU; Best Skills 24.9 no-embed. Those are **not** re-sold today.

## Same-day public research body

### 1. File change after quote = controlled commercial event (inquiry→order risk)
Sources:
- https://www.goodprints3d.com/blogs/3d/what-happens-if-you-change-the-file-after-a-3d-printing-quote-how-requotes-revisions-and-production-risk-usually-work — GoodPrints3D, published 2026-04-13, fetched live 2026-09-26.
- Supporting: https://www.goodprints3d.com/blogs/3d/should-a-3d-printing-quote-include-cancellation-and-change-fees — GoodPrints3D, published 2026-08-01, fetched 2026-09-26.

Evidence: A revised file does **not** inherit the old quote or sample approval even when the filename looks the same. Shop must treat the change as a commercial event: revision-delta packet (old→new file, plain-language delta, quantity/material/finish status, deposit/production status) + written confirm of price, schedule clock start, proof needs, committed work, and which revision is the only controlling production file. Impact lanes: identity-only / geometry / process / commercial / release. After production starts → stop-work + disposition, not silent overwrite. Aug 2026 companion: cancellation/change fees should follow release stage (inquiry → paid review → material release → capacity reserved → in progress), not a mystery penalty; change requests pause affected scope until a written change order is approved.

Action: map onto `vfconvert` / `vfsales` — after written quote approval (already briefed), add a **revision gate**: any new STL/STEP after quote or after sample requires a short delta note + written requote/confirm before beds are reserved. Pickup-Sderot adaptation: clock/disposition talk about איסוף readiness, not carrier ship. No invented ₪ fees as VF policy; pattern only. Distinct from 25.9 deposit-after-quote and 23.9 written approval.

Confidence: high for the public shop pattern; medium for which VF jobs need full delta vs light acknowledgment.

Limitation: Course-adjacent educational surface (JC Print Farm operator behind it). Take the revision-control habit, not a paid toolkit claim or US shipping framing.

### 2. Prototype vs pilot vs production — freeze baseline before batch
Sources:
- https://www.goodprints3d.com/blogs/3d/prototype-vs-production-runs-in-custom-3d-printing-how-to-plan-revisions-pricing-and-handoff-without-chaos — GoodPrints3D, published 2026-04-13, fetched 2026-09-26.

Evidence: Prototype buys learning; pilot buys repeatability/QC/pack evidence; production buys repeatable units against a named revision. Quantity alone does not define the stage. Freeze before production release: part/revision/controlling file(s), material+color, critical features, finish, delivered condition, quantity, packaging, destination. “Looks good” is not a release — approval must name what was checked, what passed, open items, and whether production is authorized. Silent prototype exceptions (hand-drill, extra sanding, unpriced bench work) must not become the unspoken production process. Compact production-release packet template is given in-source.

Action: map onto `vfconvert` / `vfprod` / `vfsales` — for custom commissions, separate “learning sample” from “released batch” in the job card; require named baseline before multi-unit or shelf-adjacent repeats. Distinct from 25.9 one-page handoff traveler (execution ownership) and from prior first-article notes — this is **stage language + written production release**. No ERP.

Confidence: high for the stage separation pattern; medium for when VF needs an explicit pilot between sample and batch.

Limitation: Same educational surface; strip national-ship / PO enterprise framing. No invented sample ₪.

### 3. Lead-time SLA: phases + buffer + pickup adaptation
Sources:
- https://printie.com/blog/2025-10-25-3d-print-fulfillment-lead-times-sla — Printie, published/updated 2025-10-25, fetched 2026-09-26.
- https://cc3dlabs.com/local-3d-printing-turnaround-expectations/ — Cc3D Labs (local shop near Philadelphia), observed live 2026-09-26.

Evidence: Separate **production time** from transit; customers confuse them. Baseline window you can hit ~90% of the time + intentional buffer (avg 3 days → promise 4–6). Rush only when capacity allows + fee + skips batching. Communicate delays before customers ask. Cutoff time for same-day processing. Track promised vs actual. Cc3D local chain: quote → file review → admin → queue → machine → post → **shipping or local pickup**; pickup eliminates the last phase. Buyers wrongly treat the whole chain as “print time.” Phase-specific updates (“when production starts / print finishes / ready for pickup”) beat “when will it be done?”

Action: map onto `vfsales` / `vfops` owner situational awareness — quote/job messages name production window + איסוף שדרות readiness (not carrier SLA). Distinct from 25.9 staffed-hours+bed-clear (internal ETA honesty) — this is **customer-facing phase language + buffer**. No invented day counts as VF policy; pattern only. No nationwide shipping SOP.

Confidence: high for phase separation + pickup advantage; medium for which numeric window VF should publish (אין ספירה).

Limitation: Printie is a fulfillment vendor; Cc3D is a local US shop. Take the communication structure, not outsourcing or invented VF lead-time numbers.

### 4. Ten-unit FPY gate + bottleneck capacity before catalog growth
Sources:
- https://printie.com/blog/2026-01-31-3d-printing-business-from-home — Printie, published 2026-01-31, updated 2026-07-22, fetched 2026-09-26.

Evidence: Before expanding catalog, build **one** repeatable SKU production packet (immutable revision, profile/orientation, material/colors, critical dims+method, appearance limits, post steps, pack, labor minutes, reprint/defect codes). Run **ten consecutive units**; record print time, hands-on, material, failures, finishing — do not average away failures. FPY = units passing without rework ÷ units started. Fix dominant failure before adding listings. Capacity from bottleneck step (finishing can cap shipments even when printers idle). Sell ≤ ~70–80% of demonstrated bottleneck capacity until variation is measured (operating buffer example, not industry standard). Order board: ID, promised date, SKU/revision, status, exception owner.

Action: map onto `vfsku` / `vfprod` — evergreen candidates earn a 10-unit measured pass before they are treated as “easy recurring.” Distinct from earlier FPY/batching metric notes and from 25.9 workflow-before-printers — this adds a **concrete SKU validation gate + bottleneck math**. No invented SKU names / ₪ / Origin slugs.

Confidence: high for the 10-unit + bottleneck pattern; medium for which VF products enter the gate first (אין ספירה).

Limitation: Home-business / Printie outsourcing pitch — take the operating test only. Percent buffers are examples, not VF policy.

### 5. Behind-the-scenes with supports still on (content from real work)
Sources:
- https://www.linkedin.com/posts/layered-shape_3dprinting-bambulab-filmprops-activity-7498665742079393792-DYQ- — Layered Shape, observed via public index 2026-08-27 content, researched 2026-09-26.
- Supporting studio-curtain framing: https://www.linkedin.com/feed/update/urn:li:activity:7477802753780649984 — Layered Shape, 2026-06-30, observed 2026-09-26.

Evidence: Small local studio content that shows craft mid-process (supports still on, cleanup ahead) + “most people don’t realise what’s behind every order” studio-curtain posts. Pattern: unfinished-process frames build trust without inventing Insights; finished polish alone hides the work. No follower/conversion numbers adopted as VF Insights.

Action: map onto `vfgrowth` / `vfcovers` — occasional Stories/feed frames from real jobs **before** cleanup (supports on, bed clear, hand finishing) as a complement to finished reveals. CTA remains Instagram message / איסוף שדרות. Distinct from 25.9 Mon/Wed/Fri three-reel roles — this is a **process-visibility** habit inside existing content, not a new cadence. No boost, no auto-DM.

Confidence: medium for the content pattern; low for any engagement claims (discard).

Limitation: LinkedIn reshared posts; UK studio with shipping business model. Take the craft-visibility idea only.

### 6. Social Intelligence
Result: `nothing-solid` for @velvets_cloud policy change.

Observed 2026-09-26: Instagram auto-DM / keyword funnels continue to conflict with PUBLIC_CURRENT_CTA and no-auto-DM — **skipped**. No Insights invented.

### 7. MakerWorld scan
Saturday — outside sun+wed cadence. **Skipped.** No candidate list invented. No fake makerworld artifact.

### 8. Slicer watch (continuity only — not headline)
- Bambu Studio `v02.08.04.57` (2.8.4 Public Beta) published 2026-09-22T11:56:36Z — already briefed 23.9/24.9/25.9 → **no re-sell**.
- Bambu Studio `v02.08.03.66` (2.8.3 Public Beta) published 2026-09-08 — older; not a new 26.9 headline.
- PrusaSlicer `version_3.0.0-alpha12` published 2026-09-21T14:34:20Z — already noted → **continuity only**.
- OrcaSlicer latest official remains **v2.4.2** (2026-07-07). No September 2026 official release observed via `gh api` 2026-09-26.

## ממצאים — Top for the 09:00 brief
1. Revision-delta gate after quote/sample when the file changes → vfconvert/vfsales.
2. Prototype / pilot / production stage freeze + written production release → vfconvert/vfprod.
3. Customer-facing lead-time phases + buffer; pickup readiness not “print time” → vfsales/vfops.
4. Ten consecutive units FPY gate + bottleneck capacity before catalog growth → vfsku/vfprod.
5. Mid-process craft frames (supports still on) as content from real jobs → vfgrowth.
6. Best Skills: not due (~47h since 24.9). MakerWorld skipped (Saturday).

## Searches performed (same-day)
- `3D print shop revision control file version customer approval 2026`
- `small 3D printing business first pass yield reprint threshold policy 2026`
- `Bambu Studio OR PrusaSlicer OR OrcaSlicer release September 2026`
- `3D print studio Instagram Stories behind the scenes pickup local maker 2026`
- `3D printing business material moisture drying log filament inventory 2026` (apps/tools — no solid VF office embed; noted skip)
- `made to order 3D print shop lead time communication template customer expectation 2026`
- `3D print custom order scope freeze change order fee written approval 2026`
- WebFetch: GP3D file-after-quote · GP3D prototype-vs-production · GP3D cancellation/change fees · Printie lead-time SLA · Printie home-business 2026-01-31 · Cc3D local turnaround
- gh api: bambulab/BambuStudio, prusa3d/PrusaSlicer, OrcaSlicer/OrcaSlicer releases

## Skips
- Deposit-after-quote / three-reel week / handoff packet / pre-pickup QC / staffed hours / workflow-before-printers / written approval / quote-speed / FPY metric-only notes — anti-recycle.
- PrusaSlicer 3.0 alpha + Bambu 2.8.4 Public Beta — continuity watch only, not re-sold.
- Filament tracker app installs (Spoolio/Spool Buddy/etc.) — no measured VF inventory gap requiring a new tool; moisture/lot already covered earlier weeks.
- Instagram auto-DM / ManyChat — CTA + no-auto-DM locks.
- National shipping / Printie outsourcing pitch / invented ₪ change fees.
- MakerWorld body — Saturday off-cadence; no fake artifact.
- Inventing ₪, Insights, customers, Origin slugs, LIVE, shelf SKU names.
- Owner research email — not sent.
- Enabling gmail-send-request — left false / untouched.
- BEST-SKILLS.json — not due; untouched.
- Cloud Agent launch: blocked on Cursor usage; GitHub CLI failover used.

## Best Skills note
Due=**false** (~47.4h since `lastPass` 2026-09-24; target ~48h; stale only after ~52h). No pass. BEST-SKILLS.json untouched.

## Owner email
Default **NO**. Findings are Morning Brief consumer material only — not a research-path/tool stale fix and not a hard blocker.

## Cutoff / freshness
`ready_for_brief` — same-day external body with primary URLs + 5 actionable findings + Best Skills not-due note + MakerWorld Saturday skip, finished before 07:00 Asia/Jerusalem.
