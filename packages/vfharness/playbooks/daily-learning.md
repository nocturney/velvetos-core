# Daily learning loop — living specialists

Module: `office-learning`.  
Agents are not static system prompts. Each day ends with review; each morning starts with inherited memory.

## When

- **Evening:** lead seat runs `vfops/hq/DAILY-RETRO.md`
- **During long tasks:** checkpoint per `EMBED.md` layer 4
- **After repeated failure:** ANTI-PATTERN line in `AGENTS.md`

## Loop

```
Day work (existing packs)
  → evening retro (all seats skim conversations)
  → promote 1 durable line to owner-memory.md
  → optional route/graph update if pattern repeats
  → morning brief reads memory block (not inbox)
  → next day starts smarter
```

## Per specialist

| Expert module | Evening question |
|---|---|
| `expert-social-booster` | Which hook/format landed? (verified only) |
| `expert-3d-model` | Which mesh issue recurred? slicer lesson? |
| `expert-trend-explorer` | Which source was worth keeping? stale link? |
| `expert-media-director` | Which storyboard/Canva path saved time? |

## Checkpoint fields (optional)

Add to `templates/checkpoint.schema.json` usage:

```json
"learned": ["one line for tomorrow"],
"ownerPreference": "only if user stated clearly"
```

## Permissions

- Write `vfops/data/owner-memory.md` — allow
- Write `AGENTS.md` ANTI-PATTERN — allow after 2nd failure
- Do not auto-send retro email unless lead asks

## Failover

No time for full retro → at minimum one line in `owner-memory.md` before session end.
