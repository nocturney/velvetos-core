# Systematic debugging — שורש לפני תיקון

מקור דפוס: [obra/superpowers `systematic-debugging`](https://github.com/obra/superpowers/tree/main/skills/systematic-debugging).  
רתמה: `vfharness` · אחרי תיקון: `verification-before-claim.md` · סוכן «נהיה גרוע»: `agent-architecture-audit.md`.

## חוק ברזל

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

בלי שלב 1 — אין להציע תיקון. תיקון סימפטום = כישלון.

## מתי חובה

- סנסור אדום (`check-*.py`)
- כלי MCP / Gmail / Canva / Drive שנכשל
- התנהגות סוכן לא צפויה / דילוג על פלייבוק
- «תיקון מהיר» שלא החזיק מעמד
- לחץ זמן (חירום מגביר ניחושים — לא מקצר חקירה)

## ארבעה שלבים (בסדר)

### 1. חקירת שורש

1. קרא את הודעת השגיאה / פלט הסנסור במלואה (שורה, קובץ, קוד).
2. שחזר באופן עקבי — מה בדיוק מפעיל?
3. בדוק שינוי אחרון רלוונטי (`git log` / ארטיפקט מעבר / checkpoint).
4. גבש השערת שורש אחת בכתב (משפט).

### 2. דפוס כשל

| דפוס | סימן | כיוון |
|---|---|---|
| רגרסיה | עבד אתמול | diff אחרון / embed אחרון |
| סביבה | רק Cloud / רק Mac | PATH, auth, MCP `needsAuth` |
| חוזה שבור | JSON/מדריך מול סנסור | schema / `check-*.py` מצפה |
| כלי למטה | timeout / 403 | failover לפי `ORCHESTRA` — לא להמציא גוף |
| סוכן דילג | פלייבוק קיים לא נקרא | `skill-first` + checkpoint |

### 3. תיקון ממוקד

- שנה רק מה שמוכיח את ההשערה.
- אחרי שינוי קטלוג/כלל/פק: `python3 scripts/check-all.py`.
- כשל סנסור → תיקון אחד → אם נכשל שוב: הסלמה עם תבנית escalation (לא ניחוש שלישי).

### 4. אימות

- הרץ את אותו שחזור מתוך שלב 1.
- אל תטען «תוקן» בלי פלט סנסור / לוג.
- רשום checkpoint תחת `packages/vfharness/state/` אם המשימה ארוכה.

## דגלים אדומים

| מחשבה | מציאות |
|---|---|
| «ברור מה לשנות» | בלי שחזור = ניחוש |
| «נוסיף retry ונמשיך» | מעלים סימפטום |
| «אין גוף / אין דירוג — נמציא» | נעול: `X ₪` / «אין ספירה» / «אין גוף» |
| «הכלי למטה — נחכה לבעלים» | failover באותו תור |

## לא

- OpenClaw / runtime שני «כדי לדברג»
- `npx skills` לתיקון מקומי
- טענת הצלחה בלי ראיה

## קשר

- `playbooks/brainstorm-gate.md` — לפני בנייה חדשה
- `playbooks/verification-before-claim.md` — לפני «סיימתי»
- `playbooks/skill-first.md` — לפני פעולה
- `playbooks/agent-architecture-audit.md` — כשל מבני חוזר
