# Office v2 Phase 2 Candidate Admission Policy v0

Authority: START HERE Phase 2. This policy defines benchmark admission; it grants no production authority.

## Admission order

`RESEARCHED → CANDIDATE → ADMITTED → LAB → SHADOW → PILOT → PRODUCTION`.

A candidate moves forward only when target-stage evidence exists. Availability, popularity, an easy install, incumbent failure, or prior discussion is never sufficient.

## COMPETITOR_NEUTRAL_ADMISSION_V1 — unbiased intake and replacement eligibility

Every plausibly relevant new alternative, including a direct competitor to the current core/office/agent runtime, is recorded as `DISCOVERED`/`RESEARCHED` in the canonical Candidate Registry **before** any "use patterns only", "skip", "we have a solution" or installation verdict. Record a source link, matching capability/fixture lane, whether it could replace the incumbent in whole or part or be composed with it, current evidence, and an explicit next decision. The historical 68-item source import is immutable; later candidates have `source_item_id: null` and a structured `comparison_review`.

A full benchmark shortlist remains 2–3 challengers for operational focus. Overflow goes in that lane's `queued_challengers`, not `REJECTED_WITH_REASON` or an untracked chat. Triage and promotion require comparable contract evidence, and previously frozen lanes can reopen for a credible challenger against the same fixture.

**Never decide from sunk cost or incumbent preference.** Exiting or deferring requires concrete capability/fixture, license, security, hardware, maintenance, cost, integration or migration/rollback evidence. "Overlaps our stack", "another orchestrator", "already implemented" or "we would need a rewrite" alone cannot justify rejection. LAB trials may compare replacement, parallel non-production or hybrid designs under isolation; unapproved production duplication is still prohibited.

**No authority expansion:** registry/research/queue state does not install software, grant network/credentials, change sources of truth, transfer external-effect authority or waive `NO_NEW_RECURRING_COST`.

## CANDIDATE → ADMITTED

Require all of:
- bounded capability/contract scope and a named shortlist lane where relevant;
- license, maintenance and ownership review;
- security/trust review and credential class;
- platform/hardware feasibility;
- isolation plan;
- resource/cost capture plan;
- rollback/export/uninstall plan, or an explicit recorded rollback failure;
- relevant Golden Fixture mapping;
- no new production writer or source-of-truth claim.

## ADMITTED → LAB

Require a versioned definition, reviewed immutable dependencies where practical, LAB-only credentials, bounded network/storage paths, health probe, teardown path and evidence location.

## LAB → SHADOW

Require relevant Golden Fixtures through a capability adapter, standard scorecards, security/operations scoring and reconciliation evidence. SHADOW has no production authority.

## SHADOW → PILOT → PRODUCTION

Require explicit bounded scope, rollback proof, operator visibility, authority-map/policy changes if production mutation is introduced, and readback receipts. A failed incumbent does not auto-promote a challenger.

## Exit verdicts

`REJECTED_WITH_REASON`, `BENCHMARKED_AND_LOST`, `SUPERSEDED`, and `DEFERRED_WITH_REASON` are valid from any appropriate stage and retain evidence plus a reason.

## Resource and cost capture

Capture wall time, CPU/RAM, GPU/VRAM when relevant, storage/network, external/API cost, recurring cost, operator burden, and install/maintenance burden. No universal numeric improvement threshold is imposed.

## Freeze rule

Stop researching when requirements are covered, fixtures ran, security and operations were scored, rollback was tested or explicitly failed, and a verdict was recorded. Reopen only for material evidence defined by `research-freeze-record.schema.json`.
