---
name: vf-daily-learning
description: Run the Velvet Factory end-of-day learning ritual — review conversations, update shared owner memory, promote durable facts. Lead seat asks every specialist to improve for tomorrow. Use at end of day, daily retro, or when the user asks for learning loop / זיכרון משותף / סוף יום.
---

# vf-daily-learning

Living office culture: specialists learn, improve, and feed shared memory — not static generic agents.

## When

- End of workday (after 18:00 Asia/Jerusalem)
- User asks: סוף יום, רטרו, למידה, זיכרון משותף, daily retro
- **One-time catch-up** before daily routine existed: `packages/vfops/hq/INITIAL-RETRO.md`
- Before closing a long multi-seat session

## Do this

1. Read `packages/vfops/hq/DAILY-RETRO.md` — lead seat checklist + **לולאת פרנסה** (פניות↔דגמים↔חומרים) + load block + history log. (First time only: `INITIAL-RETRO.md`.)
2. Skim today's conversations per seat (studio, growth, ops, production, research).
3. Fill the revenue-loop table only from real inquiries / print cards / materials — never invent demand or Insights.
4. Fill the load section only with measured hours; missing stays `~__` / «אין ספירה» — never invent hours.
5. Append a **log line** under the history section in `DAILY-RETRO.md` (keep prior days).
6. Write **one line minimum** to `packages/vfops/data/owner-memory.md` (format in `packages/vfmem/MEMORY-UPDATE.md`).
7. Open checkpoints for unfinished jobs: `packages/vfharness/state/` (set `component_state` when operational mode matters).
8. If same mistake twice → note for `AGENTS.md` ANTI-PATTERN (next catalog edit).
9. Weekly load pulse (subjective): `packages/vfops/hq/WEEKLY-LOAD.md` — does not replace the daily memory line.
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
