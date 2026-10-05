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
