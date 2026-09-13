# Connect the Sderot render hosts

This extends the existing canonical Edge render route. It does **not** add a second runtime, tunnel, queue or inbound service.

Canonical host registry: `packages/vfmcp/RENDER-HOSTS.json`  
Preferred host: `sderot-mac` / `Mac-Office`  
Fallback host: `sderot-windows` / `Windows-Office`  
Host selection: `first-healthy-verified-host`  
Render backend: `packages/vfom/HYPERFRAMES-BACKEND.json`

## Automatic failover contract

Render host order is:

```text
sderot-mac -> sderot-windows
```

Failover is automatic only for host-level failures such as host offline, route unreachable or host doctor failure. The fallback host must already be `host_smoke_verified` or `live_verified`. A merely configured machine is not eligible.

Do **not** fail over around a Content Contract, policy, rights or QA failure. A host change only moves execution; it never weakens truth, copy, brand, QA, receipt or publish gates.

## Mac-Office rollout

Run in Terminal on the dedicated Mac:

```bash
cd ~/velvetos-core
git pull --ff-only
bash scripts/bootstrap-hyperframes-host-macos.sh --start-worker
```

The Mac bootstrap is fail-closed and does not require administrator privileges. It verifies macOS, provides a user-local Node >=22 toolchain when needed, provides user-local FFmpeg/ffprobe when needed, installs the pinned public HyperFrames CLI `0.8.34`, ensures the HyperFrames browser runtime, runs `vf_hyperframes.py doctor`, performs a real portrait MP4 smoke render with deterministic Hebrew RTL text, verifies the render receipt, writes local host evidence to `~/.velvetos/render-host.json`, then reuses the existing Cursor worker route.

If `sderot-mac` is already running, the script does not start a duplicate worker.

## Windows-Office fallback rollout

Run in **PowerShell** on the Windows PC from its clone of this repository:

```powershell
cd "$env:USERPROFILE\velvetos-core"
git pull --ff-only
powershell -ExecutionPolicy Bypass -File scripts\bootstrap-hyperframes-host-windows.ps1 -StartWorker
```

The Windows bootstrap is also user-local and fail-closed. It:

- verifies native Windows x64;
- provisions Node >=22 under the user profile if needed and verifies the official Node SHA-256;
- provisions FFmpeg + ffprobe user-locally when missing;
- installs exactly HyperFrames `0.8.34` and ensures its browser runtime;
- resolves/provisions Python 3 for `scripts/vf_hyperframes.py`;
- runs the same `doctor`, portrait Hebrew smoke render and receipt verification;
- writes `%USERPROFILE%\.velvetos\render-host.json`;
- installs the official native-Windows Cursor CLI if needed;
- verifies Cursor login and starts `agent worker --name "sderot-windows" start` when `-StartWorker` is supplied.

No administrator rights, Homebrew, ngrok or inbound port are part of this route.

### Windows capability boundary

`Windows-Office` is a **render/terminal/content-production fallback**, not the subscription-browser host. Native Windows may run the normal Cursor worker, repository tools, HyperFrames, FFmpeg and deterministic content work. It must **not** be started with Cursor computer-use or desktop-sharing flags. Browser-driving subscription workflows remain on the Mac.

This preserves the existing rule in `HOST.md`: Mac-Office remains the browser/subscription host even though Windows can now back up deterministic Edge execution.

## What success looks like

On either host, before the worker starts/continues, bootstrap must print equivalents of:

- `OK hyperframes host prerequisites ...` or the successful `doctor` result;
- `OK render verified receipt=...`;
- `OK HyperFrames ... host smoke verified`.

Local evidence must exist at:

```text
macOS:   ~/.velvetos/render-host.json
Windows: %USERPROFILE%\.velvetos\render-host.json
```

That local file is host evidence only. It contains no secrets and is intentionally not a second source of truth. Git remains the configuration authority; the render receipt proves only that a local file was rendered, not that anything was published.

## Route

```text
HQ / content job
  -> choose first healthy verified host
     1. Cursor Edge worker: sderot-mac
     2. Cursor Edge worker: sderot-windows
  -> velvetos-core
  -> scripts/vf_hyperframes.py
  -> local HyperFrames + FFmpeg
  -> rendered derivative + receipt
  -> existing Visual Foundry QA
  -> existing publish path only after publish gates
```

**No inbound port** is required. Both self-hosted workers use their existing outbound Cursor connection.

## Commissioning status

### Mac

On 2026-09-12 the real `Mac-Office` completed the local HyperFrames smoke render and receipt verification, wrote `~/.velvetos/render-host.json`, and attached the canonical `sderot-mac` Cursor worker. Its registry status is `host_smoke_verified`.

### Windows

Core now contains the Windows bootstrap, host registration and automatic failover contract, but the physical Windows host has not yet completed its smoke/receipt in this commissioning pass. Its registry status therefore remains `configured_host_smoke_pending` and it is **not yet eligible for automatic failover**.

Promotion to `host_smoke_verified` requires all of:

1. run `bootstrap-hyperframes-host-windows.ps1` successfully on the real Windows PC;
2. verify the portrait HyperFrames smoke MP4 + ffprobe/SHA-256 receipt;
3. verify `agent status` is logged in and `sderot-windows` worker connects;
4. record the verified evidence in `RENDER-HOSTS.json`.

This is separate from production `LIVE / VERIFIED` for the full HyperFrames backend. Production still requires a real approved Media Vault asset through existing Brand/Reality/Artifact/Content QA and intentional HyperFrames failure -> FFmpeg fallback verification.

## HyperFrames smoke compatibility

The static smoke fixture uses `data-no-timeline`; otherwise HyperFrames waits for a missing `window.__timelines` registration. Hebrew RTL is applied to the Hebrew text layer, not to `<html dir="rtl">`, because a non-LTR direction on the root html element can render a blank/black video in this HyperFrames path.

## Failure handling

- Preferred host offline/unreachable: try `sderot-windows` **only if** its status is verified.
- Node/FFmpeg missing: the platform bootstrap provisions the user-local toolchain.
- HyperFrames version mismatch: bootstrap installs the pinned version and verifies it; any remaining mismatch fails.
- Cursor `agent` missing: bootstrap installs the official CLI on Windows; on Mac follow `HOST.md`.
- Cursor login missing: run `agent login` once on that physical host, then rerun bootstrap.
- HyperFrames render fails on one otherwise healthy host: retry once per the existing bounded policy; use the other verified host only when the failure is host-specific.
- HyperFrames engine failure independent of host: use `ffmpeg-svg-caption-composition` only when it can preserve the same Content Contract and QA requirements.
