# Structured Demand Signals — adapters inside vfresearch

Status: additive research capability inside existing `vfresearch`. Not a new runtime, scheduler, source of truth, pricing engine, or SKU generator.

## Purpose

Use structured public demand evidence when ordinary WebSearch/WebFetch is too qualitative or inconsistent. Normalize provider output into `demand-signal-packet.schema.json`, then consume it from the existing Print-Demand / market-intel workflow.

Flow:

`public source/provider -> raw evidence -> vf_demand_signals.py -> DemandSignalPacket -> PRINT-DEMAND.md / MARKET-INTEL.md -> existing vfsku/vlicense gates`

## Source priority

1. WebSearch/WebFetch remain the default when they answer the research question with adequate evidence.
2. Structured provider adapter is used when time-series, geo, related-query, marketplace, or repeatable SERP evidence materially improves the decision.
3. Provider output is evidence, never authority. Missing fields stay null/absent; no synthetic demand score or virality score.
4. Provider credentials remain environment secrets. No token, cookie, private session, or login bypass is committed.

## Vetted candidate classes — 2026-09-18

- Google Trends: `apify/google-trends-scraper` is the preferred first benchmark candidate because it is maintained by Apify and exposes search terms, geo/time range, interest over time/by region, and related queries/topics.
- Google Trends fallback candidates may be compared only with identical queries/geo/windows; selection is an adapter detail.
- Etsy autocomplete/listing research is optional phase 2 for ready-product discovery. Treat suggestions/listings as observations, not sales proof.
- Google Keyword Planner is optional when actual volume/location data is worth the additional Google Ads + provider authentication burden.
- Structured SERP/PAA/related-search adapters are optional when WebSearch is insufficient for repeatable comparison.

## Contract

Canonical schema: `demand-signal-packet.schema.json`.
Deterministic helper: `python scripts/vf_demand_signals.py`.

Allowed signal kinds:
- `search_interest`
- `search_suggestion`
- `marketplace_observation`
- `serp_observation`

Every signal keeps at least source URL, provider, kind, query, observation time, metrics, series, and related terms where present. A missing metric never becomes zero.

## Business boundary

Demand evidence can justify more research or a candidate test. It cannot by itself:
- create/promote a SKU;
- establish commercial model rights;
- choose sale price;
- claim inventory/availability;
- trigger printing;
- trigger outreach/publication.

A product candidate still follows source/license -> slice/feasibility -> test -> existing `vfsku` promotion path. Public/marketplace prices are competitor observations only and never become Velvet Factory price authority.

## Provider runtime state

Repository wiring and local normalization can be proven without provider credentials. A live provider claim requires a real run receipt. If credentials are absent, report provider runtime as `UNPROVEN`; never convert a current vendor page or static sensor into a live-data receipt.

Contract rule names are explicit for sensors and downstream consumers: `missingMetricIsNotZero`, `syntheticDemandScoreForbidden`, `noAutomaticSkuPromotion`, and `licenseGateRequiredBeforePrintCandidate`.
