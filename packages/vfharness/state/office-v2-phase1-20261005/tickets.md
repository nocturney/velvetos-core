# Office v2 Phase 1 — tickets

## P1-A · Host admission and LAB contract
Outcome: exact host prerequisites, reboot risks, ports, roots and credential boundary are explicit.
Verify: Phase 1 sensor + host admission receipt.
Done when: no install command is allowed while admission is MAINTENANCE_BLOCKED.

## P1-B · Neutral LAB definition
Outcome: network/service/storage/artifact-lane/OTel definitions exist without product winner bias.
Depends on: P1-A.
Verify: structural sensor and config parse.
Done when: compose/config can be rendered but not executed without WSL/Docker.

## P1-C · Node Contract publisher
Outcome: NODE-A and Mac can emit the same Node Contract v0 shape.
Depends on: Phase 0 Node Contract.
Verify: generator self-test + local live manifest.
Done when: Windows live manifest validates; Mac collection path is compatible.

## P1-D · Destroy/recreate + restore tooling
Outcome: scripts have dry-run plan, state boundaries and restore admission.
Depends on: P1-B.
Verify: no-op self-tests before Docker exists.
Done when: actual gate waits only for admitted host runtime.

## P1-E · Controlled WSL2/Docker maintenance
Outcome: install userspace/runtime and prove clean reboot/recovery.
Depends on: P1-A..D and maintenance admission.
Verify: boot recovery, WSL doctor, Docker doctor, no production credential leakage.
Done when: host mutation is proven rather than assumed.

## P1-F · Phase 1 gate
Outcome: lab destroy/recreate, one stateful restore, correlation trace and NODE-A manifest.
Depends on: P1-E.
Verify: exact receipts.
Done when: START HERE Phase 1 Gate is GREEN.
