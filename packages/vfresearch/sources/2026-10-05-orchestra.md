# Research Seat · 2026-10-05

State: `ready_for_brief`
Observed run: Monday 2026-10-05, ~02:10–02:50 Asia/Jerusalem, before the 07:00 cutoff. UTC clock at fetch was still 2026-10-04 evening.
Seat: Velvet Research Seat
Path: Grok Bot GitHub CLI failover (fresh `gh` clone under `/tmp`, live WebSearch + WebFetch + `gh api`). No Cursor Cloud Agent. No chatgpt.com / gemini.google.com / perplexity.ai. No Morning Brief send.

## Research metadata

- **as_of:** 2026-10-05 ~02:10–02:50 Asia/Jerusalem (2026-10-04 ~23:10–23:50 UTC). Every source below was fetched live in this window.
- **provenance:** the URLs under each finding; `upstream-watch-latest.json` (checkedAt 2026-10-04T23:11:10Z); LinklyAI/best-skills commit `fcdab075666a2332fcfc6ff6fd70584d2fa7eddf` (`data: 2026-10-04`) + https://linkly.ai/skills.
- **uncertainty:** sources are supplier/vendor blogs and tech press, not a Sderot order log and not `@velvets_cloud` Insights. Meta One prices and Edits availability are US/EU figures from press; Israel availability and price were not verified. Upstream verdicts reuse the 2026-10-04 review from unmerged PR #488 as their base (see Upstream).
- **refresh_target:** next Velvet Research Seat (2026-10-06 02:00 Asia/Jerusalem); Best Skills due again at `lastPass` + 44h; MakerWorld on Wednesday 2026-10-07.

## Current authority / context

- Read `AGENTS.md`, `instances/velvet-factory/AGENTS.md`, `packages/vfops/AGENTS.md`, `packages/vfops/ROUTINE.md`, `packages/vfops/LOOP.json`, `constitution/VISIBLE_TEXT.md`, `packages/vfresearch/AGENTS.md`, `SKILL.md`, `DAILY.md`, `ARTIFACT-CONTRACT.md`, `BEST-SKILLS.md`, `BEST-SKILLS.json`, `TIMER.md`, `hq/MAKERWORLD-SCAN.md`, and `packages/vfops/data/research.md` (2.10.2026 on main).
- Main consumer before this seat: 2.10.2026. Research Seat PRs #488 (4.10, CI red), #459 (3.10), #446, #438, #430, #405 are still open and were not merged or reused as findings.
- Best Skills: `lastPass` on main is 2026-10-02 (~72h, stale >52h) → executed. Artifact: `packages/vfresearch/sources/2026-10-05-best-skills.md`. Result: `no-embed-existing-coverage`. dataDate `2026-10-04`.
- MakerWorld/Printables: `MAKERWORLD-SCAN.md` says Sunday and Wednesday only. Today is Monday → לא יום סריקה.
- Weekly links: the 4.10 pass is on main (`sources/2026-10-04-weekly-links.md`, commit `912dc298`). This seat only replaced the stale 25.9 summary in the consumer with that pass's own block-05 line. No links were re-reviewed here.

Anti-recycle (not re-sold): 2.10 lead-time clock starts at production release; approval as the queue card; fit check before price; kit identity lock; film the real job. Unmerged 3.10: seven price-deciding intake fields; technical file review; acceptance criteria + first article; QC before pack-out; local trust from real finished work. Unmerged 4.10: catalog family, named proof version, license line as the SKU gate. Unmerged 1.10: FPY + versioned profiles; deposit before print; QC levels; functional short-print SKUs; order form outside DM chaos. Earlier filament reorder points (24.9, 28.9) are about material stock, not customer reorders.

## ממצאים

### 1. A repeat order starts from a named baseline, not from "same as last time"

Sources:
- https://www.goodprints3d.com/blogs/3d/can-a-print-farm-handle-repeat-small-batches-without-turning-every-reorder-into-a-new-project — GoodPrints3D / JC Print Farm, dated June 16, 2026. Fetched live 2026-10-05.
- https://www.jcprintfarm.com/pages/production-runs — JC Print Farm production-runs page, sections "materially updated" September 17–19, 2026. Fetched live 2026-10-05.

What the pages say: a reorder becomes routine only when the earlier job is already a released baseline: controlling file revision, item name, material and color, finish, the few checks that matter, quantity, and pack-out. "Same file as last time" is not a baseline, because a new color, added hardware or different bagging makes it a different order. The reorder note should carry a change statement: either "no change from baseline job X" or a list of the differences. Changes to geometry, material or color, quantity or date reopen price, schedule or proof; a label-only fix may not. The second page adds that a forecast ("we may need more") is not a release.

What we do: on `vfconvert` / `vfsales`, when a past customer asks for "אותו דבר שוב", the reply card names the earlier job, the file version, material/color, quantity and what changed. If nothing changed, it can move straight to the queue line from the earlier record. If anything changed, it is a fresh check and a fresh quote. «אולי נצטרך עוד» stays a note and does not reserve printer time. On `vfprod`, a finished custom job keeps one short baseline line so the next request can point at it. No invented ₪. Pickup in Sderot only.

Distinct from 4.10 "named proof version" (unlock of a first job) and 2.10 "approval as queue card" (first acceptance): this is the second and later order of something already made.

Confidence: high for the baseline + change-statement rule. Medium for how many VF jobs actually repeat today; the jobs record was not read in this seat.

Limitation: both pages come from one US print farm selling B2B production runs (POs, cartons, freight). We take the baseline and change statement only, not the procurement layer.

### 2. A quote that says what "yes" does gets fewer silent customers

Source: https://salesqueze.com/blog/why-buyers-go-silent-after-a-quote/ — SaleSqueze, Eva Rebič, 24 May 2026. Fetched live 2026-10-05.

What the page says: silence after a quote is rarely about price. The buyer is unsure about one of four things: whether the spec they picked is right, what saying yes triggers, who else has to agree, or whether the seller will deliver. More "just checking in" messages do not fix that; a quote that answers the four on the same page does. Practical moves: show the buyer their own configuration (not a catalog image), state the next step in one sentence, make the quote forwardable to a partner, and stop after about three follow-ups.

What we do: on `vfsales` / `vfconvert`, a custom quote reply carries a picture or render of their exact item (real photo first when it exists), one sentence on what happens after «כן» (file final → queue → pickup message), and a short summary a partner or parent can read without the thread. Follow-up stays manual: no auto-DM and no reminder chain. The numbers on the page (22%→58% reply rate, 5–8% close rate) are the vendor's pergola/sauna case notes, not VF figures. No ₪ in this pattern.

Distinct from 2.10 (which event starts the pickup clock) and 3.10 (which intake fields come before price): this is how the quote message itself is built.

Confidence: medium. The source is a configurator vendor with customised outdoor-living clients, not a print shop.

Limitation: the "three follow-ups then stop" rule is the vendor's heuristic. VF keeps human judgment on any follow-up.

### 3. Instagram now lets an account place posts it is tagged in on its own grid

Source: https://techcrunch.com/2026/09/10/instagrams-latest-feature-lets-you-add-tagged-posts-to-your-profile-grid/ — TechCrunch, Lauren Forristal, September 10, 2026. Fetched live 2026-10-05.

What the page says: from September 10, 2026, Instagram rolled out a way to add a post you are tagged in to your main profile grid, from the tag notification, the post itself or the Tagged tab. The original post stays with its author. It is not duplicated, and it can be removed from the grid later without leaving the Tagged tab. This sits next to the June "Reorder your grid" feature.

What we do: when a customer posts a VF piece and tags `@velvets_cloud`, that post can become a real-work tile on our grid without reposting their photo. It is an option for Christian, not an automatic step: it needs the customer's permission and a privacy check (faces, home, names), and it must pass the approved grid standard and Brand Guardian like any other tile. It goes through `vfgrowth` / `vfcovers` / `vlicense`. No public action from this seat. No Insights count. Rollout to `@velvets_cloud` was not checked.

Confidence: medium-high for the feature as reported. Unknown for the account's own rollout.

Limitation: a tagged customer post may not meet the grid visual standard; then it stays in the Tagged tab.

### 4. Meta One puts links in organic posts behind a paid plan; Edits assistant reads account metrics

Sources:
- https://searchenginewatch.com/meta-one-turns-instagram-post-links-into-a-paid-feature/ — Search Engine Watch, Radu Tyrsina, 17 September 2026. Fetched live 2026-10-05.
- https://techcrunch.com/2026/09/30/instagram-rolls-out-an-ai-video-assistant-for-creators/ — TechCrunch, Amanda Silberling, September 30, 2026. Fetched live 2026-10-05.

What the pages say: Meta One launched on September 15, 2026. Clickable links in organic Instagram posts and Reels come only with the Advanced business plan and above, with a monthly quota reported by Social Media Today (4 posts + 4 Reels on Advanced). Prices and availability vary by region. Separately, the Edits app gained a chat assistant that reads the account's own metrics (follows, views, retention, shares, comments) and suggests ideas. Usage is limited; Meta One unlocks more.

What we do: nothing to buy. `NO_NEW_RECURRING_COST` holds, and `PUBLIC_CURRENT_CTA` stays an Instagram message to `@velvets_cloud`, so post links are not needed for the pickup flow. Any Edits assistant output is a third-party summary of metrics, not a VF Insight; own-account numbers still come only from the Instagram MCP / `vfinsights` path. Whether Edits assistant is offered in Israel was not verified.

Confidence: high that post links are paid-only. Low on regional price/availability for Israel.

Limitation: the link quota comes from secondary reporting; Meta's own post does not state it.

## Best Skills

Executed. Snapshot dataDate 2026-10-04 (commit `fcdab075`). `no-embed-existing-coverage`. See `2026-10-05-best-skills.md`.

## Upstream (לא לבריף)

- `python3 scripts/vf_upstream_watch.py check --write packages/vfresearch/sources/upstream-watch-latest.json` at 2026-10-04T23:11:10Z: 95 sources, 56 pending, 6 `newDetection`, 0 failed, `autoUpgrade=false`.
- `vfresearch_cadence.py review-routing` before review: 56 pending, 39 needing deep review on main's 1.10 review file. Base verdicts were taken from the 4.10 review (unmerged PR #488): 26 rows still matched the current HEAD/release exactly and were reused. The other 30 rows (29 moved since 4.10, plus `HKUDS/DeepTutor` with no review) were read through `gh api` compare + release notes and re-bound. After review: 56/56 current, `update 0 / wait 15 / review 12 / ignore 29`, `notifyOwner` false on every row.
- `python3 scripts/vf_upstream_email.py render --arm --consume-notify`: `notify=true` (newDetection), digest `fad549248401adce`, local Visible Text Gate on `tool-updates-latest.txt` = PASS (`owner-brief`, `FINAL_INTERNAL`).
- Tool-updates email: one `workflow_dispatch` attempt of `gmail-tool-updates-send.yml` on this branch was stopped by the Grok Bot safety review before it reached GitHub (needs owner approval). Not retried, no other route. Request left `enabled:false`. No Gmail message id, so no delivery claim.
- Receipt refresh: the watch moved pending from 50 to 56, so `stage7c-research-scheduler-consolidation.json` and `stage7-acceptance.json` were regenerated with their own generators and unchanged arguments. Only the routing counts and the stage7c hash changed.
- No ack. No upgrade. No pip/npm/git pull.

Toolchain rows stay out of `packages/vfops/data/research.md`.

## מה עושים

- Repeat request: name the earlier job + version + what changed; any change is a fresh check and quote.
- Quote reply: their own item in a picture, one sentence on what «כן» triggers, a forwardable summary.
- Tagged customer posts: an option for the grid, only with permission + grid standard.
- Meta One / Edits: no purchase; CTA unchanged; no Insights from third-party summaries.
- Best Skills: no embed.

## מה דולג

- MakerWorld/Printables scan: Monday, outside Sunday/Wednesday.
- Weekly links review: done on 4.10 by its own routine; not redone here.
- Fall décor trend pages (3DSEARCH, 3DCentral, Veranda, House Beautiful, loveeattravelrepeat): US/Etsy/Quebec season framing and US$ price claims, nothing verified for a Sderot pickup shelf. Not adopted.
- SeekMake "68% of quotes" page: fetch timed out; not cited. Its reminder automation would also be auto-follow-up.
- Print Shop CRM reorder/review automation and 3D Print Manager / 3D-Pi software pages: vendor product pages for paid automation; not adopted.
- Morning Brief: not sent.
- Owner research email: not sent (no blocker, findings go to the 09:00 brief).
- chatgpt.com / gemini.google.com / perplexity.ai: not opened.
- No new pack, no new repo, no Origin slug, no npx skills, no auto-DM, no boost, no Print from HQ, no Meta One purchase.

## מגבלות

No ₪. No Insights. No customer names. No claim that anything was posted or sent. Sources are a US print farm, a configurator vendor and tech press, not a Sderot order log.
