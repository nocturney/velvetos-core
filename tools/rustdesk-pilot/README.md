# RustDesk single-operator inventory pilot

Status: RESEARCH / FIXTURE-AND-LOOPBACK-HTTP-VERIFIED / NOT DEPLOYED

This is an optional one-shot read-only adapter for the CortenDesk admin API. It is intended to inform a future VelvetOS Remote Machines card, not run a production second control plane. The only supported operations are GET requests for device inventory and fixture parsing. There is no install script, background service, credential harvesting, process injection, remote-control command, device mutation or auto-start.

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
