# Degraded Mode — בידוד רכיב + המשך Pipeline

שם רשמי ל־failover הקיים. **לא** runtime שני. ADR: `packages/velvetos/ADR-THREE-LAYERS.md`.

## הגדרה

כשרכיב (כלי MCP, API, סנסור, host) נכשל / `needsAuth` / חסום:

1. **מבודדים** אותו (לא מפילים את כל הצינור).
2. **מעבירים** את המשימה לגיבוי **באותו תור** (`constitution/ORCHESTRA.md`).
3. מסמנים `component_state: "Degraded"` ב־checkpoint (אם יש משימה פתוחה).
4. פולטים אירוע `tool.failover` או `sensor.degraded` (שדה `events` או ארטיפקט יומי).
5. כשחוזר — `sensor.recovered` + חזרה ל־`Processing` / `Idle`.

## מצבים

| `component_state` | משמעות |
|---|---|
| `Idle` | ממתין לעבודה |
| `Processing` | רץ כרגיל |
| `Degraded` | רכיב תקול; עובדים בגיבוי מוגדר |
| `Syncing` | מסנכרנים אחרי ניתוק / buffer |
| `Blocked` | שער אדם / ₪ / שדה חסר — לא ממשיכים לסגירה |

`status` של המשימה (`running`/`blocked`/`escalated`/`done`) נשאר כמו שהיה. `component_state` = מצב תפעולי של הרכיב/המשמרת.

## Safe Degradation — חוקים

- Failover ≠ המצאה (אין גוף חסום / ₪ / Insights).
- אין ארטיפקט = לא סוגרים את התור.
- Cloud Agent אפhemeral: אין להבטיח buffer מקומי ארוך; Edge אמיתי = Mac host (`vfmcp/HOST.md`).
- attach-core offline כבר קיים (`VELVETOS_CORE_OFFLINE` / stale vendor) — זה דפוס Edge/Kernel, לא broker.

## מה לא

- לא Event bus.
- לא «המערכת קרסה כי Canva נפל».
- לא להעלות לכריסטיאן דוח בושה על כלי שלא נצרך — מתקנים במשרד / פער בבריף.

## קישורים

- טבלאות כלי: `constitution/ORCHESTRA.md`
- Grok quota: `playbooks/grok-failover.md`
- Send preflight: `scripts/vf_send_preflight.py`
- חוזה אירועים: `packages/velvetos/schema/events.catalog.json`
