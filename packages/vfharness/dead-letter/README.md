# Dead-letter — כשלים שלא נעלמים

מושב: `vfharness`. חוקה: `constitution/RISK.md`.  
תור: [`queue.json`](queue.json) · סכמה: [`schema.json`](schema.json).

## זרימה

`attempt` → `retry policy` → `fallback` → `downgrade where valid` → **dead-letter** אם לא נפתר.

## שדות חובה

- actionId
- jobOrContentId
- attemptedTool
- time
- failureSummary
- retries
- fallbackAttempted
- currentState
- nextSafeAction
- riskColor
- christianRequired

## חוקים

- Dead-letter ≠ forgotten.
- Watchdog סורק ומנסה לפתור אוטונומית כש־GREEN/YELLOW.
- RED → כריסטיאן בלבד.
- אסור למחוק פריט בלי `resolved: true` + סיבה.

CLI: `python3 scripts/vf_dead_letter.py list|add|resolve`
