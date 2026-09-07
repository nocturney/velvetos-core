# ADR — שלוש שכבות · חוזה אירועים · state · Degraded · retro→signal

**סטטוס:** מקובל (2026-09-07)  
**מושב:** ראש צוות · `@studio-operations` · `@workflow-architect`  
**פקים:** `velvetos` · `vfharness` · `vfops` · `constitution`

## הקשר

הוצע ש־`velvetos-core` יהפוך ל«מערכת עצבים» (אירועים בזמן אמת / חומרה) ו־HQ ל«אינטלקט».  
הליבה היום היא **קטלוג Cursor-OS** (חוקים, מושבים, פקים, מודולים, סנסורי שלמות) — לא runtime / broker.  
שכתוב השם בלי פיצול שכבות היה יוצר בלבול מוסדי ו־runtime שני (נעול).

## החלטה

מאמצים **שלוש שכבות** + חוזה אירועים על דיסק + state מפורש + Degraded Mode + retro→signal — **בלי** broker, **בלי** להפוך את הריפו Core ל־nervous-system runtime, **בלי** pipeline בלי אדם על ₪ / WhatsApp send.

| שכבה | תפקיד | איפה |
|---|---|---|
| **Edge / nerves** (אופציונלי עתידי) | אירועי רצפה/host, buffer מקומי, sync שקט | Mac host / רצפה — **לא** שם הריפו Core |
| **Kernel** | חוקים, מודולים, חוזי אירועים, סנסורי שלמות | `velvetos-core` |
| **Office / HQ** | החלטות, CRM, תצוגות, שליחה, retro→פעולה | desk + instance frontend |

מסמך שכבות: `LAYERS.md` · חוזה: `schema/events.catalog.json` · state: `vfharness/templates/checkpoint.schema.json` (`component_state`) · Degraded: `vfharness/playbooks/degraded-mode.md` + `constitution/ORCHESTRA.md` · signals: `vfops/hq/RETRO-SIGNALS.md` + `scripts/vf_retro_signals.py`.

## נעול במפורש

1. **לא** Event bus / orchestrator שני (CrewAI, Orca, amux, repository_dispatch כ־bus).
2. **לא** להגדיר מחדש את `velvetos-core` כ־nervous-system runtime.
3. **לא** «אפס התערבות ידנית» על ₪ מכירה / WhatsApp ללקוח / בוסט / Print מ־HQ.
4. Failover ≠ המצאת גוף / ₪ / Insights.
5. Offline-first אמיתי = host מקומי; Cloud Agent אפhemeral — buffer שם מוגבל.

## חלופות שנדחו

| חלופה | למה לא |
|---|---|
| Core = עצבים, HQ = אינטלקט (שני ריפואים runtime) | הופך את הקטלוג ל־daemon; סותר LOCK + no-second-runtime |
| Message broker (Redis/NATS) | runtime שני; אין מקור אירועי רצפה חי |
| Zero-touch inquiry→close | סותר human-in-loop על כסף ושליחה |

## השלכות

- פקים מדברים באירועים מתועדים (JSON על דיסק / שדה `events` ב־checkpoint) לפי הקטלוג.
- כל משימה ארוכה מסמנת `component_state` (`Idle`/`Processing`/`Degraded`/`Syncing`/`Blocked`).
- רטרו יומי מזין `vf_retro_signals.py` → אותות לבריף (חריץ 01/05) — לא נתיחה לבעלים על מדדים חלשים.
- כלי שנפל = מצב `Degraded` רשמי + failover לאותו תור.

## סנסורים

`check-velvetos.py` · `check-vfharness.py` · `check-vfops-loop.py`

## אימות

```bash
python3 scripts/vf_retro_signals.py --write
python3 scripts/check-velvetos.py
python3 scripts/check-vfharness.py
python3 scripts/check-vfops-loop.py
python3 scripts/check-all.py
```
