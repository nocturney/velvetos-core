# Dead-letter — compatibility pointer

**SOURCE OF TRUTH:** `office/control/dead-letter.json`  
**CLI / API:** `scripts/vf_control_plane.py` · `record_dead_letter` / `list_dead_letters`  
**Thin wrapper (compat):** `python3 scripts/vf_dead_letter.py list|add|resolve`

`queue.json` here is a **pointer only** (`sourceOfTruth` + empty `items`).  
Do **not** write dead-letter items into this pack. Sensors fail red if this file holds real authoritative items.

Policy: `office/control/POLICY.md` (mirror: `constitution/RISK.md`).  
Watchdog: `python3 scripts/vf_control_plane.py watchdog` (wrapper: `vf_office_watchdog.py`).
