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
- VoiceStudio speech/TTS/ASR after local doctor **and real Hebrew TTS + back-transcription QA smoke** pass;
- QA helpers that do not require macOS-only browser control.

Windows fallback must NOT receive copied Chrome profiles, cookies, ChatGPT/Gemini/Perplexity subscription sessions, or Mac credential stores. It is not a browser-subscription host and `computerUse` stays false.

## One-time Windows commissioning

1. Install/connect Remote Desktop Commander on the Windows PC using the same ChatGPT account. The physical PC must appear **online** in the device list.
2. Open PowerShell. The bootstrap provisions the required user-local toolchain where possible, so Git/Python/Node/FFmpeg do not need to be prepared manually first.
3. Run the canonical media bootstrap:

```powershell
cd $HOME\velvetos-core
git switch main
git pull --ff-only origin main
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-media-host-windows.ps1
```

The compatibility switch `-StartWorker` is accepted, but it does not create a second Cursor worker: this Windows host reuses the existing Remote Desktop Commander route.

The media bootstrap is fail-closed. It first runs `bootstrap-edge-host-windows.ps1`, which:

- provisions Git through `winget` when needed;
- installs a pinned Node 22 user-local toolchain and verifies the official Node SHA-256 before extraction;
- resolves/provisions Python 3.12 for the current user;
- provisions FFmpeg + ffprobe user-locally when missing;
- pins HyperFrames `0.8.34` with runtime update/auto-install disabled for content jobs;
- runs `hyperframes browser ensure` and `vf_hyperframes.py doctor`;
- performs a **real 1080×1920 Hebrew RTL HyperFrames smoke render** using `data-no-timeline`;
- runs the normal VelvetOS render bridge so ffprobe validation and SHA-256 receipt generation are exercised;
- writes render evidence to `%USERPROFILE%\.velvetos\edge-host.json`.

It then runs `bootstrap-speech-host-windows.ps1`, which:

- installs the pinned current-user VoiceStudio `0.5.2` MSI when needed;
- launches VoiceStudio and requires its local speech discovery endpoint on `127.0.0.1:3900`;
- runs `vf_speech.py doctor`;
- performs a real Hebrew TTS smoke using the commercial-safe preferred `moss-tts-nano` path plus Windows ASR and back-transcription QA;
- requires similarity >= `0.90` and writes speech/QA receipts;
- writes `%USERPROFILE%\.velvetos\speech-host.json` and annotates the common Edge state.

On Windows with AMD graphics, VoiceStudio is intentionally CPU-backed: upstream VoiceStudio supports ROCm only on Linux. This affects speed, not the authority or QA contract. HyperFrames remains available as the deterministic render layer.

VoiceStudio has an explicit first-run setup gate. If the API is not ready after installation, open VoiceStudio once and press **Start installation**. Then rerun the same media-bootstrap command. The script does not bypass that user confirmation.

If the required `moss-tts-nano` / Windows ASR engine is not ready, the bootstrap fails closed and names the engines that must be enabled in VoiceStudio Model Catalogue. The host is not promoted on a partial speech setup.

If the repository already exists, the render bootstrap fast-forwards it to `origin/main`. Neither bootstrap copies browser subscription credentials or opens an inbound port/tunnel.

## Eligibility gate

The Windows host is not eligible merely because it is listed in Git or because the bootstrap file exists. It becomes routable for a capability only when all required evidence for that capability is true:

- Remote Desktop Commander reports the physical Windows device online;
- local repo is on current `main` or an explicitly selected task branch;
- render doctor + real HyperFrames smoke receipt pass before render work;
- speech doctor + real Hebrew TTS/STT back-transcription QA receipts pass before speech work;
- required tool for the task exists locally;
- no task requires a Mac-only subscription/browser session.

Until those facts are verified, its registry status remains commissioning/pending. Render evidence never silently proves speech readiness, and speech evidence never silently proves render readiness.

## Failover behavior

When `sderot-mac` is offline, route eligible Edge jobs to `sderot-windows` **only after** the requested capability is verified. When both are online, prefer the Mac for subscription/browser-bound work; Windows remains available for deterministic repo/content/render/speech work.

Failover is sticky per job so Mac and Windows do not execute the same job concurrently. Host failover is allowed for machine/route/doctor failures; it must not bypass a Content Contract, policy, rights, truth, consent or QA failure. Switching machines never lowers Brand/Reality/Artifact/Content or speech-QA thresholds.

Publication authorization does not change: render and speech receipts prove artifact creation/verification, not publication. Existing Visual Foundry, copy, truth and publish gates remain mandatory.

## Current runtime truth

- `sderot-mac`: historical HyperFrames smoke is verified; it may be physically offline at a given moment without losing that evidence. Speech still requires its own runtime evidence.
- `sderot-windows`: configured as the canonical deterministic fallback. It is not failover-eligible until Remote Desktop Commander sees the physical PC online and the local media bootstrap produces the required render and speech evidence.
