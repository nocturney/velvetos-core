# VelvetOS Remote Management — single-operator research intake

Date: 2026-10-14
Route: system_engineering (project_preflight: PASS for isolated code-only research)
Status: CODE_VALID / SANDBOX_ONLY / NO LIVE ACCEPTANCE
Owner: one human operator; team/RBAC features are explicitly deprioritized.

## Goal and user value

Create a single-operator device cockpit for heterogeneous Windows/macOS/Linux machines: reliable machine list, last-seen, one-click connect, file transfer and diagnostics. Use existing functioning RustDesk clients and Desktop Commander until alternatives are independently accepted. Enterprise user hierarchies and shared address-book administration are not the product goal. Maintain baseline remote-access security even with one operator.

## Source shortlist (GitHub source and documentation inspected 2026-10-14)

- CortenDesk (marcpope/cortendesk; AGPL-3.0-only): current leading dashboard/server candidate. Implements browser client, read-only/controlled admin API, machine inventory and self-hosted ID+relay options. Its bundled server is a separate fork; replacement is NOT approved. CortenDesk v1.13.2 released 2026-10-13. API route and serializer verified against source. Active issues still require production suitability review.
- RustDeskMCP (YaoxinCS/RustdeskMCP; AGPL-3.0): RustDesk client fork with localhost MCP desktop frame, keyboard/mouse and terminal operations. An independent local user-visible opt-in; never assume automatic fit with Remote Desktop Commander, user session or other endpoints.
- rdcli (4nkitd/rustdesk-cli; AGPL-3.0): early-stage headless RustDesk client with file transfer, terminal, tunnel and ping capabilities. Repo v0.1.0; not yet production qualified.
- QuickDesk (barry-ran/QuickDesk; MIT): AI-native remote desktop built on Chromium Remoting/WebRTC, NOT a drop-in RustDesk API plugin.
- Rem0te (agit8or1/rem0te; MIT): impressive managed device inventory and Windows diagnostics, but service-provider/team architecture is excessive for one operator.

## Current environment observations (read-only)

Desktop Commander reports six online connector devices: three Windows and three macOS. These are not necessarily six RustDesk endpoints or proof of RustDesk connectivity. On Windows Chris, the RustDesk service was Running / Automatic and RustDesk client processes observed. Docker executable not found in the tested PATH on all six hosts. Chris Remote Desktop Commander executes under Windows SYSTEM Session 0, not an interactive user session; WSL refuses to run under that identity. No Docker/WSL installation, UI action, service restart, firewall/UAC/security change, agent/scheduler or client configuration modification was performed.

Existing Core checkout at D:/Velvet/Repos/velvetos-core is on another active branch; it was not edited. This research lives in an isolated worktree based on origin/main: D:/Velvet/Worktrees/rustdesk-single-operator-20261014 on branch research/rustdesk-single-operator-20261014.

## Implemented code and evidence

The tools/rustdesk-pilot prototype parses the verified CortenDesk API envelope through an explicit read-only, one-shot adapter. It uses stable machine names/IDs and source-typed ONLINE/OFFLINE/UNKNOWN, validates pagination and source errors, never presents partial reads as complete data, and labels fixture output explicitly. The fixture has only invented TEST-* demo identities. No real device IDs, secrets or control credentials are in the code.

Windows test: python -m unittest discover -s tools/rustdesk-pilot/tests -v (13 tests PASSED), 2026-10-14.
Windows fixture smoke: counts total=3 online=1 offline=1 unknown=1 and state=FIXTURE_ONLY.
This is contract-shaped testing using synthetic fixtures, NOT real CortenDesk server integration.

## Integration outline

Existing UI / Control Center -> server-only VelvetOS adapter (future, read-only) -> CortenDesk Admin API device:r -> independently deployed/approved RustDesk staging infra. Use no browser-facing token, no duplicate scheduler, no live production writer inside Core and no fabricated status on disconnect. The remote-control action stays out of scope for this pilot. For a future one-click connect UI, prefer the installed, explicitly approved RustDesk client or a separately validated browser client.

## Explicit exclusions / risks

- NO cutover of RustDesk ID/relay server, user clients or keys.
- NO production deployment or auto-start while unrelated Office/VelvetOS tasks execute.
- NO new recurring paid services.
- NO production token, no secrets in git, no telemetry claims inferred from Desktop Commander.
- NO user-management/RBAC-heavy implementation.
- NO assumption that third-party code is secure based on being open source; audit the upstream release, license and threat model before test exposure.
- NO merge to main without separately passing routing/sensors/review.

## Next bounded action

Run the pilot tests and repository checks, then keep a draft PR for review. The next meaningful external action is an isolated CortenDesk server trial on a suitable host, which requires an approved runtime plan, nonconflicting ports, independent credentials and test-device enrollment. A future MCP or GUI control experiment should be separate and revertible.
## Read-only six-host RustDesk compatibility snapshot (2026-10-14)

- Windows Chris, Chris-Mini-PC and Chris-3DPC: installed RustDesk.exe file version 1.5.0+68 on all three; RustDesk service RUNNING with Automatic startup on all three.
- macOS MacMiniOffice2, MacMiniOffice and Mac-Bedroom: /Applications/RustDesk.app version 1.5.0 installed on all three and its service process observed.
- MacMiniOffice2 already has a live owner-managed RustDesk OSS server supervisor, running hbbs and hbbr via Colima profile named rustdesk (aarch64; 2 CPUs / 2 GiB), with existing listeners on 21115, 21116, 21117, 21118 and 21119. It also has a separate running Colima profile named velvet-qa (2 CPUs / 4 GiB); neither profile was touched or reconfigured. This is important existing production/test infrastructure, not a spare install target.
- On the Macs, the Docker CLI was not in PATH, but MacMiniOffice2 does have colima and limactl, with containerd as runtime. The earlier absence of a Docker command must NOT be interpreted as absence of all container infrastructure.
- No server secrets, RustDesk device IDs, authentication tokens, user sessions or remote endpoint addresses were collected. No server commands or process changes were made. A running RustDesk service is not proof the device has been enrolled in CortenDesk or would appear in that dashboard.
- Strong constraint for next trial: CortenDesk supports an external hbbs/hbbr server in documentation, but its admin device inventory depends on clients reporting to the configured CortenDesk API server. Therefore standing up the dashboard alone is insufficient to populate a real inventory. Test client enrollment/API settings only on a separately approved disposable test identity and without changing the existing working server/client settings.
- Actual compatibility of CortenDesk 1.13.2 with RustDesk client 1.5.0, the existing OSS server, and the Mac Colima environment remains UNTESTED.
