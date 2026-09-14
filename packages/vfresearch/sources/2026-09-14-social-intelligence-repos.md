# 2026-09-14 — Social Intelligence repo review → embedded patterns

Sources reviewed deeply:

- https://github.com/charlie947/social-media-skills
- https://github.com/cporter202/automate-for-growth
- https://github.com/cporter202/social-media-scraping-apis

## Embedded

### `charlie947/social-media-skills`

Embedded patterns, not runtime:

- evidence-backed Content Matrix as candidate expansion
- measured-performance scoring principle
- reference Reel mechanics extraction
- date/source-verified niche research discipline

Rejected:

- LinkedIn-specific assumptions
- comment-gate / auto-DM behaviour
- generic clickbait hook rules
- duplicate voice/writer/analytics runtimes

### `cporter202/automate-for-growth`

Embedded patterns only:

- cheap candidate batching before expensive rendering
- core-content → format-specific adaptation principle
- measured feedback loop / A-B discipline

Rejected:

- ViralWave dependency
- generic virality score
- bulk publishing
- repeated personal-image “brand authority” mechanic

### `cporter202/social-media-scraping-apis`

Used only as provider-discovery catalogue.

Rejected:

- vendoring/cloning the catalogue
- treating listed actors as trusted by default
- scraping our own canonical Instagram metrics
- authenticated/private scraping, cookies, engagement automation

## VelvetOS mapping

- external signals → `packages/vfresearch/SOCIAL-INTELLIGENCE.md`
- normalization/reference mechanics → `scripts/vf_social_intelligence.py`
- candidate matrix → `packages/vfom/INSTAGRAM-CONTENT-DECISION.json`
- creative prior → `packages/vfinsights/CREATIVE-PERFORMANCE-PROFILE.json`
- enforcement → `scripts/check-social-intelligence.py`

No new pack. No second runtime. No second scheduler. No second analytics source of truth.
