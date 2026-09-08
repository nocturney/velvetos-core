# Production → Content continuity

נעילה 8.9.2026 — Christian.  
מושב: ייצור (`vfprod`) + צמיחה (`vfgrowth` / `vfom` / `vfcopy`). לא פק חדש.

## חוק

אם פורסם (או אושר לפרסום) תוכן מסוג:

- WIP / process / behind-the-scenes / printing / work-in-progress
- printer footage / «בתהליך»

של **מוצר אמיתי** —

**אסור לסגור את חוט התוכן** אחרי פרסום התהליך.

יש לפתוח/להשאיר follow-up:

`waiting_for_matching_print.done`

עד שמופיע אירוע/כרטיס אמיתי `print.done` שמתאים לאותו מוצר/job.

## Matching defensible

מותר לסגור follow-up רק עם התאמה אחת לפחות:

- אותו `jobId` / `correlationId`
- אותו מק״ט + קישור מקור זהה
- זהות כרטיס ייצור (`print card` path) זהה

**אסור** לקשר `print.done` אחר רק בגלל דמיון בשם.

## אחרי matching print.done — המשרד אוטונומית

1. לאתר / לבקש / לסווג finished-product media  
2. להכין finished-product content  
3. EDIT-GATE  
4. PREFLIGHT  
5. לבחור next eligible calendar slot  
6. להכין לפרסום (`approved` / queue)  
7. כש־IG tool ready — לפרסם לפי policy  
8. verify live (`liveVerified`)

חסרה תמונת מוצר מוגמר → לא ממציאים. משימה פתוחה:

`finished-media-required`

מופיע בבריף 07:00 אם רלוונטי.

## אחסון

[`data/production-content-followups.json`](data/production-content-followups.json)

## בדיקה

`python3 scripts/check-production-content.py`
