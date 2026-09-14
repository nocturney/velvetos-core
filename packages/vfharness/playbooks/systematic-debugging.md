# Systematic debugging — שורש לפני תיקון

מקור דפוס: [obra/superpowers `systematic-debugging`](https://github.com/obra/superpowers/tree/main/skills/systematic-debugging).  
רתמה: `vfharness` · לפני תיקון פק/סנסור: `sensor-first-tdd.md` · אחרי תיקון: `verification-before-claim.md` · סוכן «נהיה גרוע»: `agent-architecture-audit.md`.

## חוק ברזל

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

בלי שחזור/סיגנל pass-fail — אין להציע תיקון. תיקון סימפטום = כישלון.

## אבחון מדורג

לא כל תקלה צריכה חקירה כבדה. בחר את המסלול הקטן ביותר שמספק ראיה אמינה:

### Light diagnosis

מותר כשכבר יש שחזור דטרמיניסטי/סנסור אדום, הכשל מקומי, אין סיכון auth/security/data, ויש לכל היותר השערת שורש אחת סבירה:

1. שחזר פעם אחת.
2. כתוב השערה אחת.
3. שנה את המינימום שמוכיח/מפריך אותה.
4. הרץ את אותו שחזור + regression proof.

אם התיקון הראשון לא מחזיק — **לא** ממשיכים לנחש; עוברים למסלול המלא.

### Full diagnosis

חובה כשאחד מאלה מתקיים: שחזור לא יציב, שורש לא ברור, כשל חוצה כמה רכיבים/ספקים, כלי production/provider, הרשאות/auth, data loss/security, התנהגות שחוזרת, או תיקון ראשון שנכשל.

## מתי חובה

- סנסור אדום (`check-*.py`)
- כלי MCP / Gmail / Canva / Drive שנכשל
- התנהגות סוכן לא צפויה / דילוג על פלייבוק
- «תיקון מהיר» שלא החזיק מעמד
- לחץ זמן (חירום מגביר ניחושים — לא מקצר חקירה)

## ארבעה שלבים (מסלול מלא)

### 1. חקירת שורש + לולאת משוב

1. קרא את הודעת השגיאה / פלט הסנסור במלואה (שורה, קובץ, קוד).
2. שחזר באופן עקבי — מה בדיוק מפעיל?
3. **בנה לולאת משוב צמודה** לפני תיקון (דפוס mattpocock `diagnosing-bugs`): בדיקה אדומה / CLI עם fixture / פקודת סנסור אחת / replay של קלט. בלי סיגנל pass/fail על *הבאג הזה* — אל תתקן.
4. בדוק שינוי אחרון רלוונטי (`git log` / ארטיפקט מעבר / checkpoint).
5. גבש השערת שורש אחת בכתב (משפט).

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

## Sanitization לפני שיתוף evidence

לוגים, HAR, dumps ו־provider traces הם ראיה — אבל לא מדביקים אותם עיוור לצ׳אט/Issue/commit. לפני שיתוף:

- הסר tokens, cookies, `Authorization` headers, API keys ו־session IDs;
- הסר/צמצם PII ונתוני לקוח שאינם נחוצים לשחזור;
- שמור רק את החלון המינימלי שמוכיח את הכשל;
- לעולם אל תכניס secret לגיט כדי «להראות את הבעיה».

## דגלים אדומים

| מחשבה | מציאות |
|---|---|
| «ברור מה לשנות» | בלי שחזור = ניחוש |
| «נוסיף retry ונמשיך» | מעלים סימפטום |
| «אין גוף / אין דירוג — נמציא» | נעול: `X ₪` / «אין ספירה» / «אין גוף» |
| «הכלי למטה — נחכה לבעלים» | failover באותו תור; wizard רק אם נשאר צעד אנושי אמיתי |

## לא

- OpenClaw / runtime שני «כדי לדברג»
- `npx skills` לתיקון מקומי
- טענת הצלחה בלי ראיה

## קשר

- `playbooks/sensor-first-tdd.md` — אדום לפני תיקון פק/סנסור
- `playbooks/brainstorm-gate.md` — לפני בנייה חדשה
- `playbooks/verification-before-claim.md` — לפני «סיימתי»
- `playbooks/skill-first.md` — לפני פעולה
- `playbooks/agent-architecture-audit.md` — כשל מבני חוזר
- `playbooks/human-step-wizard.md` — כשנשאר חוסם אנושי אמיתי
