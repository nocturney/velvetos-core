# VelvetOS Instagram Publisher — Cloudflare

Status: **ACTIVE PRIMARY SCHEDULER** for Velvet Factory Instagram scheduled publication.

This Worker replaces OpenPost scheduling. Instagram publication itself uses Meta Graph API. OpenPost is frozen and must not receive new schedules.

## Runtime

- Cloudflare Worker at `velvetos-instagram-publisher.velvetos-vf.workers.dev`.
- Cron every minute.
- D1 stores jobs/events.
- Workers KV stores approved publication media as write-once, hash-bound objects.
- Secrets: `CONTROL_TOKEN`, `SCHEDULE_HMAC_KEY`, `META_ACCESS_TOKEN`, `IG_USER_ID`.
- No token or private media is committed.

## Job states

`scheduled -> publishing -> published_verified`

`scheduled/retry -> publishing -> retry` for pre-publish failures only.

Any failure at or after `media_publish` becomes `reconcile_required`; never blind-retry an ambiguous publish.

A D1 lease prevents two cron invocations from taking the same job. Every immutable job is HMAC-bound; DB tampering becomes `dead_letter`.

## Media contract

`PUT /v1/media/{key}?sha256={hex}` with admin Bearer and exact bytes.

`GET /media/{key}` is public for Meta fetch. The Worker hashes bytes on upload and verifies KV bytes/hash again before publication.

## Control API

- `GET /healthz` public.
- `GET /v1/meta-health` authenticated Graph read-back.
- `GET /v1/jobs` and `GET /v1/jobs/{id}` require `CONTROL_TOKEN`.
- `POST /v1/jobs` schedules exact content.
- `POST /v1/jobs/{id}/cancel` cancels only `scheduled`/`retry` jobs.
- `POST /v1/run` manually processes due jobs.

## Safety

Scheduler acceptance is not publication proof. A job becomes `published_verified` only after `media_publish` returns a media id and Graph read-back returns a permalink.

The first fully scheduled write through this route remains production evidence to observe at execution time. Until then, pre-publish transport, media integrity, queue state and Meta read-back are verified.

## Migration evidence

The OpenPost schedule for `VF-OCTOPUS-20260927-CAROUSEL` was moved to this publisher for 2026-09-27 12:00 Asia/Jerusalem. OpenPost was cleared to no active schedules. The migration files in `migrations/2026-09-24-openpost/` preserve the exact content/package/media hashes and source evidence.
