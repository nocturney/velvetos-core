# VelvetOS Office v2 — Phase 1 Neutral Lab & Safety Boundary

Phase 0 is closed on canonical main at `d755c4cb62e2fde16f6c5804db180d48170238ba`.

This directory contains versioned Phase 1 definitions only. The active LAB runtime, backups, artifacts and node observations live outside Git.

## Current status

`PREP_IN_PROGRESS / HOST_MUTATION_BLOCKED`

The Windows host already has pending reboot state. WSL/VMP optional features are enabled, but WSL userspace and Docker are absent. Desktop Commander and the DCC Gateway are boot/SYSTEM capable; GrokBot and AdobePy brokers are logon-triggered. Host mutation therefore waits for a controlled maintenance admission.

## LAB identity

- Root: `D:/Velvet/OfficeV2Lab`
- WSL source: Ubuntu 26.04 LTS; dedicated instance name: `OfficeV2-Lab`
- Container runtime target: Docker Engine + Compose plugin inside the dedicated WSL2 instance; Docker Desktop is not required
- Network: `officev2_lab`
- Shared artifact lane: `D:/Velvet/OfficeV2Lab/artifacts` ↔ `/mnt/d/Velvet/OfficeV2Lab/artifacts`
- OTel host ports: 14317 (gRPC), 14318 (HTTP), 14319 (health)
- Candidate database port: 15432, reserved but unused
- Node health port: 18780, reserved
- Port 18080: excluded because live host probe found it in use

## Safety boundary

- LAB has no production authority.
- LAB receives no production credentials by default.
- Stateful candidates are not production-capable before a restore drill.
- Untrusted/generated code does not run directly on Windows/WSL host.
- Candidate availability does not make it an architectural winner.
- No production writer or business SoT is moved in Phase 1.

## Runtime definitions

`tools/office-v2-lab/` contains a neutral Compose/OTel definition. It requires an explicitly supplied reviewed image reference; no `:latest` tag is accepted by the Phase 1 sensor.

## Gate

Phase 1 remains open until the START HERE gate is proven: destroy/recreate, one stateful restore, production secrets excluded, one correlated end-to-end trace, and a valid NODE-A capability/health manifest.
