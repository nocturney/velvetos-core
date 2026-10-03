# Research Seat · 2026-10-04

State: `ready_for_brief`
Observed run: 2026-10-04 Asia/Jerusalem, before the 07:00 cutoff. UTC clock at fetch was still 2026-10-03 evening.
Seat: Velvet Research Seat (`@research-synthesist`)
Path: WebFetch + WebSearch + `gh api`. No chatgpt.com / gemini.google.com / perplexity.ai. No live Instagram publish. No auto-DM. No owner research email.

## Current authority / context

- Read `AGENTS.md`, `packages/vfresearch/DAILY.md`, `packages/vfops/ROUTINE.md`, `packages/vfops/data/research.md` (2.10.2026 on main), `BEST-SKILLS.md` / `BEST-SKILLS.json`, `hq/MAKERWORLD-SCAN.md`.
- Main consumer before this seat: 2.10.2026. Open PR #459 (2026-10-03 seat) was left open and was not reused.
- Best Skills: `lastPass` 2026-10-02 → due (≥44h). Artifact: `packages/vfresearch/sources/2026-10-04-best-skills.md`. Result: `no-embed-existing-coverage`. dataDate `2026-10-03`.
- MakerWorld: Sunday = scan day. Artifact: `packages/vfresearch/sources/2026-10-04-makerworld-scan.md`. No shelf promotion.
- Upstream watch: `python3 scripts/vf_upstream_watch.py check --write packages/vfresearch/sources/upstream-watch-latest.json` at `2026-10-03T23:09:47Z`. 95 sources, 55 pending, 5 `newDetection`. Reviews rewritten onto current `remoteHead` / `latestRelease`. No ack. No upgrade.
- Owner research email: not sent. Tool-update email is a separate channel and is not in this brief.

Anti-recycle (not re-sold from 2.10): pickup clock starts only at production release; thread «אושר» plus context card; fit check before price; multi-part bag identity; floor timelapse instead of a generic product photo.

## ממצאים

### 1. A ready catalog is a family, not a pile of one-offs

Source: https://www.goodprints3d.com/blogs/3d/lesson-14-a-catalog-full-of-one-off-prints-is-harder-to-sell-than-a-tight-family-of-products — GoodPrints3D, Lesson 14, published April 24, 2026. Fetched live 2026-10-04.

What the page says: more listings do not create more chances when every object has a different buyer, photo language, print setting, and support question. A family is nearby solves that share a buyer, a production logic, and trust: replacement parts for one tool class, organizers for one bench, or accessories for one hobby. The next product should sit beside the current winner.

What we do: `vfbiz/OFFERING.md` still has two tracks only — ready products and custom. The ready track is now explicitly a tight family (`vfsku/LAB.md`). Custom stays the second track. No third channel, no Etsy, no invented ₪. A one-off that does not sit beside an existing winner does not become a `ready` slot. License + slice still gate any shelf card.

Distinct from 2.10 floor-content and from unmerged “functional short prints vs fidgets”: this finding is catalog shape (family vs scattered one-offs), not the photo format and not a SKU name.

Confidence: high for the family rule. No sale price and no local demand count on the page.

Limitation: the source is a shop-education lesson with marketplace listings in mind. We take the catalog shape. Pickup in Sderot and Instagram message stay the public path.

### 2. Production unlock is a named proof version, not the word approved

Source: https://printshopcrm.com/blog/proof-approval-workflow-print-shops/ — Print Shop CRM. Fetched live 2026-10-04. The page does not show a publication date.

What the page says: the weak pattern takes approval from a random text and then expects production to know which file and revision is current. The cleaner pattern stores the proof on the job, shows approval status, and blocks production until the approval rules are met.

What we do: `vfconvert/PATH.md` now requires three things on the job record before «מוכן לייצור»: a named proof id (controlling file + revision), written approval bound to that id, and a cutoff after which no change is still open. `vfprod/CHECKLIST.md` keeps the queue step locked to that id. «אושר» in the thread does not unlock the printer.

Distinct from 2.10 (approval must carry who / pickup window / material / quantity / controlling file) and from any 3.10 intake-field work still sitting on PR #459: this pass is the version key and the production block, not another list of intake fields.

Confidence: high for “block production until the named revision is approved”. Medium for reminder automation — we do not add a second workflow tool.

Limitation: the page sells a CRM and mentions payments, shipping, and Slack. We take the job-record rule. No national shipping. No invented ₪. Deposit still does not start the pickup clock (2.10).

### 3. Sunday MakerWorld: five commercial-OK cards stay at the gate; three are no-sale

Full cards: `packages/vfresearch/sources/2026-10-04-makerworld-scan.md`.

Commercial-OK, GATE only, not `SHELF.json`. License class merged from the parallel MakerWorld `__NEXT_DATA__` pass (this seat’s `curl` of the model HTML returned HTTP 403):

- CC BY — https://makerworld.com/en/models/659796-egg-storage-and-dispenser-p-x1-no-supports-hardwar
- CC BY-SA — https://makerworld.com/en/models/883766-gridfinity-kitchen-drawer-parametric
- CC BY-SA — https://makerworld.com/en/models/1641382-bottle-holder-fridge-accesory
- CC BY-SA, released 2026-09-30 — https://makerworld.com/en/models/3376079-folding-box-customizable-fast
- CC0, released 2026-10-01, brand-fit caution (devotional subject, not the ready family) — https://makerworld.com/en/models/3381965-our-lady-of-nazare-multiparts

No-sale, confirmed on a live search snippet of the model URL:

- FOSBOS is Creative Commons Attribution-Noncommercial-Share Alike (BY-NC-SA), not TBD — https://makerworld.com/en/models/40503-fosbos-freeopensourcebambuorganizationalsystem
- Japandi paper towel holder is Standard Digital File License and the listing forbids selling the print — https://makerworld.com/en/models/2299607-japandi-paper-towel-holder
- Modular Kitchen Draw Organizer is the same SDFL no-sell text — https://makerworld.com/en/models/726361-modular-kitchen-draw-organizer

What we do: five cards may be discussed only inside `vlicense` / `vfsku` GATE. BY still needs credit. BY-SA keeps share-alike on a derivative. CC0 does not clear the subject caution. None are shelf, none are sliced, none have a price. NC and SDFL-no-sell stay blocked.

Confidence: high on the three no-sale snippets. The five commercial-OK classes and two release dates are from the parallel JSON pass, not a second HTML save in this seat.

### 4. The license line is the SKU gate, not the platform name

Sources:

- https://printcal.co/en/blog/commercial-stl-license-printables-makerworld-sell-prints/ — PrintCal, 3D models, June 11, 2026. Fetched live 2026-10-04.
- https://modelrover.com/g/what-license-for-selling-3d-prints — ModelRover, last updated 2026-05-09. Fetched live 2026-10-04. The page says it is not legal advice.

What the pages say: a download, a purchase, or the words Printables / MakerWorld are not permission. Sell a physical print only when that model’s license or creator membership says so. NC blocks the sale. The license belongs on the job record beside the file source. ModelRover’s table also treats unknown tags as not licensed for resale, and it warns that a CC tag does not clear a copyrighted character.

What we do: `vlicense/GATE.md` and `vfsku/GATE.md` now say the platform name is not the license. The model line is the gate and a cost input. No ₪ is invented here; a membership or paid file stays `X ₪` until a real figure exists. A commercial-OK card still needs slice evidence before `SHELF.json`.

Where the pages disagree with a listing: ModelRover’s short table says MakerWorld SDFL is “per-listing”. The Japandi and Modular Kitchen listings we read forbid selling the print. The listing sentence wins. We do not treat SDFL as a commercial grant.

Distinct from finding 3: finding 3 is today’s cards. This finding is the rule those cards sit under.

Confidence: high for “read the model line”. No local fee was on either page.

## מה עושים עם זה

- מדף מוכן: הפריט הבא יושב ליד משפחה קיימת, או נשאר מחוץ ל־`ready`.
- תור: אין מעבר ל«מוכן לייצור» בלי מזהה הוכחה.
- תוכן: כשיש עבודה אמיתית מאותה משפחה, מראים את השימוש החוזר. לא פותחים פוסט על חפץ לא קשור רק כי הוא חדש. `vfcovers` / `vfgrowth`. אין ספירת Insights.
- רישיון: חמישה כרטיסים מסחריים־אפשריים נשארים בשער. שלושה חסומים למכירה. אין שם להציע היום.

## מה דולג

- chatgpt.com / gemini.google.com / perplexity.ai
- מייל מחקר לבעלים (ברירת מחדל: לא)
- פרסום אינסטגרם חי, אוטו־DM, בוסט, Print מ־HQ
- מאמר Etsy שלא אומת במושב הזה
- שדרוג או ack של upstream בלי smoke
- רענון שבועי של `LINKS.json` — המעבר האחרון נשאר 25.9.2026; לא הומצא רענון

## Best Skills

due. dataDate 2026-10-03. `no-embed-existing-coverage`. פירוט: `packages/vfresearch/sources/2026-10-04-best-skills.md`.

## Upstream (לא לבריף)

55 pending אחרי הצמדה ל־HEAD הנוכחי. 5 גילויים חדשים: `calesthio/OpenMontage` (wait), `Jeffallan/claude-skills` (review), `Devin-AXIS/deepseek-design` / `huginn/huginn` / `tong-io/tongflow` (ignore). 28 פריטים ישנים זזו ב־HEAD וההחלטה נשארה. אין ack.

מייל עדכוני כלים: `vf_upstream_email.py render --arm --consume-notify` החזיר `notify=true armed=true enabled=true` digest `bf212b351df3665e` (55 ממתינים, כולם reviewed). `gh workflow run gmail-tool-updates-send.yml` החזיר HTTP 403 `Resource not accessible by integration` (workflow 368772560). הבקשה הוחזרה ל־`enabled:false`. אין Gmail message id. אין claim של שליחה. דגלי `notifyOwner` נוקו על ידי ה־renderer לפני הכישלון, ולכן אין שליחה חוזרת בלי גילוי או החלטה חדשים.

מייל מחקר לבעלים: לא. `owner_notify` לא נדרש.
