# Research Seat · 2026-10-03

State: `ready_for_brief`
Observed run: 2026-10-03 Asia/Jerusalem, before the 07:00 cutoff. UTC clock at the upstream check was still 2026-10-02 evening (`checkedAt` 2026-10-02T23:12:09Z).
Seat: Velvet Research Seat
Path: findings below are the supplied 2026-10-03 live fetch packet (URLs re-read this run). Upstream via `python3 scripts/vf_upstream_watch.py check`. No chatgpt.com / gemini.google.com / perplexity.ai. No Morning Brief send. No owner research email.

## Current authority / context

- Read `AGENTS.md`, `instances/velvet-factory/AGENTS.md`, `packages/vfops/ROUTINE.md`, `packages/vfops/LOOP.json`, `constitution/VISIBLE_TEXT.md`, `packages/vfresearch/DAILY.md`, `packages/vfresearch/BEST-SKILLS.md`, `packages/vfresearch/BEST-SKILLS.json`, `packages/vfresearch/TIMER.md`, `packages/vfops/data/research.md` (2.10.2026 on main).
- Best Skills: `lastPass=2026-10-02` (~24h). Due only at ≥44h. **Skipped.** `BEST-SKILLS.json` not rewritten.
- MakerWorld/Printables: LOOP `sun-wed`. Today is Saturday → **skipped**.
- Weekly links: not this seat. The 25.9 section already in the consumer stays.
- Upstream watch written to `packages/vfresearch/sources/upstream-watch-latest.json`. Reviews in `upstream-review-latest.json` bound to this report’s `remoteHead` / `latestRelease`. No ack. No upgrade. No pip/npm/git pull.

Anti-recycle (not re-sold): 2026-10-02 lead-time clock at production release; approval as queue card; fit check before ₪; kit identity lock; process/timelapse Reel. 27.9 intake 8-block; minimum quote packet + controlling revision; three finish lanes; automatic-fail QC + breakage packing; batchable organizer cost-stack; local pickup desk-reset club. Unmerged 10-01 (#446): FPY + versioned profiles + constraint batching; 7-step custom + deposit before print; QC levels + gold photo + weekly defect review; functional short-print SKUs vs generic stands/fidgets; IG marketing vs a structured order form outside DM chaos.

## ממצאים

### 1. Quote intake needs the seven price-deciding fields up front

Sources:

- https://help.makelab.com/help/article/what-information-do-i-need-to-provide-for-a-quote — Makelab Help, last updated 2026-06-29, fetched 2026-10-03.
- https://3dprintcalc.no/guides/customer-portal — 3D Print Calculator Customer Portal Guide, fetched 2026-10-03.

What the pages say: 3D Print Calculator says nine out of ten unclear orders come from a missing intake detail. Its price-deciding set is model file (STL/OBJ/3MF), quantity, material and colour, intended use, deadline, finishing, and delivery (shipping address or local pickup). The same page’s FAQ lists those plus colour as the minimum for a firm price without another contact. Makelab’s quote article (updated 2026-06-29) asks for a 3D file (STL, OBJ, STEP, or native CAD), quantity, material preference, application/use case, finish/quality level, timeline, tolerances if critical, and special requirements (colour, infill or wall thickness, inserts, assembly).

What we do: on `vfconvert` / `vfsales`, an Instagram or WhatsApp intake reply sends a short missing-fields checklist before any ₪ language when file, quantity, use, finish, or pickup window are absent. Do not buy Makelab or 3D Print Calculator. Pickup in Sderot only. No invented prices.

Distinct from the 2026-10-02 fit-check-before-price: this is the inbound field set that makes quoting possible, not a capacity go/no-go.

Confidence: high for the field list. Low for any portal vendor.

Limitation: ignore portal software, shipping surcharges, rush fees, and the page’s 3–5× reply claim. VF does not price shipping.

### 2. Technical file review is a named step before the job is committed

Source: https://orbit3d.ae/how-it-works/ — Orbit3D Dubai, fetched 2026-10-03.

What the page says: the order flow is enquiry → technical file review (size, wall thickness, complexity, recommended adjustments for strength and print success) → quote with timeline → material selection → monitored print → post-process → package/pickup. Failed prints are the shop’s cost, not the customer’s. Ideas without files are welcome; a file, a use case, and a finishing preference shorten the path to a quote.

What we do: on `vfconvert`, when a file arrives, write a one-line printability note (walls, overhangs, size, bed fit) and any recommended change before the formal quote card. A failed first print stays an internal cost, not a customer charge line. CTA stays an Instagram message to `@velvets_cloud`. No national shipping.

Distinct from the 2026-10-02 approval-as-queue-card: this is pre-quote engineering review, not the post-approval handoff.

Confidence: medium (one studio process page).

Limitation: ignore Dubai courier, phone, and pricing. Map only review-before-commit and failed-print ownership.

### 3. Acceptance criteria and first-article proof before the remaining quantity

Source: https://www.goodprints3d.com/blogs/3d/how-to-define-acceptance-criteria-and-qc-expectations-before-a-custom-3d-printing-batch-starts — GoodPrints3D, published April 15, 2026, fetched 2026-10-03.

What the page says: before a custom batch starts, define what must pass, how and how often it is checked, and the disposition on fail. The minimum release baseline covers the controlling file revision and material, critical fit or function, dimensional and cosmetic limits, inspection method and sampling, packaging, and disposition. A first article proves the released revision, material, method, and inspection plan before the remaining quantity is committed. “Looks good” is too weak. Cosmetics use viewing zones.

What we do: on `vfprod` / `vfconvert`, multi-unit or fit-critical pickup jobs get a one-line acceptance note and a first-piece check before the rest of the plate or batch runs. Map this to the pickup handoff, not a shipping certificate.

Distinct from the 2026-10-02 kit identity lock: this is pass/fail criteria and a first-article gate, not kit contents.

Confidence: high for the baseline shape. Medium for how light a VF first-piece can be.

Limitation: the source assumes shipment release and receiving. VF keeps the baseline and the first piece; it does not adopt certificates, freight, or affiliate tools.

### 4. QC before packing, then one pack-out check

Source: https://www.goodprints3d.com/blogs/3d/how-to-build-a-3d-print-qc-checklist-for-small-batch-orders-without-slowing-shipping-to-a-crawl — GoodPrints3D, published April 13, 2026, fetched 2026-10-03.

What the page says: usable QC is a short checklist against failures that cost money (count, fit-critical features, visible defects, variant or hardware, pack accuracy). Core checks apply to every order, with product-family extras. The flow is pull batch → count/variant → spot-check fit → clear rejects → pack → confirm label, quantity, and inserts before seal. Separate critical failures from acceptable cosmetic variance. Recurring failures are production problems.

What we do: on `vfprod`, pickup QC is two steps: a part check before the bag, then a bag/label/count check before the customer message that pickup is ready. No national shipping language.

Distinct from finding 3: this is the operational checklist and flow. Finding 3 is the acceptance baseline and first article.

Confidence: high for the two-step flow.

Limitation: the page’s shipping-label and seal-up language maps to the pickup bag and the ready message. No freight promise.

### 5. Local trust from repeated real finished work, not polished hype

Source: https://www.customshirtprintings.com/how-custom-shirt-printings-uses-instagram-to-sell-more-apparel/ — Custom Shirt Printings, posted August 29, 2026, fetched 2026-10-03.

What the page says: the posts it says convert best are the simplest: close-ups of the process, finished stacks, and short reels from screen to press. Local trust grows from repetition of finished orders, art approvals, and production clips. A real storefront and a pickup counter reduce online hesitation. Shoppers scan for clarity, quality, and confidence before ordering.

What we do: on `vfgrowth` / `vfcovers`, prefer a finished-stack or ready-for-pickup frame from a real Sderot job (with permission) as a trust post type alongside process clips. The caption can name איסוף שדרות. No Insights invented. Public CTA is an Instagram message only.

Distinct from the 2026-10-02 process/timelapse finding: this is finished-proof and local-pickup trust repetition, not the process shot type.

Confidence: medium-low (apparel print shop, not 3D). Pattern only.

Limitation: do not copy a phone CTA. Public CTA stays an Instagram message to `@velvets_cloud`. No auto-DM.

## Best Skills

Skipped. `lastPass=2026-10-02` is about 24 hours old. `TIMER.md` runs the pass only when `lastPass` is at least 44 hours old. A pass today would be a same-cycle double. `BEST-SKILLS.json` unchanged. No `npx skills`.

## Upstream

Watch checked 95 sources. Pending 52. New detections 2 (`huginn/huginn`, `tong-io/tongflow`, both catalog-source head moves). Failed 0. Reviews bound to the current `remoteHead` / `latestRelease`: update 0, wait 14, review 11, ignore 27. Twenty-seven bindings were stale or missing and were refreshed this run; verdicts stayed conservative (catalog and locked runtimes `ignore`, active runtimes without smoke `wait`, pattern heads without a full diff `review`). No ack. No upgrade.

Toolchain rows stay out of `packages/vfops/data/research.md`. Tool-updates mail is a separate render (`vf_upstream_email.py render --arm --consume-notify`) and is not a brief line.

## מה עושים

- Intake reply lists the missing price-deciding fields before ₪ language.
- File arrival gets a one-line printability note before the quote card. Failed first prints stay internal.
- Multi-unit or fit-critical pickup jobs get an acceptance line and a first-piece check.
- Pickup QC is part-check, then bag/label/count, before the ready message.
- Next trust frame can be a real finished stack or ready-for-pickup still, with permission.
- Best Skills: no pass.

## מה דולג

- Best Skills: ~24h since 2026-10-02, under the 44h due line.
- MakerWorld/Printables scan: Saturday, outside sun–wed.
- Weekly links pass: not this seat. Kept the 25.9 section already in the consumer.
- Morning Brief: not sent.
- Owner research email: not sent.
- chatgpt.com / gemini.google.com / perplexity.ai: not opened.
- No new pack, no new repo, no Origin slug, no npx skills, no auto-DM, no boost, no Print from HQ.
- No Makelab / 3D Print Calculator purchase. No Dubai courier. No shipping certificates.

## מגבלות

No ₪. No Insights. No customer names. No claim that Instagram was posted. Sources are vendor help, a calculator guide, one Dubai studio process page, two supplier QC posts, and one apparel Instagram post. They are not a Sderot order log.
