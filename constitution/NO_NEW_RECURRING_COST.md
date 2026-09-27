# VelvetOS Policy - NO_NEW_RECURRING_COST

Status: **CANONICAL COST AUTHORITY**
Default target: **zero new recurring cost**
Enforcement: **FAIL CLOSED ON COST**

## 1. Purpose

מדיניות זו מחייבת את כל רכיבי VelvetOS, כלי הפיתוח, סוכנים, שירותים, integrations, plugins, APIs, מודלים, ספקי ענן ופרויקטי ניסוי.

ברירת המחדל היא:

**אין ליצור עלות חדשה חוזרת, חיוב חדש, מנוי חדש או שימוש בשירות בתשלום ללא אישור מפורש מראש מבעל המערכת.**

היעד התפעולי הוא:

**אפס עלות חדשה חוזרת כברירת מחדל.**

## 2. Default Rule

כאשר קיימת חלופה מספקת מסוג:

- Open Source
- Local
- Self-hosted
- Existing licensed capability
- Existing already-paid infrastructure
- Existing approved API/service

יש להעדיף אותה על פני שירות חדש בתשלום.

אין לבחור בפתרון בתשלום רק משום שהוא:

- קל יותר להתקנה
- מהיר יותר לבדיקה
- hosted
- convenient
- recommended by vendor
- כולל free trial
- כולל credits זמניים

## 3. Absolute Prohibition Without Explicit Approval

ללא אישור מפורש מראש אסור:

1. ליצור subscription בתשלום.
2. להפעיל paid plan.
3. להזין כרטיס אשראי או אמצעי תשלום.
4. להפעיל billing account חדש.
5. לבצע upgrade מתוכנית חינמית לתוכנית בתשלום.
6. ליצור resource שידוע או סביר שייצר חיוב חדש.
7. לבצע API call בתשלום.
8. להשתמש ב-token/API key שמחויב לפי שימוש עבור workload חדש.
9. לאשר marketplace purchase.
10. להתחיל trial שהופך אוטומטית לתשלום.
11. להגדיל quota אם ההגדלה עלולה ליצור חיוב.
12. להפעיל model endpoint, GPU cloud instance, hosted database או SaaS בתשלום.
13. לרכוש license, seat, credit pack או usage bundle.
14. להעביר workload לשירות חיצוני בעל pricing usage-based בלי אישור.

**עצם קיומו של API key, billing account או כרטיס שכבר מחובר אינו נחשב אישור להשתמש בו.**

## 4. Explicit Approval Requirement

חריגה מהמדיניות תקפה רק אם בעל המערכת מאשר במפורש את כל הפרטים הבאים:

- שם השירות או הספק
- מטרת השימוש
- סוג החיוב
- עלות צפויה
- תקרת עלות
- האם העלות חד-פעמית או חוזרת
- משך האישור
- הסביבה המורשית
- האם מותר Production
- האם מותר auto-renew
- האם מותר usage-based billing

אישור כללי כגון "תתקין מה שצריך" או "תשתמש בכלים" אינו מהווה אישור ליצור חיוב.

## 5. Cost Preflight Before Installation

לפני התקנה, הפעלה או חיבור של כל רכיב חיצוני חדש יש לבצע Cost Preflight.

הבדיקה חייבת לקבוע:

### A. License
- האם הקוד חינמי?
- איזה license חל עליו?
- האם שימוש מסחרי מותר?
- האם קיימת מגבלה על self-hosting?

### B. Runtime Cost
- האם השירות יכול לרוץ מקומית?
- האם נדרש cloud resource?
- האם נדרש GPU/CPU hosted?
- האם קיימת עלות storage, traffic או database?

### C. API Cost
- האם נדרשים API calls?
- האם הם free?
- האם free tier מוגבל?
- מה קורה לאחר חריגה?
- האם billing מופעל אוטומטית?

### D. Subscription
- האם נדרש account בתשלום?
- האם יש trial בלבד?
- האם ה-trial הופך אוטומטית למנוי?

### E. Hidden/Secondary Cost
יש לבדוק גם egress, storage, managed database, logging, monitoring, hosted embeddings, inference, external search, email/SMS, webhook delivery services ו-paid marketplace integrations.

## 6. Cost Classification

כל רכיב חדש חייב לקבל אחת מהתוויות:

- `FREE_LOCAL` - ללא תשלום חדש ורץ מקומית.
- `FREE_SELF_HOSTED` - התוכנה ללא עלות רישוי חדשה, אך צורכת infrastructure קיים.
- `EXISTING_PAID_CAPABILITY` - משתמש בשירות שכבר משולם ומאושר. שימוש חדש עדיין חייב להיבדק אם הוא עלול להגדיל את החשבון.
- `FREE_TIER_LIMITED` - חינמי רק עד quota מסוים. נדרשים quota control, monitoring ו-hard cap אם אפשר.
- `PAID_OPTIONAL` - ניתן לעבוד בחינם, אך קיימים features בתשלום. יש לנעול את ההטמעה למסלול החינמי.
- `PAID_REQUIRED` - דורש תשלום. `BLOCKED_BY_NO_NEW_RECURRING_COST` עד לקבלת אישור מפורש.
- `COST_UNKNOWN` - אין מידע מספק. `BLOCKED` עד לבירור.

## 7. Approval Gates

### Gate 1 - Discovery
לפני בחירת כלי יש לקבוע האם הוא מסוגל לפעול ללא חיוב חדש. אם לא - יש לחפש חלופה חינמית.

### Gate 2 - Installation
לפני התקנה חייב להיות מתועד cost classification, license, deployment model, APIs required ו-billing risk. ללא מידע זה אין להתקין.

### Gate 3 - Credentials
לפני הכנסת API key או credentials יש לוודא האם המפתח משויך לחשבון בתשלום, האם הפעולה יכולה ליצור usage cost והאם קיימת quota. אם כן - נדרש אישור מפורש.

### Gate 4 - First External Call
לפני הקריאה החיצונית הראשונה לשירות שעשוי להיות בתשלום יש לבצע בדיקה נוספת. אם pricing אינו חד-משמעי - לא מבצעים את הקריאה.

### Gate 5 - Production
גם כלי שעבר Pilot בחינם אינו עובר אוטומטית ל-Production. יש לבדוק מחדש volume, rate, storage, traffic ו-expected monthly cost.

## 8. Free Trials

Free trial אינו נחשב חינם אם נדרש אמצעי תשלום, יש auto-renew, השירות הופך אוטומטית ל-paid, אין תקרת שימוש קשיחה או תנאי החיוב אינם ברורים. ברירת המחדל: לא מתחילים trial כזה ללא אישור.

## 9. Usage-Based APIs

API המחויב לפי tokens, requests, compute time, bandwidth, generated images, inference, embeddings, storage או messages נחשב paid service גם אם העלות ל-call בודד נמוכה. ללא אישור אסור להשתמש בו.

## 10. Existing Paid Services

כאשר VelvetOS כבר משתמש בשירות בתשלום, אין להסיק שהרחבת השימוש חופשית. לפני שימוש חדש יש לבדוק האם הוא נכלל במנוי הקיים, האם יש quota, האם מדובר ב-metered usage והאם השימוש החדש יכול להעלות את החשבון. אם קיימת אפשרות לעלייה בעלות - נדרש אישור.

## 11. Local Resource Cost

CPU מקומי, GPU מקומי, RAM, disk ו-network מקומי אינם נחשבים עלות חוזרת חדשה לצורך חסימת התקנה רגילה. אם צפויה צריכת משאבים חריגה - מאות GB, עומס GPU קבוע, שירות 24/7, שימוש חריג בחשמל או models גדולים מאוד - יש לתעד אותה.

## 12. Preference Order

1. Existing native capability
2. Existing approved local tool
3. Open-source local
4. Open-source self-hosted
5. Existing approved paid capability ללא עלות נוספת
6. Free external service עם hard limits
7. Paid service - רק לאחר אישור

## 13. Fallback Rule

אם רכיב שנבחר דורש תשלום בלתי צפוי:

1. לעצור רק את הרכיב החסום.
2. לסמן `BLOCKED_BY_NO_NEW_RECURRING_COST`.
3. לחפש חלופה חינמית.
4. להמשיך בכל שאר שלבי הפרויקט שאינם תלויים בו.
5. לפנות לבעל המערכת רק אם אין חלופה סבירה.

## 14. No Silent Cost Escalation

אסור לבצע בשקט מעבר `Local -> Hosted`, `Free -> Trial -> Paid`, `Small/local model -> Paid frontier API` או `Self-hosted DB -> Managed cloud DB`, גם אם המעבר פותר תקלה טכנית.

## 15. Model Routing Rule

כאשר אפשר לבצע workload באמצעות model מקומי מתאים, יש להעדיף אותו כאשר הדבר עומד בדרישות האיכות. אין לבצע escalation ל-paid model רק בגלל latency, convenience, quality assumption או temporary local failure ללא אישור או policy קיימת שמתירה זאת.

## 16. Logging and Evidence

עבור כל רכיב חדש יש לשמור לפחות:

- cost classification
- source/license
- free/paid mode selected
- API dependencies
- expected recurring cost
- approval evidence אם קיימת חריגה

במקרה של חריגה מאושרת יש לתעד `service`, `approved_by`, `approval_date`, `cost_limit`, `scope`, `expiration`.

## 17. Monthly Cost Drift Check

לכל רכיב חיצוני או cloud-connected שממשיך לפעול יש לבצע periodic review של pricing changes, free-tier changes, quota changes, new mandatory plans ו-discontinued free features. אם כלי שהיה חינמי הופך בתשלום, אין להמשיך אוטומטית; יש לעצור אם בטוח, לחפש חלופה, ושימוש בתשלום דורש אישור חדש.

## 18. Emergency Exceptions

חריג חירום מותר רק כאשר יש סיכון ממשי לאובדן מידע, יש צורך בפעולת recovery ואין חלופה חינמית זמינה בזמן הנדרש. גם אז אין לבצע חיוב בלי אישור אם ניתן להשיג את הבעלים. אם אין אפשרות לקבל אישור, ברירת המחדל נשארת לא ליצור חיוב. אין emergency billing אוטומטי.

## 19. Explicitly Forbidden Assumptions

אסור להניח: "זה רק כמה סנטים", "בטח יש free tier", "החשבון כבר מחובר", "כבר יש billing", "נבטל אחר כך", "זה רק לבדיקה", "ה-trial חינם" או "כנראה זה כלול". כל אחד מהמקרים דורש verification.

## 20. Enforcement Rule

כל agent, automation, developer workflow או implementation task ב-VelvetOS חייב לפעול לפי:

> **VERIFY COST BEFORE INSTALLATION.**
> **VERIFY COST BEFORE FIRST PAID-CAPABLE CALL.**
> **NEVER CREATE A CHARGE WITHOUT EXPLICIT OWNER APPROVAL.**

כאשר יש ספק: **FAIL CLOSED ON COST.**

## 21. Final Policy Statement

VelvetOS רשאי באופן אוטונומי להתקין, לבדוק, להריץ, להגדיר, לשלב, לבצע POC ולבצע benchmark רק כאשר הדבר אינו יוצר עלות חדשה חוזרת או חיוב חדש.

כל פעולה שעלולה ליצור חיוב, מנוי, usage fee או API cost חדש דורשת אישור מפורש מראש מבעל המערכת.

## 22. Compatibility and action-scoped evidence

The machine contract may accept more than one preflight evidence shape, but the policy decision is identical. Detailed schema evidence and compact action-oriented evidence both bind to the same classifications, fail-closed states, incremental-cost rule, paid-overage controls, and explicit owner approval boundary.

A compact preflight must identify the component and action, carry current evidence and a check date, and state whether incremental cost, automatic paid overage, a hard cap, or paid optional features are possible/enabled. This compatibility exists to preserve existing evidence while integrating newer production routers; it does not weaken the policy.

A monthly cost-drift review remains required for external or cloud-connected components. No silent cost escalation is permitted when changing provider, model tier, hosting mode, storage class, retention, concurrency, polling cadence, or scheduled frequency.
