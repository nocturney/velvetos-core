# CortenDesk as RustDesk cockpit — evidence, architecture and safe staging gate

Date: 2026-10-14
Scope: VelvetOS Remote Machines, **one human operator only**
Disposition: **CortenDesk-first evaluation. NOT deployed or integrated into production.**
Parent: [RustDesk PR #717](https://github.com/nocturney/velvetos-core/pull/717)

## Decision

Prefer **CortenDesk 1.13.2 with its bundled CortenDesk Server fork** as the candidate full RustDesk management subsystem. Keep the existing single-operator RustDesk OSS registry reader as a read-only fallback/probe, *not* the target UI. VelvetOS Control Center remains the previously approved UI/read-only adapter. It may link to or summarize a CortenDesk subsystem after live verification; do not redesign Control Center, publish credentials to browsers, or move business-specific logic into core.

Priority outcomes: address book, remote device cockpit, one-click connection, authenticated in-browser remote control and file transfer. Multi-user/RBAC/enterprise SSO are not the user's product goals; baseline account protection is still mandatory.

## Source-backed capability vs. verified reality

CortenDesk README **v1.13.2** claims:
- Built-in web console with device rows, aliases, presence, address books and session logs.
- Native in-browser RustDesk client: signalling over WebSockets, video, mouse/keyboard control, clipboard, chat, file transfers and folders.
- RustDesk client HTTP API: login, heartbeat/sysinfo presence and address books. Stock clients can be configured to use the CortenDesk **API Server** field.
- Standalone one-image deployment with bundled `hbbs/hbbr`, plus optional external-server mode via `CORTENDESK_EMBEDDED_SERVER=false`.
- An HTTPS front end is strongly preferred beyond loopback; browser signalling requires a WebSocket path. The bundled image contains its own nginx bridge.

These are documented upstream claims, NOT capabilities we have yet seen running with our six clients. The CortenDesk image has been pulled but the previous live launch was rejected by the remote execution tool.

### Important compatibility correction

The README and [CortenDesk Server README](https://github.com/marcpope/cortendesk-server) report that **stock RustDesk OSS hbbs does not complete a signalling key exchange** introduced for signed-in RustDesk clients since 1.4.1, potentially producing `Failed to secure tcp: deadline has elapsed`. Their server fork supplies that response. **Do not assume that using CortenDesk's external-server mode with our existing stock `hbbs` gives full address-book and signed-in client functionality.**

External-server mode can still be assessed as a *limited*, non-cutover experiment. It does not require swapping the live ID/relay processes by itself, but does not cure the above server incompatibility. Similarly, a dashboard alone will not populate real CortenDesk presence without a reporting client configured for its API.

### Two distinct questions, not one

1. Can CortenDesk provide a console/WebSocket client over a known RustDesk rendezvous/relay? Upstream advertises it, but this exact topology has not yet been tested with our real server.
2. Can the full user/account/address-book/device-presence stack operate with our **stock server and RustDesk 1.5.0**? Upstream warns against relying on this. **Use the bundled fork in staging** to test real usability, not just the login page.

Do not equate a browser HTML health 200 with proof of remote video, file transfer or successful authenticated client signalling.

## Candidate adoption paths

| Path | Pros | Cons / status |
|---|---|---|
| Existing OSS server + private ID viewer | Already exercised on MacMiniOffice2, no new runtime or client changes | Just IDs, all six presence UNKNOWN, no browser control |
| CortenDesk console + existing OSS hbbs/hbbr | No server cutover during UI/API experiment | Client API setting/enrollment needed; upstream reports signalling incompatibility for signed-in 1.4.1+ clients; NOT proven |
| **Isolated complete CortenDesk stack with bundled fork** | Tests the advertised full architecture without endangering the working server | Requires permitted dedicated staging runtime, independent keys/ports, disposable client; NOT yet run |

## Existing fleet / workload boundaries

- MacMiniOffice2 operates **production/working RustDesk OSS** in Colima profile `rustdesk`, with `hbbs/hbbr` and original service ports 21115-21119. No service/config changes are authorized as part of research.
- A separate Colima `velvet-qa` (aarch64, 2 CPUs, 4 GiB) is running unrelated Office QA infrastructure. Keep its process/service/network controls intact; do not assume it is an idle exclusive machine.
- All six Windows/macOS endpoints have RustDesk 1.5.0 installed. Six registered IDs in the active RustDesk OSS SQLite database are **not proof of six online devices**.
- The 1.13.2 multi-arch release image is cached in an isolated containerd research namespace. Its previously recorded immutable digest: `sha256:3f91c02180d6ed59bfa3d4a938b0a52cf01e8fd1e953799be05435234c062373`.
- Previous attempt to start a localhost-only trial was **DENIED** by the remote execution control. No retry-by-disguise, alternate runner or bypass is permitted. The RustDesk prod profile was never changed.

## Concrete staging design — no commands executed

A separate **offline validation tool** under `tools/rustdesk-pilot/cortendesk_staging_gate.py` accepts `fixtures/cortendesk-staging-plan.json` and checks source digest, scope, resource limits, no production mounts, no client edits, exclusive localhost host-ports, a separate namespace and an external execution-approval gate. **It cannot start containers, set credentials, configure clients or modify any system.** Current result is deliberately `STAGING_DESIGN_VALID_RUNTIME_BLOCKED` with `may_execute=false`.

Proposed profile `velvet-qa`, containerd namespace `vf-cortendesk-staging`, CortenDesk's bundled server ON, new ephemeral storage, disposable identity, CPU 0.5, RAM 1024 MiB; staged *host* loopback-only ports 18080 (console), 22115 (NAT), 22116 TCP/UDP (rendezvous), 22117 (relay). These ports are **proposal only**; actual port availability, VM namespace networking, advertised relay address and ARM64 runtime compatibility must be reverified by an authorized operator immediately before execution. Do not expose the console or rendezvous publicly or assume localhost reaches devices on other hosts.

Prohibit: mapping `21115..21119` live ports, mounting the live server SQLite or signing keys, using the default admin password `changeme`, changing any installed RustDesk 1.5.0 client during trial, exposing an unpatched console on WAN, creating autostart services or adding recurring paid dependencies.

## Acceptance matrix (future, permitted runtime only)

1. **Deployment safety:** show no conflict with existing listeners, separate namespace/volume/credentials, process exits cleanly, no production server/client changes.
2. **HTTP and API:** loopback health returns expected status; first-run admin uses unique nondefault credentials; create disposable read-only `device:r` token; validate `GET /api/v1/devices` envelope and normalized adapter across 0/1/many pages.
3. **Disposable client only:** test RustDesk 1.5.0 *disposable profile* with distinct ID server, relay, public key and API server (no real client config overwritten); verify heartbeat populates the console and offline behavior is truthful.
4. **Browser client:** prove one authenticated screen session, actual input, WebSocket handshake and relay, clipboard and file transfer with innocuous test file; verify logout/session removal.
5. **Robustness:** disconnect staging console, relay and disposable client in turn. Show explicit UNAVAILABLE state, no invented status and rollback; never affect existing six endpoints.
6. **Review:** evaluate CortenDesk release and server-fork AGPL obligations, image provenance, patch availability and opened security issues. No production go-live while blocking issues remain unresolved.

## Upstream risk and version pinning

- [Issue #105](https://github.com/marcpope/cortendesk/issues/105), opened 2026-10-14, reports broken legacy `rustdesk://{id}` protocol links in 1.13.2 with RustDesk client 1.5.0 (custom IDs). Do not promise a one-click launch until tested.
- [Issue #102](https://github.com/marcpope/cortendesk/issues/102), open as inspected 2026-10-14, reports an SSO-only password-auth bypass in 1.13.1. Enterprise SSO is outside single-operator scope; exposing any server still demands ordinary credential security and review.
- Use pinned GitHub release **v1.13.2** and immutable image digest for reproducible tests, not floating `latest`.
- Upstream recommends its bundled CortenDesk Server fork over RustDesk OSS for signed-in clients since 1.4.1; this is the *maintainer's compatibility claim*, not an independently verified diagnosis on our network.

## Explicit handoff result

CortenDesk is **preferred for the full management UX**. The existing real-ID static report is verified and remains privately on MacMiniOffice2; it is NOT live monitoring. The blocker to full CortenDesk UX is **runtime authorization and end-to-end verification**, not a decision to abandon CortenDesk. GitHub PR remains Draft and must not be merged based solely on synthetic/unit/manifest tests.

Relevant source-of-truth links:
- https://github.com/marcpope/cortendesk/blob/v1.13.2/README.md
- https://github.com/marcpope/cortendesk-server/blob/main/README.md
- https://github.com/nocturney/velvetos-core/pull/717

## Non-mutating host readiness survey (follow-up, 2026-10-14)

Introduced `cortendesk_readiness_probe.py`: a source-controlled, one-shot,
read-only Mac host + Colima guest survey. It consumes and validates the
`cortendesk-staging-plan.json` design before running commands and
explicitly limits subprocesses to `colima list`, read-only `lsof` socket
enumeration and `colima ssh` queries of `ss`, `nerdctl images`,
`nerdctl namespace ls`. No shell command is composed from unvalidated
input. Runtime launch, image pull, server/client change, account changes
and credentials are out of scope. Report excludes raw sockets, endpoint
IPs, RustDesk identifiers and process IDs. On errors the status becomes
UNKNOWN; it does not claim a port is free.

The original 70 tests have been extended with dedicated simulated
readiness-probe tests (both native and guest ports, conflicting ports,
profile downtime, digest and namespace checks, fail-closed errors).
After the following GitHub commit, copy the exact pinned source to the Mac
and record *aggregate results only*; do not commit private machine data.
This survey has no authority to clear the prior remote execution denial.

## Verified host-and-guest probe result (MacMiniOffice2, 2026-10-14)

Ran the pinned `dfce0a94` source on MacMiniOffice2 using Python 3.9.6 after confirming all three staged file/blob hashes exactly match GitHub. The probe performed read-only `colima list`, `lsof`, and Colima guest `ss` and `nerdctl images/namespace ls` inspections; no container was launched, pulled or reconfigured.

**Point-in-time aggregate evidence** stored in
`docs/implementation/remote-management/cortendesk-host-readiness-2026-10-14.json`:

- Staging ports **18080/TCP, 22115/TCP, 22116/TCP+UDP, 22117/TCP** free on BOTH macOS host and the `velvet-qa` Linux guest at inspection time; they are NOT reserved.
- Existing RustDesk original rendezvous service observed on original production ports; both `rustdesk` and `velvet-qa` Colima profiles running.
- Pinned `v1.13.2` CortenDesk image digest matched in the earlier **research namespace**, but the separate planned `vf-cortendesk-staging` namespace **does not yet exist**. An image cached in a different containerd namespace is not sufficient to run the staging design unchanged.
- **Runtime still BLOCKED** by prior remote execution safety denial; survey asserts `may_execute=false`. Remote command connector exposed no separate approval path and its security configuration was NOT altered.
- These observations prove only staging infrastructure feasibility, not RustDesk 1.5.0 compatibility, working web control, server keys, password settings, persistent storage or ability for remote devices to reach loopback-only endpoints.

Status: **HOST_AND_GUEST_PORTS_FREE_AT_OBSERVATION; SOURCE_IMAGE_CACHED_IN_RESEARCH_NS; EXECUTION_NOT_AUTHORIZED**.

## CortenDesk v1.13.2 native-launch overlay (source verified 2026-10-14)

Confirmed issue #105 is present in pinned CortenDesk 1.13.2: seven
legacy `rustdesk://{{ device_id }}` links across four Blade UI templates.
RustDesk client's **tag 1.5.0** parses
`rustdesk://connection/new/<ID>` using the URI path, which is a viable
source-backed route for preserving mixed-case custom IDs.

A separately reviewable, source-hash-guarded patch has now been generated
for those seven links. It uses a URL-encoded ID path component and does not
alter the running server, its configuration or the pulled OCI image.
`git apply --check` **passed** on pristine CortenDesk v1.13.2 source copies
with exact GitHub blob hashes, and the copies remained unchanged. See
`cortendesk-deeplink-review-2026-10-14.md` and
`cortendesk-deeplink-review-2026-10-14.json`, plus
`tools/rustdesk-pilot/patches/cortendesk-1.13.2-rustdesk-1.5-deeplinks.patch`.

**Important:** patch applicability is not a live connection test.
No CortenDesk service was started, no URL handler invoked, no client
enrolled, no branch merged and no previously denied container-execution
path circumvented. Actual integration still requires a permitted test
runtime and mixed-case disposable-client acceptance.
