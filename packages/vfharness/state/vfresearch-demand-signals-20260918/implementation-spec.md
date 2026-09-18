# Implementation spec — vfresearch structured demand signals

Goal:
Add evidence-preserving structured demand research to the existing vfresearch/Print-Demand workflow, using provider adapters rather than a new runtime or source of truth.

Non-goals:
- No Apify runtime, scheduler, MCP server, or credentials in git.
- No automatic SKU promotion, pricing, publishing, outreach, or demand/virality score.
- No replacement of WebSearch/WebFetch, SocialResearchPacket, vfinsights, vlicense, or existing research cadence.

Authority / SoT:
- packages/velvetos/PROJECT-REQUEST-GATE.md
- packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json
- packages/vfresearch/SKILL.md
- packages/vfresearch/hq/PRINT-DEMAND.md
- packages/vfresearch/SOCIAL-INTELLIGENCE.md
- packages/vfharness/SKILL.md
- owner approval in chat on 2026-09-18

Acceptance criteria:
1. API-mega-list and social-growth catalogue are registered as discovery-only sources.
2. A stable DemandSignalPacket contract preserves provider/source/query/geo/window/observed metrics and series without inventing missing values.
3. A deterministic local normalizer/validator exists and explicitly rejects synthetic demand scores.4. Print-Demand and Social Intelligence document provider selection and the boundary between signal and business truth.
5. Existing vfresearch sensor and the full repository sensor suite pass on the isolated branch.

Evidence:
- RED then GREEN test for scripts/test_vf_demand_signals.py.
- python scripts/vf_demand_signals.py --self-test
- python scripts/check-vfresearch.py
- python scripts/check-all.py
- focused git diff review.

Risk / gates:
Provider runtime remains UNPROVEN without APIFY_TOKEN. Repository implementation must not claim provider execution.
