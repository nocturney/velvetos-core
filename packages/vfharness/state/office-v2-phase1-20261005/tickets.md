# Office v2 Phase 1 — execution tickets

## P1-A · Host prerequisites
Outcome: WSL + VirtualMachinePlatform staged without automatic reboot.
State: DONE.
Evidence: D:/Velvet/Artifacts/OfficeV2/phase1/wsl-feature-stage-20261005.json.
Rollback: pre-change features were both Disabled.

## P1-B · Reboot boundary + WSL2/Ubuntu admission
Outcome: planned reboot, then prove WSL runtime health before distro activation; install Ubuntu LTS only after post-reboot checks.
State: BLOCKED_ON_PLANNED_REBOOT.
Verify:
- Windows returns with production services healthy.
- WSL feature/runtime reports healthy.
- default WSL version can be set to 2.
- Ubuntu LTS installs into the OfficeV2-Lab context and launches without production credentials.

## P1-C · Docker/Compose admission
Outcome: Docker/Compose installed only after P1-B is green.
State: NOT_STARTED.
Verify:
- Docker engine healthy.
- compose available.
- dedicated compose project/network naming enforced.
- default bind is loopback.
- no production mounts/secrets.
- teardown/recreate scripts work.

## P1-D · Artifact lane + OTel
Outcome: shared Windows/WSL artifact lane and minimal OTel collector using Phase 0 correlation IDs.
State: STAGED_CONFIG_ONLY.
Current lane:
- Windows: D:/Velvet/Lab/OfficeV2/artifacts
- WSL: /mnt/d/Velvet/Lab/OfficeV2/artifacts
OTel reserved ports: 14317/14318.

## P1-E · Stateful restore drill
Outcome: one disposable/candidate-specific stateful service is backed up, destroyed, recreated and restored.
State: NOT_STARTED.
Rule: stateful service is not production-capable until this drill passes.

## P1-F · Node-A capability/health manifest
Outcome: windows-primary publishes Node Contract v0 after WSL/Docker LAB is active; Mac is compared against the same contract.
State: PRE_REBOOT_BASELINE_ONLY.

## Phase 1 hard boundaries
- No production credentials in LAB.
- No production writer/authority moves into LAB.
- No automatic reboot.
- No universal Postgres default.
- No durable/model/MCP-A2A/NATS/feature-flag winner selection.
- No manufacturing SoT cutover.
- No untrusted/generated code directly on Windows or WSL host.
