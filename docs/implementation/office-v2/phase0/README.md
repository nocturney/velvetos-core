# VelvetOS Office v2 — Phase 0 foundation

Authority: START HERE Google Doc `15NMtyaUDjxiACPKEY_T5rW7IUFwtD2qU88yhbKQhEkw`.

This directory contains **versioned definitions only**. Live Office v2 project/runtime state, migration history and evidence live outside Git.

## Roots
- Versioned definitions: this directory.
- Project state: `D:\Velvet\State\OfficeV2\project-state\`
- Production capability projection: `D:\Velvet\State\OfficeV2\production-capability-manifest.json`
- Node manifests: `D:\Velvet\State\OfficeV2\nodes\`
- Master Ecosystem Inventory: `D:\Velvet\State\OfficeV2\ecosystem-inventory.json`
- Migration ledger: `D:\Velvet\State\OfficeV2\migration\ledger-v0.jsonl`
- Evidence: `D:\Velvet\Artifacts\OfficeV2\phase0\evidence\`
- Read-only reports: `D:\Velvet\Artifacts\OfficeV2\phase0\reports\`

## Compatibility rules
1. Reform v2 is closed and remains the baseline.
2. Existing `policy-registry.json` is the single external-effect authority map.
3. Existing `state-evidence-model.json` remains the semantic state/evidence/authorization/history model.
4. Office v2 state classes are an orthogonal storage/lifecycle axis.
5. Project State Manifest is continuation state only; it never becomes business truth, semantic-memory authority or policy authority.
6. Office v2 Phase 0 adds no production writer.
7. Existing Reform v2 repo-hosted operational state is not silently migrated by Phase 0; Phase 0 adds no new live state to Git.
8. WSL2/Docker are Phase 1 prerequisites and are intentionally not installed by this Phase 0 change.

## Phase 0 outputs
- Authority Map v0.1 with production writer/store/readers/mutations/fallback/forbidden second writers.
- Seven-class State Map mapped orthogonally to Reform v2 semantic categories.
- Cross-domain Correlation + Provenance contracts.
- Contract Registry v0 for Capability/Provider/Evidence/Artifact/Node/SideEffect plus Project State, EffectIntent/EffectReceipt and Migration Ledger.
- External Effect Safety Contract with idempotency, unknown-outcome reconciliation and no blind retry.
- Continuous Conversation Runtime v0: Context Pressure runbook + Project State + Post-Compaction Verifier.
- Backup/Restore Admission Policy with restore-drill requirement.
- Credential/trust classes with no production credentials in LAB by default.
- Master Ecosystem Inventory entry contract.
- Minimal read-only Migration Console/report.
- Registered `check-office-v2-phase0.py` sensor.

## Phase 0 live proof
The live proof is intentionally off-repo. Key receipts:
- `D:\Velvet\Artifacts\OfficeV2\phase0\evidence\2026-10-05\production-smoke-v0.json`
- `D:\Velvet\Artifacts\OfficeV2\phase0\evidence\2026-10-05\continuity-v0-verify-pass.json`
- `D:\Velvet\Artifacts\OfficeV2\phase0\evidence\2026-10-05\continuity-v0-verify-fail-closed.json`
- `D:\Velvet\Artifacts\OfficeV2\phase0\evidence\2026-10-05\final-check-all.json`

A green production smoke does **not** mean every capability is available. It means live paths work where expected and blocked/prohibited/unverified paths fail closed without inventing state or adding a second writer.

## Gate
Run:
`python scripts/check-office-v2-phase0.py`

Then run the existing Core gates, including `python scripts/check-policy-architecture.py`, `python scripts/check-office-watchdog.py` and `python scripts/check-all.py`.

Phase 1 may begin only from a sealed Project State checkpoint whose Phase 0 gate is GREEN.
