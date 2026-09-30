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
- SHA256: `7B28D274709F8C276C5C1498821801D0C3F521523EE6CFA51762E10B21ADA8EC`

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

## Known verifier/tooling mismatches

These are documented deployment/tooling mismatches, not current runtime failures:

1. Maya CLI verification resolves its receipt under the default `%USERPROFILE%\.dcc-mcp` location while the accepted deployment uses the D:\Velvet shadow state. Runtime registry + dispatch are healthy.
2. Blender CLI verification has the same shadow-receipt location mismatch. The legacy readiness helper also sends only `Accept: application/json`, while the current streamable HTTP sidecar requires both JSON and event-stream. Direct typed diagnostics passed.
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
