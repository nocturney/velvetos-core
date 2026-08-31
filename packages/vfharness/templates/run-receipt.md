# קבלת משמרת

Replay קריא של כרטיס `crews/run.md` + checkpoint. לא runtime שני — audit trail על הדיסק.

```
משמרת: <job name>
task_id: <checkpoint task_id>
צוות: <crew>
מושב: <lead | studio | growth | ops | production>
מצב: worker_done | escalation | decision_gate
דופק: working | blocked | idle
אימות: <sensor or field or חסר>
ארטיפקט: <path or «אין»>
מה נעשה: <one or two lines, cited>
חסר: <field or «אין»>
הבא: <HQ tool send | human WhatsApp | lead ₪ | none>
```

## תכנון (plan preview)

רשימת `planned_steps` מה-checkpoint — מה שה-coordinator תכנן לפני ביצוע:

1. …
2. …

## שער (gate)

אם `status` = `blocked` ויש `gate`:

- **kind:** decision_gate | escalation | approval
- **waiting_for:** …
- **reason:** …

אין `worker_done` עד שהשער נפתח. ₪ ווואטסאפ לקוח נשארים אדם.

## מקור דפוס

[Open Multi-Agent](https://github.com/open-multi-agent/open-multi-agent) — coordinator, checkpoint, durable approval.  
אצלנו: `vfharness/state/` + צוות קיים אחד. ראה `playbooks/oma-patterns.md`.
