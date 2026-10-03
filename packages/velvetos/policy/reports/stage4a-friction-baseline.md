# Stage 4A — Friction Baseline + Route Inventory

Status: **BASELINE SNAPSHOT · NO BEHAVIOR CHANGE**

Prepared against `main` `9989f0ffd11b97a28da732c9fa6ddd234ba51d35`.

This snapshot measures the current request-routing burden before Stage 4B changes the Project Request Gate. It is deliberately descriptive: no gate, authority, sensor, route or external-effect rule is disabled here.

## Headline metrics

| Metric | Current baseline |
|---|---:|
| Sampled routine flows | 14 |
| Baseline authorities resolved for every request | 9 |
| Auto-route aligned | 6 / 14 (42.9%) |
| General-business fallback | 8 / 14 (57.1%) |
| Project preflight PASS | 11 / 14 |
| Project preflight BLOCKED | 3 / 14 |
| Mean required sources | 13.29 |
| Median required sources | 10 |
| Mean hard gates | 5.14 |
| Median hard gates | 3 |
| Creative-prep burden | 22 sources / 5 packs / 11 gates |
| Production burden | 15 sources / 4 packs / 6 gates |
| Operations burden when explicitly routed | 11 sources / 2 packs / 3 gates |
| Research burden | 10 sources / 1 pack / 3 gates |

The key result is not simply “too many gates.” The present system has **both over-routing and under-routing**:

- Creative preparation can load 22 authority sources and 11 hard gates before exact evidence authorizes work.
- Eight routine examples fall back to `general_business`, so their Project Gate receipt is generic even when a downstream Gmail, Drive, DCC or operations contract is much more specific.
- `Prepare an Instagram carousel` currently falls through to `general_business` and receives a generic PASS; the same request forced through `creative_publication` is correctly BLOCKED pending exact creative evidence.
- CAD read-only correctly routes to `production`, but receives the same six hard gates as a printable build, including printer/price/print-authority constraints that do not belong to read-only inspection.

## Flow inventory

| Flow | Auto route | Project gate | Sources | Gates | Baseline finding |
|---|---|---:|---:|---:|---|
| Instagram post | creative_publication | BLOCKED | 22 | 11 | Correct scope; exact evidence required |
| Instagram Story | creative_publication | BLOCKED | 22 | 11 | Correct scope; exact evidence required |
| Instagram Reel | creative_publication | BLOCKED | 22 | 11 | Correct scope; exact evidence required |
| Instagram carousel | general_business | PASS | 10 | 3 | **Misrouted / under-gated** |
| Gmail reply | general_business | PASS | 10 | 3 | Coarse route; send law is downstream |
| Gmail send | general_business | PASS | 10 | 3 | Coarse route; commitment/price/facts are action-scoped downstream |
| Owner brief | general_business | PASS | 10 | 3 | Coarse route despite explicit owner-brief pipeline |
| Drive artifact | general_business | PASS | 10 | 3 | Coarse route; Visible Text is conditional on human-readable AI prose |
| Maya launch | general_business | PASS | 10 | 3 | Coarse route; Creative Craft compatibility/typed surface is downstream |
| Maya modeling task | general_business | PASS | 10 | 3 | Coarse route; specialist/typed route not represented |
| CAD read-only | production | PASS | 15 | 6 | Correct domain but over-gated |
| CAD build | production | PASS | 15 | 6 | Correct domain |
| Research update | research | PASS | 10 | 3 | Correct domain |
| Internal status | general_business | PASS | 10 | 3 | Coarse route; explicit operations route would be 11/2/3 |

## Downstream reality

### Gmail

`python scripts/vf_send_preflight.py --gate gmail` currently reports Gmail transport **ready**. `constitution/SEND.md` says HQ sends through tools; routine known-thread reply and owner brief do not wait for an owner click. The meaningful checks are reader-appropriate Visible Text + facts, with price/commitment/blast checks only when that action actually contains them, followed by provider evidence.

The current Project Gate does not express that distinction: both “Reply to this Gmail thread” and “Send this email to the customer” fall into generic business routing first.

### Owner brief

The real path is already specific and mostly internal:

`reader-first → vf-hebrew-copy → Humanizer/AI-tells → surface lint → fact/status validation → owner-brief Visible Text → render → Gmail provider evidence`.

Stage 4E should simplify/reuse exact-body evidence rather than make the owner approve routine delivery.

### Drive

The SEND law already scopes text readiness correctly: literal source data does not need rewriting; human-readable AI prose does. Ordinary internal `create_file` does not need owner approval.

### DCC / Maya

The current Creative Craft registry reports Maya as:

- production surface: `accepted-dcc-adapter`
- readiness: `READY_ACCEPTED_SURFACE`
- blocked: `arbitrary-agent-scripting`
- typed gaps: none

So the routine-path problem is not Maya availability. It is that the Project Gate classifies natural Maya requests as `general_business`, while the real compatibility + accepted typed-surface route lives downstream.

### Instagram

`policy_id: instagram.publish` is already the final machine authority for publish. Product Truth, brand, Visible Text, QA, transport and later CONTENT_READY should feed evidence into that authority rather than become owner-facing approval engines.

## Gate disposition inventory

The following classifications are the Stage 4A recommendation only; Stage 4A itself changes nothing.

| Current gate | Disposition | Reason |
|---|---|---|
| baseline_authority | INTERNALIZE | Resolve the minimum baseline internally |
| facts | KEEP | Truth invariant |
| offering_shape | ACTION_SCOPED | Customer/public offering claims only |
| canonical_source | KEEP | SoT invariant |
| sync_evidence | ACTION_SCOPED | Only when an external sync/write occurs |
| authority_boundary | INTERNALIZE | Router responsibility |
| verified_specs | KEEP | Engineering/product truth |
| fabrication_tool_route | INTERNALIZE | Automatic route selection |
| specialized_skill_instructions | INTERNALIZE | Load the relevant specialist behind the route |
| no_printer_control | ACTION_SCOPED | Actual printer-control attempts only |
| no_invented_price | ACTION_SCOPED | Price/cost surfaces only |
| print_authority | ACTION_SCOPED | Actual print/production execution only |
| source_evidence | KEEP | Research truth |
| no_invented_body | KEEP | Research truth |
| freshness | KEEP | Current-information truth |
| product_truth | MERGE | Preserve inside future CONTENT_READY evidence |
| visual_standard | MERGE | Preserve inside CONTENT_READY |
| creative_transformation | MERGE | Quality evidence; auto-repair before escalation |
| brand_asset | MERGE | Preserve inside CONTENT_READY |
| public_cta | ACTION_SCOPED | Only when public CTA exists |
| visible_text | ACTION_SCOPED | Only when human-visible AI-written/rewritten text exists |
| exact_final_qa | MERGE | Final-artifact evidence inside CONTENT_READY |
| reference_match | ACTION_SCOPED | Only when an approved aesthetic reference exists |
| actual_file_evidence | KEEP | Exact artifact identity |
| rejected_direction | INTERNALIZE | Correction memory, not owner ceremony |

## What Stage 4B must improve

Stage 4B should make the Project Request Gate a thin risk/scope router:

- read-only, routine LOW-risk, already-authorized, known-domain requests use a **minimal baseline + scope route**;
- full preflight remains for external mutation, unknown domain, authority conflict, stale critical evidence, spend/rights/privacy/destructive effect or a new route;
- the receipt stays internal unless it explains a real blocker;
- route precision must improve before the fast path is trusted — especially carousel, Gmail, Drive, DCC and internal operations;
- no invariant is removed merely because it creates friction. It must first be moved to the correct scoped/internal evidence surface.

## Acceptance metrics for comparison after 4B

A post-4B replay of the same 14 requests should show:

1. fewer baseline authority sources for routine LOW-risk requests;
2. a materially lower `general_business` fallback rate;
3. no creative/publication under-classification such as the current carousel case;
4. fewer irrelevant hard gates on read-only/routine routes;
5. no weakening of facts, canonical-source, verified-spec, freshness, exact-artifact or external-effect safeguards;
6. zero extra owner prompts for routine flows when the answer/evidence already exists.

Machine-readable snapshot: `stage4a-friction-baseline.json`.
