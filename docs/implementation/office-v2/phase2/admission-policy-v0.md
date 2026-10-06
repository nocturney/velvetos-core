# Office v2 Phase 2 Candidate Admission Policy v0

Authority: START HERE Phase 2. This policy defines benchmark admission; it grants no production authority.

## Admission order

`RESEARCHED → CANDIDATE → ADMITTED → LAB → SHADOW → PILOT → PRODUCTION`.

A candidate moves forward only when target-stage evidence exists. Availability, popularity, an easy install, incumbent failure, or prior discussion is never sufficient.

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
