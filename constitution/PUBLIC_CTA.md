# PUBLIC_CURRENT_CTA · מול BUSINESS_CONTACT_RECORD

נעילה 8.9.2026 — Christian (Velvet Factory).  
מקור אמת לתוכן ציבורי. לא פק חדש.

## שני שדות נפרדים

| שדה | משמעות | ערך נוכחי (VF) |
|---|---|---|
| **PUBLIC_CURRENT_CTA** | מה מופיע בפיד / סטוריז / כריכות / כיתובים ציבוריים | **Instagram DM only** — `@velvets_cloud` |
| **BUSINESS_CONTACT_RECORD** | רשומת עסק פנימית / אינטגרציה / סגירה אנושית עתידית | WhatsApp `050-2517000` · איסוף שדרות |

אסור לערבב. מספר הוואטסאפ נשאר במסמכי אינטגרציה וב־`desk.studio.whatsapp` כרשומת עסק — **לא** כ־CTA ציבורי כרגע.

## PUBLIC_CURRENT_CTA (ברירת מחדל)

ברירת מחדל:

> לפרטים והזמנות — שלחו לנו הודעה כאן באינסטגרם

ניסוחים קצרים מותרים:

- «לפרטים — שלחו הודעה»
- «רוצים אחד כזה? דברו איתנו כאן»
- «להזמנות ושאלות — בהודעות»

עברית טבעית עדיפה על «DM» באנגלית.

### אסור בתוכן ציבורי (כרגע)

- WhatsApp / וואטסאפ כ־CTA
- `wa.me`
- `050-2517000` בכיתוב / על פריים / בביו ציבורי
- «דברו איתנו בוואטסאפ»
- «הזמנות בוואטסאפ»
- אוטו־DM / `send_dm` / בוט הודעות

### עדיין נעול לנצח

- אוטו־DM, boost בלי ראש צוות, משלוח ארצי, ₪ / Insights מומצאים

## BUSINESS_CONTACT_RECORD

נשאר ל:

- `desk.studio.whatsapp`
- `mcpBind.whatsapp` (חיפוש/טיוטה; `send=false`)
- מסמכי `CONNECT-WHATSAPP.md` / אינטגרציה עתידית
- סגירה אנושית פנימית אם הבעלים יפתח מחדש

סטטוס נוכחי: **disabled for public CTA** · **disabled for customer outreach from HQ** · לא חלק מנתיב הפרסום הציבורי.

אין לשלוח הודעות לקוחות אוטומטית (לא וואטסאפ, לא DM כלי).

## איפה זה חי במכונה

| קובץ | שדה |
|---|---|
| `instances/velvet-factory/instance/velvet-factory.json` | `cta.primary` = PUBLIC · `cta.businessContact` = RECORD |
| `packages/velvetos/samples/velvet-factory.json` | אותו מבנה |
| `packages/vfcanva/FORMATS.json` | `cta.public` / `cta.businessContact` |
| `.cursor/vf-desk.json` | `studio.whatsapp` = RECORD · `studio.publicCta` = PUBLIC |
| `packages/vfigos/PROFILE-DESIRED.json` | ביו מבוקש עם CTA הודעות |

## בדיקה

`python3 scripts/check-public-cta.py` · נכלל ב־`check-all.py`.
