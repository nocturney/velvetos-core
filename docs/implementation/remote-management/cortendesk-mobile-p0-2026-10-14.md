# Remote Machines P0 — browser-first CortenDesk acceptance

Date: 2026-10-14
Owner scope: **one human operator**, six existing Windows/macOS targets
Status: **P0 PLANNED / CORTENDESK NOT RUNNING / MOBILE NOT VERIFIED**
PR: [#717](https://github.com/nocturney/velvetos-core/pull/717)

## Non-negotiable result

One authenticated HTTPS entry point usable through a normal browser on
desktop, iPhone Safari and iPad Safari, from outside the office. Do not
require the RustDesk mobile app, any proprietary desktop client on iOS, a
third-party RMM portal, or a VPN app on mobile. Management agents *on the
managed Windows/macOS hosts* remain allowed.

Start from **CortenDesk's existing interface**, not a new cloned desktop
viewer: device list, live browser remote control, address books, file
transfer and audit. Beszel monitoring comes **after** real browser control
passes. MeshCentral is optional for demonstrated gaps, not a default
second agent on every device.

## Phase 0: what exists and what is forbidden

- Production stock RustDesk OSS rendezvous/relay on MacMiniOffice2 remains
  the only live server; all six RustDesk clients and their identities
  remain unchanged.
- Separate `velvet-qa` ARM64 Colima research runtime is running.
- Pinned CortenDesk v1.13.2 OCI image and source audit exist. Independent
  isolated staging was planned for loopback port 18080 + 22115-22117.
- **Actual container launch was denied previously by the remote connector**.
  Do not circumvent this by a renamed command, alternate namespace,
  daemon proxy, startup task, agent or changed security config. There is
  no authorized running CortenDesk test service.
- Existing named offline HTML registry viewer and working RustDesk native
  links remain a private **desktop fallback**; not the proposed browser
  service or a usable iOS web remote-control product.
- No OS reinstall, PXE, recovery, firmware/BIOS, Windows Update or MDM
  rebuild capability is in scope.

## Phase 1: authorized isolated desktop/browser smoke test

Needs independent permitted runner/explicit runtime clearance first.
No production mounts, server keys, users, agent settings or ports shared
with the live RustDesk stack. Admin credentials unique and nondefault;
no default `admin/changeme` password. Use a disposable RustDesk client
enrolled only to the **bundled** stage server, not an existing live host.

The pinned local stage manifest is
`tools/rustdesk-pilot/fixtures/cortendesk-staging-plan.json`.
Read-only static design gate:

```sh
python cortendesk_staging_gate.py --plan fixtures/cortendesk-staging-plan.json
```

From `tools/rustdesk-pilot/`, once a **separately authorized** stage
is actually serving loopback on the planned port, use:

```sh
python cortendesk_local_http_gate.py \
  --plan fixtures/cortendesk-staging-plan.json \
  --allow-local-staging-read
```

This is a *GET-only unauthenticated* route inspection of **exactly**
`http://127.0.0.1:18080/login`, `/devices` and `/webclient`. It sends
no token/cookie, disables redirects and proxies, reads bounded response
bytes and logs no HTML, URL query, IP, RustDesk ID, secret or session.
A local auth-surface PASS requires a rendered login page and rejection or
login redirection for both protected routes. It explicitly **does not
assert that this is a genuine CortenDesk instance, nor that Safari,
WebSocket, desktop control, file transfer or authentication works**.

If no container is running: `STAGING_NOT_REACHABLE`. This is honest
runtime unavailability, not an invitation to bypass the earlier denial.

## Phase 2: real iPhone/iPad Safari proof before public deployment

Only after authorized CortenDesk stage passes isolation, authenticate a
disposable operator to the app through **HTTPS with authenticated access**
and verify `wss://` signalling to the stage's internally proxied
`/ws/id` and `/ws/relay`. A local host-only stage is NOT accessible
directly from the iPhone. A separate **approved** remote-access design is
required; Cloudflare Tunnel + Access is a candidate, not deployed.

Important: configure an Access self-hosted application **before**
publishing a tunnel hostname; use account-specific MFA, deny by default
and origin-side validation of the Access JWT or `cloudflared` Protect
with Access. Ensure Access protects login, WebSocket endpoints and any
future API equally. Do not expose raw RustDesk server ports, SSH or
administration to the public Internet. Test Access token/session expiry
and that WebSocket reconnects reauthorize.

Run the following **manual, real-device acceptance** on physical iPhone
Safari and iPad Safari, from cellular/another network, not only office Wi-Fi:

| Required capability | iPhone | iPad | Evidence |
|---|---|---|---|
| Log in with owner-only MFA and log out | UNTESTED | UNTESTED | Browser session |
| Device names, online state and last update truthful | UNTESTED | UNTESTED | UI+server timestamps |
| Open a disposable remote desktop **inside Safari** | UNTESTED | UNTESTED | Real screenshot/session |
| Touch pointer, drag, wheel, keyboard input | UNTESTED | UNTESTED | Real client interaction |
| Rotation, viewport scaling, multi-monitor when present | UNTESTED | UNTESTED | Real client interaction |
| Copy/paste text in both directions with iOS permissions | UNTESTED | UNTESTED | Clipboard trial |
| Upload and download test file via iOS Files picker | UNTESTED | UNTESTED | Byte/hash check |
| Disconnect/reconnect after app switching or screen lock | UNTESTED | UNTESTED | Session continuity |
| Access denial without login; session expiry and log | UNTESTED | UNTESTED | Negative-case proof |
| No native RustDesk iOS app or VPN required | UNTESTED | UNTESTED | Clean Safari device |

Use meaningful `UNSUPPORTED` when a capability cannot work on Safari;
do not present the whole browser cockpit as feature-complete until
essential control, touch, keyboard and file workflows pass on *both*.
CortenDesk v1.13.2 documents fallback decoding over HTTP (H.264);
its desktop experience is preferred on Chrome/Edge, so browser claims
alone are not sufficient proof for mobile Safari.

## Phase 3: Beszel after P0 control works

Only then inspect and, with authorization, pilot one Windows and one
Mac Beszel agent, using HTTPS and authenticated server-side API reads.
Show CPU, RAM, disk, network and timestamp/freshness, always separated
from RustDesk presence. Do not fake GPU/sensor availability. Match a
single canonical device ID across RustDesk, Beszel and VelvetOS.
Reuse VelvetOS Control Center's **read-only** adapter architecture;
never expose backend tokens in front-end JavaScript.

## No-claim rule

No CortenDesk container started, public domain published, Cloudflare
account modified, RustDesk client switched, remote connection initiated,
mobile Safari session tested or telemetry agent installed by this
planning/smoke-test stage. These remain explicit blockers, not
"completed" checkboxes. The exact user-approved next action is to
provision a **permitted isolated stage runtime**, then carry out Phase 1.
