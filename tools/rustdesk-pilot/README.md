# RustDesk single-operator inventory pilot

Status: RESEARCH / 41 UNIT+LOCALHOST TESTS / OFFLINE HTML PREVIEW / NOT DEPLOYED

This folder implements two alternative nonproduction inventory sources: an explicitly opted-in read-only adapter for the CortenDesk admin API, and a strictly offline read-only RustDesk OSS SQLite snapshot reader. A generated HTML dashboard preview renders only synthetic or snapshot data. This is intended to inform a future VelvetOS Remote Machines card, not run a second production control plane. There is no installation routine, background service, credential harvesting, process injection, remote-control command, device mutation or auto-start.

## Source contract

Upstream: https://github.com/marcpope/cortendesk (examined 2026-10-14, v1.13.2).
CortenDesk routes/api.php: GET /api/v1/devices under auth:api-token and device:r. Its admin envelope carries code, data, total, current and total_pages. Its device serializer supplies rustdesk_id, alias, hostname, online, status, platform, last_online_at, device_group, version and additional fields. This adapter deliberately discards personal or sensitive extra fields.

## Offline verification (no server connection)

From this directory:

    python -m unittest discover -s tests -v
    python cortendesk_inventory.py --fixture fixtures/devices-page1.json

The sample contains synthetic TEST-001/002/003 devices. Its output explicitly marks state=FIXTURE_ONLY. Never treat fixture output as actual fleet status. The test suite currently contains 22 tests: 13 contract tests plus 9 loopback-only HTTP tests (including Bearer header/GET, pagination, redirect token protection, 401/503 errors, oversize/invalid JSON, strict envelope code, and invalid timestamps). No external network is contacted by those tests.

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

No actual server DB snapshot was created or read for this prototype. Unit tests construct disposable fake `peer` tables and verify no sensitive peer metadata leaks.

## Standalone local preview (never a live dashboard)

    python render_preview.py --fixture fixtures/devices-page1.json --output preview/demo.html

Open `preview/demo.html` locally in your browser. It has Hebrew RTL, search, presence filtering and a copy-ID button. There are no network assets, external JavaScript, live data, real device IDs, remote-control links or control commands. An explicit non-live notice cannot be removed by the renderer. Content Security Policy blocks network requests. The file is safe to review separately from the production Control Center.

To render a known *offline* SQLite snapshot instead, run `python render_preview.py --snapshot your-completed-snapshot.sqlite3 --output preview/your-snapshot.html`. This is still not live monitoring; snapshots show presence UNKNOWN.

The renderer refuses `state=CONNECTED` and refuses overwriting an existing HTML file. Latest checks on Windows: 41/41 tests PASS (13 CortenDesk contract, 9 localhost HTTP, 12 OSS snapshot, 7 preview) plus independent `node --check` of the browser script. CI must be checked on the resulting PR commit independently.

### Routing decision

This work stays inside `tools/rustdesk-pilot/` as an isolated research candidate. There is no new runtime service, API writer, route registry, public frontend, or Control Center redesign. The existing live server and all six RustDesk clients remain unchanged.
