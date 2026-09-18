# Preflight — vfresearch structured demand signals

Base: origin/main @ 3499506ed9663fdfe742bef023f86921f6b42230
Branch: feat/vfresearch-demand-signals-20260918

| Task | Producer / Owner | Consumer / Dependent | Shared surface | Finding | Action |
|---|---|---|---|---|---|
| Contract + normalizer | vfresearch | Print-Demand | demand signal schema | new additive contract | continue |
| Print-Demand docs | vfresearch | weekly research cadence | PRINT-DEMAND.md | existing flow, no new scheduler | continue |
| Discovery registry | LINKS.json | WEEKLY.md | weekly source review | additive discovery-only entries | continue |
| Social adapter policy | SOCIAL-INTELLIGENCE.md | SocialResearchPacket flow | provider selection | no SoT change | continue |
| Sensor updates | check-vfresearch.py | check-all.py | repository proof | must remain deterministic | continue |
| Test | test_vf_demand_signals.py | vf_demand_signals.py | executable behavior | RED required before implementation | continue |

Ruling: keep acquisition outside the normalizer — credentials/provider calls are environment-specific and must not become a second runtime.
Ruling: no live provider benchmark in this task because APIFY_TOKEN/APIFY_API_TOKEN are absent; implementation can be proven locally while runtime remains UNPROVEN.
