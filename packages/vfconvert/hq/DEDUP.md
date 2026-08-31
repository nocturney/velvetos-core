# DeDuplication — פנייה כפולה

מקור דפוס: Huginn DeDuplicationAgent.  
מושב: `vfconvert` · תרחיש: `vfe2b/scenarios/inquiry-chain.md`

## מתי

לפני `mail.replied` או לפני רישום פנייה חדשה בבריף block `02`.

## בדיקות (בסדר)

1. **Checkpoint** — `vfharness/state/*.json`: אותו `threadId` או `jobName` + event `inquiry.received` ב-7 ימים אחרונים.
2. **בריף** — `vfops/BRIEF*.md` block `02`: אותו subject / שם עבודה.
3. **Gmail** — אותו thread כבר קיבל `reply` מהמשרד השבוע (אם נקרא).

## אם כפול

- מצב: `worker_done` (לא `escalation`).
- `ארטיפקט`: שורה «כפילות — לא נשלח שוב» + מזהה המקורי.
- Event: `dedup.check` עם `"duplicate": true`.

## אם חדש

- Event: `dedup.check` עם `"duplicate": false`.
- המשך צינור רגיל.

## לא עושים

- לא ממזגים שרשורים שונים של אותו לקוח בלי אדם.
- לא מוחקים checkpoint ישן.
