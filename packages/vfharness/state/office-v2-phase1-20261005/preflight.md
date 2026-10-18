# Office v2 Phase 1 - execution preflight

Canonical project preflight: PASS, domain `system_engineering`, mode `FULL`.

Accepted main: `d755c4cb62e2fde16f6c5804db180d48170238ba`.

Worktree: `D:/Velvet/Worktrees/office-v2-phase1-neutral-lab-20261005`.
Branch: `office-v2/phase1-neutral-lab-20261005`.
Existing main working tree: prohibited for Phase 1 changes.

## Live host ruling
`MAINTENANCE_BLOCKED_PREP_ALLOWED`.

Reason: WSL/VMP features are enabled but WSL userspace and Docker are absent; the host already has CBS + file-rename reboot debt, HypervisorPresent=false, and GrokBot/Adobe brokers require user logon. Reboot/install is therefore not operationally transparent.

Allowed now:
- versioned LAB definitions;
- off-repo LAB directories under `D:/Velvet/OfficeV2Lab`;
- read-only host probes;
- node manifests;
- dry-run teardown/recreate;
- backup/restore definitions;
- LAB-only identity/credential stubs.

Blocked now:
- reboot;
- `wsl --install`;
- Docker install;
- production credentials in LAB;
- production route/writer changes;
- candidate winner promotion.

## Cross-ticket checks
- P1-A + P1-B: port/root/credential boundaries are inputs to LAB config.
- P1-B + P1-D: teardown owns only LAB roots/services.
- P1-A + P1-E: host mutation requires a newer admission receipt that explicitly ALLOWs it.
- P1-C + P1-F: Node manifest must validate against the same contract on Windows/Mac.
- P1-D + P1-F: restore proof must be stateful and off-production.
- P1-E + P1-F: reboot/recovery evidence must prove boot path, not infer it.

## Pre-edit card
- Outcome: executable neutral LAB prep, not host mutation.
- Source of truth: START HERE + Phase 0 accepted main + current host admission.
- Smallest change: contracts/configs/dry-run tools only.
- Verification: targeted RED -> GREEN + self-tests + full repository sensors.
- Out of scope: Phase 2 candidate bake-offs and any production cutover.
