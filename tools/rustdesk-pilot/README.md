# RustDesk single-operator inventory pilot

Status: CORTENDESK-FIRST RESEARCH / 146 OFFLINE+LOCALHOST+DOM TESTS / MOBILE BROWSER P0 GATED

This folder supports three constrained inventory sources: an explicitly opted-in read-only CortenDesk API adapter, an offline read-only RustDesk OSS SQLite snapshot reader, and an expressly authorized one-shot local RustDesk OSS registry read. Its HTML preview renders only synthetic, offline-snapshot or locally read registration IDs, with explicit source labels and no false online inference. This research does not run a second production control plane or provide installation, background services, credential harvesting, remote-control commands, device mutations or auto-start.

## 2026-10-19 release refresh — v1.14.0 (NOT deployed)

The proposed isolated stage now pins **CortenDesk v1.14.0** (upstream source
commit `2070d598d30cbaec207060a0fbef539ccf5d5d52`) and the verified GHCR
OCI multi-platform index `sha256:3305ea4bca8814e71f6c0dcf49df449cf44f82be4023a0c98e15fdc2ef919545`.
The index's Linux/ARM64 child is `sha256:e26c1f5d2d2b14ffd97b46c04c5c8ef1a3dd6da3fa5e21baa7eb379fabcfea39`.
These digests were obtained by **anonymous public-registry metadata GET**,
not by pulling or starting an image. The previously cached v1.13.2 image is
**not** proof that v1.14.0 is cached.

Upstream v1.14.0 fixes the #102 client-login SSO bypass and #105 legacy
native RustDesk deep links and adds client TOTP/email-code support.
The review-only v1.13.2 link patch below is **obsolete for this target**:
do not apply it to v1.14.0. The source's `routes/api.php` retains the
read-only scoped `GET /api/v1/devices` route, while `routes/web.php`
protects `/devices` and `/webclient` with web authentication.
Those source facts do **not** establish runtime safety, mobile Safari
compatibility, signed-in client signalling or deployment readiness.

The new plan preserves localhost-only host ports, independent stage
namespace/data/keys, disposable clients and the **existing remote execution
denial** (`may_execute=false`). No new image was pulled, no container was
started, no server or client was reconfigured and no fleet-console code was
changed. See `docs/implementation/remote-management/cortendesk-release-refresh-2026-10-19.md`.

## CortenDesk-first staging decision

**The intended full remote-management solution is CortenDesk with its bundled
CortenDesk Server fork**, subject to independent end-to-end verification. The
local OSS ID viewer is a proven, read-only fallback, not a replacement for
CortenDesk. The maintainer warns that the stock RustDesk OSS `hbbs` server
can fail modern signed-in RustDesk 1.4.1+ signalling key exchange, so
`CORTENDESK_EMBEDDED_SERVER=false` is not assured full address-book
compatibility with our installed RustDesk 1.5.0 clients.

A pinned, isolated staging **design** (not a launch/install command):

    python cortendesk_staging_gate.py --plan fixtures/cortendesk-staging-plan.json

This must report `STAGING_DESIGN_VALID_RUNTIME_BLOCKED` and
`may_execute=false`. It statically checks a proposed localhost-only,
nonproduction staging topology while honoring the earlier denied remote
container-launch action. It does not query or change host services,
accounts, credentials, Docker/Colima, clients, ports or the actual server.
For source evidence, deployment limits and the stage acceptance matrix, see
`../../docs/implementation/remote-management/cortendesk-integration-decision-2026-10-14.md`
(from repository root: `docs/implementation/remote-management/...`).

## Source contract

Upstream: https://github.com/marcpope/cortendesk (examined 2026-10-14, v1.13.2).
CortenDesk routes/api.php: GET /api/v1/devices under auth:api-token and device:r. Its admin envelope carries code, data, total, current and total_pages. Its device serializer supplies rustdesk_id, alias, hostname, online, status, platform, last_online_at, device_group, version and additional fields. This adapter deliberately discards personal or sensitive extra fields.

## Offline verification (no server connection)

From this directory:

    python -m unittest discover -s tests -v
    python cortendesk_inventory.py --fixture fixtures/devices-page1.json

The sample contains synthetic TEST-001/002/003 devices. Its output explicitly marks state=FIXTURE_ONLY. Never treat fixture output as actual fleet status. The CortenDesk portion includes 22 tests: 13 contract tests plus 9 loopback-only HTTP tests (including Bearer header/GET, pagination, redirect token protection, 401/503 errors, oversize/invalid JSON, strict envelope code, and invalid timestamps). No external network is contacted by those tests.

## Optional live inventory read, only after a separate approval and a real test service

Use an API token with ONLY device:r permission. Store the token in CORTENDESK_READ_TOKEN on the execution host; never commit credentials. Use HTTPS and a CortenDesk staging origin (HTTP is accepted only for loopback testing).

    python cortendesk_inventory.py --base-url https://staging.example.invalid --allow-live-read

Without --allow-live-read, the adapter refuses to perform any network operation. It accepts no configuration writes and does not discover or read secrets by itself. Use the smallest possible scope with a nonproduction server; run the command manually.

## Contract / errors

Output schema: velvetos.remote_inventory.v0.
States: FIXTURE_ONLY (synthetic), CONNECTED (successfully read the configured source), UNAVAILABLE (explicit error, always an empty device list). Presence: ONLINE, OFFLINE or UNKNOWN, never guessed from absence of a heartbeat. All pages must agree on reported totals. A partial read, inconsistent pagination, duplicate device ID, invalid time-zone-less last-seen timestamp or unexpected upstream envelope is an error rather than a partial live dashboard. Multi-page reads are not a database-transaction snapshot: simultaneous device registration could still race with pagination, so this is not yet a production inventory authority.

Hard limits: 10 pages, 100 devices/page, 2 MB response/page, 5-second transport timeout. Live transport makes only GET /api/v1/devices, rejects redirects and HTTP on non-loopback hosts, does not proxy requests or log tokens. No scheduled recurring reads.

## Next gates

1. Confirm the user's existing RustDesk server/clients and identify any conflicts.
2. Smoke-test CortenDesk in an independent, owner-approved isolated environment with independent keys; never switch the live clients automatically.
3. Obtain a read-only device:r token in that test environment and verify real response shape, last-seen semantics, failure and offline handling.
4. Verify CortenDesk source/license/supply chain and the supported RustDesk client versions; treat CortenDesk upstream security/availability issues as blocking for production.
5. Review whether a read-only UI adapter can be wired to the existing Control Center architecture without making Core a live runtime.
6. Treat RustDeskMCP / rdcli as separate experimental candidates, not as silent replacements for existing Remote Desktop Commander.

Acceptance for this PR is fixture tests and research documentation only. It does not constitute deployment, use of production credentials, host permission change or migration.
## Current execution gate (2026-10-14)

The real CortenDesk 1.13.2 ARM64 OCI image has been fetched into an isolated containerd namespace on a test Mac VM, but a proposed localhost-only container launch was rejected by the remote tool's safety policy. No service was started, no CortenDesk device API was queried, no RustDesk clients were moved and no workaround was attempted. Therefore `CONNECTED` is only a unit-test behavior, not a proven live integration. Do not use the mock data to populate the existing VelvetOS Control Center. See the dated research intake for the immutable image digest and the source/compatibility review.

## Alternative: stock RustDesk OSS registry snapshot (no client API enrollment)

The upstream RustDesk OSS hbbs source (`rustdesk/rustdesk-server/src/database.rs`) stores known peers in a SQLite `peer` table, including `id`, `created_at` and sensitive columns. This adapter reads ONLY the `id` column from an explicitly supplied **completed offline snapshot**; it never reads the PK, UUID, GUID, user, note or info columns. It does not access or locate the live database, open a TCP connection, nor modify RustDesk configurations. The SQLite URI is read-only/immutable. Do NOT pass a working/live database with WAL to an immutable reader: an inconsistent live view could be produced.

    python rustdesk_oss_snapshot.py --snapshot path/to/a/completed-copy-of-db_v2.sqlite3

The result uses the same `velvetos.remote_inventory.v0` envelope as the CortenDesk adapter, with `state=SNAPSHOT_ONLY`, `observed_at=null` and `snapshot_read_at` as the local file-read time (NOT the source capture time). Crucially **every device is presence UNKNOWN**. The stock hbbs SQLite `created_at` is not a proof of last-seen/online status. This offers basic registered-ID discovery without enrolling each RustDesk client into a CortenDesk API server.

No full production database snapshot was created. An early metadata-only read confirmed the OSS `peer` schema and six rows; a later explicit read-only local query successfully produced a private HTML report containing only registered IDs on MacMiniOffice2. No real IDs, passwords, UUIDs, public keys or device records were committed or printed. Unit tests use disposable synthetic `peer` tables.

## Standalone local preview (never a live dashboard)

    python render_preview.py --fixture fixtures/devices-page1.json --output preview/demo.html

Open `preview/demo.html` locally in your browser. It has Hebrew RTL, search, presence filtering and a copy-ID button. There are no network assets, external JavaScript, live data, real device IDs, remote-control links or control commands. An explicit non-live notice cannot be removed by the renderer. Content Security Policy blocks network requests. The file is safe to review separately from the production Control Center.

To render a known *offline* SQLite snapshot instead, run `python render_preview.py --snapshot your-completed-snapshot.sqlite3 --output preview/your-snapshot.html`. This is still not live monitoring; snapshots show presence UNKNOWN.

The renderer refuses `state=CONNECTED` and refuses overwriting an existing HTML file. The extended test suite has 52 cases (13 CortenDesk contract, 9 localhost HTTP, 12 OSS snapshot, 7 preview and 11 private local-registry tests). The earlier PR head's `check-all` passed; new CI must be rechecked on the resulting commit.

### Routing decision

This work stays inside `tools/rustdesk-pilot/` as an isolated research candidate. There is no new runtime service, API writer, route registry, public frontend, or Control Center redesign. The existing live server and all six RustDesk clients remain unchanged.

## Private one-shot viewer for the existing RustDesk OSS server

For a **single human operator**, CortenDesk is optional if the immediate goal
is registered device discovery. There is now an explicit, read-only *local
registry* mode that queries a known SQLite `peer` table on the same host using
SQLite `mode=ro`, `query_only=ON` and one read transaction (including WAL).
Only `peer.id` is selected. No UUID, public key, notes, usernames, host system
data or service secrets are exported. The server stays untouched.

Example on MacMiniOffice2 (replace the destination filename each time):

    mkdir -p "$HOME/Library/Application Support/VelvetOS/RustDeskPilot/private"
    chmod 700 "$HOME/Library/Application Support/VelvetOS/RustDeskPilot/private"
    python3 render_preview.py \
      --registry-db "$HOME/Library/Application Support/Velvet/RustDesk/server/data/db_v2.sqlite3" \
      --allow-live-local-read \
      --output "$HOME/Library/Application Support/VelvetOS/RustDeskPilot/private/remote-machines-private.html"

This one-off command **reads real registered RustDesk IDs**, so its output is
private and must NOT be committed, shared, exposed via a web server or stored
under a Git worktree. An explicit flag is mandatory and a restrictive
owner-only `0600` file is created without overwriting an existing report.
The page uses an offline `REGISTRY_READ_ONLY` state with every machine marked
`UNKNOWN`. It is **not live device health**, has no auto-refresh, no
background process, no server API, and no one-click remote access. Each
refresh is an explicit new one-off invocation with a new output filename.

The mode requires **local OS read access** to the actual registry database
and does not request elevation or modify database records. This is distinct
from the `SNAPSHOT_ONLY` mode, which accepts a separately completed copy.
A denied read fails closed and produces no real-ID HTML. To view a real-ID
report, open its local path on the host; do not place it in a public folder.

## One-shot read-only Colima host readiness survey

The CortenDesk-first **staging design** remains blocked from execution under the
previous remote tool safety denial. A second, independent **read-only host
survey** checks the plan against reality on the MacMiniOffice2 host and its
currently running `velvet-qa` Colima VM; it never calls `nerdctl run/pull`,
`docker`, changes configuration or reads credentials.

Run only on the **MacMiniOffice2 host**, from this pilot folder:

    python3 cortendesk_readiness_probe.py \
      --plan fixtures/cortendesk-staging-plan.json

The survey checks: both Colima profiles running, native-host TCP/UDP staging
ports, guest Linux TCP/UDP staging ports (from a read-only `ss` listing),
the original RustDesk production rendezvous ports, image digest in the
**research** namespace, and whether the planned **staging** namespace exists.
It retains no raw socket addresses, process IDs, machine identifiers, secret
paths or command output.

A "free" observation is point-in-time only, not a reserved port or verified
network forwarding. `pinned_image_cached_in_research_namespace=true` does
**not** mean the image is accessible from the staging namespace. If checks
fail or output is unparseable, statuses are `unknown`, not success.
Every result returns `may_execute=false` and
`has_performed_mutation=false` even if all preconditions look good. The
earlier container launch denial is NOT cleared by these read-only checks.

Staging is intentionally scoped to 0.5 CPU / 1,024 MiB RAM and 127.0.0.1
host bindings with **new** test identities, keys and data. No production
RustDesk server or six installed clients are involved. Real CortenDesk
functional acceptance still requires a separately permitted execution
environment and end-to-end disposable-client verification.

## Pinned upstream CortenDesk RustDesk 1.5.0 deep-link fix (review only)

CortenDesk [issue #105](https://github.com/marcpope/cortendesk/issues/105)
reports a native-launch link problem for custom IDs with uppercase characters.
CortenDesk v1.13.2 still renders seven `href="rustdesk://{{ ... }}"`
links in four Blade templates. The RustDesk 1.5.0 tagged source
(`flutter/lib/common.dart`, `urlLinkToCmdArgs`) explicitly supports
`rustdesk://connection/new/<ID>` and reads ID from the **path**, not from
URI authority, which avoids browser host normalization of capital letters.

The standalone `cortendesk_deeplink_patch.py` generator validates all
four exact upstream Git blobs and produces a reviewable git patch converting
legacy links to `rustdesk://connection/new/{{ rawurlencode($x->rustdesk_id) }}`.
`rawurlencode` keeps the dynamic ID inside a single URL path component
instead of embedding it as a URL authority/query/fragment. It does **not**
connect to any device, edit CortenDesk or compile an OCI image.

With an unchanged local source checkout of CortenDesk tag `v1.13.2`:

    python cortendesk_deeplink_patch.py --source-root /private/source/v1.13.2
    python cortendesk_deeplink_patch.py --source-root /private/source/v1.13.2 \
      --patch-output /private/output/cortendesk-1.13.2-rustdesk-deeplinks.patch

Output is a **new file only**, never overwriting. The tool fails closed if
one source blob, link target or expected count differs. Use `git apply --check`
in an isolated source checkout to review applicability, not on any production
service. Applying/building/deploying requires a separate permitted runtime
and follow-up acceptance against real RustDesk clients. This local fix is
version-specific; do not silently carry it to a newer CortenDesk release.

## Optional manual native RustDesk launch — private viewer only

A single operator may now create an **opt-in private, offline** registry
report with a native RustDesk link beside each valid registered ID:

    python3 render_preview.py \
      --registry-db "$HOME/Library/Application Support/Velvet/RustDesk/server/data/db_v2.sqlite3" \
      --allow-live-local-read \
      --enable-native-connect \
      --output "$HOME/Library/Application Support/VelvetOS/RustDeskPilot/2026-10-14/private/registered-machines-manual-$(date -u +%Y%m%dT%H%M%SZ).html"

The output is new and owner-private (mode `0600` on macOS/Linux).
This mode is **not** enabled in fixtures, offline snapshots or ordinary
registry views. The operator must separately choose both read permission
(`--allow-live-local-read`) and native launch permission
(`--enable-native-connect`). The generated page has no network fetch,
auto-refresh, background process, embedded RustDesk client, or automatic
navigation.

Links are fixed `rustdesk://connection/new/<encoded-ID>` URIs supported by
RustDesk 1.5.0 source. Only IDs matching a constrained token are offered a
link; malformed IDs remain visible but have **copy only**. The browser may
prompt to allow the RustDesk app to open, and the installed client's usual
connection/authentication behavior then applies. An **actual one-click
connection has not been tested**; do not treat presence as online. Never
share or host the private HTML; it contains real registered machine IDs.

Tests: `python -m unittest discover -s tests -q` (111 cases) and Node
VM-based DOM behavior tests in `tests/native_launch_dom_check.js`, verifying
no automatic navigation, case-preserving safe URIs, link gating, and no
active-launch button in fixtures. The Mac report remains standalone.
CortenDesk (including browser control) is still the preferred full cockpit
and still requires a permitted runtime/isolated acceptance. This local
launcher is only an interim native-client convenience, not a CortenDesk
replacement or a change to VelvetOS Control Center.

## Friendly names — verified offline overlay, no IDs in GitHub

For the one-operator private RustDesk HTML view, supply an optional
owner-private `--aliases-file` together with `--registry-db` and
`--allow-live-local-read`. The file maps **SHA-256 hashes of exact registered
RustDesk IDs** to friendly hostnames. It does **not** contain actual IDs or
server credentials; do not commit or upload it. The loader enforces private
POSIX file permissions, rejects symlinks/Git paths, duplicate IDs/names,
unknown evidence types and invalid labels. Only an **exact hash match**
changes the display name; mismatches retain the original ID and are
explicitly labeled unknown. Remote-control URIs continue using the
**original** registered ID, never a guessed label.

The private mapping on MacMiniOffice2 was generated from six independently
matched registry entries: four clients' read-only RustDesk `--get-id` hashes,
plus two exact ID-to-hostname associations from the main Windows RustDesk
peer cache cross-checked with the registered server IDs and Windows
hostnames. No RustDesk ID, UUID, key, password, or alias mapping was
committed to GitHub. The six private entries have owner-only mode `0600`.

To build a new *named*, manual-link report on **MacMiniOffice2 only**:

    python3 render_preview.py \
      --registry-db "$HOME/Library/Application Support/Velvet/RustDesk/server/data/db_v2.sqlite3" \
      --aliases-file "$HOME/Library/Application Support/VelvetOS/RustDeskPilot/2026-10-14/private/friendly-names-verified-20261014.json" \
      --allow-live-local-read --enable-native-connect \
      --output "$HOME/Library/Application Support/VelvetOS/RustDeskPilot/2026-10-14/private/registered-machines-named-$(date -u +%Y%m%dT%H%M%SZ).html"

A different path/date is required on each invocation because reports use
exclusive creation and never overwrite existing private files. If one host
changes RustDesk ID, it is intentionally displayed as **unmatched** rather
than reusing an incorrect name. Availability remains `UNKNOWN` and does
not become live monitoring. This capability does not launch CortenDesk,
change RustDesk clients or affect the existing `hbbs/hbbr` services.

Source: `local_aliases.py`, `tests/test_local_aliases.py` plus the
Node DOM test validating the visible name and original native URI.

## P0 browser/mobile acceptance before monitoring

The solo-operator requirement is a single authenticated **browser** portal
for desktop, iPhone Safari and iPad Safari, without mobile management apps.
Prioritize CortenDesk's existing web client, not the interim private
RustDesk native-link viewer. **Do not start with Beszel/extra agents**
before the mobile control proof. Windows/macOS OS updates, reinstalls,
recovery, PXE and BIOS tasks are explicitly out of scope.

Pinned upstream CortenDesk `routes/web.php` defines `/login` (guest),
`/devices` (authenticated/device:r) and `/webclient` (authenticated).
One-shot, no-cookie/no-login **local** auth surface probe for an *already*
running independently authorized staging service:

    python cortendesk_local_http_gate.py \
      --plan fixtures/cortendesk-staging-plan.json \
      --allow-local-staging-read

This sends GET only to `127.0.0.1:18080`, never opens a browser session,
never follows a redirect and never launches a container. It checks that the
login route is available and neither protected page is public. Even PASS
means `LOCAL_HTTP_AUTH_SURFACE_PASS_NOT_MOBILE`; it proves **none** of
iPhone Safari, WebSocket, authenticated UI, video, clipboard or file transfer.
All physical mobile checks remain `UNTESTED` until separately conducted.

See `docs/implementation/remote-management/cortendesk-mobile-p0-2026-10-14.md`
for the exact security boundary and real-device test matrix. The earlier
denied runtime launch is still binding; no approval is implied by the
read-only probe or this change.
