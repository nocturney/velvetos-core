# Velvet Research Seat · 2026-09-14

Same-day public-source research body. Cutoff state: **`ready_for_brief`**. GREEN is based on this external research body, not CI/index success.

## Current authority/state read

- Read current `packages/vfresearch/DAILY.md`, `constitution/ORCHESTRA.md`, `packages/vfgrowth/CALENDAR.md`, `packages/vfsku/SHELF.json`, `packages/vfresearch/LINKS.json`, current Best Skills authority and latest research artifacts before research.
- Live `VF HQ · jobs/books/quotes` was checked. Office state still includes delivered receivables and one finished batch awaiting delivery/payment; this report avoids customer names because they are not needed for the research decision.
- Content reset remains active. No future content should be scheduled merely to fill cadence; VF-R001/R002/R003 remain blocked on rights + execution receipt.
- All five repeatable-SKU shelf slots remain empty. Product signals below are preflight candidates only until `vlicense` + local slice/cost/fit gates pass.
- Mac-Office was offline during this run. The Windows worker was available as the approved fallback for runtime/repo checks. The last locally verified production slicer observation remains Snapmaker Orca 2.3.5 from 2026-09-13; it was **not re-verified today**.

## External sources read

| Source | source/publication date | relevance |
|---|---:|---|
| Printables — Line hider · https://www.printables.com/model/1832415-line-hider | updated 2026-09-04; checked 2026-09-14 | 1 mm-thin reading aid; no supports; PLA/PETG; CC BY; Commercial Use allowed; personalization variants |
| Printables — Fidget Spiral · https://www.printables.com/model/1699407-fidget-spiral | updated 2026-09-06; checked 2026-09-14 | support-free PLA desk/sensory item; Commercial Use allowed; secondary candidate only |
| Printables — cleanable makeup holder · https://www.printables.com/model/1834110-cleanable-makeup-holder | updated 2026-09-06; checked 2026-09-14 | two-part, support-free, removable for cleaning; CC BY / Commercial Use; useful adjacent signal but bulkier than first-test target |
| Snapmaker Orca — v2.3.6 release · https://github.com/Snapmaker/OrcaSlicer/releases/tag/v2.3.6 | published 2026-08-26; checked 2026-09-14 | official release is marked Pre-Release; includes timelapse export and print preferences for spaghetti / foreign-object detection |
| Snapmaker Orca — v2.4.0-alpha · https://github.com/Snapmaker/OrcaSlicer/releases/tag/v2.4.0-alpha | published 2026-09-10; checked 2026-09-14 | official Alpha/pre-release; new UI/model/material features and dependency upgrades; not a production-upgrade recommendation |
| LinklyAI/best-skills · https://github.com/LinklyAI/best-skills/tree/main/data/2026-09-13/rankings | dataDate 2026-09-13; checked 2026-09-14 | newest confirmed dataset today; 2026-09-14 dataset was not yet present during the run |

## ממצאים — Top 3 for the 09:00 brief

### 1. New shelf preflight candidate: a tiny reading line-hider, not another large organizer

The fresh Line hider model is materially smaller and simpler than the large desk organizers repeatedly surfaced by marketplace search: the source describes a 1 mm-thin model, no supports, PLA/PETG and CC Attribution with Commercial Use allowed. It also supports personalization, which fits Velvet's strength without forcing a custom-only workflow.

**Velvet action:** `vlicense` confirmation → local slice → record actual grams/minutes → print one neutral sample → photograph it in real use → only then test one real inquiry. Do not assign a SKU slot or price before those gates.

**Confidence:** high for source/license/print-setup facts; medium for print simplicity; low for Sderot demand until Velvet gets a real inquiry signal.

### 2. Production: stay on the verified path; test failure-detection only in a sandbox

Snapmaker's official repo now has v2.3.6 and v2.4.0-alpha, but both are marked pre-release. v2.3.6 is interesting operationally because its release notes add preferences for spaghetti and foreign-object detection, which could reduce wasted print time/material if failed prints become a measured problem. That potential benefit does **not** justify changing the production slicer blindly.

**Velvet action:** no production upgrade today. When the Mac worker is back, re-verify the installed version and, only if failed-print waste is a measured bottleneck, test v2.3.6 on a non-production profile/job before any rollout. v2.4.0-alpha stays out of production.

**Confidence:** high for official release status/features; medium for potential waste reduction; local compatibility/benefit unproven.

### 3. Keep SKU experiments tiny while finished work and receivables are still open

The live office state shows that production capacity is not the only constraint: there is finished work awaiting delivery/payment and delivered work awaiting payment. Combined with five empty shelf slots, the right research response is **not** to start a batch of speculative inventory. One-print experiments preserve learning without adding another queue.

**Velvet action:** if a shelf experiment is run, cap it at one test print/photo until delivery/payment follow-through is cleaner and a real local inquiry validates the item. The Line hider is a better candidate for that test shape than a large organizer.

**Confidence:** high for current office-state observation; medium for the operational recommendation; no claim about customer demand is made.

## Best Skills maintenance — due today

`standingForever=true`; previous `lastPass=2026-09-12`, so the ~48h refresh was due and was executed inside this research run.

Required datasets read from the newest confirmed dataDate **2026-09-13**:

- https://github.com/LinklyAI/best-skills/blob/main/data/2026-09-13/rankings/best-100.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-09-13/rankings/trending-7d.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-09-13/rankings/social-buzz.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-09-13/rankings/top-repos.csv

Relevant durable signal: `mattpocock/skills` remains #2 in top-repos; `improve-codebase-architecture`, `codebase-design` and `domain-modeling` continue to rank/trend. No new embed is justified because `packages/vfharness/playbooks/agent-architecture-audit.md` already cites and implements the codebase-navigability pattern from `improve-codebase-architecture`, including evidence-first refactor gates and smallest-change fixes. Installing/duplicating that system would add overlap, not capability.

Other high-motion signals were deliberately skipped: Google Agents CLI (vendor CLI / second deployment path), social automation, self-improving runtimes, and duplicate orchestration runtimes. Hyperframes remains relevant only through the already-approved media pipeline, not as a second publishing/runtime system.

**Best Skills result:** `no-embed-existing-coverage`.

**Timer:** `UNPROVEN` — the required `cursor-subscriptions/list_subscriptions` namespace is not exposed in this runtime. No `timer: ok`/`renewed` claim is made and no duplicate automation was created.

Full maintenance note: `packages/vfresearch/sources/2026-09-14-best-skills.md`.

## Deliberate skips / limitations

- Marketplace popularity is not treated as Sderot/Israel demand.
- NonCommercial/restricted models found during search were excluded from product recommendations.
- Creator/source print claims are not Velvet production data; local grams/minutes remain unknown until slice.
- No price, Instagram Insight, customer claim, turnaround, or local demand was invented.
- No private subscription UI was browsed.
- Mac-Office being offline prevented same-day local slicer-version re-verification; yesterday's 2.3.5 observation is retained only as the last verified state.
- Best Skills legacy timer verification remains unproven because the named subscription namespace is unavailable here.

## Brief payload

```text
05 · מחקר ורעיונות
- מועמד preflight חדש למדף: line hider דק לקריאה — 1 מ״מ, בלי תמיכות, שימוש מסחרי מותר במקור; אצלנו עדיין חובה vlicense + slice + test print לפני SKU/מחיר.
- ייצור: Snapmaker Orca 2.3.6 ו-2.4.0-alpha מסומנות pre-release. 2.3.6 מוסיפה זיהוי spaghetti/עצם זר; אין שדרוג production, רק sandbox test אם בזבוז מהדפסות כושלות נהיה bottleneck.
- כרגע עדיף ניסוי של הדפסה אחת ולא מלאי: יש עבודה מוכנה/יתרות פתוחות, וחמשת סלוטי המדף עדיין ריקים. ללמוד קטן לפני שמוסיפים queue.
```

Cutoff state: **`ready_for_brief`**.  
Freshness: **2026-09-14 · GREEN body evidence**.
