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

## P1-F · Phase 1 gate — DONE / GREEN
All five technical criteria are PASS. Canonical 118-sensor regression is PASS, PR #565 is merged, exact-main Core Sensors run 37418107706 is GREEN, checkpoint 008 is sealed, temporary OfficeV2 tasks are removed, and the permanent WSL lease is headless/hidden.

Phase 2 Inventory, Contracts & Benchmark Engineering may begin. Implementation winners remain gated by contracts, Golden Fixtures and benchmark evidence.
