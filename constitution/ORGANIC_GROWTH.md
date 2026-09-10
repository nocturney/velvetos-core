# Organic Growth Control Plane

מושב: **צמיחה** על פקים קיימים (`vfgrowth` · `vfprod` · `vfcopy` · `vfcanva` · `vfbriefux` · `vfinsights` · `vfsales` · `vfops` · `vfom` · `vfigos`).  
לא פק חדש. לא בוט אינסטגרם. לא runtime שני.

ה־Control Plane מייצר **הזדמנויות תוכן, תוכן, QA, ניסויים, מדידה והמלצות**. הוא אינו Publish API בעצמו. שליחה בפועל שייכת ל־`vfigos` דרך כלי מחובר ובהתאם להרשאת ה־instance.

## עיקרון

| שלב | המשרד עושה אוטונומית | נשאר אנושי רק כשנדרש |
|---|---|---|
| לכידת מדיה | קורא `print.done`/media אמיתי, בודק ומסווג | צילום/סטייג'ינג פיזי שחסר |
| קריאייטיב | concept, Hook, shot list, EDL, cover, caption, QA | אין בחירת Hook/cover שגרתית |
| פרסום | מעביר ל־`vfigos`; standing authorization מאפשר tool publish | ללא standing authorization או שער חוקי/עסקי |
| קהילה | טיוטות/Work Order `pending_ops` | פעולה חיצונית חריגה |
| המרה | ייחוס הסתברותי | תמחור/סגירה/WhatsApp ללקוח |

אירוע רצפה = `print.done` (לא ניחוש מ־G-code). חסר צילום אמיתי = `waiting_for_media` + `shotRequest` מדויק.

## שער מצבים

```text
draft
  -> quality_checked
  -> policy_checked
  -> pending_publish_authorization
      -> authorized_for_tool_publish   (standing authorization)
      -> approved_for_manual_posting   (legacy / human path)
  -> published_verified | posted_manually
  -> performance_imported
  -> attributed
  -> learned
```

`posted_manually` נשמר כתאימות למסלול שבו אדם העלה ידנית. במסלול כלי, הצלחה היא `published_verified` ורק עם receipt + verification evidence.

## Creative Autopilot

מקור: `packages/vfom/CREATIVE-AUTOPILOT.md` · `VISUAL-OS.md` · `EDIT-DIRECTOR.md`.

- החלטות קריאטיביות שגרתיות מבוצעות אוטונומית.
- כשל איכות חוזר לתיקון פנימי; לא לבעלים.
- Visual OS brandScore >=80 + `CONTENT-RUBRIC >=20/25` + policy + written PREFLIGHT + rights הם תנאי מעבר.
- אם `creativeAutonomy.publish.standingAuthorization=true` בפרופיל ה־instance, תוכן שגרתי שעבר את כל השערים רשאי לעבור ל־`vfigos` בלי אישור נכס נוסף.
- אין publish tool/receipt/verification -> failover כנה; לא לטעון “פורסם”.

## Human Required

- צילום/סטייג'ינג פיזי שחסר.
- זכויות לקוח/מדיה, private CAD או זהות לקוח שאינן ברורות.
- מחיר, רכישה, Boost/Ads או הוצאה.
- הצעת מחיר/התחייבות עסקית או customer WhatsApp send.
- Print from HQ.
- תיוג משתמש בלי opt-in.
- חסם קשיח אחרי failover מתועד.

## מותר

- קליטת סטטוס הדפסה ומדיה אחרי `print.done`.
- טיוטות Reels / Stories / Covers / כיתובים והאשטגים.
- בחירה אוטונומית של Hook/cover/edit/slot בתוך הלוח הקבוע.
- tool publish דרך `vfigos` אם standing authorization פעיל וכל השערים עברו.
- ניתוח Insights **מיובאים** בלבד; חסר = «אין ספירה».
- סקרי קהילה כטיוטה; Work Order פנימי `pending_ops`.
- `approved_for_manual_posting` במסלול legacy שבו אדם בוחר לפרסם ידנית.

## אסור

- שה־Control Plane עצמו יהפוך ל־Instagram bot או יקרא Publish API ישירות.
- auto-DM / `send_dm`, תגובה, Follow/Like/unfollow אוטומטיים.
- רכישת עוקבים/מעורבות.
- Boost/Ads בלי ראש צוות.
- תיוג משתמשים בלי opt-in.
- הצעת מחיר או customer WhatsApp send אוטומטי.
- הצגת ייחוס הסתברותי כאמת מוחלטת.
- פרסום תצלום לקוח / שם / CAD / מידע עסקי בלי אישור זכויות ברור.
- סקר->Print מ־HQ. Work Order ≠ הדפסה.
- המצאת ₪ / Insights / סצנת רצפה / חוזק/חום בלי מקור.

## CTA

**PUBLIC_CURRENT_CTA** = הודעת Instagram בלבד (`@velvets_cloud`).  
ברירת מחדל: «לפרטים והזמנות — שלחו לנו הודעה כאן באינסטגרם».  
אסור בתוכן ציבורי: וואטסאפ / `050-2517000` / `wa.me` / «הזמנות בוואטסאפ».  
BUSINESS_CONTACT_RECORD: `050-2517000` פנימי בלבד. אוטו־DM נשאר נעול.

## לוח

`vfgrowth/CALENDAR.md` מנצח. **אין ריל כל יום**; אין cadence מומצא. Feed Architect רשאי לבחור רק בין משבצות מותרות קיימות.

## מדידה

`vfinsights/ATTRIBUTION.md` + `vfsales/ORDERS.md`.  
`estimated_value_ils` / `closed_value_ils` נשארים `null` עד אימות אדם. חסר מספר אמיתי = «אין ספירה».

## CLI

```text
python3 scripts/vf_organic_growth.py brief [--write]
python3 scripts/vf_organic_growth.py policy
python3 scripts/vf_organic_growth.py queue
python3 scripts/vf_organic_growth.py score
```

בריף 07:00 הוא read model/exception surface. כש־Creative Autopilot פעיל הוא לא מבקש אישור על החלטות קריאטיביות שגרתיות; הוא מציג רק `human_required` אמיתי.

סנסורים: `scripts/check-organic-growth.py` + `scripts/check-creative-autopilot.py`.
