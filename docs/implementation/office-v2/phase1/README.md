# VelvetOS Office v2 — Phase 1 Neutral Lab & Safety Boundary

Phase 0 is closed on canonical main at `d755c4cb62e2fde16f6c5804db180d48170238ba`.
Phase 1 neutral-LAB preparation is merged. Formal closure work starts from `origin/main@6c3865acee79fb11dbaeeace0a5bc73f9624d187`.

This directory contains versioned Phase 1 definitions and bounded receipt summaries only. Raw runtime evidence, backups, artifacts and live node observations remain outside Git.

## Current status

`RUNTIME_PROVEN / FORMAL_CLOSURE_PENDING`

The five START HERE technical gate criteria have real runtime proof. The canonical 118-sensor repository regression is green and the temporary WSL user-context bridge has been deleted. Formal closure now requires sealed Project State, PR merge and exact-main CI.

## Realized LAB runtime

- Windows post-reboot: CBS and Windows Update reboot flags are clear. Residual delete-only/temp file-rename entries remain visible as warnings and are not manually cleared.
- WSL: 3.0.1.0; kernel 6.18.40.1-1.
- Distro: `OfficeV2-Lab`, Ubuntu 26.04.1 LTS, WSL2, default user `officev2` uid 1000.
- Docker Engine: 29.8.2; Docker Compose: v5.6.0; systemd and Docker are active.
- Network: `officev2_lab`.
- OTel: digest-pinned collector; loopback-only ports 14317/14318/14319.
- Shared artifact lane: `D:/Velvet/OfficeV2Lab/artifacts` ↔ `/var/officev2/artifacts`.
- Full `/mnt/c` and `/mnt/d` mounts are absent.
- Artifact mount requires `rw,nosuid,nodev,noexec,nosymfollow` plus metadata, uid=1000, gid=1000 and umask=077.

## Safety boundary

- LAB has no production authority.
- LAB receives no production credentials by default.
- Only LAB_ONLY_SECRET and PUBLIC_IDENTIFIER credential classes are admitted.
- Untrusted/generated code does not run directly on the Windows/WSL host.
- PostgreSQL was used only as a disposable restore-drill candidate; it is not a universal Office v2 database decision.
- No production writer or business source of truth moved in Phase 1.

## Gate evidence

- Destroy/recreate without production impact: PASS.
- Stateful LAB restore: PASS.
- Production-secret exclusion: PASS.
- Real correlated end-to-end trace: PASS.
- Fresh NODE-A capability/health manifest: PASS.

Canonical raw evidence stays under `D:/Velvet/Artifacts/OfficeV2/phase1/evidence/2026-10-06/` and `D:/Velvet/OfficeV2Lab/`. Versioned files cite those paths but do not copy credentials, secrets or raw production payloads into Git.

Phase 2 remains blocked until formal Phase 1 closure is GREEN on merged current main.
