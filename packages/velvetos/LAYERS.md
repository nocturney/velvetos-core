# שלוש שכבות VelvetOS — SoC

ADR: `ADR-THREE-LAYERS.md`. לא runtime שני. לא broker.

```
┌─────────────────────────────────────────────────────────┐
│  Office / HQ — אינטלקט + שליטה                          │
│  desk · instance frontend · brief · CRM · send via tools│
├─────────────────────────────────────────────────────────┤
│  Kernel — velvetos-core                                 │
│  laws · seats · packs · modules · event contracts ·     │
│  computational sensors (check-*.py)                     │
├─────────────────────────────────────────────────────────┤
│  Edge / nerves — אופציונלי עתידי (לא שם הריפו)          │
│  host Mac / רצפה · local buffer · sync · degraded local │
└─────────────────────────────────────────────────────────┘
```

## Separation of Concerns

| שכבה | עושה | לא עושה |
|---|---|---|
| **Edge** | אוגר מטריקות/לוגים מקומית; מסנכרן כשחוזר חיבור; מבודד רכיב תקול | לא מחליט ₪; לא שולח WhatsApp ללקוח; לא מחליף חוקה |
| **Kernel** | מגדיר חוזים, מודולים, סנסורי שלמות קטלוג, מצבי `component_state` | לא HTTP API חי; לא IoT daemon בתוך הריפו |
| **Office / HQ** | קשרי לקוחות, תצוגות, החלטות, שליחת Gmail/IG דרך כלים, retro→signal | לא מדפיס מ־HQ; לא אוטו־DM; לא בוסט בלי ראש צוות |

## ביצוע מול ניהול

- **ביצוע תפעולי נמוך** (failover כלי, checkpoint, sensor suite, attach-core offline) = Kernel + harness.
- **ניהול עסקי** (פנייה→הצעה, לוח תוכן, כסף מאומת, החלטות) = Office / HQ על הפקים.
- **חומרה/רצפה** = Edge בלבד כשקיים מקור אמיתי — עד אז אין להמציא טלמטריה.

## חוזה נתונים

אירועים ופקודות: `schema/events.catalog.json` (+ `schema/event-envelope.schema.json`).  
אין תלות קוד ישירה בין Edge↔Office — רק ארטיפקטים/סכמות על דיסק (או שדה `events` ב־checkpoint).

## מצבי רכיב (`component_state`)

`Idle` · `Processing` · `Degraded` · `Syncing` · `Blocked`  
ראה `vfharness/templates/checkpoint.schema.json` + `playbooks/skillstate.md`.

## Degraded Mode

כלי/רכיב נפל → מבודדים → ממשיכים ב־failover → מסמנים `Degraded`.  
פלייבוק: `vfharness/playbooks/degraded-mode.md` · טבלאות: `constitution/ORCHESTRA.md`.

## Human gates (תמיד)

₪ מכירה · WhatsApp ללקוח · בוסט · Print מ־HQ — **אדם / ראש צוות** (human-in-loop). אוטומציה עד טיוטה ושיבוץ — כן; סגירה בלי שער — לא.
