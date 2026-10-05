# Office v2 Phase 1 — Neutral Lab & Safety Boundary preflight

Baseline: Phase 0 GREEN checkpoint `office-v2-phase0-v0-cp003-green`, code commit `bfe5af897ceea81d060a9dc450d3ec68b0b05fcc`.

Canonical project preflight: PASS for `system_engineering` in FULL mode.

## Live readiness
- Windows virtualization firmware: enabled.
- VM Monitor Mode Extensions: yes.
- SLAT: yes.
- Windows Subsystem for Linux feature: Disabled.
- VirtualMachinePlatform feature: Disabled.
- WSL CLI: not installed.
- Docker CLI/runtime: not installed.
- Current execution identity belongs to BUILTIN\Administrators.

Evidence: `D:\Velvet\Artifacts\OfficeV2\phase1\readiness-20261005.json`.

## First bounded change
Enable only:
1. `Microsoft-Windows-Subsystem-Linux`
2. `VirtualMachinePlatform`

Use DISM `/NoRestart`. Do not install Ubuntu or Docker until the feature state is re-read and the required reboot boundary is explicit.

## Safety invariants
- No automatic reboot.
- No production credentials in LAB.
- No production writer or authority moves into WSL/Docker.
- No durable-engine/model-gateway/MCP-A2A/NATS/feature-flag winner selection.
- No manufacturing SoT cutover.
- No untrusted/generated code on the Windows/WSL host.
- Any later Docker/Postgres instance is LAB/disposable or candidate-specific until admitted by contract and restore drill.
- Phase 0 capability statuses remain authoritative for production behavior.

## Rollback point
Pre-change feature state: WSL=Disabled, VirtualMachinePlatform=Disabled.

If the feature enable fails or production health regresses, stop before Ubuntu/Docker. Record DISM state and plan disabling only the two Phase-1-enabled features. Reboot remains a separately admitted/manual boundary.
