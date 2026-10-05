# Office v2 Backup / Restore Admission Policy v0

Phase 0 rule: backup existence is not restore authority. A stateful candidate is **not production-capable until a restore drill passes**.

## Required stateful-service admission record

Before any candidate persists important state, record all of the following:

| Field | Requirement |
|---|---|
| data owner | named authoritative owner/domain |
| storage path | exact logical/physical store reference |
| backup target | named backup destination/class |
| off-host copy | required/available state and location class |
| encryption | at-rest/in-transit expectation and owner |
| RPO/RTO class | explicit recovery-point and recovery-time class |
| restore procedure | executable or documented restore path |
| schema migration path | compatibility/migration path across versions |
| export/uninstall path | how data exits the candidate cleanly |
| health probe | exact post-restore proof |
| restore drill | timestamped evidence; must PASS before production-capable |

## State classes

- **VERSIONED_DEFINITION** — recover through Git/versioned review.
- **BUSINESS_TRUTH** — recover only through the owning domain system and its recovery semantics.
- **PROJECT_STATE** — recover only after Project State validation and continuity-verifier admission.
- **RUNTIME_STATE** — recover only with runtime-specific quiesce/version/schema checks.
- **EVENT** — replay/append only when the owning system declares replay safe.
- **GENERATED_ARTIFACT** — recover by digest/location; never overwrite newer authoritative truth.
- **DERIVED_SEARCH_OR_MEMORY** — rebuild from authoritative sources when possible.

## Restore admission outcomes

A stateful restore must compare source identity/digest/time/schema with the live target owner and current target version.

- `ALLOW_RESTORE` — compatible and no newer authoritative truth would be overwritten.
- `ALLOW_REBUILD_DERIVED` — derived/search/memory state should be rebuilt.
- `REQUIRE_RECONCILIATION` — source and target diverged; reconcile before mutation.
- `DENY_STALE_OVERWRITE` — restore would overwrite newer business/runtime truth.
- `DENY_UNKNOWN_SCHEMA` — compatibility is unproven.
- `DENY_AUTHORITY_MISMATCH` — the backup source does not own the target domain.

## Credentials and external effects

Credential material follows `credential-trust-classes-v0.json`; ordinary data backup never grants a credential or effect permission.

A restored queue/checkpoint does not re-authorize a side effect. Pending or unknown outcomes preserve the original intent/idempotency/policy-decision/receipt identities. `UNKNOWN_OUTCOME` is reconciled before retry.

## Phase 0 boundary

This policy defines admission only. Phase 0 does not move current production data, does not restore a production store, and does not make a candidate production-capable.
