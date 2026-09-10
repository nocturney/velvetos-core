# מסירת מנהל · Office Control Plane · 2026-09-10

לא מערכת משרד שנייה. מקורות אמת: `office/control-plane.json`.

## מה פעיל עכשיו
- אין פעיל מחוץ ללולאה הרגילה

## מה ממתין
- `fu-G003-soccerball` · waiting_for_print_done

## מה נכשל (dead letter)
- אין

## חסום לבעלים (אדום/כתום בלבד)
- אין החלטת בעלים פתוחה

## הבא בתור
- הרץ watchdog
- סגור followups ready_for_finished_content דרך EDIT-GATE+PREFLIGHT
- אל תטריד את כריסטיאן על מדדים חלשים

## מה השתנה היום
- Office Control Plane מוטמע
- followups=1
- dead_letters=0

## מקורות סמכות
- **policy:** `constitution/CONSTITUTION.md + constitution/ORCHESTRA.md`
- **risk_policy:** `office/control/POLICY.md`
- **jobs:** `Google Sheet VF HQ · jobs (office/ledger/bindings.json) — local adapter cache office/ledger/live/jobs.csv via vf_office.py jobs pull`
- **jobs_bindings:** `office/ledger/bindings.json`
- **jobs_cache:** `office/ledger/live/jobs.csv`
- **media:** `packages/vfmedia/catalog.json + docs/MEDIA-VAULT.md`
- **content_calendar:** `packages/vfgrowth/CALENDAR.md`
- **content_approval:** `packages/vfgrowth/data/approval-queue.json`
- **production_completion:** `packages/vfprod/hq/cards/*.md via print.done`
- **office_loop:** `packages/vfops/LOOP.json`
- **manager_handoff:** `office/control/HANDOFF.json`
- **decisions:** `office/control/decisions.jsonl`
- **dead_letter:** `office/control/dead-letter.json`
- **followups:** `office/control/followups.json`
- **public_cta:** `constitution/PUBLIC_CTA.md`
- **publication_states:** `packages/vfigos/PUBLICATION-STATES.json`
- **instagram_capabilities:** `packages/vfigos/CAPABILITIES.json`
- **profile_desired:** `packages/vfigos/PROFILE-DESIRED.json`
- **feed_audit:** `packages/vfgrowth/data/feed-audit.json`
- **insights:** `packages/vfinsights/data/ (MCP-verified via vf_insights_ingest.py)`

## כלים מדולדלים
- אין חסם קשיח מדווח

## בטוח להמשך AI הבא
- `python3 scripts/vf_control_plane.py watchdog`
- `python3 scripts/vf_control_plane.py followups`
- `python3 scripts/vfops_loop.py brief`
- `python3 scripts/check-all.py`

## אסור לחזור
- invent ₪ or Insights
- auto-DM
- claim published without verification
- duplicate media catalog
- Meta Business Suite
- nationwide shipping
- bother Christian with weak metrics

## מדיניות עדכנית
- `constitution/CONSTITUTION.md`
- `constitution/ORCHESTRA.md`
- `office/control/POLICY.md`
- `office/control-plane.json`

## משימות ChatGPT (רק אחרי הוכחת נתיב)
להשאיר: Velvet Morning Brief, Velvet Research Seat — 06:15 live web research body; non-mechanical intelligence task, optional Velvet Publish Watch / hard-blocker alert
מועמדים לכיבוי אחרי הוכחה: Media Intake, Content Sprint, Insights/Office Review, Memory Hygiene, Opportunity Radar, WIP→Finished watcher, Dead-letter monitoring, routine watchdog, source-of-truth validation, Studio Pulse, Universal Intake, Invisible Work Detector, Failure Museum, Velvet Lab, Living Studio Skills Registry

אל תפנה לכריסטיאן על מדדים חלשים.
