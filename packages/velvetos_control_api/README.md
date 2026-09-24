# VelvetOS Control API v1

HTTP **projection gateway** over existing VelvetOS sources of truth.

This package is **not a Control Plane**, **not a runtime**, **not a queue**, **not a database**, and **not a source of truth**.
It is also not a replacement for existing CLI tools or a duplicated provider-integration layer.

```
VelvetOS canonical SoTs
        ↓
existing adapters / projections (vf_jobs_adapter, vf_control_plane, vf_autonomy, …)
        ↓
VelvetOS Control API  ← this package
        ↓
ChatGPT Site server-side adapter
        ↓
Control Center UI
```

## Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/health` | no | Service liveness (`service` vs `velvetos`) |
| `GET` | `/v1/snapshot` | yes | Full UI snapshot |
| `GET` | `/v1/search?q=` | yes | Federated search over projected domains |
| `GET` | `/v1/capabilities` | yes | Normalized capabilities |
| `POST` | `/v1/actions` | yes | Action contract — fail-closed in v1 |

Schema id: `velvetos.control.v1`.

## Authoritative sources

| Domain | Authority |
|--------|-----------|
| System / locks / SoT map | `office/control-plane.json` |
| Risk / Don't Bother Christian | `office/control/POLICY.md` |
| Capabilities | `packages/vfops/hq/capabilities.json` + `packages/vfigos/CAPABILITIES.json` |
| Attention | `vf_control_plane.owner_surface_items` + `vf_autonomy.blockers` |
| Activity | `office/control/HANDOFF.json`, `decisions.jsonl`, living-studio pulse/autonomy projections |
| Jobs | `scripts/vf_jobs_adapter.py` (Sheet canonical; CSV cache) |

**Unavailable in v1 (honest `items: null`):** production, content, files, agents, models.

Absent source ≠ verified empty. Verified empty jobs (`state=ready`, `items=[]`) is allowed only when the jobs adapter reports `ready`.

## Auth

Server-to-server only. Assume the consuming Site may be link-shared.

1. **Cloud Run IAM** — deploy with `--no-allow-unauthenticated` (primary).
2. **App bearer** — `VELVETOS_CONTROL_API_TOKEN` via Secret Manager (defense in depth).

Send `Authorization: Bearer <token>` or `X-Api-Key`. Credentials never in git. Endpoint contracts stay Bearer-shaped so a later scoped operator identity can replace the shared secret without UI/API churn.

## Actions (fail-closed)

Body:

```json
{
  "actionId": "…",
  "objectId": "…",
  "confirmation": "…",
  "idempotencyKey": "…"
}
```

Rules: unknown → reject; unavailable → `CAPABILITY_UNAVAILABLE`; denied → reject; missing approval/confirmation → reject; no shell / path / URL fetch from caller input. v1 does **not** invent write implementations — successful future calls must return a **receipt**; accepted ≠ completed.

## Extending (module contributions)

Register a contribution in `CONTRIBUTIONS.json` instead of editing a giant switch:

```json
{
  "id": "my-domain",
  "module": "velvetos_control_api.contributions.my_domain",
  "class": "MyDomainContribution",
  "domains": ["my-domain"]
}
```

Implement `project(ctx)` + `search(q, ctx)`. Project existing adapters only — never create a second store.

## Local use

```bash
export PYTHONPATH=packages
export VELVETOS_CONTROL_API_TOKEN=dev-only-not-for-git
python3 scripts/vf_control_api.py snapshot
python3 scripts/vf_control_api.py selftest
python3 -m velvetos_control_api --port 8080 --skip-isolation
```

Sensor: `python3 scripts/check-control-api.py`.

## Deployment

See [`DEPLOY.md`](DEPLOY.md). Prefer existing GCP / Cloud Run patterns. Isolate from Instagram mutation secrets.
