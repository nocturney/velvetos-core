# VelvetOS Instagram Publisher — Cloudflare Free

Purpose: replace OpenPost scheduling with a small fail-closed scheduler while keeping Instagram Graph as the publication target.

## Runtime
- Cloudflare Worker Free, cron every minute.
- D1 stores jobs/events.
- Workers KV stores approved publication media as write-once, hash-bound objects.
- Secrets: CONTROL_TOKEN, SCHEDULE_HMAC_KEY, META_ACCESS_TOKEN, IG_USER_ID.
- No token or private media is committed.

## Job states
scheduled -> publishing -> published_verified
scheduled/retry -> publishing -> retry (pre-publish failure only)
publishing -> reconcile_required (failure at/after media_publish; never blind-retry)
retry -> dead_letter after MAX_ATTEMPTS
scheduled/retry -> cancelled

A D1 lease prevents two cron invocations from taking the same job. Every immutable job is HMAC-bound; DB tampering produces dead_letter.

## Media contract
PUT /v1/media/{key}?sha256={hex} with admin Bearer and the exact bytes.
GET /media/{key} is public for Meta fetch. The upload hashes bytes before KV write.
Before publication the scheduler reads KV again and checks the stored bytes/hash against the job.
Max supported object: 25 MiB (KV limit).

## Control API
GET /healthz is public.
GET /v1/jobs and GET /v1/jobs/{id} require CONTROL_TOKEN.
POST /v1/jobs schedules exact content.
POST /v1/jobs/{id}/cancel cancels only scheduled/retry jobs.
POST /v1/run manually processes due jobs (operator/testing only).

## Google Calendar mirror
The dedicated Google Calendar `אינסטגרם` is a one-way operational mirror of D1 jobs. Cloudflare Publisher remains the only schedule source of truth. Calendar edits never change publication time or authorization. The bridge code lives in `../apps_script_calendar_bridge/` and is designed to run every 5 minutes inside the owner's Google account. Mirror failure is reported operationally but does not cancel an already scheduled publication.

## Safety
Scheduler acceptance is not publication proof. A job becomes published_verified only after media_publish returns a media id and a Graph read-back returns a permalink.
Any ambiguous failure after the publish boundary becomes reconcile_required, not retry.
New content should carry normal VelvetOS publication approval evidence. The 2026-09-24 OpenPost migration has a separately recorded migration_authorization because the original approval lives in the OpenPost record.

## Deployment
1. Authenticate Wrangler once with the owner's Cloudflare account.
2. Create D1 database and KV namespace; replace the two REPLACE_AFTER_* ids in wrangler.toml.
3. Apply schema.sql remotely.
4. Put the four secrets above. Generate CONTROL_TOKEN and SCHEDULE_HMAC_KEY randomly; copy Meta token / IG user id from existing Secret Manager without printing them.
5. Deploy and verify /healthz.
6. Upload every approved media object; GET it back and verify SHA-256.
7. POST the job; read it back and verify scheduled_at/status.
8. Only after steps 5-7 pass, cancel the corresponding OpenPost schedule.
9. After due time, require published_verified and cross-check Instagram read-back.

Local smoke is safe because the test job is scheduled for 2099 and never calls Meta.
