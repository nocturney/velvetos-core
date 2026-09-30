# VelvetOS DCC + Adobe Integration — Final Handoff

Date: 2026-09-30

Machine: Chris — Intel Core i9-14900K + NVIDIA GeForce RTX 4080 SUPER

Remote Commander device ID: `516b9b39-92b7-4a73-8d4b-901cc1a70a98`

## Read this before changing anything

This integration is complete for the current scope. Do not reinstall accepted Tier A adapters, do not weaken global signature/integrity policy, do not modify Adobe host binaries, and do not replace the accepted launch paths with direct executable launches.

All GUI DCC/Adobe hosts must continue to launch through the normal vendor/Start Menu shortcut via Explorer. Fusion and Cinema 4D remain out of scope. Substance 3D Sampler, Modeler and Stager still have no accepted official adapter; do not invent one.

Never commit, print or expose AdobePy tokens.

## Final result

Overall status: **PASS_WITH_DOCUMENTED_UPSTREAM_LIMITATION**.

| Component | Version | Final state |
| --- | --- | --- |
| AutoCAD / dwg-mcp | 2.0.1 | PASS |
| Maya / dcc-mcp-maya | 0.9.31 | PASS |
| 3ds Max / dcc-mcp-3dsmax | 0.2.14 | PASS |
| Inventor / ipt-mcp | 0.1.0 | PASS |
| Blender / dcc-mcp-blender | 0.2.12 | PASS |
| ZBrush / dcc-mcp-zbrush | 0.2.26 | PASS |
| Substance Painter | 0.6.0 | PASS |
| Substance Designer | 0.8.1 | PASS |
| Illustrator | 0.3.1 | PASS |
| After Effects | 0.7.0 | FUNCTIONAL PASS — exact CEP runtime identity blocked upstream |
| Photoshop first-party bridge | 0.1.1 | PRODUCTION PASS |
| Premiere first-party bridge | 0.1.3 | PRODUCTION PASS |

Canonical final matrix:
- Local: `D:\Velvet\Logs\DCC-MCP\dcc-adobe-final-regression-matrix-2026-09-30.json`
- Repo copy: `docs/evidence/dcc-adobe-final-regression-2026-09-30.json`
- SHA256: `8061B1B5813C6E6AE6ED48AE489A24D70AA8E31FE2FEE57607F625157FDB1544`

## Runtime architecture

- Shared DCC gateway: `127.0.0.1:9765`
- Adobe UXP Developer Tool service: `127.0.0.1:14001`
- Illustrator AdobePy broker: `127.0.0.1:47391`
- After Effects / Premiere broker: `127.0.0.1:47392`
- Photoshop broker: `127.0.0.1:47393`
- ZBrush sidecar: `127.0.0.1:13481`

Live desktop autostart:
- `D:\Velvet\Runtime\Autostart\Start-VelvetDccDesktopHosts.ps1`
- SHA256 at acceptance: `4941CBA86A6A1F840C1EAEB8BAEA0BD3AA5BCC8267E0CEA4978A0C9CE35DF55E`
- `-ValidateOnly` = PASS, 16 enabled / 1 disabled.

## Adobe production startup

### Photoshop

Production plugin is installed through Adobe UPIA:

`C:\Program Files\Common Files\Adobe\UXP\Plugins\External\com.velvetos.photoshop.bridge_0.1.1`

No Photoshop watcher is required. The temporary watcher was retired and archived. Acceptance included typed read-only RPC, a controlled temporary-document create/close cycle, and a clean normal-shortcut restart with the watcher stopped.

Primary evidence:
- `D:\Velvet\Logs\AdobeBridge\photoshop-first-party-0.1.1-acceptance-no-watcher-2026-09-30.json`
- SHA256 `B622C35E4EA461A0902347F7D1339C106BA98EF9299E983780EF0C854DE0B4E4`
- Restart evidence SHA256 `2CF40809FD1C2CC6EEB86527667450DB7D45E12037228E407871C05A3F719FFC`

### Premiere Pro

Production plugin is installed through Adobe UPIA:

`C:\Program Files\Common Files\Adobe\UXP\Plugins\External\com.velvetos.premiere.bridge_0.1.3`

Premiere 26.3.2 uses the installed panel route. Do not restore the old DevTools workspace override or `hostUIContext.hideFromMenu` workaround.

`Debug Database.txt` was cleaned so:
- `dvauxphost.UseDebugUXPDir = false`
- the stale DebugUXPDir value is no longer used.

Primary evidence:
- Acceptance SHA256 `E9FC96B0A1A5759CF31A7146FF92218E59ED3AA8B2E136AD669731264EBEA10B`
- Restart persistence SHA256 `B5CA335DD08A1F5469907D394EA73CA21D64ED9C08F3D28D8685185FDDABE9D8`
- Post-debug-cleanup restart SHA256 `2D735471B68FAC6D78A8460216C6DEC5ED4DA44E0F049D280C8AC99956A4B096`

### Illustrator

Illustrator requires a fresh AdobePy bootstrap transaction before host startup. Shortcut-only startup is not sufficient for the accepted AdobePy CEP identity contract.

Runtime bootstrap:
- `D:\Velvet\Runtime\Autostart\Bootstrap-VelvetIllustrator.py`
- SHA256 `B9F71AE9E363354F98C1F571929D0F9EB60E023306EF19624F10DFAE3708F5A8`

The live autostart starts this bounded Python transaction, waits two seconds, then uses the existing official Illustrator shortcut through Explorer. The bootstrap:
- hashes the installed host and CEP payload;
- requests a fresh nonce + host identity from broker 47391;
- reads the token only from the local token file;
- exits after readiness/timeout;
- never launches Illustrator.exe itself;
- never remains as a watcher or daemon.

Final autostart persistence evidence:
`D:\Velvet\Logs\AdobeBridge\illustrator-0.3.1-final-autostart-persistence-2026-09-30.json`

SHA256:
`C8DA428DDFFE739C87F473A120D2CC7C8054A0394ACD3C4D9A7423AB10DCF7D2`

Final result: broker session 1, typed read-only RPC 30.8.1, canonical verify `directly_usable=true`, bootstrap stderr 0 bytes.

### After Effects

After Effects is functionally healthy:
- normal shortcut launch;
- typed RPC works;
- version `26.3x87`;
- active project read succeeded.

Exact AdobePy CEP runtime identity remains fail-closed upstream. This is not bypassed locally.

Final status: `FUNCTIONAL_PASS_IDENTITY_BLOCKED_UPSTREAM`

Evidence:
`D:\Velvet\Logs\AdobeBridge\aftereffects-0.7.0-final-functional-regression-2026-09-30.json`

SHA256:
`6798269181DC90AB2F23278E21C7C17C4F068E794F140167C206151CB8C91FEE`

## Source control

Repository:
`https://github.com/nocturney/velvetos-core.git`

Branch:
`chore/dcc-adobe-compat-overlays-20260929`

Runtime/source head verified by the final matrix:
`665e5d99 chore: persist Illustrator bootstrap transaction`

Earlier integration commits:
- `f62610c9 chore: harden Adobe bridge persistence`
- `e6e1e2d3 chore: reconcile DCC Adobe compatibility sources`

The branch contains:
- version-pinned Blender / Illustrator / After Effects compatibility overlays;
- Substance Designer loader provenance;
- secret-free Photoshop 0.1.1 and Premiere 0.1.3 first-party bridge sources;
- Illustrator bounded bootstrap source and provenance;
- `scripts/validate-dcc-adobe-compat.py`.

## Blender 5.2 final clarification

Blender 5.2.2 LTS is **PASS**. The apparent regression observed during the final pass was caused by a stale fixed-port assumption, not a broken startup or adapter.

Verified inside the live Blender interpreter:
- `dcc_mcp_blender_startup` is loaded in `sys.modules`;
- the startup file exists and still matches its accepted receipt hash;
- `dcc_mcp_blender 0.2.12` and `dcc_mcp_core 0.20.37` resolve from the accepted hostenv;
- `BlenderMcpServer.is_running == true` and the startup module owns the server.

Important runtime behavior:
- the Blender MCP HTTP listener is **ephemeral/dynamic** (`McpHttpServer(..., port=0)`);
- do **not** require or hardcode port `3102`;
- discover the current loopback listener owned by the active Blender PID and verify its `/health` response identifies `dcc-mcp-http`;
- streamable MCP requests must accept both `application/json` and `text/event-stream`.

Observed dynamic ports during acceptance included `23588`, `58483` and `14279`; changing values are expected.

End-to-end direct MCP validation passed before restart:
- initialize HTTP 200;
- initialized HTTP 202;
- tools/list HTTP 200;
- typed read-only `dcc_diagnostics__get_instance_info` HTTP 200 with `success=true`, Blender PID matching the live host, Core `0.20.37`, Python `3.13.13`, gateway `9765`.

After normal shortcut restart, the compact initial core surface passed:
- `dcc_diagnostics__process_status` -> `success=true`, `dcc_alive=true`;
- `dcc_capability_manifest` -> Blender `5.2.2 LTS`, 374 discoverable actions and 48 skills;
- `dcc_diagnostics__get_instance_info` is listed by the manifest as an unloaded capability and may not appear in the initial 32-tool surface until loaded.

Canonical final Blender evidence:
- `D:\Velvet\Logs\DCC-MCP\blender-0.2.12-final-regression-2026-09-30.json`
- SHA256 `53258BC48210DAB59B9AA797710DF007A0B833A22F21A3441338B4ADA90239C7`

No Blender executable, signature policy, startup script or accepted hostenv was modified to obtain this PASS.

## Known verifier/tooling mismatches

These are documented deployment/tooling mismatches, not current runtime failures:

1. Maya CLI verification resolves its receipt under the default `%USERPROFILE%\.dcc-mcp` location while the accepted deployment uses the D:\Velvet shadow state. Runtime registry + dispatch are healthy.
2. Blender CLI verification has the same shadow-receipt location mismatch. Port `3102` is a stale fixed-port assumption: the accepted server binds an ephemeral loopback port. The legacy readiness helper also sends only `Accept: application/json`, while the current streamable HTTP server requires both JSON and event-stream. Direct typed diagnostics and restart persistence passed.
3. Substance Painter CLI verification resolves the default Documents profile; the accepted profile is redirected to D:\Documents. Direct health + typed diagnostics passed.
4. Substance Designer CLI verification does not resolve the Velvet state receipt in this deployment. Direct health + typed diagnostics passed.
5. After Effects exact CEP runtime identity remains unavailable in the supported AdobePy contract. Functional typed RPC is healthy and no bypass is used.

Do not copy receipts into default profile paths merely to make a verifier report green.

## Repository checks

Final full `check-all` on the pushed source head:
- 116 sensors total
- 115 PASS
- 1 failure: `check-staleness`
- failure reason: no 2026-09-30 daily brief artifact after the configured 09:15 Asia/Jerusalem cutoff
- this failure is unrelated to the DCC/Adobe changes

Evidence:
`D:\Velvet\Logs\DCC-MCP\dcc-adobe-final-check-all-2026-09-30.json`

SHA256:
`BB3499A9F6EB2604DE5F6E0DA0CE0DD3A427D2BB20F01534ADD03BDB38BBF6F3`

Targeted checks also passed:
- DCC/Adobe compatibility validator
- critical syntax
- policy architecture
- `git diff --check`
- Blender / Illustrator / After Effects patch `git apply --check` against clean bases

## Rollback / backups

Important backups retained:

- Before retiring Adobe watchers:
  `D:\Velvet\State\AdobeBridge\backups\Start-VelvetDccDesktopHosts.before-retire-adobe-watchers-2026-09-30.ps1`
- Before Illustrator bootstrap hook:
  `D:\Velvet\State\AdobeBridge\backups\Start-VelvetDccDesktopHosts.before-illustrator-bootstrap-hook-2026-09-30.ps1`
- Retired Photoshop watcher:
  `D:\Velvet\State\AdobeBridge\backups\Watch-VelvetPhotoshopBridge.retired-2026-09-30.ps1`
- Retired Premiere watcher:
  `D:\Velvet\State\AdobeBridge\backups\Watch-VelvetPremiereBridge.retired-2026-09-30.ps1`
- Premiere Debug Database before final cleanup:
  `D:\Velvet\State\AdobeBridge\backups\Premiere-Debug-Database.before-final-debuguxp-cleanup-2026-09-30.txt`

Do not delete these until the production setup has survived normal use and at least one real machine reboot.

## Real machine reboot persistence closure

A real Windows reboot was completed after the original acceptance run.

Post-reboot result: **PASS**.

Two persistence defects were found and fixed during this gate:

1. **DCC gateway BootTrigger**
   - Root cause: Windows PowerShell with ErrorActionPreference='Stop' promoted native dcc-mcp-server.exe stderr to a terminating error immediately after the wrapper logged START.
   - Fix: retain fail-closed Stop behavior for the wrapper, but temporarily use Continue only around the native gateway process, capture LASTEXITCODE, and restore the prior preference.
   - Boot task: VelvetOS DCC Gateway, SYSTEM, BootTrigger.
   - Real reboot result: /health returned HTTP 200 before interactive login and the task completed with result 0.

2. **Photoshop first-party broker persistence**
   - The UPIA Photoshop bridge 0.1.1 persisted correctly, but its dedicated AdobePy broker on 127.0.0.1:47393 had no durable logon task.
   - Added VelvetOS AdobePy Broker Photoshop, running in the Chris interactive session at logon.
   - The broker is loopback-only, long-lived and self-retrying.
   - After the real reboot and login, Photoshop established a live client connection to 47393.
   - No Photoshop watcher and no UXP Developer Tool load command are required.

Source-controlled deployment templates:
- packages/vfharness/devtools/dcc-adobe-runtime-persistence/Start-VelvetDccGateway.ps1
- packages/vfharness/devtools/dcc-adobe-runtime-persistence/Start-AdobePyBroker-Photoshop.ps1
- packages/vfharness/devtools/dcc-adobe-runtime-persistence/Install-DccAdobeRebootPersistence.ps1
- packages/vfharness/devtools/dcc-adobe-runtime-persistence.json

Post-reboot evidence:
- docs/evidence/dcc-adobe-post-reboot-persistence-2026-09-30.json

The compatibility validator hash-checks the deployment templates and asserts the BootTrigger/AtLogOn task contracts so future source drift fails CI.

127.0.0.1:14001 is the Adobe UXP Developer Tool service and is not required for the installed production Photoshop/Premiere UPIA routes. It is intentionally not added as a production autostart dependency.

## Desktop cleanliness / hidden on-demand mode

The workstation is a general-purpose daily-use PC, not a dedicated DCC kiosk. GUI hosts therefore no longer start automatically at Windows logon.

Current contract:
- DCC gateway remains background-only at boot.
- AdobePy brokers may remain background-only at logon.
- VelvetOS DCC Desktop Hosts has no trigger and is manual-only.
- Each enabled GUI host has one manual VelvetOS DCC OnDemand <app-id> task with no trigger.
- Agent launches pass -HideAfterLaunch; the host window is hidden from the desktop/taskbar after launch.
- Invoke-VelvetDccHost.ps1 exposes bounded start / stop / status control for one app.
- Normal vendor/Start Menu shortcuts are unchanged, so owner-launched applications remain normal interactive applications.
- Seven obsolete acceptance/temp/reconnect tasks were removed after XML backup.
- No matching Run-key or Startup-folder entry was found.

Live acceptance on 2026-09-30:
- all previously auto-launched GUI hosts were closed; zero enabled GUI hosts remained running;
- cold Blender launch through the manual task produced a hidden host with its loopback listeners still alive, then stopped cleanly;
- hiding Photoshop removed its main window while the 47393 broker retained an established Photoshop client;
- gateway health remained HTTP 200 and the background brokers remained available.

Canonical evidence:
- docs/evidence/dcc-adobe-hidden-on-demand-2026-09-30.json

No extra reboot was forced for this ergonomics change. The next-login contract is statically guarded by the absence of GUI logon/run/startup triggers and by CI validation of the source-controlled installer.

## Final clean state

At the end of regression:
- After Effects closed
- Photoshop closed
- Premiere closed
- Illustrator closed
- brokers 47391 / 47392 / 47393 still listening
- zero established Adobe bridge clients
- DCC gateway 9765 listening
- UXP service 14001 listening
- Photoshop watcher not running
- Premiere watcher not running
- Illustrator bootstrap not running

No temporary write acceptance artifact was left open.

## What remains

The DCC/Adobe integration work in this handoff is complete.

Separate follow-up items, not blockers for this integration:
1. Decide whether to merge `chore/dcc-adobe-compat-overlays-20260929` into main after normal review.
2. Fix or satisfy the unrelated daily-brief `check-staleness` failure.
3. Optionally upstream the generic fixes (for example the streamable-HTTP Accept-header compatibility and configurable receipt-root behavior) instead of carrying local compatibility overlays forever.
4. Re-run the final matrix after material host/adapter upgrades; all local overlays are version-pinned and should fail closed on drift.
