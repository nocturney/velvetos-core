# Schema — velvetos.control.v1

## Snapshot

```json
{
  "schema": "velvetos.control.v1",
  "generatedAt": "ISO-8601Z",
  "connection": "connected",
  "freshness": { "state": "live|fresh|stale|unknown", "verifiedAt": "…" },
  "flags": {},
  "modules": [],
  "capabilities": [],
  "health": [],
  "attention": [],
  "activity": [],
  "collections": {
    "jobs": { "state": "ready|needs_sync|conflict|unavailable|unknown", "items": [] | null, "count": 0 | null, "reason": null, "provenance": {} },
    "production": { "state": "unavailable", "items": null, "count": null, "reason": "…" },
    "content": {},
    "files": {},
    "agents": {},
    "models": {}
  }
}
```

### Collection honesty

| State | `items` | `count` | Meaning |
|-------|---------|---------|---------|
| `ready` | array (maybe empty) | `len(items)` | Authoritative adapter verified |
| `unavailable` / `needs_sync` / `conflict` / `unknown` | **`null`** | **`null`** | Must not be shown as “0 jobs” |

## Capability

```json
{
  "id": "…",
  "domain": "…",
  "label": "…",
  "status": "AVAILABLE|DEGRADED|NEEDS_AUTH|UNAVAILABLE|BLOCKED|APPROVAL_REQUIRED",
  "risk": "GREEN|YELLOW|ORANGE|RED",
  "provider": "…",
  "reason": null,
  "verifiedAt": "…",
  "provenance": { "source": "…", "verifiedAt": "…", "freshness": "…", "receipt": null, "authority": "canonical|projection|adapter-cache" }
}
```

Risk/gate derive from `office/control/POLICY.md` + capability `gate` fields — not from “tool seems connected”.

## Search

```json
{
  "results": [
    {
      "id": "…",
      "type": "…",
      "module": "…",
      "title": "…",
      "source": "…",
      "status": "…",
      "destination": "/jobs/…"
    }
  ]
}
```

`destination` must be a relative UI path under allowlisted prefixes (`/jobs/`, `/attention/`, …). No absolute URLs.

## Action request / receipt

Request:

```json
{
  "actionId": "…",
  "objectId": "…",
  "confirmation": "…",
  "idempotencyKey": "…"
}
```

Rejection / future success always carries:

```json
{
  "ok": false,
  "accepted": false,
  "completed": false,
  "error": { "code": "CAPABILITY_UNAVAILABLE", "message": "…" },
  "receipt": {
    "receiptId": "rcv_…",
    "actionId": "…",
    "idempotencyKey": "…",
    "outcome": "…",
    "at": "…"
  }
}
```

Same `idempotencyKey` + `actionId` + outcome → same `receiptId`.
