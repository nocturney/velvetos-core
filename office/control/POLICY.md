# Don't Bother Christian

מדיניות משטח בעלים ל־Office Control Plane.  
מקור חוקה: `constitution/CONSTITUTION.md` + `constitution/ORCHESTRA.md`.

כריסטיאן רואה רק **החלטה אמיתית**. מדדים חלשים, תיקוני איכות פנימיים, כשלונות MCP עם failover עובד — נשארים פנימיים.

## ירוק — לבצע אוטונומית

- סיווג מדיה / ארכיון
- עדכון מצב פנימי
- טיוטת קופי פנימית
- קריאה / חיפוש
- תחזוקת handoff
- רשימת פערים פנימית
- תיקוני איכות שגרתיים

## צהוב — לבצע + לדווח בבריף

- הכנת תוכן
- ארגון Drive/מדיה
- עדכון תוכנית לוח
- עדכון מצב תפעולי לא-כספי
- מעקב production→content
- תיקוני watchdog דטרמיניסטיים

## כתום — להכין בלבד, לא לבצע

- הודעה חיצונית חדשה
- טענה עובדתית ציבורית שדורשת אימות
- שינוי מדיניות
- פעולת פרסום חריגה
- כל דבר שחסר לו שער חובה

## אדום — אישור כריסטיאן

- רכישה / תשלום
- כל עלות חדשה חוזרת / paid API call / billing-capable resource ללא אישור מפורש - `NO_NEW_RECURRING_COST`
- שינוי מחיר
- פעולה חיצונית הרסנית
- הרשאת פרסום שדורשת בעלים
- חסם קשיח בלי failover
- מחיקה בלתי הפיכה — `policy_id: external.irreversible.delete`
- שינוי, הרחבה או ביטול הרשאת גישה/שיתוף חיצונית — `policy_id: external.permission.mutate`
- התחייבות עסקית שלא מכוסה במדיניות
- עלות חוזרת חדשה / מנוי / תוכנית / משאב בתשלום בלי אישור בעלים מפורש
- קריאת API בתשלום, workload usage-based או billing-capable resource בלי cost preflight ואישור נדרש
- `COST_UNKNOWN` — כשהעלות, overage או incremental cost לא הוכחו

## משטח בעלים (read model)

תור האישורים הקנוני נשאר `packages/vfgrowth/data/approval-queue.json`.  
