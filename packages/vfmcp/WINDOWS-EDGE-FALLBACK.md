# Windows Edge Fallback

Purpose: keep VelvetOS content/repo/render/speech execution available when `Mac-Office` is offline, without creating a second orchestrator or moving browser subscription credentials.

## Roles

Primary: `sderot-mac` (`Mac-Office`).  
Fallback: `sderot-windows` (`Windows-Fallback`).  
Selection rule: first **healthy and verified** host from `packages/vfmcp/RENDER-HOSTS.json`.

Windows fallback may handle:

- repository work and local command execution;
- content pipeline support and artifact preparation;
- HyperFrames/FFmpeg rendering after local doctor **and render smoke** pass;
- local speech/TTS/ASR workloads when their backend is installed and verified;
- QA helpers that do not require macOS-only browser control.

Windows fallback must NOT receive copied Chrome profiles, cookies, ChatGPT/Gemini/Perplexity subscription sessions, or Mac credential stores. It is not a browser-subscription host and `computerUse` stays false.

## One-time Windows commissioning

1. Install/connect Remote Desktop Commander on the Windows PC using the same ChatGPT account. The physical PC must appear **online** in the device list.
2. Open PowerShell. The bootstrap now provisions the required user-local toolchain where possible, so Git/Python/Node/FFmpeg do not need to be prepared manually first.
3. Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
irm https://raw.githubusercontent.com/nocturney/velvetos-core/main/scripts/bootstrap-edge-host-windows.ps1 | iex
```

The bootstrap is fail-closed. It:

- provisions Git through `winget` when needed;
- installs a pinned Node 22 user-local toolchain and verifies the official Node SHA-256 before extraction;
- resolves/provisions Python 3.12 for the current user;
- provisions FFmpeg + ffprobe user-locally when missing;
- pins HyperFrames `0.8.34` with runtime update/auto-install disabled for content jobs;
- runs `hyperframes browser ensure` and `vf_hyperframes.py doctor`;
- performs a **real 1080×1920 Hebrew RTL HyperFrames smoke render** using `data-no-timeline`;
- runs the normal VelvetOS render bridge so ffprobe validation and SHA-256 receipt generation are exercised;
- writes host evidence to `%USERPROFILE%\.velvetos\edge-host.json`, including `doctor=pass`, `renderSmoke=pass`, receipt path/SHA and repo head.

If the repository already exists, the bootstrap fast-forwards it to `origin/main`. It never copies browser subscription credentials and does not open an inbound port or tunnel.

## Eligibility gate

The Windows host is not eligible merely because it is listed in Git or because the bootstrap file exists. It becomes routable for render fallback only when all are true:

- Remote Desktop Commander reports the physical Windows device online;
- local repo is on current `main` or an explicitly selected task branch;
- bootstrap/doctor passes;
- the real HyperFrames smoke render passes and a valid render receipt exists;
- required tool for the task exists locally;
- no task requires a Mac-only subscription/browser session.

Until those facts are verified, its registry status remains `configured_pending_device_registration`. After the device is online and its local evidence is inspected, the registry may be promoted to `host_smoke_verified`.

## Failover behavior

When `sderot-mac` is offline, route eligible Edge jobs to `sderot-windows` **only after** Windows is `host_smoke_verified` or `live_verified`. When both are online, prefer the Mac for subscription/browser-bound work; the Windows host remains available for deterministic repo/content/render/speech work.

Host failover is allowed for machine/route failures such as offline, unreachable, failed doctor, or missing host smoke. It must not be used to bypass a Content Contract, policy, rights, truth or QA failure. Switching machines never lowers Brand/Reality/Artifact/Content thresholds.

Publication authorization does not change: a render receipt proves artifact creation, not publication. Existing Visual Foundry, copy, truth and publish gates remain mandatory.

## Current runtime truth

- `sderot-mac`: previously `host_smoke_verified`; it may be physically offline at a given moment without losing its historical evidence.
- `sderot-windows`: **configured, not yet physically verified in this commissioning step**. It is not failover-eligible until Remote Desktop Commander sees the device online and the strengthened bootstrap produces its real smoke receipt.
