# Retro → Signal — מהרטרו לאות בבריף

הופך את יומן ה־Daily Retro מתיעוד סביל ל**אותות תפעוליים** לבריף.  
לא מדדים חלשים לבעלים. לא «רמה נמוכה». ADR: `packages/velvetos/ADR-THREE-LAYERS.md`.

## מתי

סוף רטרו ערב **או** לפני בריף 07:00:

```bash
python3 scripts/vf_retro_signals.py --write
```

כותב: `packages/vfops/data/retro-signals.json`  
אירוע קטלוג: `retro.anomaly`

## מה סורקים (מקורות קיימים בלבד)

| מקור | מה מחפשים |
|---|---|
| `vfops/data/owner-memory.md` | בלוקי יום אחרונים — חזרות על כשל/חסר/צוואר בקבוק |
| `vfops/hq/DAILY-RETRO.md` (לוג תחתית) | «מה לא» / סנסור אדום |
| `vfharness/state/*.json` | `component_state=Degraded` או `unresolved` עם sensor/failover |
| `vfops/data/research.md` | שורות failover X→Y |

## סוגי אות (kind)

| kind | briefSlot | משמעות |
|---|---|---|
| `sensor_repeat_fail` | 01 | אותו סנסור/כלי נכשל ≥2 פעמים בחלון |
| `inquiry_lag` | 01 | פניות פתוחות / «לא נסגר» חוזר |
| `ingest_bottleneck` | 05 | רישום נתונים / Insights / memory חסר מקור |
| `failover_streak` | 05 | failover חוזר — מצב Degraded מתמשך |
| `none` | — | אין חריגה — קובץ עם `signals: []` |

## חוקים

- רק מטקסט שכבר על הדיסק. **אין** המצאת Insights / ₪ / מגמות.
- אות = שורת **פער תפעולי למשרד** (חריץ 01 החלטה או 05 משרד) — לא נזיפה לבעלים.
- Christian lock: לא «רמה נמוכה»; לא נתיחת איכות אחרי פרסום.
- Human gates נשארים: ₪ / WhatsApp / בוסט.

## צריכה בבריף

`BRIEF-SLOTS.md`: חריץ 01/05 קוראים את `retro-signals.json` אם קיים ו־`generatedAt` מהיום (Asia/Jerusalem).  
ריק = אין שורת אות (לא ממלאים רעש).

## קישורים

- רטרו: `DAILY-RETRO.md`
- למידה: `vfharness/playbooks/daily-learning.md`
- מודול: `velvetos/modules/office-learning.md`
