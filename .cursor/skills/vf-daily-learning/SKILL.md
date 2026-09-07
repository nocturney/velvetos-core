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

1. Read `packages/vfops/hq/DAILY-RETRO.md` — lead seat checklist + load block + history log. (First time only: `INITIAL-RETRO.md`.)
2. Skim today's conversations per seat (studio, growth, ops, production).
3. Fill the load section only with measured hours; missing stays `~__` / «אין ספירה» — never invent hours.
4. Append a **log line** under the history section in `DAILY-RETRO.md` (keep prior days).
5. Write **one line minimum** to `packages/vfops/data/owner-memory.md` (format in `packages/vfmem/MEMORY-UPDATE.md`).
6. Open checkpoints for unfinished jobs: `packages/vfharness/state/`.
7. If same mistake twice → note for `AGENTS.md` ANTI-PATTERN (next catalog edit).
8. Weekly load pulse (subjective): `packages/vfops/hq/WEEKLY-LOAD.md` — does not replace the daily memory line.

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
