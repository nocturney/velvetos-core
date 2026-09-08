# מסירת מנהל · Office Control Plane · 2026-09-08

לא מערכת משרד שנייה. מקורות אמת: `office/control-plane.json`.

## מה פעיל עכשיו
- אין פעיל מחוץ ללולאה הרגילה

## מדיה (פאזות נפרדות · קטלוג יחיד)
- total=`400` · inbox=`398` · source=`2`
- רשום בלבד=`398` · אומת ונקלט=`2` · נבדק חזותית=`0`
- intake=`Idle` · activation=`True`
- registered ≠ verified ≠ visually_reviewed · validate≠monitoring · upload≠approval · no invented SKU/job association

## מה ממתין
- אין

## מה נכשל (dead letter)
- אין

## חסום לבעלים (אדום/כתום בלבד)
- אין החלטת בעלים פתוחה

## הבא בתור
- הרץ watchdog
- המשך קליטת מדיה אוטומטית (intake run) — לא רק validate
- סגור followups ready_for_finished_content דרך EDIT-GATE+PREFLIGHT
- אל תטריד את כריסטיאן על מדדים חלשים
- Instagram stays needsAuth until Meta email verify + long-lived token

## מה השתנה היום
- Office Control Plane מוטמע
- followups=0
- dead_letters=0
- media_catalog_items=400
- media_inbox=398
- media_source=2
- media_verified=2
- media_registered_only=398
- media_visually_reviewed=0

## מקורות סמכות
- **policy:** `constitution/CONSTITUTION.md + constitution/ORCHESTRA.md`
- **risk_policy:** `office/control/POLICY.md`
- **jobs:** `office/ledger/live/jobs.csv`
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

## כלים מדולדלים
- אין חסם קשיח מדווח

## בטוח להמשך AI הבא
- `python3 scripts/vf_control_plane.py watchdog`
- `python3 scripts/vf_control_plane.py followups`
- `python3 scripts/vf_control_plane.py simulate --scenario failover`
- `python3 scripts/vfops_loop.py brief`
- `python3 scripts/check-all.py`
- `python3 scripts/vfmedia.py validate`
- `python3 scripts/vfmedia.py intake status`
- `python3 scripts/vfmedia.py intake selftest`

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
להשאיר: Velvet Morning Brief, optional Velvet Publish Watch / hard-blocker alert
מועמדים לכיבוי אחרי הוכחה: Media Intake, Content Sprint, Insights/Office Review, Memory Hygiene, Opportunity Radar, WIP→Finished watcher, Dead-letter monitoring, routine watchdog, source-of-truth validation

אל תפנה לכריסטיאן על מדדים חלשים.
