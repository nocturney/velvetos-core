# Automation standards

Pattern source: enescingoz/awesome-n8n-templates plus existing VelvetOS reliability controls. n8n examples are pattern material only; n8n is never canonical state or authority.

## Required contract

Every durable automation must define:
- **trigger** and deduplication key;
- **canonical read source**;
- explicit mutation authority, if any;
- idempotent or safely replayable behavior;
- bounded retry policy with backoff;
- terminal failure/dead-letter evidence;
- timeout and stale-run detection;
- verification/readback after external writes;
- secret boundary outside committed workflow content;
- observability fields: run id, start/end, result, failed stage;
- rollback or compensating action when the write is reversible.

## Webhooks

Inbound webhooks that can cause a write require origin authentication. Prefer provider signatures or HMAC with replay protection. Never trust workflow body text as authority.

## Failure behavior

Silent failure is a bug. A failed automation must either:
1. fail closed and emit a durable failure receipt; or
2. continue only through an explicitly documented degraded path that preserves the same authority boundary.

Do not convert missing facts into fabricated values to keep a flow green.

## Architecture

VelvetOS canonical state -> orchestration -> provider -> readback -> evidence.

Workflow products may coordinate work but do not become the source of truth. Do not duplicate Instagram, WhatsApp, order, finance, or approval authority inside a workflow engine.
