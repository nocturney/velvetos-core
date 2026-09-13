# Daily learning loop — living specialists

Module: `office-learning`.  
Agents are not static system prompts. Each day ends with review; each morning starts with inherited memory.

This loop now feeds the evidence-backed lifecycle in `learning-lifecycle.md`; a daily observation is not automatically a durable rule.

## When

- **Evening:** lead seat runs `vfops/hq/DAILY-RETRO.md`
- **During long tasks:** checkpoint per `EMBED.md` layer 4
- **After repeated failure:** create/update a learning candidate; promote an `ANTI-PATTERN` only when the existing repetition/human gate is met

## Loop

```
Day work (existing packs)
  -> evening retro (all seats skim conversations)
  -> emit/update bounded learning candidates
  -> accumulate concrete evidence / owner corrections
  -> accept, reject, absorb, promote, or prune
  -> promote only durable lessons to owner-memory / playbook / skill / rule
  -> optional route/graph update if pattern repeats
  -> morning brief reads governed memory block (not inbox)
  -> next day starts smarter
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
"learningCandidates": ["learn-..."],
"ownerPreference": "only if user stated clearly"
```

## Promotion gate

Before adding a new skill/rule/playbook, classify the candidate:

`Save | Improve then Save | Absorb into <existing> | Drop`

Prefer updating an existing canonical capability over creating another overlapping skill.

## Permissions

- Write `vfops/data/owner-memory.md` — allow when the memory governance gate is satisfied
- Write `AGENTS.md` ANTI-PATTERN — allow after the established repetition/human gate
- Do not auto-send retro email unless lead asks
- Never promote unverified model inference as owner preference

## Failover

No time for full retro -> at minimum persist the bounded observation in the task checkpoint. Do not force-promote it to durable memory merely to avoid losing it.

## Verification

```bash
python3 scripts/check-learning-lifecycle.py
```
