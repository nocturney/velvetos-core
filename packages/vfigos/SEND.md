# Instagram publication / scheduling — current authority

Machine SoT: `packages/vfigos/PUBLISHER.json`.

Canonical route: `VF creative/publication gates -> exact approved bytes -> Cloudflare Instagram Publisher -> official Meta Instagram Graph API -> live Graph verification`.

- Scheduler/queue: **cloudflare-instagram-publisher**.
- OpenPost: **FROZEN**, zero active schedules.
- Canva/vfcanva: **FORBIDDEN/REMOVED**, never fallback.
- Instagram MCP bridge: read/Insights/independent live verification, not scheduler authority.

Before a job is created, bind the exact content/package hash, final caption/media bytes and current owner/publication authorization. Upload only approved bytes with expected SHA-256. The Worker re-verifies media hashes before Meta.

Pre-publish failures may retry. Any ambiguity at/after `media_publish` becomes `reconcile_required` and must not be blindly retried.

`scheduled != publishing != published_verified`. Only a live Graph id + permalink upgrades to `published_verified`.

Current migrated job: `VF-OCTOPUS-20260927-CAROUSEL`, 2026-09-27 12:00 Asia/Jerusalem (09:00Z), six media objects. Pre-boundary checks passed; the first scheduled write through this route remains unproven until due time.
