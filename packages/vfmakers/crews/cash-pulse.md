# Crew: cash pulse

Source pattern: [makerskills `company-cfo`](https://github.com/coreyhaines31/makerskills/blob/main/skills/company-cfo/SKILL.md) — weekly pulse / monthly snapshot / scenario. **No live bank.**
Packs: `vfbooks`, `vfcost`. Seat: תפעול. Mention: `@bookkeeper-controller` `@finance-tracker`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Reader | `vfbooks` | Reads labeled mail + written ledger | Send a dunning note |
| Cost | `vfcost` | Units already in the pack | Invent sale ₪ |
| Human | — | Decides collection / wait | Agent as collector |

## Sources (only these)

1. `packages/vfbooks/` and `packages/vfcost/` text that already exists
2. Gmail **read**: `label:חשבונות OR subject:(חשבונית OR Invoice4U OR קבלה)`
3. A file the user named

No Mercury, Plaid, Stripe, Ramp, Gusto. No walk-back from a guessed balance. If two sources disagree, stop and write **חסר / סתירה** — do not average.

## Modes

| Ask | Mode |
|---|---|
| `@vfmakers cash` / weekly | **weekly** — 15-minute pulse |
| monthly / צילום חודשי | **monthly** — closed prior month |
| «מה אם» | **scenario** — only knobs that already have numbers |

## Weekly pulse

1. List bills / receipts from the last 7 days (subject + date, no secret dump).
2. Open receivables **only** if `vfbooks` already has an amount. Else `X ₪` / «אין במקור».
3. Known outflows in the next 7 days from calendar or labeled mail.
4. One Hebrew line: `קופה: <מאומת או אין במקור> · כניסה ידועה · יציאה ידועה · רצפה: בסדר / לעיון / חסר`
5. Write `packages/vfbooks/hq/pulse/YYYY-WW.md` and append `INDEX.md`.

Do not email the customer. Do not chase debt from HQ.

## Monthly snapshot

Same sources, closed month. Sections:

1. TL;DR — only numbers that appeared in Phase sources
2. Cash in — Invoice4U / labeled receipts
3. Cash out — bills
4. Open items — questions, not forecasts
5. Recommended **decisions** for the lead seat → `crews/decide.md` if material

No ranking of «most profitable jobs» unless both `vfcost` cost **and** a verified sale amount exist.

## Scenario

«What if we hire / buy / open B2B» — copy existing numbers only. Missing input stays `X ₪`. B2B logos/QR/napkins stay locked unless the lead seat already opened them in `vfbiz`.

## Done when

The pulse file exists and every figure is cited or marked **אין במקור**.
