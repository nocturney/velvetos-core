# Office v2 Phase 1 — implementation spec

Authority: START HERE Google Doc `15NMtyaUDjxiACPKEY_T5rW7IUFwtD2qU88yhbKQhEkw`, Phase 1 “Neutral Lab & Safety Boundary”.

Closure baseline: `origin/main@6c3865acee79fb11dbaeeace0a5bc73f9624d187` at the start of formal Phase 1 closure.

## Goal
Create a neutral, reversible LAB boundary and prove it without granting the LAB production authority or credentials.

## Realized host/runtime state
- Controlled reboot completed before new WSL/Docker mutation.
- CBS RebootPending=false and Windows Update RebootRequired=false.
- Residual delete-only/temp file-renames remain visible and are not manually cleared.
- WSL runtime 3.0.1.0; kernel 6.18.40.1-1.
- OfficeV2-Lab: Ubuntu 26.04.1 LTS, WSL2, user officev2 uid 1000.
- Docker Engine 29.8.2; Compose v5.6.0; systemd and Docker active.
- Full Windows drive automount is disabled in the LAB.
- Only `D:/Velvet/OfficeV2Lab/artifacts` is exposed at `/var/officev2/artifacts`.
- OTel is loopback-only on 14317/14318/14319.

Canonical raw evidence remains outside Git under `D:/Velvet/Artifacts/OfficeV2/phase1/evidence/2026-10-06/` and `D:/Velvet/OfficeV2Lab/`.

## Deliverable status
1. Dedicated LAB identity/network/service/storage boundary — REALIZED.
2. Isolated Windows↔WSL artifact lane — VERIFIED.
3. LAB-only credential boundary / no production credentials — VERIFIED.
4. Minimal OTel using Phase 0 correlation IDs — VERIFIED E2E.
5. Destroy/recreate tooling and real proof — VERIFIED.
6. Node Contract v0 publisher/validator for NODE-A — VERIFIED; Mac remains compatible with the same contract.
7. Backup target and one stateful restore drill — VERIFIED.
8. Controlled WSL2/Docker maintenance sequence — EXECUTED AND VERIFIED.
9. Stateful candidate admission rule — PRESERVED.
10. No durable-engine/model-gateway/MCP-A2A/NATS/feature-flag/Postgres-universal winner — PRESERVED.

## Gate
The five START HERE technical criteria are backed by live evidence. The canonical 118-sensor regression passed, PR #565 merged at `cf040c36a3d772ffd425586bfd80f02313621360`, exact-main Core Sensors run `37418107706` is GREEN, Project State checkpoint 008 is sealed, and routine WSL operation is headless. Phase 1 is formally GREEN; Phase 2 may begin without preselecting implementation winners.
