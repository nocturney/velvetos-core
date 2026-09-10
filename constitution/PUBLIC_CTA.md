# PUBLIC_CURRENT_CTA · מול BUSINESS_CONTACT_RECORD

נעילה 10.9.2026 — Christian (Velvet Factory).  
מקור אמת לתוכן ציבורי. לא פק חדש.

## שני שדות נפרדים

| שדה | משמעות | ערך נוכחי (VF) |
|---|---|---|
| **PUBLIC_CURRENT_CTA** | מה מותר להציג בפיד / סטוריז / כריכות / כיתובים ציבוריים | Instagram בלבד; הניסוח תלוי `showcase` מול `commercial` |
| **BUSINESS_CONTACT_RECORD** | רשומת עסק פנימית / אינטגרציה / סגירה אנושית עתידית | WhatsApp `050-2517000` · איסוף שדרות |

אסור לערבב. מספר הוואטסאפ נשאר במסמכי אינטגרציה וב־`desk.studio.whatsapp` כרשומת עסק — **לא** כ־CTA ציבורי כרגע.

## Intent לפני CTA

כל פריט תוכן מקבל intent לפני כתיבת CTA:

### `showcase` / editorial — ברירת מחדל כשמציגים הדפסה בלי להציע את הפריט למכירה

המטרה: להראות תהליך, תנועה, פרטים, גימור, החלטת סטודיו או אובייקט שהודפס — **לא** להצהיר בפוסט שהמודל המצולם מוצע למכירה.

מותר:
- בלי CTA בכלל כאשר הסיפור עומד בפני עצמו.
- CTA מעורבות טבעי: שאלה, תגובה, follow/המשך.
- Instagram message ניטרלי כאשר יש סיבה אמיתית לשיחה, למשל «יש שאלות? שלחו לנו הודעה כאן באינסטגרם».

אסור ב־showcase:
- «לפרטים והזמנות»
- «רוצים אחד כזה?» / «רוצים אחד משלכם?»
- מחיר / זמינות / «מוכן לאיסוף» של הפריט המצולם
- ניסוח שמציג במפורש את המודל המצולם כהצעת מכר

פנייה פרטית שנכנסת בעקבות showcase היא שיחה פרטית נפרדת; אין צורך להפוך את הפוסט הציבורי למודעת מכירה כדי לאפשר פניות.

### `commercial` — תוכן שמטרתו להציע מוצר/שירות למכירה

ברירת המחדל נשארת:

> לפרטים והזמנות — שלחו לנו הודעה כאן באינסטגרם

ניסוחים קצרים מותרים:
- «לפרטים — שלחו הודעה»
- «להזמנות ושאלות — בהודעות»

`commercial` נבחר רק כאשר זו כוונת התוכן בפועל וה־subject/claims/מחיר אם ישנם מתאימים למסלול המסחרי. אין להפוך showcase ל־commercial אוטומטית רק מפני שהחשבון עסקי.

עברית טבעית עדיפה על «DM» באנגלית.

## אסור בתוכן ציבורי (כרגע)

- WhatsApp / וואטסאפ כ־CTA
- `wa.me`
- `050-2517000` בכיתוב / על פריים / בביו ציבורי
- «דברו איתנו בוואטסאפ»
- «הזמנות בוואטסאפ»
- אוטו־DM / `send_dm` / בוט הודעות

### עדיין נעול לנצח

- אוטו־DM, boost בלי lead, משלוח ארצי, ₪ / Insights מומצאים

## BUSINESS_CONTACT_RECORD

נשאר ל:
- `desk.studio.whatsapp`
- `mcpBind.whatsapp` (חיפוש/טיוטה; `send=false`)
- מסמכי `CONNECT-WHATSAPP.md` / אינטגרציה עתידית
- סגירה אנושית פנימית אם הבעלים יפתח מחדש

סטטוס נוכחי: **disabled for public CTA** · **disabled for customer outreach from HQ** · לא חלק מנתיב הפרסום הציבורי.

אין לשלוח הודעות לקוחות אוטומטית (לא WhatsApp, לא DM כלי).

## איפה זה חי במכונה

| קובץ | שדה |
|---|---|
| `instances/velvet-factory/instance/velvet-factory.json` | `cta.primary` = commercial Instagram-message default · `cta.businessContact` = RECORD |
| `packages/velvetos/samples/velvet-factory.json` | אותו מבנה |
| `packages/vfcanva/FORMATS.json` | `cta.public` / `cta.businessContact` |
| `.cursor/vf-desk.json` | `studio.whatsapp` = RECORD · `studio.publicCta` = PUBLIC |
| `packages/vfigos/PROFILE-DESIRED.json` | ביו מבוקש עם Instagram-message CTA |
| `packages/vfom/CREATIVE-MANIFEST.schema.json` / job manifest | creative intent קובע showcase מול commercial לפני copy |

השדות הקיימים של `cta.primary` נשארים ברירת מחדל למסלול **commercial**; הם אינם הוראה להזריק CTA מכירתי לכל פוסט.

## רישיון מודל מול CTA

מדיניות ה־workflow: owner-captured `showcase` אינו נחסם אוטומטית רק בגלל שחסר metadata של רישיון מסחרי למודל. אם התוכן הציבורי מציע במפורש את המודל למכירה, מדובר ב־`commercial` ואז בדיקות המסלול המסחרי יכולות לחול. מדיה צד ג׳, UGC, פרטיות או מגבלת זכויות ידועה נשארים gates נפרדים.

זו מדיניות תפעול פנימית ולא קביעה משפטית לגבי תנאי רישיון מסוים.

## בדיקה

`python3 scripts/check-public-cta.py` · נכלל ב־`check-all.py`.
