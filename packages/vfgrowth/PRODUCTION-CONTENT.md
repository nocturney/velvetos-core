# Production → Content continuity

נעילה 8.9.2026 — Christian.  
מושב: ייצור (`vfprod`) + צמיחה (`vfgrowth` / `vfom` / `vfcopy`). לא פק חדש.

## מקור אמת

**Canonical store:** `office/control/followups.json`  
**Sync / matching:** `python3 scripts/vf_control_plane.py followups` · `sync_followups` · `defensible_match`

`data/production-content-followups.json` הוא **מצביע תאימות בלבד** (`sourceOfTruth`) — לא מאחסן follow-ups סמכותיים.

## חוק

אם פורסם (או אושר לפרסום) תוכן מסוג:

- WIP / process / behind-the-scenes / printing / work-in-progress
- printer footage / «בתהליך»

של **מוצר אמיתי** —

**אסור לסגור את חוט התוכן** אחרי פרסום התהליך.

יש לפתוח/להשאיר follow-up במצב:

`waiting_for_print_done` (legacy label: `waiting_for_matching_print.done`)

עד שמופיע אירוע/כרטיס אמיתי `print.done` שמתאים לאותו מוצר/job.

## Matching defensible

`defensible_match(followup, print_row)` — מותר לסגור/לקדם רק עם התאמה אחת לפחות:

- אותו `jobId`
- אותו `correlationId` / `correlation_id`
- אותו `printCardPath` / `print_card_path`
- **או** אותו `sku` + אותו `sourceLink`

**אסור** לקשר `print.done` אחר רק בגלל דמיון בשם.

## אחרי matching print.done — המשרד אוטונומית

1. `waiting_for_print_done` → `ready_for_finished_content`
2. אם אין finished media → `waiting_for_media` (`finished-media-required`)
3. EDIT-GATE
4. PREFLIGHT
5. `suggested_slot` מ־`CALENDAR.md`
6. `publication=not_published` עד `liveVerified` עם `verification_evidence`
7. כש־IG tool ready — לפרסם לפי policy
8. verify live (`liveVerified`)

חסרה תמונת מוצר מוגמר → לא ממציאים. משימה פתוחה:

`finished-media-required` / `waiting_for_media`

מופיע בבריף 07:00 אם רלוונטי.

## בדיקה

`python3 scripts/check-production-content.py`  
`python3 scripts/vf_control_plane.py selftest`
