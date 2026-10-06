# Office v2 Phase 1 — tickets

## P1-A · Host admission and LAB contract — DONE
Post-reboot admission is recorded; production recovery passed before WSL/Docker continuation.

## P1-B · Neutral LAB definition — DONE
Dedicated LAB network/storage/OTel definition is realized with only the isolated artifact lane mounted.

## P1-C · Node Contract publisher — DONE
Fresh NODE-A manifest from the closure tree validates and reports WSL 3.0.1.0, Ubuntu 26.04.1 LTS, Docker 29.8.2, Compose v5.6.0, systemd and the isolated artifact lane.

## P1-D · Destroy/recreate + restore tooling — DONE
LAB destroy/recreate and a disposable PostgreSQL stateful restore drill passed; PostgreSQL remains drill-only and non-authoritative.

## P1-E · Controlled WSL2/Docker maintenance — DONE
The pre-existing reboot transition was separated first; WSL/Ubuntu/Docker were then installed and verified without production regression.

## P1-F · Phase 1 gate — FORMAL CLOSURE IN PROGRESS
Technical criteria are PASS. Canonical 118-sensor regression is PASS and the temporary user-context Scheduled Task is deleted. Remaining formal work: seal gate/Project State receipts, merge the dedicated closure PR, and verify exact-main CI.

Phase 2 is not allowed to start until P1-F is formally GREEN.
