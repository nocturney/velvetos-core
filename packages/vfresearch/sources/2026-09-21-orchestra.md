# Research Seat · 2026-09-21

State: `ready_for_brief`
Observed run: 2026-09-21 ~02:00–02:30 Asia/Jerusalem (before 07:00 cutoff).
Seat: Velvet Research Seat

## Current authority / context
- Read DAILY, BEST-SKILLS + TIMER, SOCIAL-INTELLIGENCE, ORCHESTRA, ROUTINE, LOOP.json, VISIBLE_TEXT, prior `research.md` (20.9), and `2026-09-20-orchestra.md` from current main.
- vfsku SHELF: 5 slots, all `empty` (updatedAt 2026-09-02). No speculative SKU created.
- `python3 scripts/vfsku.py scan` on 2026-09-21: `לא יום סריקה (ראשון/רביעי בלבד)`. Official MakerWorld scan **not** due (Monday). Product-pattern look still ran inside the daily body.
- vfgrowth calendar: content reset still active; R001–R003 remain blocked/rebuild-required. No future feed items scheduled.
- LINKS.json lastReviewed cluster still 2026-09-16; no duplicate weekly sweep spawned.
- Drive / live jobs: not required for this pass; no invented jobs or customers.
- Content reset / R001–R003 preflight authority unchanged; Social Intelligence did not justify creative-policy change.
- Best Skills: standingForever=true; `lastPass=2026-09-20` (~24h, inside 48h+4h grace) → **not due**. `lastPass` left unchanged. No second timer/automation.
- Owner email: default NO. `packages/vfops/out/gmail-send-request.json` remains `enabled:false`.
- OpenPost release monitoring not duplicated.

Yesterday (20.9) already covered PrusaSlicer 3.0 preview, custom-order checklist, and FPY/batching. Those are **not** re-sold today.

## Same-day public research body

### 1. Prusament PLA Lightweight — specialty filament watch (not a production default)
Sources:
- https://blog.prusa3d.com/prusament-pla-lw-65-lighter-than-regular-pla-perfect-choice-for-aircraft-cosplay-and-more_138059/ — published 2026-09-17 (Jakub Kočí), observed 2026-09-21. Official vendor blog.
- https://chiptron.eu/prusament-pla-lightweight-foamed-pla-up-to-65-lighter-i-tried-it/ — published 2026-09-17, observed 2026-09-21. Independent hands-on.
- https://filamentfeed.com/article/prusament-pla-lightweight-foaming-filament-65-percent-lighter-june-2026 — published 2026-09-19, observed 2026-09-21. Secondary synthesis of the two primaries.

Evidence: Actively foaming PLA. Heat in the nozzle expands the melt; Prusa claims up to 65% lower printed mass than regular PLA and 2–3× more models from the same spool mass. Positioned for RC/drone parts, cosplay, floaters, and thermal-insulation inserts — not everyday functional parts. Default PrusaSlicer profile: 230 °C / bed 60 °C / retractions **off** / extrusion multiplier **0.45**; foaming rises from 215 °C to a max around 235 °C; do not exceed 250 °C (fume warning). Hygroscopic: dry 5 h at 55 °C. Colors print paler than the spool (Galaxy Black → concrete grey); matte/SLS-like surface. Chiptron weighed one part 8.17 g in PETG vs 3.42 g in PLA Lightweight (~58% lighter) and flags stringing, easy scratching, and low heat resistance. Supported official profiles in the blog: CORE One+ / CORE One L+ / MK4S (commenters noted XL profile gap). Vendor list price on the blog is 56.99 USD / 59.90 EUR per 1 kg — **foreign list only; IL ₪ = אין ספירה**.

Action: watch/lab only. Do **not** change the everyday PLA/PETG stack. Do not buy a spool from HQ without a lead-seat ask. If a later inquiry is explicitly drone / cosplay / insulation / floater: one calibration cube + dry-box habit on the floor, then slicer grams into `vfcost` — never invent sale ₪. Distinct from 20.9 PrusaSlicer 3.0 preview (tool vs material).

Confidence: high for release/process facts (vendor blog + same-day independent try); low for VF demand (no local inquiry).

Limitation: specialty filament; “up to 65%” is not a guarantee; scratch/heat limits rule it out as a pickup-shelf default.

### 2. Kitchen / wet-area self-draining organizers — recurring-product family, not a shelf name
Sources (WebSearch snippets; MakerWorld WebFetch hit Cloudflare):
- https://makerworld.com/en/models/2414746-self-draining-sponge-holder-kitchen-sink-organizer — released 2026-02-18; snippet observed 2026-09-21. Inclined base + cantilever drain into the sink. **Cipriani 3Design License** — commercial print/sale requires paid subscription; SDFL-style “no paid physical prints” without it.
- https://3dsearch.net/model/bottle-dryer-with-spout-1837965 — published/updated 2026-09-09, observed 2026-09-21. Single-piece bottle dryer with 5° internal slope into the sink.
- https://3dsearch.net/model/wall-mounted-towel-holder-minimal-functional-mw3280089 — published/updated 2026-09-08, observed 2026-09-21. Small wall towel holder; commercial license pointed at Patreon.
- Related same-family listings (older, license-gated): https://makerworld.com/en/models/2148912-voronoi-draining-soap-dish-minimalist · https://makerworld.com/en/models/2451525-japandi-drain-tray-sponge-soap-holder

Evidence: Independent 2026 listings cluster on **wet-area utility** — sponge/soap/bottle dryers that drain into the sink, plus small wall towel/key holders. This is a different family from the 19.9 desk/cable utility signal. Almost every commercial-looking listing is Standard Digital File License or a paid creator commercial seat. Official Sunday/Wednesday MakerWorld scan is **not** due today (`vfsku.py scan` → לא יום סריקה).

Action: no shelf fill. Keep as a `vfsku` / `vlicense` / `MAKERWORLD-SCAN` watch family. Next official scan day (Wed 23.9): only a named URL with an explicit commercial-ok license + floor slice can become a slot. Foreign-creator license is not used as a Research Seat ranking criterion; Israeli brand/catalog still stops before file use.

Confidence: medium for category persistence; low for Sderot demand; **none** for a named SKU.

Limitation: Cloudflare blocked MakerWorld HTML bodies this pass (`אין גוף` on the live page). Snippets are not GATE. Download ≠ license. No invented model names on the 5-slot shelf.

### 3. Pickup-ready physical trigger — office habit, not a new shop stack
Source: https://autoprint.email/click-and-collect-for-small-shops — vendor recipe; prices checked July 2026; observed 2026-09-21.

Evidence: The useful (non-software) claim is operational: most small-shop pickup failures are “order sits in an inbox / customer arrives before the bag exists.” The script that does not require their app: a visible ready signal → pick and **tick every line** → one bag, name visible → dedicated pickup shelf → mark fulfilled only at handover. Their storefront / email-to-print / POS stack is a vendor pitch (Shopify/Square/Big Cartel + $14.99/mo printer app) and is **skipped**.

Action: map the habit onto existing `vfsales/hq/TIMELINE-AUTO.md` + `vfprod/PRINT-DONE.md`: do not invite איסוף שדרות until the physical piece is ticked and parked. Human WhatsApp/Instagram reply only — **no auto-DM**, no new storefront, no nationwide shipping, no second runtime.

Confidence: medium for the failure-mode pattern; low for VF-measured no-show data (none local).

Limitation: commercial blog selling email-to-print software. Take the paper/habit, not the stack. Foreign ₪/USD fees are not VF prices.

### 4. Bambu Lab everyday-filament price cut — procurement watch only
Source: https://forum.bambulab.com/t/filament-prices-drop-across-all-regions/259832 — official BambuLab announcement 2026-09-16, observed 2026-09-21.

Evidence: Vendor says everyday filament prices were lowered **in all regions**; the post lists **US** refill examples (PETG Basic $13.99, PLA Basic $15.99, PLA Pure $16.99), a 2-roll discount, bulk as low as $10.91/roll at 10 rolls, and a US free-shipping threshold drop $89→$59. Explicit: “details vary by region and filament.” No Israel/ILS table in the announcement.

Action: procurement watch only if the floor already buys Bambu filament. Do **not** change `vfcost` sale cards or invent IL ₪. If a later purchase is actually made, read the **current regional store page** that day — this forum post is not an Israeli price list.

Confidence: high that Bambu announced a regional price cut (primary forum); **none** for local landed cost.

Limitation: US numbers ≠ Sderot cost. Community guesses about manufacturing moves are not facts.

### 5. Supporting material-hygiene note (not a top brief line)
Source: https://www.sunlu.com/blogs/Silk-2.0-and-PETG-2.0-Materials — published 2026-09-07, observed 2026-09-21.

Evidence: SUNLU PETG 2.0 / Silk 2.0 launch. Vendor claims PETG moisture as the usual stringing/bubble/adhesion failure, and that PETG 2.0 is meant to stay printable after open-air exposure (their 15-day tower test). Also restates: dry PETG (they cite 65 °C / 12 h in their test protocol).

Action: no brand switch. Keep the existing dry-box / dry-before-PETG habit on the floor. Useful only as corroboration next to Prusament LW’s 55 °C / 5 h dry note.

Confidence: medium for the moisture failure mode (well-known + vendor test); low for their comparative claim vs unnamed “other brand.”

### 6. Social Intelligence
Result: `nothing-solid` for @velvets_cloud policy change.

Sources observed 2026-09-21:
- Instagram process-footage search (`3D print studio Instagram Reels process footage pickup shop September 2026`) returned mostly unrelated / old print-on-demand BTS (e.g. printseekers 2025 demo reel), not a dated mechanic with a source-relative baseline.
- Inquiry-conversion search surfaced OrderPost / form-builder vendors that explicitly pitch Instagram **auto-reply / DM keyword** funnels — **skipped** (auto-DM locked). Not a new convert/sales embed.

Mechanic note only: “content from real work” remains the existing print.done → draft path. No source-relative baseline for @velvets_cloud. Instagram MCP remains Insights authority. No change to content reset / preflight / PUBLIC_CURRENT_CTA.

Confidence: low external mechanic signal; no local performance inference.

## ממצאים — Top for the 09:00 brief
1. Prusament PLA Lightweight (17.9 official + same-day independent try) is the strongest new **material** signal: watch/lab only; not an everyday production filament.
2. Wet-area / self-draining kitchen-sink organizers are a distinct recurring-product family from 19.9 desk/cable utility; licenses are mostly non-commercial without a paid seat — no shelf name.
3. Pickup failures in small shops are framed as “customer arrives before the bag exists”; keep a physical ready/tick/shelf habit on existing TIMELINE + print.done — no new shop software.
4. Bambu announced an all-region everyday-filament price cut (16.9); IL ₪ remains אין ספירה.
5. Social Intelligence = nothing-solid; Best Skills skipped-not-due (`lastPass` 2026-09-20).

## Searches performed (same-day)
- `new 3D printer filament material release September 2026 PETG TPU PLA`
- `Printables MakerWorld trending functional 3D prints September 2026 household`
- `local pickup 3D print shop studio operations counter workflow 2026`
- `easy to print easy to sell 3D printed products recurring SKU 2026 hooks planters kitchen`
- `Bambu Lab OR Polymaker OR Prusament filament news September 2026`
- `Instagram local pickup service business convert inquiry to order 2026 without DM automation`
- `3D print studio Instagram Reels process footage pickup shop September 2026`
- `site:makerworld.com self draining kitchen sink organizer license 2026`
- `site:chiptron.eu Prusament PLA Lightweight foamed 2026`
- WebFetch: Prusa PLA Lightweight blog · Bambu filament-price forum · FilamentFeed synthesis · SUNLU PETG 2.0 · AutoPrintEmail click-and-collect · MakerWorld sponge-holder (Cloudflare / אין גוף)

## Skips
- PrusaSlicer 3.0 / custom-order checklist / FPY+batching — yesterday’s body; no newer primary that changes those points.
- Official MakerWorld/Printables scan artifact — not Sunday/Wednesday (`vfsku.py scan` → לא יום סריקה).
- Best Skills full pass — not due (`lastPass` 2026-09-20 still inside 48h+4h).
- OrderPost / Instagram DM auto-reply / keyword funnels — auto-DM locked.
- AutoPrintEmail / Shopify / Square / PrintAdmin / PrintersGoBoom / Printago / QRdy — vendor shop/farm stacks; no second runtime.
- RAMA kitchen-rail set (Cults, 2025-06) — not a 2026 freshness signal.
- Protopasta metal-PETG EX16 (2026-09-01) — specialty composite, not VF everyday.
- FormFutura COMPOST3D®2 — retailer/vendor sustainability pitch; no local compost/claim path from HQ.
- Desk/cable utility — already covered 19.9; not re-opened as news.
- Cloudflare-blocked MakerWorld HTML: «אין גוף» on the live model page; snippets only.
- OpenPost Release Watch: not duplicated.
- Owner research email: not sent.

## Best Skills note
Due=**no**. Cadence ~48h + 4h grace. `lastPass=2026-09-20` (~24h) is still fresh. Full pass **skipped-not-due**. `BEST-SKILLS.json` pulse fields **not** refreshed. No npx; no second timer.

## Owner email
Default **NO**. Findings are brief-worthy for Morning Brief consumer `research.md`; they are not a research-path/tool stale fix and not a hard blocker. One-shot Gmail request left `enabled:false`. Prior OAuth 401 on owner-email send is unchanged and unused.

## Cutoff / freshness
`ready_for_brief` — same-day external body with primary URLs + findings, finished before 07:00 Asia/Jerusalem.
