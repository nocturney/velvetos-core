# Research Seat · 2026-09-28

State: `ready_for_brief`
Observed run: 2026-09-28 ~02:09–02:25 Asia/Jerusalem (before 07:00 cutoff).
Seat: Velvet Research Seat
Path: live WebSearch/WebFetch + GitHub CLI shallow clone / `gh` failover (Cloud Agent launch blocked: Cursor usage exhausted / on-demand required). No chatgpt.com / gemini.google.com / perplexity.ai browser.

## Current authority / context
- Read AGENTS.md, instances/velvet-factory/AGENTS.md, packages/vfops/ROUTINE.md + LOOP.json, constitution/VISIBLE_TEXT.md, packages/vfresearch/DAILY.md, HQ-ROUTINE.md, BEST-SKILLS.md/json, TIMER.md, hq/MAKERWORLD-SCAN.md, prior `research.md` (27.9), `2026-09-27-orchestra.md`.
- Best Skills: standingForever=true; `lastPass=2026-09-27` (~23.8h at this wake; due ≥44h, stale >52h) → **SKIPPED (not due)**. BEST-SKILLS.json untouched.
- Official MakerWorld/Printables scan: **Monday** → cadence sun+wed → **«לא יום סריקה»**. No makerworld-scan artifact.
- Social Intelligence: no policy-change signal; PUBLIC_CURRENT_CTA = Instagram message / איסוף שדרות. WhatsApp 050-2517000 desk-only. Auto-DM / keyword automation sources skipped (constitution).
- Owner email: default NO. Do not enable `packages/vfops/out/gmail-send-request.json`.

Anti-recycle: 20.9–27.9 already covered intake spine; acceptance/first-article checklists; filament lot/label; quote-speed; written quote approval; deposit-after-quote; three-reel week; production handoff packet; pre-pickup automatic-fail QC + packing priority; staffed hours+bed-clear; workflow-before-printers; PrusaSlicer 3.0 alpha; Bambu 2.8.4 Public Beta; drying temps; ColorMix/Lightweight; QC-before-cleanup; FPY/batching metrics; SUNLU; revision-delta after quote; prototype/pilot/production freeze; lead-time phases+buffer; 10-unit FPY gate; supports-on process frames; quote intake worksheet; min quote packet; finish lanes; batchable organizer SKUs; desk-reset club; Best Skills 24.9/27.9. Those are **not** re-sold today.

## Same-day public research body

### 1. Weekly operations calendar — three horizons + weekday risk themes + safe-start
Sources:
- https://printie.com/blog/2025-11-14-3d-printing-operations-calendar — Printie, published 2025-11-14, updated 2026-07-22, fetched live 2026-09-28.
- Supporting: https://printie.com/blog/2025-12-10-production-scheduling-for-3d-print-sellers-from-queue-chaos-to-predictable-ship- — Printie scheduling companion (search hit 2026-09-28; pattern only).

Evidence: A useful ops calendar protects delivery promises first, then reserves explicit windows for material, maintenance, packing, and one improvement experiment. Three linked horizons: **Today** (what must start/finish — order, SKU, safe-start time, runtime, station, blocker); **This week** (capacity/material/packing sufficiency — hours sold/available, due units, reprint reserve, material cover); **Next 4–12 weeks** (known demand/capacity shocks). Latest safe start = promised handoff minus production duration minus QC/pack time minus reprint allowance — not “order received.” Short open (15m) / mid (10m) / close (15m) checks beat long production meetings. Example weekday risk themes (movable if a day is the busiest handoff day): Mon demand/capacity; Tue material control; Wed quality review → **one** corrective experiment; Thu maintenance from manufacturer evidence; Fri packing/inventory audit. Capacity table needs gross / protected downtime / reprint reserve / committed / free per resource class (printer hours ≠ finishing hours ≠ packed orders). Maintenance is evidence-triggered (nozzle change, collision, dimensional drift), not “recalibrate every Monday.”

Action: map onto `vfops` Office Loop / HANDOFF — Hebrew weekly rhythm card with three horizons + safe-start fields on the job queue + one Wednesday quality experiment slot. Adapt “ship” → איסוף readiness. Distinct from prior lead-time buffer notes and from bed-clear/staffed-hours — this is **calendar rhythm + capacity table + safe-start math**. No Printie outsourcing; no national shipping framing.

Confidence: high for the three-horizon + safe-start pattern; medium for which weekday VF should protect (shop hours vary).

Limitation: Printie is a fulfillment vendor publishing seller SOPs. Take the rhythm and capacity discipline; strip Shippo/ShipStation and storefront-ship assumptions.

### 2. Material cover days + reorder points — filament/hardware/packaging as working capital
Sources:
- https://3dprinting.zone/managing-filament-and-resin-inventory-in-a-busy-print-bureau/ — Kinsoft / 3D Printing Zone, published 2026-07-15, fetched live 2026-09-28.
- https://print-pulse.app/3d-printing-inventory-management — PrintPulse product page, fetched live 2026-09-28 (pattern only; no install).
- Supporting formula in Printie ops calendar (same fetch as #1): `material cover (days) = usable material on hand ÷ average daily usage`; flag cover shorter than supplier lead time + buffer.

Evidence: Stockouts stall paid work; overstock ties cash and raises spoilage. Reorder point for each regular material = average weekly consumption × supplier lead time + Friday-afternoon buffer; review quarterly as mix drifts. Opened-spool storage/drying remains process (if you cannot vouch for storage, dry before a critical job) — but today’s signal is **reorder math**, not drying temperatures. Inventory is broader than filament: hardware (magnets, inserts, screws) and packaging (bags, labels, cartons) belong in the same table with unit, on-hand, reorder point, landed cost, location. Transaction discipline beats month-end counting: receive on check-in, deduct on build/pick, investigate negative stock and below-reorder before quoting surprises. A quote that prices only filament while the BOM needs magnets/screws/cartons understates cost and readiness.

Action: map onto `vfprod` / `vfsku` / `vfconvert` — short shelf card for core PLA/PETG colours + any hardware/packaging used on repeat jobs: on-hand, reorder point, cover days, location. Quote checklist field: “BOM materials available?” before promising איסוף. **No invented ₪ amounts**; structure and cover/reorder fields only. Distinct from prior filament lot/label and drying-temp notes, and from 27.9 full cost-stack for organizers — this is **reorder + cover + non-filament BOM stock**. Do not install PrintPulse / farm SaaS (NO_NEW_RECURRING_COST); pattern in existing packs.

Confidence: high for reorder-point + cover-days habit; medium for how many VF colours/hardware lines need active tracking today.

Limitation: Kinsoft is an AU bureau blog; PrintPulse is SaaS marketing with € example costs — those figures are **not** VF prices. Strip resin shelf-life if VF stays FDM-primary; keep the reorder/cover and hardware/packaging classes.

### 3. Approval event vs quote revision vs design revision vs requote (policy language)
Sources:
- https://www.goodprints3d.com/blogs/3d/gp3d-asset-06-approval-and-revision-policy-template-for-custom-3d-printing-jobs — GoodPrints3D Asset 06, published 2026-04-24, fetched live 2026-09-28.
- https://www.goodprints3d.com/blogs/3d/how-many-revisions-are-normal-before-a-custom-3d-printing-quote-becomes-final — GoodPrints3D, published 2026-04-19, fetched live 2026-09-28.

Evidence: Buyer enthusiasm is not approval. Define the exact event that counts as approval; state what is being approved (file version, material, finish, quantity, timing assumptions, sample requirement); spell out what after-approval changes become paid revisions, timing resets, or a fresh quote; use the same language in quote, approval request, and follow-ups. One or two quote revisions are normal; the control is change impact, not revision count. Separate **quote revision** (commercial clarification of a substantially defined job) from **design revision** (geometry/manufacturing problem changed — often requote). Requote triggers: new geometry, material family change, fit-critical dims, new cosmetic standard, major quantity change, new hardware/assembly, accelerated date. When a thread reaches revision three/four, send a compact **delta packet**: new controlling revision; list of changes since last priced baseline; what did not change; next decision class (budgetary / prototype / first-article / production-ready); which prior price/lead/approval assumptions remain valid. Final quote must stand alone (not “same as April email except…”) and name the next authorization gate.

Action: map onto `vfconvert` / `vfsales` — Hebrew one-pager “מדיניות אישור ושינויים” for IG/WhatsApp custom jobs + internal delta-packet template. Distinct from 26.9 revision-delta (post-quote file change mechanics) and from 27.9 intake/min-quote-packet — this is **approval-event definition + requote triggers + reset packet**. No invented ₪ for paid-change rates; boundary language only.

Confidence: high for the separation of approval / quote revision / design revision / requote; medium for which VF job types get the full policy vs a three-line DM version.

Limitation: Educational/course surface behind GoodPrints; take the policy structure, not a paid toolkit or national-ship destination fields. Adapt destination to איסוף שדרות.

### 4. Sample approved + production still on hold — two written decisions
Sources:
- https://www.goodprints3d.com/blogs/3d/can-you-approve-a-3d-printing-sample-and-still-keep-production-on-hold-until-a-separate-written-release — GoodPrints3D, published 2026-04-20, fetched live 2026-09-28.

Evidence: Sample approval and production release are often owned by different people/questions. Blunt hold language when needed: sample approved for review/validation; production remains on hold pending separate written release; do not begin quantity build until that release; current revision is sample reference only unless instructed otherwise. Later release must name quantity/lot, revision/material/finish, pending pack/label items, timing window, and who issued/can stop the release — not a vague “go ahead.” Situations: fit confirmed but timing open; technical yes but spend not released; field feedback wanted first; packaging/marking still open. Distinct from first-lot release (some quantity starts) and from sample-only wording at the front edge.

Action: map onto `vfsales` / `vfconvert` / `vfops` job card — two Hebrew message templates: (A) sample OK + production hold; (B) written production release checklist. Distinct from earlier first-article checklist coverage and from stage freeze (prototype/pilot/production) — this is the **explicit hold after a passed sample**. No auto-DM; human WhatsApp/IG send only.

Confidence: high for the two-decision pattern; medium for how often VF custom jobs need the hold vs auto-release after sample.

Limitation: Same educational surface; strip enterprise purchasing roles — for VF the “purchasing/release owner” is usually Christian or the named customer contact.

### 5. Skipped / walls
- Best Skills: not due (~23.8h < 44h).
- MakerWorld/Printables: Monday ≠ scan day.
- WhatsApp Business API / OrderPilot-style pickup automation: skipped — customer WhatsApp send stays human; auto-DM forbidden; PUBLIC_CURRENT_CTA = Instagram message.
- Bambu Farm Manager / PrintPulse / 3D Print Manager installs: skipped (NO_NEW_RECURRING_COST; Print from HQ locked; pattern notes only where used above).
- chatgpt.com / gemini.google.com / perplexity.ai: not opened.

## Cadence scripts (run in clone after write)
```bash
python3 scripts/vfresearch_cadence.py freshness
```

## Resolution
`ready_for_brief` — four concrete findings with live URLs, mapped to existing packs, anti-recycle checked. Owner email not warranted (routine improvements, not a research-path blocker or major course correction).

## ממצאים — Top for the 09:00 brief
1. Weekly ops calendar — three horizons + safe-start + weekday risk themes → vfops.
2. Material cover days + reorder points for filament/hardware/packaging → vfprod/vfsku/vfconvert (no invented ₪; no inventory SaaS install).
3. Approval-event policy — quote revision vs design revision vs requote + delta packet → vfconvert/vfsales.
4. Sample approved + production still on hold — two written decisions → vfsales/vfconvert/vfops.
5. Best Skills: not due (~24h since 27.9) — skipped; BEST-SKILLS.json untouched.
6. MakerWorld/Printables: Monday — «לא יום סריקה».

## Searches performed (same-day)
- `small 3D print shop operations checklist 2026 pickup local studio filament inventory reorder point`
- `custom 3D printing shop customer communication revision control after sample approval 2026`
- `Bambu Lab OrcaSlicer PrusaSlicer update September 2026 release notes small farm`
- `Instagram Reels content from real 3D print jobs local pickup studio 2026 case study`
- `site:goodprints3d.com sample approval first article custom 3D printing 2026`
- `3D print shop pickup readiness notification customer WhatsApp Instagram local studio process 2026`
- `3D printing shop reprint reserve capacity planning safe start time promised handoff 2026`
- WebFetch: Printie ops calendar (updated 2026-07-22) · Kinsoft filament inventory (2026-07-15) · GP3D Asset 06 approval policy · GP3D how-many-revisions · GP3D sample approved + production hold · PrintPulse inventory page (pattern only)

## Skips
- Best Skills pass — not due (~23.8h < 44h).
- MakerWorld/Printables scan — Monday ≠ sun+wed.
- First-article checklist / revision-delta / finish lanes / auto-fail QC / organizer SKUs / desk-reset — anti-recycle from 20.9–27.9.
- WhatsApp Business API / OrderPilot pickup automation — human WhatsApp send + no auto-DM.
- Bambu Farm Manager / PrintPulse / 3D Print Manager installs — NO_NEW_RECURRING_COST; Print from HQ locked.
- National shipping / invented ₪ / invented Insights / invented customers / Origin slugs / LIVE.
- Owner research email — not sent.
- Enabling gmail-send-request — left false / untouched.
- Cloud Agent launch: blocked on Cursor usage; GitHub CLI failover used.
- npx skills / second runtime / chatgpt.com / gemini.google.com / perplexity.ai browser.

## Best Skills note
Due=**false** (~23.8h since `lastPass` 2026-09-27). Pass skipped. `BEST-SKILLS.json` untouched (`lastResult=no-embed-existing-coverage`, `dataDate=2026-09-26`).

## Owner email
Default **NO**. Findings are Morning Brief consumer material only — not a research-path/tool stale fix and not a hard blocker.

## Cutoff / freshness
`ready_for_brief` — same-day external body with primary URLs + 4 actionable findings + Best Skills not-due skip + MakerWorld Monday skip («לא יום סריקה»). Finished before 07:00 Asia/Jerusalem.
