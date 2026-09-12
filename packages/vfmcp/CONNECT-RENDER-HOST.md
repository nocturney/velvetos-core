# Connect the Sderot render host

This extends the existing canonical `Mac-Office` / Cursor worker route. It does **not** add a second runtime, tunnel, queue or inbound service.

Canonical host registry: `packages/vfmcp/RENDER-HOSTS.json`  
Canonical worker: `sderot-mac`  
Render backend: `packages/vfom/HYPERFRAMES-BACKEND.json`

## One-command rollout on Mac-Office

Run in Terminal on the dedicated Mac:

```bash
cd ~/velvetos-core
git pull --ff-only
bash scripts/bootstrap-hyperframes-host-macos.sh --start-worker
```

The bootstrap is fail-closed and does not require administrator privileges. It verifies macOS, provides a user-local Node >=22 toolchain when needed, provides user-local FFmpeg/ffprobe when needed, installs the pinned public HyperFrames CLI `0.8.34` under the user profile, ensures the HyperFrames browser runtime, runs `vf_hyperframes.py doctor`, performs a real portrait MP4 smoke render with deterministic Hebrew RTL text, verifies the render receipt, writes local host evidence to `~/.velvetos/render-host.json`, then reuses the existing Cursor worker route.

If `sderot-mac` is already running, the script does not start a duplicate worker.

## What success looks like

Before the worker starts/continues, the bootstrap must print:

- `OK hyperframes host prerequisites ...`
- `OK render verified receipt=...`
- `OK HyperFrames host smoke verified`

Local evidence must exist at:

```text
~/.velvetos/render-host.json
```

That local file is host evidence only. It contains no secrets and is intentionally not a second source of truth. Git remains the configuration authority; the render receipt proves only that a local file was rendered, not that anything was published.

## Route

```text
HQ / content job
  -> existing Cursor Edge worker: sderot-mac
  -> ~/velvetos-core
  -> scripts/vf_hyperframes.py
  -> local HyperFrames + FFmpeg
  -> rendered derivative + receipt
  -> existing Visual Foundry QA
  -> existing publish path only after publish gates
```

No inbound port, ngrok or extra HTTP daemon is required for this route.

## Commissioning status

On 2026-09-12 the real `Mac-Office` completed the local HyperFrames smoke render and receipt verification, wrote `~/.velvetos/render-host.json`, and attached the canonical `sderot-mac` Cursor worker. The registry may therefore use `host_smoke_verified`.

This is **not yet the same as production `LIVE / VERIFIED` for the full HyperFrames backend**. Issue #180 remains open until both production promotion gates pass:

1. render a real/approved Media Vault asset with deterministic Hebrew overlay and pass the existing Brand/Reality/Artifact/Content QA;
2. intentionally fail HyperFrames once and verify fallback to `ffmpeg-svg-caption-composition` without lowering QA.

Only after those gates may the overall backend / README be promoted to `LIVE / VERIFIED` and issue #180 be closed.

## HyperFrames smoke compatibility

The static smoke fixture uses `data-no-timeline`; otherwise HyperFrames waits for a missing `window.__timelines` registration. Hebrew RTL is applied to the Hebrew text layer, not to `<html dir="rtl">`, because a non-LTR direction on the root html element can render a blank/black video in this HyperFrames path.

## Failure handling

- Node/FFmpeg missing: bootstrap installs the required toolchain under the user's profile without sudo/Homebrew.
- HyperFrames version mismatch: installs the pinned version and verifies it; any remaining mismatch fails.
- Cursor `agent` missing/not logged in: render smoke can finish, but host routing is not considered connected; follow `packages/vfmcp/HOST.md` and rerun.
- HyperFrames render fails: do not promote the backend; use the existing `ffmpeg-svg-caption-composition` fallback only when the artifact can preserve the content contract and QA requirements.
