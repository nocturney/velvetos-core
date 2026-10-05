# Office v2 Phase 0 — tickets

## P0-A · Baseline and live truth
Outcome: immutable timestamped live-state evidence + critical capability projection.
Depends on: accepted START HERE, project_preflight PASS.
Area/files: off-repo Evidence/State roots; no production mutations.
Verify: receipt references exact observations and no secret material.
Done when: current baseline can be reconstructed without chat memory.

## P0-B · Contracts and authority-safe semantics
Outcome: correlation, capability/provider/evidence/artifact/node, side-effect, effect-intent/effect-receipt, project-state and migration-ledger contracts.
Depends on: P0-A source observations.
Area/files: `docs/implementation/office-v2/phase0/contracts/`, contract registry, authority/state maps.
Verify: `scripts/check-office-v2-phase0.py`.
Done when: schemas parse, registry refs resolve, side-effect contract points to existing policy registry and forbids blind retry.

## P0-C · Continuity drill
Outcome: checkpoint → compact → verifier → resume proof without a second runtime.
Depends on: P0-B Project State contract.
Area/files: `scripts/vf_office_v2_continuity.py`; off-repo project-state checkpoints.
Verify: good compact returns PASS; authority/prohibited-action drift returns FAIL_CLOSED.
Done when: both positive and negative controls are captured.

## P0-D · Migration ledger + read-only console
Outcome: append-only project migration record and minimal read-only report.
Depends on: P0-B contracts.
Area/files: `scripts/vf_office_v2_migration_console.py`; off-repo migration ledger/reports.
Verify: report reads state only and performs no provider/business mutations.
Done when: initial Office v2 changes appear with rollback/verification refs.

## P0-E · Admission/trust/backup rules
Outcome: restore admission, credential classes and node trust rules are explicit.
Depends on: P0-B Node/Artifact/Evidence contracts.
Area/files: Phase-0 docs/config only.
Verify: targeted sensor + spec review.
Done when: stateful data cannot be restored blindly over newer truth and credentials are referenced by class, never embedded.

## P0-F · Integration proof and review
Outcome: post-change targeted/full checks, diff review, isolated branch commit/push.
Depends on: P0-A..E.
Verify: targeted sensor, policy architecture, check-all, independent review packet.
Done when: branch is reviewable and Phase-0 remaining blockers are explicit; no merge/deployment claim.
