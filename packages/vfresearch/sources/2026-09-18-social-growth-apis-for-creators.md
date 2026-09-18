# social-growth-apis-for-creators — VelvetOS review · 2026-09-18

Status: **embedded as provider discovery only**. No provider runtime, scheduler, analytics source of truth, publishing path, or engagement automation is added.

## Source lock

- Upstream: https://github.com/cporter202/social-growth-apis-for-creators
- Reviewed upstream commit: `807993fcd3b1c14efab3a8912c9d6c08c571374e`
- Review date: 2026-09-18
- Upstream README inventory: 2,786 entries across 6 sections, last updated 2026-09-16.
- Category counts at the reviewed commit:
  - Instagram & TikTok: 848
  - YouTube & Video: 356
  - Twitter/X & LinkedIn: 488
  - Facebook & Meta: 233
  - Analytics & Listening: 418
  - Other Social Tools: 443
- Exact category enumeration at review: 2,786 / 2,786 catalogue rows resolve to `apify.com`. The catalogue is therefore treated as an Apify Actor discovery index, not as a code dependency.

Affiliate query parameters in catalogue URLs are not part of provider identity or VelvetOS configuration.

## Fit for Velvet Factory

The useful value is **discovery and comparison of external public-data adapters** for the Social Intelligence flow that already exists in `vfresearch`.

Preferred candidate families from the reviewed catalogue:

1. **Reference Reel / public Reel research**
   - `apify/instagram-reel-scraper`
   - Use: public Reel/profile evidence, captions/transcripts when returned, timestamps, hashtags and observed public metrics for reference mechanics.
   - Destination: normalize into `SocialResearchPacket` / `reference-pattern.schema.json`. Never copy creative expression.

2. **Instagram hashtag intelligence**
   - `apify/instagram-hashtag-analytics-scraper`
   - Use: total post count, posts/day, top/latest posts and related hashtags when the provider returns them.
   - Destination: external evidence only; no fabricated trend conclusion and no replacement of own-account Insights.

3. **Meta creative intelligence**
   - `apify/facebook-ads-scraper` (catalogued as Facebook Ads Library Scraper)
   - Use: public Meta Ad Library research for creative/category/reference signals.
   - Destination: research evidence only. This does not authorize ad creation, boost, spend, or campaign execution.

4. **Narrow competitor/reference monitoring**
   - `instaprism/instagram-post-monitor` is a discovery candidate for public new-post monitoring.
   - Treat provider alerts/webhooks as optional transport only; VelvetOS must normalize the returned public evidence and compute its own deterministic delta.
   - Provider status, price, limits and current availability must be revalidated at use time.

Secondary research-only candidates:
- public TikTok trend actors may be used as an early external trend signal; they do not enable TikTok as a VF publishing channel.
- `nexgendata/social-content-mcp-server` is interesting as a search adapter but is **not** installed as a second MCP/runtime.
- autocomplete/keyword actors may support point research when ordinary web evidence is insufficient.

## Explicit rejects

Do not select catalogue entries whose primary behavior is:
- bulk DM / DM automation;
- follow/unfollow automation;
- automated comments, likes or engagement manipulation;
- mass outreach or influencer-contact automation;
- phone/email lead harvesting for outreach;
- automatic social publishing that bypasses `vfigos` / Instagram MCP;
- private/session-cookie scraping, login bypass or copied owner auth;
- black-box “viral score”, sentiment or strategy output used as fact.

Raw observed data may be used with provenance. Provider-generated conclusions remain provider claims, not VelvetOS truth.

## Provider-selection gate

A candidate may be used only when all of the following are true for the exact run:

1. The task needs public external evidence and ordinary `WebSearch` / `WebFetch` is insufficient.
2. The exact Actor/provider is revalidated as available for the requested public data.
3. Input scope is narrow and named; result caps and cost exposure are bounded before execution.
4. No owner cookies, private auth, login bypass or engagement automation are required.
5. Each accepted row preserves `source_url`, provider and observation time.
6. Missing metrics remain null/absent, never zero.
7. Own-account profile/media/Insights remain canonical in Instagram MCP / `vfinsights`.
8. The provider gets no publish/send authority.

Prefer an official platform/provider Actor when it satisfies the evidence need; otherwise select the smallest currently verified adapter that does.

## Competitor/reference watch pattern

No new scheduler is introduced.

The acquisition side may collect two bounded snapshots for the same named public watchlist. VelvetOS then runs the existing deterministic helper:

```bash
python3 scripts/vf_social_intelligence.py watch-delta \
  --previous previous-packet.json \
  --current current-packet.json \
  --output watch-delta.json
```

The delta contract:
- reports new public signal URLs appearing in the current packet;
- emits metric deltas only for the same `source_url + provider` present in both snapshots;
- groups descriptive counts by public author/handle when present;
- never coerces missing metrics to zero;
- never ranks one account against another;
- never produces a global virality score.

Any recurring acquisition must reuse an existing authorized scheduler/control-plane path; this integration does not create one.

## Integration points

- recurring discovery registry: `packages/vfresearch/LINKS.json`
- authority/playbook: `packages/vfresearch/SOCIAL-INTELLIGENCE.md`
- deterministic normalization + snapshot delta: `scripts/vf_social_intelligence.py`
- validation: `scripts/check-social-intelligence.py`
- output continues to the existing `vfom/INSTAGRAM-CONTENT-DECISION.json` path.

## Evidence boundary

This review verifies catalogue contents and integration rules only. No Apify credentials were configured, no billable Actor run was executed, no live competitor scrape was performed, and no Instagram publish/send action was taken.
