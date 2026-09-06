# Handoff — מסירת סשן

מקור דפוס: [mattpocock/skills `handoff`](https://github.com/mattpocock/skills).  
ב־HQ: checkpoint תחת `packages/vfharness/state/<task-id>/` — לא רק קובץ ב־`/tmp`.

## מתי

- משמרת נגמרת באמצע job
- העברה בין מושבים / סוכן חדש
- אחרי `decision_gate` לפני שהאדם חוזר

## מה לכתוב

שמור ב־`state/<task-id>/handoff.md` (או עדכן `progress.md` + `findings.md`):

1. **מטרה** — משפט אחד
2. **מה כבר נעשה** — קישורים לנתיבים/PR/ארטיפקטים (לא לשכפל גופים ארוכים)
3. **מה הבא** — הצעד הבא הקונקרטי
4. **שערים פתוחים** — ₪ / אדם / כלי `needsAuth`
5. **Suggested skills** — איזה `.cursor/skills/…` לקרוא מיד
6. **נעילות** — מה אסור (אוטו־DM, Print, המצאת ₪)

## חוקים

- אל תשכפל תוכן שכבר ב־ADR / plan / diff — רק הפניה
- צנזר סודות / מפתחות / PHI
- אם המשתמש נתן מטרת סשן הבא — התאם את המסמך

## קשר

- `PLANNING-FILES.md` · `templates/checkpoint.schema.json`
- `playbooks/verification-before-claim.md` לפני «מסרתי והכל ירוק»
