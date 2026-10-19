# CortenDesk v1.14.0 — independent staging refresh

Date: 2026-10-19
Scope: stand-alone CortenDesk research in `tools/rustdesk-pilot/`, **not** a Fleet Console integration.
Disposition: OFFLINE TESTED / RUNTIME BLOCKED / NOT DEPLOYED.

## Verified upstream change
- CortenDesk latest GitHub release observed: [v1.14.0](https://github.com/marcpope/cortendesk/releases/tag/v1.14.0), published 2026-10-15.
- Immutable upstream source tag commit: `2070d598d30cbaec207060a0fbef539ccf5d5d52` ([tag ref](https://github.com/marcpope/cortendesk/tree/v1.14.0)).
- Official GHCR OCI index: `ghcr.io/marcpope/cortendesk@sha256:3305ea4bca8814e71f6c0dcf49df449cf44f82be4023a0c98e15fdc2ef919545`.
- Linux/ARM64 child manifest in that index: `sha256:e26c1f5d2d2b14ffd97b46c04c5c8ef1a3dd6da3fa5e21baa7eb379fabcfea39`.
- Verified index and architecture through an **anonymous public GHCR metadata GET** returning HTTP 200 on MacMiniOffice2; no OCI image was pulled or run.
- Release notes mark [#102](https://github.com/marcpope/cortendesk/issues/102) (password sign-in under enforced SSO) and [#105](https://github.com/marcpope/cortendesk/issues/105) (legacy client URI for uppercase IDs) fixed, and add TOTP/email-code client authentication. These are **upstream claims**, not a security audit of a running deployment.

## Source-contract spot check
- v1.14.0 `routes/api.php` Git blob `c3ff2a628b1f5a141596c6b29c59613b633d1407` retains `GET /api/v1/devices` under `auth:api-token` and `api-token-can:device,r`.
- v1.14.0 `routes/web.php` Git blob `a4eb478d1ccf55133ec605cff42a7187e7244141` keeps `/devices` and `/webclient` behind the `auth` group.
- These static route checks alone do not establish correctness of login, real API responses, WebSocket authentication, WebCodecs/Safari decoding, online presence or file transfer.
- The dedicated v1.13.2 manual deep-link patch is historical. **Do not apply it to v1.14.0.**

## Isolated stage design updated
Changed the single pinned release and OCI image index in `fixtures/cortendesk-staging-plan.json`. The static gate still restricts Colima profile `velvet-qa`, dedicated containerd namespace, loopback-only host bindings, 0.5 CPU/1 GiB, ephemeral fresh data and a disposable test client.
The read-only readiness parser now requires **repository + exact release tag + immutable image digest on one row**, preventing the old cached v1.13.2 image from being misreported as v1.14.0.
Guardrails unchanged: no production mounts, private keys, client settings, password reuse, internet listening, automatic service startup, paid services or Fleet Console changes.

## Read-only live environment evidence
- MacMiniOffice2: existing Colima `rustdesk` and `velvet-qa` profiles observed running.
- Existing RustDesk ID/relay listeners observed on original 21116/21117 TCP ports.
- No CortenDesk listener at stage console port 18080, and no CortenDesk process was seen in the host process listing.
- The earlier CortenDesk 1.13.2 image was cached in a research namespace at the prior checkpoint; **no assertion that the 1.14.0 image is cached**.
- This survey does not prove all six hosts are online or ready for remote control. No CortenDesk runtime was started.

## Verification and blocked gate
- Windows isolated research worktree: `python -m unittest discover -s tools/rustdesk-pilot/tests -q` — 146 tests, 1 platform-specific skip, PASS.
- Updated `cortendesk_staging_gate.py` — `STAGING_DESIGN_VALID_RUNTIME_BLOCKED`, `may_execute=false`.
- `git diff --check` — PASS.
- Prior independent remote execution safety denial **remains binding**. We did not attempt launching CortenDesk by a renamed command, other runner, alternate namespace, scheduled process or security configuration change.
- No container run, image pull, user enrollment, token creation, server cutover, RustDesk endpoint change, exposed HTTPS tunnel, Safari session or Fleet Console integration has occurred.

## Next authorized experiment
1. Obtain a **legitimately permitted** isolated runner/environment for the v1.14.0 staging design. Do not override the previous denial.
2. Reverify pinned image against public metadata and local container cache, host/guest port isolation, ephemeral volumes and distinct test credentials.
3. Start **only** a disposable staging instance; run the existing localhost GET-only authentication-surface gate, then enroll one disposable RustDesk 1.5.0 client.
4. Verify actual browser WebSocket signalling, video/input, files, signed-in client address book and negative authentication cases.
5. Only with a separately approved authenticated HTTPS/WSS path, test Safari on physical iPhone and iPad outside LAN; no mandatory mobile RustDesk app or VPN.
6. No changes to production RustDesk clients/server until the above gates pass, and no Fleet Console integration during this stand-alone experiment.
