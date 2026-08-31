# Cloud Environment — every VelvetOS instance repo

Every **frontend** repo (`VelvetOS — <Business>`) must ship `.cursor/environment.json` so Cloud Agents clone **VelvetOS Core** on boot.

## Required file

Path: `.cursor/environment.json`

```json
{
  "name": "VelvetOS — <Business display name>",
  "install": "./scripts/attach-core.sh",
  "repositoryDependencies": [
    "github.com/nocturney/velvetos-core"
  ]
}
```

## What it does

| Field | Effect |
|---|---|
| `install` | After checkout, runs `./scripts/attach-core.sh` → `vendor/velvetos-core/` |
| `repositoryDependencies` | GitHub token for the Cloud VM can read **core** (needed if core is private) |

`vendor/velvetos-core/` stays **gitignored** — not duplicated in the instance repo.

## New instance checklist

1. Copy scaffold from `instances/velvet-factory/` or `instances/_template/`
2. Include `scripts/attach-core.sh` + `.gitignore` with `vendor/velvetos-core/`
3. Add `.cursor/environment.json` (copy template; set `name`)
4. Publish with `scripts/publish-instance.sh`
5. Sensor: `python3 scripts/check-velvetos.py`

Template: `instances/_template/.cursor/environment.json`
