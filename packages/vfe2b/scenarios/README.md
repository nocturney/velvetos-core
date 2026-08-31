# vfe2b — Scenarios (Huginn pattern)

מקור דפוס: [huginn/huginn](https://github.com/huginn/huginn) — Scenarios = גרף סוכנים שמור.  
**לא** מתקינים Huginn. Cursor מריץ את התרחיש כמשמרת אחת.

רשימת מכונה: [`scenarios.json`](../scenarios.json)

## תרחישים

| id | קובץ | צוות | Events עיקריים |
|---|---|---|---|
| `morning-digest` | [`morning-digest.md`](morning-digest.md) | morning-brief | `calendar.read` → `mail.read` → `brief.written` → `mail.sent` |
| `inquiry-chain` | [`inquiry-chain.md`](inquiry-chain.md) | inquiry | `inquiry.received` → `fields.extracted` → `draft.ready` → `mail.replied` |
| `weekly-links` | [`weekly-links.md`](weekly-links.md) | research | `links.listed` → `link.reviewed` → `embed.done` → `brief.block05` |
| `content-live` | [`content-live.md`](content-live.md) | content | `brief.ready` → `canva.done` → `ig.send` / `ig.failover` |

## איך מריצים

```
@vfe2b run <job> — scenario morning-digest
```

או פותחים את קובץ התרחיש ועוקבים אחרי הגרף. כל צומת = checkpoint event ב-`vfharness/state/<task-id>.json`.

## חוקים

- מצב סיום אחד: `worker_done` / `escalation` / `decision_gate` (`crews/run.md`).
- `working?` = `python3 scripts/check-staleness.py` + סנסורים.
- אין fan-out של ₪ או שליחה.
