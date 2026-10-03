# Runtime Repairs & Compatibility — Completion Handoff

Date: 2026-10-01
Source: Handoff 03 — Runtime Repairs & Compatibility
Scope: repair-only; no new creative features, no printer control, no publish/send, no integrity bypass, no push/merge.

## Executive state

The explicit Phase 2 runtime-repair issues are repaired and revalidated:
- HyperFrames runtime restored on Windows with latest-compatible 0.8.105.
- PrusaSlicer 2.9.6 is now discovered as a fallback while OrcaSlicer remains canonical first.
- OpenSCAD Nightly is integrated into Update Sentinel with a real CLI export/render compatibility probe and an official snapshot watch.
- Topaz Gigapixel is retired from active inventory/state and remains uninstalled.
- Update Sentinel state was reconciled; Adobe startup readiness race was fixed without weakening fail-closed behavior.
- Existing Creative Craft Milestone 1 evidence was not regressed.

One unrelated pre-existing routing exception remains: Maya is still blocked as needs_compatibility_repair from an earlier failed dynamic MCP probe. Its current fingerprint matches its accepted baseline, so it was not automatically relaunched/revalidated under the no-heavy-GUI-without-drift rule.

## 1. HyperFrames

Before:
- edge-host state claimed HyperFrames 0.8.34 doctor/render PASS from 2026-09-24.
- D:\Velvet\Runtime\VelvetOS\npm was empty and HyperFrames was not runnable from PATH.

Root cause at this repair boundary:
- Runtime package presence and historical verified state had diverged; the old receipt remained authoritative after the runtime prefix lost the package.

After:
- Installed hyperframes@latest-compatible = 0.8.105 into D:\Velvet\Runtime\VelvetOS\npm.
- Browser ensure PASS using existing cached Chrome Headless Shell.
- vf_hyperframes doctor PASS with Node v24.19.0 and ffmpeg/ffprobe 9.0.2.
- Real harmless MP4 smoke: 1080x1920, 30 fps, 2.0 s, H.264.
- Output SHA256: 3f854f8298ba1bdea1844b9be4c807fbe2d2b1ae12ddd963db053ad200b60374.
- Receipt: D:\Velvet\Tmp\velvet-hyperframes-windows-smoke\renders\host-smoke.mp4.receipt.json.
- D:\Velvet\State\VelvetOS\edge-host.json updated to truthful 0.8.105/PASS state.
- No inbound port or tunnel added.
- npm's blocked esbuild install script was not blindly approved because browser/doctor/render all passed without it.

Recovery:
- Existing bootstrap-edge-host-windows.ps1 remains latest-compatible and carries 0.8.34 as the recovery/minimum baseline.
- Full bootstrap was intentionally not run because it also performs repo checkout/pull and the canonical repo was on another branch.

## 2. PrusaSlicer discovery

Before:
- PrusaSlicer 2.9.6 existed at C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe.
- gcode_tool discover reported prusa-slicer available=false.
- OrcaSlicer 2.4.2 was available and preferred.

Root cause:
- Upstream gcode_tool recognized the executable name but only searched configured env/PATH plus macOS bundle paths; it did not search Windows Prusa3D Program Files.

Repair:
- Added a VelvetOS-local discover_prusa overlay in scripts\vf_cad.py.
- Overlay checks PRUSASLICER_BIN, PATH, Program Files, Program Files (x86), and LOCALAPPDATA\Programs.
- It sets PRUSASLICER_BIN only when a real file is found.
- Upstream text-to-cad repository was left untouched and clean.
- Same patch deployed to live runtime copy: D:\Velvet\Runtime\VelvetOS\Cognee\cognee-core\scripts\vf_cad.py.
- Runtime rollback: D:\Velvet\Runtime\VelvetOS\Cognee\cognee-core\scripts\vf_cad.py.before-prusa-discovery-20261001.bak.
Acceptance:
- Worktree vf_cad doctor PASS.
- Live runtime vf_cad doctor PASS.
- Live Fabrication Router doctor PASS.
- Discovery now reports Orca first, Prusa second, Cura third.
- Canonical active slicer remains OrcaSlicer 2.4.2.
- Real local-only Prusa slice created D:\Velvet\Tmp\prusa-runtime-repair\cube.gcode.
- G-code SHA256: AFFBB2CE374091BFD3D2D8BE35B11FD66E4F37A680CF78DEFA264F4079AC4E90.
- No printer upload, print start, heating, motion, or network control occurred.

## 3. OpenSCAD Nightly update health

Installed remains OpenSCAD Nightly 2026.09.18. Stable was not substituted.

Added:
- Check-OpenScadNightlyUpdate.ps1 using https://files.openscad.org/snapshots/ and specifically Windows x86-64 Installer versions.
- Probe-OpenScadNightly.ps1 performing real STL export and PNG render.
- OpenSCAD Nightly host in DCC Update Sentinel as standalone_cli.
- Scheduled Sentinel scans now execute the update watch automatically.
- Auto-update remains false.

Current watch result at completion:
- installed: 2026.09.18
- latest observed by the live official-index watch: 2026.10.01
- status: UPDATE_AVAILABLE
- policy: do not update automatically; after an installed-version change, fail closed until the CLI compatibility smoke passes.

Current compatibility evidence:
- OpenSCAD gate: PASS_NEW_VERSION for the newly tracked host.
- Receipt: D:\Velvet\Logs\DCC-Adobe-Update-Sentinel\receipts\20261001T165930Z-openscad-nightly.json.
- Receipt SHA256: BD182F0A2639E872E852BF77D05EB0F2485E9A6A631D6B2D71A5F211F95DFEC5.
- openscad.com SHA256: 2A0A1D2F5D942A63E77A659623D92FD67D7C6CF91A17BAEF0702D736DAE0B268.
- STL smoke SHA256: 95ED0BA2988C760597CBCF13E9FFADB90CD731E4FA1B1C72DE0B4E8246DE810E.
- PNG smoke SHA256: 2269E9DE6EAB15427BACFC5AA8C18132B981CB380DDB775D742E40AA1E03421F.
## 4. Topaz Gigapixel retirement

Before:
- Active Update Sentinel config and accepted baseline still contained topaz-gigapixel inventory-only state from earlier work.

After:
- Removed from active Update Sentinel config.
- Removed from accepted baseline.
- Removed stale notification-state file.
- Removed active topaz-gigapixel connector JSON from the Creative Tools worktree.
- Live executable and Photoshop plugin paths both verify absent.
- Historical evidence/receipts were intentionally preserved.
- A timestamped accepted-baseline backup was created before retirement.
- No reinstall was performed.

## 5. Update Sentinel consistency repairs

Two Sentinel-state defects were found while reviewing evidence consistency.

Adobe readiness race:
- A freshly launched Photoshop could be probed after only ~2 seconds and fail with "bridge disconnected before response".
- Sentinel now retries the same read-only Adobe compatibility probe within a bounded 45-second readiness window.
- It remains fail-closed: only structured PASS can clear the gate.
- Photoshop then revalidated successfully.
- Photoshop receipt SHA256: 4F0A98D24BA04BC12694ABCDE4C6F7CF362BEC508982F7934F0C9875F6E30E31.

Stale pending routing:
- Several hosts retained pending_validation even when current fingerprint exactly matched accepted baseline.
- Sentinel now reconciles only that exact stale condition to available.
- needs_compatibility_repair is never auto-cleared by this logic.

Targeted real drift was revalidated:
- Topaz Video receipt SHA256: EE2F7EF014D3F92E288643D26C7A7FE093FA834E4500240E3A2F332CAF28A1A5.
- CorelDRAW receipt SHA256: 1F9F106DE8D68AB98921F41D17FC214FF8B5A29168B1255ACCE5CBF8DBECD450.
- Corel DESIGNER receipt SHA256: 1DE8BA075E96FEEC918A90836B0CBDEDF29B8309E1E72DF5DA131C68898F6453.

Final consistency:
- Integrated baseline vs current inventory fingerprint diffs: 0.
- All current integrated routes are available except Maya.
- Maya remains needs_compatibility_repair from receipt error "no live dynamic MCP endpoint for maya"; no fingerprint drift exists, so this handoff did not relaunch it.
## Runtime/source hashes

- Update Sentinel script: 75462C6C7B0A963060CA9962B363AD4AC3AF9FB2F53FF5F2C4F63BB0E1593559.
- Sentinel config: 890BFAA57FD3D36F8C3C6E769B3AE3B390CF585906557FA607C0940F98C333AA.
- OpenSCAD update watch: 55C567E0AC6AFC6D609E2BCC1B5629227D37729E231FE4C05ECF48A6E3E28CA3.
- OpenSCAD compatibility probe: DB4EFCE377809F167FF070027D1E04E4C0FD5B64F791193CFE8D222ADD524034.
- Runtime/source copies of Sentinel files were hash-matched after deployment.

Runtime backups:
- D:\Velvet\Runtime\UpdateSentinel\Invoke-DccAdobeUpdateSentinel.ps1.20261001-runtime-repair.bak
- D:\Velvet\Runtime\UpdateSentinel\dcc-adobe-update-sentinel.json.20261001-runtime-repair.bak
- D:\Velvet\Runtime\UpdateSentinel\Invoke-DccAdobeUpdateSentinel.ps1.before-adobe-readiness-20261001.bak
- Prusa runtime backup listed above.
- Gigapixel baseline backup is stored beside accepted-baseline.json with prefix accepted-baseline.before-gigapixel-retire-.

## Files changed/added for consolidation

Tracked patch:
- scripts\vf_cad.py

Creative Tools worktree files:
- packages\vfharness\devtools\creative-tools\update-sentinel\Invoke-DccAdobeUpdateSentinel.ps1
- packages\vfharness\devtools\creative-tools\update-sentinel\dcc-adobe-update-sentinel.json
- packages\vfharness\devtools\creative-tools\update-sentinel\Check-OpenScadNightlyUpdate.ps1
- packages\vfharness\devtools\creative-tools\update-sentinel\Probe-OpenScadNightly.ps1
- packages\vfharness\devtools\creative-tools\topaz-gigapixel.json retired/removed.

Evidence:
- docs\evidence\creative-craft\runtime-repairs-compatibility-2026-10-01.json
- docs\evidence\creative-craft\runtime-repairs-compatibility-handoff-2026-10-01.md

No commit, push, or merge was performed. Preserve unrelated worktree modifications during consolidation.
