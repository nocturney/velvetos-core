# Core stability four axes — bounded embed (2026-09-07)

ADR-style playbook on **existing** packs. No second runtime. No Jinja. No repository_dispatch bus.

## Decision

Stabilize VelvetOS Core with four local fixes — not a sync/observability rewrite.

| # | Axis | Where | What |
|---|---|---|---|
| 1 | Atomic index swap | `packages/vfmem/scripts/vf_semantic_search.py` | Staging `.pkl.tmp` + `os.replace` before readers see `semantic_index.pkl` |
| 2 | Send preflight (light) | `scripts/vf_send_preflight.py` + `constitution/SEND.md` | Desk status + API key presence → JSON; `--gate` exit 2 = failover same turn |
| 3 | Retro day-block contract | `MEMORY-UPDATE.md` + `DAILY-RETRO.md` + `check-vfops-loop.py` | Dated `### YYYY-MM-DD` blocks require **מושב** / **למדנו** / **מקור** |
| 4 | Attach-core offline | `instances/*/scripts/attach-core.sh` | Keep stale vendor on network fail; `VELVETOS_CORE_OFFLINE` / `VELVETOS_CORE_PATH` |

## Explicitly rejected

- Exponential backoff wrapping every `check-*.py` (sensors are local file checks)
- `repository_dispatch` as the Core↔instance sync (attach-core / publish-instance stay)
- Pydantic/Zod for DAILY-RETRO (Markdown contract + sensor)
- Central Jinja/Handlebars template engine
- Unified live JSON observability stack

## Sensors

| Script | Needle |
|---|---|
| `check-vfmem.py` | `atomic_pickle_dump` / `os.replace` in semantic search |
| `check-vfmcp.py` | `vf_send_preflight.py` + SEND.md mention |
| `check-vfops-loop.py` | owner-memory dated blocks + DAILY-RETRO contract |
| `check-velvetos.py` | attach-core offline / `VELVETOS_CORE_PATH` / stamp |

## Verify

```bash
python3 scripts/vf_send_preflight.py --pretty
python3 scripts/vf_send_preflight.py --gate instagram   # expect exit 2 while needsAuth
VELVETOS_CORE_OFFLINE=1 VELVETOS_CORE_PATH=/workspace \
  instances/velvet-factory/scripts/attach-core.sh
python3 scripts/check-all.py
```
