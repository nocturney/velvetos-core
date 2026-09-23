# Research Seat · 2026-09-23

State: `ready_for_brief`
Observed run: 2026-09-23 ~02:10–02:45 Asia/Jerusalem (before 07:00 cutoff).
Seat: Velvet Research Seat
Path: live WebSearch/WebFetch + GitHub MCP artifact write (Cloud Agent launch blocked: Cursor usage exhausted / on-demand required). No chatgpt.com / gemini.google.com / perplexity.ai browser.

## Current authority / context
- Read AGENTS.md, instances/velvet-factory/AGENTS.md, packages/vfops/ROUTINE.md, LOOP.json, constitution/VISIBLE_TEXT.md (referenced), packages/vfresearch/DAILY.md, HQ-ROUTINE.md, TIMER.md, BEST-SKILLS.json, MAKERWORLD-SCAN.md, prior `research.md` (22.9), and `2026-09-22-orchestra.md` from current main.
- Best Skills: standingForever=true; `lastPass=2026-09-22` (~24h at this wake) → **not due** (target 48h + 4h grace). No best-skills pass this run; no BEST-SKILLS.json mutation.
- Official MakerWorld/Printables scan: **Wednesday** → due. Separate artifact `2026-09-23-makerworld-scan.md`. MakerWorld HTML blocked by Cloudflare («אין גוף» on direct fetch); candidates recorded from public search index with license UNPROVEN until `vlicense` GATE. No shelf names invented.
- Social Intelligence: no policy-change signal; PUBLIC_CURRENT_CTA unchanged.
- Owner email: default NO. Do not enable `packages/vfops/out/gmail-send-request.json`.

Anti-recycle: 20.9–22.9 already covered PrusaSlicer 3.0 preview, custom-order intake checklist, FPY/batching metrics, Prusament PLA Lightweight, ColorMix, MakerWorld Make for Good, early QC-before-cleanup, wet-area organizers, pickup tick+shelf, Bambu filament price cut, SUNLU PETG moisture. Those are **not** re-sold today.

## Same-day public research body

### 1. Bambu Studio 2.8.4 Public Beta (22.9) — top-surface path + shop UX (floor watch)
Sources:
- https://github.com/bambulab/BambuStudio/releases — tag `v02.08.04.57`, released 22 Sep 2026 ~11:56 (observed 2026-09-23). Primary GitHub releases page.
- Related prior beta context (not the headline): https://forum.bambulab.com/t/bambu-studio-v2-8-3-public-beta/259574 — 2.8.3 Public Beta notes 10 Sep 2026 (first-layer infill line width, wipe-tower auto placement) — observed 2026-09-23.
- Stable production baseline remains 2.8.2.x Public Release per same releases page; betas note 3MF from Beta temporarily not uploadable to MakerWorld.

Evidence: Same-day-adjacent GitHub pre-release `2.8.4 Public Beta` focuses on UX/performance: texture-import UI/stability, delete prompts to prevent accidental filament/model ops, smoother Cut tool + Device page, and a slicing-engine change that optimizes **top-surface monotonic line infill** paths to reduce travel (more noticeable on detailed tops). 2.8.3 beta (already out 10.9) remains the source for independent initial-layer infill line width (example: 0.55 mm on 0.4 mm nozzle) and automatic wipe-tower placement when switching printers / auto-arrange.

Action: **floor watch / optional beta try beside production profile** — not a production-slicer mandate. Distinct from 20.9 PrusaSlicer 3.0 preview. Do not claim VF printers upgraded. No Print from HQ. Prefer waiting for Public Release before any standing floor profile change.

Confidence: high for release existence and stated features (GitHub primary); low for VF measured time savings (no local bench yet).

Limitation: Beta; MakerWorld upload restriction for Beta 3MF; production shops should keep a stable channel.

### 2. Written quote approval before production — conversion gate (not intake checklist recycle)
Sources:
- https://apex3dprint.com/3d-print-quote-approval-workflow/ — Apex 3D Print Lab, 2026-04-11, observed 2026-09-23.
- Supporting (same vendor family): https://apex3dprint.com/3d-print-order-checklist/ — observed 2026-09-23.
- Supporting sequence framing: https://laticy.com/repeatable-custom-order-workflow/ — observed 2026-09-23.

Evidence: Small-seller quote workflow: capture request → review specs → estimate → send quote that lists price assumptions, lead time, and **revision limits** → get **written confirmation** → only then lock files and start production. Explicit failure modes: starting production without approval; unclear revision scope; rushed deadlines. Pickup/shipping is a quote field, not a national-shipping push.

Action: map onto existing `vfsales` / `vfconvert` quote path as an office habit — **no print / no filament commit until written approval** (Instagram message thread counts as written). Distinct from 20.9 intake checklist (what to capture) — this is the **gate before the bed starts**. Keep PUBLIC_CURRENT_CTA; no auto-DM; no invented ₪.

Confidence: medium for the operations pattern (commercial blogs); high that it fits VF locks without new pack.

Limitation: vendor marketing tone; take the gate, not their software stack or calculator prices.

### 3. Filament drying by material TDS — Prusa Knowledge Base temperatures
Sources:
- https://help.prusa3d.com/article/drying-filament_332086 — Prusa Knowledge Base, observed 2026-09-23 (primary).

Evidence: Hygroscopic materials need manufacturer/TDS temperatures — not a universal dryer setting. Documented Prusament examples include PLA/rPLA 45 °C / 6 h; PETG 55 °C / 6 h; TPU 60 °C / 4–6 h; PA11-CF 90 °C / 6 h. Prevention via sealed storage + desiccant preferred; XL multi-tool idle heat makes moisture more critical. New Prusament spool designs tolerate higher drying temps than older cardboard-core black spools (old black: caution above ~45 °C without screw).

Action: map onto `vfprod` filament handling / floor SOP — dry by material table; label spool after dry; do not invent a new dryer SKU or HQ Print job. Distinct from prior SUNLU PETG moisture product note (21.9) — this is the **temperature/time table** habit.

Confidence: high for vendor-stated temps; medium for VF local RH (אין ספירה).

Limitation: home ovens swing; follow filament TDS over blog shortcuts.

### 4. Social Intelligence
Result: `nothing-solid` for @velvets_cloud policy change.

Observed 2026-09-23: Instagram auto-reply / Meta Inbox Automations / form-in-bio funnels continue to conflict with PUBLIC_CURRENT_CTA = Instagram message / איסוף שדרות and the no-auto-DM lock — skipped. No Insights invented. No change to content reset / preflight.

### 5. MakerWorld scan (Wednesday)
See `packages/vfresearch/sources/2026-09-23-makerworld-scan.md`. Candidates URL-only; license UNPROVEN (Cloudflare blocked model pages); no SHELF.json names; no ₪.

## ממצאים — Top for the 09:00 brief
1. Bambu Studio 2.8.4 Public Beta (22.9 GitHub) — top-surface monotonic path travel reduction + UX; floor watch only; stable remains 2.8.2.x.
2. Written quote approval before production — map to vfsales/vfconvert; Instagram thread OK as written; no auto-DM.
3. Prusa KB filament drying temps (PLA 45/6h, PETG 55/6h, …) — vfprod habit; not a new product buy from HQ.
4. Wed MakerWorld scan ran; licenses blocked/unproven → no shelf fill.
5. Best Skills not due (`lastPass` 2026-09-22).

## Searches performed (same-day)
- `3D printing news September 2026 Prusa Bambu MakerWorld filament release`
- `small 3D print shop pickup order workflow checklist 2026`
- `MakerWorld Printables trending useful printable organizers September 2026`
- `PrusaSlicer Bambu Studio update September 2026`
- `Bambu Studio 2.8.3 beta first layer infill wipe tower September 2026`
- `Bambu Studio 2.8.4 release September 2026`
- `Instagram local service business inquiry quote deposit before production no auto DM 2026`
- `3D printing filament dryer humidity shop SOP September 2026`
- `site:makerworld.com parametric sorting trays organizer free commercial use 2026`
- WebFetch: BambuStudio GitHub releases · Bambu 2.8.3 forum · Apex quote-approval · Prusa drying KB · MakerWorld model URL (Cloudflare block)

## Skips
- MakerWorld Make for Good / Prusament ColorMix / Lightweight / early QC-before-cleanup — prior days.
- PrusaSlicer 3.0 preview — already covered 20.9; no newer production claim.
- Link-in-bio form CTA / Instagram auto-DM — CTA + auto-DM locks.
- Inventing commercial license for Cloudflare-blocked MakerWorld pages.
- Best Skills pass — not due.
- Owner research email — not sent.
- Enabling gmail-send-request — left false.
- Cloud Agent launch: blocked on Cursor usage; GitHub MCP failover used.

## Best Skills note
Due=**no** (~24h since `lastPass` 2026-09-22). Next pulse ~2026-09-24. No artifact / JSON mutation this run.

## Owner email
Default **NO**. Findings are Morning Brief consumer material only — not a research-path/tool stale fix and not a hard blocker. One-shot Gmail request must stay `enabled:false`.

## Cutoff / freshness
`ready_for_brief` — same-day external body with primary URLs + findings + Wed scan artifact, finished before 07:00 Asia/Jerusalem.
