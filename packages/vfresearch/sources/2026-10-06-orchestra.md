# Research Seat · 2026-10-06

State: `ready_for_brief`
Observed run: Tuesday 2026-10-06, ~02:07–02:30 Asia/Jerusalem, before the 07:00 cutoff. UTC clock at fetch was still 2026-10-05 evening.
Seat: Velvet Research Seat
Path: Grok Bot GitHub CLI failover (fresh `gh` clone under `/tmp`, live WebSearch + WebFetch + `gh api`). No Cursor Cloud Agent. No chatgpt.com / gemini.google.com / perplexity.ai. No Morning Brief send.

## Research metadata

- **as_of:** 2026-10-06 ~02:07–02:30 Asia/Jerusalem (2026-10-05 ~23:07–23:30 UTC). Every source below was fetched live in this window.
- **provenance:** the URLs under each finding; `upstream-watch-latest.json` (checkedAt 2026-10-05T23:09:22Z); LinklyAI/best-skills commit `32cd4d1733e9651bff52a27e8976751e4f1ee39b` (`data: 2026-10-05`).
- **uncertainty:** sources are a quoting-tool vendor, a shipping-software blog, an inventory-software dataset (US/Christmas sellers), Meta's own newsroom, a calendar site and an older maker safety test. None of it is a Sderot order log or `@velvets_cloud` Insights. The VF printer-hours, queue depth and handling time were not read in this seat, so no actual Hanukkah order-by date is computed here. Upstream verdicts reuse the 2026-10-05 review from unmerged PR #535 as their base (see Upstream).
- **refresh_target:** next Velvet Research Seat (2026-10-07 02:00 Asia/Jerusalem); Best Skills due again at `lastPass` + 44h (≈ 2026-10-08); MakerWorld on Wednesday 2026-10-07.

## Current authority / context

- Read `AGENTS.md`, `packages/velvetos/PROJECT-REQUEST-GATE.md` + `PROJECT-AUTHORITY-MANIFEST.json` (`instructionLocality` → research → `packages/vfresearch/AGENTS.md`), `instances/velvet-factory/AGENTS.md`, `packages/vfops/ROUTINE.md`, `packages/vfops/LOOP.json`, `constitution/VISIBLE_TEXT.md`, `packages/vfresearch/DAILY.md`, `ARTIFACT-CONTRACT.md`, `BEST-SKILLS.md`, `BEST-SKILLS.json`, and `packages/vfops/data/research.md` (2.10.2026 on main). Preflight: research, `FAST_PATH` (read-only research + internal artifact mutation; no external effect).
- Main consumer before this seat: 2.10.2026. Research Seat PRs #535 (5.10), #488 (4.10), #459 (3.10), #446, #438, #430, #405 are still open; nothing in them was merged here or re-sold as a finding.
- Best Skills: `lastPass` on main is 2026-10-02 (~96h, stale >52h) → executed. Artifact: `packages/vfresearch/sources/2026-10-06-best-skills.md`. Result: `no-embed-existing-coverage`. dataDate `2026-10-05`.
- MakerWorld/Printables: Sunday and Wednesday only. Today is Tuesday → לא יום סריקה.
- Weekly links: the 4.10 pass is on main (`sources/2026-10-04-weekly-links.md`). Not re-reviewed here; the consumer carries that pass's own line.

Anti-recycle (not re-sold): 5.10 repeat-order baseline; quote that says what «כן» triggers; tagged customer posts on the grid; Meta One paid post links / Edits assistant. 4.10 catalog family, named proof version, license line. 3.10 seven intake fields, technical file review, acceptance criteria + first article, QC before pack-out, local trust. 2.10 lead-time clock starts at production release; approval as queue card; fit check before price; kit identity lock; film the real job. 1.10 FPY + versioned profiles; deposit before print; QC levels; short-print SKUs; order form. Filament reorder points (24.9, 28.9).

## ממצאים

### 1. A Hanukkah "order by" date worked backwards from real printer capacity

Sources:
- https://filaquote.com/guides/3d-printing-lead-times/ — Filaquote, Jan Schwoebel, "Updated September 2026". Fetched live 2026-10-06.
- https://reachship.com/holiday-shipping-deadlines-2026/ — ReachShip, dated October 5, 2026. Fetched live 2026-10-06.
- https://craftybase.com/blog/handmade-business-seasonal-sales-calendar — Craftybase, "Last updated: April 2026" (orders April 2024–March 2026, 1,200+ handmade sellers). Fetched live 2026-10-06.
- https://www.hebcal.com/holidays/chanukah-2026 — Hebcal: Chanukah 5787 begins at sundown on Friday 4 December 2026 and ends at nightfall on Saturday 12 December 2026. Fetched live 2026-10-06.

What the pages say: Filaquote says to quote a lead time the shop can hit 95% of the time, built from three numbers: real productive printer-hours per day (after the failure rate), the hours already queued, and handling after the print. Add a buffer of about one day or 20%, whichever is larger. Put the promise on the quote and the confirmation, flag very long or heavy prints before accepting them, and tell the customer before the date passes if a reprint is needed. ReachShip's point is that the date a customer reads is not the carrier date: subtract handling, non-working days and one buffer day, then publish an "order by" date with a time of day. Craftybase's data says October is the production-planning month and that late-season stockouts trace back to late October; its peak week (8 December) is driven by Christmas shipping.

What we do: on `vfprod` / `vfsales`, compute one "last day to order a custom piece for Hanukkah" from VF's own numbers: free printer-hours per day, what is already in the queue, post-processing and finishing, and a buffer day. Pickup in Sderot means there is no carrier step, so the end point is a pickup slot before the first candle on Friday 4.12. Christian approves the date before it appears anywhere public. Long or heavy jobs get flagged before they join the Hanukkah queue, and if a print fails, the customer hears it before the promised day with a new date. No ₪ in this pattern. Filaquote's paid rush tiers (+25–100%) are a price decision for Christian only and are not adopted. No shipping.

Distinct from 2.10 (which event starts the pickup clock): this is the seasonal cutoff date derived from capacity, published once for a holiday window.

Confidence: high for the method. Low for any specific date: VF's printer-hours and queue were not read in this seat, so no date is stated.

Limitation: Craftybase's curve is US/Christmas. Hanukkah 2026 starts three weeks before Christmas, so VF's peak, if any, comes earlier and is not measured.

### 2. Meta's Business Agent can answer and close sales in Instagram DMs; it stays off for VF

Sources:
- https://about.fb.com/news/2026/06/meta-business-agent/ — Meta Newsroom, "Be There for Every Customer With Meta Business Agent", June 3, 2026. Fetched live 2026-10-06.
- https://about.fb.com/news/2026/09/introducing-muse-small-business/ — Meta Newsroom, "Muse for Small Business", September 29, 2026. Fetched live 2026-10-06 (via search highlight).
- https://techcrunch.com/2026/09/29/meta-is-expanding-its-ai-agent-muse-to-small-businesses/ — TechCrunch, Aisha Malik, September 29, 2026 (via search highlight).

What the pages say: Meta Business Agent answers business questions, recommends catalog products, books appointments, qualifies leads and closes sales, in the business's tone and the customer's language. Meta says it is expanding to Instagram, free to start, with paid subscriptions "in the coming months", and it also delivers a "morning briefing" of chats missed overnight. Separately, Muse for Small Business (29.9.2026) connects to Instagram professional analytics, Facebook Pages and tools such as Canva, Shopify and QuickBooks. Meta says Muse is available in the US and Canada, free with usage limits.

What we do: Business Agent replying in `@velvets_cloud` DMs would be an automated reply to customers, which the office rules forbid (no auto-DM, human commercial close). If Instagram offers to switch it on, the answer is no, and DM replies keep coming from Christian with `vfsales` / `vfconvert` drafts. Its "morning briefing" does not replace the 09:00 brief or the Instagram MCP read. Muse is not offered in Israel per Meta's own page, and any number from Muse or Business Agent is Meta's summary, not a VF Insight. Nothing to buy; `NO_NEW_RECURRING_COST` holds.

Distinct from 5.10 (Meta One paid post links, Edits metrics assistant): this is the customer-facing DM agent.

Confidence: high for what Meta announced. Unknown whether Business Agent is offered to `@velvets_cloud` today; the account was not checked.

Limitation: rollout and pricing vary by region and account; Meta has not published Instagram pricing.

### 3. Hanukkah pieces: printed decor yes, a plastic holder for real flames no

Sources:
- https://studioarmadillo.com/products/hanukkah-menorah-for-early-adopters-3d-printed — Armadillo Judaica (Israel), clay 3D-printed menorah page, pre-Hanukkah offer; page undated. Fetched live 2026-10-06.
- https://stldenise3d.com/how-safe-are-3d-printed-candle-holders/ — stlDenise3D, Denise Bertacchi, last updated March 28, 2023 (older safety test, cited only for the safety point). Fetched live 2026-10-06.

What the pages say: an Israeli studio already sells 3D-printed Judaica for Hanukkah, but the menorah is printed in clay and glazed, with brass parts, not plastic. The maker safety test burned tea lights in PLA holders: a thin vase-mode print got crispy in 25 minutes, thicker ones singed, and the author still does not recommend real candles in a print and suggests LED candles.

What we do: if a Hanukkah item enters `vfsku` / `vfprod`, flame-free pieces (dreidels, decor, gift-box inserts) are the plain path. A printed holder meant for real candles or oil does not go to the shelf as PLA/PETG alone. It needs a metal or glass insert and a safety check, or it is sold for LED candles only, and that wording must be true. The Armadillo design is an Israeli creator's work and is not copied (`vlicense` stop); it is only a signal that local buyers know printed Judaica. Candidate models go through Wednesday's MakerWorld scan and its license and slice gates, never straight to SKU or price.

Confidence: medium. The safety test is informal and from 2023; no VF material was tested here.

Limitation: no demand count for printed Hanukkah items in Sderot was available; this is a product-safety rule, not a sales forecast.

## Best Skills

Executed. Snapshot dataDate 2026-10-05 (commit `32cd4d17`). `no-embed-existing-coverage`. See `2026-10-06-best-skills.md`.

## Upstream (לא לבריף)

- `python3 scripts/vf_upstream_watch.py check --write packages/vfresearch/sources/upstream-watch-latest.json` at 2026-10-05T23:09:22Z: 95 sources, 56 pending, 6 `newDetection` (the same six repos as 5.10, still not acked on main), 0 failed, `autoUpgrade=false`.
- `vfresearch_cadence.py review-routing` on main's older review file: most pending rows needed deep review. Base verdicts were taken from the 5.10 review (unmerged PR #535): 26 rows still matched the current HEAD/release exactly and were reused. The other 30 rows moved since 5.10 and were read through `gh api` compare + release notes and re-bound. After review: 56/56 current (`deepReviewRequired: 0`), `update 0 / wait 15 / review 12 / ignore 29`, every verdict unchanged, `notifyOwner` false on every row. Notes: `mattpocock/skills` added an experimental chief-of-staff skill (still `review`); `earthtojake/text-to-cad` v0.7.14 fixes Windows STEP import (still `wait`, no smoke).
- `python3 scripts/vf_upstream_email.py render --arm --consume-notify`: `notify=true` (the same sticky newDetection rows), digest `2c85e834f8196789`. Hebrew lint on `tool-updates-latest.txt` passes; the full Visible Text Gate stays `UNPROVEN` because the reader-first / surface-QA / copy-authority stages were not run for a send.
- Tool-updates email: not dispatched. The 5.10 `workflow_dispatch` was stopped by the Grok Bot safety review pending owner approval, and today's detections are the same six repos, so this seat did not retry or use another route. Request committed `enabled:false`. No Gmail message id, so no delivery claim.
- Receipt refresh: the watch kept pending at 56 but main's receipts still carried 50, so `stage7c-research-scheduler-consolidation.json` and `stage7-acceptance.json` were regenerated with their own generators and unchanged arguments (only the routing counts 50→56 and the stage7c hash changed), the same refresh as PR #535.
- No ack. No upgrade. No pip/npm/git pull.

Toolchain rows stay out of `packages/vfops/data/research.md`.

## מה עושים

- Hanukkah: one capacity-based "order by" date for custom pieces, approved by Christian before any public use; flag long jobs; warn before a missed date.
- Meta Business Agent: stays off in DMs; no purchase; Muse/agent numbers are not Insights.
- Hanukkah SKU: flame-free decor first; any real-flame holder needs an insert and a safety check or is LED-only; no copying Israeli designs.
- Best Skills: no embed.

## מה דולג

- MakerWorld/Printables scan: Tuesday, outside Sunday/Wednesday.
- Weekly links review: done on 4.10 by its own routine; not redone here.
- Instagram "originality" ranking page (creators.instagram.com, April 30, 2024): too old to count as a new finding.
- Instagram Live video ads (distk.in, 29.9.2026) and "Muse automates DM sales" (pops4.com, secondary): paid ads / auto-DM, and the second source is unverified secondary reporting.
- Bambu Lab R1 laser (Bambu blog, 22.9.2026, $2,499): new equipment spend; not adopted.
- Bambu Handy queue (3dbite.com): unverified blog report; no action.
- canadacreate.com "test before launch" page: fetch returned a web-agency sales page, no usable body; not cited.
- Morning Brief: not sent. Owner research email: not sent (no blocker; findings go to the 09:00 brief).
- chatgpt.com / gemini.google.com / perplexity.ai: not opened.
- No new pack, no new repo, no Origin slug, no npx skills, no auto-DM, no boost, no Print from HQ.

## Checks

- `python3 scripts/vfresearch_cadence.py freshness`: OK (date 2026-10-06, 9 external sources).
- `python3 scripts/vf_visible_text.py --surface owner-brief --tier FINAL_INTERNAL --file packages/vfops/data/research.md --truth-checked --reader-first --copy-authority --surface-qa --gate`: PASS, text sha256 `fd0b4f2f37bcc82261d4a45926af892bd3f23f71818cb98563584523db6714c9`.
- `python3 scripts/check-all.py`: 118/118 PASS on a full (non-shallow) clone.

## מגבלות

No ₪. No Insights. No customer names. No claim that anything was posted or sent. No Hanukkah order-by date is stated, because VF's own capacity numbers were not read.
