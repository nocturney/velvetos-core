# Research Seat · 2026-10-02

State: `ready_for_brief`
Observed run: 2026-10-02 Asia/Jerusalem, before the 07:00 cutoff. UTC clock at fetch was still 2026-10-01 evening.
Seat: Velvet Research Seat
Path: live WebSearch + WebFetch + `gh api`. No chatgpt.com / gemini.google.com / perplexity.ai. No Morning Brief send.

## Current authority / context

- Read `AGENTS.md`, `packages/vfresearch/DAILY.md`, `packages/vfops/ROUTINE.md`, `packages/vfops/data/research.md` (27.9.2026 on main), `BEST-SKILLS.md` / `BEST-SKILLS.json` / `TIMER.md`.
- Prior consumer on main is 27.9.2026. Open Research Seat PRs #446, #438, #430, #405 were left unmerged and were not reopened.
- Best Skills: `lastPass=2026-09-27` (~120h, stale >52h) → executed. Artifact: `packages/vfresearch/sources/2026-10-02-best-skills.md`. Result: `no-embed-existing-coverage`. dataDate `2026-10-01`.
- MakerWorld/Printables: LOOP is Sunday+Wednesday. Today is Friday → **skipped**.
- Upstream watch: `python3 scripts/vf_upstream_watch.py check --write packages/vfresearch/sources/upstream-watch-latest.json`. Reviews in `upstream-review-latest.json`. No ack. No upgrade.
- Owner research email: not sent. This run keeps the brief consumer as the office surface.

Anti-recycle (not re-sold): 27.9 intake 8-block; minimum quote packet + controlling revision; three finish lanes; automatic-fail QC + breakage packing; batchable organizer cost-stack; local pickup desk-reset club. Unmerged #446: FPY + versioned profiles + constraint batching; 7-step custom + deposit before print; QC levels + gold photo + weekly defect review; functional short-print SKUs vs generic stands/fidgets; IG marketing vs a structured order form outside DM chaos.

## ממצאים

### 1. Lead-time clock starts at production release, not when the quote is sent

Source: https://www.goodprints3d.com/blogs/3d/when-does-lead-time-start-on-a-custom-3d-printing-order-quote-deposit-or-approval — GoodPrints3D, published May 14, 2026, fetched live 2026-10-02.

What the page says: lead time usually starts at production release, when the shop has the approved file revision, quantity, material, required checks, delivery scope, and authority to begin. A quote, purchase order, or deposit can be a commercial commitment and still leave the job blocked on a sample, a file change, a material decision, or a packaging instruction. The practical test: could an operator start today without another interpretation call?

What we do: on `vfsales` / `vfconvert`, the quote names the event that starts the pickup-ready clock (final file + approval + any still-open release condition). A deposit may reserve a window; it does not by itself start the promised days. Pickup in Sderot replaces ship-to. No invented day counts.

Distinct from the unmerged 10-01 “deposit before print” step: this finding is when the promised clock starts, including the case where payment exists and the file is still open.

Confidence: high for the release-event rule. Medium for how short a repeat pickup job can be before the same sentence is still worth writing.

Limitation: GoodPrints3D is a supplier education page with ship/freight examples. We take the start-event rule, not a carrier promise.

### 2. Approval has to carry the job into the queue

Source: https://printcal.co/en/blog/3d-printing-quote-approval-link-production-queue/ — PrintCal, published May 10, 2026, fetched live 2026-10-02.

What the page says: the weak point is after the price is sent. A chat “approved” still leaves someone hunting the file, material, and deadline. A useful handoff keeps customer, deadline, priority, material, printer, quantity, and notes on the accepted job so the queue does not start from memory. The page’s checklist also says the deadline should reflect the real queue, not slicer time alone.

What we do: on `vfconvert` / `vfsales`, an acceptance note is the production card (who, promised pickup window, material/color, quantity, controlling file, open exceptions). A bare «אושר» in Instagram messages is not the handoff. Do not buy PrintCal. Do not copy its prices.

Distinct from “get written approval”: the new requirement is that the approval artifact is the queue entry.

Confidence: high for the handoff shape. Low for any vendor UI.

Limitation: PrintCal is quote software. Pattern only.

### 3. Fit check before a price

Source: https://laticy.com/repeatable-custom-order-workflow/ — Laticy, dated June 19, 2026, fetched live 2026-10-02.

What the page says: step 2 is an internal fit check before quoting. Questions include whether the shop has the materials, machine capacity, and finishing workflow, whether the requested timeline is realistic, and whether the job will block other work. The same page says delivery dates get promised before the schedule is checked, and that a firm date should wait until the order is defined.

What we do: on `vfconvert`, custom requests get a capacity/feasibility line (material on hand, bed time, finishing, collision with the current queue) before any ₪ language. If the fit check fails, the lane is hold or a smaller first piece, not a price.

Distinct from the 27.9 intake worksheet and from the 10-01 seven-step deposit sequence: this is the go/no-go before price, not the intake form and not the payment gate.

Confidence: medium. The source is a general maker-custom workflow (names, proofs, events), not a measured Sderot print queue.

Limitation: do not import the rest of that page’s deposit/proof ladder; those steps are already covered elsewhere.

### 4. Lock kit identity before the batch, not only part protection

Source: https://www.goodprints3d.com/blogs/3d/what-packaging-labeling-and-inspection-details-to-confirm-before-a-custom-3d-printing-batch-starts — GoodPrints3D, published April 13, 2026, fetched live 2026-10-02.

What the page says: before the batch starts, write the delivery unit (loose part, pair, kit, or sale unit), identity fields (part, revision, variant, color, quantity), kit contents, and the checks that happen before the package is sealed. A correct print can still be the wrong delivered product when variants mix, hardware is missing, or the label does not match the released revision. An approved printed sample does not approve packaging unless the sample included that pack-out.

What we do: on `vfprod`, pickup jobs with more than one part, a left/right pair, or supplied hardware get a one-line identity lock before the batch: unit, revision, qty per bag, what else is in the handoff. Finish approval is not pack-out approval. No national shipping. No invented packaging ₪.

Distinct from 27.9 breakage-prevention packing: this is identity and kit contents, not cushioning.

Confidence: high for the identity lock on multi-part pickup. Low for barcode/carton language, which we do not adopt.

Limitation: the source assumes a receiving dock. VF maps it to the pickup handoff only.

### 5. Film the real job, not a finished still

Source: https://craftgineer.com/blog/social-media-marketing-makers — Craftgineer, March 13, 2026, fetched live 2026-10-02.

What the page says: for makers, Reels are the reach format, and process videos, time-lapses, and making clips are the ones it recommends over a static photo of the finished object. Its practical unit is a 30–60 second time-lapse of making something from start to finish, batched from a real session rather than invented daily. The page’s “10x” laser example is the blog’s claim, not a VF measurement.

What we do: on `vfcovers` / `vfgrowth`, the next floor-origin candidate is a short process frame from a real print (bed, WIP, pull-off), not a generic finished still and not a repost. No Insights invented. No TikTok requirement. No ListingLab/Canvas Pro tooling.

Distinct from the 27.9 “original content” note: that note was about Meta’s originality weighting. This one is the shot type (process/timelapse of our own job).

Confidence: medium-low. One maker-marketing blog, laser/CNC examples, no `@velvets_cloud` count.

Limitation: do not treat the 10x sentence as an Insight.

## Best Skills

Executed. Snapshot dataDate 2026-10-01. `no-embed-existing-coverage`. See `2026-10-02-best-skills.md`.

## Upstream

Watch checked 95 sources. Pending 50. New detections 39. Failed 0. Reviews bound to the current `remoteHead` / `latestRelease`: update 0, wait 14, review 11, ignore 25. No ack.

Toolchain rows stay out of `packages/vfops/data/research.md`.

## מה עושים

- Quote copy names the pickup-clock start event.
- Acceptance note is the production card.
- Fit check before ₪ language on custom jobs.
- Identity/kit line before a multi-part batch.
- Next floor Reel candidate is a real process frame.
- Best Skills: no embed.

## מה דולג

- MakerWorld/Printables scan: Friday, outside sun–wed.
- Weekly links pass: not this seat (Friday 12:00 accountability is separate). Kept the 25.9 section already in the consumer.
- AMS vs direct-feed / color-batch days: not adopted. It overlaps the unmerged 10-01 constraint-batching finding, and this pass did not verify a separate operational split.
- Morning Brief: not sent.
- Owner research email: not sent.
- chatgpt.com / gemini.google.com / perplexity.ai: not opened.
- No new pack, no new repo, no Origin slug, no npx skills, no auto-DM, no boost, no Print from HQ.

## מגבלות

No ₪. No Insights. No customer names. No claim that Instagram was posted. Sources are supplier and maker blogs, not a Sderot order log.
