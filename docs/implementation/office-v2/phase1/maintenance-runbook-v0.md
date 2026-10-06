# Office v2 Phase 1 Controlled WSL2 / Docker Maintenance Runbook v0

Status: **EXECUTED / RUNTIME VALIDATED / FORMAL CLOSURE PENDING**.

This runbook changes only the Phase 1 LAB substrate. It never changes a production writer, production authority, business source of truth, or production credential boundary.

## Runtime target

- Windows node: NODE-A / RTX workstation.
- WSL architecture: WSL2.
- Ubuntu source: Ubuntu 26.04 LTS.
- Dedicated WSL instance name: `OfficeV2-Lab`.
- Container runtime: Docker Engine + Compose plugin inside `OfficeV2-Lab`.
- Docker Desktop: not required.
- Shared artifact lane: `D:/Velvet/OfficeV2Lab/artifacts` <-> `/var/officev2/artifacts`; full `/mnt/c` and `/mnt/d` automounts are disabled.
- LAB host ports remain loopback-only unless a later gate explicitly changes that.

The exact commands and package versions are revalidated against current Microsoft/Ubuntu/Docker documentation immediately before execution.

## Admission prerequisites

Do not execute any maintenance step unless a fresh host-admission receipt says ALLOW and all of the following are true:

1. Project State is sealed immediately before maintenance.
2. Interactive user workload is drained and unsaved-state risk is explicitly cleared.
3. No active local fabrication/print job depends on NODE-A.
4. Production providers have current readback/health evidence.
5. Desktop Commander SYSTEM/boot recovery is known.
6. Logon-scoped GrokBot/Adobe recovery is explicit.
7. LAB contains no production credentials.
8. Rollback/post-boot probes are written before the reboot.

## Stage A - separate the pre-existing reboot debt

The current host already has CBS + file-rename reboot debt. Do **not** combine that unknown transition with a new WSL/Docker install.

After admission:

1. Seal a maintenance checkpoint and receipt.
2. Record current boot/logon service health.
3. Reboot NODE-A once **without installing new Phase 1 runtime packages first**.
4. Re-establish Remote Commander connectivity.
5. Re-run production smoke and node health.
6. Re-run pending-reboot probes.
7. Stop if production behavior regressed, the reboot debt remains unexplained, or recovery is incomplete.

This stage exists to prevent attribution ambiguity.

## Stage B - install/activate WSL runtime only

Only after Stage A is green:

1. Revalidate `wsl --help` and official install syntax.
2. Install/update the WSL runtime without adding an unrelated distro first when the host supports that path.
3. Reboot only if the WSL installer explicitly requires it.
4. Verify `wsl --status`.
5. Verify WSL 2 is the default/available architecture.
6. Record the exact WSL version and post-install reboot state.

No Docker packages are installed until WSL itself is healthy.

## Stage C - install the dedicated Ubuntu LTS instance

1. Revalidate that `Ubuntu-26.04` is available.
2. Install it under the dedicated instance name `OfficeV2-Lab`, preferably with no automatic first launch while unattended.
3. Verify with `wsl -l -v` that `OfficeV2-Lab` is version 2.
4. Create only LAB-local identity/configuration.
5. Do not import production tokens, SSH material, provider secrets, or production environment files.

If the distro install requires interactive account initialization, the run stops at that bounded human step rather than weakening the credential boundary.

## Stage D - Docker Engine + Compose inside the LAB distro

1. Use Docker's official Ubuntu apt repository.
2. Use reviewed package versions available for Ubuntu 26.04 LTS; record exact versions in the execution receipt.
3. Install Docker Engine, CLI, containerd, Buildx and Compose plugin.
4. Do not use the convenience installer script for the admitted production workstation path.
5. Keep Docker scoped to the `OfficeV2-Lab` WSL instance.
6. Re-run `vf_office_v2_lab_doctor.py`; it must detect Docker through `wsl -d OfficeV2-Lab -- docker ...`.
7. The doctor must reach `READY_FOR_LAB_RUNTIME` before lifecycle execution is allowed.

## Stage E - first neutral LAB runtime proof

1. Admit a reviewed immutable OTel Collector image reference.
2. Put LAB runtime environment only in LAB-local state, not Git.
3. Run the OTel service through `vf_office_v2_lab_lifecycle.py`.
4. Verify ports 14317/14318/14319 bind only to loopback.
5. Send one trace carrying the Phase 0 correlation IDs.
6. Capture logs/evidence.
7. Destroy and recreate the LAB service with no production impact.

## Stage F - stateful restore drill

The Phase 1 gate remains open until one admitted stateful LAB service proves:

- backup artifact + digest;
- destroy of LAB-only state;
- service recreation from versioned definition;
- restore;
- health/readback;
- known fixture/correlation identity;
- measured restore time;
- no production store touched.

Postgres is allowed only when a candidate/fixture actually requires it; its presence never makes it a universal Office v2 database.

## Fail-closed rules

- Any unknown external-effect outcome is reconciled before retry.
- A LAB runtime error cannot promote a fallback challenger to production.
- A candidate receiving production credentials is a security incident: isolate, revoke/rotate and audit.
- A failed post-boot production smoke stops the migration before additional installs.
- A failed restore drill keeps the stateful candidate LAB-only.
- Do not clear Windows reboot markers manually.

## Teardown boundary

Normal LAB teardown removes only:
- `officev2_lab` Docker resources;
- LAB containers/volumes;
- `D:/Velvet/OfficeV2Lab` data explicitly admitted for deletion.

Unregistering `OfficeV2-Lab` is a separate destructive maintenance action and is never part of ordinary `down`/recreate.

## Reference validation

Before execution, revalidate:
- Microsoft WSL install/basic-command documentation;
- Ubuntu on WSL install guidance for Ubuntu 26.04 LTS;
- Docker Engine Ubuntu installation/support documentation.

## Realized execution summary — 2026-10-06

- Stage A separated the pre-existing reboot transition; CBS/Windows Update reboot flags cleared after the controlled reboot.
- Stage B installed the Microsoft-signed WSL 3.0.1.0 runtime.
- Stage C created `OfficeV2-Lab` as WSL2 with Ubuntu 26.04.1 LTS.
- Stage D installed Docker Engine 29.8.2 and Compose v5.6.0 from Docker's official Ubuntu repository.
- Filesystem isolation was hardened after the initial automount exposed full C:/D:. The validated state has no full drive mounts and exposes only the artifact lane at `/var/officev2/artifacts`.
- Stage E ran the digest-pinned OTel collector on loopback only and passed a real correlated OTLP HTTP trace.
- Stage F passed destroy/recreate plus a disposable stateful PostgreSQL restore drill.
- No production credentials were introduced into LAB and no production writer changed.
- LocalSystem/WSL incompatibility was handled with a temporary on-demand interactive-token task; the task was deleted after final runtime verification and is not an architecture dependency.
