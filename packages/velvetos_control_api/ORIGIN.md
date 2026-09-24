# velvetos_control_api

VelvetOS Control API — HTTP **projection gateway** (`velvetos.control.v1`) for the Control Center UI.

Projects existing Office Control Plane, jobs adapter, capability registries, and autonomy blockers.
Not a Control Plane, not a runtime, not a queue, not a database, not a source of truth.

Write-up: [`README.md`](README.md) · Deploy: [`DEPLOY.md`](DEPLOY.md)

| | |
|---|---|
| Origin slug | `unknown` |
| Codebase | (this HQ repo; not an Origin tree) |
| Clone | `(none)` |
| vendor | `hq-native` |
| Sensor | `scripts/check-control-api.py` |
| CLI | `python3 scripts/vf_control_api.py` |

Do not commit secrets. Do not invent prices or Insights.
Do not mount Instagram mutation credentials on this service.
HQ sends Gmail/Instagram via tools (`constitution/SEND.md`) — this API does not bypass that.
