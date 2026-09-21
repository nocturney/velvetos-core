# task_plan — OpenPost release watch 2026-09-21

> תבנית: `packages/vfharness/templates/task_plan.md`

**task_id:** openpost-release-watch-2026-09-21  
**pack:** vfigos  
**משמרת:** OpenPost tip watch HOLD  
**נפתח:** 2026-09-21

## מטרה

Watch-only record that upstream OpenPost tip is **v5.2.2** while the merged pin stays **v4.35.0**. Decision `PIN_HOLD_REVIEW_REQUIRED`. No pin bump, no staging/production promotion, no owner notify.

## שלבים

- [x] **1. תכנון** — vfmem + graft + harness; existing PR #279 inspected.
- [x] **2. מקור** — current main OPENPOST authority + GitHub Releases API tip v5.2.2.
- [x] **3. ביצוע** — new 2026-09-21 hold-watch on current main; #279 superseded for tip currency only. Draft PR #298.
- [x] **4. אימות** — relevant sensors PASS; pin-hold proof PASS; check-all 70/76 local PIL/starlette import gaps.
- [x] **5. סגירה** — checkpoint + draft PR #298.

## החלטות

| תאריך | החלטה | למה |
|---|---|---|
| 2026-09-21 | Open new PR instead of updating #279 | #279 is based on stale main and still describes LIVE_BLOCKED / productionHost v4.35.0. Current merged authority is LIVE_VERIFIED + `v4.35.0-vfbridge6`. |
| 2026-09-21 | Keep pin v4.35.0 | Watch-only. No requiredChecks PASS on any gap tag. |
| 2026-09-21 | ownerNotify=false | Explicit job gate. No email. |

## חסומים / escalation

`decision_gate`: next hop is staging review of at least v4.36.3. No promotion this turn.
