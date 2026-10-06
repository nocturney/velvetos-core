# Office v2 Phase 1 LAB Backup / Restore Contract v0

The LAB is disposable by design, but any stateful candidate must prove restore before it can be considered production-capable.

## LAB ownership

- Data owner: Office v2 LAB only.
- Storage root: `D:/Velvet/OfficeV2Lab/state`.
- Backup target: `D:/Velvet/OfficeV2Lab/backups`.
- Off-host copy: REQUIRED before any candidate can advance beyond LAB; destination is not selected by this Phase 1 prep step.
- Encryption: required for any backup that later contains sensitive candidate state.
- RPO class: LAB_BEST_EFFORT until a specific stateful candidate is admitted.
- RTO class: LAB_RECREATE_FIRST; restore time is measured during the drill.

## Restore admission record

Each stateful candidate records:
- candidate/service identity and schema version;
- source state path;
- backup artifact digest;
- backup timestamp;
- off-host copy state;
- schema migration compatibility;
- restore procedure;
- export/uninstall procedure;
- health probe;
- restore drill result;
- rollback/abort path.

## Restore drill

A valid drill destroys only the candidate's LAB state, recreates the service from versioned definition, restores the selected backup, runs its health probe, and verifies a known fixture or correlation identity.

A restore drill may never target a production store. A failed drill leaves the candidate LAB-only.

## Postgres rule

If a candidate later requires Postgres, it is a candidate-specific/disposable substrate. Availability on the LAB does not make Postgres a universal VelvetOS source of truth.

## Removal

Every candidate must have an export/uninstall path. Destroy/recreate tooling must be able to remove LAB containers/networks/volumes without touching `D:/Velvet` production state outside `D:/Velvet/OfficeV2Lab`.

## Phase 1 realized restore drill — 2026-10-06

The required Phase 1 restore drill passed using a disposable PostgreSQL 18.4 service solely as a candidate-specific restore fixture.

- Image: digest-pinned `postgres@sha256:a02db8cac496f15b094798a38254f14d6e00741f709360e5e00bb6668ea31636`.
- Host DB port: not exposed.
- Production data/credentials: not used.
- Fixture: `phase1-restore-fixture | before-destroy`.
- Backup: `D:/Velvet/OfficeV2Lab/artifacts/postgres-phase1-restore.dump`.
- Backup SHA256: `1802005DFDC691CCBA17FAA268AD110A04EFE37AED71201E11793734668B7A53`.
- Destroy: LAB DB volume/network removed.
- Recreate: database healthy; OTel healthy.
- Restore/readback: `pg_restore` PASS and the fixture query matched.
- Cleanup: drill DB container/volume removed; OTel remains.

Canonical raw evidence: `D:/Velvet/Artifacts/OfficeV2/phase1/evidence/2026-10-06/stateful-restore-drill-pass.json`.

This proof does not select PostgreSQL as a universal Office v2 database.
