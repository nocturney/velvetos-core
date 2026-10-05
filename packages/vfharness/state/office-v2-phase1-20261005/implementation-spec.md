# Office v2 Phase 1 — implementation spec

Authority: START HERE Google Doc `15NMtyaUDjxiACPKEY_T5rW7IUFwtD2qU88yhbKQhEkw`, Phase 1 “Neutral Lab & Safety Boundary”.

Accepted baseline: `origin/main@d755c4cb62e2fde16f6c5804db180d48170238ba` after Phase 0 exact-main acceptance.

## Goal
Create a neutral, reversible LAB boundary and its executable admission/health contracts without granting the LAB production authority or credentials.

## Current host admission
Windows host mutation is **MAINTENANCE_BLOCKED**:
- CPU/firmware virtualization + SLAT: available.
- Windows optional features `Microsoft-Windows-Subsystem-Linux` and `VirtualMachinePlatform`: enabled.
- WSL userspace: not installed.
- Docker: absent.
- Existing CBS reboot + pending file-renames: present.
- Desktop Commander + DCC Gateway: boot/SYSTEM capable.
- GrokBot + AdobePy brokers: logon-triggered, therefore reboot is not operationally transparent.

Canonical live admission evidence:
`D:/Velvet/Artifacts/OfficeV2/phase1/evidence/2026-10-05/windows-host-admission.json`.

## Phase 1 deliverables
1. Dedicated LAB identity, network, service names, ports and storage roots.
2. Shared Windows↔WSL artifact lane.
3. LAB credential/egress contract: LAB-only by default; no production credentials.
4. Minimal OTel collector definition carrying Phase 0 correlation IDs.
5. Teardown/recreate tooling and dry-run proofs.
6. Node Contract v0 publisher/validator for NODE-A; Mac inventory compatible with same contract.
7. Backup target + restore-drill definition.
8. Safe WSL2/Docker maintenance runbook; actual host mutation only after maintenance admission.
9. Stateful candidate rule: no production-capable state until restore drill passes.
10. No universal Postgres, durable engine, model gateway, MCP/A2A, NATS, feature-flag or sandbox winner.

## Neutral LAB defaults
- Windows root: `D:/Velvet/OfficeV2Lab`
- WSL source: Ubuntu 26.04 LTS; dedicated instance: `OfficeV2-Lab`
- Container runtime: Docker Engine + Compose plugin inside the dedicated WSL2 instance; Docker Desktop is not required
- Shared artifact lane: `D:/Velvet/OfficeV2Lab/artifacts` ↔ `/mnt/d/Velvet/OfficeV2Lab/artifacts`
- Network name: `officev2_lab`
- OTel host ports: `14317→4317`, `14318→4318`
- Reserved candidate DB host port: `15432` (unused until admitted)
- Node/health reserved host port: `18780`
- `18080` is explicitly excluded because it is in use on the live host.

## Non-goals
- No host reboot from an unadmitted state.
- No copying production secrets into LAB.
- No production writer or production SoT cutover.
- No candidate winner selection merely because a container can run.
- No untrusted/generated code directly on the Windows/WSL host.

## Verification
- RED then GREEN: `python scripts/check-office-v2-phase1.py`
- LAB doctor dry-run must work with WSL/Docker absent and return `MAINTENANCE_BLOCKED_PREP_ALLOWED`, not false success.
- Node manifest generator must self-test and validate Phase 0 Node Contract v0 fields.
- Teardown/recreate plan must be dry-run safe before any Docker install.
- Existing repository suite remains green after Phase 1 definition changes.

## Gate
Phase 1 cannot be GREEN until:
- LAB can be destroyed/recreated without production impact;
- one stateful LAB service restore drill passes;
- production secrets remain inaccessible to LAB by default;
- one end-to-end trace carries correlation IDs;
- NODE-A publishes a valid capability/health manifest.

Until the host-maintenance gate is admitted, Phase 1 status is `PREP_IN_PROGRESS / HOST_MUTATION_BLOCKED`.
