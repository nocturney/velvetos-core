---
name: vf-daily-learning
description: Run the Velvet Factory scoped learning/retro loop when meaningful work changed — review only participating domains, capture learning candidates, and promote durable facts through the evidence gate. Use after a meaningful correction/failure/handoff, at close of a material work session, or when the user asks for learning loop / זיכרון משותף / retro.
---

# vf-daily-learning

Living office culture: specialists learn, improve, and feed shared memory — not static generic agents.

## When

- A meaningful owner correction, failure/failover, workflow/policy change, new material/revenue signal, or unfinished multi-step handoff creates something worth learning.
- User asks: סוף יום, רטרו, למידה, זיכרון משותף, retro.
- Before closing a long multi-seat session **only when** it produced new evidence/candidates.
- **One-time catch-up** before the old routine existed: `packages/vfops/hq/INITIAL-RETRO.md`.
- No standing 18:00/daily clock and no empty retro for untouched seats.

## Do this

1. Read `packages/vfops/hq/DAILY-RETRO.md` — lead seat checklist + **לולאת פרנסה** (פניות↔דגמים↔חומרים) + load block + history log. (First time only: `INITIAL-RETRO.md`.)
2. Identify which seats/domains actually changed or received new evidence; review only those conversations/artifacts. Untouched seats are skipped.
3. Fill the revenue-loop table only from real inquiries / print cards / materials — never invent demand or Insights.
4. Fill the load section only with measured hours; missing stays `~__` / «אין ספירה» — never invent hours.
5. When the run has a meaningful observation/candidate/handoff, append a **log line** under the history section in `DAILY-RETRO.md` (keep prior history). Do not create an empty log merely to satisfy cadence.
6. If there is a meaningful signal, create/update the bounded learning candidate or checkpoint. Write `owner-memory.md` only after the promotion gate; if there is no durable learning, record no memory line.
7. Open checkpoints for unfinished jobs: `packages/vfharness/state/` (set `component_state` when operational mode matters).
8. If same mistake twice → note for `AGENTS.md` ANTI-PATTERN (next catalog edit).
9. Weekly load pulse (subjective): `packages/vfops/hq/WEEKLY-LOAD.md` — operational logging is separate from durable-memory promotion.
10. **Retro → signal:** `python3 scripts/vf_retro_signals.py --write` → brief slots 01/05 (`RETRO-SIGNALS.md`; kinds include `model_demand` / `material_signal`). No owner shame / weak Insights upward.

## Per expert module

| Job | Open |
|---|---|
| Social Booster | `vfgrowth/experts/SOCIAL-BOOSTER.md` |
| 3D model | `vfprod/experts/3D-MODEL.md` |
| Trend explorer | `vfresearch/experts/TREND-EXPLORER.md` |
| Media director | `vfom/experts/MEDIA-DIRECTOR.md` |

## Route

```bash
python3 scripts/vfmem.py who "daily retro"
python3 scripts/vfmem.py who "social booster"
```

## Do not

- Invent ₪, Insights, or trends in memory
- Store secrets or personal/medical/legal paths
- Send blast email unless lead explicitly asks
- Install a second runtime for "learning"

## Morning handoff

Next `vf-morning-brief` reads `owner-memory.md` block — not Gmail inbox.

## Verification

Before claiming completion, verify the routed target state or run the existing package/route sensor. Configuration, a draft, a command exit, or an agent statement alone is not success. If live/provider evidence is unavailable, report the state as `UNPROVEN`/blocked rather than COMPLETE.
