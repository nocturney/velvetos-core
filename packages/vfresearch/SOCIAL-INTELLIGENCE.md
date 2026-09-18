# Social Intelligence — external signals inside vfresearch

Status: embedded into the existing `vfresearch` + Velvet Visual Foundry flow. This is **not** a new pack, scheduler, scraper runtime, analytics source of truth, or publishing authority.

## Purpose

Give the existing Instagram decision pipeline current, evidence-backed external signals without contaminating Velvet Factory voice or replacing canonical Instagram data.

The flow is:

`public external signal → normalized SocialResearchPacket → content-matrix candidates → saturation/anti-generic/format/hook/retention → vfcopy + Visual Foundry → vfigos → verified Instagram Insights → vfinsights learning`

## Source authority

1. **Our own account and posts:** Instagram MCP remains canonical for profile/media/Insights. Never scrape our own metrics when the Graph/MCP can return them.
2. **External public research:** use `WebSearch` / `WebFetch` first when they provide enough evidence. Browser/manual public-page inspection is allowed when authorized by the tool surface.
3. **Optional scraping provider:** Apify or another provider may be used only for public material when a normal web source is insufficient. Provider choice is an adapter detail, not a system dependency.
4. `cporter202/social-media-scraping-apis` is a **provider-discovery catalogue only**. Do not vendor, clone, or treat its thousands of listings as trusted integrations.
5. No cookies copied from owner sessions. No private/auth-only scraping. No login bypass. No automated likes, follows, comments, DMs, or engagement manipulation.
6. Costed scraping must be bounded and visible. Prefer cached public evidence and narrow watchlists over broad crawling.

## SocialResearchPacket

Canonical schema: `social-research-packet.schema.json`.

Every signal keeps provenance:

- `source_url`
- author/handle when public
- `published_at` when known
- `observed_at`
- media type
- public observed metrics only when actually returned
- topic / mechanic tags
- provider
- evidence quality
- raw reference or note

Missing metric stays absent/null. Never coerce unavailable → `0`.

The deterministic helper is:

```bash
python3 scripts/vf_social_intelligence.py normalize-signals --input raw.json --output packet.json --window-start 2026-09-07 --window-end 2026-09-14
python3 scripts/vf_social_intelligence.py validate-packet packet.json
```

The helper normalizes and validates facts. It does **not** invent trends, virality, sentiment, or recommendations.

## Reference Reel / short-form analyzer

Canonical schema: `reference-pattern.schema.json`.

A reference is used to learn **mechanics**, never to copy wording, identity, branding, footage, or protected creative expression.

Allowed extracted mechanics include:

- duration
- first spoken beat
- first visual change
- shot/event count
- overlay count
- reveal timing when explicitly annotated
- CTA type when explicitly observed
- hook/visual/narrative mechanic tags supplied by an analyst/model with source evidence

Flow:

`public reference URL → lawful acquisition / transcript / vision notes → vf_social_intelligence.py reference-pattern → REFERENCE-PATTERN.json → format_selection / hook_tournament / retention_pass`

HyperFrames / existing render tools remain the renderer. VoiceStudio remains the speech layer when used. The reference analyzer is research only.

## Content Matrix operator

The matrix is an **ideation operator inside `INSTAGRAM-CONTENT-DECISION.json`**, not a post generator or publisher.

Use 3–5 Velvet-specific content pillars and these eight angle families:

1. actionable
2. motivational
3. analytical
4. contrarian
5. observation
6. x_vs_y
7. present_vs_future
8. listicle

Every candidate must bind to real Velvet Factory proof (`proofRef`) or current external evidence (`source_refs`). A generic candidate with no proof is rejected before expensive generation.

A single strong `print.done` / real-proof opportunity may record `not_applicable_single_evidence`; the stage may never be silently skipped.

## Outlier / trend radar

External metrics are contextual, not directly comparable across accounts. An outlier score is allowed only when a baseline for the **same source/account and same metric family** exists. Otherwise write `outlier_score: null`.

No global “virality score”. No synthetic benchmark pretending to be measured data.

Recommended watchlist behaviour:

- narrow named public sources
- verified dates
- 7–30 day windows depending on the research task
- source-relative baselines
- clustering after collection, not before
- `why_now` must cite source refs
- `nothing-solid` is valid when evidence is weak

## Learning bridge

`vfinsights` writes `CREATIVE-PERFORMANCE-PROFILE.json` from verified `posts.csv` plus optional qualitative annotations in `data/creative-annotations.csv`.

The profile is a **prior**, never a truth override:

- each promoted pattern needs at least 3 measured posts for that pattern
- missing metrics stay null
- no composite virality score
- measured history may influence hook/format ranking, but proof, rights, brand fit, and quality gates still win

## External source inspirations embedded

- `charlie947/social-media-skills`: content matrix, data-backed post scoring, reference-Reel mechanics, date-verified niche research.
- `cporter202/automate-for-growth`: batching as cheap candidate expansion + feedback-loop discipline only; no ViralWave dependency.
- `cporter202/social-media-scraping-apis`: provider discovery only; no clone/runtime dependency.

All three stay registered in `LINKS.json` for recurring review.

## Preferred adapter selection

Provider catalogues are discovery indexes, never trusted integration lists. Select an adapter only for a named evidence gap: WebSearch/WebFetch first; then a narrow public provider if repeatability, transcript depth, structured metrics, or monitoring materially helps. Prefer bounded queries, explicit source URLs, observation timestamps, provider health/current docs, cached evidence, and normalization into the existing packet contracts. Never add a provider-specific scheduler or analytics source of truth.

`cporter202/social-growth-apis-for-creators` and `cporter202/API-mega-list` are discovery catalogues. Social signals continue to normalize into `SocialResearchPacket`; non-social search/marketplace demand observations use `DemandSignalPacket` from `DEMAND-SIGNALS.md`.
