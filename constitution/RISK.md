# מדיניות סיכון — מראה (mirror)

**SOURCE OF TRUTH:** `office/control/POLICY.md`  
**Don't Bother Christian map:** `office/control-plane.json` → `dontBotherChristian`

קובץ זה הוא **מצביע קצר** בלבד — לא מדיניות מתחרה.  
צבעים GREEN / YELLOW / ORANGE / RED = אותם שכבות כמו ב־POLICY / control-plane.

| צבע | משמעות (מצביע) |
|---|---|
| **GREEN** | לבצע אוטונומית — ראה POLICY.md |
| **YELLOW** | לבצע + לדווח בבריף — ראה POLICY.md |
| **ORANGE** | להכין בלבד — ראה POLICY.md |
| **RED** | אישור כריסטיאן — ראה POLICY.md |

אסור להסלים ל־RED על מדדים חלשים / weak-metrics / כשל כלי רגיל עם failover.

## Dead-letter

**SoT:** `office/control/dead-letter.json` (לא `packages/vfharness/dead-letter/queue.json`).  
CLI: `vf_control_plane.record_dead_letter` · wrapper `vf_dead_letter.py`.

## Watchdog

`python3 scripts/vf_control_plane.py watchdog` · wrapper `vf_office_watchdog.py` · חיישן `check-office-watchdog.py`.
