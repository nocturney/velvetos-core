# Office v2 Phase 1 — Neutral Lab & Safety Boundary

Phase 1 starts only from the sealed Phase 0 GREEN checkpoint.

## Objective
Create a reversible OfficeV2-Lab surface on the Windows RTX workstation without changing production authority.

## Ordered admission
1. Re-read virtualization, WSL and Docker state.
2. Enable WSL + VirtualMachinePlatform with no automatic restart.
3. Record post-enable state and reboot requirement.
4. After a planned reboot, install/verify WSL2 + Ubuntu LTS.
5. Define OfficeV2-Lab network, service names, ports and volumes before Docker workloads.
6. Install Docker/Compose only after WSL2 health is proven.
7. Create a shared artifact lane between Windows and WSL.
8. Add minimal OTel using Phase 0 correlation IDs.
9. Use LAB-only identity/credential stubs.
10. Prove destroy/recreate and one stateful restore before any LAB stateful service can be production-capable.

## Hard boundaries
Production secrets, business truth, production writers and canonical approvals stay outside LAB. A LAB service gains no authority by being installed first.

No architecture winner is selected in Phase 1.
