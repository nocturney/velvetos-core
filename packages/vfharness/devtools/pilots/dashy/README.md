# Dashy read-only Velvet Office launchpad (Chris, 2026-10-08)

This is a navigation-only **static Dashy front end**, not a business control plane, database, authority source, proxy, or write adapter. The actual Control Center remains protected by IAP.

## Pinned supply chain

- Upstream: `Lissy93/dashy`, version `4.7.0` (MIT), official prebuilt asset `dashy-4.7.0.tar.gz`.
- Verified SHA-256: `e7b288c5f49ecc7f19a945b6c62fe235c857b5b325da7cfd25cfefa8061ee248`.
- Extract the verified release into `D:\\Velvet\\Tools\\DashyLaunchpad\\4.7.0\\app`. Never commit the vendor archive or compiled assets.
- Copy `conf.yml` over `app/dist/conf.yml` and `app/user-data/conf.yml`.
- Place `serve-readonly.js` alongside `app`, then start it with Node.js 24+ under the unprivileged `CHRIS\\Chris` login. The documented pilot task `Velvet-Dashy-ReadOnly-Launchpad` starts it at that user's logon. No SYSTEM service, Docker, Yarn, new cloud spend, or cross-host Office mutation.

## Security and verification

Only `GET` and `HEAD` static resources are served at `http://127.0.0.1:4000`. The HTTP server deliberately exposes **no application control API, configuration write route, server-side proxy, authentication flow, or outbound command**. `conf.yml` sets `disableConfiguration`, `preventWriteToDisk`, and `preventLocalSave`. All three links are verified, explicitly named canonical surfaces (Control Center, health endpoint, source repository).

Observed on 2026-10-08: `GET /` 200, `GET /conf.yml` 200, `GET /api/config` 404, `POST /conf.yml` 405, actual browser-rendered DOM includes Velvet Office and both canonical service links. The API health response is service-level readiness only and does **not** prove downstream VelvetOS integrations.

Rollback: stop and unregister the exact `Velvet-Dashy-ReadOnly-Launchpad` task, stop only the matching node process that runs `serve-readonly.js`, and remove the isolated Dashy directory after preserving evidence. Receipt: `packages/vfharness/state/dashy-launchpad-smoke-2026-10-08.json`. Runtime authority remains false.
