# VelvetOS Instagram Publisher — Cloudflare

Status: **ACTIVE PRIMARY SCHEDULER** for Velvet Factory Instagram scheduled publication.

This Worker replaces OpenPost scheduling. Instagram publication itself uses Meta Graph API. OpenPost is frozen and must not receive new schedules.

## Runtime

- Cloudflare Worker at `velvetos-instagram-publisher.velvetos-vf.workers.dev`.
- Cron every minute.
- D1 stores jobs/events.
- Workers KV stores approved publication media as write-once, hash-bound objects.
- Secrets: `CONTROL_TOKEN`, optional read-only `SNAPSHOT_TOKEN`, `SCHEDULE_HMAC_KEY`, `META_ACCESS_TOKEN`, `IG_USER_ID`.
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
- Read endpoints `GET /v1/meta-health`, `/v1/runtime`, `/v1/jobs`, `/v1/jobs/{id}` accept `CONTROL_TOKEN` or the separate read-only `SNAPSHOT_TOKEN` when configured.
- Write endpoints never accept `SNAPSHOT_TOKEN`.
- `POST /v1/jobs` schedules exact content with `CONTROL_TOKEN`. New jobs require `authorization.kind=policy_authorization_v1` plus `authorization.policy_context`; the Worker computes the caption digest itself, projects standing authorization from runtime config, and evaluates `policy_id: instagram.publish` before accepting the job.
- `POST /v1/jobs/{id}/cancel` cancels only `scheduled`/`retry` jobs.
- `POST /v1/run` manually processes due jobs.

## Safety

Scheduler acceptance is not publication proof. A job becomes `published_verified` only after `media_publish` returns a media id and Graph read-back returns a permalink.

`policy_id: instagram.publish` is evaluated twice: once before a new job is accepted, and again after the D1 lease/HMAC check immediately before fingerprint/publish work. The second decision receipt is written to the event log before any Meta Graph publish mutation. `DENY` becomes `dead_letter`; `REQUIRE_OWNER_APPROVAL` becomes `waiting_approval`; neither path reaches `publishJob()`.

Stored pre-cutover jobs without `policy_context` are evaluated only through the bounded legacy-compatibility branch. New jobs cannot use the legacy authorization kinds.

The first fully scheduled write through this route remains production evidence to observe at execution time. Until then, pre-publish transport, media integrity, queue state and Meta read-back are verified.

## Migration evidence

The OpenPost schedule for `VF-OCTOPUS-20260927-CAROUSEL` was moved to this publisher for 2026-09-27 12:00 Asia/Jerusalem. OpenPost was cleared to no active schedules. The migration files in `migrations/2026-09-24-openpost/` preserve the exact content/package/media hashes and source evidence.

## Publish fingerprint guard · LIVE

The 72-hour fingerprint guard (same definition as `packages/vfigos/approval/publish_fingerprint.py`) is **live in production** as of 2026-09-27. D1 contains `publish_fingerprints`; the Worker checks the fingerprint before any Meta write and records both `published_verified` and `reconcile_required` outcomes.

Deployment order remains fail-closed for future environments:

1. `npx wrangler d1 execute velvetos-instagram-publisher --remote --file=migrations/d1/0001_publish_fingerprints.sql`
2. verify the table exists;
3. deploy the Worker.

The production deploy that activated the guard is Worker version `c302b0a1-4d03-4db6-9ff9-056ee69166d7`.

### New job authorization contract · Stage 4D

`authorization.policy_context` supplies only evidence that the Worker cannot derive from immutable job bytes. The Worker ignores any caller attempt to supply standing authorization and derives that value from runtime configuration.

New routine jobs use exactly one `CONTENT_READY` evidence envelope. The envelope aggregates exact artifact identity + Product Truth + brand + copy + visual QA + rights/privacy + render/transport evidence. It is **not** an authorization engine: `policy_id: instagram.publish` remains the only ALLOW / DENY / REQUIRE_OWNER_APPROVAL authority.

```json
{
  "kind": "policy_authorization_v1",
  "evidence": "CONTENT_READY exact envelope",
  "policy_context": {
    "risk_class": "LOW",
    "forbidden_effects": [],
    "content_ready": {
      "schema_version": "velvet.content_ready.v1",
      "status": "PASS",
      "bindings": {
        "content_id": "G100",
        "package_sha256": "<64hex>",
        "copy_sha256": "<64hex>",
        "media_sha256s": ["<64hex>"]
      },
      "evidence": {
        "product_truth": {"status": "PASS", "ref": "<receipt-ref>", "sha256": "<64hex>", "failure_mode": null, "reason": null},
        "brand": {"status": "PASS", "ref": "<receipt-ref>", "sha256": "<64hex>", "failure_mode": null, "reason": null},
        "copy": {"status": "PASS", "ref": "<receipt-ref>", "sha256": "<64hex>", "failure_mode": null, "reason": null},
        "visual_qa": {"status": "PASS", "ref": "<receipt-ref>", "sha256": "<64hex>", "failure_mode": null, "reason": null},
        "rights_privacy": {"status": "PASS", "ref": "<receipt-ref>", "sha256": "<64hex>", "failure_mode": null, "reason": null},
        "render_transport": {"status": "PASS", "ref": "<receipt-ref>", "sha256": "<64hex>", "failure_mode": null, "reason": null}
      },
      "repair_targets": [],
      "retry_targets": [],
      "hard_blockers": [],
      "owner_surface": "NONE",
      "validated_at": "<ISO-8601>"
    },
    "human_approval": null
  }
}
```

With runtime standing authorization enabled, `risk_class=LOW` + exact-bound `CONTENT_READY=PASS` produces one `instagram.publish` decision and no per-asset owner approval. A routine quality failure is repaired/retried upstream and the envelope is regenerated; only a real hard blocker surfaces to the owner. For a non-routine decision that genuinely requires owner approval, `human_approval` must bind `content_id`, `package_sha256` and the Worker-computed raw UTF-8 caption SHA-256. A mismatched approval is `DENY`, not a fallback to standing authorization.

For migration safety only, the Worker accepts the previous seven-gate `policy_context` for jobs whose server-recorded `created_at` is before `2026-10-04T00:00:00Z`. This is bounded compatibility, not the new authoring contract.

## Canonical policy gate · LIVE

`policy_id: instagram.publish` is live in production as of 2026-09-27 on Worker version `c4e82e25-2949-47ce-9446-4222012ff81e`. Cutover evidence is stored at `packages/velvetos/policy/reports/stage1-instagram-publish-cutover.json`. The deployment was verified with an empty scheduled queue, healthy cron and Meta read-back, plus a negative control proving a new legacy-form scheduling request is rejected before persistence.
