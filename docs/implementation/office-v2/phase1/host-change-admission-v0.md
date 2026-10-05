# Office v2 Phase 1 Host Change Admission v0

Current verdict: **MAINTENANCE_BLOCKED / PREP_ALLOWED**.

## Observed host facts

- Firmware virtualization: enabled.
- VM monitor extensions: available.
- SLAT: available.
- Windows Subsystem for Linux optional feature: Enabled.
- VirtualMachinePlatform optional feature: Enabled.
- WSL userspace/runtime: not installed.
- Docker CLI/Desktop: not installed.
- HypervisorPresent: false at observation time.
- Existing Component Based Servicing pending reboot: yes.
- Existing pending file rename operations: yes (86 entries at the latest admission probe).
- Interactive console session: active; absence of unsaved user state is not remotely provable.
- Local Windows print jobs: none.
- Bambu Studio / OrcaSlicer processes: not running at observation time.
- Desktop Commander Remote: SYSTEM + Boot trigger.
- VelvetOS DCC Gateway: SYSTEM + Boot trigger.
- GrokBot watchdog: user logon trigger.
- AdobePy brokers: user logon trigger.

Evidence: `D:/Velvet/Artifacts/OfficeV2/phase1/evidence/2026-10-05/windows-host-admission.json`.

## Admission rule

The existing pending reboot is treated as an unknown combined host transition. The active interactive console session is also a separate maintenance blocker until user workload/unsaved-state risk is explicitly cleared. No new WSL userspace install, Docker install, hypervisor change or reboot is executed while this receipt remains `MAINTENANCE_BLOCKED`.

A newer receipt may change the verdict only after:
1. Project State checkpoint is sealed.
2. No active local fabrication/critical user workload is found.
3. Reboot rollback and post-boot probes are explicit.
4. Desktop Commander boot recovery is expected and independently rechecked.
5. The recovery path for logon-only GrokBot/Adobe dependencies is explicit.
6. LAB configuration contains no production credentials.
7. Host mutation is bounded to the admitted WSL/Docker sequence.

## Reboot success criteria

After an admitted reboot:
- Remote Commander boot path responds.
- DCC Gateway boot path responds.
- WSL runtime reports usable WSL2 capability.
- Production providers remain unaffected or recover to their prior safe state.
- Logon-only components are not claimed recovered until a user session actually restores them.
- Any mismatch produces a fail-closed maintenance receipt rather than another reboot loop.

## Prohibited shortcuts

Do not clear reboot registry markers manually. Do not disable boot/security controls to force WSL. Do not copy production secrets into LAB. Do not treat an installed container runtime as production authority.
