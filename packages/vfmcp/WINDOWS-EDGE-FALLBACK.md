# Windows Edge Fallback

Purpose: keep VelvetOS content/repo/render/speech execution available when `Mac-Office` is offline, without creating a second orchestrator or moving browser subscription credentials.

## Roles

Primary: `sderot-mac` (`Mac-Office`).
Fallback: `sderot-windows` (`Windows-Fallback`).
Selection rule: first healthy host from `packages/vfmcp/RENDER-HOSTS.json`.

Windows fallback may handle:

- repository work and local command execution;
- content pipeline support and artifact preparation;
- HyperFrames/FFmpeg rendering after local doctor passes;
- local speech/TTS/ASR workloads when their backend is installed and verified;
- QA helpers that do not require macOS-only browser control.

Windows fallback must NOT receive copied Chrome profiles, cookies, ChatGPT/Gemini/Perplexity subscription sessions, or Mac credential stores. It is not a browser-subscription host and `computerUse` stays false.

## One-time Windows commissioning

1. Install/connect Remote Desktop Commander on the Windows PC using the same ChatGPT account. The device must appear online in the device list.
2. Install Git, Python 3, Node 22+, FFmpeg/ffprobe, and PowerShell 7 if missing.
3. Open PowerShell and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
irm https://raw.githubusercontent.com/nocturney/velvetos-core/main/scripts/bootstrap-edge-host-windows.ps1 | iex
```

If the repository already exists, the bootstrap fast-forwards it to `origin/main`. It pins HyperFrames `0.8.34`, runs `vf_hyperframes.py doctor`, and writes host evidence to `%USERPROFILE%\.velvetos\edge-host.json`.

## Eligibility gate

The Windows host is not eligible merely because it is listed in Git. It becomes routable only when all are true:

- Remote Desktop Commander reports the device online;
- local repo is on/at current `main` or an explicitly selected task branch;
- bootstrap/doctor passes;
- required tool for the task exists locally;
- no task requires a Mac-only subscription/browser session.

Until then its registry status remains `configured_pending_device_registration`.

## Failover behavior

When `sderot-mac` is offline, route eligible Edge jobs to `sderot-windows` rather than failing the whole content pipeline. When both are online, prefer the Mac for subscription/browser-bound work and the Windows host may still be chosen for heavy local render/speech work when explicitly requested or when capacity routing is added later.

Publication authorization does not change: a render receipt proves artifact creation, not publication. Existing Visual Foundry, copy, truth and publish gates remain mandatory.
